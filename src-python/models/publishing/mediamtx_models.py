"""
Modelos de datos para la API de MediaMTX.

Define las estructuras esperadas en las respuestas de la API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(Enum):
    """Tipos de fuente en MediaMTX."""
    RTSP = "rtsp"
    RTMP = "rtmp"
    HLS = "hls"
    WEBRTC = "webrtc"
    SRT = "srt"


class PathState(Enum):
    """Estados de un path."""
    READY = "ready"
    NOT_READY = "notReady"


class PathSource(BaseModel):
    """Información de la fuente de un path."""
    type: SourceType
    id: str


class PathReader(BaseModel):
    """Información de un lector/consumidor."""
    type: str
    id: str


class PathInfo(BaseModel):
    """
    Información completa de un path en MediaMTX.
    
    Representa un stream activo con su fuente y lectores.
    """
    name: str
    source: Optional[PathSource] = None
    ready: bool = False
    readyTime: Optional[datetime] = None
    readers: List[PathReader] = Field(default_factory=list)
    bytesReceived: int = 0
    bytesSent: int = 0
    
    @property
    def reader_count(self) -> int:
        """Número de lectores activos."""
        return len(self.readers)
    
    @property
    def is_active(self) -> bool:
        """Verifica si el path está activo."""
        return self.ready and self.source is not None


class PathList(BaseModel):
    """Lista de paths desde la API."""
    items: Dict[str, PathInfo] = Field(default_factory=dict)
    
    @property
    def paths(self) -> List[PathInfo]:
        """Convierte a lista de PathInfo."""
        return list(self.items.values())
    
    @property
    def count(self) -> int:
        """Número total de paths."""
        return len(self.items)