"""
Servicio de métricas para MediaMTX.

Gestiona la recolección, análisis y cálculo de métricas
de calidad para las publicaciones de streaming.
"""

import asyncio

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
import aiohttp
from asyncio import Lock

from services.base_service import BaseService
from services.database.mediamtx_db_service import get_mediamtx_db_service
from utils.exceptions import ServiceError, MediaMTXAPIError
from models.publishing import PublishStatus
from services.logging_service import get_secure_logger


logger = logging.getLogger(__name__)


@dataclass
class MetricThresholds:
    """Umbrales para evaluación de métricas."""
    # FPS
    optimal_fps: float = 25.0
    acceptable_fps: float = 20.0
    poor_fps: float = 15.0
    
    # Bitrate (Kbps)
    optimal_bitrate: float = 2000.0
    acceptable_bitrate: float = 1000.0
    poor_bitrate: float = 500.0
    
    # Frame loss %
    optimal_frame_loss: float = 0.1
    acceptable_frame_loss: float = 1.0
    poor_frame_loss: float = 5.0
    
    # Latencia (ms)
    optimal_latency: float = 100.0
    acceptable_latency: float = 500.0
    poor_latency: float = 1000.0
    
    # CPU %
    warning_cpu: float = 70.0
    critical_cpu: float = 85.0
    
    # Memoria MB
    warning_memory: float = 1024.0
    critical_memory: float = 2048.0


@dataclass
class StreamMetrics:
    """Métricas de un stream individual."""
    camera_id: str
    timestamp: datetime
    fps: float
    bitrate_kbps: float
    frames: int
    dropped_frames: int
    viewer_count: int
    size_kb: float
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    latency_ms: Optional[float] = None
    
    @property
    def frame_loss_percent(self) -> float:
        """Calcula el porcentaje de frames perdidos."""
        if self.frames == 0:
            return 0.0
        return (self.dropped_frames / self.frames) * 100


@dataclass 
class MetricHistory:
    """Historial de métricas para análisis de tendencias."""
    camera_id: str
    metrics: List[StreamMetrics] = field(default_factory=list)
    max_history_size: int = 100
    
    def add_metric(self, metric: StreamMetrics) -> None:
        """Agrega una métrica al historial."""
        self.metrics.append(metric)
        # Mantener solo las últimas N métricas
        if len(self.metrics) > self.max_history_size:
            self.metrics = self.metrics[-self.max_history_size:]
    
    def get_recent_metrics(self, minutes: int = 5) -> List[StreamMetrics]:
        """Obtiene métricas recientes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [m for m in self.metrics if m.timestamp > cutoff_time]
    
    def calculate_trend(self, attribute: str, minutes: int = 5) -> Optional[float]:
        """
        Calcula la tendencia de un atributo.
        
        Returns:
            Pendiente de la regresión lineal (positiva = mejora, negativa = empeora)
        """
        recent = self.get_recent_metrics(minutes)
        if len(recent) < 2:
            return None
            
        values = [getattr(m, attribute) for m in recent]
        if not all(v is not None for v in values):
            return None
            
        # Regresión lineal simple
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator


class MediaMTXMetricsService(BaseService):
    """
    Servicio para gestión de métricas de MediaMTX.
    
    Responsabilidades:
    - Recolección periódica de métricas desde MediaMTX API
    - Cálculo de quality score
    - Detección de degradación y generación de alertas
    - Análisis de tendencias
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            self._metric_history: Dict[str, MetricHistory] = {}
            self._collection_tasks: Dict[str, asyncio.Task] = {}
            self._thresholds = MetricThresholds()
            self._session: Optional[aiohttp.ClientSession] = None
            
    async def initialize(self) -> None:
        """Inicializa el servicio."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        logger.info("MediaMTXMetricsService inicializado")
    
    async def shutdown(self) -> None:
        """Cierra el servicio y limpia recursos."""
        # Cancelar todas las tareas de recolección
        for task in self._collection_tasks.values():
            task.cancel()
        
        # Esperar a que terminen
        if self._collection_tasks:
            await asyncio.gather(*self._collection_tasks.values(), return_exceptions=True)
        
        # Cerrar sesión HTTP
        if self._session:
            await self._session.close()
            self._session = None
            
        logger.info("MediaMTXMetricsService cerrado")
    
    async def start_metric_collection(
        self,
        camera_id: str,
        mediamtx_api_url: str,
        publish_path: str,
        interval_seconds: float = 5.0
    ) -> None:
        """
        Inicia la recolección periódica de métricas para una cámara.
        
        Args:
            camera_id: ID de la cámara
            mediamtx_api_url: URL de la API de MediaMTX
            publish_path: Path de publicación en MediaMTX
            interval_seconds: Intervalo de recolección
        """
        # Detener recolección existente si hay
        await self.stop_metric_collection(camera_id)
        
        # Crear historial si no existe
        if camera_id not in self._metric_history:
            self._metric_history[camera_id] = MetricHistory(camera_id)
        
        # Crear tarea de recolección
        task = asyncio.create_task(
            self._collect_metrics_loop(
                camera_id,
                mediamtx_api_url,
                publish_path,
                interval_seconds
            )
        )
        self._collection_tasks[camera_id] = task
        
        logger.info(f"Iniciada recolección de métricas para {camera_id}")
    
    async def stop_metric_collection(self, camera_id: str) -> None:
        """Detiene la recolección de métricas para una cámara."""
        if camera_id in self._collection_tasks:
            task = self._collection_tasks[camera_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._collection_tasks[camera_id]
            logger.info(f"Detenida recolección de métricas para {camera_id}")
    
    async def _collect_metrics_loop(
        self,
        camera_id: str,
        api_url: str,
        publish_path: str,
        interval: float
    ) -> None:
        """Loop de recolección de métricas."""
        db_service = get_mediamtx_db_service()
        
        while True:
            try:
                # Recolectar métricas desde MediaMTX
                metrics = await self._fetch_mediamtx_metrics(
                    api_url,
                    publish_path
                )
                
                if metrics:
                    # Agregar al historial
                    self._metric_history[camera_id].add_metric(metrics)
                    
                    # Calcular quality score
                    quality_score = self.calculate_quality_score(metrics)
                    
                    # Guardar en BD
                    await db_service.save_publication_metric(
                        camera_id=camera_id,
                        metrics={
                            'fps': metrics.fps,
                            'bitrate_kbps': metrics.bitrate_kbps,
                            'frames': metrics.frames,
                            'dropped_frames': metrics.dropped_frames,
                            'viewer_count': metrics.viewer_count,
                            'size_kb': metrics.size_kb,
                            'cpu_usage_percent': metrics.cpu_usage_percent,
                            'memory_usage_mb': metrics.memory_usage_mb,
                            'quality_score': quality_score,
                            'timestamp': metrics.timestamp
                        }
                    )
                    
                    # Verificar alertas
                    await self._check_metric_alerts(camera_id, metrics, quality_score)
                    
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error recolectando métricas para {camera_id}: {e}")
                await asyncio.sleep(interval)
    
    async def _fetch_mediamtx_metrics(
        self,
        api_url: str,
        publish_path: str
    ) -> Optional[StreamMetrics]:
        """Obtiene métricas desde la API de MediaMTX."""
        if not self._session:
            return None
            
        try:
            # Consultar paths activos
            async with self._session.get(
                f"{api_url}/v3/paths/list",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                
                # Buscar nuestro path
                path_info = None
                for item in data.get('items', []):
                    if item.get('name') == publish_path:
                        path_info = item
                        break
                
                if not path_info:
                    return None
                
                # Extraer métricas
                source = path_info.get('source', {})
                readers = path_info.get('readers', [])
                
                # Calcular totales
                total_bytes = 0
                for reader in readers:
                    total_bytes += reader.get('bytesReceived', 0)
                
                return StreamMetrics(
                    camera_id=publish_path,  # Temporal, se sobreescribe en el loop
                    timestamp=datetime.utcnow(),
                    fps=25.0,  # MediaMTX no provee FPS directo, usar valor nominal
                    bitrate_kbps=(total_bytes * 8 / 1024) / 60,  # Aproximación
                    frames=0,  # No disponible directamente
                    dropped_frames=0,  # No disponible directamente
                    viewer_count=len(readers),
                    size_kb=total_bytes / 1024,
                    cpu_usage_percent=None,  # Requeriría métricas del sistema
                    memory_usage_mb=None,    # Requeriría métricas del sistema
                    latency_ms=None         # Requeriría medición activa
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo métricas de MediaMTX: {e}")
            return None
    
    def calculate_quality_score(self, metrics: StreamMetrics) -> float:
        """
        Calcula el quality score basado en múltiples factores.
        
        Fórmula:
        - FPS: 40%
        - Estabilidad de bitrate: 30%
        - Frame loss: 20%
        - Latencia: 10%
        
        Returns:
            Score entre 0 y 100
        """
        scores = []
        weights = []
        
        # Score de FPS (40%)
        if metrics.fps > 0:
            fps_score = min(100, (metrics.fps / self._thresholds.optimal_fps) * 100)
            scores.append(fps_score)
            weights.append(0.4)
        
        # Score de bitrate (30%)
        if metrics.bitrate_kbps > 0:
            bitrate_score = min(100, (metrics.bitrate_kbps / self._thresholds.optimal_bitrate) * 100)
            scores.append(bitrate_score)
            weights.append(0.3)
        
        # Score de frame loss (20%)
        frame_loss_score = max(0, 100 - (metrics.frame_loss_percent * 20))
        scores.append(frame_loss_score)
        weights.append(0.2)
        
        # Score de latencia (10%) - si está disponible
        if metrics.latency_ms is not None:
            latency_score = max(0, 100 - (metrics.latency_ms / self._thresholds.optimal_latency) * 100)
            scores.append(latency_score)
            weights.append(0.1)
        else:
            # Si no hay latencia, redistribuir el peso
            if weights:
                factor = 1.0 / sum(weights)
                weights = [w * factor for w in weights]
        
        # Calcular score ponderado
        if not scores:
            return 0.0
            
        total_score = sum(s * w for s, w in zip(scores, weights))
        
        # Penalizaciones adicionales
        if metrics.cpu_usage_percent and metrics.cpu_usage_percent > self._thresholds.critical_cpu:
            total_score *= 0.8  # Penalización del 20% por CPU crítico
            
        if metrics.memory_usage_mb and metrics.memory_usage_mb > self._thresholds.critical_memory:
            total_score *= 0.9  # Penalización del 10% por memoria crítica
        
        return round(min(100, max(0, total_score)), 2)
    
    async def _check_metric_alerts(
        self,
        camera_id: str,
        metrics: StreamMetrics,
        quality_score: float
    ) -> None:
        """Verifica y genera alertas basadas en métricas."""
        alerts = []
        
        # Alerta por quality score bajo
        if quality_score < 50:
            severity = "critical" if quality_score < 30 else "warning"
            alerts.append({
                'severity': severity,
                'alert_type': 'performance',
                'title': f'Calidad de transmisión {severity}',
                'message': f'La calidad de transmisión de {camera_id} es {quality_score:.1f}/100',
                'camera_id': camera_id
            })
        
        # Alerta por FPS bajo
        if metrics.fps < self._thresholds.poor_fps:
            alerts.append({
                'severity': 'warning',
                'alert_type': 'performance',
                'title': 'FPS bajo detectado',
                'message': f'FPS actual: {metrics.fps:.1f}, esperado: {self._thresholds.optimal_fps}',
                'camera_id': camera_id
            })
        
        # Alerta por pérdida de frames
        if metrics.frame_loss_percent > self._thresholds.poor_frame_loss:
            alerts.append({
                'severity': 'error',
                'alert_type': 'performance',
                'title': 'Alta pérdida de frames',
                'message': f'Pérdida de frames: {metrics.frame_loss_percent:.1f}%',
                'camera_id': camera_id
            })
        
        # Alerta por uso de recursos
        if metrics.cpu_usage_percent and metrics.cpu_usage_percent > self._thresholds.critical_cpu:
            alerts.append({
                'severity': 'critical',
                'alert_type': 'resource',
                'title': 'Uso crítico de CPU',
                'message': f'CPU al {metrics.cpu_usage_percent:.1f}%',
                'camera_id': camera_id
            })
        
        # Verificar tendencias
        history = self._metric_history.get(camera_id)
        if history:
            # Tendencia de FPS
            fps_trend = history.calculate_trend('fps', minutes=5)
            if fps_trend is not None and fps_trend < -2.0:  # Cayendo más de 2 FPS/min
                alerts.append({
                    'severity': 'warning',
                    'alert_type': 'performance',
                    'title': 'Degradación de FPS detectada',
                    'message': f'El FPS está cayendo rápidamente',
                    'camera_id': camera_id
                })
        
        # Emitir alertas
        for alert in alerts:
            self._emit_event('metric_alert', alert)
    
    def get_current_metrics(self, camera_id: str) -> Optional[StreamMetrics]:
        """Obtiene las métricas más recientes de una cámara."""
        history = self._metric_history.get(camera_id)
        if history and history.metrics:
            return history.metrics[-1]
        return None
    
    def get_metric_trends(
        self,
        camera_id: str,
        minutes: int = 5
    ) -> Dict[str, Optional[float]]:
        """
        Obtiene las tendencias de las métricas principales.
        
        Returns:
            Dict con tendencias por métrica (positivo = mejora)
        """
        history = self._metric_history.get(camera_id)
        if not history:
            return {}
            
        return {
            'fps_trend': history.calculate_trend('fps', minutes),
            'bitrate_trend': history.calculate_trend('bitrate_kbps', minutes),
            'frame_loss_trend': history.calculate_trend('frame_loss_percent', minutes),
            'viewer_trend': history.calculate_trend('viewer_count', minutes)
        }
    
    def get_metric_statistics(
        self,
        camera_id: str,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de las métricas."""
        history = self._metric_history.get(camera_id)
        if not history:
            return {}
            
        recent = history.get_recent_metrics(minutes)
        if not recent:
            return {}
            
        # Calcular estadísticas
        fps_values = [m.fps for m in recent if m.fps > 0]
        bitrate_values = [m.bitrate_kbps for m in recent if m.bitrate_kbps > 0]
        viewer_values = [m.viewer_count for m in recent]
        
        stats = {}
        
        if fps_values:
            stats['fps'] = {
                'avg': statistics.mean(fps_values),
                'min': min(fps_values),
                'max': max(fps_values),
                'stdev': statistics.stdev(fps_values) if len(fps_values) > 1 else 0
            }
            
        if bitrate_values:
            stats['bitrate_kbps'] = {
                'avg': statistics.mean(bitrate_values),
                'min': min(bitrate_values),
                'max': max(bitrate_values),
                'stdev': statistics.stdev(bitrate_values) if len(bitrate_values) > 1 else 0
            }
            
        if viewer_values:
            stats['viewers'] = {
                'avg': statistics.mean(viewer_values),
                'min': min(viewer_values),
                'max': max(viewer_values),
                'total_unique': len(set(viewer_values))  # Aproximación
            }
            
        return stats


# Singleton
_metrics_service_instance = None


def get_mediamtx_metrics_service() -> MediaMTXMetricsService:
    """Obtiene la instancia singleton del servicio de métricas."""
    global _metrics_service_instance
    if _metrics_service_instance is None:
        _metrics_service_instance = MediaMTXMetricsService()
    return _metrics_service_instance