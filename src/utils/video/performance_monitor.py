"""
Monitor de performance para streaming de video.

Proporciona herramientas para monitorear y optimizar el rendimiento
del sistema de streaming.
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta
import threading


@dataclass
class PerformanceSnapshot:
    """Snapshot de métricas de rendimiento en un momento dado."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    active_streams: int
    total_fps: float
    avg_latency_ms: float
    network_mbps: float


class StreamPerformanceMonitor:
    """
    Monitor de rendimiento para streams de video.
    
    Mantiene estadísticas de CPU, memoria, red y métricas específicas
    de streaming para optimizar el rendimiento.
    """
    
    def __init__(self, history_size: int = 60):
        """
        Inicializa el monitor.
        
        Args:
            history_size: Cantidad de snapshots históricos a mantener
        """
        self.history_size = history_size
        self.history: deque = deque(maxlen=history_size)
        self.logger = logging.getLogger(__name__)
        
        # Métricas por stream
        self._stream_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Control de monitoreo
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = 1.0  # segundos
        
        # Umbrales de alerta
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 80.0  # %
        self.latency_threshold = 200.0  # ms
        
        # Proceso actual para métricas
        self._process = psutil.Process()
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Inicia el monitoreo periódico.
        
        Args:
            interval: Intervalo de muestreo en segundos
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_interval = interval
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info(f"Monitoreo de performance iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self) -> None:
        """Detiene el monitoreo periódico."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        
        self.logger.info("Monitoreo de performance detenido")
    
    def _monitor_loop(self) -> None:
        """Loop principal de monitoreo."""
        while self._monitoring:
            try:
                snapshot = self.take_snapshot()
                self._check_thresholds(snapshot)
                time.sleep(self._monitor_interval)
            except Exception as e:
                self.logger.error(f"Error en loop de monitoreo: {e}")
    
    def register_stream(self, stream_id: str) -> None:
        """Registra un nuevo stream para monitoreo."""
        self._stream_metrics[stream_id] = {
            'fps': 0.0,
            'latency_ms': 0.0,
            'frames_processed': 0,
            'bytes_processed': 0,
            'start_time': time.time()
        }
    
    def unregister_stream(self, stream_id: str) -> None:
        """Elimina un stream del monitoreo."""
        self._stream_metrics.pop(stream_id, None)
    
    def update_stream_metrics(
        self,
        stream_id: str,
        fps: Optional[float] = None,
        latency_ms: Optional[float] = None,
        frames: Optional[int] = None,
        bytes_processed: Optional[int] = None
    ) -> None:
        """
        Actualiza métricas de un stream específico.
        
        Args:
            stream_id: ID del stream
            fps: Frames por segundo actual
            latency_ms: Latencia en milisegundos
            frames: Frames procesados (incremento)
            bytes_processed: Bytes procesados (incremento)
        """
        if stream_id not in self._stream_metrics:
            return
        
        metrics = self._stream_metrics[stream_id]
        
        if fps is not None:
            metrics['fps'] = fps
        if latency_ms is not None:
            metrics['latency_ms'] = latency_ms
        if frames is not None:
            metrics['frames_processed'] += frames
        if bytes_processed is not None:
            metrics['bytes_processed'] += bytes_processed
    
    def take_snapshot(self) -> PerformanceSnapshot:
        """Toma un snapshot actual de las métricas de rendimiento."""
        # Métricas del sistema
        cpu_percent = self._process.cpu_percent(interval=0.1)
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = self._process.memory_percent()
        
        # Métricas agregadas de streams
        active_streams = len(self._stream_metrics)
        total_fps = sum(m['fps'] for m in self._stream_metrics.values())
        
        avg_latency = 0.0
        if active_streams > 0:
            total_latency = sum(m['latency_ms'] for m in self._stream_metrics.values())
            avg_latency = total_latency / active_streams
        
        # Calcular ancho de banda aproximado
        total_bytes = sum(m['bytes_processed'] for m in self._stream_metrics.values())
        total_mbps = 0.0
        if active_streams > 0:
            # Asumir que los bytes son del último segundo
            total_mbps = (total_bytes * 8) / 1_000_000
        
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            active_streams=active_streams,
            total_fps=total_fps,
            avg_latency_ms=avg_latency,
            network_mbps=total_mbps
        )
        
        self.history.append(snapshot)
        return snapshot
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas actuales en formato diccionario."""
        if not self.history:
            return {}
        
        current = self.history[-1]
        return {
            'timestamp': current.timestamp.isoformat(),
            'cpu_percent': current.cpu_percent,
            'memory_mb': current.memory_mb,
            'memory_percent': current.memory_percent,
            'active_streams': current.active_streams,
            'total_fps': current.total_fps,
            'avg_latency_ms': current.avg_latency_ms,
            'network_mbps': current.network_mbps,
            'health_status': self._calculate_health_status(current)
        }
    
    def get_average_metrics(self, seconds: int = 60) -> Dict[str, Any]:
        """
        Calcula métricas promedio de los últimos N segundos.
        
        Args:
            seconds: Ventana de tiempo en segundos
            
        Returns:
            Diccionario con métricas promedio
        """
        if not self.history:
            return {}
        
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        recent_snapshots = [s for s in self.history if s.timestamp >= cutoff_time]
        
        if not recent_snapshots:
            return {}
        
        return {
            'window_seconds': seconds,
            'samples': len(recent_snapshots),
            'avg_cpu_percent': sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots),
            'avg_memory_mb': sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots),
            'avg_fps': sum(s.total_fps for s in recent_snapshots) / len(recent_snapshots),
            'avg_latency_ms': sum(s.avg_latency_ms for s in recent_snapshots) / len(recent_snapshots),
            'peak_cpu': max(s.cpu_percent for s in recent_snapshots),
            'peak_memory_mb': max(s.memory_mb for s in recent_snapshots)
        }
    
    def _check_thresholds(self, snapshot: PerformanceSnapshot) -> None:
        """Verifica umbrales y emite alertas si es necesario."""
        alerts = []
        
        if snapshot.cpu_percent > self.cpu_threshold:
            alerts.append(f"CPU alto: {snapshot.cpu_percent:.1f}%")
        
        if snapshot.memory_percent > self.memory_threshold:
            alerts.append(f"Memoria alta: {snapshot.memory_percent:.1f}%")
        
        if snapshot.avg_latency_ms > self.latency_threshold:
            alerts.append(f"Latencia alta: {snapshot.avg_latency_ms:.0f}ms")
        
        if alerts:
            self.logger.warning(f"Alertas de performance: {', '.join(alerts)}")
    
    def _calculate_health_status(self, snapshot: PerformanceSnapshot) -> str:
        """
        Calcula el estado de salud basado en las métricas.
        
        Returns:
            'good', 'warning', o 'critical'
        """
        if (snapshot.cpu_percent > 90 or 
            snapshot.memory_percent > 90 or 
            snapshot.avg_latency_ms > 300):
            return 'critical'
        elif (snapshot.cpu_percent > self.cpu_threshold or 
              snapshot.memory_percent > self.memory_threshold or 
              snapshot.avg_latency_ms > self.latency_threshold):
            return 'warning'
        else:
            return 'good'
    
    def get_optimization_suggestions(self) -> List[str]:
        """
        Genera sugerencias de optimización basadas en las métricas actuales.
        
        Returns:
            Lista de sugerencias de optimización
        """
        suggestions = []
        
        if not self.history:
            return suggestions
        
        current = self.history[-1]
        avg_metrics = self.get_average_metrics(60)
        
        # CPU
        if current.cpu_percent > self.cpu_threshold:
            suggestions.append("Reducir FPS objetivo o resolución para disminuir uso de CPU")
        
        # Memoria
        if current.memory_percent > self.memory_threshold:
            suggestions.append("Reducir buffer de frames o cantidad de streams simultáneos")
        
        # Latencia
        if current.avg_latency_ms > self.latency_threshold:
            suggestions.append("Verificar conexión de red o reducir calidad de stream")
        
        # FPS bajo
        if avg_metrics.get('avg_fps', 0) < 15 * current.active_streams:
            suggestions.append("FPS bajo detectado, considerar optimizar procesamiento de frames")
        
        return suggestions
    
    def reset_metrics(self) -> None:
        """Reinicia todas las métricas."""
        self.history.clear()
        self._stream_metrics.clear()
        self.logger.info("Métricas de performance reiniciadas")