"""
Modelos de dominio para el sistema de publicación a MediaMTX.

Este módulo define las estructuras de datos principales para gestionar
la publicación de streams RTSP hacia servidores MediaMTX.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import asyncio

from models.publishing.metrics_models import PublishMetrics


class PublishStatus(Enum):
    """
    Estados posibles de un proceso de publicación.
    
    NOTA: Los estados STOPPING y RECONNECTING se manejan solo en el frontend
    para mejorar la UX sin agregar complejidad al backend.
    
    IMPORTANTE: Los valores usan MAYÚSCULAS para mantener consistencia
    con el enum PublishingStatus del frontend TypeScript.
    """
    IDLE = "IDLE"           # Sin actividad
    STARTING = "STARTING"   # Iniciando proceso de publicación
    PUBLISHING = "PUBLISHING"  # Publicando activamente
    ERROR = "ERROR"         # Error en la publicación
    STOPPED = "STOPPED"     # Detenido (para historial)


class PublishErrorType(Enum):
    """Tipos de errores en publicación."""
    CONNECTION_FAILED = "connection_failed"
    AUTHENTICATION_FAILED = "auth_failed"
    STREAM_UNAVAILABLE = "stream_unavailable"
    MEDIAMTX_UNREACHABLE = "mediamtx_unreachable"
    PROCESS_CRASHED = "process_crashed"
    LIMIT_EXCEEDED = "limit_exceeded"
    ALREADY_PUBLISHING = "already_publishing"
    NOT_PUBLISHING = "not_publishing"
    REMOTE_ERROR = "remote_error"
    INTERNAL_ERROR = "internal_error"
    AUTH_FAILED = "auth_failed"
    CONFIG_ERROR = "config_error"
    UNKNOWN = "unknown"


@dataclass
class PublisherProcess:
    """
    Representa un proceso de publicación activo.
    
    Attributes:
        camera_id: ID único de la cámara
        process: Referencia al proceso asyncio
        start_time: Momento de inicio
        status: Estado actual del proceso
        error_count: Contador de errores para reintentos
        last_error: Último error registrado
        metrics: Métricas del proceso
    """
    camera_id: str
    process: Optional[asyncio.subprocess.Process] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    status: PublishStatus = PublishStatus.IDLE
    error_count: int = 0
    last_error: Optional[str] = None
    error_type: Optional[PublishErrorType] = None
    metrics: Optional[PublishMetrics] = None
    
    @property
    def is_active(self) -> bool:
        """Verifica si el proceso está activo."""
        return self.status in [
            PublishStatus.STARTING,
            PublishStatus.PUBLISHING
        ]
    
    @property
    def uptime_seconds(self) -> float:
        """Calcula el tiempo activo en segundos."""
        if not self.is_active:
            return 0.0
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def update_metrics(self, metrics: PublishMetrics) -> None:
        """Actualiza métricas del proceso."""
        self.metrics = metrics


@dataclass
class PublishConfiguration:
    """
    Configuración para publicación a MediaMTX.
    
    Attributes:
        mediamtx_url: URL base del servidor MediaMTX
        api_enabled: Si la API está habilitada
        api_port: Puerto de la API (default: 9997)
        api_url: URL completa de la API (opcional, se calcula si no se proporciona)
        publish_prefix: Prefijo para paths (e.g., "cam_")
        publish_path_template: Template para generar paths
        auth_enabled: Si requiere autenticación
        username: Usuario para publicación
        password: Contraseña para publicación
        use_tcp: Forzar transporte TCP
        reconnect_delay: Segundos entre reintentos
        max_reconnects: Máximo de reintentos
        metadata: Metadatos adicionales
    """
    mediamtx_url: str
    api_enabled: bool = True
    api_port: int = 9997
    api_url: Optional[str] = None
    publish_prefix: str = "cam_"
    publish_path_template: str = "camera_{camera_id}"
    auth_enabled: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    use_tcp: bool = True
    reconnect_delay: float = 5.0
    max_reconnects: int = 10
    metadata: Optional[Dict[str, Any]] = None
    
    def get_api_url(self) -> str:
        """
        Obtiene o construye la URL completa de la API.
        
        Returns:
            URL de la API MediaMTX
        """
        # Si se proporcionó api_url explícita, usarla
        if self.api_url:
            return self.api_url
            
        # Si no, construirla desde mediamtx_url y api_port
        from urllib.parse import urlparse
        parsed = urlparse(self.mediamtx_url)
        host = parsed.hostname or "localhost"
        return f"http://{host}:{self.api_port}"
    
    def get_publish_path(self, camera_id: str) -> str:
        """
        Genera el path de publicación para una cámara.
        
        TODO: Este método actualmente usa una implementación simple.
        Cuando se integre completamente con MediaMTXPathsService,
        debería usar el sistema de plantillas completo que soporta:
        - {instance_id}: ID único de la instancia UCV
        - {camera_id}: ID completo de la cámara
        - {camera_code}: Código corto (primeros 8 chars)
        - {timestamp}: Marca de tiempo
        - {random}: Sufijo aleatorio
        
        Por ahora mantiene compatibilidad con el sistema existente.
        """
        # Tomar solo los primeros 8 caracteres del UUID
        short_id = camera_id.split('-')[0] if '-' in camera_id else camera_id[:8]
        return f"{self.publish_prefix}{short_id}"


@dataclass
class PublishResult:
    """Resultado de una operación de publicación."""
    success: bool
    camera_id: str
    publish_path: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[PublishErrorType] = None
    process_id: Optional[int] = None
    # Campos adicionales para publicación remota
    publish_url: Optional[str] = None
    webrtc_url: Optional[str] = None
    message: Optional[str] = None
    session_id: Optional[str] = None