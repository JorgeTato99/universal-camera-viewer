"""
Endpoints REST para gestión de publicación a MediaMTX.

Expone funcionalidades de control y monitoreo de streams publicados.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any

from api.models.publishing_models import (
    StartPublishRequest,
    StopPublishRequest,
    PublishStatusResponse,
    PublishListResponse,
    MediaMTXConfigRequest
)
from presenters.publishing_presenter import get_publishing_presenter
from models.publishing import PublishConfiguration, PublisherProcess, PublishErrorType
from utils.exceptions import ServiceError

# Configurar logger
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/publishing",
    tags=["publishing"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/start",
    response_model=PublishStatusResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Solicitud inválida o cámara ya publicando"},
        404: {"description": "Cámara no encontrada"},
        500: {"description": "Error interno del servidor"}
    }
)
async def start_publishing(
    request: StartPublishRequest,
    presenter = Depends(get_publishing_presenter)
) -> PublishStatusResponse:
    """
    Inicia la publicación de una cámara a MediaMTX.
    
    Inicia un proceso FFmpeg para realizar relay del stream RTSP
    de la cámara hacia el servidor MediaMTX.
    
    Args:
        request: Datos de la solicitud con camera_id y force_restart
        
    Returns:
        PublishStatusResponse con el estado actual de la publicación
        
    Raises:
        HTTPException: Si hay errores en la solicitud o el proceso
    """
    logger.info(f"API: Solicitud de publicación para cámara {request.camera_id} "
               f"(force_restart={request.force_restart})")
    
    try:
        # Delegar al presenter
        result = await presenter.start_publishing(
            camera_id=request.camera_id,
            force_restart=request.force_restart
        )
        
        if not result.success:
            # Determinar código de estado según tipo de error
            status_code = status.HTTP_400_BAD_REQUEST
            
            if result.error_type == PublishErrorType.STREAM_UNAVAILABLE:
                status_code = status.HTTP_404_NOT_FOUND
            elif result.error_type == PublishErrorType.ALREADY_PUBLISHING:
                status_code = status.HTTP_409_CONFLICT
            elif result.error_type in [PublishErrorType.PROCESS_CRASHED, PublishErrorType.UNKNOWN]:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                
            logger.warning(f"Fallo al iniciar publicación: {result.error} (tipo: {result.error_type})")
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": result.error or "Error iniciando publicación",
                    "error_type": result.error_type.value if result.error_type else None,
                    "camera_id": request.camera_id
                }
            )
        
        # Obtener estado actualizado
        process = await presenter.get_camera_status(request.camera_id)
        if not process:
            logger.error(f"No se pudo obtener estado después de iniciar para {request.camera_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo estado después de iniciar"
            )
            
        # Obtener path desde el presenter
        publish_path = result.publish_path
        if hasattr(presenter, '_config') and presenter._config:
            publish_path = presenter._config.get_publish_path(request.camera_id)
            
        response = PublishStatusResponse(
            camera_id=process.camera_id,
            status=process.status,
            publish_path=publish_path,
            uptime_seconds=process.uptime_seconds,
            error_count=process.error_count,
            last_error=process.last_error,
            metrics=process.metrics
        )
        
        logger.info(f"Publicación iniciada exitosamente para {request.camera_id}")
        return response
        
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"ServiceError en start_publishing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "error_code": e.error_code if hasattr(e, 'error_code') else None
            }
        )
    except Exception as e:
        logger.exception(f"Error inesperado en start_publishing para {request.camera_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/stop",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Cámara no encontrada o no publicando"},
        500: {"description": "Error al detener publicación"}
    }
)
async def stop_publishing(
    request: StopPublishRequest,
    presenter = Depends(get_publishing_presenter)
) -> Dict[str, str]:
    """
    Detiene la publicación de una cámara.
    
    Termina el proceso FFmpeg asociado y libera recursos.
    
    Args:
        request: Datos con el camera_id a detener
        
    Returns:
        Mensaje de confirmación
        
    Raises:
        HTTPException: Si la cámara no está publicando
    """
    logger.info(f"API: Solicitud para detener publicación de cámara {request.camera_id}")
    
    try:
        success = await presenter.stop_publishing(request.camera_id)
        
        if not success:
            logger.warning(f"Cámara {request.camera_id} no está publicando")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Cámara no está publicando actualmente",
                    "camera_id": request.camera_id
                }
            )
            
        logger.info(f"Publicación detenida exitosamente para {request.camera_id}")
        return {
            "message": "Publicación detenida exitosamente",
            "camera_id": request.camera_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado deteniendo publicación para {request.camera_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al detener publicación"
        )


@router.get(
    "/status",
    response_model=PublishListResponse,
    responses={
        200: {"description": "Lista de todas las publicaciones"}
    }
)
async def get_publishing_status(
    presenter = Depends(get_publishing_presenter)
) -> PublishListResponse:
    """
    Obtiene el estado de todas las publicaciones.
    
    Retorna información detallada de todos los procesos de publicación,
    tanto activos como en error o detenidos recientemente.
    
    Returns:
        PublishListResponse con lista completa y estadísticas
    """
    logger.debug("API: Obteniendo estado de todas las publicaciones")
    
    try:
        all_processes = await presenter.get_all_status()
        
        items = []
        active_count = 0
        error_count = 0
        
        for camera_id, process in all_processes.items():
            # Obtener path desde la configuración
            publish_path = None
            if hasattr(presenter, '_config') and presenter._config:
                publish_path = presenter._config.get_publish_path(camera_id)
                
            status_item = PublishStatusResponse(
                camera_id=camera_id,
                status=process.status,
                publish_path=publish_path,
                uptime_seconds=process.uptime_seconds,
                error_count=process.error_count,
                last_error=process.last_error,
                metrics=process.metrics
            )
            items.append(status_item)
            
            # Contar por estado
            if process.is_active:
                active_count += 1
            elif process.status.value == "error":
                error_count += 1
                
        response = PublishListResponse(
            total=len(items),
            active=active_count,
            items=items
        )
        
        logger.info(f"Estado de publicaciones: Total={len(items)}, Activas={active_count}, "
                   f"En error={error_count}")
        
        return response
        
    except Exception as e:
        logger.exception("Error obteniendo estado de publicaciones")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de publicaciones"
        )


@router.get(
    "/status/{camera_id}",
    response_model=PublishStatusResponse,
    responses={
        200: {"description": "Estado de publicación de la cámara"},
        404: {"description": "Cámara no encontrada o sin publicación"}
    }
)
async def get_camera_publishing_status(
    camera_id: str,
    presenter = Depends(get_publishing_presenter)
) -> PublishStatusResponse:
    """
    Obtiene el estado de publicación de una cámara específica.
    
    Args:
        camera_id: Identificador único de la cámara
        
    Returns:
        PublishStatusResponse con estado detallado
        
    Raises:
        HTTPException: Si la cámara no existe o no tiene proceso
    """
    logger.debug(f"API: Obteniendo estado de publicación para cámara {camera_id}")
    
    try:
        # Validar entrada
        if not camera_id or not camera_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="camera_id no puede estar vacío"
            )
            
        process = await presenter.get_camera_status(camera_id)
        
        if not process:
            logger.debug(f"Cámara {camera_id} no tiene proceso de publicación")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Cámara no encontrada o sin proceso de publicación",
                    "camera_id": camera_id
                }
            )
        
        # Obtener path desde la configuración
        publish_path = None
        if hasattr(presenter, '_config') and presenter._config:
            publish_path = presenter._config.get_publish_path(camera_id)
            
        response = PublishStatusResponse(
            camera_id=process.camera_id,
            status=process.status,
            publish_path=publish_path,
            uptime_seconds=process.uptime_seconds,
            error_count=process.error_count,
            last_error=process.last_error,
            metrics=process.metrics
        )
        
        logger.info(f"Estado obtenido para {camera_id}: {process.status.value}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error obteniendo estado para {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de publicación"
        )