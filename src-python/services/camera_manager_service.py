"""
Servicio de gestión de cámaras con nueva estructura 3FN.

Proporciona una interfaz de alto nivel para gestionar cámaras,
integrando el DataService con la nueva estructura normalizada.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from services.base_service import BaseService
from services.data_service import DataService, get_data_service
from services.connection_service import ConnectionService, ConnectionType
from models.camera_model import CameraModel, ConnectionConfig, StreamConfig, CameraCapabilities, ProtocolType, ConnectionStatus
from utils.exceptions import (
    CameraNotFoundError,
    CameraAlreadyExistsError,
    InvalidCredentialsError,
    ServiceError
)


class CameraManagerService(BaseService):
    """
    Servicio de gestión de cámaras con persistencia 3FN.
    
    Responsabilidades:
    - CRUD de cámaras con nueva estructura
    - Gestión de credenciales encriptadas
    - Manejo de endpoints descubiertos
    - Coordinación con ConnectionService
    - Conversión entre modelos de dominio y DB
    """
    
    _instance = None
    
    def __new__(cls) -> "CameraManagerService":
        """Garantiza una única instancia del servicio (Singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio."""
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self._data_service = get_data_service()
        self._connection_service = ConnectionService()
        self._cameras_cache: Dict[str, CameraModel] = {}
        self._cache_lock = asyncio.Lock()
        self._initialized = True
        
        self.logger.info("CameraManagerService inicializado")
    
    async def initialize(self) -> None:
        """Inicializa el servicio y carga cámaras desde DB."""
        try:
            # Inicializar servicios dependientes
            await self._data_service.initialize()
            
            # Iniciar ConnectionService
            if not self._connection_service.is_running:
                await self._connection_service.start_async()
                self.logger.info("ConnectionService iniciado")
            
            # Cargar cámaras existentes
            await self._load_cameras_from_db()
            
            self.logger.info(f"Servicio inicializado con {len(self._cameras_cache)} cámaras")
            
        except Exception as e:
            self.logger.error(f"Error inicializando servicio: {e}")
            raise ServiceError(f"No se pudo inicializar CameraManagerService: {e}")
    
    async def _load_cameras_from_db(self) -> None:
        """Carga todas las cámaras desde la base de datos."""
        try:
            # Limpiar caché existente
            async with self._cache_lock:
                self._cameras_cache.clear()
                self.logger.info("Caché de cámaras limpiado")
            
            # Obtener IDs de cámaras activas
            camera_ids = await self._data_service.get_all_camera_ids()
            
            for camera_id in camera_ids:
                try:
                    camera = await self._load_camera_from_db(camera_id)
                    if camera:
                        async with self._cache_lock:
                            self._cameras_cache[camera_id] = camera
                except Exception as e:
                    self.logger.error(f"Error cargando cámara {camera_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error cargando cámaras desde DB: {e}")
    
    async def _load_camera_from_db(self, camera_id: str) -> Optional[CameraModel]:
        """
        Carga una cámara específica desde la DB.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            CameraModel o None si no existe
        """
        try:
            # Obtener configuración completa desde nueva estructura
            camera_data = await self._data_service.get_camera_full_config(camera_id)
            
            if not camera_data:
                return None
            
            # Reconstruir modelo desde datos
            return self._build_camera_model_from_db(camera_data)
            
        except Exception as e:
            self.logger.error(f"Error cargando cámara {camera_id} desde DB: {e}")
            return None
    
    async def list_cameras(self) -> List[CameraModel]:
        """
        Lista todas las cámaras activas.
        
        Returns:
            Lista de CameraModel
        """
        try:
            # Obtener IDs de todas las cámaras
            camera_ids = await self._data_service.get_all_camera_ids()
            
            cameras = []
            for camera_id in camera_ids:
                camera = await self.get_camera(camera_id)
                if camera:
                    cameras.append(camera)
            
            self.logger.info(f"Listadas {len(cameras)} cámaras desde base de datos")
            return cameras
            
        except Exception as e:
            self.logger.error(f"Error listando cámaras: {e}")
            return []
    
    def _build_camera_model_from_db(self, data: Dict[str, Any]) -> CameraModel:
        """
        Construye un CameraModel desde datos de la DB.
        
        Args:
            data: Datos de la DB
            
        Returns:
            CameraModel reconstruido
        """
        # Configuración de conexión
        creds = data.get('credentials', {})
        connection_config = ConnectionConfig(
            ip=data['ip_address'],
            username=creds.get('username', 'admin'),
            password=creds.get('password', ''),
            auth_type=creds.get('auth_type', 'basic')
        )
        
        # Obtener puertos desde protocolos
        protocols = data.get('protocols', [])
        for protocol in protocols:
            if protocol['type'] == 'RTSP':
                connection_config.rtsp_port = protocol.get('port', 554)
            elif protocol['type'] == 'ONVIF':
                connection_config.onvif_port = protocol.get('port', 80)
            elif protocol['type'] == 'HTTP':
                connection_config.http_port = protocol.get('port', 80)
        
        # Configuración de streaming
        stream_profiles = data.get('stream_profiles', [])
        default_profile = next((p for p in stream_profiles if p.get('is_default')), None)
        
        if default_profile:
            stream_config = StreamConfig(
                channel=default_profile.get('channel', 1),
                subtype=default_profile.get('subtype', 0),
                resolution=default_profile.get('resolution', '1920x1080'),
                codec=default_profile.get('codec', 'H264'),
                fps=default_profile.get('fps', 30),
                bitrate=default_profile.get('bitrate', 2048),
                quality=default_profile.get('quality', 'high')
            )
        else:
            stream_config = StreamConfig()
        
        # Capacidades
        supported_protocols = [
            ProtocolType(p['type'].lower()) 
            for p in protocols 
            if p.get('is_enabled', True)
        ]
        
        capabilities = CameraCapabilities(
            supported_protocols=supported_protocols
        )
        
        # Crear modelo con ID de la base de datos
        camera = CameraModel(
            brand=data['brand'],
            model=data['model'],
            display_name=data.get('display_name', f"{data['brand']} {data['model']}"),
            connection_config=connection_config,
            stream_config=stream_config,
            capabilities=capabilities,
            camera_id=data['camera_id']  # Pasar el ID desde la DB
        )
        camera.is_active = data.get('is_active', True)
        camera.location = data.get('location')
        camera.description = data.get('description')
        
        # Establecer el protocolo principal o el primero disponible
        primary_protocol = next((p for p in protocols if p.get('is_primary')), None)
        if primary_protocol:
            camera.protocol = ProtocolType(primary_protocol['type'].lower())
        elif supported_protocols:
            camera.protocol = supported_protocols[0]
        
        self.logger.info(f"Cámara {camera.camera_id} cargada con protocolo: {camera.protocol.value if camera.protocol else 'None'}")
        
        # Cargar endpoints descubiertos
        for endpoint in data.get('endpoints', []):
            camera.add_discovered_endpoint(
                endpoint_type=endpoint['type'],
                url=endpoint['url'],
                verified=endpoint.get('verified', False),
                priority=endpoint.get('priority', 0)
            )
        
        # Cargar estadísticas
        stats = data.get('statistics', {})
        if stats:
            camera.stats.connection_attempts = stats.get('total_connections', 0)
            camera.stats.successful_connections = stats.get('successful_connections', 0)
            camera.stats.failed_connections = stats.get('failed_connections', 0)
        
        return camera
    
    # === Métodos CRUD ===
    
    async def create_camera(self, camera_data: Dict[str, Any]) -> CameraModel:
        """
        Crea una nueva cámara.
        
        Args:
            camera_data: Datos de la cámara
            
        Returns:
            CameraModel creado
            
        Raises:
            CameraAlreadyExistsError: Si la cámara ya existe
            ValidationError: Si los datos son inválidos
        """
        try:
            # Construir modelo
            connection_config = ConnectionConfig(
                ip=camera_data['ip'],
                username=camera_data['username'],
                password=camera_data['password'],
                rtsp_port=camera_data.get('rtsp_port', 554),
                onvif_port=camera_data.get('onvif_port', 80),
                http_port=camera_data.get('http_port', 80),
                auth_type=camera_data.get('auth_type', 'basic')
            )
            
            camera = CameraModel(
                brand=camera_data['brand'],
                model=camera_data.get('model', 'Unknown'),
                display_name=camera_data['display_name'],
                connection_config=connection_config
            )
            
            # Verificar si ya existe
            if camera.camera_id in self._cameras_cache:
                raise CameraAlreadyExistsError(camera.camera_id)
            
            # Preparar credenciales
            credentials = {
                'username': connection_config.username,
                'password': connection_config.password
            }
            
            # Guardar en DB con nueva estructura
            success = await self._data_service.save_camera_with_config(
                camera=camera,
                credentials=credentials,
                endpoints=camera_data.get('endpoints', [])
            )
            
            if not success:
                raise ServiceError("No se pudo guardar la cámara en la base de datos")
            
            # Agregar a cache
            async with self._cache_lock:
                self._cameras_cache[camera.camera_id] = camera
            
            self.logger.info(f"Cámara creada: {camera.camera_id}")
            return camera
            
        except Exception as e:
            self.logger.error(f"Error creando cámara: {e}")
            raise
    
    async def get_camera(self, camera_id: str) -> CameraModel:
        """
        Obtiene una cámara por ID.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            CameraModel
            
        Raises:
            CameraNotFoundError: Si no se encuentra la cámara
        """
        # Buscar en cache primero
        async with self._cache_lock:
            if camera_id in self._cameras_cache:
                return self._cameras_cache[camera_id]
        
        # Si no está en cache, cargar desde DB
        camera = await self._load_camera_from_db(camera_id)
        
        if not camera:
            raise CameraNotFoundError(camera_id)
        
        # Agregar a cache
        async with self._cache_lock:
            self._cameras_cache[camera_id] = camera
        
        return camera
    
    async def get_all_cameras(self) -> List[CameraModel]:
        """
        Obtiene todas las cámaras.
        
        Returns:
            Lista de CameraModel
        """
        async with self._cache_lock:
            # Si el caché está vacío, cargar desde DB
            if not self._cameras_cache:
                self.logger.warning("Caché de cámaras vacío, recargando desde DB")
                # Liberar el lock temporalmente para evitar deadlock
                pass
        
        # Cargar desde DB si es necesario (fuera del lock)
        if not self._cameras_cache:
            await self._load_cameras_from_db()
        
        # Devolver cámaras del caché
        async with self._cache_lock:
            return list(self._cameras_cache.values())
    
    async def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> CameraModel:
        """
        Actualiza una cámara.
        
        Args:
            camera_id: ID de la cámara
            updates: Campos a actualizar
            
        Returns:
            CameraModel actualizado
            
        Raises:
            CameraNotFoundError: Si no se encuentra la cámara
        """
        camera = await self.get_camera(camera_id)
        
        # Actualizar campos básicos
        if 'display_name' in updates:
            camera.display_name = updates['display_name']
        
        if 'location' in updates:
            camera.location = updates['location']
            
        if 'description' in updates:
            camera.description = updates['description']
        
        # Actualizar configuración de conexión
        if 'connection_config' in updates:
            camera.update_connection_config(**updates['connection_config'])
        
        # Actualizar credenciales si se proporcionan
        if 'credentials' in updates:
            credentials = updates['credentials']
            await self._data_service.save_camera_with_config(
                camera=camera,
                credentials=credentials
            )
        
        # Actualizar endpoints si se proporcionan
        if 'endpoints' in updates:
            for endpoint in updates['endpoints']:
                camera.add_discovered_endpoint(**endpoint)
                await self._data_service.save_discovered_endpoint(
                    camera_id=camera_id,
                    endpoint_type=endpoint['type'],
                    url=endpoint['url'],
                    verified=endpoint.get('verified', False)
                )
        
        self.logger.info(f"Cámara actualizada: {camera_id}")
        return camera
    
    async def delete_camera(self, camera_id: str) -> bool:
        """
        Elimina una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            CameraNotFoundError: Si no se encuentra la cámara
        """
        # Verificar que existe
        await self.get_camera(camera_id)
        
        # Desconectar si está conectada
        await self.disconnect_camera(camera_id)
        
        # Eliminar de DB
        # TODO: Implementar delete en DataService
        
        # Eliminar de cache
        async with self._cache_lock:
            self._cameras_cache.pop(camera_id, None)
        
        self.logger.info(f"Cámara eliminada: {camera_id}")
        return True
    
    # === Métodos de conexión ===
    
    async def connect_camera(self, camera_id: str) -> bool:
        """
        Conecta una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se conectó exitosamente
        """
        self.logger.info(f"[MANAGER] Iniciando conexión para cámara: {camera_id}")
        
        camera = await self.get_camera(camera_id)
        
        # Log detalles de la cámara
        self.logger.info(f"[MANAGER] Detalles de cámara:")
        self.logger.info(f"  - ID: {camera.camera_id}")
        self.logger.info(f"  - Nombre: {camera.display_name}")
        self.logger.info(f"  - IP: {camera.connection_config.ip}")
        self.logger.info(f"  - Marca: {camera.brand}")
        self.logger.info(f"  - Protocolo: {camera.protocol}")
        self.logger.info(f"  - Puerto ONVIF: {camera.connection_config.onvif_port}")
        self.logger.info(f"  - Puerto RTSP: {camera.connection_config.rtsp_port}")
        self.logger.info(f"  - Usuario: {camera.connection_config.username}")
        
        # Usar ConnectionService para conectar
        success = await self._connection_service.connect_camera_async(
            camera=camera,
            connection_type=ConnectionType.RTSP_STREAM
        )
        
        # Actualizar estadísticas
        await self._data_service.update_connection_stats(
            camera_id=camera_id,
            success=success
        )
        
        return success
    
    async def disconnect_camera(self, camera_id: str) -> bool:
        """
        Desconecta una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se desconectó exitosamente
        """
        camera = await self.get_camera(camera_id)
        
        # Usar ConnectionService para desconectar
        return await self._connection_service.disconnect_camera_async(camera.camera_id)
    
    async def save_discovered_endpoint(self, camera_id: str, endpoint_type: str, 
                                     url: str, verified: bool = True) -> bool:
        """
        Guarda un endpoint descubierto.
        
        Args:
            camera_id: ID de la cámara
            endpoint_type: Tipo de endpoint
            url: URL descubierta
            verified: Si fue verificada
            
        Returns:
            True si se guardó correctamente
        """
        camera = await self.get_camera(camera_id)
        
        # Agregar al modelo
        camera.add_discovered_endpoint(endpoint_type, url, verified)
        
        # Persistir en DB
        return await self._data_service.save_discovered_endpoint(
            camera_id=camera_id,
            endpoint_type=endpoint_type,
            url=url,
            verified=verified
        )
    
    # === Métodos de utilidad ===
    
    async def test_camera_connection(self, connection_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Prueba la conexión a una cámara sin guardarla.
        
        Args:
            connection_data: Datos de conexión
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            # Crear modelo temporal
            connection_config = ConnectionConfig(
                ip=connection_data['ip'],
                username=connection_data['username'],
                password=connection_data['password']
            )
            
            temp_camera = CameraModel(
                brand=connection_data.get('brand', 'Generic'),
                model='Test',
                display_name='Test Camera',
                connection_config=connection_config
            )
            
            # Intentar conectar
            success = await self._connection_service.test_connection(temp_camera)
            
            if success:
                return True, "Conexión exitosa"
            else:
                return False, "No se pudo establecer conexión"
                
        except Exception as e:
            return False, str(e)
    
    async def get_camera_statistics(self, camera_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Diccionario con estadísticas
        """
        camera = await self.get_camera(camera_id)
        
        return {
            'camera_id': camera_id,
            'connection_attempts': camera.stats.connection_attempts,
            'successful_connections': camera.stats.successful_connections,
            'failed_connections': camera.stats.failed_connections,
            'success_rate': camera.stats.get_success_rate(),
            'last_connection_time': camera.stats.last_connection_time,
            'last_error': camera.stats.last_error,
            'discovered_endpoints': len(camera.discovered_endpoints),
            'verified_endpoints': len(camera.get_verified_endpoints())
        }
    
    async def update_connection_stats(self, camera_id: str, success: bool, connection_time: float = 0) -> bool:
        """
        Actualiza las estadísticas de conexión de una cámara.
        
        Args:
            camera_id: ID de la cámara
            success: Si la conexión fue exitosa
            connection_time: Tiempo de conexión en segundos
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Delegar al DataService
            return await self._data_service.update_connection_stats(
                camera_id=camera_id,
                success=success,
                connection_time=connection_time
            )
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas de {camera_id}: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        # Desconectar todas las cámaras
        for camera_id in list(self._cameras_cache.keys()):
            try:
                await self.disconnect_camera(camera_id)
            except Exception as e:
                self.logger.error(f"Error desconectando cámara {camera_id}: {e}")
        
        # Limpiar cache
        self._cameras_cache.clear()
        
        self.logger.info("CameraManagerService cerrado")


# Instancia global del servicio
camera_manager_service = CameraManagerService()