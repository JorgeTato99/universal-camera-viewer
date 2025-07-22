"""
Schemas de response para endpoints de MediaMTX.

Estos modelos definen la estructura de las respuestas
que devuelve la API para operaciones con MediaMTX.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# Reutilizar enums del módulo de requests
from api.schemas.requests.mediamtx_requests import (
    PublicationStatus,
    TerminationReason,
    ViewerProtocol,
    PathSourceType
)


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


class MediaMTXServerListResponse(BaseModel):
    """Lista paginada de servidores MediaMTX."""
    total: int = Field(..., description="Total de servidores")
    items: List[MediaMTXServerResponse] = Field(..., description="Servidores en esta página")
    page: int = Field(1, description="Página actual")
    page_size: int = Field(50, description="Tamaño de página")
    
    class Config:
        from_attributes = True


# === Responses de Métricas ===

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


class PublicationMetricsResponse(BaseModel):
    """Respuesta con métricas de una publicación."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    publication_id: int = Field(..., description="ID de la publicación")
    time_range: str = Field(..., description="Rango de tiempo consultado")
    data_points: List[MetricPoint] = Field(..., description="Puntos de métrica")
    summary: MetricsSummary = Field(..., description="Resumen estadístico")
    viewer_stats: Optional[Dict[str, Any]] = Field(None, description="Estadísticas de viewers")
    
    class Config:
        from_attributes = True


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
    top_cameras: List[Dict[str, Any]] = Field(..., description="Top cámaras por viewers")
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


class PublicationHistoryResponse(BaseModel):
    """Respuesta con historial de publicaciones."""
    
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    items: List[PublicationHistoryItem] = Field(..., description="Items del historial")
    filters_applied: Dict[str, Any] = Field(..., description="Filtros aplicados")
    
    class Config:
        from_attributes = True


class PublicationSessionDetailResponse(BaseModel):
    """Detalle completo de una sesión de publicación."""
    
    session_info: PublicationHistoryItem = Field(..., description="Información de la sesión")
    metrics_summary: MetricsSummary = Field(..., description="Resumen de métricas")
    error_timeline: List[Dict[str, Any]] = Field(..., description="Timeline de errores")
    viewer_summary: Dict[str, Any] = Field(..., description="Resumen de viewers")
    ffmpeg_command: Optional[str] = Field(None, description="Comando FFmpeg usado")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")
    
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


class ViewersListResponse(BaseModel):
    """Respuesta con lista de viewers."""
    
    total: int = Field(..., description="Total de viewers")
    active_count: int = Field(..., description="Viewers activos")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    items: List[ActiveViewer] = Field(..., description="Lista de viewers")
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
    viewer_trends: List[Dict[str, Any]] = Field(..., description="Tendencias por período")
    protocol_distribution: Dict[str, float] = Field(..., description="Distribución por protocolo %")
    top_cameras: List[Dict[str, Any]] = Field(..., description="Cámaras más vistas")
    
    # Análisis geográfico opcional
    geographic_distribution: Optional[Dict[str, int]] = Field(None, description="Viewers por país")
    
    # Métricas de calidad
    avg_quality_score: float = Field(..., description="Score de calidad promedio")
    buffer_event_rate: float = Field(..., description="Tasa de eventos de buffer")
    
    class Config:
        from_attributes = True


# === Responses de Paths ===

class MediaMTXPath(BaseModel):
    """Información de un path MediaMTX."""
    
    path_id: int = Field(..., description="ID del path")
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


class SystemHealthResponse(BaseModel):
    """Respuesta de salud global del sistema de publicación."""
    
    overall_status: str = Field(..., description="Estado general: healthy, degraded, critical")
    check_timestamp: datetime = Field(..., description="Momento del chequeo")
    
    # Resumen
    total_servers: int = Field(..., description="Total de servidores")
    healthy_servers: int = Field(..., description="Servidores saludables")
    active_publications: int = Field(..., description="Publicaciones activas")
    total_viewers: int = Field(..., description="Viewers totales")
    
    # Detalles por servidor
    servers: List[ServerHealthStatus] = Field(..., description="Estado de cada servidor")
    
    # Alertas
    active_alerts: List[Dict[str, Any]] = Field(..., description="Alertas activas")
    recommendations: List[str] = Field(..., description="Recomendaciones")
    
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


class AlertsListResponse(BaseModel):
    """Respuesta con lista de alertas."""
    
    total: int = Field(..., description="Total de alertas")
    active_count: int = Field(..., description="Alertas activas")
    critical_count: int = Field(..., description="Alertas críticas")
    items: List[PublishingAlertResponse] = Field(..., description="Lista de alertas")
    by_severity: Dict[str, int] = Field(..., description="Conteo por severidad")
    by_alert_type: Dict[str, int] = Field(..., description="Conteo por tipo de alerta")
    
    class Config:
        from_attributes = True