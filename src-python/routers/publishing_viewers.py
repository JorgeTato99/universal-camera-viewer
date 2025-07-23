"""
Router para endpoints de viewers/consumidores MediaMTX.

Proporciona APIs para monitorear y analizar la audiencia
de los streams publicados.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, Dict, Any, List
from datetime import datetime

from api.schemas.requests.mediamtx_requests import (
    GetViewersRequest, ViewerAnalyticsRequest,
    ViewerProtocol, MetricTimeRange
)
from api.schemas.responses.mediamtx_responses import (
    ViewersListResponse, ViewerAnalyticsResponse,
    ActiveViewer
)
from api.dependencies import create_response
from services.database.mediamtx_db_service import get_mediamtx_db_service
from utils.exceptions import ServiceError
from api.validators.mediamtx_validators import (
    validate_page_params, validate_viewer_ip
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/publishing/viewers",
    tags=["publishing-viewers"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=ViewersListResponse,
    summary="Listar viewers activos",
    description="""
    Obtiene la lista de viewers/consumidores activos o históricos.
    
    Permite filtrar por:
    - Publicación específica
    - Solo activos o todos
    - Protocolo utilizado
    
    Incluye breakdown por protocolo y estadísticas básicas.
    """
)
async def get_viewers(
    publication_id: Optional[int] = Query(
        None,
        description="Filtrar por ID de publicación"
    ),
    active_only: bool = Query(
        True,
        description="Solo mostrar viewers activos"
    ),
    protocol: Optional[ViewerProtocol] = Query(
        None,
        description="Filtrar por protocolo"
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(
        50,
        ge=1,
        le=200,
        description="Tamaño de página"
    )
) -> ViewersListResponse:
    """
    Lista viewers con filtros opcionales.
    
    Args:
        publication_id: ID de publicación para filtrar
        active_only: Si mostrar solo viewers conectados
        protocol: Protocolo específico para filtrar
        page: Número de página
        page_size: Registros por página
        
    Returns:
        ViewersListResponse con lista paginada
    """
    logger.debug(f"Obteniendo viewers, active_only={active_only}, página {page}")
    
    try:
        # Validar paginación
        page, page_size = validate_page_params(page, page_size)
        
        # Crear request object
        request = GetViewersRequest(
            publication_id=publication_id,
            active_only=active_only,
            protocol=protocol,
            include_history=False,
            page=page,
            page_size=page_size
        )
        
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Consultar viewers
        viewers_data = await db_service.get_active_viewers(request)
        
        # Construir respuesta
        response = ViewersListResponse(**viewers_data)
        
        logger.info(f"Viewers obtenidos: {response.active_count} activos de "
                   f"{response.total} totales")
        
        return response
        
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"ServiceError obteniendo viewers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error inesperado obteniendo viewers")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo viewers"
        )


@router.get(
    "/{publication_id}",
    response_model=ViewersListResponse,
    summary="Viewers de una publicación",
    description="Obtiene los viewers de una publicación específica"
)
async def get_publication_viewers(
    publication_id: int,
    include_history: bool = Query(
        False,
        description="Incluir viewers históricos"
    )
) -> ViewersListResponse:
    """
    Obtiene viewers de una publicación específica.
    
    Args:
        publication_id: ID de la publicación
        include_history: Si incluir viewers desconectados
        
    Returns:
        ViewersListResponse filtrada por publicación
    """
    # Reutilizar endpoint principal con filtro
    return await get_viewers(
        publication_id=publication_id,
        active_only=not include_history,
        page=1,
        page_size=100  # Mostrar más por defecto para una publicación
    )


@router.get(
    "/analytics",
    response_model=ViewerAnalyticsResponse,
    summary="Análisis de audiencia",
    description="""
    Genera análisis detallado de la audiencia.
    
    Incluye:
    - Viewers únicos y totales
    - Horas de visualización
    - Distribución por protocolo
    - Tendencias temporales
    - Análisis geográfico (opcional)
    - Métricas de calidad de experiencia
    
    **NOTA**: Actualmente devuelve datos de ejemplo. La implementación
    real del análisis en el servicio de BD está pendiente.
    """
)
async def get_viewer_analytics(
    time_range: MetricTimeRange = Query(
        MetricTimeRange.LAST_7_DAYS,
        description="Período de análisis"
    ),
    group_by: str = Query(
        "day",
        regex="^(hour|day|week|protocol|camera)$",
        description="Criterio de agrupación"
    ),
    include_geographic: bool = Query(
        False,
        description="Incluir análisis geográfico por IP"
    ),
    camera_id: Optional[str] = Query(
        None,
        description="Filtrar por cámara específica"
    )
) -> ViewerAnalyticsResponse:
    """
    Genera análisis de audiencia para el período especificado.
    
    Args:
        time_range: Rango de tiempo a analizar
        group_by: Cómo agrupar los resultados
        include_geographic: Si incluir análisis por ubicación
        camera_id: Cámara específica para analizar
        
    Returns:
        ViewerAnalyticsResponse con análisis completo
    """
    logger.debug(f"Generando análisis de audiencia: {time_range}, agrupado por {group_by}")
    
    try:
        # Por ahora retornamos datos de ejemplo
        # TODO: Implementar análisis real en el servicio de BD
        
        # Datos base
        total_unique_viewers = 847
        total_viewing_hours = 2341.5
        avg_session_duration = 165.3  # minutos
        peak_viewers = 124
        peak_time = datetime.utcnow().replace(hour=20, minute=30, second=0)
        
        # Tendencias según agrupación
        viewer_trends = []
        
        if group_by == "hour":
            # Últimas 24 horas
            for hour in range(24):
                viewer_trends.append({
                    "period": f"{hour:02d}:00",
                    "viewers": 20 + (hour % 12) * 5,
                    "avg_duration_minutes": 150 + (hour % 6) * 10,
                    "new_viewers": 5 + (hour % 4)
                })
        elif group_by == "day":
            # Últimos 7 días
            days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            for i, day in enumerate(days):
                viewer_trends.append({
                    "period": day,
                    "viewers": 100 + i * 20,
                    "viewing_hours": 280 + i * 40,
                    "peak_concurrent": 20 + i * 3
                })
        elif group_by == "protocol":
            # Por protocolo
            protocols = [
                ("RTSP", 45.2, 412),
                ("HLS", 28.7, 263),
                ("WebRTC", 18.4, 169),
                ("RTMP", 7.7, 71)
            ]
            for proto, percent, count in protocols:
                viewer_trends.append({
                    "protocol": proto,
                    "percentage": percent,
                    "viewer_count": count,
                    "avg_quality_score": 85 + (count % 10)
                })
        elif group_by == "camera":
            # Top cámaras
            cameras = [
                ("cam-001", "Entrada Principal", 289, 4.2),
                ("cam-002", "Pasillo", 234, 3.8),
                ("cam-003", "Almacén", 187, 3.1),
                ("cam-004", "Oficina", 137, 2.5)
            ]
            for cam_id, name, viewers, rating in cameras:
                viewer_trends.append({
                    "camera_id": cam_id,
                    "camera_name": name,
                    "unique_viewers": viewers,
                    "satisfaction_rating": rating
                })
        
        # Distribución por protocolo
        protocol_distribution = {
            "RTSP": 45.2,
            "HLS": 28.7,
            "WebRTC": 18.4,
            "RTMP": 7.7
        }
        
        # Top cámaras
        top_cameras = [
            {
                "camera_id": "cam-001",
                "camera_name": "Entrada Principal",
                "viewer_hours": 687.3,
                "unique_viewers": 289
            },
            {
                "camera_id": "cam-002",
                "camera_name": "Pasillo",
                "viewer_hours": 534.2,
                "unique_viewers": 234
            },
            {
                "camera_id": "cam-003",
                "camera_name": "Almacén",
                "viewer_hours": 423.8,
                "unique_viewers": 187
            }
        ]
        
        # Distribución geográfica si se solicita
        geographic_distribution = None
        if include_geographic:
            geographic_distribution = {
                "US": 342,
                "MX": 187,
                "CA": 98,
                "ES": 76,
                "AR": 54,
                "Other": 90
            }
        
        # Construir respuesta
        response = ViewerAnalyticsResponse(
            time_range=time_range.value,
            total_unique_viewers=total_unique_viewers,
            total_viewing_hours=total_viewing_hours,
            avg_session_duration_minutes=avg_session_duration,
            peak_concurrent_viewers=peak_viewers,
            peak_time=peak_time,
            viewer_trends=viewer_trends,
            protocol_distribution=protocol_distribution,
            top_cameras=top_cameras,
            geographic_distribution=geographic_distribution,
            avg_quality_score=87.3,
            buffer_event_rate=2.1
        )
        
        logger.info(f"Análisis generado: {total_unique_viewers} viewers únicos, "
                   f"{total_viewing_hours:.1f} horas totales")
        
        return response
        
    except Exception as e:
        logger.exception("Error generando análisis de audiencia")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando análisis"
        )


@router.get(
    "/history",
    response_model=ViewersListResponse,
    summary="Historial de viewers",
    description="Obtiene el historial completo de viewers con filtros"
)
async def get_viewer_history(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    min_duration_seconds: Optional[int] = Query(
        None,
        ge=0,
        description="Duración mínima de sesión"
    ),
    protocol: Optional[ViewerProtocol] = Query(None),
    camera_id: Optional[str] = Query(None, description="Filtrar por cámara"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
) -> ViewersListResponse:
    """
    Obtiene historial de viewers con filtros avanzados.
    
    Útil para análisis retrospectivo y auditoría de accesos.
    """
    # Construir request con include_history
    request = GetViewersRequest(
        active_only=False,
        protocol=protocol,
        include_history=True,
        page=page,
        page_size=page_size
    )
    
    # TODO: Extender el servicio de BD para soportar estos filtros adicionales
    
    return await get_viewers(
        active_only=False,
        protocol=protocol,
        page=page,
        page_size=page_size
    )


@router.post(
    "/track",
    summary="Registrar nuevo viewer",
    description="Registra manualmente un nuevo viewer conectado",
    include_in_schema=False  # Endpoint interno
)
async def track_viewer(
    publication_id: int,
    viewer_ip: str,
    protocol: ViewerProtocol,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registra un nuevo viewer conectado.
    
    Este endpoint es principalmente para uso interno del sistema.
    
    Args:
        publication_id: ID de la publicación
        viewer_ip: IP del viewer
        protocol: Protocolo utilizado
        user_agent: User agent del cliente
        
    Returns:
        Dict con ID del viewer registrado
    """
    try:
        # Validar IP
        viewer_ip = validate_viewer_ip(viewer_ip)
        
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Registrar viewer
        viewer_id = await db_service.track_viewer(
            publication_id=publication_id,
            viewer_ip=viewer_ip,
            protocol=protocol,
            user_agent=user_agent
        )
        
        logger.info(f"Viewer registrado: {viewer_ip} -> publicación {publication_id}")
        
        return create_response(
            success=True,
            data={"viewer_id": viewer_id}
        )
        
    except Exception as e:
        logger.exception("Error registrando viewer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registrando viewer"
        )


@router.put(
    "/disconnect/{viewer_id}",
    summary="Registrar desconexión de viewer",
    description="Actualiza información cuando un viewer se desconecta",
    include_in_schema=False  # Endpoint interno
)
async def disconnect_viewer(
    viewer_id: int,
    bytes_received: int = 0,
    quality_changes: int = 0,
    buffer_events: int = 0
) -> Dict[str, Any]:
    """
    Registra la desconexión de un viewer.
    
    Este endpoint es principalmente para uso interno del sistema.
    
    Args:
        viewer_id: ID del viewer
        bytes_received: Bytes totales recibidos
        quality_changes: Cambios de calidad durante la sesión
        buffer_events: Eventos de buffering
        
    Returns:
        Dict con confirmación
    """
    try:
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Actualizar desconexión
        await db_service.update_viewer_disconnection(
            viewer_id=viewer_id,
            bytes_received=bytes_received,
            quality_changes=quality_changes,
            buffer_events=buffer_events
        )
        
        logger.info(f"Viewer {viewer_id} desconectado")
        
        return create_response(
            success=True,
            message="Viewer disconnection recorded"
        )
        
    except Exception as e:
        logger.exception(f"Error registrando desconexión de viewer {viewer_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registrando desconexión"
        )


@router.get(
    "/stats/protocols",
    summary="Estadísticas por protocolo",
    description="""
    Obtiene estadísticas detalladas de uso por protocolo.
    
    Proporciona información sobre:
    - Viewers activos por protocolo
    - Sesiones totales del día
    - Duración promedio de sesión
    - Ancho de banda utilizado
    - Score de calidad promedio
    - Problemas comunes por protocolo
    
    **NOTA**: Los datos actuales son de ejemplo. La implementación
    con consulta real a BD está pendiente.
    """
)
async def get_protocol_statistics() -> Dict[str, Any]:
    """
    Genera estadísticas de uso por protocolo.
    
    Útil para optimización de infraestructura y decisiones técnicas.
    
    Returns:
        Dict con estadísticas por protocolo
    """
    try:
        # TODO: Implementar consulta real a BD
        stats = {
            "protocols": [
                {
                    "protocol": "RTSP",
                    "active_viewers": 145,
                    "total_sessions_today": 892,
                    "avg_session_duration_minutes": 178,
                    "total_bandwidth_mbps": 287.5,
                    "avg_quality_score": 88.2,
                    "common_issues": ["High latency", "Connection drops"]
                },
                {
                    "protocol": "HLS",
                    "active_viewers": 89,
                    "total_sessions_today": 567,
                    "avg_session_duration_minutes": 145,
                    "total_bandwidth_mbps": 156.3,
                    "avg_quality_score": 91.5,
                    "common_issues": ["Initial buffering"]
                },
                {
                    "protocol": "WebRTC",
                    "active_viewers": 67,
                    "total_sessions_today": 423,
                    "avg_session_duration_minutes": 93,
                    "total_bandwidth_mbps": 98.7,
                    "avg_quality_score": 94.1,
                    "common_issues": ["Browser compatibility"]
                },
                {
                    "protocol": "RTMP",
                    "active_viewers": 23,
                    "total_sessions_today": 134,
                    "avg_session_duration_minutes": 210,
                    "total_bandwidth_mbps": 45.2,
                    "avg_quality_score": 86.7,
                    "common_issues": ["Legacy support"]
                }
            ],
            "recommendations": [
                "Consider migrating RTMP viewers to HLS for better compatibility",
                "WebRTC shows best quality scores for low-latency requirements",
                "RTSP remains dominant for professional/surveillance use cases"
            ]
        }
        
        return create_response(
            success=True,
            data=stats
        )
        
    except Exception as e:
        logger.exception("Error generando estadísticas por protocolo")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando estadísticas"
        )