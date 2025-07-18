"""
Router para endpoints de monitoreo de cámaras.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging

from api.dependencies import create_response
from api.models.camera_models import (
    EventType,
    EventSeverity,
    CameraEventsResponse,
    CameraLogsResponse,
    CameraSnapshotsResponse
)
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    ServiceError
)

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/cameras",
    tags=["camera-monitoring"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Endpoints de Monitoreo ===


@router.get("/{camera_id}/events", response_model=CameraEventsResponse)
async def get_camera_events(
    camera_id: str,
    event_type: Optional[EventType] = None,
    severity: Optional[EventSeverity] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50
):
    """
    Obtener el historial de eventos de una cámara.
    
    Devuelve eventos paginados con filtros opcionales por tipo, severidad y rango de fechas.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        event_type: Filtrar por tipo de evento
        severity: Filtrar por severidad
        start_date: Fecha inicial del rango
        end_date: Fecha final del rango
        page: Número de página (default: 1)
        page_size: Eventos por página (default: 50, max: 200)
        
    Returns:
        CameraEventsResponse: Lista paginada de eventos
        
    Raises:
        HTTPException 404: Si la cámara no existe
        HTTPException 400: Parámetros inválidos
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        # Validar paginación
        if page < 1:
            logger.warning(f"Número de página inválido: {page}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de página debe ser mayor a 0"
            )
        
        if page_size < 1 or page_size > 200:
            logger.warning(f"Tamaño de página inválido: {page_size}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tamaño de página debe estar entre 1 y 200"
            )
        
        # Validar rango de fechas
        if start_date and end_date and start_date > end_date:
            logger.warning(f"Rango de fechas inválido: {start_date} > {end_date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha inicial debe ser anterior a la fecha final"
            )
            
        logger.info(f"Obteniendo eventos de cámara {camera_id}, página {page}")
        
        result = await camera_manager_service.get_camera_events(
            camera_id,
            event_type=event_type.value if event_type else None,
            severity=severity.value if severity else None,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        # Log resumen de resultados
        total_events = result.get('total', 0)
        logger.info(f"Devolviendo {len(result.get('events', []))} de {total_events} eventos totales")
        
        return create_response(
            success=True,
            data=result
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo eventos: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error obteniendo eventos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/logs", response_model=CameraLogsResponse)
async def get_camera_logs(
    camera_id: str,
    level: Optional[str] = None,
    component: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 100
):
    """
    Obtener logs técnicos de una cámara.
    
    Devuelve logs paginados con filtros opcionales por nivel, componente y rango de fechas.
    Los niveles disponibles son: DEBUG, INFO, WARNING, ERROR.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        level: Filtrar por nivel de log (DEBUG, INFO, WARNING, ERROR)
        component: Filtrar por componente (connection, streaming, discovery, etc)
        start_date: Fecha inicial del rango
        end_date: Fecha final del rango
        page: Número de página (default: 1)
        page_size: Logs por página (default: 100, max: 500)
        
    Returns:
        CameraLogsResponse: Lista paginada de logs
        
    Raises:
        HTTPException 404: Si la cámara no existe
        HTTPException 400: Parámetros inválidos
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        # Validar nivel de log
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if level and level.upper() not in valid_levels:
            logger.warning(f"Nivel de log inválido: {level}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nivel de log inválido. Debe ser uno de: {', '.join(valid_levels)}"
            )
        
        # Validar paginación
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de página debe ser mayor a 0"
            )
        
        if page_size < 1 or page_size > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tamaño de página debe estar entre 1 y 500"
            )
        
        # Validar rango de fechas
        if start_date and end_date and start_date > end_date:
            logger.warning(f"Rango de fechas inválido: {start_date} > {end_date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha inicial debe ser anterior a la fecha final"
            )
            
        logger.info(f"Obteniendo logs de cámara {camera_id}, página {page}")
        
        result = await camera_manager_service.get_camera_logs(
            camera_id,
            level=level.upper() if level else None,
            component=component,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        return create_response(
            success=True,
            data=result
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/snapshots", response_model=CameraSnapshotsResponse)
async def get_camera_snapshots(
    camera_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    trigger: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    Obtener lista de snapshots/capturas de una cámara.
    
    Devuelve información sobre las capturas guardadas, incluyendo metadatos
    como tamaño, resolución, y trigger que generó la captura.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        start_date: Fecha inicial del rango
        end_date: Fecha final del rango
        trigger: Filtrar por tipo de trigger (manual, scheduled, motion, etc)
        page: Número de página (default: 1)
        page_size: Snapshots por página (default: 20, max: 100)
        
    Returns:
        CameraSnapshotsResponse: Lista paginada de snapshots
        
    Raises:
        HTTPException 404: Si la cámara no existe
        HTTPException 400: Parámetros inválidos
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        # Validar paginación
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de página debe ser mayor a 0"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tamaño de página debe estar entre 1 y 100"
            )
        
        # Validar rango de fechas
        if start_date and end_date and start_date > end_date:
            logger.warning(f"Rango de fechas inválido: {start_date} > {end_date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha inicial debe ser anterior a la fecha final"
            )
        
        # Validar trigger si se proporciona
        valid_triggers = ["manual", "scheduled", "motion", "event", "api"]
        if trigger and trigger not in valid_triggers:
            logger.warning(f"Trigger inválido: {trigger}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trigger inválido. Debe ser uno de: {', '.join(valid_triggers)}"
            )
            
        logger.info(f"Obteniendo snapshots de cámara {camera_id}, página {page}")
        
        result = await camera_manager_service.get_camera_snapshots(
            camera_id,
            start_date=start_date,
            end_date=end_date,
            trigger=trigger,
            page=page,
            page_size=page_size
        )
        
        # Log resumen de resultados
        total_snapshots = result.get('total', 0)
        logger.info(f"Devolviendo {len(result.get('snapshots', []))} de {total_snapshots} snapshots totales")
        
        return create_response(
            success=True,
            data=result
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo snapshots: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error obteniendo snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )