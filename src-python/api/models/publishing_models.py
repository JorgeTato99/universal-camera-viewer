"""
Modelos Pydantic para endpoints de publicación.

Define las estructuras de request/response para la API REST.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.publishing import PublishStatus, PublishErrorType
from models.publishing.metrics_models import PublishMetrics


class StartPublishRequest(BaseModel):
    """Request para iniciar publicación."""
    camera_id: str = Field(..., description="ID de la cámara")
    force_restart: bool = Field(
        default=False,
        description="Forzar reinicio si ya está publicando"
    )


class StopPublishRequest(BaseModel):
    """Request para detener publicación."""
    camera_id: str = Field(..., description="ID de la cámara")


class PublishStatusResponse(BaseModel):
    """Response con estado de publicación."""
    camera_id: str
    status: PublishStatus
    publish_path: Optional[str] = None
    uptime_seconds: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    metrics: Optional[PublishMetrics] = Field(None, description="Métricas actuales de la publicación")


class PublishListResponse(BaseModel):
    """Response con lista de publicaciones activas."""
    total: int
    active: int
    items: List[PublishStatusResponse]


class MediaMTXConfigRequest(BaseModel):
    """Request para configurar MediaMTX."""
    mediamtx_url: str = Field(..., description="URL del servidor MediaMTX")
    api_enabled: bool = Field(default=True)
    api_port: int = Field(default=9997)
    username: Optional[str] = Field(None, description="Usuario para auth")
    password: Optional[str] = Field(None, description="Contraseña para auth")
    use_tcp: bool = Field(default=True, description="Forzar transporte TCP")