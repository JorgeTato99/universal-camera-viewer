"""
Modelo de métricas de streaming.

Mantiene estadísticas y métricas de rendimiento para streams.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import deque


@dataclass
class StreamMetrics:
    """
    Métricas de rendimiento para un stream de video.
    
    Attributes:
        stream_id: ID del stream
        fps_history: Historial de FPS (últimos N valores)
        latency_history: Historial de latencia en ms
        bandwidth_kbps: Ancho de banda actual en kbps
        total_frames: Total de frames procesados
        dropped_frames: Total de frames perdidos
        error_count: Contador de errores
        reconnect_count: Contador de reconexiones
        start_time: Tiempo de inicio del stream
        last_update: Última actualización de métricas
    """
    
    # Identificador
    stream_id: str
    
    # Historial de métricas (ventana deslizante)
    fps_history: deque = field(default_factory=lambda: deque(maxlen=30))
    latency_history: deque = field(default_factory=lambda: deque(maxlen=30))
    bandwidth_history: deque = field(default_factory=lambda: deque(maxlen=30))
    
    # Contadores acumulados
    total_frames: int = 0
    dropped_frames: int = 0
    error_count: int = 0
    reconnect_count: int = 0
    
    # Ancho de banda
    bandwidth_kbps: float = 0.0
    total_bytes: int = 0
    
    # Timestamps
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    
    # Estadísticas calculadas
    _avg_fps: float = 0.0
    _avg_latency: float = 0.0
    _avg_bandwidth: float = 0.0
    
    def update_fps(self, fps: float) -> None:
        """Actualiza el FPS actual."""
        self.fps_history.append(fps)
        self._avg_fps = sum(self.fps_history) / len(self.fps_history)
        self.last_update = datetime.now()
    
    def update_latency(self, latency_ms: float) -> None:
        """Actualiza la latencia actual en ms."""
        self.latency_history.append(latency_ms)
        self._avg_latency = sum(self.latency_history) / len(self.latency_history)
        self.last_update = datetime.now()
    
    def update_bandwidth(self, bytes_received: int, time_delta: float) -> None:
        """
        Actualiza el ancho de banda.
        
        Args:
            bytes_received: Bytes recibidos
            time_delta: Tiempo transcurrido en segundos
        """
        if time_delta > 0:
            kbps = (bytes_received * 8 / 1000) / time_delta
            self.bandwidth_history.append(kbps)
            self.bandwidth_kbps = kbps
            self._avg_bandwidth = sum(self.bandwidth_history) / len(self.bandwidth_history)
            self.total_bytes += bytes_received
        self.last_update = datetime.now()
    
    def increment_frame_count(self) -> None:
        """Incrementa el contador de frames."""
        self.total_frames += 1
        self.last_update = datetime.now()
    
    def increment_dropped_frames(self, count: int = 1) -> None:
        """Incrementa el contador de frames perdidos."""
        self.dropped_frames += count
        self.last_update = datetime.now()
    
    def increment_error_count(self) -> None:
        """Incrementa el contador de errores."""
        self.error_count += 1
        self.last_update = datetime.now()
    
    def increment_reconnect_count(self) -> None:
        """Incrementa el contador de reconexiones."""
        self.reconnect_count += 1
        self.last_update = datetime.now()
    
    def get_current_fps(self) -> float:
        """Obtiene el FPS actual (último valor)."""
        return self.fps_history[-1] if self.fps_history else 0.0
    
    def get_average_fps(self) -> float:
        """Obtiene el FPS promedio."""
        return self._avg_fps
    
    def get_current_latency(self) -> float:
        """Obtiene la latencia actual en ms."""
        return self.latency_history[-1] if self.latency_history else 0.0
    
    def get_average_latency(self) -> float:
        """Obtiene la latencia promedio en ms."""
        return self._avg_latency
    
    def get_drop_rate(self) -> float:
        """Calcula la tasa de pérdida de frames (%)."""
        if self.total_frames == 0:
            return 0.0
        return (self.dropped_frames / self.total_frames) * 100
    
    def get_uptime(self) -> timedelta:
        """Obtiene el tiempo de actividad."""
        return datetime.now() - self.start_time
    
    def get_health_score(self) -> float:
        """
        Calcula un score de salud del stream (0-100).
        
        Basado en:
        - FPS actual vs objetivo
        - Tasa de pérdida de frames
        - Cantidad de errores
        - Latencia
        """
        score = 100.0
        
        # Penalizar por bajo FPS (asumiendo objetivo de 30 FPS)
        if self._avg_fps < 30:
            fps_penalty = (30 - self._avg_fps) * 2
            score -= min(fps_penalty, 30)
        
        # Penalizar por pérdida de frames
        drop_rate = self.get_drop_rate()
        if drop_rate > 0:
            score -= min(drop_rate * 2, 20)
        
        # Penalizar por errores
        if self.error_count > 0:
            error_penalty = min(self.error_count * 5, 20)
            score -= error_penalty
        
        # Penalizar por alta latencia (>200ms es problemático)
        if self._avg_latency > 200:
            latency_penalty = min((self._avg_latency - 200) / 10, 20)
            score -= latency_penalty
        
        return max(0.0, score)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las métricas a diccionario."""
        uptime = self.get_uptime()
        
        return {
            'stream_id': self.stream_id,
            'current_fps': self.get_current_fps(),
            'average_fps': self.get_average_fps(),
            'current_latency_ms': self.get_current_latency(),
            'average_latency_ms': self.get_average_latency(),
            'bandwidth_kbps': self.bandwidth_kbps,
            'average_bandwidth_kbps': self._avg_bandwidth,
            'total_frames': self.total_frames,
            'dropped_frames': self.dropped_frames,
            'drop_rate_percent': self.get_drop_rate(),
            'error_count': self.error_count,
            'reconnect_count': self.reconnect_count,
            'total_bytes': self.total_bytes,
            'uptime_seconds': uptime.total_seconds(),
            'health_score': self.get_health_score(),
            'last_update': self.last_update.isoformat()
        }
    
    def get_summary(self) -> str:
        """Obtiene un resumen textual de las métricas."""
        return (
            f"FPS: {self.get_current_fps():.1f} (avg: {self.get_average_fps():.1f}) | "
            f"Latency: {self.get_current_latency():.0f}ms | "
            f"Bandwidth: {self.bandwidth_kbps:.0f}kbps | "
            f"Drops: {self.get_drop_rate():.1f}% | "
            f"Health: {self.get_health_score():.0f}%"
        )