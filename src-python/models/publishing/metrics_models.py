"""
Modelos de dominio para métricas y analytics del sistema de publicación.

Este módulo define las estructuras de datos para gestionar métricas,
historial de sesiones y analytics de viewers en el sistema MediaMTX.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any


# === ENUMS ===

class StreamStatus(Enum):
    """Estados de calidad del stream basados en métricas."""
    OPTIMAL = "optimal"      # Score >= 80
    DEGRADED = "degraded"    # Score 50-79
    POOR = "poor"           # Score < 50
    UNKNOWN = "unknown"      # Sin datos suficientes


class TerminationReason(Enum):
    """Razones de terminación de una sesión de publicación."""
    USER_INITIATED = "user_initiated"      # Detenido por el usuario
    ERROR = "error"                        # Error técnico
    CONNECTION_LOST = "connection_lost"    # Pérdida de conexión
    SERVER_SHUTDOWN = "server_shutdown"    # Servidor apagado
    CAMERA_DISCONNECTED = "camera_disconnected"  # Cámara desconectada
    TIMEOUT = "timeout"                    # Timeout de inactividad
    REPLACED = "replaced"                  # Reemplazado por nueva sesión
    UNKNOWN = "unknown"                    # Razón desconocida


# === MODELOS DE MÉTRICAS ===

@dataclass
class PublishMetrics:
    """
    Métricas en tiempo real de una publicación activa.
    
    Compatible con el tipo PublishMetrics del frontend TypeScript.
    Representa un punto de métrica en un momento específico.
    
    Attributes:
        camera_id: ID único de la cámara
        timestamp: Momento de la captura
        fps: Frames por segundo actual
        bitrate_kbps: Bitrate en kilobits por segundo
        viewers: Número de viewers conectados
        frames_sent: Total de frames enviados desde el inicio
        bytes_sent: Total de bytes enviados desde el inicio
        quality_score: Score de calidad calculado (0-100)
        status: Estado del stream basado en quality_score
        cpu_usage_percent: Uso de CPU del proceso (opcional)
        memory_usage_mb: Uso de memoria en MB (opcional)
        dropped_frames: Frames perdidos (opcional)
        buffer_health: Salud del buffer 0-100 (opcional)
    """
    camera_id: str
    timestamp: datetime
    fps: float
    bitrate_kbps: float
    viewers: int = 0
    frames_sent: int = 0
    bytes_sent: int = 0
    quality_score: Optional[float] = None
    status: Optional[StreamStatus] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    dropped_frames: Optional[int] = None
    buffer_health: Optional[float] = None
    
    def __post_init__(self):
        """Validación y cálculo automático después de inicialización."""
        # Calcular quality_score si no se proporcionó
        if self.quality_score is None:
            self.quality_score = self._calculate_quality_score()
        
        # Determinar status basado en quality_score
        if self.status is None and self.quality_score is not None:
            self.status = self._determine_status()
    
    def _calculate_quality_score(self) -> float:
        """
        Calcula el score de calidad basado en las métricas disponibles.
        
        Returns:
            Score de 0 a 100
        """
        score = 100.0
        
        # Penalizar por FPS bajo
        if self.fps < 15:
            score -= 30
        elif self.fps < 20:
            score -= 15
        elif self.fps < 25:
            score -= 5
        
        # Penalizar por bitrate bajo
        if self.bitrate_kbps < 500:
            score -= 30
        elif self.bitrate_kbps < 1000:
            score -= 15
        elif self.bitrate_kbps < 2000:
            score -= 5
        
        # Penalizar por frames perdidos
        if self.dropped_frames and self.frames_sent > 0:
            drop_rate = (self.dropped_frames / self.frames_sent) * 100
            if drop_rate > 5:
                score -= 30
            elif drop_rate > 2:
                score -= 15
            elif drop_rate > 0.5:
                score -= 5
        
        # Considerar salud del buffer si está disponible
        if self.buffer_health is not None:
            if self.buffer_health < 50:
                score -= 20
            elif self.buffer_health < 80:
                score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _determine_status(self) -> StreamStatus:
        """Determina el estado basado en el score de calidad."""
        if self.quality_score is None:
            return StreamStatus.UNKNOWN
        elif self.quality_score >= 80:
            return StreamStatus.OPTIMAL
        elif self.quality_score >= 50:
            return StreamStatus.DEGRADED
        else:
            return StreamStatus.POOR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "camera_id": self.camera_id,
            "timestamp": self.timestamp.isoformat(),
            "fps": self.fps,
            "bitrate_kbps": self.bitrate_kbps,
            "viewers": self.viewers,
            "frames_sent": self.frames_sent,
            "bytes_sent": self.bytes_sent,
            "quality_score": self.quality_score,
            "status": self.status.value if self.status else None,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_mb": self.memory_usage_mb,
            "dropped_frames": self.dropped_frames,
            "buffer_health": self.buffer_health
        }


# === MODELOS DE HISTORIAL ===

@dataclass
class PublishingHistorySession:
    """
    Sesión histórica de publicación.
    
    Representa una sesión completa de publicación desde inicio hasta fin,
    con todas las métricas agregadas y estadísticas.
    
    Attributes:
        session_id: ID único de la sesión
        camera_id: ID de la cámara
        camera_name: Nombre de la cámara (opcional)
        server_id: ID del servidor MediaMTX
        server_name: Nombre del servidor (opcional)
        publish_path: Path usado en MediaMTX
        start_time: Momento de inicio
        end_time: Momento de fin (None si aún activa)
        duration_seconds: Duración total en segundos
        status: Estado final de la sesión
        termination_reason: Razón de terminación
        error_message: Mensaje de error si aplica
        total_frames: Total de frames transmitidos
        total_bytes: Total de bytes transmitidos
        average_fps: FPS promedio de la sesión
        average_bitrate_kbps: Bitrate promedio
        peak_viewers: Máximo de viewers simultáneos
        average_viewers: Promedio de viewers
        total_viewer_minutes: Minutos totales de visualización
        quality_score: Score de calidad promedio
        error_count: Número de errores durante la sesión
        reconnect_count: Número de reconexiones
        metadata: Metadatos adicionales
    """
    session_id: str
    camera_id: str
    server_id: int
    publish_path: str
    start_time: datetime
    camera_name: Optional[str] = None
    server_name: Optional[str] = None
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    status: str = "completed"
    termination_reason: Optional[TerminationReason] = None
    error_message: Optional[str] = None
    total_frames: int = 0
    total_bytes: int = 0
    average_fps: float = 0.0
    average_bitrate_kbps: float = 0.0
    peak_viewers: int = 0
    average_viewers: float = 0.0
    total_viewer_minutes: float = 0.0
    quality_score: float = 0.0
    error_count: int = 0
    reconnect_count: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calcula duración si no se proporcionó."""
        if self.end_time and not self.duration_seconds:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
    
    @property
    def duration_formatted(self) -> str:
        """Retorna la duración en formato legible."""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    @property
    def data_transferred_gb(self) -> float:
        """Retorna los datos transferidos en GB."""
        return self.total_bytes / (1024 ** 3)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "publish_path": self.publish_path,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self.duration_formatted,
            "status": self.status,
            "termination_reason": self.termination_reason.value if self.termination_reason else None,
            "error_message": self.error_message,
            "total_frames": self.total_frames,
            "total_bytes": self.total_bytes,
            "data_transferred_gb": round(self.data_transferred_gb, 2),
            "average_fps": round(self.average_fps, 1),
            "average_bitrate_kbps": round(self.average_bitrate_kbps, 1),
            "peak_viewers": self.peak_viewers,
            "average_viewers": round(self.average_viewers, 1),
            "total_viewer_minutes": round(self.total_viewer_minutes, 1),
            "quality_score": round(self.quality_score, 1),
            "error_count": self.error_count,
            "reconnect_count": self.reconnect_count,
            "metadata": self.metadata
        }


# === MODELOS DE PATHS ===

@dataclass
class MediaMTXPath:
    """
    Path configurado en MediaMTX.
    
    Representa un path/stream configurado en el servidor MediaMTX,
    incluyendo su configuración y estado actual.
    
    Attributes:
        path_id: ID único del path
        server_id: ID del servidor MediaMTX
        server_name: Nombre del servidor
        path_name: Nombre del path en MediaMTX
        source_type: Tipo de fuente (rtsp, rtmp, hls, webrtc)
        source_url: URL de la fuente si es pull
        is_active: Si está activo
        is_running: Si está transmitiendo actualmente
        connected_publishers: Número de publishers conectados
        connected_readers: Número de readers/viewers conectados
        record_enabled: Si la grabación está habilitada
        record_path: Ruta de grabación
        authentication_required: Si requiere autenticación
        allowed_ips: Lista de IPs permitidas
        created_at: Fecha de creación
        updated_at: Última actualización
        last_used: Último uso
        metadata: Metadatos adicionales
    """
    path_id: int
    server_id: int
    path_name: str
    source_type: str = "rtsp"
    server_name: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True
    is_running: bool = False
    connected_publishers: int = 0
    connected_readers: int = 0
    record_enabled: bool = False
    record_path: Optional[str] = None
    authentication_required: bool = False
    allowed_ips: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_configured(self) -> bool:
        """Verifica si el path está completamente configurado."""
        if self.source_type in ["rtsp", "rtmp", "hls"]:
            return bool(self.source_url)
        return True
    
    @property
    def viewer_count(self) -> int:
        """Alias para connected_readers por compatibilidad."""
        return self.connected_readers
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "path_id": self.path_id,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "path_name": self.path_name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "is_active": self.is_active,
            "is_running": self.is_running,
            "connected_publishers": self.connected_publishers,
            "connected_readers": self.connected_readers,
            "viewer_count": self.viewer_count,
            "record_enabled": self.record_enabled,
            "record_path": self.record_path,
            "authentication_required": self.authentication_required,
            "allowed_ips": self.allowed_ips,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "metadata": self.metadata
        }


# === MODELOS DE ESTADÍSTICAS ===

@dataclass
class CameraActivity:
    """
    Actividad agregada de una cámara.
    
    Representa las estadísticas de actividad de una cámara
    durante un período de tiempo específico.
    
    Attributes:
        camera_id: ID de la cámara
        camera_name: Nombre de la cámara
        total_sessions: Número total de sesiones
        total_duration_hours: Horas totales de publicación
        total_data_gb: GB totales transmitidos
        average_viewers: Promedio de viewers
        peak_viewers: Pico máximo de viewers
        average_quality_score: Score de calidad promedio
        error_rate: Porcentaje de sesiones con error
        uptime_percentage: Porcentaje de uptime
        last_active: Última actividad registrada
    """
    camera_id: str
    camera_name: str
    total_sessions: int = 0
    total_duration_hours: float = 0.0
    total_data_gb: float = 0.0
    average_viewers: float = 0.0
    peak_viewers: int = 0
    average_quality_score: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 0.0
    last_active: Optional[datetime] = None
    
    @property
    def is_recently_active(self) -> bool:
        """Verifica si estuvo activa en las últimas 24 horas."""
        if not self.last_active:
            return False
        return (datetime.now(timezone.utc) - self.last_active).total_seconds() < 86400
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "total_sessions": self.total_sessions,
            "total_duration_hours": round(self.total_duration_hours, 1),
            "total_data_gb": round(self.total_data_gb, 2),
            "average_viewers": round(self.average_viewers, 1),
            "peak_viewers": self.peak_viewers,
            "average_quality_score": round(self.average_quality_score, 1),
            "error_rate": round(self.error_rate, 1),
            "uptime_percentage": round(self.uptime_percentage, 1),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "is_recently_active": self.is_recently_active
        }


@dataclass
class PublishingStatistics:
    """
    Estadísticas agregadas del sistema de publicación.
    
    Proporciona una vista general del rendimiento y uso del sistema
    durante un período de tiempo específico.
    
    Attributes:
        time_range: Descripción del rango de tiempo
        start_date: Fecha de inicio del análisis
        end_date: Fecha de fin del análisis
        total_sessions: Total de sesiones de publicación
        total_duration_hours: Horas totales de streaming
        total_data_gb: GB totales transmitidos
        unique_cameras: Número de cámaras únicas
        average_viewers: Promedio de viewers por sesión
        peak_viewers: Pico máximo de viewers simultáneos
        peak_datetime: Momento del pico de viewers
        most_active_cameras: Lista de cámaras más activas
        error_rate: Porcentaje de sesiones con error
        average_session_duration_minutes: Duración promedio de sesión
        uptime_percentage: Porcentaje de uptime global
        protocol_distribution: Distribución de uso por protocolo
        hourly_distribution: Distribución de actividad por hora
        quality_metrics: Métricas de calidad agregadas
    """
    time_range: str
    start_date: datetime
    end_date: datetime
    total_sessions: int = 0
    total_duration_hours: float = 0.0
    total_data_gb: float = 0.0
    unique_cameras: int = 0
    average_viewers: float = 0.0
    peak_viewers: int = 0
    peak_datetime: Optional[datetime] = None
    most_active_cameras: List[CameraActivity] = field(default_factory=list)
    error_rate: float = 0.0
    average_session_duration_minutes: float = 0.0
    uptime_percentage: float = 0.0
    protocol_distribution: Dict[str, float] = field(default_factory=dict)
    hourly_distribution: Dict[int, int] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicializa valores por defecto para distribuciones."""
        if not self.protocol_distribution:
            self.protocol_distribution = {
                "rtsp": 0.0,
                "rtmp": 0.0,
                "hls": 0.0,
                "webrtc": 0.0
            }
        
        if not self.quality_metrics:
            self.quality_metrics = {
                "average_fps": 0.0,
                "average_bitrate_kbps": 0.0,
                "average_quality_score": 0.0,
                "sessions_optimal": 0,
                "sessions_degraded": 0,
                "sessions_poor": 0
            }
    
    @property
    def total_bandwidth_gbps(self) -> float:
        """Calcula el ancho de banda promedio en Gbps."""
        if self.total_duration_hours == 0:
            return 0.0
        return (self.total_data_gb * 8) / (self.total_duration_hours * 3600)
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito (100 - error_rate)."""
        return 100.0 - self.error_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "time_range": self.time_range,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_sessions": self.total_sessions,
            "total_duration_hours": round(self.total_duration_hours, 1),
            "total_data_gb": round(self.total_data_gb, 2),
            "total_bandwidth_gbps": round(self.total_bandwidth_gbps, 3),
            "unique_cameras": self.unique_cameras,
            "average_viewers": round(self.average_viewers, 1),
            "peak_viewers": self.peak_viewers,
            "peak_datetime": self.peak_datetime.isoformat() if self.peak_datetime else None,
            "most_active_cameras": [cam.to_dict() for cam in self.most_active_cameras],
            "error_rate": round(self.error_rate, 1),
            "success_rate": round(self.success_rate, 1),
            "average_session_duration_minutes": round(self.average_session_duration_minutes, 1),
            "uptime_percentage": round(self.uptime_percentage, 1),
            "protocol_distribution": self.protocol_distribution,
            "hourly_distribution": self.hourly_distribution,
            "quality_metrics": self.quality_metrics
        }


# === MODELOS DE ANALYTICS ===

@dataclass
class ViewerTrendData:
    """Datos de tendencia de viewers para analytics."""
    timestamp: datetime
    viewer_count: int
    average_viewers: float
    peak_viewers: int
    protocol_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "viewer_count": self.viewer_count,
            "average_viewers": self.average_viewers,
            "peak_viewers": self.peak_viewers,
            "protocol_breakdown": self.protocol_breakdown
        }


@dataclass
class EngagementMetrics:
    """Métricas de engagement de viewers."""
    average_watch_percentage: float = 0.0
    return_viewer_rate: float = 0.0
    bounce_rate: float = 0.0
    engagement_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convierte a diccionario."""
        return {
            "average_watch_percentage": self.average_watch_percentage,
            "return_viewer_rate": self.return_viewer_rate,
            "bounce_rate": self.bounce_rate,
            "engagement_score": self.engagement_score
        }


@dataclass
class GeographicDistribution:
    """Distribución geográfica de viewers."""
    country_code: str
    country_name: str
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    city_name: Optional[str] = None
    viewer_count: int = 0
    percentage: float = 0.0
    average_session_minutes: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "state_code": self.state_code,
            "state_name": self.state_name,
            "city_name": self.city_name,
            "viewer_count": self.viewer_count,
            "percentage": round(self.percentage, 1),
            "average_session_minutes": round(self.average_session_minutes, 1)
        }


@dataclass
class ViewerAnalytics:
    """
    Analytics detallados de audiencia.
    
    Proporciona información agregada sobre el comportamiento
    y características de los viewers.
    
    Attributes:
        time_range: Período analizado
        camera_id: ID de cámara específica o None para global
        total_unique_viewers: Viewers únicos totales
        total_viewing_hours: Horas totales de visualización
        average_session_duration_minutes: Duración promedio
        peak_concurrent_viewers: Pico de viewers simultáneos
        peak_time: Momento del pico
        viewer_trends: Tendencias temporales
        protocol_distribution: Distribución por protocolo
        device_distribution: Distribución por dispositivo
        geographic_distribution: Distribución geográfica
        engagement_metrics: Métricas de engagement
        quality_metrics: Métricas de calidad percibida
    """
    time_range: str
    total_unique_viewers: int = 0
    total_viewing_hours: float = 0.0
    average_session_duration_minutes: float = 0.0
    peak_concurrent_viewers: int = 0
    peak_time: Optional[datetime] = None
    camera_id: Optional[str] = None
    viewer_trends: List[ViewerTrendData] = field(default_factory=list)
    protocol_distribution: Dict[str, float] = field(default_factory=dict)
    device_distribution: Dict[str, float] = field(default_factory=dict)
    geographic_distribution: List[GeographicDistribution] = field(default_factory=list)
    engagement_metrics: Optional[EngagementMetrics] = None
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if not self.engagement_metrics:
            self.engagement_metrics = EngagementMetrics()
        
        if not self.quality_metrics:
            self.quality_metrics = {
                "average_buffer_ratio": 0.0,
                "average_startup_time": 0.0,
                "quality_switch_rate": 0.0,
                "error_rate": 0.0
            }
    
    @property
    def viewer_retention_rate(self) -> float:
        """Calcula la tasa de retención de viewers."""
        if self.total_unique_viewers == 0:
            return 0.0
        return self.engagement_metrics.return_viewer_rate if self.engagement_metrics else 0.0
    
    def get_top_locations(self, limit: int = 10) -> List[GeographicDistribution]:
        """Obtiene las top ubicaciones por viewers."""
        return sorted(
            self.geographic_distribution,
            key=lambda x: x.viewer_count,
            reverse=True
        )[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "time_range": self.time_range,
            "camera_id": self.camera_id,
            "total_unique_viewers": self.total_unique_viewers,
            "total_viewing_hours": round(self.total_viewing_hours, 1),
            "average_session_duration_minutes": round(self.average_session_duration_minutes, 1),
            "peak_concurrent_viewers": self.peak_concurrent_viewers,
            "peak_time": self.peak_time.isoformat() if self.peak_time else None,
            "viewer_retention_rate": round(self.viewer_retention_rate, 1),
            "viewer_trends": [t.to_dict() for t in self.viewer_trends],
            "protocol_distribution": self.protocol_distribution,
            "device_distribution": self.device_distribution,
            "geographic_distribution": [g.to_dict() for g in self.geographic_distribution],
            "top_locations": [g.to_dict() for g in self.get_top_locations()],
            "engagement_metrics": self.engagement_metrics.to_dict() if self.engagement_metrics else {},
            "quality_metrics": self.quality_metrics
        }


# === FUNCIONES AUXILIARES ===

def calculate_metrics_summary(metrics_list: List[PublishMetrics]) -> Dict[str, Any]:
    """
    Calcula un resumen estadístico de una lista de métricas.
    
    Args:
        metrics_list: Lista de métricas para analizar
        
    Returns:
        Diccionario con estadísticas agregadas
    """
    if not metrics_list:
        return {
            "count": 0,
            "avg_fps": 0.0,
            "min_fps": 0.0,
            "max_fps": 0.0,
            "avg_bitrate_kbps": 0.0,
            "avg_viewers": 0.0,
            "peak_viewers": 0,
            "avg_quality_score": 0.0
        }
    
    fps_values = [m.fps for m in metrics_list]
    bitrate_values = [m.bitrate_kbps for m in metrics_list]
    viewer_values = [m.viewers for m in metrics_list]
    quality_scores = [m.quality_score for m in metrics_list if m.quality_score is not None]
    
    return {
        "count": len(metrics_list),
        "avg_fps": sum(fps_values) / len(fps_values),
        "min_fps": min(fps_values),
        "max_fps": max(fps_values),
        "avg_bitrate_kbps": sum(bitrate_values) / len(bitrate_values),
        "avg_viewers": sum(viewer_values) / len(viewer_values) if viewer_values else 0,
        "peak_viewers": max(viewer_values) if viewer_values else 0,
        "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    }


def aggregate_camera_activities(
    sessions: List[PublishingHistorySession]
) -> List[CameraActivity]:
    """
    Agrega sesiones por cámara para generar actividades.
    
    Args:
        sessions: Lista de sesiones históricas
        
    Returns:
        Lista de actividades por cámara ordenada por total de sesiones
    """
    activities: Dict[str, CameraActivity] = {}
    
    for session in sessions:
        if session.camera_id not in activities:
            activities[session.camera_id] = CameraActivity(
                camera_id=session.camera_id,
                camera_name=session.camera_name or session.camera_id
            )
        
        activity = activities[session.camera_id]
        activity.total_sessions += 1
        activity.total_duration_hours += session.duration_seconds / 3600
        activity.total_data_gb += session.total_bytes / (1024 ** 3)
        activity.peak_viewers = max(activity.peak_viewers, session.peak_viewers)
        
        # Actualizar promedios
        if activity.total_sessions > 0:
            activity.average_viewers = (
                (activity.average_viewers * (activity.total_sessions - 1) + session.average_viewers) /
                activity.total_sessions
            )
            activity.average_quality_score = (
                (activity.average_quality_score * (activity.total_sessions - 1) + session.quality_score) /
                activity.total_sessions
            )
        
        # Actualizar error rate
        if session.error_count > 0 or session.termination_reason == TerminationReason.ERROR:
            error_sessions = activity.error_rate * activity.total_sessions / 100
            activity.error_rate = ((error_sessions + 1) / activity.total_sessions) * 100
        
        # Actualizar última actividad
        if not activity.last_active or session.start_time > activity.last_active:
            activity.last_active = session.start_time
    
    # Ordenar por total de sesiones descendente
    return sorted(activities.values(), key=lambda x: x.total_sessions, reverse=True)