"""
Router para endpoints de capacidades de cámaras.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging

from api.dependencies import create_response
from api.models.camera_models import (
    CameraCapabilitiesDetailResponse
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
    tags=["camera-capabilities"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Endpoints de Capacidades ===


@router.get("/{camera_id}/capabilities", response_model=CameraCapabilitiesDetailResponse)
async def get_camera_capabilities(camera_id: str):
    """
    Obtener las capacidades detalladas de una cámara.
    
    Devuelve información completa sobre las capacidades detectadas de la cámara,
    organizadas por categorías: video, audio, PTZ, analytics, events, network, storage.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        
    Returns:
        CameraCapabilitiesDetailResponse: Capacidades organizadas por categoría
        
    Raises:
        HTTPException 404: Si la cámara no existe
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
            
        logger.info(f"Obteniendo capacidades de cámara: {camera_id}")
        
        capabilities = await camera_manager_service.get_camera_capabilities_detail(camera_id)
        
        # Log resumen de capacidades encontradas
        if capabilities:
            video_caps = capabilities.get('video', {})
            audio_caps = capabilities.get('audio', {})
            ptz_caps = capabilities.get('ptz', {})
            logger.info(
                f"Capacidades obtenidas para cámara {camera_id}: "
                f"Video: {video_caps.get('supported', False)}, "
                f"Audio: {audio_caps.get('supported', False)}, "
                f"PTZ: {ptz_caps.get('supported', False)}"
            )
        
        return create_response(
            success=True,
            data=capabilities
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
        logger.error(f"Error de servicio obteniendo capacidades: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado obteniendo capacidades para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )