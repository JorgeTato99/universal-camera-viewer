"""
Ejemplo de uso de Rate Limiting en routers.

Este archivo documenta cómo aplicar rate limiting a diferentes tipos de endpoints.
NO es parte de la aplicación principal, solo sirve como referencia.
"""

from fastapi import APIRouter, Request
from api.dependencies import create_response
from api.dependencies.rate_limit import (
    rate_limit,
    read_limit,
    write_limit,
    camera_operation_limit,
    critical_operation_limit,
    websocket_rate_limit,
    check_rate_limit
)

# Crear router de ejemplo
router = APIRouter(
    prefix="/example",
    tags=["rate-limit-examples"],
)


# === Ejemplos de uso ===

@router.get("/basic-read")
@read_limit()  # Aplica límite de lectura: 100/min (1000/min en dev)
async def example_read():
    """Ejemplo de endpoint de lectura con rate limit estándar."""
    return create_response(
        success=True,
        data={"message": "Lectura exitosa"}
    )


@router.post("/basic-write")
@write_limit()  # Aplica límite de escritura: 10/min (100/min en dev)
async def example_write():
    """Ejemplo de endpoint de escritura con rate limit estándar."""
    return create_response(
        success=True,
        data={"message": "Escritura exitosa"}
    )


@router.post("/custom-limit")
@rate_limit("custom", "5/hour")  # Límite personalizado
async def example_custom():
    """Ejemplo con límite personalizado."""
    return create_response(
        success=True,
        data={"message": "Operación con límite personalizado"}
    )


@router.post("/camera-connect")
@camera_operation_limit("connect")  # 5/minute - para conexiones costosas
async def example_camera_connect():
    """Ejemplo de operación de cámara con límite estricto."""
    return create_response(
        success=True,
        data={"message": "Conexión de cámara simulada"}
    )


@router.post("/network-scan")
@critical_operation_limit()  # 1/minute - operaciones muy costosas
async def example_critical_operation():
    """Ejemplo de operación crítica con límite muy estricto."""
    return create_response(
        success=True,
        data={"message": "Operación crítica ejecutada"}
    )


@router.get("/check-limit")
async def example_check_limit(request: Request):
    """
    Ejemplo de verificación manual de rate limit.
    
    Útil cuando necesitas lógica condicional basada en límites.
    """
    # Verificar si el usuario puede hacer una operación de lectura
    allowed, info = await check_rate_limit(request, "read")
    
    if not allowed:
        return create_response(
            success=False,
            error="Rate limit cercano al límite",
            data={
                "limit_info": info,
                "suggestion": "Intente más tarde"
            }
        )
    
    # Si está permitido, ejecutar operación
    return create_response(
        success=True,
        data={
            "message": "Operación permitida",
            "remaining_requests": info["remaining"] if info else "unlimited"
        }
    )


# === Ejemplo de WebSocket con rate limiting ===

@router.websocket("/ws-example")
@websocket_rate_limit("websocket_connect")  # 20/hour
async def example_websocket(websocket):
    """
    Ejemplo de WebSocket con rate limiting.
    
    El decorador rechazará conexiones que excedan el límite.
    """
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        pass


# === Múltiples decoradores ===

@router.post("/multi-limit")
@write_limit()  # Primero aplica límite de escritura
@rate_limit("special_operation", "2/hour")  # Luego límite adicional más estricto
async def example_multiple_limits():
    """
    Ejemplo con múltiples límites.
    
    Se aplican AMBOS límites, el más restrictivo prevalece.
    """
    return create_response(
        success=True,
        data={"message": "Operación con múltiples límites"}
    )


# === Headers de respuesta ===

@router.get("/response-headers")
@read_limit()
async def example_headers():
    """
    Ejemplo mostrando headers de rate limit.
    
    La respuesta incluirá automáticamente:
    - X-RateLimit-Limit: Límite total
    - X-RateLimit-Remaining: Peticiones restantes
    - X-RateLimit-Reset: Timestamp de reset
    - X-RateLimit-Window: Ventana de tiempo
    
    En caso de exceder límite (429):
    - Retry-After: Segundos hasta poder reintentar
    """
    return create_response(
        success=True,
        data={
            "message": "Revisa los headers de respuesta",
            "headers_info": {
                "X-RateLimit-Limit": "Límite total de peticiones",
                "X-RateLimit-Remaining": "Peticiones restantes",
                "X-RateLimit-Reset": "Unix timestamp cuando se resetea",
                "X-RateLimit-Window": "Ventana de tiempo en segundos"
            }
        }
    )


# === Documentación de configuración ===

"""
CONFIGURACIÓN DE RATE LIMITS
===========================

1. Archivo de configuración: src-python/config/rate_limit_settings.yaml

2. Límites predefinidos:
   - global: 1000/hour (protección DoS general)
   - read: 100/minute (operaciones GET)
   - write: 10/minute (POST, PUT, DELETE)
   - camera_connect: 5/minute (conexión a cámaras)
   - network_scan: 1/minute (escaneo de red)
   - stream_start: 10/minute (iniciar streaming)
   - websocket_connect: 20/hour (nuevas conexiones WS)

3. Modificadores por ambiente:
   - development: x10 (límites 10 veces más altos)
   - production: x1 (límites normales)

4. IPs confiables (bypass completo):
   - 127.0.0.1
   - ::1

5. Paths excluidos:
   - /health
   - /metrics
   - /docs
   - /redoc
   - /openapi.json

6. Storage:
   - Actualmente: Memoria local
   - TODO: Migrar a Redis para múltiples workers

7. Logging:
   - Cada bloqueo se loguea con detalle
   - Estadísticas agregadas cada minuto

8. Respuesta 429:
   {
     "success": false,
     "error": "Mensaje personalizado según el límite",
     "error_code": "RATE_LIMIT_EXCEEDED",
     "detail": {
       "limit": 100,
       "remaining": 0,
       "reset_at": "2024-01-23T12:30:00Z",
       "retry_after": 45
     }
   }
"""