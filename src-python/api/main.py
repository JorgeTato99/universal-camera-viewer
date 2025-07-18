"""
Aplicación principal FastAPI
Universal Camera Viewer API v0.8.2
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config import settings
from api.middleware import setup_middleware
from api.dependencies import cleanup_services, create_response

# Importar routers
from routers import cameras, scanner, config, streaming
from routers.cameras_v2 import router as cameras_v2_router
from routers.stream_profiles import router as stream_profiles_router
from api.routers.publishing import router as publishing_router
from api.routers.publishing_config import router as publishing_config_router
from services.camera_manager_service import camera_manager_service
from websocket.handlers.publishing_handler import get_publishing_ws_handler

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file) if settings.log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación."""
    # Startup
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    logger.info(f"Servidor en http://{settings.host}:{settings.port}")
    logger.info(f"Documentación en http://{settings.host}:{settings.port}/docs")
    
    # Inicializar servicios
    try:
        await camera_manager_service.initialize()
        logger.info("CameraManagerService inicializado correctamente")
        
        # Inicializar WebSocket handler para publicación
        ws_handler = get_publishing_ws_handler()
        await ws_handler.start()
        logger.info("PublishingWebSocketHandler iniciado correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando servicios: {e}")
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")
    
    # Detener WebSocket handler
    try:
        ws_handler = get_publishing_ws_handler()
        await ws_handler.stop()
        logger.info("PublishingWebSocketHandler detenido")
    except Exception as e:
        logger.error(f"Error deteniendo WebSocket handler: {e}")
    
    await cleanup_services()
    logger.info("Aplicación cerrada correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST y WebSocket para Universal Camera Viewer",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar middlewares
setup_middleware(app)


# === Endpoints básicos ===

@app.get("/")
async def root():
    """
    Endpoint raíz de la API.
    
    Proporciona información básica sobre el servicio y enlaces útiles.
    
    Returns:
        Dict con nombre, versión, estado y enlaces de documentación
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "api": settings.api_prefix
    }


@app.get("/health")
async def health_check():
    """
    Endpoint de verificación de salud del servicio.
    
    Utilizado para monitoreo y balanceadores de carga para verificar
    que el servicio está funcionando correctamente.
    
    Returns:
        Respuesta con estado 'healthy' y versión actual
    """
    return create_response(
        success=True,
        data={
            "status": "healthy",
            "version": settings.app_version
        }
    )


@app.get(f"{settings.api_prefix}/info")
async def api_info():
    """
    Información detallada de la API.
    
    Proporciona información sobre endpoints disponibles, protocolos
    soportados y capacidades del sistema.
    
    Returns:
        Respuesta con endpoints, características y capacidades
    """
    return create_response(
        success=True,
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "endpoints": {
                "cameras": f"{settings.api_prefix}/cameras",
                "scanner": f"{settings.api_prefix}/scanner",
                "streaming": "/ws/stream",
                "events": "/ws/events",
                "config": f"{settings.api_prefix}/config"
            },
            "features": {
                "protocols": ["ONVIF", "RTSP", "HTTP"],
                "streaming": ["WebSocket", "Base64"],
                "formats": ["JPEG", "PNG", "WebP"]
            }
        }
    )


@app.get(f"{settings.api_prefix}/system/info")
async def system_info():
    """
    Información del sistema y recursos.
    
    Proporciona estadísticas del sistema operativo, uso de recursos
    (CPU, memoria, disco) y métricas de la API.
    
    Returns:
        Respuesta con información de plataforma, recursos y métricas
    """
    import platform
    import psutil
    
    return create_response(
        success=True,
        data={
            "platform": {
                "system": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "python_version": platform.python_version()
            },
            "resources": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available_mb": round(psutil.virtual_memory().available / 1024 / 1024),
                "disk_usage_percent": psutil.disk_usage("/").percent
            },
            "api": {
                "version": settings.app_version,
                "uptime_seconds": 0,  # TODO: Implementar contador de uptime
                "active_connections": 0,  # TODO: Obtener de ConnectionManager
                "active_streams": 0  # TODO: Obtener de VideoStreamService
            }
        }
    )


# === Manejo global de errores ===

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Manejador personalizado para errores 404.
    
    Captura todas las rutas no encontradas y devuelve una respuesta
    consistente en formato JSON.
    
    Args:
        request: Objeto Request de FastAPI con información de la petición
        exc: Excepción HTTPException con detalles del error
        
    Returns:
        JSONResponse con mensaje de error y la ruta solicitada
    """
    return JSONResponse(
        status_code=404,
        content=create_response(
            success=False,
            error="Endpoint no encontrado",
            data={"path": str(request.url.path)}
        )
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """
    Manejador personalizado para errores 500.
    
    Captura errores internos del servidor, los registra para debugging
    y devuelve una respuesta genérica sin exponer detalles sensibles.
    
    Args:
        request: Objeto Request de FastAPI con información de la petición
        exc: Excepción del servidor con detalles del error
        
    Returns:
        JSONResponse con mensaje de error genérico
    """
    logger.error(f"Error interno: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_response(
            success=False,
            error="Error interno del servidor"
        )
    )


# === Incluir routers ===

app.include_router(cameras.router, prefix=settings.api_prefix)
app.include_router(scanner.router, prefix=settings.api_prefix)
app.include_router(config.router, prefix=settings.api_prefix)

# API v2 routers
app.include_router(cameras_v2_router, prefix="/api/v2")
app.include_router(stream_profiles_router, prefix="/api/v2")

# Publishing routers (para MediaMTX)
app.include_router(publishing_router)
app.include_router(publishing_config_router)

# WebSocket routers (sin prefijo API)
app.include_router(streaming.router, prefix="/ws")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )