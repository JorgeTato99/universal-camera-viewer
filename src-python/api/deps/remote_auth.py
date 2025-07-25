"""
Dependencias para autenticación con servidores MediaMTX remotos.

Proporciona decoradores y validaciones para endpoints que requieren
autenticación previa con un servidor remoto específico.
"""

from functools import wraps
from typing import Callable, Optional, Any
from fastapi import HTTPException, status
import inspect

from services.mediamtx.auth_service import get_auth_service
from services.logging_service import get_secure_logger
from utils.exceptions import ValidationError


logger = get_secure_logger("api.deps.remote_auth")


class RemoteAuthError(HTTPException):
    """Excepción específica para errores de autenticación remota."""
    
    def __init__(
        self,
        detail: str,
        server_id: Optional[int] = None,
        headers: Optional[dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )
        self.server_id = server_id


def requires_remote_auth(server_id_param: str = "server_id"):
    """
    Decorator que verifica autenticación con servidor remoto.
    
    Verifica que exista un token JWT válido para el servidor especificado
    antes de permitir la ejecución del endpoint.
    
    Args:
        server_id_param: Nombre del parámetro que contiene el server_id
        
    Usage:
        @router.post("/publish")
        @requires_remote_auth()
        async def publish_to_remote(server_id: int, ...):
            ...
            
    El decorator intentará:
    1. Obtener el server_id del parámetro especificado
    2. Verificar que existe un token válido
    3. Si no hay token, lanzar 401 con mensaje descriptivo
    4. Si el token es inválido, intentar renovarlo
    5. Inyectar el token en los kwargs como 'auth_token'
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener server_id de los parámetros
            server_id = kwargs.get(server_id_param)
            
            if server_id is None:
                # Buscar en args si es necesario
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                
                if server_id_param in params:
                    idx = params.index(server_id_param)
                    if idx < len(args):
                        server_id = args[idx]
            
            if server_id is None:
                logger.error(f"No se pudo obtener {server_id_param} para verificar autenticación")
                raise ValidationError(f"Parámetro {server_id_param} requerido")
            
            # Obtener servicio de autenticación
            auth_service = get_auth_service()
            
            # Verificar si existe token válido
            token = await auth_service.get_valid_token(server_id)
            
            if not token:
                # No hay token válido
                token_info = await auth_service.get_token_info(server_id)
                
                if token_info:
                    # Hay info pero el token expiró
                    raise RemoteAuthError(
                        detail="Token de autenticación expirado. Por favor, autentique nuevamente.",
                        server_id=server_id
                    )
                else:
                    # No hay autenticación previa
                    raise RemoteAuthError(
                        detail="No está autenticado con este servidor. Por favor, autentique primero.",
                        server_id=server_id
                    )
            
            # Inyectar token en kwargs para uso del endpoint
            kwargs['auth_token'] = token
            
            # Llamar función original
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator


async def get_remote_auth_headers(server_id: int) -> dict:
    """
    Obtiene headers de autenticación para un servidor remoto.
    
    Args:
        server_id: ID del servidor
        
    Returns:
        Dict con headers de autorización
        
    Raises:
        RemoteAuthError: Si no hay token válido
    """
    auth_service = get_auth_service()
    
    headers = await auth_service.get_auth_headers(server_id)
    
    if not headers:
        raise RemoteAuthError(
            detail="No hay autenticación válida para este servidor",
            server_id=server_id
        )
    
    return headers


async def validate_and_refresh_token(server_id: int, api_url: str) -> bool:
    """
    Valida y refresca el token si es necesario.
    
    Args:
        server_id: ID del servidor
        api_url: URL de la API del servidor
        
    Returns:
        True si el token es válido o se refrescó exitosamente
        
    Note:
        MediaMTX actualmente no soporta refresh tokens, por lo que
        esta función solo valida. El refresco debe ser manual.
    """
    auth_service = get_auth_service()
    
    # Validar token actual
    is_valid, error_msg = await auth_service.validate_token(server_id, api_url)
    
    if is_valid:
        return True
    
    logger.warning(f"Token inválido para servidor {server_id}: {error_msg}")
    
    # TODO: Implementar refresco cuando MediaMTX lo soporte
    # Por ahora, retornar False para forzar re-autenticación manual
    
    return False