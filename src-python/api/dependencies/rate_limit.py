"""
Dependencias y decoradores para rate limiting en endpoints específicos.

Este módulo proporciona decoradores fáciles de usar para aplicar
rate limiting a endpoints individuales con límites personalizados.
"""

import logging
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.middleware.rate_limit import (
    get_client_identifier,
    rate_limit_config,
    rate_limit_stats,
    rate_limit_storage
)

logger = logging.getLogger(__name__)


# === Limiter con configuración personalizada ===

# Crear limiter que usa nuestra función de identificación
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[]  # No aplicar límites por defecto
)


# === Decoradores de Rate Limiting ===

def rate_limit(limit_name: str, custom_limit: Optional[str] = None):
    """
    Decorador para aplicar rate limiting a un endpoint específico.
    
    Args:
        limit_name: Nombre del límite en la configuración (e.g., 'read', 'camera_connect')
        custom_limit: Límite personalizado opcional (e.g., '5/minute')
        
    Uso:
        @router.get("/cameras")
        @rate_limit("read")
        async def list_cameras():
            pass
            
        @router.post("/scan")
        @rate_limit("network_scan", "2/hour")  # Override del config
        async def scan_network():
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Obtener límite de configuración o usar custom
        if custom_limit:
            limit_str = custom_limit
        else:
            limit_str = rate_limit_config.get_limit(limit_name)
            
        if not limit_str:
            # Si no hay límite configurado, retornar función sin modificar
            logger.warning(f"No rate limit configured for '{limit_name}'")
            return func
        
        # Log del límite aplicado
        logger.debug(f"Applying rate limit '{limit_name}': {limit_str} to {func.__name__}")
        
        # Aplicar decorador de slowapi
        decorated = limiter.limit(limit_str)(func)
        
        # Agregar metadata para logging
        decorated._rate_limit_name = limit_name
        decorated._rate_limit_str = limit_str
        
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            """Wrapper que agrega logging y métricas."""
            client_ip = get_client_identifier(request)
            
            # Verificar si es IP confiable
            if rate_limit_config.is_trusted_ip(client_ip):
                logger.debug(f"Trusted IP {client_ip} bypassing limit '{limit_name}'")
                return await func(request, *args, **kwargs)
            
            try:
                # Ejecutar función decorada
                result = await decorated(request, *args, **kwargs)
                
                # Registrar petición exitosa
                await rate_limit_stats.record_request(client_ip, blocked=False)
                
                return result
                
            except HTTPException as e:
                if e.status_code == 429:
                    # Rate limit excedido - log detallado
                    logger.warning(
                        f"Rate limit exceeded: "
                        f"IP={client_ip}, "
                        f"Endpoint={request.url.path}, "
                        f"Method={request.method}, "
                        f"Limit={limit_name} ({limit_str})"
                    )
                    
                    # Registrar bloqueo
                    await rate_limit_stats.record_request(
                        client_ip, 
                        blocked=True,
                        limit_name=limit_name
                    )
                    
                    # Personalizar mensaje de error
                    e.detail = {
                        "success": False,
                        "error": rate_limit_config.get_message(limit_name),
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "limit_type": limit_name
                    }
                    
                raise
                
        return wrapper
    
    return decorator


# === Decoradores específicos para operaciones comunes ===

def read_limit(custom_limit: Optional[str] = None):
    """
    Rate limit para operaciones de lectura (GET).
    
    Límite por defecto: 100/minute (1000/minute en desarrollo)
    """
    return rate_limit("read", custom_limit)


def write_limit(custom_limit: Optional[str] = None):
    """
    Rate limit para operaciones de escritura (POST, PUT, DELETE).
    
    Límite por defecto: 10/minute (100/minute en desarrollo)
    """
    return rate_limit("write", custom_limit)


def camera_operation_limit(operation: str = "connect"):
    """
    Rate limit para operaciones de cámara.
    
    Args:
        operation: Tipo de operación ('connect', 'stream_start', 'test_connection')
    """
    limit_map = {
        "connect": "camera_connect",
        "stream": "stream_start",
        "test": "test_connection"
    }
    
    limit_name = limit_map.get(operation, "camera_connect")
    return rate_limit(limit_name)


def critical_operation_limit():
    """
    Rate limit para operaciones críticas (escaneo de red, etc).
    
    Aplica los límites más estrictos.
    """
    return rate_limit("network_scan")


# === Decorador para WebSocket ===

def websocket_rate_limit(limit_name: str = "websocket_connect"):
    """
    Rate limit especial para conexiones WebSocket.
    
    WebSocket requiere manejo diferente porque no usa HTTPException.
    """
    def decorator(func: Callable) -> Callable:
        limit_str = rate_limit_config.get_limit(limit_name)
        
        if not limit_str:
            return func
        
        @wraps(func)
        async def wrapper(websocket, *args, **kwargs):
            """Wrapper para WebSocket con rate limiting."""
            # Obtener IP del cliente
            client_ip = websocket.client.host if websocket.client else "unknown"
            
            # Verificar si es IP confiable
            if rate_limit_config.is_trusted_ip(client_ip):
                return await func(websocket, *args, **kwargs)
            
            # Verificar límite manualmente
            try:
                from api.middleware.rate_limit import rate_limit_storage
                
                key = f"{limit_name}:{client_ip}"
                window = _parse_window(limit_str)
                count, reset_time = await rate_limit_storage.increment(key, window)
                limit = _parse_limit(limit_str)
                
                if count > limit:
                    # Log detallado
                    logger.warning(
                        f"WebSocket rate limit exceeded: "
                        f"IP={client_ip}, "
                        f"Limit={limit_name} ({limit_str}), "
                        f"Count={count}/{limit}"
                    )
                    
                    # Registrar bloqueo
                    await rate_limit_stats.record_request(
                        client_ip,
                        blocked=True,
                        limit_name=limit_name
                    )
                    
                    # Rechazar conexión
                    await websocket.close(
                        code=1008,  # Policy Violation
                        reason=rate_limit_config.get_message(limit_name)
                    )
                    return
                
                # Registrar petición exitosa
                await rate_limit_stats.record_request(client_ip, blocked=False)
                
                # Continuar con la conexión
                return await func(websocket, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in WebSocket rate limit: {e}")
                # En caso de error, permitir conexión
                return await func(websocket, *args, **kwargs)
        
        return wrapper
    
    return decorator


# === Utilidades auxiliares ===

def _parse_limit(limit_str: str) -> int:
    """Extrae el número de peticiones del string de límite."""
    try:
        count, _ = limit_str.split('/')
        return int(count)
    except:
        return 100


def _parse_window(limit_str: str) -> int:
    """Extrae la ventana de tiempo en segundos."""
    try:
        _, period = limit_str.split('/')
        
        multipliers = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        for unit, mult in multipliers.items():
            if unit in period:
                return mult
                
        return 60  # Default: 1 minuto
    except:
        return 60


# === Funciones de utilidad para verificación manual ===

async def check_rate_limit(
    request: Request, 
    limit_name: str
) -> tuple[bool, Optional[dict]]:
    """
    Verifica manualmente si se ha excedido un rate limit.
    
    Útil para lógica condicional basada en límites.
    
    Args:
        request: Request de FastAPI
        limit_name: Nombre del límite a verificar
        
    Returns:
        Tupla de (permitido, info_dict)
    """
    client_ip = get_client_identifier(request)
    
    if rate_limit_config.is_trusted_ip(client_ip):
        return True, None
    
    limit_str = rate_limit_config.get_limit(limit_name)
    if not limit_str:
        return True, None
    
    try:
        key = f"{limit_name}:{client_ip}"
        count = await rate_limit_storage.get_count(key)
        limit = _parse_limit(limit_str)
        
        allowed = count < limit
        
        info = {
            "limit": limit,
            "current": count,
            "remaining": max(0, limit - count),
            "allowed": allowed
        }
        
        return allowed, info
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return True, None


async def reset_rate_limit(client_ip: str, limit_name: str) -> bool:
    """
    Resetea manualmente un rate limit para un cliente.
    
    Útil para casos especiales o testing.
    
    Args:
        client_ip: IP del cliente
        limit_name: Nombre del límite
        
    Returns:
        True si se reseteó exitosamente
    """
    try:
        key = f"{limit_name}:{client_ip}"
        await rate_limit_storage.reset(key)
        logger.info(f"Rate limit reset: IP={client_ip}, Limit={limit_name}")
        return True
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        return False