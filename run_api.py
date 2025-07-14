#!/usr/bin/env python
"""
Script para ejecutar el servidor FastAPI
"""

import sys
import os
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent / "src-python"))

if __name__ == "__main__":
    # Cambiar al directorio src-python
    os.chdir(Path(__file__).parent / "src-python")
    
    # Importar y ejecutar
    import uvicorn
    from api.config import settings
    
    print(f"[STARTING] {settings.app_name} v{settings.app_version}")
    print(f"[SERVER] http://{settings.host}:{settings.port}")
    print(f"[DOCS] http://{settings.host}:{settings.port}/docs")
    print(f"[RELOAD] {'Enabled' if settings.reload else 'Disabled'}")
    print("-" * 50)
    
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )