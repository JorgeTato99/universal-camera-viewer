"""
Servicio adaptador para publicación de streams a servidores MediaMTX remotos.

Este servicio coordina entre el API client de MediaMTX y el publisher RTSP existente,
gestionando el ciclo de vida completo de publicación remota.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
import asyncio
import uuid

from services.base_service import BaseService
from services.mediamtx.api_client import get_mediamtx_api_client
from services.mediamtx.auth_service import get_auth_service
from services.mediamtx.remote_models import CameraMapping
from services.publishing.rtsp_publisher_service import get_publisher_service
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.camera_manager_service import camera_manager_service
from models.publishing import PublishConfiguration, PublishResult, PublishErrorType
from services.logging_service import get_secure_logger
from utils.exceptions import ServiceError, ValidationError, MediaMTXAPIError
from utils.sanitizers import sanitize_url


logger = get_secure_logger("services.mediamtx.remote_publisher")


class MediaMTXRemotePublisher(BaseService):
    """
    Servicio que coordina la publicación de cámaras locales hacia servidores MediaMTX remotos.
    
    Este servicio actúa como adaptador entre:
    - MediaMTXAPIClient: Para gestionar cámaras en el servidor remoto
    - RTSPPublisherService: Para gestionar procesos FFmpeg locales
    - MediaMTXAuthService: Para mantener autenticación válida
    
    Implementa el patrón Singleton para mantener estado consistente.
    """
    
    # Límites de configuración para evitar crecimiento indefinido de memoria
    MAX_REMOTE_PUBLICATIONS = 100  # Máximo de publicaciones simultáneas
    
    def __init__(self):
        """Inicializa el servicio con sus dependencias."""
        super().__init__()
        self.logger = logger
        
        # Servicios dependientes
        self._api_client = get_mediamtx_api_client()
        self._auth_service = get_auth_service()
        self._db_service = get_mediamtx_db_service()
        self._camera_manager = camera_manager_service
        self._rtsp_publisher = None  # Se inicializa en initialize()
        
        # Estado interno: mapeo camera_id -> información de publicación remota
        self._remote_publications: Dict[str, Dict[str, Any]] = {}
        
        # Lock para operaciones concurrentes
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Inicializa el servicio y sus dependencias.
        
        Realiza:
        - Inicialización de servicios dependientes
        - Carga de publicaciones remotas activas desde BD
        - Verificación de configuración
        """
        self.logger.info("Inicializando MediaMTXRemotePublisher")
        
        try:
            # Inicializar servicios si es necesario
            await self._api_client.initialize()
            await self._auth_service.initialize()
            
            # Obtener servicio de publicación RTSP
            # Por ahora usar configuración dummy para remoto
            # TODO: Crear configuración específica para publicación remota
            dummy_config = PublishConfiguration(
                mediamtx_url="rtsp://dummy",  # Se sobrescribirá con URL remota
                auth_enabled=False,
                api_enabled=False
            )
            self._rtsp_publisher = get_publisher_service(dummy_config)
            await self._rtsp_publisher.initialize()
            
            # Cargar publicaciones remotas activas
            await self._load_active_remote_publications()
            
            self.logger.info("MediaMTXRemotePublisher inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando servicio: {str(e)}")
            raise ServiceError(
                f"No se pudo inicializar MediaMTXRemotePublisher: {str(e)}",
                error_code="INIT_ERROR"
            )
    
    async def _load_active_remote_publications(self) -> None:
        """Carga publicaciones remotas activas desde la base de datos."""
        try:
            publications = await self._db_service.get_active_remote_publications()
            
            for pub in publications:
                self._remote_publications[pub['camera_id']] = {
                    'server_id': pub['server_id'],
                    'remote_camera_id': pub['remote_camera_id'],
                    'publish_url': pub['publish_url'],
                    'webrtc_url': pub['webrtc_url'],
                    'session_id': pub['session_id'],
                    'status': pub['status'],
                    'created_at': pub['start_time']
                }
            
            self.logger.info(
                f"Cargadas {len(self._remote_publications)} publicaciones remotas activas"
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando publicaciones activas: {str(e)}")
    
    async def publish_camera(
        self,
        camera_id: str,
        server_id: int,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None
    ) -> PublishResult:
        """
        Publica una cámara local a un servidor MediaMTX remoto.
        
        Este método coordina todo el flujo:
        1. Verificar autenticación con servidor remoto
        2. Crear/obtener cámara en servidor remoto
        3. Iniciar proceso FFmpeg local para push al remoto
        4. Guardar estado en BD
        
        Args:
            camera_id: ID de la cámara local
            server_id: ID del servidor MediaMTX destino
            custom_name: Nombre personalizado para la cámara remota
            custom_description: Descripción personalizada
            
        Returns:
            PublishResult con el resultado de la operación
        """
        async with self._lock:
            try:
                # Verificar si ya está publicando
                if camera_id in self._remote_publications:
                    self.logger.warning(f"Cámara {camera_id} ya está publicando remotamente")
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="La cámara ya está publicando en un servidor remoto",
                        error_type=PublishErrorType.ALREADY_PUBLISHING
                    )
                
                # Verificar límite de publicaciones
                if len(self._remote_publications) >= self.MAX_REMOTE_PUBLICATIONS:
                    self.logger.error(
                        f"Límite de publicaciones remotas alcanzado: {self.MAX_REMOTE_PUBLICATIONS}"
                    )
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error=f"Se alcanzó el límite máximo de {self.MAX_REMOTE_PUBLICATIONS} publicaciones simultáneas",
                        error_type=PublishErrorType.LIMIT_EXCEEDED
                    )
                
                # Verificar autenticación
                self.logger.debug(f"Verificando autenticación con servidor {server_id}")
                token = await self._auth_service.get_valid_token(server_id)
                if not token:
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="No hay sesión activa con el servidor remoto",
                        error_type=PublishErrorType.AUTH_FAILED
                    )
                
                # Obtener información del servidor
                server = await self._db_service.get_server_by_id(server_id)
                if not server:
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="Servidor no encontrado",
                        error_type=PublishErrorType.CONFIG_ERROR
                    )
                
                # Obtener o crear cámara remota
                self.logger.info(
                    f"Creando cámara remota para {camera_id} en servidor {server['server_name']}"
                )
                
                mapping = await self._get_or_create_remote_camera(
                    camera_id, server_id, custom_name, custom_description
                )
                
                if not mapping:
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="No se pudo crear la cámara en el servidor remoto",
                        error_type=PublishErrorType.REMOTE_ERROR
                    )
                
                # Obtener información de la cámara local
                camera = await self._camera_manager.get_camera(camera_id)
                if not camera:
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="Cámara local no encontrada",
                        error_type=PublishErrorType.STREAM_UNAVAILABLE
                    )
                
                # Construir URL de origen (cámara local)
                source_url = await self._build_camera_rtsp_url(camera)
                
                # Iniciar publicación usando RTSPPublisherService modificado
                self.logger.info(
                    f"Iniciando publicación FFmpeg hacia {sanitize_url(mapping.publish_url)}"
                )
                
                # Llamar a RTSPPublisherService con URL externa
                result = await self._start_ffmpeg_publishing(
                    camera_id=camera_id,
                    source_url=source_url,
                    target_url=mapping.publish_url,
                    is_remote=True
                )
                
                if result.success:
                    # Guardar estado de publicación remota
                    session_id = str(uuid.uuid4())
                    
                    await self._db_service.save_remote_publication(
                        camera_id=camera_id,
                        server_id=server_id,
                        remote_camera_id=mapping.remote_camera_id,
                        publish_url=mapping.publish_url,
                        webrtc_url=mapping.webrtc_url,
                        agent_command=None,  # TODO: Obtener de remote_camera si está disponible
                        session_id=session_id
                    )
                    
                    # Actualizar estado interno
                    self._remote_publications[camera_id] = {
                        'server_id': server_id,
                        'remote_camera_id': mapping.remote_camera_id,
                        'publish_url': mapping.publish_url,
                        'webrtc_url': mapping.webrtc_url,
                        'session_id': session_id,
                        'status': 'publishing',
                        'created_at': datetime.utcnow()
                    }
                    
                    # Agregar URLs remotas al resultado
                    result.publish_url = mapping.publish_url
                    result.webrtc_url = mapping.webrtc_url
                    result.message = f"Publicando correctamente en {server['server_name']}"
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error publicando cámara {camera_id}: {str(e)}")
                return PublishResult(
                    success=False,
                    camera_id=camera_id,
                    error=f"Error interno: {str(e)}",
                    error_type=PublishErrorType.INTERNAL_ERROR
                )
    
    async def _get_or_create_remote_camera(
        self,
        camera_id: str,
        server_id: int,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None
    ) -> Optional[CameraMapping]:
        """
        Obtiene o crea una cámara en el servidor remoto.
        
        Args:
            camera_id: ID de cámara local
            server_id: ID del servidor remoto
            custom_name: Nombre personalizado
            custom_description: Descripción personalizada
            
        Returns:
            CameraMapping con la información de mapeo o None si falla
        """
        try:
            # Primero intentar obtener mapeo existente
            existing_mapping = self._api_client.get_camera_mapping(camera_id)
            if existing_mapping:
                self.logger.info(f"Usando mapeo existente para cámara {camera_id}")
                return existing_mapping
            
            # Si no existe, crear nueva cámara remota
            self.logger.info(f"Creando nueva cámara remota para {camera_id}")
            
            # Obtener información de la cámara local
            camera = await self._camera_manager.get_camera(camera_id)
            if not camera:
                self.logger.error(f"Cámara {camera_id} no encontrada")
                return None
            
            # Preparar request para crear cámara remota
            from services.mediamtx.remote_models import RemoteCameraRequest
            
            # Obtener URL RTSP
            rtsp_url = await self._build_camera_rtsp_url(camera)
            
            # Preparar metadatos
            # Obtener capacidades reales de la cámara
            capabilities = camera.get('capabilities', [])
            features = {
                'motion_detection': 'motion_detection' in capabilities,
                'night_vision': 'night_vision' in capabilities,
                'two_way_audio': 'audio' in capabilities or 'two_way_audio' in capabilities,
                'ptz': 'ptz' in capabilities
            }
            
            # Obtener información del stream principal si está disponible
            stream_info = self._get_stream_info(camera)
            
            json_data = {
                'features': features,
                'fps': stream_info.get('fps', 25),  # Default más realista: 25 fps
                'location': {
                    'building': camera.get('location', 'Sin ubicación'),
                    'zone': camera.get('zone', 'general')
                },
                'model': f"{camera.get('brand', 'Unknown')} {camera.get('model', 'Camera')}",
                'resolution': stream_info.get('resolution', '1280x720'),  # Default más común
                'local_camera_id': camera_id,
                'local_camera_code': camera.get('code', '')
            }
            
            camera_request = RemoteCameraRequest(
                name=custom_name or camera.get('display_name', f"Camera {camera_id}"),
                description=custom_description or camera.get('description', ''),
                rtsp_address=rtsp_url,
                json_data=json_data
            )
            
            # Crear cámara en servidor remoto
            remote_camera = await self._api_client.create_camera(
                server_id=server_id,
                camera_data=camera_request
            )
            
            # Crear mapeo local-remoto
            mapping = await self._api_client.map_local_to_remote(
                local_camera_id=camera_id,
                server_id=server_id,
                remote_camera_response=remote_camera
            )
            
            return mapping
            
        except Exception as e:
            self.logger.error(f"Error obteniendo/creando cámara remota: {str(e)}")
            return None
    
    def _get_stream_info(self, camera: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene información del stream principal de la cámara.
        
        Args:
            camera: Información de la cámara
            
        Returns:
            Dict con fps y resolución del stream
        """
        # Buscar información en los endpoints descubiertos
        endpoints = camera.get('endpoints', [])
        
        for endpoint in endpoints:
            if endpoint.get('type') == 'rtsp_main':
                # Si el endpoint tiene metadata del stream
                stream_meta = endpoint.get('metadata', {})
                if stream_meta:
                    return {
                        'fps': stream_meta.get('fps', 25),
                        'resolution': stream_meta.get('resolution', '1280x720')
                    }
        
        # Buscar en profiles si existe
        profiles = camera.get('profiles', [])
        if profiles:
            # Usar el primer perfil (generalmente el principal)
            main_profile = profiles[0]
            return {
                'fps': main_profile.get('framerate', 25),
                'resolution': f"{main_profile.get('width', 1280)}x{main_profile.get('height', 720)}"
            }
        
        # Valores por defecto basados en la marca
        brand = camera.get('brand', '').lower()
        if brand in ['dahua', 'hikvision']:
            return {'fps': 30, 'resolution': '1920x1080'}
        elif brand == 'tp-link':
            return {'fps': 15, 'resolution': '1280x720'}
        else:
            return {'fps': 25, 'resolution': '1280x720'}
    
    async def _build_camera_rtsp_url(self, camera: Dict[str, Any]) -> str:
        """
        Construye la URL RTSP de una cámara local.
        
        Args:
            camera: Información de la cámara
            
        Returns:
            URL RTSP completa con credenciales
        """
        # TODO: Implementar construcción real de URL RTSP
        # Por ahora usar lógica similar al presenter
        
        endpoints = camera.get('endpoints', [])
        for endpoint in endpoints:
            if endpoint.get('type') == 'rtsp_main':
                return endpoint['url']
        
        # Construir URL genérica si no hay endpoint
        ip = camera.get('ip_address')
        if not ip:
            raise ValidationError(f"Cámara {camera['camera_id']} sin dirección IP")
        
        # TODO: Agregar credenciales si están disponibles
        return f"rtsp://{ip}:554/stream1"
    
    async def _start_ffmpeg_publishing(
        self,
        camera_id: str,
        source_url: str,
        target_url: str,
        is_remote: bool = True
    ) -> PublishResult:
        """
        Inicia la publicación FFmpeg con URLs personalizadas.
        
        Usa el RTSPPublisherService modificado que ahora acepta URLs externas.
        
        Args:
            camera_id: ID de la cámara
            source_url: URL RTSP de origen
            target_url: URL RTSP de destino (remoto)
            is_remote: Indica si es publicación remota
            
        Returns:
            PublishResult con el resultado
        """
        try:
            # Llamar al servicio de publicación con URLs externas
            result = await self._rtsp_publisher.start_publishing(
                camera_id=camera_id,
                source_url=source_url,
                target_url=target_url,
                is_remote=is_remote,
                force_restart=False
            )
            
            if result.success:
                self.logger.info(
                    f"Proceso FFmpeg iniciado correctamente para publicación remota "
                    f"de cámara {camera_id}"
                )
            else:
                self.logger.error(
                    f"Error iniciando FFmpeg para cámara {camera_id}: {result.error}"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error iniciando publicación FFmpeg: {str(e)}")
            return PublishResult(
                success=False,
                camera_id=camera_id,
                error=f"Error iniciando FFmpeg: {str(e)}",
                error_type=PublishErrorType.INTERNAL_ERROR
            )
    
    async def stop_publishing(self, camera_id: str) -> PublishResult:
        """
        Detiene la publicación remota de una cámara.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            PublishResult con el resultado de la operación
        """
        async with self._lock:
            try:
                if camera_id not in self._remote_publications:
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="La cámara no está publicando remotamente",
                        error_type=PublishErrorType.NOT_PUBLISHING
                    )
                
                publication = self._remote_publications[camera_id]
                
                # Detener proceso FFmpeg local
                ffmpeg_result = await self._rtsp_publisher.stop_publishing(camera_id)
                
                if not ffmpeg_result.success:
                    self.logger.warning(
                        f"Error deteniendo FFmpeg para {camera_id}: {ffmpeg_result.error}"
                    )
                
                # Eliminar cámara del servidor remoto (opcional)
                # TODO: Implementar política de limpieza de cámaras remotas
                # Depende de la política: ¿mantener cámara remota o eliminarla?
                
                # Actualizar BD
                await self._db_service.deactivate_publication(camera_id)
                
                # Limpiar estado interno
                del self._remote_publications[camera_id]
                
                self.logger.info(f"Publicación remota detenida para cámara {camera_id}")
                
                return PublishResult(
                    success=True,
                    camera_id=camera_id,
                    message="Publicación remota detenida correctamente"
                )
                
            except Exception as e:
                self.logger.error(f"Error deteniendo publicación remota: {str(e)}")
                return PublishResult(
                    success=False,
                    camera_id=camera_id,
                    error=f"Error interno: {str(e)}",
                    error_type=PublishErrorType.INTERNAL_ERROR
                )
    
    async def get_remote_publication_status(
        self,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene el estado de publicación remota de una cámara.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con información de estado
        """
        if camera_id in self._remote_publications:
            publication = self._remote_publications[camera_id]
            
            # TODO: Sincronizar con estado real del proceso FFmpeg
            # y estado de la cámara en el servidor remoto
            
            return {
                'is_publishing': True,
                'server_id': publication['server_id'],
                'remote_camera_id': publication['remote_camera_id'],
                'publish_url': publication['publish_url'],
                'webrtc_url': publication['webrtc_url'],
                'status': publication['status'],
                'created_at': publication['created_at']
            }
        
        return {
            'is_publishing': False
        }
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self.logger.info("Limpiando MediaMTXRemotePublisher")
        
        # Detener todas las publicaciones remotas
        camera_ids = list(self._remote_publications.keys())
        for camera_id in camera_ids:
            await self.stop_publishing(camera_id)
        
        self._remote_publications.clear()
        self.logger.info("MediaMTXRemotePublisher limpiado correctamente")


# Instancia singleton
_instance: Optional[MediaMTXRemotePublisher] = None
_lock = asyncio.Lock()


async def get_mediamtx_remote_publisher() -> MediaMTXRemotePublisher:
    """
    Obtiene la instancia singleton del servicio.
    
    Returns:
        MediaMTXRemotePublisher singleton
    """
    global _instance
    
    if _instance is None:
        async with _lock:
            if _instance is None:
                _instance = MediaMTXRemotePublisher()
                await _instance.initialize()
    
    return _instance