"""
Router para analytics de viewers de MediaMTX.

Proporciona endpoints para análisis de audiencia, estadísticas
por protocolo y tracking de viewers en tiempo real.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from services.publishing.viewer_analytics_service import get_viewer_analytics_service
from api.dependencies import get_current_user
from utils.exceptions import ServiceError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/publishing/viewers", tags=["publishing-viewers"])


# ==================== Modelos de Request/Response ====================

class ViewerInfo(BaseModel):
    """Información básica de un viewer."""
    viewer_id: str = Field(..., description="ID único del viewer")
    camera_id: str = Field(..., description="ID de la cámara")
    protocol: str = Field(..., description="Protocolo usado (RTSP, HLS, etc)")
    start_time: str = Field(..., description="Hora de inicio ISO 8601")
    duration_seconds: int = Field(..., description="Duración de la sesión en segundos")
    ip_address: Optional[str] = Field(None, description="IP del viewer (cuando esté disponible)")
    location: Optional[Dict[str, str]] = Field(None, description="Ubicación geográfica como país, estado, ciudad")


class CurrentViewersResponse(BaseModel):
    """Response con viewers actuales."""
    camera_id: str = Field(..., description="ID de la cámara")
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    total_viewers: int = Field(..., description="Total de viewers actuales")
    viewers_by_protocol: Dict[str, int] = Field(
        default_factory=dict,
        description="Viewers por protocolo"
    )


class AnalyticsSummary(BaseModel):
    """Resumen de estadísticas para analytics."""
    total_unique_viewers: int = Field(..., description="Viewers únicos totales")
    total_viewing_hours: float = Field(..., description="Horas totales de visualización")
    average_session_duration_minutes: float = Field(..., description="Duración promedio de sesión")
    peak_concurrent_viewers: int = Field(..., description="Pico de viewers concurrentes")
    peak_time: Optional[str] = Field(None, description="Momento del pico ISO 8601")


class GeographicDistributionItem(BaseModel):
    """Item de distribución geográfica."""
    location: str = Field(..., description="Nombre de la ubicación")
    viewers: int = Field(..., description="Número de viewers")
    percentage: float = Field(..., description="Porcentaje del total")


class ProtocolDistributionItem(BaseModel):
    """Item de distribución por protocolo."""
    protocol: str = Field(..., description="Nombre del protocolo")
    viewers: int = Field(..., description="Número de viewers")
    percentage: float = Field(..., description="Porcentaje del total")


class AnalyticsTrends(BaseModel):
    """Tendencias identificadas en analytics."""
    growth_rate: float = Field(..., description="Tasa de crecimiento en porcentaje")
    peak_hours: List[int] = Field(..., description="Horas pico del día (0-23)")
    most_popular_protocol: str = Field(..., description="Protocolo más usado")
    average_quality_score: float = Field(..., description="Score de calidad promedio")


class ViewerHistoryPoint(BaseModel):
    """Punto de datos para gráfico de historial."""
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    viewers: int = Field(..., description="Número de viewers")
    by_protocol: Dict[str, int] = Field(
        default_factory=dict,
        description="Desglose por protocolo"
    )


class ViewerAnalyticsResponse(BaseModel):
    """Response con analytics completos."""
    time_range: str = Field(..., description="Rango de tiempo analizado")
    camera_id: Optional[str] = Field(None, description="ID de cámara o null para todas")
    summary: AnalyticsSummary = Field(..., description="Resumen de estadísticas")
    geographic_distribution: List[GeographicDistributionItem] = Field(..., description="Distribución geográfica")
    protocol_distribution: List[ProtocolDistributionItem] = Field(..., description="Distribución por protocolo")
    trends: AnalyticsTrends = Field(..., description="Tendencias identificadas")
    data_note: str = Field(..., description="Nota sobre el origen de los datos")


class TrackingResponse(BaseModel):
    """Response para endpoints de tracking."""
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    tracking_id: Optional[str] = Field(None, description="ID de tracking si aplica")
    

class ProtocolStatistics(BaseModel):
    """Estadísticas por protocolo."""
    protocol: str = Field(..., description="Nombre del protocolo")
    count: int = Field(..., description="Número total de conexiones")
    percentage: float = Field(..., description="Porcentaje del total")
    avg_duration: Optional[float] = Field(None, description="Duración promedio en segundos")


class ViewerSnapshot(BaseModel):
    """Snapshot de viewers en un momento."""
    timestamp: str = Field(..., description="Timestamp ISO 8601")
    camera_id: str = Field(..., description="ID de la cámara")
    total_viewers: int = Field(..., description="Total de viewers")
    viewers_by_protocol: Dict[str, int] = Field(..., description="Viewers por protocolo")


# ==================== Endpoints ====================

@router.get("/", response_model=List[ViewerInfo])
async def list_viewers(
    camera_id: Optional[str] = Query(None, description="Filtrar por cámara"),
    protocol: Optional[str] = Query(None, description="Filtrar por protocolo"),
    active_only: bool = Query(True, description="Solo viewers activos"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=200, description="Número máximo de registros"),
    current_user: dict = Depends(get_current_user)
) -> List[ViewerInfo]:
    """
    Lista viewers activos o históricos.
    
    NOTA: Actualmente MediaMTX solo proporciona conteo total.
    Los datos detallados están preparados para cuando MediaMTX
    exponga más información sobre viewers individuales.
    """
    try:
        # TODO: Cuando tengamos tracking individual de viewers,
        # implementar query a BD con filtros
        
        # Por ahora retornar lista vacía con nota
        logger.info(
            "Listado de viewers solicitado. "
            "Funcionalidad pendiente de información detallada de MediaMTX"
        )
        
        return []
        
    except Exception as e:
        logger.error(f"Error listando viewers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current/{camera_id}", response_model=CurrentViewersResponse)
async def get_current_viewers(
    camera_id: str,
    current_user: dict = Depends(get_current_user)
) -> CurrentViewersResponse:
    """
    Obtiene información actual de viewers para una cámara.
    
    Proporciona el conteo total y distribución por protocolo
    basado en la información disponible de MediaMTX.
    """
    try:
        viewer_service = get_viewer_analytics_service()
        data = await viewer_service.get_current_viewers(camera_id)
        
        return CurrentViewersResponse(**data)
        
    except Exception as e:
        logger.error(f"Error obteniendo viewers actuales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{camera_id}", response_model=List[ViewerHistoryPoint])
async def get_viewer_history(
    camera_id: str,
    hours: int = Query(1, ge=1, le=24, description="Horas de historial"),
    interval_minutes: int = Query(5, ge=1, le=60, description="Intervalo de agregación en minutos"),
    current_user: dict = Depends(get_current_user)
) -> List[ViewerHistoryPoint]:
    """
    Obtiene historial de viewers para gráficos.
    
    Retorna puntos de datos agregados según el intervalo especificado.
    """
    try:
        viewer_service = get_viewer_analytics_service()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        history = await viewer_service.get_viewer_history(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=interval_minutes
        )
        
        return [ViewerHistoryPoint(**point) for point in history]
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=ViewerAnalyticsResponse)
async def get_viewer_analytics(
    camera_id: Optional[str] = Query(None, description="ID de cámara específica o todas"),
    time_range: str = Query("1h", description="Rango de tiempo: 1h, 24h, 7d, 30d"),
    current_user: dict = Depends(get_current_user)
) -> ViewerAnalyticsResponse:
    """
    Obtiene analytics detallados de viewers.
    
    Incluye:
    - Resumen de estadísticas
    - Distribución geográfica (MOCK por ahora)
    - Distribución por protocolo
    - Tendencias identificadas
    
    IMPORTANTE: La distribución geográfica usa datos MOCK de México
    (Puebla, Veracruz, CDMX) hasta que MediaMTX proporcione IPs reales.
    """
    try:
        viewer_service = get_viewer_analytics_service()
        analytics = await viewer_service.get_viewer_analytics(
            camera_id=camera_id,
            time_range=time_range
        )
        
        return ViewerAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/protocols", response_model=List[ProtocolStatistics])
async def get_protocol_statistics(
    hours: int = Query(24, ge=1, le=168, description="Horas de análisis"),
    current_user: dict = Depends(get_current_user)
) -> List[ProtocolStatistics]:
    """
    Obtiene estadísticas de uso por protocolo.
    
    Analiza la distribución de viewers entre diferentes protocolos
    de streaming (RTSP, HLS, WebRTC, etc).
    """
    try:
        viewer_service = get_viewer_analytics_service()
        stats = await viewer_service.get_protocol_statistics()
        
        result = []
        for protocol, data in stats.items():
            result.append(ProtocolStatistics(
                protocol=protocol,
                count=data["count"],
                percentage=data["percentage"],
                avg_duration=None  # TODO: Calcular cuando tengamos sesiones individuales
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de protocolo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track", response_model=TrackingResponse)
async def track_viewer(
    camera_id: str = Query(..., description="ID de la cámara"),
    publish_path: str = Query(..., description="Path de publicación en MediaMTX"),
    current_user: dict = Depends(get_current_user)
) -> TrackingResponse:
    """
    Inicia el tracking de viewers para una cámara.
    
    Este endpoint es usado internamente cuando se inicia una publicación.
    """
    try:
        viewer_service = get_viewer_analytics_service()
        await viewer_service.start_tracking(camera_id, publish_path)
        
        return TrackingResponse(
            success=True,
            message=f"Tracking iniciado para {camera_id}",
            tracking_id=camera_id
        )
        
    except Exception as e:
        logger.error(f"Error iniciando tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/disconnect/{viewer_id}")
async def disconnect_viewer(
    viewer_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Registra la desconexión de un viewer.
    
    NOTA: Este endpoint está preparado para cuando tengamos
    tracking individual de viewers. Actualmente no tiene efecto.
    """
    try:
        # TODO: Implementar cuando tengamos tracking individual
        logger.info(
            f"Desconexión de viewer {viewer_id} registrada. "
            "Funcionalidad pendiente de implementación completa."
        )
        
        return {
            "success": True,
            "message": "Desconexión registrada",
            "viewer_id": viewer_id,
            "note": "Tracking individual pendiente de implementación"
        }
        
    except Exception as e:
        logger.error(f"Error registrando desconexión: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots/{camera_id}", response_model=List[ViewerSnapshot])
async def get_viewer_snapshots(
    camera_id: str,
    minutes: int = Query(60, ge=5, le=1440, description="Minutos de historial"),
    current_user: dict = Depends(get_current_user)
) -> List[ViewerSnapshot]:
    """
    Obtiene snapshots recientes de viewers.
    
    Útil para debugging y monitoreo detallado.
    """
    try:
        viewer_service = get_viewer_analytics_service()
        
        # Obtener historial como snapshots
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        history = await viewer_service.get_viewer_history(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=1  # Snapshots sin agregación
        )
        
        return [
            ViewerSnapshot(
                timestamp=point["timestamp"],
                camera_id=camera_id,
                total_viewers=point["viewers"],
                viewers_by_protocol=point["by_protocol"]
            )
            for point in history
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Inicializar servicio al importar
async def _init_viewer_service():
    """Inicializa el servicio de viewer analytics."""
    try:
        service = get_viewer_analytics_service()
        await service.initialize()
    except Exception as e:
        logger.error(f"Error inicializando servicio de viewers: {e}")


# TODO: Llamar _init_viewer_service() cuando la aplicación inicie