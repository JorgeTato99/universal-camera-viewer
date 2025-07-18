"""
Router para endpoints CRUD básicos de cámaras.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging
import asyncio

from api.dependencies import create_response
from api.models.camera_models import (
    CreateCameraRequest,
    UpdateCameraRequest,
    CameraResponse,
    CameraListResponse,
    ProtocolType,
    EndpointRequest,
)
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    CameraAlreadyExistsError,
    InvalidCredentialsError,
    ServiceError
)
from .shared import build_camera_response

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/cameras",
    tags=["cameras-v2-crud"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Endpoints CRUD ===

@router.get("/")
async def list_cameras(
    active_only: bool = True,
    protocol: Optional[ProtocolType] = None
):
    """
    Listar todas las cámaras configuradas.
    
    Args:
        active_only: Si solo mostrar cámaras activas
        protocol: Filtrar por protocolo específico
        
    Returns:
        Lista de cámaras con información completa
    """
    try:
        logger.info(f"Listando cámaras - active_only: {active_only}, protocol: {protocol}")
        
        # Obtener todas las cámaras
        cameras = await camera_manager_service.get_all_cameras()
        
        # Filtrar si es necesario
        if active_only:
            cameras = [c for c in cameras if c.is_active]
            
        if protocol:
            cameras = [c for c in cameras if c.can_connect_with_protocol(protocol)]
        
        # Construir respuestas
        camera_responses = []
        for camera in cameras:
            try:
                camera_responses.append(build_camera_response(camera))
            except ValueError as e:
                logger.warning(f"Error construyendo respuesta para cámara {getattr(camera, 'camera_id', 'unknown')}: {e}")
                # Continuar con las demás cámaras
        
        response_data = CameraListResponse(
            total=len(camera_responses),
            cameras=camera_responses
        )
        
        return create_response(
            success=True,
            data=response_data.dict()
        )
        
    except ServiceError as e:
        logger.error(f"Error de servicio listando cámaras: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado listando cámaras: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}")
async def get_camera(camera_id: str):
    """
    Obtener información detallada de una cámara específica.
    
    Args:
        camera_id: ID único de la cámara
        
    Returns:
        Información completa de la cámara
        
    Raises:
        HTTPException: Si la cámara no existe
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
    try:
        logger.info(f"Obteniendo información de cámara: {camera_id}")
        
        camera = await camera_manager_service.get_camera(camera_id)
        camera_response = build_camera_response(camera)
        
        return create_response(
            success=True,
            data=camera_response.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.error(f"Error construyendo respuesta para cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar información de la cámara"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado obteniendo cámara {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_camera(request: CreateCameraRequest):
    """
    Crear una nueva cámara.
    
    Args:
        request: Datos de la nueva cámara
        
    Returns:
        Cámara creada
        
    Raises:
        HTTPException: Si la cámara ya existe o hay error de validación
    """
    try:
        # Validar datos de entrada
        if not request.display_name or not request.ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="display_name e ip son campos obligatorios"
            )
            
        logger.info(f"Creando nueva cámara: {request.display_name} ({request.ip})")
        
        # Preparar datos
        camera_data = {
            'brand': request.brand,
            'model': request.model,
            'display_name': request.display_name,
            'ip': request.ip,
            'username': request.credentials.username,
            'password': request.credentials.password,
            'auth_type': request.credentials.auth_type,
            'location': request.location,
            'description': request.description
        }
        
        # Agregar protocolos si se proporcionan
        if request.protocols:
            for protocol in request.protocols:
                if protocol.protocol_type == ProtocolType.RTSP:
                    camera_data['rtsp_port'] = protocol.port
                elif protocol.protocol_type == ProtocolType.ONVIF:
                    camera_data['onvif_port'] = protocol.port
                elif protocol.protocol_type == ProtocolType.HTTP:
                    camera_data['http_port'] = protocol.port
        
        # Agregar endpoints si se proporcionan
        if request.endpoints:
            camera_data['endpoints'] = [
                {
                    'type': ep.type,
                    'url': ep.url,
                    'verified': ep.verified,
                    'priority': ep.priority
                }
                for ep in request.endpoints
            ]
        
        # Crear cámara
        camera = await camera_manager_service.create_camera(camera_data)
        camera_response = build_camera_response(camera)
        
        return create_response(
            success=True,
            data=camera_response.dict()
        )
        
    except CameraAlreadyExistsError as e:
        logger.warning(f"Cámara ya existe: {request.ip}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        logger.error(f"Error de validación creando cámara: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Error de servicio creando cámara: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado creando cámara: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{camera_id}")
async def update_camera(camera_id: str, request: UpdateCameraRequest):
    """
    Actualizar una cámara existente.
    
    Args:
        camera_id: ID de la cámara
        request: Datos a actualizar
        
    Returns:
        Cámara actualizada
        
    Raises:
        HTTPException: Si la cámara no existe
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
    try:
        logger.info(f"Actualizando cámara: {camera_id}")
        
        # Preparar actualizaciones
        updates = {}
        
        if request.display_name is not None:
            updates['display_name'] = request.display_name
        if request.location is not None:
            updates['location'] = request.location
        if request.description is not None:
            updates['description'] = request.description
        if request.is_active is not None:
            updates['is_active'] = request.is_active
            
        if request.credentials:
            updates['credentials'] = {
                'username': request.credentials.username,
                'password': request.credentials.password
            }
            
        if request.endpoints:
            updates['endpoints'] = [
                {
                    'type': ep.type,
                    'url': ep.url,
                    'verified': ep.verified,
                    'priority': ep.priority
                }
                for ep in request.endpoints
            ]
        
        # Actualizar cámara
        camera = await camera_manager_service.update_camera(camera_id, updates)
        camera_response = build_camera_response(camera)
        
        return create_response(
            success=True,
            data=camera_response.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada para actualizar: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.error(f"Error de validación actualizando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Error de servicio actualizando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado actualizando cámara {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: str):
    """
    Eliminar una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Raises:
        HTTPException: Si la cámara no existe
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
    try:
        logger.info(f"Eliminando cámara: {camera_id}")
        
        await camera_manager_service.delete_camera(camera_id)
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada para eliminar: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio eliminando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado eliminando cámara {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/statistics")
async def get_camera_statistics(camera_id: str):
    """
    Obtener estadísticas de una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Estadísticas detalladas
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
    try:
        logger.info(f"Obteniendo estadísticas de cámara: {camera_id}")
        
        stats = await camera_manager_service.get_camera_statistics(camera_id)
        
        return create_response(
            success=True,
            data=stats
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada para estadísticas: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado obteniendo estadísticas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/endpoints")
async def add_camera_endpoint(
    camera_id: str,
    endpoint: EndpointRequest
):
    """
    Agregar un endpoint descubierto a una cámara.
    
    Args:
        camera_id: ID de la cámara
        endpoint: Datos del endpoint
        
    Returns:
        Confirmación
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
    # Validar endpoint
    if not endpoint.type or not endpoint.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="type y url son campos obligatorios para el endpoint"
        )
        
    try:
        logger.info(f"Agregando endpoint a cámara {camera_id}: {endpoint.type}")
        
        success = await camera_manager_service.save_discovered_endpoint(
            camera_id=camera_id,
            endpoint_type=endpoint.type,
            url=endpoint.url,
            verified=endpoint.verified
        )
        
        return create_response(
            success=success,
            data={
                "camera_id": camera_id,
                "endpoint_type": endpoint.type,
                "message": "Endpoint agregado exitosamente"
            }
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada para agregar endpoint: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.error(f"Error de validación agregando endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Error de servicio agregando endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado agregando endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )