"""
Middlewares para FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import logging
from typing import Callable
from .config import settings

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware para medir tiempos de respuesta."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log solo para requests lentas
        if process_time > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para manejo global de errores."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}", exc_info=True)
            return Response(
                content=f"Internal server error: {str(e)}",
                status_code=500
            )


def setup_middleware(app: FastAPI) -> None:
    """
    Configurar todos los middlewares de la aplicación.
    
    Args:
        app: Instancia de FastAPI
    """
    
    # CORS - Permitir conexiones desde el frontend React
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Trusted Host - Seguridad básica
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # En producción, especificar hosts permitidos
    )
    
    # Timing - Métricas de rendimiento
    app.add_middleware(TimingMiddleware)
    
    # Error Handling - Manejo global de errores
    app.add_middleware(ErrorHandlingMiddleware)
    
    logger.info("Middlewares configurados correctamente")