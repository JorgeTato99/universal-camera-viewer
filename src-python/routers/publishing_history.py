"""
Router para endpoints de historial de publicaciones MediaMTX.

Proporciona APIs para consultar, analizar y gestionar el historial
de sesiones de publicación pasadas.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, Dict, Any
from datetime import datetime

from api.schemas.requests.mediamtx_requests import (
    GetHistoryRequest, CleanupHistoryRequest,
    PublicationStatus, TerminationReason
)
from api.schemas.responses.mediamtx_responses import (
    PublicationHistoryResponse, PublicationSessionDetailResponse,
    HistoryCleanupResponse, PublicationHistoryItem
)
from api.dependencies import create_response
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.camera_manager_service import camera_manager_service
from utils.exceptions import ServiceError
from api.validators.mediamtx_validators import (
    validate_session_id, validate_page_params
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/publishing/history",
    tags=["publishing-history"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=PublicationHistoryResponse,
    summary="Listar historial de publicaciones",
    description="""
    Obtiene el historial de publicaciones con filtros opcionales.
    
    Permite filtrar por:
    - Cámara específica
    - Servidor MediaMTX
    - Estado de terminación
    - Rango de fechas
    - Duración mínima
    
    Los resultados se devuelven paginados y ordenados.
    """
)
async def get_publication_history(
    camera_id: Optional[str] = Query(None, description="Filtrar por cámara"),
    server_id: Optional[int] = Query(None, description="Filtrar por servidor"),
    termination_reason: Optional[TerminationReason] = Query(
        None,
        description="Filtrar por razón de terminación"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Fecha de inicio del rango"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Fecha de fin del rango"
    ),
    min_duration_seconds: Optional[int] = Query(
        None,
        ge=0,
        description="Duración mínima en segundos"
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(
        50,
        ge=1,
        le=200,
        description="Tamaño de página"
    ),
    order_by: str = Query(
        "start_time",
        regex="^(start_time|end_time|duration_seconds|total_frames|error_count)$",
        description="Campo para ordenar"
    ),
    order_desc: bool = Query(True, description="Orden descendente")
) -> PublicationHistoryResponse:
    """
    Lista el historial de publicaciones con filtros.
    
    Args:
        camera_id: ID de cámara para filtrar
        server_id: ID de servidor para filtrar
        termination_reason: Razón de terminación para filtrar
        start_date: Inicio del rango de fechas
        end_date: Fin del rango de fechas
        min_duration_seconds: Duración mínima
        page: Número de página
        page_size: Registros por página
        order_by: Campo de ordenamiento
        order_desc: Si ordenar descendente
        
    Returns:
        PublicationHistoryResponse con resultados paginados
    """
    logger.debug(f"Obteniendo historial de publicaciones, página {page}")
    
    try:
        # Validar parámetros de paginación
        page, page_size = validate_page_params(page, page_size)
        
        # Validar que camera_id existe si se proporciona
        if camera_id:
            camera = await camera_manager_service.get_camera(camera_id)
            if not camera:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cámara {camera_id} no encontrada"
                )
        
        # Crear request object
        request = GetHistoryRequest(
            camera_id=camera_id,
            server_id=server_id,
            termination_reason=termination_reason,
            start_date=start_date,
            end_date=end_date,
            min_duration_seconds=min_duration_seconds,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc
        )
        
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Consultar historial
        history_data = await db_service.get_publication_history(request)
        
        # Construir respuesta
        response = PublicationHistoryResponse(**history_data)
        
        logger.info(f"Historial obtenido: {response.total} registros totales, "
                   f"página {response.page} de {(response.total + page_size - 1) // page_size}")
        
        return response
        
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"ServiceError obteniendo historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error inesperado obteniendo historial")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo historial"
        )


@router.get(
    "/{session_id}",
    response_model=PublicationSessionDetailResponse,
    summary="Detalle de sesión de publicación",
    description="""
    Obtiene el detalle completo de una sesión de publicación específica.
    
    Incluye:
    - Información completa de la sesión
    - Resumen de métricas
    - Timeline de errores
    - Estadísticas de viewers
    - Comando FFmpeg utilizado
    """
)
async def get_session_detail(
    session_id: str
) -> PublicationSessionDetailResponse:
    """
    Obtiene el detalle de una sesión de publicación.
    
    Args:
        session_id: ID único de la sesión
        
    Returns:
        PublicationSessionDetailResponse con toda la información
        
    Raises:
        HTTPException: Si la sesión no existe
    """
    logger.debug(f"Obteniendo detalle de sesión {session_id}")
    
    try:
        # Validar session_id
        session_id = validate_session_id(session_id)
        
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Consultar detalle
        session_detail = await db_service.get_session_detail(session_id)
        
        if not session_detail:
            logger.warning(f"Sesión {session_id} no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión {session_id} no encontrada"
            )
        
        # Construir respuesta
        response = PublicationSessionDetailResponse(**session_detail)
        
        logger.info(f"Detalle obtenido para sesión {session_id}")
        
        return response
        
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"ServiceError obteniendo detalle de sesión: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo detalle de sesión {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo detalle de sesión"
        )


@router.get(
    "/camera/{camera_id}",
    response_model=PublicationHistoryResponse,
    summary="Historial por cámara",
    description="Obtiene el historial de publicaciones de una cámara específica"
)
async def get_camera_history(
    camera_id: str,
    days: int = Query(
        7,
        ge=1,
        le=365,
        description="Número de días hacia atrás"
    ),
    include_errors_only: bool = Query(
        False,
        description="Solo mostrar sesiones con errores"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
) -> PublicationHistoryResponse:
    """
    Obtiene el historial de una cámara específica.
    
    Atajo conveniente para filtrar por cámara con opciones comunes.
    
    Args:
        camera_id: ID de la cámara
        days: Días hacia atrás para buscar
        include_errors_only: Si solo mostrar sesiones problemáticas
        page: Número de página
        page_size: Tamaño de página
        
    Returns:
        PublicationHistoryResponse filtrado por cámara
    """
    # Calcular fecha de inicio basada en días
    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = start_date.replace(day=start_date.day - days + 1)
    
    # Reutilizar endpoint principal con filtros
    return await get_publication_history(
        camera_id=camera_id,
        start_date=start_date,
        termination_reason=TerminationReason.ERROR if include_errors_only else None,
        page=page,
        page_size=page_size,
        order_by="start_time",
        order_desc=True
    )


@router.delete(
    "/",
    response_model=HistoryCleanupResponse,
    summary="Limpiar historial antiguo",
    description="""
    Elimina registros antiguos del historial de publicaciones.
    
    Por defecto opera en modo dry_run (simulación) para previsualizar
    qué se eliminaría sin hacer cambios reales.
    """
)
async def cleanup_history(
    request: CleanupHistoryRequest = CleanupHistoryRequest()
) -> HistoryCleanupResponse:
    """
    Limpia registros antiguos del historial.
    
    Args:
        request: Parámetros de limpieza
        
    Returns:
        HistoryCleanupResponse con información de registros afectados
    """
    logger.info(f"Limpieza de historial solicitada: {request.older_than_days} días, "
               f"dry_run={request.dry_run}")
    
    try:
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Ejecutar limpieza
        cleanup_result = await db_service.cleanup_old_history(
            older_than_days=request.older_than_days,
            keep_errors=request.keep_errors,
            dry_run=request.dry_run
        )
        
        # Construir respuesta
        response = HistoryCleanupResponse(**cleanup_result)
        
        action = "simularía eliminar" if request.dry_run else "eliminó"
        logger.info(f"Limpieza {action} {response.records_affected} registros, "
                   f"liberando {response.space_freed_mb} MB")
        
        return response
        
    except ServiceError as e:
        logger.error(f"ServiceError en limpieza: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error inesperado en limpieza de historial")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error limpiando historial"
        )


@router.get(
    "/stats/summary",
    summary="Estadísticas del historial",
    description="Obtiene estadísticas agregadas del historial de publicaciones"
)
async def get_history_statistics(
    days: int = Query(30, ge=1, le=365, description="Días a analizar"),
    group_by: str = Query(
        "day",
        regex="^(hour|day|week|camera|server|termination_reason)$",
        description="Agrupar estadísticas por"
    )
) -> Dict[str, Any]:
    """
    Genera estadísticas agregadas del historial.
    
    Args:
        days: Número de días hacia atrás para analizar
        group_by: Criterio de agrupación
        
    Returns:
        Dict con estadísticas agregadas
    """
    logger.debug(f"Generando estadísticas de historial: {days} días, agrupado por {group_by}")
    
    try:
        # Por simplicidad, retornamos estadísticas mock
        # TODO: Implementar agregación real en el servicio de BD
        
        stats = {
            "period_analyzed": f"Last {days} days",
            "total_sessions": 1547,
            "total_hours_published": 3894.5,
            "average_session_duration_hours": 2.52,
            "success_rate_percent": 94.3,
            "top_error_reasons": [
                {"reason": "camera_disconnected", "count": 45},
                {"reason": "server_shutdown", "count": 23},
                {"reason": "network_error", "count": 15}
            ],
            "grouped_data": []
        }
        
        # Agregar datos agrupados según criterio
        if group_by == "day":
            # Últimos 7 días
            for i in range(7):
                date = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                date = date.replace(day=date.day - i)
                stats["grouped_data"].append({
                    "date": date.isoformat(),
                    "sessions": 220 - (i * 10),
                    "hours": 550 - (i * 25),
                    "errors": 11 - i
                })
        elif group_by == "camera":
            # Top 5 cámaras
            cameras = [
                {"camera_id": "cam-001", "name": "Entrada Principal", "sessions": 412},
                {"camera_id": "cam-002", "name": "Pasillo", "sessions": 389},
                {"camera_id": "cam-003", "name": "Almacén", "sessions": 301},
                {"camera_id": "cam-004", "name": "Oficina", "sessions": 245},
                {"camera_id": "cam-005", "name": "Parking", "sessions": 200}
            ]
            stats["grouped_data"] = cameras
        
        return create_response(
            success=True,
            data=stats
        )
        
    except Exception as e:
        logger.exception("Error generando estadísticas de historial")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando estadísticas"
        )