"""
Schemas de request para endpoints de perfiles de streaming.

Modelos Pydantic para validar datos de entrada en perfiles de stream.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from api.validators import validate_timeout


class StreamQuality(str, Enum):
    """Calidad de stream."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BEST = "best"
    AUTO = "auto"


class VideoCodec(str, Enum):
    """Codecs de video soportados."""
    H264 = "h264"
    H265 = "h265"
    MJPEG = "mjpeg"
    AUTO = "auto"


class StreamProtocol(str, Enum):
    """Protocolos de streaming."""
    RTSP = "rtsp"
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"


class CreateStreamProfileRequest(BaseModel):
    """Request para crear un perfil de streaming."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del perfil")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del perfil")
    quality: StreamQuality = Field(..., description="Calidad del stream")
    codec: Optional[VideoCodec] = Field(VideoCodec.AUTO, description="Codec de video")
    protocol: Optional[StreamProtocol] = Field(StreamProtocol.RTSP, description="Protocolo preferido")
    resolution: Optional[str] = Field(None, description="Resolución (ej: 1920x1080)")
    fps: Optional[int] = Field(None, ge=1, le=60, description="FPS objetivo")
    bitrate: Optional[int] = Field(None, ge=100, le=50000, description="Bitrate en kbps")
    audio_enabled: bool = Field(True, description="Habilitar audio")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Configuraciones personalizadas")
    
    @validator('name')
    def validate_name(cls, v):
        """Valida el nombre del perfil."""
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        # No permitir caracteres especiales peligrosos
        forbidden_chars = ['/', '\\', '..', '<', '>', '|', ':', '*', '?', '"']
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f"El nombre no puede contener: {char}")
        return v.strip()
    
    @validator('resolution')
    def validate_resolution(cls, v):
        """Valida formato de resolución."""
        if v is not None:
            # Formato esperado: WIDTHxHEIGHT (ej: 1920x1080)
            parts = v.lower().split('x')
            if len(parts) != 2:
                raise ValueError("Resolución debe tener formato WIDTHxHEIGHT (ej: 1920x1080)")
            try:
                width = int(parts[0])
                height = int(parts[1])
                if width < 160 or width > 7680:  # 8K max
                    raise ValueError("Ancho debe estar entre 160 y 7680")
                if height < 120 or height > 4320:  # 8K max
                    raise ValueError("Alto debe estar entre 120 y 4320")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError("Resolución debe contener solo números")
                raise
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alta Calidad",
                "description": "Perfil para visualización en alta calidad",
                "quality": "high",
                "codec": "h264",
                "protocol": "rtsp",
                "resolution": "1920x1080",
                "fps": 25,
                "bitrate": 4000,
                "audio_enabled": True,
                "custom_settings": {
                    "gop": 50,
                    "profile": "main"
                }
            }
        }


class UpdateStreamProfileRequest(BaseModel):
    """Request para actualizar un perfil de streaming."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nuevo nombre")
    description: Optional[str] = Field(None, max_length=500, description="Nueva descripción")
    quality: Optional[StreamQuality] = Field(None, description="Nueva calidad")
    codec: Optional[VideoCodec] = Field(None, description="Nuevo codec")
    protocol: Optional[StreamProtocol] = Field(None, description="Nuevo protocolo")
    resolution: Optional[str] = Field(None, description="Nueva resolución")
    fps: Optional[int] = Field(None, ge=1, le=60, description="Nuevos FPS")
    bitrate: Optional[int] = Field(None, ge=100, le=50000, description="Nuevo bitrate")
    audio_enabled: Optional[bool] = Field(None, description="Estado de audio")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Nuevas configuraciones")
    
    @validator('name')
    def validate_name(cls, v):
        """Valida el nombre del perfil."""
        if v is not None:
            if not v.strip():
                raise ValueError("El nombre no puede estar vacío")
            forbidden_chars = ['/', '\\', '..', '<', '>', '|', ':', '*', '?', '"']
            for char in forbidden_chars:
                if char in v:
                    raise ValueError(f"El nombre no puede contener: {char}")
        return v.strip() if v else v
    
    @validator('resolution')
    def validate_resolution(cls, v):
        """Valida formato de resolución."""
        if v is not None:
            parts = v.lower().split('x')
            if len(parts) != 2:
                raise ValueError("Resolución debe tener formato WIDTHxHEIGHT")
            try:
                width = int(parts[0])
                height = int(parts[1])
                if width < 160 or width > 7680:
                    raise ValueError("Ancho debe estar entre 160 y 7680")
                if height < 120 or height > 4320:
                    raise ValueError("Alto debe estar entre 120 y 4320")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError("Resolución debe contener solo números")
                raise
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Calidad Media Actualizada",
                "quality": "medium",
                "resolution": "1280x720",
                "fps": 15,
                "bitrate": 2000
            }
        }


class ApplyProfileRequest(BaseModel):
    """Request para aplicar un perfil a una cámara."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    persist: bool = Field(True, description="Guardar como perfil predeterminado")
    test_duration: Optional[int] = Field(None, ge=1, le=300, description="Duración de prueba en segundos")
    
    @validator('test_duration')
    def validate_test_duration(cls, v):
        """Valida duración de prueba."""
        if v is not None:
            return validate_timeout(v, min_timeout=1, max_timeout=300)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "persist": True,
                "test_duration": 30
            }
        }


class CloneProfileRequest(BaseModel):
    """Request para clonar un perfil."""
    
    new_name: str = Field(..., min_length=1, max_length=100, description="Nombre del nuevo perfil")
    new_description: Optional[str] = Field(None, max_length=500, description="Descripción del nuevo perfil")
    
    @validator('new_name')
    def validate_name(cls, v):
        """Valida el nombre del perfil."""
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        forbidden_chars = ['/', '\\', '..', '<', '>', '|', ':', '*', '?', '"']
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f"El nombre no puede contener: {char}")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_name": "Perfil Clonado",
                "new_description": "Copia del perfil original con ajustes"
            }
        }


class TestProfileRequest(BaseModel):
    """Request para probar un perfil."""
    
    camera_id: str = Field(..., description="ID de la cámara para prueba")
    duration: int = Field(10, ge=1, le=60, description="Duración de la prueba en segundos")
    collect_metrics: bool = Field(True, description="Recolectar métricas durante la prueba")
    
    @validator('duration')
    def validate_duration(cls, v):
        """Valida duración de prueba."""
        return validate_timeout(v, min_timeout=1, max_timeout=60)
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "duration": 10,
                "collect_metrics": True
            }
        }