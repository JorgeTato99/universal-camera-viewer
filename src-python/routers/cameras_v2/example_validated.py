"""
Ejemplo de router con validación completa usando los nuevos schemas.

Este archivo muestra cómo implementar las validaciones en un endpoint real.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import logging

from api.schemas.requests.camera_requests import (
    CreateCameraRequest,
    UpdateCameraRequest,
    CameraFilterRequest,
    BatchCameraOperationRequest
)
from api.schemas.responses.camera_responses import (
    CameraDetailResponse,
    CameraListResponse,
    CameraOperationResponse,
    BatchOperationResponse
)
from api.dependencies import create_response
from api.dependencies.validation_deps import (
    validate_camera_exists,
    validate_camera_not_exists,
    validate_camera_connected,
    scan_rate_limit
)
from services.camera_manager_service import camera_manager_service
from utils.exceptions import ServiceError

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/api/v2/cameras",
    tags=["cameras-v2-validated"],
    responses={
        404: {"description": "Cámara no encontrada"},
        400: {"description": "Datos inválidos"},
        409: {"description": "Conflicto con el estado actual"}
    }
)


@router.post("/", response_model=CameraDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    request: CreateCameraRequest,
    _: str = Depends(lambda req: validate_camera_not_exists(req.ip))
):
    """
    Crear una nueva cámara con validación completa.
    
    Este endpoint muestra cómo usar:
    - Validación automática con Pydantic (CreateCameraRequest)
    - Validación con dependencies (validate_camera_not_exists)
    - Manejo de errores estructurado
    """
    try:
        logger.info(f"Creando nueva cámara: {request.display_name} ({request.ip})")
        
        # Preparar datos para el servicio
        camera_data = {
            'brand': request.brand,
            'model': request.model,
            'display_name': request.display_name,
            'ip': request.ip,
            'username': request.username,
            'password': request.password,
            'auth_type': request.auth_type,
            'rtsp_port': request.rtsp_port,
            'onvif_port': request.onvif_port,
            'http_port': request.http_port,
            'location': request.location,
            'description': request.description
        }
        
        # Crear cámara usando el servicio
        camera = await camera_manager_service.create_camera(camera_data)
        
        # Construir respuesta estructurada
        response = CameraDetailResponse(
            basic_info={
                'camera_id': camera.camera_id,
                'display_name': camera.display_name,
                'ip_address': camera.connection_config.ip,
                'brand': camera.brand,
                'model': camera.model,
                'status': camera.status,
                'is_active': camera.is_active,
                'is_connected': camera.is_connected
            },
            connection_info={
                'primary_protocol': camera.connection_config.primary_protocol,
                'rtsp_port': camera.connection_config.rtsp_port,
                'onvif_port': camera.connection_config.onvif_port,
                'http_port': camera.connection_config.http_port,
                'has_credentials': bool(camera.connection_config.username),
                'last_connection_time': getattr(camera, 'last_connection_time', None),
                'connection_errors': getattr(camera, 'connection_errors', 0)
            },
            capabilities={
                'supports_onvif': 'ONVIF' in camera.capabilities.supported_protocols,
                'supports_rtsp': 'RTSP' in camera.capabilities.supported_protocols,
                'supports_ptz': camera.capabilities.features.get('ptz', False),
                'supports_audio': camera.capabilities.features.get('audio', False),
                'supports_motion_detection': camera.capabilities.features.get('motion_detection', False),
                'max_resolution': camera.capabilities.max_resolution,
                'max_fps': camera.capabilities.max_fps
            },
            statistics={
                'total_connections': 0,
                'successful_connections': 0,
                'failed_connections': 0,
                'total_streaming_time': 0,
                'total_snapshots': 0,
                'average_fps': 0.0,
                'bandwidth_usage': 0
            },
            location=camera.location,
            description=camera.description,
            created_at=camera.created_at,
            updated_at=camera.last_updated
        )
        
        logger.info(f"Cámara {camera.camera_id} creada exitosamente")
        return response
        
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


@router.put("/{camera_id}", response_model=CameraDetailResponse)
async def update_camera(
    request: UpdateCameraRequest,
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Actualizar una cámara existente.
    
    Usa dependency injection para validar que la cámara existe.
    """
    try:
        logger.info(f"Actualizando cámara {camera_id}")
        
        # Preparar solo los campos que se actualizarán
        updates = {}
        if request.display_name is not None:
            updates['display_name'] = request.display_name
        if request.location is not None:
            updates['location'] = request.location
        if request.description is not None:
            updates['description'] = request.description
        if request.is_active is not None:
            updates['is_active'] = request.is_active
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )
        
        # Actualizar usando el servicio
        camera = await camera_manager_service.update_camera(camera_id, updates)
        
        # Construir y devolver respuesta
        # (mismo código de construcción que en create_camera)
        
        logger.info(f"Cámara {camera_id} actualizada exitosamente")
        return create_response(success=True, data={"message": "Cámara actualizada"})
        
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio actualizando cámara: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado actualizando cámara: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/", response_model=CameraListResponse)
async def list_cameras(filter_params: CameraFilterRequest = Depends()):
    """
    Listar cámaras con filtros y paginación.
    
    Los parámetros se validan automáticamente usando CameraFilterRequest.
    """
    try:
        logger.info(f"Listando cámaras - página {filter_params.page}, tamaño {filter_params.page_size}")
        
        # Obtener cámaras del servicio
        cameras = await camera_manager_service.get_all_cameras()
        
        # Aplicar filtros
        filtered_cameras = cameras
        if filter_params.brand:
            filtered_cameras = [c for c in filtered_cameras if c.brand == filter_params.brand]
        if filter_params.is_active is not None:
            filtered_cameras = [c for c in filtered_cameras if c.is_active == filter_params.is_active]
        if filter_params.is_connected is not None:
            filtered_cameras = [c for c in filtered_cameras if c.is_connected == filter_params.is_connected]
        if filter_params.location:
            filtered_cameras = [c for c in filtered_cameras if filter_params.location.lower() in (c.location or '').lower()]
        
        # Ordenar
        # (implementar lógica de ordenamiento según sort_by y sort_order)
        
        # Paginar
        total = len(filtered_cameras)
        start = (filter_params.page - 1) * filter_params.page_size
        end = start + filter_params.page_size
        page_cameras = filtered_cameras[start:end]
        
        # Construir respuesta
        response = CameraListResponse(
            total=total,
            page=filter_params.page,
            page_size=filter_params.page_size,
            cameras=[
                {
                    'camera_id': c.camera_id,
                    'display_name': c.display_name,
                    'ip_address': c.connection_config.ip,
                    'brand': c.brand,
                    'model': c.model,
                    'status': c.status,
                    'is_active': c.is_active,
                    'is_connected': c.is_connected
                }
                for c in page_cameras
            ]
        )
        
        return response
        
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


@router.post("/batch", response_model=BatchOperationResponse)
async def batch_operation(
    request: BatchCameraOperationRequest,
    background_tasks: BackgroundTasks
):
    """
    Realizar operaciones en lote sobre múltiples cámaras.
    
    Muestra validación de listas y operaciones asíncronas.
    """
    try:
        logger.info(f"Operación en lote '{request.operation}' para {len(request.camera_ids)} cámaras")
        
        results = []
        successful = 0
        failed = 0
        
        for camera_id in request.camera_ids:
            try:
                # Ejecutar operación según el tipo
                if request.operation == 'connect':
                    background_tasks.add_task(
                        camera_manager_service.connect_camera,
                        camera_id
                    )
                    message = "Conexión iniciada"
                    success = True
                elif request.operation == 'disconnect':
                    success = await camera_manager_service.disconnect_camera(camera_id)
                    message = "Cámara desconectada" if success else "Error al desconectar"
                # ... más operaciones ...
                else:
                    success = False
                    message = f"Operación '{request.operation}' no implementada"
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                results.append(CameraOperationResponse(
                    success=success,
                    camera_id=camera_id,
                    operation=request.operation,
                    message=message
                ))
                
            except Exception as e:
                failed += 1
                logger.error(f"Error en operación {request.operation} para cámara {camera_id}: {e}")
                results.append(CameraOperationResponse(
                    success=False,
                    camera_id=camera_id,
                    operation=request.operation,
                    message=str(e)
                ))
        
        return BatchOperationResponse(
            total_requested=len(request.camera_ids),
            successful=successful,
            failed=failed,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error en operación batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )