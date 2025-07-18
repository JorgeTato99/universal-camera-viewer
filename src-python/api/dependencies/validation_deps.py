"""
Dependencies para validaciones complejas.

Estas dependencies se usan para validaciones que requieren
acceso a base de datos o servicios externos.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
import logging

from services.camera_manager_service import camera_manager_service
from api.validators import validate_uuid

logger = logging.getLogger(__name__)


async def validate_camera_exists(camera_id: str) -> str:
    """
    Dependency que valida que una cámara existe.
    
    Args:
        camera_id: ID de la cámara a validar
        
    Returns:
        ID validado si la cámara existe
        
    Raises:
        HTTPException 400: Si el ID no es válido
        HTTPException 404: Si la cámara no existe
    """
    # Primero validar formato UUID
    try:
        camera_id = validate_uuid(camera_id, "ID de cámara")
    except ValueError as e:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Verificar que existe
    try:
        camera = await camera_manager_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        return camera_id
    except Exception as e:
        logger.error(f"Error verificando existencia de cámara {camera_id}: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error verificando cámara"
        )


async def validate_camera_not_exists(ip: str) -> str:
    """
    Dependency que valida que no existe una cámara con la IP dada.
    
    Args:
        ip: Dirección IP a verificar
        
    Returns:
        IP si no existe ninguna cámara con esa dirección
        
    Raises:
        HTTPException 409: Si ya existe una cámara con esa IP
    """
    try:
        cameras = await camera_manager_service.get_all_cameras()
        for camera in cameras:
            if camera.connection_config.ip == ip:
                logger.warning(f"Ya existe una cámara con IP {ip}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe una cámara configurada con la IP {ip}"
                )
        return ip
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando duplicación de IP {ip}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error verificando duplicación"
        )


async def validate_camera_connected(camera_id: str = Depends(validate_camera_exists)) -> str:
    """
    Dependency que valida que una cámara está conectada.
    
    Args:
        camera_id: ID de la cámara (ya validado)
        
    Returns:
        ID si la cámara está conectada
        
    Raises:
        HTTPException 409: Si la cámara no está conectada
    """
    try:
        camera = await camera_manager_service.get_camera(camera_id)
        if not camera.is_connected:
            logger.warning(f"Cámara {camera_id} no está conectada")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La cámara debe estar conectada para esta operación"
            )
        return camera_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando conexión de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error verificando conexión"
        )


async def validate_camera_disconnected(camera_id: str = Depends(validate_camera_exists)) -> str:
    """
    Dependency que valida que una cámara está desconectada.
    
    Args:
        camera_id: ID de la cámara (ya validado)
        
    Returns:
        ID si la cámara está desconectada
        
    Raises:
        HTTPException 409: Si la cámara está conectada
    """
    try:
        camera = await camera_manager_service.get_camera(camera_id)
        if camera.is_connected:
            logger.warning(f"Cámara {camera_id} está conectada")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La cámara debe estar desconectada para esta operación"
            )
        return camera_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando desconexión de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error verificando desconexión"
        )


async def validate_credential_exists(
    camera_id: str,
    credential_id: int
) -> tuple[str, int]:
    """
    Dependency que valida que una credencial existe para una cámara.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Returns:
        Tupla (camera_id, credential_id) si existe
        
    Raises:
        HTTPException 404: Si no existe
    """
    # Validar cámara
    camera_id = await validate_camera_exists(camera_id)
    
    # Validar credencial
    try:
        credentials = await camera_manager_service.get_camera_credentials(camera_id)
        if not any(c['credential_id'] == credential_id for c in credentials):
            logger.warning(f"Credencial {credential_id} no encontrada para cámara {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credencial {credential_id} no encontrada"
            )
        return camera_id, credential_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando credencial {credential_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error verificando credencial"
        )


class RateLimitDependency:
    """
    Dependency para limitar la tasa de requests.
    
    Útil para endpoints costosos como escaneo o discovery.
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # IP -> lista de timestamps
    
    async def __call__(self, request) -> None:
        """
        Verifica el rate limit para la IP del cliente.
        
        Args:
            request: Request de FastAPI
            
        Raises:
            HTTPException 429: Si se excede el límite
        """
        from datetime import datetime, timedelta
        
        client_ip = request.client.host
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Limpiar requests antiguos
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip]
                if ts > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Verificar límite
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit excedido para IP {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Límite excedido: máximo {self.max_requests} requests por {self.window_seconds} segundos"
            )
        
        # Registrar request
        self.requests[client_ip].append(now)


# Instancias de rate limiters para diferentes endpoints
scan_rate_limit = RateLimitDependency(max_requests=5, window_seconds=300)  # 5 escaneos por 5 minutos
discovery_rate_limit = RateLimitDependency(max_requests=10, window_seconds=60)  # 10 discoveries por minuto
snapshot_rate_limit = RateLimitDependency(max_requests=30, window_seconds=60)  # 30 snapshots por minuto