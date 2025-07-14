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
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")
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
    """Endpoint raíz."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "api": settings.api_prefix
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return create_response(
        success=True,
        data={
            "status": "healthy",
            "version": settings.app_version
        }
    )


@app.get(f"{settings.api_prefix}/info")
async def api_info():
    """Información de la API."""
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
    """Información del sistema."""
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
    """Manejador para rutas no encontradas."""
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
    """Manejador para errores internos."""
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