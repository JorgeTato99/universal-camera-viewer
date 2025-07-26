"""
Presenter para publicación de cámaras a servidores MediaMTX remotos.

Coordina la lógica de negocio entre cámaras locales y publicación remota,
siguiendo estrictamente el patrón MVP.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from presenters.base_presenter import BasePresenter
from services.mediamtx.api_client import get_mediamtx_api_client
from services.mediamtx.auth_service import get_auth_service
from services.mediamtx.remote_models import (
    RemoteCameraRequest,
    RemoteCameraResponse,
    CameraMapping
)
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.camera_manager_service import camera_manager_service
from services.publishing.stream_service import get_publishing_stream_service
from services.logging_service import get_secure_logger
from utils.exceptions import ValidationError, ServiceError, MediaMTXAPIError, MediaMTXAuthenticationError
from utils.sanitizers import sanitize_url


logger = get_secure_logger("presenters.mediamtx_publishing")


class MediaMTXPublishingPresenter(BasePresenter):
    """
    Presenter para gestión de publicación a servidores MediaMTX remotos.
    
    Responsabilidades:
    - Coordinar creación de cámaras remotas
    - Mapear cámaras locales a remotas
    - Gestionar URLs de publicación
    - Validar operaciones de negocio
    - Emitir eventos de estado
    """
    
    def __init__(self):
        """Inicializa el presenter."""
        super().__init__()
        self.logger = logger
        
        # Servicios
        self._api_client = get_mediamtx_api_client()
        self._auth_service = get_auth_service()
        self._db_service = get_mediamtx_db_service()
        self._camera_manager = camera_manager_service
        self._stream_service = get_publishing_stream_service()
        
        # Estado interno
        self._active_publications: Dict[str, Dict[str, Any]] = {}
        
    async def _initialize_presenter(self) -> None:
        """Inicialización específica del presenter."""
        self.logger.info("Inicializando MediaMTXPublishingPresenter")
        
        # Inicializar servicios si es necesario
        await self._api_client.initialize()
        await self._auth_service.initialize()
        await self._stream_service.initialize()
        
        # Cargar publicaciones activas de la BD
        await self._load_active_publications()
        
    async def _cleanup_presenter(self) -> None:
        """Limpieza específica del presenter."""
        self.logger.info("Limpiando MediaMTXPublishingPresenter")
        
        # Limpiar recursos
        await self._api_client.cleanup()
        await self._stream_service.cleanup()
        self._active_publications.clear()
    
    async def _load_active_publications(self) -> None:
        """Carga publicaciones activas desde la base de datos."""
        try:
            # Cargar publicaciones remotas activas
            publications = await self._db_service.get_active_remote_publications()
            
            for pub in publications:
                self._active_publications[pub['camera_id']] = {
                    'server_id': pub['server_id'],
                    'remote_id': pub['remote_camera_id'],
                    'publish_url': pub['publish_url'],
                    'webrtc_url': pub['webrtc_url'],
                    'status': pub['status'].lower(),
                    'created_at': pub['start_time']
                }
            
            self.logger.info(f"Cargadas {len(publications)} publicaciones remotas activas")
            
        except Exception as e:
            self.logger.error(f"Error cargando publicaciones activas: {str(e)}")
    
    async def publish_camera_to_remote(
        self,
        camera_id: str,
        server_id: int,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publica una cámara local a un servidor MediaMTX remoto.
        
        Args:
            camera_id: ID de la cámara local
            server_id: ID del servidor MediaMTX de destino
            custom_name: Nombre personalizado (opcional)
            custom_description: Descripción personalizada (opcional)
            
        Returns:
            Dict con resultado de la operación incluyendo URLs
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            ServiceError: Si hay error en la operación
        """
        try:
            await self.set_busy(True)
            
            # Validar cámara local existe
            camera = await self._camera_manager.get_camera(camera_id)
            if not camera:
                raise ValidationError(f"Cámara {camera_id} no encontrada")
            
            # Validar servidor existe y está autenticado
            server = await self._db_service.get_server_by_id(server_id)
            if not server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            # Verificar autenticación
            token = await self._auth_service.get_valid_token(server_id)
            if not token:
                raise ServiceError(
                    f"No hay sesión activa para servidor {server['server_name']}",
                    error_code="NOT_AUTHENTICATED"
                )
            
            self.logger.info(
                f"Publicando cámara {camera_id} ({camera.display_name or 'Sin nombre'}) "
                f"a servidor {server['server_name']}"
            )
            
            # Preparar datos para crear cámara remota
            camera_request = await self._prepare_camera_request(
                camera,
                custom_name,
                custom_description
            )
            
            # Crear cámara en servidor remoto con manejo de autenticación
            try:
                remote_camera = await self._api_client.create_camera(
                    server_id=server_id,
                    camera_data=camera_request
                )
            except MediaMTXAuthenticationError as e:
                # Error de autenticación - token inválido o expirado
                self.logger.warning(f"Error de autenticación creando cámara: {str(e)}")
                
                # Eliminar token del cache para forzar re-autenticación
                await self._auth_service.logout(server_id)
                
                return {
                    'success': False,
                    'error': 'Sesión expirada. Por favor, autentique nuevamente con el servidor.',
                    'error_code': 'AUTH_EXPIRED',
                    'server_id': server_id
                }
            except MediaMTXAPIError as e:
                # Verificar si es error 409 (conflicto - cámara ya existe)
                if e.status_code == 409:
                    self.logger.warning(
                        f"Cámara ya existe en servidor remoto, intentando obtener información"
                    )
                    
                    # TODO: Implementar lógica para obtener la cámara existente
                    # Por ahora, devolver error específico
                    return {
                        'success': False,
                        'error': 'La cámara ya existe en el servidor remoto. Por favor, elimínela primero o use otro nombre.',
                        'error_code': 'CAMERA_ALREADY_EXISTS',
                        'details': e.response_data if hasattr(e, 'response_data') else None
                    }
                
                # Otros errores de API
                self.logger.error(f"Error de API creando cámara: {str(e)}")
                return {
                    'success': False,
                    'error': f'Error del servidor remoto: {str(e)}',
                    'error_code': 'API_ERROR',
                    'details': e.response_data if hasattr(e, 'response_data') else None
                }
            
            # Crear mapeo local-remoto
            mapping = await self._api_client.map_local_to_remote(
                local_camera_id=camera_id,
                server_id=server_id,
                remote_camera_response=remote_camera
            )
            
            # Guardar en base de datos
            await self._save_publication_to_db(camera_id, server_id, mapping, remote_camera)
            
            # Generar session_id único
            import uuid
            session_id = str(uuid.uuid4())
            
            # Iniciar streaming con FFmpeg
            stream_started = False
            stream_message = ""
            
            try:
                success, message = await self._stream_service.start_stream(
                    session_id=session_id,
                    camera_id=camera_id,
                    server_id=server_id,
                    agent_command=remote_camera.agent_command
                )
                
                if success:
                    stream_started = True
                    stream_message = "Streaming iniciado"
                    self.logger.info(f"Stream iniciado para cámara {camera_id} - Sesión: {session_id}")
                else:
                    stream_message = f"Advertencia: No se pudo iniciar streaming - {message}"
                    self.logger.warning(stream_message)
                    
            except Exception as e:
                stream_message = f"Error iniciando streaming: {str(e)}"
                self.logger.error(stream_message)
            
            # Actualizar estado interno
            self._active_publications[camera_id] = {
                'server_id': server_id,
                'remote_id': remote_camera.id,
                'publish_url': remote_camera.publish_url,
                'webrtc_url': remote_camera.webrtc_url,
                'status': 'streaming' if stream_started else 'created',
                'session_id': session_id if stream_started else None,
                'created_at': datetime.utcnow()
            }
            
            # Emitir evento
            await self._emit_event('camera_published', {
                'camera_id': camera_id,
                'server_id': server_id,
                'remote_id': remote_camera.id,
                'publish_url': sanitize_url(remote_camera.publish_url),
                'webrtc_url': sanitize_url(remote_camera.webrtc_url),
                'streaming': stream_started
            })
            
            return {
                'success': True,
                'camera_id': camera_id,
                'remote_camera_id': remote_camera.id,
                'publish_url': remote_camera.publish_url,
                'webrtc_url': remote_camera.webrtc_url,
                'agent_command': remote_camera.agent_command,
                'streaming': stream_started,
                'session_id': session_id if stream_started else None,
                'message': f'Cámara publicada exitosamente en {server["server_name"]}. {stream_message}'
            }
            
        except ValidationError as e:
            self.logger.error(f"Error de validación: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
            
        except MediaMTXAPIError as e:
            self.logger.error(f"Error de API MediaMTX: {str(e)}")
            return {
                'success': False,
                'error': f'Error del servidor remoto: {str(e)}',
                'error_code': 'API_ERROR'
            }
            
        except Exception as e:
            self.logger.error(f"Error publicando cámara: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
            
        finally:
            await self.set_busy(False)
    
    async def _prepare_camera_request(
        self,
        camera: Dict[str, Any],
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None
    ) -> RemoteCameraRequest:
        """
        Prepara los datos de la cámara para enviar al servidor remoto.
        
        Args:
            camera: Datos de la cámara local
            custom_name: Nombre personalizado
            custom_description: Descripción personalizada
            
        Returns:
            RemoteCameraRequest listo para enviar
        """
        # Obtener RTSP URL de la cámara
        rtsp_url = await self._get_camera_rtsp_url(camera)
        
        # Preparar metadatos
        json_data = {
            'features': {
                'motion_detection': False,  # TODO: Implementar detección de movimiento
                'night_vision': camera.capabilities.has_ir if camera.capabilities else False,
                'two_way_audio': camera.capabilities.has_audio if camera.capabilities else False,
                'ptz': camera.capabilities.has_ptz if camera.capabilities else False
            },
            'fps': 30,  # TODO: Obtener FPS real del stream profile
            'location': {
                'building': camera.location or 'Sin ubicación',
                'zone': camera.location or 'general'
            },
            'model': f"{camera.brand or 'Unknown'} {camera.model or 'Camera'}",
            'resolution': '1920x1080',  # TODO: Obtener resolución real
            'local_camera_id': camera.camera_id,
            'local_camera_code': ''  # No existe atributo code en CameraModel
        }
        
        return RemoteCameraRequest(
            name=custom_name or camera.display_name or f"Camera {camera.camera_id}",
            description=custom_description or camera.description or '',
            rtsp_address=rtsp_url,
            json_data=json_data
        )
    
    async def _get_camera_rtsp_url(self, camera) -> str:
        """
        Obtiene la URL RTSP de una cámara local.
        
        Args:
            camera: Objeto CameraModel
            
        Returns:
            URL RTSP completa
            
        Raises:
            ValidationError: Si no se puede obtener la URL
        """
        # TODO: Implementar lógica real para obtener RTSP URL de los endpoints verificados
        # Por ahora usar un patrón genérico basado en la información de la cámara
        
        # Verificar que tenemos IP
        if not camera.ip:
            raise ValidationError(f"Cámara {camera.camera_id} sin dirección IP")
        
        # @todo: Obtener el endpoint RTSP real desde los protocolos verificados
        # Por ahora, usar patrones genéricos basados en marca
        
        # Construir URL con credenciales si están disponibles
        username = camera.username or ''
        password = camera.password or ''
        
        # Si hay credenciales, incluirlas en la URL
        auth_part = f"{username}:{password}@" if username and password else ""
        
        # Patrón genérico basado en marca
        brand = (camera.brand or '').lower()
        if brand == 'dahua':
            return f"rtsp://{auth_part}{camera.ip}:554/cam/realmonitor?channel=1&subtype=0"
        elif brand == 'hikvision':
            return f"rtsp://{auth_part}{camera.ip}:554/Streaming/Channels/101"
        elif brand == 'tp-link' or brand == 'tplink':
            return f"rtsp://{auth_part}{camera.ip}:554/stream1"
        else:
            # Patrón genérico
            return f"rtsp://{auth_part}{camera.ip}:554/stream1"
    
    async def _save_publication_to_db(
        self,
        camera_id: str,
        server_id: int,
        mapping: CameraMapping,
        remote_camera: RemoteCameraResponse
    ) -> None:
        """
        Guarda la publicación en la base de datos.
        
        Args:
            camera_id: ID de cámara local
            server_id: ID del servidor
            mapping: Mapeo local-remoto
            remote_camera: Respuesta del servidor remoto
        """
        try:
            # Generar session_id único
            import uuid
            session_id = str(uuid.uuid4())
            
            # Guardar en BD
            publication_id = await self._db_service.save_remote_publication(
                camera_id=camera_id,
                server_id=server_id,
                remote_camera_id=remote_camera.id,
                publish_url=mapping.publish_url,
                webrtc_url=mapping.webrtc_url,
                agent_command=remote_camera.agent_command,
                session_id=session_id
            )
            
            if publication_id:
                self.logger.info(
                    f"Publicación guardada en BD - ID: {publication_id}, "
                    f"Cámara: {camera_id} -> Remoto: {remote_camera.id}"
                )
            else:
                self.logger.warning("No se pudo guardar la publicación en BD")
            
        except Exception as e:
            self.logger.error(f"Error guardando publicación en BD: {str(e)}")
            # No fallar la operación por error de BD
    
    async def unpublish_camera(
        self,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Elimina una cámara del servidor remoto.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            await self.set_busy(True)
            
            # Verificar si está publicada
            if camera_id not in self._active_publications:
                return {
                    'success': False,
                    'error': 'La cámara no está publicada',
                    'error_code': 'NOT_PUBLISHED'
                }
            
            publication = self._active_publications[camera_id]
            server_id = publication['server_id']
            remote_id = publication['remote_id']
            
            self.logger.info(
                f"Despublicando cámara {camera_id} (remoto: {remote_id})"
            )
            
            # Detener streaming si está activo
            if publication.get('session_id'):
                try:
                    await self._stream_service.stop_stream(
                        publication['session_id'],
                        reason="User requested unpublish"
                    )
                    self.logger.info(f"Stream detenido para cámara {camera_id}")
                except Exception as e:
                    self.logger.error(f"Error deteniendo stream: {str(e)}")
            
            # Eliminar del servidor remoto
            success = await self._api_client.delete_camera(
                server_id=server_id,
                camera_id=remote_id
            )
            
            if success:
                # Actualizar estado
                del self._active_publications[camera_id]
                
                # Actualizar BD para marcar como inactiva
                await self._db_service.deactivate_publication(camera_id)
                
                # Emitir evento
                await self._emit_event('camera_unpublished', {
                    'camera_id': camera_id,
                    'server_id': server_id,
                    'remote_id': remote_id
                })
                
                return {
                    'success': True,
                    'message': 'Cámara despublicada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo eliminar la cámara del servidor remoto',
                    'error_code': 'DELETE_FAILED'
                }
                
        except Exception as e:
            self.logger.error(f"Error despublicando cámara: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
            
        finally:
            await self.set_busy(False)
    
    async def get_publication_status(
        self,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene el estado de publicación de una cámara.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con información de publicación
        """
        if camera_id in self._active_publications:
            publication = self._active_publications[camera_id]
            
            # Sincronizar estado con servidor remoto si es posible
            try:
                remote_status = await self._api_client.sync_camera_status(
                    server_id=publication['server_id'],
                    camera_id=publication['remote_id']
                )
                
                if remote_status:
                    publication['status'] = remote_status.lower()
                    
            except Exception as e:
                self.logger.error(f"Error sincronizando estado: {str(e)}")
            
            return {
                'is_published': True,
                'publication': publication
            }
        
        return {
            'is_published': False,
            'publication': None
        }
    
    async def get_streaming_metrics(
        self,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene métricas en tiempo real del streaming de una cámara.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con métricas del streaming o error
        """
        try:
            publication = self._active_publications.get(camera_id)
            if not publication:
                return {
                    'success': False,
                    'error': 'Cámara no está publicada',
                    'error_code': 'NOT_PUBLISHED'
                }
            
            session_id = publication.get('session_id')
            if not session_id:
                return {
                    'success': False,
                    'error': 'No hay streaming activo para esta cámara',
                    'error_code': 'NO_STREAM'
                }
            
            # Obtener métricas del servicio de streaming
            metrics = await self._stream_service.get_stream_metrics(session_id)
            
            if metrics:
                return {
                    'success': True,
                    'camera_id': camera_id,
                    'metrics': metrics
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudieron obtener métricas',
                    'error_code': 'METRICS_ERROR'
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo métricas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    async def restart_streaming(
        self,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Reinicia el streaming de una cámara publicada.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            publication = self._active_publications.get(camera_id)
            if not publication:
                return {
                    'success': False,
                    'error': 'Cámara no está publicada',
                    'error_code': 'NOT_PUBLISHED'
                }
            
            session_id = publication.get('session_id')
            if not session_id:
                return {
                    'success': False,
                    'error': 'No hay streaming activo para reiniciar',
                    'error_code': 'NO_STREAM'
                }
            
            self.logger.info(f"Reiniciando streaming para cámara {camera_id}")
            
            # Reiniciar stream
            success, message = await self._stream_service.restart_stream(session_id)
            
            if success:
                # Emitir evento
                await self._emit_event('stream_restarted', {
                    'camera_id': camera_id,
                    'session_id': session_id
                })
                
                return {
                    'success': True,
                    'message': 'Streaming reiniciado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': message,
                    'error_code': 'RESTART_FAILED'
                }
                
        except Exception as e:
            self.logger.error(f"Error reiniciando streaming: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    async def list_published_cameras(
        self,
        server_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista las cámaras publicadas.
        
        Args:
            server_id: Filtrar por servidor (opcional)
            
        Returns:
            Lista de publicaciones activas
        """
        publications = []
        
        for camera_id, publication in self._active_publications.items():
            if server_id is None or publication['server_id'] == server_id:
                # Obtener info de cámara local
                camera = await self._camera_manager.get_camera(camera_id)
                
                publications.append({
                    'camera_id': camera_id,
                    'camera_name': camera.display_name if camera else 'Desconocida',
                    'server_id': publication['server_id'],
                    'remote_id': publication['remote_id'],
                    'publish_url': publication['publish_url'],
                    'webrtc_url': publication['webrtc_url'],
                    'status': publication.get('status', 'unknown'),
                    'created_at': publication['created_at']
                })
        
        return publications


# Instancia singleton
_presenter: Optional[MediaMTXPublishingPresenter] = None


def get_mediamtx_publishing_presenter() -> MediaMTXPublishingPresenter:
    """
    Obtiene la instancia singleton del presenter.
    
    Returns:
        MediaMTXPublishingPresenter singleton
    """
    global _presenter
    
    if _presenter is None:
        _presenter = MediaMTXPublishingPresenter()
        
    return _presenter