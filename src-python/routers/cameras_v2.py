"""
Router mejorado para endpoints de cámaras con nueva estructura 3FN.
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
    TestConnectionRequest,
    CameraResponse,
    CameraListResponse,
    TestConnectionResponse,
    ConnectionStatus,
    ProtocolType,
    CredentialsResponse,
    ProtocolResponse,
    EndpointRequest,
    EndpointResponse,
    StreamProfileResponse,
    CameraStatisticsResponse,
    CameraCapabilitiesResponse
)
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    CameraAlreadyExistsError,
    InvalidCredentialsError,
    ServiceError
)

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/api/v2/cameras",
    tags=["cameras-v2"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Funciones auxiliares ===

def _build_camera_response(camera_model) -> CameraResponse:
    """
    Construye una respuesta de cámara desde el modelo de dominio.
    
    Args:
        camera_model: Instancia de CameraModel
        
    Returns:
        CameraResponse para la API
    """
    # Credenciales (sin contraseña)
    credentials = CredentialsResponse(
        username=camera_model.connection_config.username,
        auth_type=camera_model.connection_config.auth_type,
        is_configured=bool(camera_model.connection_config.password)
    )
    
    # Protocolos
    protocols = []
    for idx, protocol in enumerate(camera_model.capabilities.supported_protocols):
        port = 80  # Default
        if protocol == ProtocolType.RTSP:
            port = camera_model.connection_config.rtsp_port
        elif protocol == ProtocolType.ONVIF:
            port = camera_model.connection_config.onvif_port
        elif protocol == ProtocolType.HTTP:
            port = camera_model.connection_config.http_port
            
        protocols.append(ProtocolResponse(
            protocol_type=protocol,
            port=port,
            is_enabled=True,
            is_primary=idx == 0
        ))
    
    # Endpoints descubiertos
    endpoints = []
    for ep_type, ep_data in camera_model.discovered_endpoints.items():
        endpoints.append(EndpointResponse(
            type=ep_type,
            url=ep_data['url'],
            is_verified=ep_data.get('verified', False),
            priority=ep_data.get('priority', 0)
        ))
    
    # Perfiles de streaming
    stream_profiles = []
    for profile in camera_model.stream_profiles:
        stream_profiles.append(StreamProfileResponse(**profile))
    
    # Si no hay perfiles, crear uno por defecto
    if not stream_profiles:
        stream_profiles.append(StreamProfileResponse(
            profile_name="default",
            stream_type="main",
            resolution=camera_model.stream_config.resolution,
            fps=camera_model.stream_config.fps,
            bitrate=camera_model.stream_config.bitrate,
            codec=camera_model.stream_config.codec,
            channel=camera_model.stream_config.channel,
            subtype=camera_model.stream_config.subtype,
            is_default=True
        ))
    
    # Capacidades
    capabilities = CameraCapabilitiesResponse(
        supported_protocols=camera_model.capabilities.supported_protocols,
        has_ptz=camera_model.capabilities.has_ptz,
        has_audio=camera_model.capabilities.has_audio,
        has_ir=camera_model.capabilities.has_ir,
        max_resolution=camera_model.capabilities.max_resolution,
        supported_codecs=camera_model.capabilities.supported_codecs
    )
    
    # Estadísticas
    statistics = CameraStatisticsResponse(
        total_connections=camera_model.stats.connection_attempts,
        successful_connections=camera_model.stats.successful_connections,
        failed_connections=camera_model.stats.failed_connections,
        success_rate=camera_model.stats.get_success_rate(),
        last_connection_at=camera_model.stats.last_connection_time,
        last_error_message=camera_model.stats.last_error
    )
    
    return CameraResponse(
        camera_id=camera_model.camera_id,
        brand=camera_model.brand,
        model=camera_model.model,
        display_name=camera_model.display_name,
        ip_address=camera_model.connection_config.ip,
        mac_address=camera_model.mac_address,
        status=camera_model.status,
        is_active=camera_model.is_active,
        is_connected=camera_model.is_connected,
        is_streaming=camera_model.is_streaming,
        firmware_version=camera_model.firmware_version,
        hardware_version=camera_model.hardware_version,
        serial_number=camera_model.serial_number,
        location=camera_model.location,
        description=camera_model.description,
        credentials=credentials,
        protocols=protocols,
        endpoints=endpoints,
        stream_profiles=stream_profiles,
        capabilities=capabilities,
        statistics=statistics,
        created_at=camera_model.created_at,
        updated_at=camera_model.last_updated
    )


# === Endpoints ===

@router.get("/", response_model=CameraListResponse)
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
        camera_responses = [_build_camera_response(camera) for camera in cameras]
        
        return CameraListResponse(
            total=len(camera_responses),
            cameras=camera_responses
        )
        
    except Exception as e:
        logger.error(f"Error listando cámaras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{camera_id}", response_model=CameraResponse)
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
    try:
        logger.info(f"Obteniendo información de cámara: {camera_id}")
        
        camera = await camera_manager_service.get_camera(camera_id)
        return _build_camera_response(camera)
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error obteniendo cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
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
        
        return _build_camera_response(camera)
        
    except CameraAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creando cámara: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{camera_id}", response_model=CameraResponse)
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
        
        return _build_camera_response(camera)
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error actualizando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    try:
        logger.info(f"Eliminando cámara: {camera_id}")
        
        await camera_manager_service.delete_camera(camera_id)
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error eliminando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{camera_id}/connect")
async def connect_camera(camera_id: str, background_tasks: BackgroundTasks):
    """
    Conectar a una cámara.
    
    Args:
        camera_id: ID de la cámara
        background_tasks: Tareas en background de FastAPI
        
    Returns:
        Estado de la conexión
    """
    try:
        logger.info(f"Conectando a cámara: {camera_id}")
        
        # Conectar en background para no bloquear
        background_tasks.add_task(
            camera_manager_service.connect_camera,
            camera_id
        )
        
        return create_response(
            success=True,
            data={
                "camera_id": camera_id,
                "status": "connecting",
                "message": "Conexión iniciada"
            }
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error conectando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{camera_id}/disconnect")
async def disconnect_camera(camera_id: str):
    """
    Desconectar una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Estado de la desconexión
    """
    try:
        logger.info(f"Desconectando cámara: {camera_id}")
        
        success = await camera_manager_service.disconnect_camera(camera_id)
        
        return create_response(
            success=success,
            data={
                "camera_id": camera_id,
                "status": "disconnected",
                "message": "Cámara desconectada"
            }
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error desconectando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """
    Probar conexión a una cámara sin guardarla.
    
    Args:
        request: Datos de conexión
        
    Returns:
        Resultado de la prueba
    """
    try:
        logger.info(f"Probando conexión a {request.ip}")
        
        connection_data = {
            'ip': request.ip,
            'username': request.username,
            'password': request.password,
            'brand': request.brand or 'Generic'
        }
        
        if request.port:
            if request.protocol == ProtocolType.RTSP:
                connection_data['rtsp_port'] = request.port
            elif request.protocol == ProtocolType.ONVIF:
                connection_data['onvif_port'] = request.port
            elif request.protocol == ProtocolType.HTTP:
                connection_data['http_port'] = request.port
        
        success, message = await camera_manager_service.test_camera_connection(connection_data)
        
        return TestConnectionResponse(
            success=success,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error probando conexión: {e}")
        return TestConnectionResponse(
            success=False,
            message=str(e)
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
    try:
        logger.info(f"Obteniendo estadísticas de cámara: {camera_id}")
        
        stats = await camera_manager_service.get_camera_statistics(camera_id)
        
        return create_response(
            success=True,
            data=stats
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error agregando endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )