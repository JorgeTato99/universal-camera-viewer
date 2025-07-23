"""
Servicio de analytics para viewers de MediaMTX.

Gestiona el tracking, análisis y estadísticas de viewers de streams,
preparado para futuras mejoras cuando MediaMTX exponga más información.
"""

import asyncio
import logging

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import random

from services.base_service import BaseService
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.publishing import MediaMTXClient
from utils.exceptions import ServiceError
from api.schemas.requests.mediamtx_requests import ViewerProtocol
from models.publishing.mediamtx_models import PathInfo, PathReader
from services.logging_service import get_secure_logger


logger = logging.getLogger(__name__)


@dataclass
class ViewerSnapshot:
    """Snapshot de viewers en un momento específico."""
    timestamp: datetime
    camera_id: str
    total_viewers: int
    viewers_by_protocol: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ViewerSession:
    """Sesión de un viewer individual."""
    viewer_id: str
    camera_id: str
    protocol: ViewerProtocol
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    ip_address: Optional[str] = None  # TODO: Cuando MediaMTX lo proporcione
    user_agent: Optional[str] = None  # TODO: Cuando MediaMTX lo proporcione
    bytes_received: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Mapeo de tipos MediaMTX a protocolos
MEDIAMTX_PROTOCOL_MAP = {
    "rtspSession": ViewerProtocol.RTSP,
    "rtspsSession": ViewerProtocol.RTSP,  # RTSP seguro
    "rtmpConn": ViewerProtocol.RTMP,
    "hlsMuxer": ViewerProtocol.HLS,
    "webRTCSession": ViewerProtocol.WEBRTC,
    "srtConn": ViewerProtocol.SRT
}


class ViewerAnalyticsService(BaseService):
    """
    Servicio para analytics de viewers de MediaMTX.
    
    IMPORTANTE: Actualmente MediaMTX solo proporciona conteo básico de viewers.
    Este servicio está preparado para futuras mejoras cuando MediaMTX exponga
    más información detallada o se implemente captura via logs/webhooks.
    
    Responsabilidades:
    - Recolectar snapshots de viewers periódicamente
    - Analizar tendencias y patrones
    - Generar estadísticas por protocolo
    - Proporcionar datos para visualización
    - Mantener historial de viewers
    
    TODO: Cuando MediaMTX proporcione más información:
    - Implementar tracking individual de viewers
    - Capturar IPs para análisis geográfico
    - Registrar duración de sesiones individuales
    - Análisis de calidad por viewer
    """
    
    def __init__(self):
        """Inicializa el servicio de analytics."""
        super().__init__()
        self._db_service = None
        self._mediamtx_client: Optional[MediaMTXClient] = None
        self._snapshots: Dict[str, List[ViewerSnapshot]] = defaultdict(list)
        self._active_sessions: Dict[str, ViewerSession] = {}
        self._snapshot_interval = 30  # segundos
        self._max_snapshots_memory = 120  # mantener 1 hora en memoria
        self._collection_tasks: Dict[str, asyncio.Task] = {}
        self.logger = get_secure_logger("services.publishing.viewer_analytics_service")
        
    async def initialize(self) -> None:
        """Inicializa el servicio y sus dependencias."""
        self.logger.info("Inicializando ViewerAnalyticsService")
        
        try:
            self._db_service = get_mediamtx_db_service()
            # TODO: MediaMTXClient necesita URL de API para inicializarse
            # Por ahora no inicializar, se debe pasar desde el presenter
            # self._mediamtx_client = MediaMTXClient(api_url)
            
            # TODO: Cargar sesiones activas desde BD si es necesario
            
            self.logger.info("ViewerAnalyticsService inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando servicio: {e}")
            raise ServiceError(
                f"Error inicializando ViewerAnalyticsService: {str(e)}",
                error_code="VIEWER_SERVICE_INIT_ERROR"
            )
    
    async def start_tracking(self, camera_id: str, publish_path: str) -> None:
        """
        Inicia el tracking de viewers para una cámara.
        
        Args:
            camera_id: ID de la cámara
            publish_path: Path de publicación en MediaMTX
        """
        if camera_id in self._collection_tasks:
            self.logger.warning(f"Tracking ya activo para {camera_id}")
            return
            
        self.logger.info(f"Iniciando tracking de viewers para {camera_id} en path {publish_path}")
        
        # Crear tarea de recolección
        task = asyncio.create_task(
            self._collect_viewer_snapshots(camera_id, publish_path),
            name=f"viewer_tracking_{camera_id}"
        )
        self._collection_tasks[camera_id] = task
    
    async def stop_tracking(self, camera_id: str) -> None:
        """
        Detiene el tracking de viewers para una cámara.
        
        Args:
            camera_id: ID de la cámara
        """
        if camera_id not in self._collection_tasks:
            return
            
        self.logger.info(f"Deteniendo tracking de viewers para {camera_id}")
        
        task = self._collection_tasks.pop(camera_id)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Guardar snapshots pendientes
        await self._save_pending_snapshots(camera_id)
    
    async def _collect_viewer_snapshots(self, camera_id: str, publish_path: str) -> None:
        """
        Recolecta snapshots de viewers periódicamente.
        
        Args:
            camera_id: ID de la cámara
            publish_path: Path de publicación
        """
        while True:
            try:
                # Obtener información de viewers desde MediaMTX
                viewer_data = await self._get_viewer_data(publish_path)
                
                if viewer_data:
                    # Crear snapshot
                    snapshot = ViewerSnapshot(
                        timestamp=datetime.now(),
                        camera_id=camera_id,
                        total_viewers=viewer_data["total"],
                        viewers_by_protocol=viewer_data["by_protocol"]
                    )
                    
                    # Almacenar en memoria
                    self._snapshots[camera_id].append(snapshot)
                    
                    # Limpiar snapshots antiguos
                    self._cleanup_old_snapshots(camera_id)
                    
                    # Guardar en BD periódicamente
                    if len(self._snapshots[camera_id]) % 10 == 0:
                        await self._save_snapshot_to_db(snapshot)
                
                await asyncio.sleep(self._snapshot_interval)
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Error recolectando snapshots para {camera_id}: {e}")
                await asyncio.sleep(self._snapshot_interval)
    
    async def _get_viewer_data(self, publish_path: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de viewers desde MediaMTX.
        
        Args:
            publish_path: Path de publicación
            
        Returns:
            Datos de viewers o None si hay error
        """
        try:
            if not self._mediamtx_client:
                return None
                
            paths = await self._mediamtx_client.list_paths()
            
            for path in paths:
                if path.name == publish_path:
                    # Contar viewers por protocolo
                    viewers_by_protocol = defaultdict(int)
                    
                    for reader in path.readers:
                        protocol = self._get_protocol_from_type(reader.type)
                        viewers_by_protocol[protocol.value] += 1
                    
                    return {
                        "total": len(path.readers),
                        "by_protocol": dict(viewers_by_protocol),
                        "readers": path.readers  # Para futuro análisis detallado
                    }
            
            return {"total": 0, "by_protocol": {}}
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de viewers: {e}")
            return None
    
    def _get_protocol_from_type(self, reader_type: str) -> ViewerProtocol:
        """
        Mapea el tipo de reader de MediaMTX a protocolo.
        
        Args:
            reader_type: Tipo de reader de MediaMTX
            
        Returns:
            Protocolo correspondiente
        """
        return MEDIAMTX_PROTOCOL_MAP.get(reader_type, ViewerProtocol.RTSP)
    
    def _cleanup_old_snapshots(self, camera_id: str) -> None:
        """Limpia snapshots antiguos de memoria."""
        if camera_id not in self._snapshots:
            return
            
        snapshots = self._snapshots[camera_id]
        if len(snapshots) > self._max_snapshots_memory:
            # Mantener solo los más recientes
            self._snapshots[camera_id] = snapshots[-self._max_snapshots_memory:]
    
    async def _save_snapshot_to_db(self, snapshot: ViewerSnapshot) -> None:
        """
        Guarda un snapshot en la base de datos.
        
        TODO: Implementar cuando se cree la tabla de snapshots
        """
        # Por ahora solo loguear
        self.logger.debug(
            f"Snapshot para {snapshot.camera_id}: "
            f"{snapshot.total_viewers} viewers, "
            f"protocolos: {snapshot.viewers_by_protocol}"
        )
    
    async def _save_pending_snapshots(self, camera_id: str) -> None:
        """Guarda snapshots pendientes antes de detener tracking."""
        if camera_id not in self._snapshots:
            return
            
        snapshots = self._snapshots[camera_id]
        # TODO: Guardar todos los snapshots pendientes en BD
        
        # Limpiar de memoria
        del self._snapshots[camera_id]
    
    async def get_current_viewers(self, camera_id: str) -> Dict[str, Any]:
        """
        Obtiene información actual de viewers para una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Información actual de viewers
        """
        # Obtener último snapshot
        if camera_id in self._snapshots and self._snapshots[camera_id]:
            latest = self._snapshots[camera_id][-1]
            return {
                "camera_id": camera_id,
                "timestamp": latest.timestamp.isoformat(),
                "total_viewers": latest.total_viewers,
                "viewers_by_protocol": latest.viewers_by_protocol
            }
        
        return {
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "total_viewers": 0,
            "viewers_by_protocol": {}
        }
    
    async def get_viewer_history(
        self,
        camera_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de viewers para gráficos.
        
        Args:
            camera_id: ID de la cámara
            start_time: Tiempo de inicio (por defecto última hora)
            end_time: Tiempo de fin (por defecto ahora)
            interval_minutes: Intervalo de agregación
            
        Returns:
            Lista de puntos para gráfico
        """
        if not start_time:
            start_time = datetime.now() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.now()
            
        # Por ahora usar snapshots en memoria
        snapshots = self._snapshots.get(camera_id, [])
        
        # Filtrar por rango de tiempo
        filtered = [
            s for s in snapshots
            if start_time <= s.timestamp <= end_time
        ]
        
        # Agregar por intervalos
        # TODO: Implementar agregación por intervalos
        
        # Por ahora retornar todos los puntos
        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "viewers": s.total_viewers,
                "by_protocol": s.viewers_by_protocol
            }
            for s in filtered
        ]
    
    async def get_viewer_analytics(
        self,
        camera_id: Optional[str] = None,
        time_range: str = "1h"
    ) -> Dict[str, Any]:
        """
        Obtiene analytics detallados de viewers.
        
        Args:
            camera_id: ID de cámara específica o None para todas
            time_range: Rango de tiempo (1h, 24h, 7d, 30d)
            
        Returns:
            Analytics detallados incluyendo distribución geográfica mock
        """
        # Calcular tiempo de inicio según rango
        now = datetime.now()
        range_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        start_time = now - range_map.get(time_range, timedelta(hours=1))
        
        # TODO: Cuando tengamos IPs reales, implementar análisis geográfico real
        # Por ahora, generar datos MOCK de México
        
        # Datos MOCK de distribución geográfica en México
        geo_distribution = self._generate_mexico_mock_data()
        
        # Estadísticas por protocolo (basadas en snapshots reales si hay)
        protocol_stats = await self._get_protocol_statistics(camera_id, start_time)
        
        # Tendencias
        trends = await self._calculate_viewer_trends(camera_id, start_time)
        
        # Convertir distribución geográfica a lista
        geo_items = []
        if isinstance(geo_distribution, dict) and "states" in geo_distribution:
            for state_code, state_data in geo_distribution["states"].items():
                geo_items.append({
                    "location": state_data["name"],
                    "viewers": state_data["viewers"],
                    "percentage": state_data["percentage"]
                })
        
        # Convertir distribución de protocolo a lista
        protocol_items = []
        viewer_count = geo_distribution.get("total_viewers", 0)
        for protocol, percentage in protocol_stats.items():
            protocol_items.append({
                "protocol": protocol,
                "viewers": int(viewer_count * percentage / 100),
                "percentage": percentage
            })
        
        return {
            "time_range": time_range,
            "camera_id": camera_id,
            "summary": {
                "total_unique_viewers": geo_distribution["total_viewers"],
                "total_viewing_hours": geo_distribution["total_viewers"] * 0.5,  # Mock: 30 min promedio
                "average_session_duration_minutes": 30.0,
                "peak_concurrent_viewers": trends.get("peak", 0),
                "peak_time": trends.get("peak_time", now.isoformat())
            },
            "geographic_distribution": geo_items,
            "protocol_distribution": protocol_items,
            "trends": {
                "growth_rate": trends.get("growth_rate", 0.0),
                "peak_hours": trends.get("peak_hours", [14, 15, 20, 21]),
                "most_popular_protocol": trends.get("most_popular", "RTSP"),
                "average_quality_score": trends.get("quality_score", 85.0)
            },
            "data_note": "IMPORTANTE: Datos geográficos son MOCK. MediaMTX actualmente no proporciona IPs de viewers."
        }
    
    def _generate_mexico_mock_data(self) -> Dict[str, Any]:
        """
        Genera datos MOCK de distribución geográfica en México.
        
        TODO: Reemplazar con datos reales cuando MediaMTX proporcione IPs
        y podamos usar un servicio de GeoIP.
        
        Returns:
            Distribución geográfica mock centrada en Puebla, Veracruz y CDMX
        """
        # Distribución ponderada entre los estados solicitados
        total_viewers = random.randint(50, 200)
        
        # Porcentajes aproximados
        cdmx_percent = random.uniform(0.35, 0.45)  # 35-45%
        puebla_percent = random.uniform(0.25, 0.35)  # 25-35%
        veracruz_percent = 1 - cdmx_percent - puebla_percent  # El resto
        
        cdmx_viewers = int(total_viewers * cdmx_percent)
        puebla_viewers = int(total_viewers * puebla_percent)
        veracruz_viewers = total_viewers - cdmx_viewers - puebla_viewers
        
        return {
            "total_viewers": total_viewers,
            "countries": {
                "MX": {
                    "name": "México",
                    "viewers": total_viewers,
                    "percentage": 100.0
                }
            },
            "states": {
                "CDMX": {
                    "name": "Ciudad de México",
                    "viewers": cdmx_viewers,
                    "percentage": round(cdmx_percent * 100, 1)
                },
                "PUE": {
                    "name": "Puebla",
                    "viewers": puebla_viewers,
                    "percentage": round(puebla_percent * 100, 1)
                },
                "VER": {
                    "name": "Veracruz",
                    "viewers": veracruz_viewers,
                    "percentage": round(veracruz_percent * 100, 1)
                }
            },
            "cities": {
                "Ciudad de México": {
                    "state": "CDMX",
                    "viewers": int(cdmx_viewers * 0.8),
                    "percentage": round(cdmx_percent * 80, 1)
                },
                "Ecatepec": {
                    "state": "CDMX",
                    "viewers": int(cdmx_viewers * 0.2),
                    "percentage": round(cdmx_percent * 20, 1)
                },
                "Puebla": {
                    "state": "PUE",
                    "viewers": int(puebla_viewers * 0.7),
                    "percentage": round(puebla_percent * 70, 1)
                },
                "Cholula": {
                    "state": "PUE",
                    "viewers": int(puebla_viewers * 0.3),
                    "percentage": round(puebla_percent * 30, 1)
                },
                "Veracruz": {
                    "state": "VER",
                    "viewers": int(veracruz_viewers * 0.5),
                    "percentage": round(veracruz_percent * 50, 1)
                },
                "Xalapa": {
                    "state": "VER",
                    "viewers": int(veracruz_viewers * 0.3),
                    "percentage": round(veracruz_percent * 30, 1)
                },
                "Coatzacoalcos": {
                    "state": "VER",
                    "viewers": int(veracruz_viewers * 0.2),
                    "percentage": round(veracruz_percent * 20, 1)
                }
            }
        }
    
    async def _get_protocol_statistics(
        self,
        camera_id: Optional[str],
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas por protocolo.
        
        Args:
            camera_id: ID de cámara o None para todas
            start_time: Tiempo de inicio para el análisis
            
        Returns:
            Estadísticas por protocolo
        """
        # Agregar datos de todos los snapshots relevantes
        protocol_counts = defaultdict(int)
        total_samples = 0
        
        cameras = [camera_id] if camera_id else list(self._snapshots.keys())
        
        for cam_id in cameras:
            snapshots = self._snapshots.get(cam_id, [])
            for snapshot in snapshots:
                if snapshot.timestamp >= start_time:
                    for protocol, count in snapshot.viewers_by_protocol.items():
                        protocol_counts[protocol] += count
                    total_samples += 1
        
        # Calcular porcentajes
        total_viewers = sum(protocol_counts.values())
        
        if total_viewers == 0:
            # Datos por defecto si no hay viewers
            return {
                ViewerProtocol.RTSP.value: {"count": 0, "percentage": 0},
                ViewerProtocol.HLS.value: {"count": 0, "percentage": 0},
                ViewerProtocol.WEBRTC.value: {"count": 0, "percentage": 0}
            }
        
        return {
            protocol: {
                "count": count,
                "percentage": round((count / total_viewers) * 100, 1)
            }
            for protocol, count in protocol_counts.items()
        }
    
    async def _calculate_viewer_trends(
        self,
        camera_id: Optional[str],
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Calcula tendencias de viewers.
        
        Args:
            camera_id: ID de cámara o None para todas
            start_time: Tiempo de inicio
            
        Returns:
            Tendencias calculadas
        """
        all_viewers = []
        peak_viewers = 0
        peak_time = None
        
        cameras = [camera_id] if camera_id else list(self._snapshots.keys())
        
        for cam_id in cameras:
            snapshots = self._snapshots.get(cam_id, [])
            for snapshot in snapshots:
                if snapshot.timestamp >= start_time:
                    all_viewers.append(snapshot.total_viewers)
                    if snapshot.total_viewers > peak_viewers:
                        peak_viewers = snapshot.total_viewers
                        peak_time = snapshot.timestamp
        
        if not all_viewers:
            return {
                "average": 0,
                "peak": 0,
                "peak_time": None,
                "trend": "stable"
            }
        
        avg_viewers = sum(all_viewers) / len(all_viewers)
        
        # Determinar tendencia simple
        if len(all_viewers) >= 2:
            recent_avg = sum(all_viewers[-10:]) / len(all_viewers[-10:])
            older_avg = sum(all_viewers[:10]) / min(10, len(all_viewers[:10]))
            
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "average": round(avg_viewers, 1),
            "peak": peak_viewers,
            "peak_time": peak_time.isoformat() if peak_time else None,
            "trend": trend,
            "samples": len(all_viewers)
        }
    
    async def get_protocol_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales por protocolo.
        
        Returns:
            Estadísticas de uso por protocolo
        """
        return await self._get_protocol_statistics(None, datetime.now() - timedelta(hours=24))
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self.logger.info("Limpiando ViewerAnalyticsService")
        
        # Detener todas las tareas de tracking
        camera_ids = list(self._collection_tasks.keys())
        for camera_id in camera_ids:
            await self.stop_tracking(camera_id)
        
        # Limpiar datos en memoria
        self._snapshots.clear()
        self._active_sessions.clear()


# Singleton del servicio
_viewer_service: Optional[ViewerAnalyticsService] = None


def get_viewer_analytics_service() -> ViewerAnalyticsService:
    """
    Obtiene la instancia singleton del servicio de analytics.
    
    Returns:
        Instancia única del servicio
    """
    global _viewer_service
    
    if _viewer_service is None:
        _viewer_service = ViewerAnalyticsService()
        
    return _viewer_service