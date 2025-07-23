"""
Modelos de respuesta para la API remota de MediaMTX.

Define las estructuras de datos que devuelve el servidor MediaMTX remoto
al interactuar con su API REST.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class RemoteCameraResponse(BaseModel):
    """
    Respuesta del servidor MediaMTX al crear/obtener una cámara.
    
    Basado en la respuesta real documentada en mediamtx_integration.md
    """
    id: str = Field(..., description="ID único de la cámara en el servidor remoto")
    name: str = Field(..., description="Nombre de la cámara")
    description: Optional[str] = Field(None, description="Descripción de la cámara")
    rtsp_address: str = Field(..., description="Dirección RTSP original de la cámara")
    status: str = Field(default="OFFLINE", description="Estado actual: OFFLINE, ONLINE, ERROR")
    last_seen_at: Optional[datetime] = Field(None, description="Última vez vista activa")
    
    # URLs generadas por el servidor
    publish_url: str = Field(..., description="URL RTMP para publicar el stream")
    webrtc_url: str = Field(..., description="URL WebRTC para visualización")
    agent_command: str = Field(..., description="Comando FFmpeg completo para el agente")
    
    # Metadatos adicionales
    json_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Datos JSON adicionales de la cámara"
    )
    
    # Timestamps
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    class Config:
        """Configuración del modelo."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RemoteCameraRequest(BaseModel):
    """
    Request para crear/actualizar una cámara en el servidor remoto.
    
    Estructura esperada por la API según mediamtx_integration.md
    """
    name: str = Field(..., description="Nombre de la cámara")
    description: Optional[str] = Field(None, description="Descripción de la cámara")
    rtsp_address: str = Field(..., description="Dirección RTSP de la cámara")
    json_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales"
    )
    
    class Config:
        """Configuración del modelo."""
        schema_extra = {
            "example": {
                "name": "Cámara Principal",
                "description": "Cámara de entrada principal",
                "rtsp_address": "rtsp://192.168.1.100:554/stream1",
                "json_data": {
                    "features": {
                        "motion_detection": True,
                        "night_vision": True,
                        "two_way_audio": False
                    },
                    "fps": 30,
                    "location": {
                        "building": "A",
                        "floor": 1,
                        "zone": "entrance"
                    },
                    "model": "Dahua IP Camera",
                    "resolution": "1920x1080"
                }
            }
        }


class RemoteCameraListResponse(BaseModel):
    """
    Respuesta al listar cámaras del servidor remoto.
    """
    cameras: List[RemoteCameraResponse] = Field(
        default_factory=list,
        description="Lista de cámaras"
    )
    total: int = Field(0, description="Total de cámaras")
    page: Optional[int] = Field(1, description="Página actual")
    per_page: Optional[int] = Field(100, description="Elementos por página")


class RemoteCameraUpdate(BaseModel):
    """
    Request para actualizar parcialmente una cámara.
    """
    name: Optional[str] = Field(None, description="Nuevo nombre")
    description: Optional[str] = Field(None, description="Nueva descripción")
    rtsp_address: Optional[str] = Field(None, description="Nueva dirección RTSP")
    json_data: Optional[Dict[str, Any]] = Field(None, description="Nuevos metadatos")


class CameraMapping(BaseModel):
    """
    Mapeo entre cámara local y remota para sincronización.
    """
    local_camera_id: str = Field(..., description="ID de la cámara local")
    remote_camera_id: str = Field(..., description="ID en el servidor remoto")
    server_id: int = Field(..., description="ID del servidor MediaMTX")
    
    # URLs remotas
    publish_url: str = Field(..., description="URL RTMP para publicación")
    webrtc_url: str = Field(..., description="URL WebRTC para visualización")
    agent_command: str = Field(..., description="Comando FFmpeg")
    
    # Estado
    is_active: bool = Field(True, description="Si el mapeo está activo")
    last_sync: datetime = Field(
        default_factory=datetime.utcnow,
        description="Última sincronización"
    )
    
    class Config:
        """Configuración del modelo."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }