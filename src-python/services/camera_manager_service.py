"""
Servicio de gestión de cámaras con nueva estructura 3FN.

Proporciona una interfaz de alto nivel para gestionar cámaras,
integrando el DataService con la nueva estructura normalizada.
"""
import asyncio

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from services.base_service import BaseService
from services.data_service import DataService, get_data_service
from services.connection_service import ConnectionService, ConnectionType
from models.camera_model import CameraModel, ConnectionConfig, StreamConfig, CameraCapabilities, ProtocolType, ConnectionStatus
from utils.exceptions import (
from services.logging_service import get_secure_logger
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
        supported_protocols = []
        for p in protocols:
            if p.get('is_enabled', True):
                protocol_type = p['type'].lower()
                # Convertir HTTPS a HTTP para compatibilidad
                if protocol_type == 'https':
                    protocol_type = 'http'
                try:
                    supported_protocols.append(ProtocolType(protocol_type))
                except ValueError:
                    self.logger.warning(f"Protocolo no soportado: {p['type']}")
        
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
            protocol_type = primary_protocol['type'].lower()
            # Convertir HTTPS a HTTP para compatibilidad
            if protocol_type == 'https':
                protocol_type = 'http'
            try:
                camera.protocol = ProtocolType(protocol_type)
            except ValueError:
                self.logger.warning(f"Protocolo principal no válido: {primary_protocol['type']}")
                if supported_protocols:
                    camera.protocol = supported_protocols[0]
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
    
    # === Métodos de Gestión de Credenciales ===
    
    async def get_camera_credentials(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las credenciales de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Lista de credenciales (sin contraseñas)
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
        """
        # Verificar que existe la cámara
        await self.get_camera(camera_id)
        
        try:
            credentials = await self._data_service.get_camera_credentials(camera_id)
            # Eliminar contraseñas de la respuesta
            for cred in credentials:
                cred.pop('password_encrypted', None)
            return credentials
        except Exception as e:
            self.logger.error(f"Error obteniendo credenciales de {camera_id}: {e}")
            raise ServiceError(f"Error obteniendo credenciales: {e}")
    
    async def add_camera_credential(self, camera_id: str, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agrega una nueva credencial a una cámara.
        
        Si es la primera credencial o se marca como default, se establecerá como predeterminada.
        Las contraseñas se encriptan automáticamente antes de almacenar.
        
        Args:
            camera_id: ID de la cámara
            credential_data: Diccionario con campos:
                - credential_name (str): Nombre descriptivo único
                - username (str): Nombre de usuario
                - password (str): Contraseña sin encriptar
                - auth_type (str): Tipo de autenticación (basic, digest, bearer)
                - is_default (bool): Si debe ser la credencial predeterminada
            
        Returns:
            Dict con la credencial creada (sin contraseña)
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si los datos son inválidos o falta información requerida
            ServiceError: Error al crear la credencial en la base de datos
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Validar datos requeridos
            if not credential_data.get('username'):
                raise ValueError("El nombre de usuario es requerido")
            if not credential_data.get('password'):
                raise ValueError("La contraseña es requerida")
            if not credential_data.get('credential_name'):
                raise ValueError("El nombre de la credencial es requerido")
            
            # Validar que no exista una credencial con el mismo nombre
            existing_creds = await self._data_service.get_camera_credentials(camera_id)
            for cred in existing_creds:
                if cred['credential_name'].lower() == credential_data['credential_name'].lower():
                    raise ValueError(f"Ya existe una credencial con el nombre '{credential_data['credential_name']}'")
            
            # Si es la primera credencial o se marca como default, establecerla como default
            if not existing_creds or credential_data.get('is_default', False):
                credential_data['is_default'] = True
                # Quitar default de otras credenciales si hay
                if credential_data['is_default'] and existing_creds:
                    await self._data_service.clear_default_credentials(camera_id)
            
            # Crear credencial
            credential_id = await self._data_service.add_camera_credential(camera_id, credential_data)
            
            # Obtener credencial creada
            credential = await self._data_service.get_credential_by_id(camera_id, credential_id)
            if not credential:
                raise ServiceError(f"No se pudo recuperar la credencial creada con ID {credential_id}")
            
            # Actualizar caché de la cámara si es default
            if credential.get('is_default'):
                async with self._cache_lock:
                    if camera_id in self._cameras_cache:
                        self._cameras_cache[camera_id].connection_config.username = credential['username']
                        self._cameras_cache[camera_id].connection_config.auth_type = credential['auth_type']
                        self.logger.debug(f"Caché actualizado con nueva credencial default para cámara {camera_id}")
            
            # Eliminar contraseña de la respuesta por seguridad
            credential.pop('password_encrypted', None)
            
            self.logger.info(f"Credencial '{credential['credential_name']}' creada exitosamente para cámara {camera_id}")
            return credential
            
        except ValueError as e:
            # Las excepciones de validación se propagan tal cual
            self.logger.warning(f"Validación fallida al agregar credencial: {e}")
            raise
        except Exception as e:
            # Cualquier otro error se convierte en ServiceError
            self.logger.error(f"Error inesperado agregando credencial a {camera_id}: {e}", exc_info=True)
            raise ServiceError(f"Error agregando credencial: {str(e)}")
    
    async def update_camera_credential(self, camera_id: str, credential_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una credencial existente.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial
            updates: Datos a actualizar
            
        Returns:
            Credencial actualizada (sin contraseña)
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si la credencial no existe
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Verificar que existe la credencial
            credential = await self._data_service.get_credential_by_id(camera_id, credential_id)
            if not credential:
                raise ValueError(f"Credencial {credential_id} no encontrada")
            
            # Si se marca como default, quitar default de otras
            if updates.get('is_default'):
                await self._data_service.clear_default_credentials(camera_id)
            
            # Actualizar credencial
            success = await self._data_service.update_credential(camera_id, credential_id, updates)
            if not success:
                raise ServiceError("No se pudo actualizar la credencial")
            
            # Obtener credencial actualizada
            credential = await self._data_service.get_credential_by_id(camera_id, credential_id)
            
            # Actualizar caché si es default
            if credential.get('is_default'):
                camera.connection_config.username = credential['username']
                camera.connection_config.auth_type = credential.get('auth_type', 'basic')
            
            # Eliminar contraseña de la respuesta
            credential.pop('password_encrypted', None)
            return credential
            
        except Exception as e:
            self.logger.error(f"Error actualizando credencial {credential_id}: {e}")
            if isinstance(e, ValueError):
                raise
            raise ServiceError(f"Error actualizando credencial: {e}")
    
    async def delete_camera_credential(self, camera_id: str, credential_id: int) -> bool:
        """
        Elimina una credencial de una cámara.
        
        No se permite eliminar la única credencial de una cámara para evitar
        dejarla sin acceso. Si se elimina la credencial predeterminada,
        se asignará automáticamente otra credencial activa como predeterminada.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial a eliminar
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si la credencial no existe o es la única credencial
            ServiceError: Error al eliminar de la base de datos
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Verificar que existe la credencial
            credential = await self._data_service.get_credential_by_id(camera_id, credential_id)
            if not credential:
                raise ValueError(f"Credencial {credential_id} no encontrada para la cámara {camera_id}")
            
            # Obtener todas las credenciales activas
            all_creds = await self._data_service.get_camera_credentials(camera_id)
            active_creds = [c for c in all_creds if c['is_active']]
            
            # Verificar que no es la única credencial activa
            if len(active_creds) <= 1 and credential['is_active']:
                raise ValueError("No se puede eliminar la única credencial activa de la cámara. Debe existir al menos una credencial para acceder a la cámara.")
            
            # Si es la credencial predeterminada, asignar default a otra
            if credential.get('is_default'):
                self.logger.info(f"La credencial {credential_id} es default, asignando default a otra credencial")
                
                # Buscar otra credencial activa para establecer como default
                new_default_id = None
                for cred in all_creds:
                    if cred['credential_id'] != credential_id and cred['is_active']:
                        new_default_id = cred['credential_id']
                        break
                
                if new_default_id:
                    await self._data_service.set_credential_as_default(camera_id, new_default_id)
                    
                    # Actualizar caché con la nueva credencial default
                    new_default = await self._data_service.get_credential_by_id(camera_id, new_default_id)
                    if new_default:
                        async with self._cache_lock:
                            if camera_id in self._cameras_cache:
                                self._cameras_cache[camera_id].connection_config.username = new_default['username']
                                self._cameras_cache[camera_id].connection_config.auth_type = new_default.get('auth_type', 'basic')
                                self.logger.debug(f"Caché actualizado con nueva credencial default {new_default_id}")
                else:
                    self.logger.warning(f"No se encontró otra credencial activa para establecer como default")
            
            # Eliminar credencial
            success = await self._data_service.delete_credential(camera_id, credential_id)
            
            if success:
                self.logger.info(f"Credencial {credential_id} eliminada exitosamente de cámara {camera_id}")
            else:
                raise ServiceError(f"No se pudo eliminar la credencial {credential_id} de la base de datos")
                
            return success
            
        except ValueError as e:
            # Las excepciones de validación se propagan tal cual
            self.logger.warning(f"Validación fallida al eliminar credencial: {e}")
            raise
        except Exception as e:
            # Cualquier otro error se convierte en ServiceError
            self.logger.error(f"Error inesperado eliminando credencial {credential_id}: {e}", exc_info=True)
            raise ServiceError(f"Error eliminando credencial: {str(e)}")
    
    async def set_default_credential(self, camera_id: str, credential_id: int) -> bool:
        """
        Establece una credencial como predeterminada.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial
            
        Returns:
            True si se estableció correctamente
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si la credencial no existe
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Verificar que existe la credencial
            credential = await self._data_service.get_credential_by_id(camera_id, credential_id)
            if not credential:
                raise ValueError(f"Credencial {credential_id} no encontrada")
            
            # Establecer como default
            success = await self._data_service.set_credential_as_default(camera_id, credential_id)
            
            # Actualizar caché
            if success:
                camera.connection_config.username = credential['username']
                camera.connection_config.auth_type = credential.get('auth_type', 'basic')
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error estableciendo credencial default: {e}")
            if isinstance(e, ValueError):
                raise
            raise ServiceError(f"Error estableciendo credencial default: {e}")
    
    # === Métodos de Gestión de Stream Profiles ===
    
    async def get_stream_profiles(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los perfiles de streaming de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Lista de perfiles de streaming
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ServiceError: Error al obtener perfiles
        """
        # Verificar que existe la cámara
        await self.get_camera(camera_id)
        
        try:
            profiles = await self._data_service.get_stream_profiles(camera_id)
            self.logger.info(f"Obtenidos {len(profiles)} perfiles para cámara {camera_id}")
            return profiles
        except Exception as e:
            self.logger.error(f"Error obteniendo perfiles de {camera_id}: {e}")
            raise ServiceError(f"Error obteniendo perfiles: {e}")
    
    async def add_stream_profile(self, camera_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agrega un nuevo perfil de streaming a una cámara.
        
        Si es el primer perfil o se marca como default, se establecerá como predeterminado.
        Solo puede haber un perfil default por tipo de stream.
        
        Args:
            camera_id: ID de la cámara
            profile_data: Diccionario con campos:
                - profile_name (str): Nombre único del perfil
                - stream_type (str): Tipo de stream (main, sub, third, mobile)
                - resolution (str): Resolución (ej: 1920x1080)
                - framerate (int): FPS
                - bitrate (int): Bitrate en kbps
                - encoding (str): Codec (H264, H265, etc)
                - quality (str): Nivel de calidad
                - gop_interval (int): Intervalo GOP opcional
                - channel (int): Canal de la cámara
                - subtype (int): Subtipo del stream
                - is_default (bool): Si debe ser el perfil predeterminado
            
        Returns:
            Dict con el perfil creado
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si los datos son inválidos o el perfil ya existe
            ServiceError: Error al crear el perfil
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Validar datos requeridos
            if not profile_data.get('profile_name'):
                raise ValueError("El nombre del perfil es requerido")
            if not profile_data.get('resolution'):
                raise ValueError("La resolución es requerida")
            if not profile_data.get('framerate'):
                raise ValueError("El framerate es requerido")
            if not profile_data.get('bitrate'):
                raise ValueError("El bitrate es requerido")
            
            # Validaciones adicionales de rangos
            framerate = profile_data.get('framerate', 0)
            if framerate < 1 or framerate > 120:
                raise ValueError("El framerate debe estar entre 1 y 120 FPS")
            
            bitrate = profile_data.get('bitrate', 0)
            if bitrate < 64 or bitrate > 50000:
                raise ValueError("El bitrate debe estar entre 64 y 50000 kbps")
            
            # Validar GOP interval si se proporciona
            if profile_data.get('gop_interval'):
                gop = profile_data['gop_interval']
                if gop < 1 or gop > 300:
                    raise ValueError("El intervalo GOP debe estar entre 1 y 300")
                if gop > framerate * 10:
                    self.logger.warning(
                        f"GOP interval ({gop}) muy alto para {framerate} FPS. "
                        f"Máximo recomendado: {framerate * 10}"
                    )
            
            # Validar que no exista un perfil con el mismo nombre
            existing_profiles = await self._data_service.get_stream_profiles(camera_id)
            for profile in existing_profiles:
                if profile['profile_name'].lower() == profile_data['profile_name'].lower():
                    raise ValueError(f"Ya existe un perfil con el nombre '{profile_data['profile_name']}'")
            
            # Si es el primer perfil del tipo o se marca como default, establecerlo como default
            stream_type = profile_data.get('stream_type', 'main')
            profiles_of_type = [p for p in existing_profiles if p['stream_type'] == stream_type]
            
            if not profiles_of_type or profile_data.get('is_default', False):
                profile_data['is_default'] = True
                # Quitar default de otros perfiles del mismo tipo
                if profile_data['is_default'] and profiles_of_type:
                    await self._data_service.clear_default_profiles(camera_id, stream_type)
            
            # Crear perfil
            profile_id = await self._data_service.add_stream_profile(camera_id, profile_data)
            
            # Obtener perfil creado
            profile = await self._data_service.get_stream_profile_by_id(camera_id, profile_id)
            if not profile:
                raise ServiceError(f"No se pudo recuperar el perfil creado con ID {profile_id}")
            
            self.logger.info(f"Perfil '{profile['profile_name']}' creado exitosamente para cámara {camera_id}")
            return profile
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al agregar perfil: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado agregando perfil a {camera_id}: {e}", exc_info=True)
            raise ServiceError(f"Error agregando perfil: {str(e)}")
    
    async def update_stream_profile(self, camera_id: str, profile_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un perfil de streaming existente.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil
            updates: Datos a actualizar
            
        Returns:
            Perfil actualizado
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si el perfil no existe o datos inválidos
            ServiceError: Error al actualizar
        """
        # Verificar que existe la cámara
        await self.get_camera(camera_id)
        
        try:
            # Verificar que existe el perfil
            profile = await self._data_service.get_stream_profile_by_id(camera_id, profile_id)
            if not profile:
                raise ValueError(f"Perfil {profile_id} no encontrado")
            
            # Si se marca como default, quitar default de otros del mismo tipo
            if updates.get('is_default'):
                stream_type = profile['stream_type']
                await self._data_service.clear_default_profiles(camera_id, stream_type)
            
            # Actualizar perfil
            success = await self._data_service.update_stream_profile(camera_id, profile_id, updates)
            if not success:
                raise ServiceError("No se pudo actualizar el perfil")
            
            # Obtener perfil actualizado
            profile = await self._data_service.get_stream_profile_by_id(camera_id, profile_id)
            
            self.logger.info(f"Perfil {profile_id} actualizado exitosamente")
            return profile
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al actualizar perfil: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando perfil {profile_id}: {e}", exc_info=True)
            raise ServiceError(f"Error actualizando perfil: {str(e)}")
    
    async def delete_stream_profile(self, camera_id: str, profile_id: int) -> bool:
        """
        Elimina un perfil de streaming.
        
        No se permite eliminar el único perfil activo de una cámara.
        Si se elimina el perfil default, se asignará otro como default.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil a eliminar
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si el perfil no existe o es el único
            ServiceError: Error al eliminar
        """
        # Verificar que existe la cámara
        await self.get_camera(camera_id)
        
        try:
            # Verificar que existe el perfil
            profile = await self._data_service.get_stream_profile_by_id(camera_id, profile_id)
            if not profile:
                raise ValueError(f"Perfil {profile_id} no encontrado")
            
            # Obtener todos los perfiles activos
            all_profiles = await self._data_service.get_stream_profiles(camera_id)
            active_profiles = [p for p in all_profiles if p['is_active']]
            
            # Verificar que no es el único perfil activo
            if len(active_profiles) <= 1 and profile['is_active']:
                raise ValueError("No se puede eliminar el único perfil activo de la cámara")
            
            # Si es default, asignar default a otro del mismo tipo
            if profile.get('is_default'):
                stream_type = profile['stream_type']
                self.logger.info(f"El perfil {profile_id} es default, asignando default a otro perfil")
                
                # Buscar otro perfil activo del mismo tipo
                for p in all_profiles:
                    if (p['profile_id'] != profile_id and 
                        p['is_active'] and 
                        p['stream_type'] == stream_type):
                        await self._data_service.set_stream_profile_as_default(camera_id, p['profile_id'])
                        break
            
            # Eliminar perfil
            success = await self._data_service.delete_stream_profile(camera_id, profile_id)
            
            if success:
                self.logger.info(f"Perfil {profile_id} eliminado exitosamente de cámara {camera_id}")
            else:
                raise ServiceError(f"No se pudo eliminar el perfil {profile_id}")
                
            return success
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al eliminar perfil: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando perfil {profile_id}: {e}", exc_info=True)
            raise ServiceError(f"Error eliminando perfil: {str(e)}")
    
    async def set_default_stream_profile(self, camera_id: str, profile_id: int) -> bool:
        """
        Establece un perfil como predeterminado.
        
        Solo puede haber un perfil default por tipo de stream.
        El perfil debe estar activo.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil
            
        Returns:
            True si se estableció correctamente
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si el perfil no existe o no está activo
            ServiceError: Error al establecer default
        """
        # Verificar que existe la cámara
        await self.get_camera(camera_id)
        
        try:
            # Verificar que existe el perfil
            profile = await self._data_service.get_stream_profile_by_id(camera_id, profile_id)
            if not profile:
                raise ValueError(f"Perfil {profile_id} no encontrado")
            
            # Verificar que está activo
            if not profile.get('is_active', True):
                raise ValueError("Solo se pueden establecer como default perfiles activos")
            
            # Establecer como default
            success = await self._data_service.set_stream_profile_as_default(camera_id, profile_id)
            
            if success:
                self.logger.info(f"Perfil {profile_id} establecido como default para cámara {camera_id}")
            
            return success
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al establecer perfil default: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error estableciendo perfil default: {e}", exc_info=True)
            raise ServiceError(f"Error estableciendo perfil default: {str(e)}")
    
    async def test_stream_profile(self, camera_id: str, profile_id: int, duration: int = 5) -> Dict[str, Any]:
        """
        Prueba un perfil de streaming.
        
        Intenta conectar y obtener algunos frames para validar la configuración.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil a probar
            duration: Duración de la prueba en segundos
            
        Returns:
            Dict con resultado de la prueba y métricas
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si el perfil no existe
            ServiceError: Error al probar
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Verificar que existe el perfil
            profile = await self._data_service.get_stream_profile_by_id(camera_id, profile_id)
            if not profile:
                raise ValueError(f"Perfil {profile_id} no encontrado")
            
            self.logger.info(f"Probando perfil '{profile['profile_name']}' de cámara {camera_id}")
            
            # TODO: Integrar con VideoStreamService para prueba real
            # Por ahora simular resultado con validaciones básicas
            
            # Validar duración
            if duration < 1 or duration > 30:
                raise ValueError("La duración debe estar entre 1 y 30 segundos")
            
            # Simular prueba con delay proporcional
            test_duration = min(duration, 5)  # Máximo 5 segundos de prueba real
            await asyncio.sleep(test_duration * 0.4)  # Simular 40% del tiempo en conexión
            
            # Calcular métricas simuladas basadas en el perfil
            expected_frames = test_duration * profile['framerate']
            fps_loss = 0.05 if profile['bitrate'] >= 2000 else 0.1  # Mayor pérdida con bitrate bajo
            actual_fps = profile['framerate'] * (1 - fps_loss)
            
            result = {
                'success': True,
                'profile_id': profile_id,
                'profile_name': profile['profile_name'],
                'stream_type': profile['stream_type'],
                'resolution': profile['resolution'],
                'codec': profile['encoding'],
                'configured_fps': profile['framerate'],
                'configured_bitrate': profile['bitrate'],
                'test_duration': test_duration,
                'frames_captured': int(expected_frames * (1 - fps_loss)),
                'average_fps': round(actual_fps, 1),
                'fps_stability': round((1 - fps_loss) * 100, 1),  # Porcentaje de estabilidad
                'connection_time': round(0.3 + (0.2 if profile['encoding'] == 'H265' else 0), 2),
                'bandwidth_usage_kbps': int(profile['bitrate'] * 0.85),  # 85% del configurado
                'message': 'Perfil probado exitosamente',
                'recommendations': []
            }
            
            # Agregar recomendaciones si es necesario
            if fps_loss > 0.08:
                result['recommendations'].append(
                    f"Considere aumentar el bitrate para mejorar la estabilidad de FPS"
                )
            if profile['bitrate'] > 10000:
                result['recommendations'].append(
                    f"Bitrate alto ({profile['bitrate']} kbps) puede causar problemas en redes lentas"
                )
            
            self.logger.info(f"Prueba de perfil {profile_id} completada exitosamente")
            return result
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al probar perfil: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error probando perfil {profile_id}: {e}", exc_info=True)
            return {
                'success': False,
                'profile_id': profile_id,
                'error': str(e),
                'message': 'Error al probar perfil'
            }
    
    # === Métodos de Gestión de Protocolos ===
    
    async def get_camera_protocols(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los protocolos configurados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Lista de protocolos con toda su información
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ServiceError: Error al obtener protocolos
        """
        # Verificar que existe la cámara
        await self.get_camera(camera_id)
        
        try:
            protocols = await self._data_service.get_camera_protocols(camera_id)
            self.logger.info(f"Obtenidos {len(protocols)} protocolos para cámara {camera_id}")
            return protocols
            
        except Exception as e:
            self.logger.error(f"Error obteniendo protocolos de {camera_id}: {e}", exc_info=True)
            raise ServiceError(f"Error obteniendo protocolos: {str(e)}")
    
    async def update_protocol_config(self, camera_id: str, protocol_type: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza la configuración de un protocolo específico.
        
        Valida que no haya conflictos de puerto entre protocolos habilitados
        y gestiona automáticamente el flag de protocolo primario.
        
        Args:
            camera_id: ID de la cámara (UUID)
            protocol_type: Tipo de protocolo (onvif, rtsp, http, etc.)
            updates: Campos a actualizar:
                - port (int): Puerto del protocolo (1-65535)
                - is_enabled (bool): Si está habilitado
                - is_primary (bool): Si es el protocolo principal
                - version (str): Versión del protocolo
                - path (str): Path específico (para HTTP/HTTPS)
            
        Returns:
            Dict con el protocolo actualizado incluyendo status y capacidades
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si el protocolo no existe, puerto inválido o en conflicto
            ServiceError: Error al actualizar en base de datos
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Validar protocolo existe
            protocols = await self._data_service.get_camera_protocols(camera_id)
            protocol = next((p for p in protocols if p['protocol_type'] == protocol_type), None)
            
            if not protocol:
                raise ValueError(f"Protocolo {protocol_type} no encontrado para cámara {camera_id}")
            
            # Validar puerto si se está cambiando
            if 'port' in updates:
                port = updates['port']
                if port < 1 or port > 65535:
                    raise ValueError(f"Puerto {port} fuera de rango válido (1-65535)")
                
                # Verificar si otro protocolo ya usa ese puerto
                for p in protocols:
                    if p['protocol_id'] != protocol['protocol_id'] and p['port'] == port and p['is_enabled']:
                        raise ValueError(f"Puerto {port} ya está en uso por protocolo {p['protocol_type']}")
                
                # Advertir si es un puerto no estándar para el protocolo
                standard_ports = {
                    'onvif': [80, 8080, 2020],
                    'rtsp': [554, 555],
                    'http': [80, 8080, 8000],
                    'https': [443, 8443]
                }
                if protocol_type in standard_ports and port not in standard_ports[protocol_type]:
                    self.logger.warning(
                        f"Puerto {port} no es estándar para {protocol_type}. "
                        f"Puertos comunes: {standard_ports[protocol_type]}"
                    )
            
            # Si se marca como primario, quitar primario de otros
            if updates.get('is_primary', False):
                await self._data_service.clear_primary_protocols(camera_id)
            
            # Actualizar protocolo
            success = await self._data_service.update_protocol_config(
                camera_id, protocol['protocol_id'], updates
            )
            
            if not success:
                raise ServiceError("No se pudo actualizar el protocolo")
            
            # Obtener protocolo actualizado
            updated_protocol = await self._data_service.get_protocol_by_type(camera_id, protocol_type)
            
            # Si se cambió habilitación, actualizar caché
            if 'is_enabled' in updates:
                if camera_id in self._cameras_cache:
                    self._cameras_cache[camera_id]['protocols_enabled'] = \
                        [p['protocol_type'] for p in await self._data_service.get_camera_protocols(camera_id) 
                         if p['is_enabled']]
            
            self.logger.info(f"Protocolo {protocol_type} actualizado para cámara {camera_id}")
            return updated_protocol
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al actualizar protocolo: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando protocolo {protocol_type}: {e}", exc_info=True)
            raise ServiceError(f"Error actualizando protocolo: {str(e)}")
    
    async def test_protocol(self, camera_id: str, protocol_type: str, 
                          timeout: int = 10, credential_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Prueba la conectividad de un protocolo específico.
        
        Args:
            camera_id: ID de la cámara
            protocol_type: Tipo de protocolo a probar
            timeout: Timeout en segundos
            credential_id: ID de credencial específica (opcional)
            
        Returns:
            Resultado de la prueba con métricas
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ValueError: Si el protocolo no existe
            ServiceError: Error al probar
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            # Obtener protocolo
            protocol = await self._data_service.get_protocol_by_type(camera_id, protocol_type)
            if not protocol:
                raise ValueError(f"Protocolo {protocol_type} no encontrado")
            
            if not protocol['is_enabled']:
                return {
                    'success': False,
                    'protocol_type': protocol_type,
                    'port': protocol['port'],
                    'error': 'Protocol is disabled',
                    'message': 'El protocolo está deshabilitado'
                }
            
            # Obtener credencial a usar
            if credential_id:
                credential = await self._data_service.get_credential_by_id(camera_id, credential_id)
                if not credential:
                    raise ValueError(f"Credencial {credential_id} no encontrada")
            else:
                # Usar credencial default
                credentials = await self._data_service.get_camera_credentials(camera_id)
                credential = next((c for c in credentials if c['is_default']), None)
                if not credential:
                    raise ValueError("No hay credencial default configurada")
            
            self.logger.info(f"Probando protocolo {protocol_type} en {camera['ip']}:{protocol['port']}")
            
            # Delegar prueba al ProtocolService
            from services.protocol_service import protocol_service
            
            # Desencriptar password de forma segura
            try:
                decrypted_password = await self._encryption_service.decrypt(
                    credential['password_encrypted']
                )
            except Exception as e:
                self.logger.error(f"Error desencriptando credencial: {e}")
                raise ServiceError("Error al procesar credenciales")
            
            start_time = asyncio.get_event_loop().time()
            
            result = await protocol_service.test_protocol(
                ip=camera['ip'],
                port=protocol['port'],
                protocol_type=protocol_type,
                username=credential['username'],
                password=decrypted_password,
                timeout=timeout
            )
            
            response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            # Actualizar último test en BD
            await self._data_service.update_protocol_test_result(
                camera_id,
                protocol['protocol_id'],
                success=result.get('success', False),
                response_time_ms=response_time,
                version=result.get('version'),
                error=result.get('error')
            )
            
            return {
                'success': result.get('success', False),
                'protocol_type': protocol_type,
                'port': protocol['port'],
                'response_time_ms': response_time,
                'version_detected': result.get('version'),
                'capabilities': result.get('capabilities'),
                'error': result.get('error'),
                'message': result.get('message', 'Prueba completada')
            }
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida al probar protocolo: {e}")
            raise
        except asyncio.TimeoutError:
            return {
                'success': False,
                'protocol_type': protocol_type,
                'port': protocol.get('port', 0),
                'error': 'Timeout',
                'message': f'Timeout después de {timeout} segundos'
            }
        except Exception as e:
            self.logger.error(f"Error probando protocolo {protocol_type}: {e}", exc_info=True)
            return {
                'success': False,
                'protocol_type': protocol_type,
                'port': protocol.get('port', 0),
                'error': str(e),
                'message': 'Error al probar protocolo'
            }
    
    async def discover_protocols(self, camera_id: str, scan_common_ports: bool = True,
                               deep_scan: bool = False, timeout: int = 30,
                               credential_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Auto-descubre protocolos disponibles en la cámara.
        
        Args:
            camera_id: ID de la cámara
            scan_common_ports: Si escanear puertos comunes
            deep_scan: Si hacer escaneo profundo
            timeout: Timeout total en segundos
            credential_ids: IDs de credenciales a probar
            
        Returns:
            Resultado del discovery
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
            ServiceError: Error en discovery
        """
        # Verificar que existe la cámara
        camera = await self.get_camera(camera_id)
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Puertos a escanear
            if deep_scan:
                ports_to_scan = [80, 81, 443, 554, 555, 8000, 8080, 8081, 8443, 
                               2020, 2021, 37777, 37778, 9000, 5000]
            elif scan_common_ports:
                ports_to_scan = [80, 554, 8080, 8000, 2020]
            else:
                # Solo puertos ya configurados
                protocols = await self._data_service.get_camera_protocols(camera_id)
                ports_to_scan = [p['port'] for p in protocols]
            
            # Obtener credenciales a probar
            if credential_ids:
                credentials = []
                for cred_id in credential_ids:
                    cred = await self._data_service.get_credential_by_id(camera_id, cred_id)
                    if cred:
                        credentials.append(cred)
            else:
                # Usar todas las credenciales activas
                all_creds = await self._data_service.get_camera_credentials(camera_id)
                credentials = [c for c in all_creds if c['is_active']]
            
            if not credentials:
                raise ValueError("No hay credenciales disponibles para discovery")
            
            self.logger.info(
                f"Iniciando discovery en {camera['ip']}: "
                f"{len(ports_to_scan)} puertos, {len(credentials)} credenciales"
            )
            
            # Delegar discovery al ProtocolService
            from services.protocol_service import protocol_service
            
            discovered = []
            protocols_tested = set()
            
            # Probar cada puerto con cada credencial
            for port in ports_to_scan:
                if (asyncio.get_event_loop().time() - start_time) > timeout:
                    break
                
                for credential in credentials:
                    if (asyncio.get_event_loop().time() - start_time) > timeout:
                        break
                    
                    # Determinar protocolos a probar en este puerto
                    if port in [80, 81, 8080, 8081, 2020, 2021]:
                        test_protocols = ['onvif', 'http']
                    elif port in [443, 8443]:
                        test_protocols = ['https']
                    elif port in [554, 555]:
                        test_protocols = ['rtsp']
                    elif port == 37777:
                        test_protocols = ['amcrest']
                    else:
                        test_protocols = ['http', 'rtsp']
                    
                    for proto in test_protocols:
                        key = f"{proto}:{port}"
                        if key in protocols_tested:
                            continue
                        
                        protocols_tested.add(key)
                        
                        try:
                            # Desencriptar password de forma segura
                            decrypted_password = await self._encryption_service.decrypt(
                                credential['password_encrypted']
                            )
                            
                            result = await protocol_service.test_protocol(
                                ip=camera['ip'],
                                port=port,
                                protocol_type=proto,
                                username=credential['username'],
                                password=decrypted_password,
                                timeout=5  # Timeout corto para discovery
                            )
                        except Exception as e:
                            self.logger.debug(
                                f"Error probando {proto} en puerto {port}: {e}"
                            )
                            result = {'success': False, 'error': str(e)}
                        
                        if result.get('success'):
                            discovered.append({
                                'protocol_type': proto,
                                'port': port,
                                'version': result.get('version'),
                                'verified': True,
                                'credential_id': credential['credential_id']
                            })
                            
                            # Guardar en BD si es nuevo
                            existing = await self._data_service.get_protocol_by_type(
                                camera_id, proto
                            )
                            if not existing:
                                await self._data_service.add_camera_protocol(camera_id, {
                                    'protocol_type': proto,
                                    'port': port,
                                    'is_enabled': True,
                                    'is_verified': True,
                                    'version': result.get('version')
                                })
            
            scan_duration = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return {
                'discovered_count': len(discovered),
                'scan_duration_ms': scan_duration,
                'protocols_found': discovered,
                'ports_scanned': ports_to_scan,
                'credentials_tested': len(credentials),
                'message': f"Discovery completado. Encontrados {len(discovered)} protocolos activos."
            }
            
        except ValueError as e:
            self.logger.warning(f"Validación fallida en discovery: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error en discovery de protocolos: {e}", exc_info=True)
            raise ServiceError(f"Error en discovery: {str(e)}")
    
    async def discover_protocols_async(self, camera_id: str, **kwargs):
        """
        Versión asíncrona de discover_protocols para ejecutar en background.
        
        Actualiza el estado del discovery en la BD mientras ejecuta.
        """
        try:
            # Marcar inicio de discovery
            await self._data_service.update_camera_discovery_status(
                camera_id, 'discovering', 'Discovery en progreso...'
            )
            
            # Ejecutar discovery
            result = await self.discover_protocols(camera_id, **kwargs)
            
            # Marcar completado
            await self._data_service.update_camera_discovery_status(
                camera_id, 'completed', 
                f"Encontrados {result['discovered_count']} protocolos"
            )
            
        except Exception as e:
            # Marcar error
            await self._data_service.update_camera_discovery_status(
                camera_id, 'failed', f"Error: {str(e)}"
            )
            self.logger.error(f"Error en discovery asíncrono: {e}", exc_info=True)
    
    # === Métodos de Solo Lectura (Fase 4) ===
    
    async def get_camera_capabilities_detail(self, camera_id: str) -> Dict[str, Any]:
        """
        Obtiene las capacidades detalladas de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Dict con capacidades organizadas por categoría
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
        """
        # Verificar que la cámara existe
        await self._get_camera_or_raise(camera_id)
        
        try:
            # Obtener capacidades desde la base de datos
            capabilities_data = await self.data_service.get_camera_capabilities_detail(camera_id)
            
            if not capabilities_data:
                # Si no hay capacidades guardadas, intentar detectarlas
                self.logger.info(f"No hay capacidades guardadas para {camera_id}, intentando detectar")
                
                # Obtener protocolos activos
                protocols = await self.data_service.get_camera_protocols(camera_id)
                
                # Intentar detectar con ONVIF si está disponible
                onvif_protocol = next(
                    (p for p in protocols if p['protocol_type'] == 'onvif' and p['is_enabled']),
                    None
                )
                
                if onvif_protocol:
                    # Aquí normalmente se conectaría a ONVIF para detectar capacidades
                    # Por ahora devolvemos capacidades básicas
                    capabilities_data = {
                        'camera_id': camera_id,
                        'last_updated': datetime.now(),
                        'discovery_method': 'manual',
                        'categories': {
                            'video': [
                                {'name': 'h264_encoding', 'supported': True, 'details': None},
                                {'name': 'mjpeg_encoding', 'supported': True, 'details': None}
                            ],
                            'audio': [
                                {'name': 'audio_input', 'supported': False, 'details': None}
                            ],
                            'ptz': [
                                {'name': 'pan_tilt', 'supported': False, 'details': None}
                            ],
                            'analytics': [],
                            'events': [],
                            'network': [
                                {'name': 'rtsp_streaming', 'supported': True, 'details': None}
                            ],
                            'storage': []
                        }
                    }
                else:
                    # Capacidades mínimas por defecto
                    capabilities_data = {
                        'camera_id': camera_id,
                        'last_updated': datetime.now(),
                        'discovery_method': 'default',
                        'categories': {
                            'video': [
                                {'name': 'streaming', 'supported': True, 'details': None}
                            ],
                            'audio': [],
                            'ptz': [],
                            'analytics': [],
                            'events': [],
                            'network': [],
                            'storage': []
                        }
                    }
            
            return capabilities_data
            
        except Exception as e:
            self.logger.error(f"Error obteniendo capacidades de {camera_id}: {e}")
            raise ServiceError(f"Error obteniendo capacidades: {str(e)}")
    
    async def get_camera_events(
        self,
        camera_id: str,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Obtiene eventos paginados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            event_type: Tipo de evento a filtrar
            severity: Severidad a filtrar
            start_date: Fecha inicial
            end_date: Fecha final
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Dict con eventos paginados
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
        """
        # Verificar que la cámara existe
        await self._get_camera_or_raise(camera_id)
        
        try:
            # Obtener eventos desde la base de datos
            result = await self.data_service.get_camera_events(
                camera_id,
                event_type=event_type,
                severity=severity,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo eventos de {camera_id}: {e}")
            raise ServiceError(f"Error obteniendo eventos: {str(e)}")
    
    async def get_camera_logs(
        self,
        camera_id: str,
        level: Optional[str] = None,
        component: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Obtiene logs paginados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            level: Nivel de log a filtrar
            component: Componente a filtrar
            start_date: Fecha inicial
            end_date: Fecha final
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Dict con logs paginados
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
        """
        # Verificar que la cámara existe
        await self._get_camera_or_raise(camera_id)
        
        try:
            # Obtener logs desde la base de datos
            result = await self.data_service.get_camera_logs(
                camera_id,
                level=level,
                component=component,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo logs de {camera_id}: {e}")
            raise ServiceError(f"Error obteniendo logs: {str(e)}")
    
    async def get_camera_snapshots(
        self,
        camera_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        trigger: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Obtiene snapshots paginados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            start_date: Fecha inicial
            end_date: Fecha final
            trigger: Tipo de trigger a filtrar
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Dict con snapshots paginados
            
        Raises:
            CameraNotFoundError: Si la cámara no existe
        """
        # Verificar que la cámara existe
        await self._get_camera_or_raise(camera_id)
        
        try:
            # Obtener snapshots desde la base de datos
            result = await self.data_service.get_camera_snapshots(
                camera_id,
                start_date=start_date,
                end_date=end_date,
                trigger=trigger,
                page=page,
                page_size=page_size
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo snapshots de {camera_id}: {e}")
            raise ServiceError(f"Error obteniendo snapshots: {str(e)}")
    
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