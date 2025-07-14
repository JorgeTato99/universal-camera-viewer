#!/usr/bin/env python3
"""
Script para iniciar el backend Python como servidor HTTP/WebSocket
para comunicación con Tauri.
"""

import sys
import os
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

# Importar presenters y servicios
from presenters import get_main_presenter
from services.video.video_stream_service import VideoStreamService

app = FastAPI(title="Universal Camera Viewer Backend")

# Configurar CORS para permitir comunicación con Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints API
@app.get("/api/health")
async def health_check():
    """Verifica que el backend esté funcionando."""
    return {"status": "ok", "service": "Universal Camera Viewer Backend"}

@app.post("/api/camera/connect")
async def connect_camera(camera_id: str, ip: str, protocol: str):
    """Conecta a una cámara."""
    presenter = get_main_presenter()
    # TODO: Implementar conexión a través del presenter
    return {"status": "connecting", "camera_id": camera_id}

@app.get("/api/camera/stream/{camera_id}")
async def get_stream(camera_id: str):
    """Obtiene el stream de una cámara."""
    service = VideoStreamService()
    # TODO: Implementar obtención de stream
    return {"camera_id": camera_id, "stream_url": f"/stream/{camera_id}"}

if __name__ == "__main__":
    # Iniciar servidor en puerto 8080
    uvicorn.run(app, host="127.0.0.1", port=8080)