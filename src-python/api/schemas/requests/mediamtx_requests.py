"""
Schemas de request para endpoints de MediaMTX.

Estos modelos validan los datos de entrada para las operaciones
relacionadas con métricas, historial, viewers y paths de MediaMTX.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class MetricTimeRange(str, Enum):
    """Rangos de tiempo predefinidos para consultas de métricas."""
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    CUSTOM = "custom"


class PublicationStatus(str, Enum):
    """Estados posibles de una publicación."""
    IDLE = "idle"
    STARTING = "starting"
    PUBLISHING = "publishing"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class TerminationReason(str, Enum):
    """Razones de terminación de una publicación."""
    COMPLETED = "completed"
    USER_STOPPED = "user_stopped"
    ERROR = "error"
    SERVER_SHUTDOWN = "server_shutdown"
    CAMERA_DISCONNECTED = "camera_disconnected"


class ViewerProtocol(str, Enum):
    """Protocolos soportados para viewers."""
    RTSP = "RTSP"
    RTMP = "RTMP"
    HLS = "HLS"
    WEBRTC = "WebRTC"
    SRT = "SRT"


class PathSourceType(str, Enum):
    """Tipos de fuente para paths MediaMTX."""
    PUBLISHER = "publisher"
    REDIRECT = "redirect"
    RPI_CAMERA = "rpiCamera"
    RTSP = "rtsp"
    RTMP = "rtmp"
    HLS = "hls"
    UDP = "udp"
    WEBRTC = "webrtc"


# === Requests de Métricas ===

class GetMetricsRequest(BaseModel):
    """Request para obtener métricas de publicación."""
    
    time_range: MetricTimeRange = Field(
        MetricTimeRange.LAST_HOUR,
        description="Rango de tiempo para las métricas"
    )
    start_time: Optional[datetime] = Field(
        None,
        description="Tiempo de inicio para rango custom"
    )
    end_time: Optional[datetime] = Field(
        None,
        description="Tiempo de fin para rango custom"
    )
    include_viewers: bool = Field(
        False,
        description="Incluir estadísticas de viewers"
    )
    aggregate_interval: Optional[str] = Field(
        None,
        description="Intervalo de agregación (1m, 5m, 1h, etc.)"
    )
    
    @validator('start_time', 'end_time')
    def validate_custom_range(cls, v, values):
        """Valida que se proporcionen ambas fechas para rango custom."""
        if values.get('time_range') == MetricTimeRange.CUSTOM:
            if not v:
                raise ValueError("start_time y end_time son requeridos para rango CUSTOM")
        return v


class ExportMetricsRequest(BaseModel):
    """Request para exportar métricas."""
    
    format: str = Field(
        "csv",
        pattern="^(csv|json|excel)$",
        description="Formato de exportación"
    )
    time_range: MetricTimeRange = Field(
        MetricTimeRange.LAST_24_HOURS,
        description="Rango de tiempo a exportar"
    )
    include_raw_data: bool = Field(
        False,
        description="Incluir datos crudos sin agregar"
    )


# === Requests de Historial ===

class GetHistoryRequest(BaseModel):
    """Request para obtener historial de publicaciones."""
    
    camera_id: Optional[str] = Field(None, description="Filtrar por cámara")
    server_id: Optional[int] = Field(None, description="Filtrar por servidor")
    status: Optional[PublicationStatus] = Field(None, description="Filtrar por estado")
    termination_reason: Optional[TerminationReason] = Field(
        None,
        description="Filtrar por razón de terminación"
    )
    start_date: Optional[datetime] = Field(None, description="Fecha inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha fin")
    min_duration_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Duración mínima en segundos"
    )
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(50, ge=1, le=200, description="Tamaño de página")
    order_by: str = Field(
        "start_time",
        pattern="^(start_time|end_time|duration_seconds|total_frames|error_count)$",
        description="Campo para ordenar"
    )
    order_desc: bool = Field(True, description="Orden descendente")


class CleanupHistoryRequest(BaseModel):
    """Request para limpiar historial antiguo."""
    
    older_than_days: int = Field(
        30,
        ge=1,
        le=365,
        description="Eliminar registros más antiguos que N días"
    )
    keep_errors: bool = Field(
        True,
        description="Mantener registros con errores"
    )
    dry_run: bool = Field(
        True,
        description="Solo simular, no eliminar realmente"
    )


# === Requests de Viewers ===

class GetViewersRequest(BaseModel):
    """Request para obtener información de viewers."""
    
    publication_id: Optional[int] = Field(None, description="Filtrar por publicación")
    active_only: bool = Field(True, description="Solo viewers activos")
    protocol: Optional[ViewerProtocol] = Field(None, description="Filtrar por protocolo")
    include_history: bool = Field(False, description="Incluir historial de viewers")
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(50, ge=1, le=200, description="Tamaño de página")


class ViewerAnalyticsRequest(BaseModel):
    """Request para análisis de audiencia."""
    
    time_range: MetricTimeRange = Field(
        MetricTimeRange.LAST_7_DAYS,
        description="Período de análisis"
    )
    group_by: str = Field(
        "hour",
        pattern="^(hour|day|week|protocol|camera)$",
        description="Agrupar resultados por"
    )
    include_geographic: bool = Field(
        False,
        description="Incluir análisis geográfico por IP"
    )


# === Requests de Paths ===

class CreatePathRequest(BaseModel):
    """Request para crear un path MediaMTX."""
    
    server_id: int = Field(..., description="ID del servidor MediaMTX")
    path_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Nombre del path (sin espacios)"
    )
    source_type: PathSourceType = Field(..., description="Tipo de fuente")
    source_url: Optional[str] = Field(None, description="URL de la fuente")
    
    # Configuración de grabación
    record_enabled: bool = Field(False, description="Habilitar grabación")
    record_path: Optional[str] = Field(None, description="Ruta de grabación")
    record_format: Optional[str] = Field(
        "fmp4",
        pattern="^(fmp4|mpegts)$",
        description="Formato de grabación"
    )
    record_segment_duration: int = Field(
        3600,
        ge=60,
        le=86400,
        description="Duración de segmentos en segundos"
    )
    
    # Control de acceso
    authentication_required: bool = Field(False, description="Requiere autenticación")
    publish_user: Optional[str] = Field(None, description="Usuario para publicar")
    publish_password: Optional[str] = Field(None, description="Contraseña para publicar")
    read_user: Optional[str] = Field(None, description="Usuario para leer")
    read_password: Optional[str] = Field(None, description="Contraseña para leer")
    allowed_ips: Optional[List[str]] = Field(None, description="IPs permitidas")
    
    # Scripts
    run_on_init: Optional[str] = Field(None, description="Comando al inicializar")
    run_on_demand: Optional[str] = Field(None, description="Comando bajo demanda")
    
    @validator('source_url')
    def validate_source_url(cls, v, values):
        """Valida que se proporcione URL para ciertos tipos de fuente."""
        source_type = values.get('source_type')
        if source_type in [PathSourceType.RTSP, PathSourceType.RTMP, PathSourceType.HLS]:
            if not v:
                raise ValueError(f"source_url es requerido para tipo {source_type}")
        return v
    
    @validator('record_path')
    def validate_record_path(cls, v, values):
        """Valida configuración de grabación."""
        if values.get('record_enabled') and not v:
            raise ValueError("record_path es requerido cuando record_enabled es True")
        return v


class UpdatePathRequest(BaseModel):
    """Request para actualizar un path MediaMTX."""
    
    path_name: Optional[str] = Field(None, description="Nuevo nombre del path")
    source_type: Optional[PathSourceType] = Field(None, description="Tipo de fuente")
    source_url: Optional[str] = Field(None, description="URL de la fuente")
    record_enabled: Optional[bool] = Field(None, description="Habilitar grabación")
    record_path: Optional[str] = Field(None, description="Ruta de grabación")
    authentication_required: Optional[bool] = Field(None, description="Requiere auth")
    is_active: Optional[bool] = Field(None, description="Estado activo")
    
    class Config:
        # Permitir que todos los campos sean opcionales para actualizaciones parciales
        validate_assignment = True


class TestPathRequest(BaseModel):
    """Request para probar un path MediaMTX."""
    
    timeout_seconds: int = Field(
        10,
        ge=1,
        le=60,
        description="Timeout para la prueba"
    )
    test_write: bool = Field(
        False,
        description="Probar escritura además de lectura"
    )


# === Requests de Health/Monitoreo ===

class HealthCheckRequest(BaseModel):
    """Request para verificar salud de servidor MediaMTX."""
    
    check_api: bool = Field(True, description="Verificar API REST")
    check_rtsp: bool = Field(True, description="Verificar servidor RTSP")
    check_paths: bool = Field(False, description="Verificar paths configurados")
    timeout_seconds: int = Field(
        5,
        ge=1,
        le=30,
        description="Timeout para cada verificación"
    )