"""
Schemas de response para endpoints de MediaMTX.

Estos modelos definen la estructura de las respuestas
que devuelve la API para operaciones con MediaMTX.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# Importar clases base
from api.schemas.base import PaginatedResponse


# Reutilizar enums del módulo de requests
from api.schemas.requests.mediamtx_requests import (
    PublicationStatus,
    TerminationReason,
    ViewerProtocol,
    PathSourceType
)


# === Modelos auxiliares para evitar Dict[str, Any] ===

class ViewerStats(BaseModel):
    """Estadísticas detalladas de viewers."""
    total_viewers: int = Field(..., description="Total de viewers únicos")
    current_viewers: int = Field(..., description="Viewers actuales")
    peak_viewers: int = Field(..., description="Pico máximo de viewers")
    average_session_duration: float = Field(..., description="Duración promedio en minutos")
    bounce_rate: float = Field(..., description="Tasa de rebote (% sesiones < 10s)")
    
    class Config:
        from_attributes = True


class ErrorEvent(BaseModel):
    """Evento de error en el timeline."""
    timestamp: datetime = Field(..., description="Momento del error")
    error_type: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    severity: str = Field(..., description="Severidad: low, medium, high")
    affected_viewers: Optional[int] = Field(None, description="Viewers afectados")
    
    class Config:
        from_attributes = True


class ViewerSummary(BaseModel):
    """Resumen de información de viewers."""
    total_unique: int = Field(..., description="Viewers únicos totales")
    total_sessions: int = Field(..., description="Total de sesiones")
    total_viewing_minutes: float = Field(..., description="Minutos totales de visualización")
    by_protocol: Dict[str, int] = Field(..., description="Distribución por protocolo")
    by_location: Dict[str, int] = Field(..., description="Distribución por ubicación")
    
    class Config:
        from_attributes = True


class TopCamera(BaseModel):
    """Información de cámara más vista."""
    camera_id: str = Field(..., description="ID de la cámara")
    camera_name: str = Field(..., description="Nombre de la cámara")
    viewer_count: int = Field(..., description="Número de viewers")
    total_minutes: float = Field(..., description="Minutos totales visualizados")
    average_viewers: float = Field(..., description="Promedio de viewers")
    
    class Config:
        from_attributes = True


class ViewerTrend(BaseModel):
    """Tendencia de viewers en un período."""
    timestamp: datetime = Field(..., description="Momento del dato")
    viewer_count: int = Field(..., description="Número de viewers")
    trend_direction: str = Field(..., description="Dirección: up, down, stable")
    change_percentage: float = Field(..., description="Cambio porcentual")
    
    class Config:
        from_attributes = True


# === Responses de Configuración ===

class MediaMTXServerResponse(BaseModel):
    """
    Respuesta de configuración de servidor MediaMTX.
    
    Sigue las mejores prácticas REST:
    - Usa 'id' como identificador principal
    - Usa 'name' en lugar de prefijos redundantes
    - Nombres descriptivos y consistentes
    """
    id: int = Field(..., description="ID único del servidor")
    name: str = Field(..., description="Nombre descriptivo del servidor")
    server_url: str = Field(..., description="URL base del servidor MediaMTX")
    rtsp_port: int = Field(554, description="Puerto RTSP")
    api_url: Optional[str] = Field(None, description="URL de la API MediaMTX")
    api_port: int = Field(9997, description="Puerto de la API")
    api_enabled: bool = Field(True, description="Si la API está habilitada")
    username: Optional[str] = Field(None, description="Usuario para autenticación")
    # password se omite en responses por seguridad
    auth_required: bool = Field(False, description="Si requiere autenticación")
    use_tcp: bool = Field(True, description="Forzar transporte TCP")
    is_active: bool = Field(False, description="Si está activa")
    is_default: bool = Field(False, description="Si es la configuración por defecto")
    max_reconnect_attempts: int = Field(10, description="Máximo de intentos de reconexión")
    reconnect_delay_seconds: float = Field(5.0, description="Segundos entre reconexiones")
    publish_path_template: str = Field(
        "cam_{camera_id}",
        description="Template para generar paths de publicación"
    )
    health_status: Optional[str] = Field(None, description="Estado de salud actual")
    last_health_check: Optional[datetime] = Field(None, description="Última verificación de salud")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    created_by: str = Field("system", description="Usuario que creó la configuración")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "MediaMTX Principal",
                "server_url": "rtsp://192.168.1.100:8554",
                "rtsp_port": 8554,
                "api_url": "http://192.168.1.100:9997",
                "api_port": 9997,
                "api_enabled": True,
                "username": "admin",
                "auth_required": True,
                "use_tcp": True,
                "is_active": True,
                "is_default": True,
                "max_reconnect_attempts": 10,
                "reconnect_delay_seconds": 5.0,
                "publish_path_template": "cam_{camera_id}",
                "health_status": "healthy",
                "last_health_check": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "created_by": "admin"
            }
        }


class MediaMTXServerListResponse(PaginatedResponse[MediaMTXServerResponse]):
    """Lista paginada de servidores MediaMTX."""
    # Los campos de paginación vienen del genérico
    # No se necesitan campos adicionales
    
    class Config:
        from_attributes = True


# === Responses de Métricas ===

class PublishMetricsSnapshot(BaseModel):
    """
    Snapshot de métricas en tiempo real para dashboard.
    
    Compatible con el tipo PublishMetrics del frontend.
    Proporciona la métrica más reciente de una publicación.
    """
    camera_id: str = Field(..., description="ID de la cámara")
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    fps: float = Field(..., description="Frames por segundo actual")
    bitrate_kbps: float = Field(..., description="Bitrate en kilobits por segundo")
    viewers: int = Field(..., description="Número de viewers conectados")
    frames_sent: int = Field(..., description="Total de frames enviados")
    bytes_sent: int = Field(..., description="Total de bytes enviados")
    quality_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=100,
        description="Score de calidad de la transmisión (0-100)"
    )
    status: Optional[Literal["optimal", "degraded", "poor"]] = Field(
        None,
        description="Estado de la transmisión basado en quality_score"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "camera_id": "cam_001",
                "timestamp": "2024-01-15T10:30:00Z",
                "fps": 25.0,
                "bitrate_kbps": 2048.5,
                "viewers": 3,
                "frames_sent": 150000,
                "bytes_sent": 31457280,
                "quality_score": 95.5,
                "status": "optimal"
            }
        }


class MetricPoint(BaseModel):
    """Punto de métrica individual."""
    
    timestamp: datetime = Field(..., description="Momento de la métrica")
    fps: Optional[float] = Field(None, description="Frames por segundo")
    bitrate_kbps: Optional[float] = Field(None, description="Bitrate en Kbps")
    frames: Optional[int] = Field(None, description="Frames totales")
    dropped_frames: Optional[int] = Field(None, description="Frames perdidos")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Score de calidad")
    viewer_count: Optional[int] = Field(None, description="Viewers conectados")
    cpu_usage_percent: Optional[float] = Field(None, description="Uso de CPU %")
    memory_usage_mb: Optional[float] = Field(None, description="Uso de memoria MB")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00Z",
                "fps": 25.0,
                "bitrate_kbps": 2048.5,
                "frames": 150000,
                "dropped_frames": 12,
                "quality_score": 94.5,
                "viewer_count": 5,
                "cpu_usage_percent": 35.2,
                "memory_usage_mb": 256.8
            }
        }


class MetricsSummary(BaseModel):
    """Resumen estadístico de métricas."""
    
    avg_fps: float = Field(..., description="FPS promedio")
    min_fps: float = Field(..., description="FPS mínimo")
    max_fps: float = Field(..., description="FPS máximo")
    avg_bitrate_kbps: float = Field(..., description="Bitrate promedio")
    total_frames: int = Field(..., description="Frames totales")
    total_dropped_frames: int = Field(..., description="Frames perdidos totales")
    avg_quality_score: float = Field(..., description="Score de calidad promedio")
    peak_viewers: int = Field(..., description="Pico de viewers simultáneos")
    avg_viewers: float = Field(..., description="Viewers promedio")
    total_data_mb: float = Field(..., description="Datos totales en MB")
    uptime_percent: float = Field(..., description="Porcentaje de uptime")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "avg_fps": 24.8,
                "min_fps": 22.5,
                "max_fps": 25.0,
                "avg_bitrate_kbps": 2015.3,
                "total_frames": 8928000,
                "total_dropped_frames": 342,
                "avg_quality_score": 92.7,
                "peak_viewers": 15,
                "avg_viewers": 7.3,
                "total_data_mb": 14567.8,
                "uptime_percent": 99.2
            }
        }


class PublicationMetricsResponse(BaseModel):
    """Respuesta con métricas de una publicación."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    publication_id: int = Field(..., description="ID de la publicación")
    time_range: str = Field(..., description="Rango de tiempo consultado")
    data_points: List[MetricPoint] = Field(..., description="Puntos de métrica")
    summary: MetricsSummary = Field(..., description="Resumen estadístico")
    viewer_stats: Optional[ViewerStats] = Field(None, description="Estadísticas de viewers")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "camera_id": "cam_001",
                "publication_id": 42,
                "time_range": "LAST_HOUR",
                "data_points": [
                    {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "fps": 25.0,
                        "bitrate_kbps": 2048.5,
                        "frames": 150000,
                        "dropped_frames": 12,
                        "quality_score": 94.5,
                        "viewer_count": 5
                    }
                ],
                "summary": {
                    "avg_fps": 24.8,
                    "min_fps": 22.5,
                    "max_fps": 25.0,
                    "avg_bitrate_kbps": 2015.3,
                    "total_frames": 8928000,
                    "total_dropped_frames": 342,
                    "avg_quality_score": 92.7,
                    "peak_viewers": 15,
                    "avg_viewers": 7.3,
                    "total_data_mb": 14567.8,
                    "uptime_percent": 99.2
                },
                "viewer_stats": {
                    "total_viewers": 45,
                    "current_viewers": 5,
                    "peak_viewers": 15,
                    "average_session_duration": 32.5,
                    "bounce_rate": 12.3
                }
            }
        }


class PaginatedMetricsResponse(PaginatedResponse[PublishMetricsSnapshot]):
    """
    Respuesta paginada para historial de métricas.
    
    Diseñada para ser compatible con el frontend que espera
    una lista de PublishMetrics para gráficos temporales.
    """
    camera_id: str = Field(..., description="ID de la cámara")
    # Los campos de paginación (total, page, page_size, items) vienen del genérico
    time_range: Dict[str, str] = Field(
        ...,
        description="Rango de tiempo de los datos",
        example={"start": "2024-01-15T00:00:00Z", "end": "2024-01-15T23:59:59Z"}
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "camera_id": "cam_001",
                "total": 1440,
                "page": 1,
                "page_size": 100,
                "has_next": True,
                "has_previous": False,
                "total_pages": 15,
                "items": [
                    {
                        "camera_id": "cam_001",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "fps": 25.0,
                        "bitrate_kbps": 2048.5,
                        "viewers": 3,
                        "frames_sent": 150000,
                        "bytes_sent": 31457280,
                        "quality_score": 95.5,
                        "status": "optimal"
                    }
                ],
                "time_range": {
                    "start": "2024-01-15T00:00:00Z",
                    "end": "2024-01-15T23:59:59Z"
                }
            }
        }


class MetricsExportResponse(BaseModel):
    """Respuesta de exportación de métricas."""
    
    export_id: str = Field(..., description="ID único de la exportación")
    format: str = Field(..., description="Formato del archivo")
    file_size_bytes: int = Field(..., description="Tamaño del archivo")
    download_url: str = Field(..., description="URL de descarga")
    expires_at: datetime = Field(..., description="Fecha de expiración")
    record_count: int = Field(..., description="Número de registros exportados")


class GlobalMetricsSummaryResponse(BaseModel):
    """Resumen global de métricas del sistema."""
    
    total_cameras_publishing: int = Field(..., description="Cámaras publicando")
    total_active_viewers: int = Field(..., description="Viewers activos totales")
    total_bandwidth_mbps: float = Field(..., description="Ancho de banda total Mbps")
    avg_quality_score: float = Field(..., description="Score de calidad promedio global")
    system_cpu_percent: float = Field(..., description="CPU del sistema %")
    system_memory_percent: float = Field(..., description="Memoria del sistema %")
    top_cameras: List[TopCamera] = Field(..., description="Top cámaras por viewers")
    alerts_count: int = Field(..., description="Número de alertas activas")
    
    class Config:
        from_attributes = True


# === Responses de Historial ===

class PublicationHistoryItem(BaseModel):
    """Item de historial de publicación."""
    
    history_id: int = Field(..., description="ID del registro histórico")
    camera_id: str = Field(..., description="ID de la cámara")
    camera_name: Optional[str] = Field(None, description="Nombre de la cámara")
    server_id: int = Field(..., description="ID del servidor MediaMTX")
    server_name: Optional[str] = Field(None, description="Nombre del servidor")
    session_id: str = Field(..., description="ID único de la sesión")
    publish_path: str = Field(..., description="Path de publicación")
    start_time: datetime = Field(..., description="Tiempo de inicio")
    end_time: Optional[datetime] = Field(None, description="Tiempo de fin")
    duration_seconds: Optional[int] = Field(None, description="Duración en segundos")
    total_frames: int = Field(..., description="Frames totales transmitidos")
    average_fps: Optional[float] = Field(None, description="FPS promedio")
    average_bitrate_kbps: Optional[float] = Field(None, description="Bitrate promedio")
    total_data_mb: float = Field(..., description="Datos totales transmitidos")
    max_viewers: int = Field(..., description="Máximo de viewers simultáneos")
    error_count: int = Field(..., description="Número de errores")
    termination_reason: Optional[TerminationReason] = Field(None, description="Razón de terminación")
    last_error: Optional[str] = Field(None, description="Último error registrado")
    
    class Config:
        from_attributes = True


class PublicationHistoryResponse(PaginatedResponse[PublicationHistoryItem]):
    """Respuesta con historial de publicaciones."""
    # Los campos de paginación vienen del genérico
    filters_applied: Dict[str, str] = Field(..., description="Filtros aplicados como clave-valor")
    
    class Config:
        from_attributes = True


class PublicationSessionDetailResponse(BaseModel):
    """Detalle completo de una sesión de publicación."""
    
    session_info: PublicationHistoryItem = Field(..., description="Información de la sesión")
    metrics_summary: MetricsSummary = Field(..., description="Resumen de métricas")
    error_timeline: List[ErrorEvent] = Field(..., description="Timeline de errores")
    viewer_summary: ViewerSummary = Field(..., description="Resumen de viewers")
    ffmpeg_command: Optional[str] = Field(None, description="Comando FFmpeg usado")
    metadata: Optional[Dict[str, str]] = Field(None, description="Metadata adicional como clave-valor")
    
    class Config:
        from_attributes = True


class HistoryCleanupResponse(BaseModel):
    """Respuesta de limpieza de historial."""
    
    records_affected: int = Field(..., description="Registros que serán eliminados")
    space_freed_mb: float = Field(..., description="Espacio a liberar en MB")
    oldest_record_date: Optional[datetime] = Field(None, description="Fecha del registro más antiguo")
    dry_run: bool = Field(..., description="Si fue simulación")
    details: Dict[str, int] = Field(..., description="Detalles por categoría")


# === Responses de Viewers ===

class ActiveViewer(BaseModel):
    """Información de un viewer activo."""
    
    viewer_id: int = Field(..., description="ID del viewer")
    publication_id: int = Field(..., description="ID de la publicación")
    camera_id: str = Field(..., description="ID de la cámara")
    camera_name: Optional[str] = Field(None, description="Nombre de la cámara")
    viewer_ip: str = Field(..., description="IP del viewer")
    viewer_user_agent: Optional[str] = Field(None, description="User agent")
    protocol_used: ViewerProtocol = Field(..., description="Protocolo usado")
    start_time: datetime = Field(..., description="Tiempo de conexión")
    duration_seconds: int = Field(..., description="Duración de visualización")
    bytes_received: int = Field(..., description="Bytes recibidos")
    quality_changes: int = Field(..., description="Cambios de calidad")
    buffer_events: int = Field(..., description="Eventos de buffer")
    
    class Config:
        from_attributes = True


class ViewersListResponse(PaginatedResponse[ActiveViewer]):
    """Respuesta con lista de viewers."""
    # Los campos de paginación vienen del genérico
    active_count: int = Field(..., description="Viewers activos")
    protocol_breakdown: Dict[str, int] = Field(..., description="Viewers por protocolo")
    
    class Config:
        from_attributes = True


class ViewerAnalyticsResponse(BaseModel):
    """Respuesta de análisis de audiencia."""
    
    time_range: str = Field(..., description="Período analizado")
    total_unique_viewers: int = Field(..., description="Viewers únicos totales")
    total_viewing_hours: float = Field(..., description="Horas totales de visualización")
    avg_session_duration_minutes: float = Field(..., description="Duración promedio de sesión")
    peak_concurrent_viewers: int = Field(..., description="Pico de viewers concurrentes")
    peak_time: datetime = Field(..., description="Momento del pico")
    
    # Análisis por agrupación
    viewer_trends: List[ViewerTrend] = Field(..., description="Tendencias por período")
    protocol_distribution: Dict[str, float] = Field(..., description="Distribución por protocolo %")
    top_cameras: List[TopCamera] = Field(..., description="Cámaras más vistas")
    
    # Análisis geográfico opcional
    geographic_distribution: Optional[Dict[str, int]] = Field(None, description="Viewers por país")
    
    # Métricas de calidad
    avg_quality_score: float = Field(..., description="Score de calidad promedio")
    buffer_event_rate: float = Field(..., description="Tasa de eventos de buffer")
    
    class Config:
        from_attributes = True


# === Responses de Paths ===

class MediaMTXPath(BaseModel):
    """
    Información de un path MediaMTX.
    
    NOTA: El campo path_id se serializa como 'id' para compatibilidad con el frontend.
    El frontend espera 'id' pero la base de datos usa 'path_id'.
    
    TODO: Considerar actualizar el frontend para usar 'path_id' consistentemente.
    """
    
    path_id: int = Field(..., alias="id", description="ID del path")
    server_id: int = Field(..., description="ID del servidor")
    server_name: Optional[str] = Field(None, description="Nombre del servidor")
    path_name: str = Field(..., description="Nombre del path")
    source_type: PathSourceType = Field(..., description="Tipo de fuente")
    source_url: Optional[str] = Field(None, description="URL de la fuente")
    
    # Estado
    is_active: bool = Field(..., description="Si está activo")
    is_running: bool = Field(..., description="Si está ejecutándose")
    connected_publishers: int = Field(..., description="Publishers conectados")
    connected_readers: int = Field(..., description="Readers conectados")
    
    # Configuración
    record_enabled: bool = Field(..., description="Grabación habilitada")
    record_path: Optional[str] = Field(None, description="Ruta de grabación")
    authentication_required: bool = Field(..., description="Requiere autenticación")
    
    # Timestamps
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    last_used: Optional[datetime] = Field(None, description="Último uso")
    
    class Config:
        from_attributes = True
        populate_by_name = True  # Permite recibir tanto 'id' como 'path_id'


class PathsListResponse(BaseModel):
    """Respuesta con lista de paths MediaMTX."""
    
    total: int = Field(..., description="Total de paths")
    active_count: int = Field(..., description="Paths activos")
    items: List[MediaMTXPath] = Field(..., description="Lista de paths")
    server_summary: Dict[int, int] = Field(..., description="Paths por servidor")
    
    class Config:
        from_attributes = True


class PathTestResponse(BaseModel):
    """Respuesta de prueba de path."""
    
    path_id: int = Field(..., description="ID del path probado")
    path_name: str = Field(..., description="Nombre del path")
    test_timestamp: datetime = Field(..., description="Momento de la prueba")
    
    # Resultados
    read_test_passed: bool = Field(..., description="Prueba de lectura exitosa")
    write_test_passed: Optional[bool] = Field(None, description="Prueba de escritura exitosa")
    response_time_ms: float = Field(..., description="Tiempo de respuesta en ms")
    
    # Detalles
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    warnings: List[str] = Field(..., description="Advertencias encontradas")
    
    class Config:
        from_attributes = True


# === Responses de Health/Monitoreo ===

class ServerHealthStatus(BaseModel):
    """Estado de salud de un servidor MediaMTX."""
    
    server_id: int = Field(..., description="ID del servidor")
    server_name: str = Field(..., description="Nombre del servidor")
    health_status: str = Field(..., description="Estado: healthy, unhealthy, unknown")
    last_check_time: datetime = Field(..., description="Último chequeo")
    
    # Componentes
    rtsp_server_ok: bool = Field(..., description="Servidor RTSP funcionando")
    api_server_ok: Optional[bool] = Field(None, description="API REST funcionando")
    paths_ok: Optional[bool] = Field(None, description="Paths verificados")
    
    # Métricas
    active_connections: int = Field(..., description="Conexiones activas")
    cpu_usage_percent: Optional[float] = Field(None, description="Uso de CPU")
    memory_usage_mb: Optional[float] = Field(None, description="Uso de memoria")
    uptime_seconds: Optional[int] = Field(None, description="Tiempo activo")
    
    # Errores
    error_count: int = Field(..., description="Errores recientes")
    last_error: Optional[str] = Field(None, description="Último error")
    warnings: List[str] = Field(..., description="Advertencias actuales")
    
    class Config:
        from_attributes = True


class PublishingAlertResponse(BaseModel):
    """
    Respuesta de alerta del sistema de publicación.
    
    Sigue las mejores prácticas REST:
    - Usa 'id' como identificador principal
    - Usa 'alert_type' en lugar de 'category'
    - Separa 'auto_resolve' (comportamiento del sistema) de 'user_dismissible' (permisos del usuario)
    - Usa 'dismissible' para indicar si el usuario puede descartar la alerta
    """
    id: str = Field(..., description="ID único de la alerta")
    severity: str = Field(..., description="Severidad: info, warning, error, critical")
    alert_type: str = Field(..., description="Tipo de alerta: performance, connectivity, resource, security")
    title: str = Field(..., description="Título de la alerta")
    message: str = Field(..., description="Mensaje detallado")
    affected_resources: List[str] = Field(..., description="Recursos afectados")
    created_at: datetime = Field(..., description="Fecha de creación")
    acknowledged: bool = Field(..., description="Si fue reconocida")
    acknowledged_by: Optional[str] = Field(None, description="Usuario que reconoció")
    acknowledged_at: Optional[datetime] = Field(None, description="Fecha de reconocimiento")
    auto_resolve: bool = Field(..., description="Si se resuelve automáticamente por el sistema")
    dismissible: bool = Field(..., description="Si el usuario puede descartar manualmente la alerta")
    resolved: bool = Field(..., description="Si está resuelta")
    resolved_at: Optional[datetime] = Field(None, description="Fecha de resolución")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "alert_123456",
                "severity": "warning",
                "alert_type": "performance",
                "title": "Alto uso de CPU en publicación",
                "message": "La publicación de camera_001 está usando más del 80% de CPU",
                "affected_resources": ["camera_001", "mediamtx_server_1"],
                "created_at": "2024-01-15T10:30:00Z",
                "acknowledged": False,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "auto_resolve": True,
                "dismissible": True,
                "resolved": False,
                "resolved_at": None
            }
        }


class SystemHealthResponse(BaseModel):
    """
    Respuesta de salud global del sistema de publicación.
    
    Estados del sistema:
    - healthy: Todo funcionando correctamente
    - degraded: Funcionando con problemas menores (mapeado a 'warning' para frontend)
    - critical: Problemas graves que requieren atención inmediata (mapeado a 'error' para frontend)
    
    NOTA: El backend usa 'degraded' y 'critical' internamente, pero se mapean
    a 'warning' y 'error' respectivamente para compatibilidad con el frontend.
    """
    
    overall_status: Literal["healthy", "warning", "error"] = Field(
        ..., 
        description="Estado general del sistema de publicación"
    )
    
    @validator('overall_status', pre=True)
    def map_health_status(cls, v):
        """
        Mapea los valores del backend a los esperados por el frontend.
        
        Backend -> Frontend:
        - healthy -> healthy (sin cambio)
        - degraded -> warning
        - critical -> error
        """
        status_mapping = {
            'healthy': 'healthy',
            'degraded': 'warning',
            'critical': 'error'
        }
        return status_mapping.get(v, v)
    check_timestamp: datetime = Field(..., description="Momento del chequeo")
    
    # Resumen
    total_servers: int = Field(..., description="Total de servidores MediaMTX")
    healthy_servers: int = Field(..., description="Servidores funcionando correctamente")
    active_publications: int = Field(..., description="Publicaciones activas en este momento")
    total_viewers: int = Field(..., description="Viewers totales conectados")
    
    # Detalles por servidor
    servers: List[ServerHealthStatus] = Field(
        ..., 
        description="Estado detallado de cada servidor MediaMTX"
    )
    
    # Alertas - Usando tipo específico
    active_alerts: List[PublishingAlertResponse] = Field(
        default_factory=list,
        description="Alertas activas del sistema de publicación"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recomendaciones de optimización basadas en el estado actual"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "overall_status": "warning",
                "check_timestamp": "2024-01-15T10:30:00Z",
                "total_servers": 2,
                "healthy_servers": 1,
                "active_publications": 5,
                "total_viewers": 23,
                "servers": [
                    {
                        "server_id": 1,
                        "server_name": "MediaMTX Principal",
                        "health_status": "healthy",
                        "last_check_time": "2024-01-15T10:28:00Z",
                        "rtsp_server_ok": True,
                        "api_server_ok": True,
                        "paths_ok": True,
                        "active_connections": 5,
                        "cpu_usage_percent": 45.2,
                        "memory_usage_mb": 512.5,
                        "uptime_seconds": 86400,
                        "error_count": 0,
                        "last_error": None,
                        "warnings": []
                    },
                    {
                        "server_id": 2,
                        "server_name": "MediaMTX Backup",
                        "health_status": "unhealthy",
                        "last_check_time": "2024-01-15T10:28:00Z",
                        "rtsp_server_ok": False,
                        "api_server_ok": True,
                        "paths_ok": False,
                        "active_connections": 0,
                        "cpu_usage_percent": 0,
                        "memory_usage_mb": 0,
                        "uptime_seconds": 0,
                        "error_count": 5,
                        "last_error": "Connection refused",
                        "warnings": ["RTSP server not responding"]
                    }
                ],
                "active_alerts": [
                    {
                        "id": "alert_123456",
                        "severity": "warning",
                        "alert_type": "connectivity",
                        "title": "Servidor MediaMTX Backup sin conexión",
                        "message": "El servidor MediaMTX Backup no responde a las verificaciones de salud",
                        "affected_resources": ["mediamtx_server_2"],
                        "created_at": "2024-01-15T10:25:00Z",
                        "acknowledged": False,
                        "acknowledged_by": None,
                        "acknowledged_at": None,
                        "auto_resolve": True,
                        "dismissible": True,
                        "resolved": False,
                        "resolved_at": None
                    }
                ],
                "recommendations": [
                    "Revisar conectividad del servidor MediaMTX Backup",
                    "Considerar reiniciar el servicio RTSP en el servidor 2"
                ]
            }
        }


# Eliminada definición duplicada - movida antes de SystemHealthResponse


class AlertsListResponse(PaginatedResponse[PublishingAlertResponse]):
    """Respuesta con lista de alertas."""
    # Los campos de paginación vienen del genérico
    active_count: int = Field(..., description="Alertas activas")
    critical_count: int = Field(..., description="Alertas críticas")
    by_severity: Dict[str, int] = Field(..., description="Conteo por severidad")
    by_alert_type: Dict[str, int] = Field(..., description="Conteo por tipo de alerta")
    
    class Config:
        from_attributes = True


class DismissAlertResponse(BaseModel):
    """Respuesta al descartar una alerta."""
    
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje de confirmación")
    alert_id: str = Field(..., description="ID de la alerta descartada")
    dismissed_at: datetime = Field(..., description="Momento del descarte")
    note: Optional[str] = Field(None, description="Nota adicional")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Alerta alert_123456 descartada exitosamente",
                "alert_id": "alert_123456",
                "dismissed_at": "2024-01-15T10:30:00Z",
                "note": "El descarte es temporal y se perderá al reiniciar el servidor"
            }
        }