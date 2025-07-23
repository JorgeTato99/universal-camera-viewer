"""
Cliente API para operaciones con cámaras en servidores MediaMTX remotos.

Extiende la funcionalidad base para proporcionar operaciones CRUD
específicas para la gestión de cámaras remotas.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.mediamtx.api_base import MediaMTXAPIBase
from services.mediamtx.remote_models import (
    RemoteCameraResponse,
    RemoteCameraRequest,
    RemoteCameraListResponse,
    RemoteCameraUpdate,
    CameraMapping
)
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.logging_service import get_secure_logger
from utils.exceptions import (
    ServiceError,
    MediaMTXAPIError,
    ValidationError
)
from utils.sanitizers import sanitize_url


logger = get_secure_logger("services.mediamtx.api_client")


class MediaMTXAPIClient(MediaMTXAPIBase):
    """
    Cliente para operaciones CRUD de cámaras en MediaMTX remoto.
    
    Proporciona métodos para:
    - Crear cámaras remotas
    - Actualizar configuración
    - Eliminar cámaras
    - Listar y buscar cámaras
    - Mapear cámaras locales a remotas
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Garantiza singleton thread-safe."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el cliente API."""
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self.logger = logger
        self._db_service = get_mediamtx_db_service()
        self._camera_mappings: Dict[str, CameraMapping] = {}
        self._initialized = True
    
    async def create_camera(
        self,
        server_id: int,
        camera_data: RemoteCameraRequest
    ) -> RemoteCameraResponse:
        """
        Crea una nueva cámara en el servidor remoto.
        
        Args:
            server_id: ID del servidor MediaMTX
            camera_data: Datos de la cámara a crear
            
        Returns:
            RemoteCameraResponse con los datos de la cámara creada
            
        Raises:
            ValidationError: Si los datos son inválidos
            MediaMTXAPIError: Si la API devuelve error
            ServiceError: Si hay error de servicio
        """
        # Obtener información del servidor
        server = await self._db_service.get_server_by_id(server_id)
        if not server:
            raise ValidationError(f"Servidor {server_id} no encontrado")
        
        if not server['api_enabled']:
            raise ServiceError(
                f"API deshabilitada para servidor {server['server_name']}",
                error_code="API_DISABLED"
            )
        
        self.logger.info(
            f"Creando cámara '{camera_data.name}' en servidor {server['server_name']}"
        )
        
        # Realizar petición
        try:
            response_data = await self.post(
                endpoint='api/v1/cameras',
                server_id=server_id,
                base_url=server['api_url'],
                data=camera_data.dict(exclude_none=True)
            )
            
            # Parsear respuesta
            camera_response = RemoteCameraResponse(**response_data)
            
            self.logger.info(
                f"Cámara creada exitosamente - ID: {camera_response.id}, "
                f"Publish URL: {sanitize_url(camera_response.publish_url)}"
            )
            
            return camera_response
            
        except MediaMTXAPIError as e:
            # Re-lanzar errores de API con contexto
            self.logger.error(f"Error creando cámara: {str(e)}")
            raise
            
        except Exception as e:
            self.logger.error(f"Error inesperado creando cámara: {str(e)}")
            raise ServiceError(
                f"Error creando cámara: {str(e)}",
                error_code="CAMERA_CREATE_ERROR"
            )
    
    async def update_camera(
        self,
        server_id: int,
        camera_id: str,
        update_data: RemoteCameraUpdate
    ) -> RemoteCameraResponse:
        """
        Actualiza una cámara existente en el servidor remoto.
        
        Args:
            server_id: ID del servidor MediaMTX
            camera_id: ID de la cámara remota
            update_data: Datos a actualizar
            
        Returns:
            RemoteCameraResponse con los datos actualizados
            
        Raises:
            ValidationError: Si los datos son inválidos
            MediaMTXAPIError: Si la API devuelve error
        """
        # Obtener información del servidor
        server = await self._db_service.get_server_by_id(server_id)
        if not server:
            raise ValidationError(f"Servidor {server_id} no encontrado")
        
        self.logger.info(
            f"Actualizando cámara {camera_id} en servidor {server['server_name']}"
        )
        
        # Realizar petición
        response_data = await self.put(
            endpoint=f'api/v1/cameras/{camera_id}',
            server_id=server_id,
            base_url=server['api_url'],
            data=update_data.dict(exclude_none=True)
        )
        
        # Parsear respuesta
        camera_response = RemoteCameraResponse(**response_data)
        
        self.logger.info(f"Cámara {camera_id} actualizada exitosamente")
        
        return camera_response
    
    async def delete_camera(
        self,
        server_id: int,
        camera_id: str
    ) -> bool:
        """
        Elimina una cámara del servidor remoto.
        
        Args:
            server_id: ID del servidor MediaMTX
            camera_id: ID de la cámara remota
            
        Returns:
            True si se eliminó exitosamente
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            MediaMTXAPIError: Si la API devuelve error
        """
        # Obtener información del servidor
        server = await self._db_service.get_server_by_id(server_id)
        if not server:
            raise ValidationError(f"Servidor {server_id} no encontrado")
        
        self.logger.info(
            f"Eliminando cámara {camera_id} de servidor {server['server_name']}"
        )
        
        try:
            await self.delete(
                endpoint=f'api/v1/cameras/{camera_id}',
                server_id=server_id,
                base_url=server['api_url']
            )
            
            self.logger.info(f"Cámara {camera_id} eliminada exitosamente")
            
            # Limpiar mapeo local si existe
            for local_id, mapping in list(self._camera_mappings.items()):
                if mapping.remote_camera_id == camera_id:
                    del self._camera_mappings[local_id]
                    self.logger.debug(f"Mapeo local eliminado para cámara {local_id}")
            
            return True
            
        except MediaMTXAPIError as e:
            if e.status_code == 404:
                self.logger.warning(f"Cámara {camera_id} no encontrada en servidor")
                return True  # Ya no existe, consideramos exitoso
            raise
    
    async def get_camera(
        self,
        server_id: int,
        camera_id: str
    ) -> Optional[RemoteCameraResponse]:
        """
        Obtiene información de una cámara específica.
        
        Args:
            server_id: ID del servidor MediaMTX
            camera_id: ID de la cámara remota
            
        Returns:
            RemoteCameraResponse o None si no existe
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            ServiceError: Si hay error de servicio
        """
        # Obtener información del servidor
        server = await self._db_service.get_server_by_id(server_id)
        if not server:
            raise ValidationError(f"Servidor {server_id} no encontrado")
        
        self.logger.debug(
            f"Obteniendo cámara {camera_id} de servidor {server['server_name']}"
        )
        
        try:
            response_data = await self.get(
                endpoint=f'api/v1/cameras/{camera_id}',
                server_id=server_id,
                base_url=server['api_url']
            )
            
            return RemoteCameraResponse(**response_data)
            
        except MediaMTXAPIError as e:
            if e.status_code == 404:
                self.logger.debug(f"Cámara {camera_id} no encontrada")
                return None
            raise
    
    async def list_cameras(
        self,
        server_id: int,
        page: int = 1,
        per_page: int = 100
    ) -> RemoteCameraListResponse:
        """
        Lista todas las cámaras del servidor remoto.
        
        Args:
            server_id: ID del servidor MediaMTX
            page: Página a obtener (1-based)
            per_page: Elementos por página
            
        Returns:
            RemoteCameraListResponse con la lista de cámaras
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            ServiceError: Si hay error de servicio
        """
        # Obtener información del servidor
        server = await self._db_service.get_server_by_id(server_id)
        if not server:
            raise ValidationError(f"Servidor {server_id} no encontrado")
        
        self.logger.info(
            f"Listando cámaras de servidor {server['server_name']} "
            f"(página {page}, {per_page} por página)"
        )
        
        # Realizar petición
        response_data = await self.get(
            endpoint='api/v1/cameras',
            server_id=server_id,
            base_url=server['api_url'],
            params={
                'page': page,
                'per_page': per_page
            }
        )
        
        # La API devuelve directamente la lista en 'cameras'
        cameras_data = response_data.get('cameras', [])
        
        # Crear lista de respuestas
        cameras = [RemoteCameraResponse(**cam) for cam in cameras_data]
        
        response = RemoteCameraListResponse(
            cameras=cameras,
            total=len(cameras),  # TODO: La API debería devolver el total real
            page=page,
            per_page=per_page
        )
        
        self.logger.info(f"Obtenidas {len(cameras)} cámaras del servidor")
        
        return response
    
    async def map_local_to_remote(
        self,
        local_camera_id: str,
        server_id: int,
        remote_camera_response: RemoteCameraResponse
    ) -> CameraMapping:
        """
        Crea un mapeo entre cámara local y remota.
        
        Args:
            local_camera_id: ID de la cámara local
            server_id: ID del servidor MediaMTX
            remote_camera_response: Respuesta del servidor remoto
            
        Returns:
            CameraMapping con el mapeo creado
        """
        mapping = CameraMapping(
            local_camera_id=local_camera_id,
            remote_camera_id=remote_camera_response.id,
            server_id=server_id,
            publish_url=remote_camera_response.publish_url,
            webrtc_url=remote_camera_response.webrtc_url,
            agent_command=remote_camera_response.agent_command,
            is_active=True,
            last_sync=datetime.utcnow()
        )
        
        # Guardar en cache local
        self._camera_mappings[local_camera_id] = mapping
        
        self.logger.info(
            f"Mapeo creado: Local {local_camera_id} -> "
            f"Remoto {remote_camera_response.id}"
        )
        
        return mapping
    
    def get_camera_mapping(
        self,
        local_camera_id: str
    ) -> Optional[CameraMapping]:
        """
        Obtiene el mapeo de una cámara local.
        
        Args:
            local_camera_id: ID de la cámara local
            
        Returns:
            CameraMapping o None si no existe
        """
        return self._camera_mappings.get(local_camera_id)
    
    async def sync_camera_status(
        self,
        server_id: int,
        camera_id: str
    ) -> Optional[str]:
        """
        Sincroniza el estado de una cámara remota.
        
        Args:
            server_id: ID del servidor MediaMTX
            camera_id: ID de la cámara remota
            
        Returns:
            Estado actual de la cámara o None si no existe
        """
        camera = await self.get_camera(server_id, camera_id)
        if camera:
            return camera.status
        return None


# Instancia singleton
_api_client: Optional[MediaMTXAPIClient] = None


def get_mediamtx_api_client() -> MediaMTXAPIClient:
    """
    Obtiene la instancia singleton del cliente API.
    
    Returns:
        MediaMTXAPIClient singleton
    """
    global _api_client
    
    if _api_client is None:
        _api_client = MediaMTXAPIClient()
        
    return _api_client