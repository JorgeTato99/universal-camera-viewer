"""
Schemas de response para endpoints de perfiles de streaming.

Modelos para estructurar las respuestas de perfiles de stream.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProfileStatus(str, Enum):
    """Estado del perfil."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"


class CustomProfileSettings(BaseModel):
    """Configuraciones personalizadas de perfil de streaming."""
    gop: Optional[int] = Field(None, description="Group of pictures size")
    profile: Optional[str] = Field(None, description="H264 profile (baseline, main, high)")
    level: Optional[str] = Field(None, description="H264 level")
    preset: Optional[str] = Field(None, description="Encoding preset")
    tune: Optional[str] = Field(None, description="Encoding tune option")
    keyframe_interval: Optional[int] = Field(None, description="Intervalo de keyframes")
    b_frames: Optional[int] = Field(None, description="Número de B-frames")
    ref_frames: Optional[int] = Field(None, description="Número de frames de referencia")
    
    class Config:
        extra = 'allow'  # Permitir campos adicionales


class ProfileTestMetrics(BaseModel):
    """Métricas recolectadas durante la prueba de un perfil."""
    avg_fps: float = Field(..., description="FPS promedio")
    avg_bitrate_kbps: float = Field(..., description="Bitrate promedio en kbps")
    dropped_frames: int = Field(..., description="Frames perdidos")
    latency_ms: float = Field(..., description="Latencia en milisegundos")
    cpu_usage_percent: float = Field(..., description="Uso de CPU en porcentaje")
    memory_usage_mb: float = Field(..., description="Uso de memoria en MB")
    packet_loss_percent: Optional[float] = Field(None, description="Porcentaje de pérdida de paquetes")
    jitter_ms: Optional[float] = Field(None, description="Jitter en milisegundos")
    quality_score: Optional[float] = Field(None, description="Score de calidad 0-100")


class StreamProfileInfo(BaseModel):
    """Información básica de un perfil de streaming."""
    
    profile_id: str = Field(..., description="ID único del perfil")
    name: str = Field(..., description="Nombre del perfil")
    description: Optional[str] = Field(None, description="Descripción")
    quality: str = Field(..., description="Calidad del stream")
    is_default: bool = Field(..., description="Si es el perfil por defecto")
    is_system: bool = Field(..., description="Si es un perfil del sistema")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Última actualización")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "prof_123e4567",
                "name": "Alta Calidad",
                "description": "Perfil para visualización en alta calidad",
                "quality": "high",
                "is_default": False,
                "is_system": False,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T15:45:00Z"
            }
        }


class StreamProfileDetailResponse(BaseModel):
    """Detalles completos de un perfil de streaming."""
    
    profile_id: str = Field(..., description="ID único del perfil")
    name: str = Field(..., description="Nombre del perfil")
    description: Optional[str] = Field(None, description="Descripción")
    quality: str = Field(..., description="Calidad del stream")
    codec: str = Field(..., description="Codec de video")
    protocol: str = Field(..., description="Protocolo de streaming")
    resolution: Optional[str] = Field(None, description="Resolución")
    fps: Optional[int] = Field(None, description="FPS")
    bitrate: Optional[int] = Field(None, description="Bitrate en kbps")
    audio_enabled: bool = Field(..., description="Audio habilitado")
    custom_settings: CustomProfileSettings = Field(..., description="Configuraciones adicionales")
    is_default: bool = Field(..., description="Si es el perfil por defecto")
    is_system: bool = Field(..., description="Si es un perfil del sistema")
    cameras_using: int = Field(..., description="Número de cámaras usando este perfil")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Última actualización")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "prof_123e4567",
                "name": "Alta Calidad",
                "description": "Perfil optimizado para visualización HD",
                "quality": "high",
                "codec": "h264",
                "protocol": "rtsp",
                "resolution": "1920x1080",
                "fps": 25,
                "bitrate": 4000,
                "audio_enabled": True,
                "custom_settings": {
                    "gop": 50,
                    "profile": "main",
                    "level": "4.0"
                },
                "is_default": False,
                "is_system": False,
                "cameras_using": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T15:45:00Z"
            }
        }


class ProfileListResponse(BaseModel):
    """Respuesta con lista de perfiles."""
    
    total: int = Field(..., description="Total de perfiles")
    profiles: List[StreamProfileInfo] = Field(..., description="Lista de perfiles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "profiles": [
                    {
                        "profile_id": "prof_123",
                        "name": "Alta Calidad",
                        "description": "HD 1080p",
                        "quality": "high",
                        "is_default": False,
                        "is_system": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": None
                    }
                ]
            }
        }


class ProfileApplicationResult(BaseModel):
    """Resultado de aplicar un perfil a una cámara."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    profile_id: str = Field(..., description="ID del perfil aplicado")
    success: bool = Field(..., description="Si se aplicó exitosamente")
    status: ProfileStatus = Field(..., description="Estado actual")
    message: Optional[str] = Field(None, description="Mensaje informativo")
    stream_url: Optional[str] = Field(None, description="URL del stream si está activo")
    error: Optional[str] = Field(None, description="Error si falló")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "profile_id": "prof_123",
                "success": True,
                "status": "active",
                "message": "Perfil aplicado exitosamente",
                "stream_url": "rtsp://192.168.1.100:554/stream1",
                "error": None
            }
        }


class ProfileTestResult(BaseModel):
    """Resultado de prueba de un perfil."""
    
    profile_id: str = Field(..., description="ID del perfil probado")
    camera_id: str = Field(..., description="ID de la cámara de prueba")
    success: bool = Field(..., description="Si la prueba fue exitosa")
    duration_seconds: float = Field(..., description="Duración de la prueba")
    metrics: Optional[ProfileTestMetrics] = Field(None, description="Métricas recolectadas")
    issues: List[str] = Field(..., description="Problemas detectados")
    recommendations: List[str] = Field(..., description="Recomendaciones")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "prof_123",
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "success": True,
                "duration_seconds": 10.5,
                "metrics": {
                    "avg_fps": 24.8,
                    "avg_bitrate_kbps": 3950,
                    "dropped_frames": 2,
                    "latency_ms": 120,
                    "cpu_usage_percent": 15.5,
                    "memory_usage_mb": 45.2
                },
                "issues": [],
                "recommendations": [
                    "El FPS actual está ligeramente por debajo del objetivo"
                ]
            }
        }


class ProfileStatistics(BaseModel):
    """Estadísticas de uso de un perfil."""
    
    profile_id: str = Field(..., description="ID del perfil")
    total_cameras: int = Field(..., description="Total de cámaras usando el perfil")
    active_streams: int = Field(..., description="Streams activos con este perfil")
    total_usage_hours: float = Field(..., description="Horas totales de uso")
    avg_performance_score: float = Field(..., ge=0, le=100, description="Puntuación promedio")
    common_issues: Dict[str, int] = Field(..., description="Problemas comunes y frecuencia")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "prof_123",
                "total_cameras": 5,
                "active_streams": 3,
                "total_usage_hours": 1250.5,
                "avg_performance_score": 87.5,
                "common_issues": {
                    "high_latency": 12,
                    "dropped_frames": 5,
                    "connection_lost": 2
                }
            }
        }


class ProfileCompatibilityResponse(BaseModel):
    """Respuesta de compatibilidad de perfil con cámara."""
    
    profile_id: str = Field(..., description="ID del perfil")
    camera_id: str = Field(..., description="ID de la cámara")
    is_compatible: bool = Field(..., description="Si el perfil es compatible")
    compatibility_score: float = Field(..., ge=0, le=100, description="Puntuación de compatibilidad")
    supported_features: List[str] = Field(..., description="Características soportadas")
    unsupported_features: List[str] = Field(..., description="Características no soportadas")
    warnings: List[str] = Field(..., description="Advertencias")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "prof_123",
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_compatible": True,
                "compatibility_score": 85.0,
                "supported_features": [
                    "h264_codec",
                    "1080p_resolution",
                    "rtsp_protocol",
                    "audio_stream"
                ],
                "unsupported_features": [
                    "h265_codec"
                ],
                "warnings": [
                    "La cámara podría no alcanzar los 25 FPS solicitados"
                ]
            }
        }


class DefaultProfileResponse(BaseModel):
    """Respuesta con perfiles por defecto del sistema."""
    
    total_defaults: int = Field(..., description="Total de perfiles por defecto")
    quality_profiles: Dict[str, StreamProfileInfo] = Field(..., description="Perfiles por calidad")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_defaults": 4,
                "quality_profiles": {
                    "low": {
                        "profile_id": "default_low",
                        "name": "Baja Calidad",
                        "description": "Optimizado para bajo ancho de banda",
                        "quality": "low",
                        "is_default": True,
                        "is_system": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": None
                    },
                    "high": {
                        "profile_id": "default_high",
                        "name": "Alta Calidad",
                        "description": "Máxima calidad disponible",
                        "quality": "high",
                        "is_default": True,
                        "is_system": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": None
                    }
                }
            }
        }