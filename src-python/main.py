#!/usr/bin/env python
"""
Script principal para ejecutar el servidor FastAPI desde src-python.

Este archivo evita problemas con rutas relativas al ejecutar
directamente desde el directorio src-python.
"""

import uvicorn
import sys
from api.config import settings
from logging_config import configure_logging

# Configurar event loop para Windows antes de cualquier uso de asyncio
if sys.platform == 'win32':
    from utils.async_helpers import setup_windows_event_loop
    setup_windows_event_loop()


def main():
    """Función principal para ejecutar el servidor."""
    # Configurar filtros de logging
    configure_logging()
    
    print(f"[STARTING] {settings.app_name} v{settings.app_version}")
    print(f"[SERVER] http://{settings.host}:{settings.port}")
    print(f"[DOCS] http://{settings.host}:{settings.port}/docs")
    print(f"[RELOAD] {'Enabled' if settings.reload else 'Disabled'}")
    print("-" * 50)
    
    # En Windows, forzar loop_type para uvicorn
    loop = "uvloop" if sys.platform != "win32" else "asyncio"
    
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        loop=loop
    )


if __name__ == "__main__":
    main()