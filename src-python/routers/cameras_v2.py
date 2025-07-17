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
    CameraCapabilitiesResponse,
    CreateCredentialRequest,
    UpdateCredentialRequest,
    CredentialDetailResponse,
    CredentialListResponse,
    # Protocol management models
    ProtocolStatus,
    UpdateProtocolRequest,
    TestProtocolRequest,
    DiscoverProtocolsRequest,
    ProtocolDetailResponse,
    ProtocolListResponse,
    TestProtocolResponse,
    DiscoverProtocolsResponse,
    # Read-only endpoints models
    EventType,
    EventSeverity,
    CameraEventsResponse,
    CameraLogsResponse,
    CameraSnapshotsResponse,
    CameraCapabilitiesDetailResponse
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
    prefix="/cameras",
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
        camera_responses = [_build_camera_response(camera) for camera in cameras]
        
        response_data = CameraListResponse(
            total=len(camera_responses),
            cameras=camera_responses
        )
        
        return create_response(
            success=True,
            data=response_data.dict()
        )
        
    except Exception as e:
        logger.error(f"Error listando cámaras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    try:
        logger.info(f"Obteniendo información de cámara: {camera_id}")
        
        camera = await camera_manager_service.get_camera(camera_id)
        camera_response = _build_camera_response(camera)
        
        return create_response(
            success=True,
            data=camera_response.dict()
        )
        
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
        camera_response = _build_camera_response(camera)
        
        return create_response(
            success=True,
            data=camera_response.dict()
        )
        
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
        camera_response = _build_camera_response(camera)
        
        return create_response(
            success=True,
            data=camera_response.dict()
        )
        
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


@router.post("/test-connection")
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
        
        response_data = TestConnectionResponse(
            success=success,
            message=message
        )
        
        return create_response(
            success=True,
            data=response_data.dict()
        )
        
    except Exception as e:
        logger.error(f"Error probando conexión: {e}")
        response_data = TestConnectionResponse(
            success=False,
            message=str(e)
        )
        
        return create_response(
            success=False,
            error=str(e),
            data=response_data.dict()
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


# === Endpoints de Credenciales ===

@router.get("/{camera_id}/credentials", response_model=CredentialListResponse)
async def list_camera_credentials(camera_id: str):
    """
    Listar todas las credenciales de una cámara.
    
    Las credenciales se devuelven sin las contraseñas por seguridad.
    La credencial marcada como 'is_default' será la utilizada para conexiones automáticas.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        
    Returns:
        CredentialListResponse: Lista de credenciales con información básica
        
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
            
        logger.info(f"Listando credenciales de cámara: {camera_id}")
        
        credentials = await camera_manager_service.get_camera_credentials(camera_id)
        
        # Construir respuesta con validación
        credential_responses = []
        for cred in credentials:
            try:
                credential_responses.append(CredentialDetailResponse(
                    credential_id=cred['credential_id'],
                    credential_name=cred['credential_name'],
                    username=cred['username'],
                    auth_type=cred['auth_type'],
                    is_active=cred['is_active'],
                    is_default=cred['is_default'],
                    last_used=cred.get('last_used'),
                    created_at=cred['created_at'],
                    updated_at=cred['updated_at']
                ))
            except Exception as e:
                logger.warning(f"Error procesando credencial {cred.get('credential_id')}: {e}")
                # Continuar con las demás credenciales
        
        response_data = CredentialListResponse(
            total=len(credential_responses),
            credentials=credential_responses
        )
        
        logger.info(f"Devolviendo {len(credential_responses)} credenciales para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=response_data.dict()
        )
        
    except CameraNotFoundError as e:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio listando credenciales: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado listando credenciales para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/credentials", status_code=status.HTTP_201_CREATED, response_model=CredentialDetailResponse)
async def create_camera_credential(
    camera_id: str,
    request: CreateCredentialRequest
):
    """
    Agregar una nueva credencial a una cámara.
    
    Si es la primera credencial o se marca como 'is_default', se establecerá automáticamente
    como la credencial predeterminada. Solo puede haber una credencial predeterminada por cámara.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        request: Datos de la nueva credencial incluyendo usuario y contraseña
        
    Returns:
        CredentialDetailResponse: Credencial creada (sin contraseña)
        
    Raises:
        HTTPException 400: Datos inválidos o credencial duplicada
        HTTPException 404: Si la cámara no existe
        HTTPException 409: Si ya existe una credencial con el mismo nombre
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
        
        # Validar longitud de contraseña
        if len(request.password) < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 4 caracteres"
            )
            
        logger.info(f"Creando credencial '{request.credential_name}' para cámara {camera_id}")
        
        # Preparar datos con valores por defecto
        credential_data = {
            'credential_name': request.credential_name.strip(),
            'username': request.username.strip(),
            'password': request.password,  # No hacer strip a contraseñas
            'auth_type': request.auth_type.value if hasattr(request.auth_type, 'value') else request.auth_type,
            'is_default': request.is_default
        }
        
        # Validar que no haya espacios en el username
        if ' ' in credential_data['username']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario no puede contener espacios"
            )
        
        credential = await camera_manager_service.add_camera_credential(
            camera_id, 
            credential_data
        )
        
        credential_response = CredentialDetailResponse(
            credential_id=credential['credential_id'],
            credential_name=credential['credential_name'],
            username=credential['username'],
            auth_type=credential['auth_type'],
            is_active=credential['is_active'],
            is_default=credential['is_default'],
            last_used=credential.get('last_used'),
            created_at=credential['created_at'],
            updated_at=credential['updated_at']
        )
        
        logger.info(f"Credencial {credential['credential_id']} creada exitosamente para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=credential_response.dict()
        )
        
    except CameraNotFoundError as e:
        logger.warning(f"Cámara no encontrada al crear credencial: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Datos inválidos al crear credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio creando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado creando credencial para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{camera_id}/credentials/{credential_id}")
async def update_camera_credential(
    camera_id: str,
    credential_id: int,
    request: UpdateCredentialRequest
):
    """
    Actualizar una credencial existente.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        request: Datos a actualizar
        
    Returns:
        Credencial actualizada
    """
    try:
        logger.info(f"Actualizando credencial {credential_id} de cámara {camera_id}")
        
        updates = {}
        if request.credential_name is not None:
            updates['credential_name'] = request.credential_name
        if request.username is not None:
            updates['username'] = request.username
        if request.password is not None and request.password:
            updates['password'] = request.password
        if request.auth_type is not None:
            updates['auth_type'] = request.auth_type
        if request.is_default is not None:
            updates['is_default'] = request.is_default
        
        credential = await camera_manager_service.update_camera_credential(
            camera_id,
            credential_id,
            updates
        )
        
        credential_response = CredentialDetailResponse(
            credential_id=credential['credential_id'],
            credential_name=credential['credential_name'],
            username=credential['username'],
            auth_type=credential['auth_type'],
            is_active=credential['is_active'],
            is_default=credential['is_default'],
            last_used=credential.get('last_used'),
            created_at=credential['created_at'],
            updated_at=credential['updated_at']
        )
        
        return create_response(
            success=True,
            data=credential_response.dict()
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error actualizando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{camera_id}/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera_credential(
    camera_id: str,
    credential_id: int
):
    """
    Eliminar una credencial.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Raises:
        HTTPException: Si la cámara o credencial no existe
    """
    try:
        logger.info(f"Eliminando credencial {credential_id} de cámara {camera_id}")
        
        await camera_manager_service.delete_camera_credential(camera_id, credential_id)
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error eliminando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{camera_id}/credentials/{credential_id}/set-default")
async def set_default_credential(
    camera_id: str,
    credential_id: int
):
    """
    Marcar una credencial como la predeterminada.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Returns:
        Confirmación
    """
    try:
        logger.info(f"Estableciendo credencial {credential_id} como default para cámara {camera_id}")
        
        success = await camera_manager_service.set_default_credential(camera_id, credential_id)
        
        return create_response(
            success=success,
            data={
                "camera_id": camera_id,
                "credential_id": credential_id,
                "message": "Credencial establecida como predeterminada"
            }
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error estableciendo credencial default: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# === Endpoints de Gestión de Protocolos ===


@router.get("/{camera_id}/protocols", response_model=ProtocolListResponse)
async def list_camera_protocols(
    camera_id: str,
    only_enabled: bool = False
):
    """
    Listar todos los protocolos configurados de una cámara.
    
    Los protocolos definen las formas de comunicación disponibles
    (ONVIF, RTSP, HTTP, etc.) con sus configuraciones específicas.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        only_enabled: Si solo mostrar protocolos habilitados
        
    Returns:
        ProtocolListResponse: Lista de protocolos con estado y configuración
        
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
        
        logger.info(f"Listando protocolos de cámara: {camera_id}")
        
        protocols = await camera_manager_service.get_camera_protocols(camera_id)
        
        # Filtrar si se solicita
        if only_enabled:
            protocols = [p for p in protocols if p.get('is_enabled', False)]
        
        # Construir respuesta
        protocol_responses = []
        for protocol in protocols:
            try:
                protocol_responses.append(ProtocolDetailResponse(
                    protocol_id=protocol['protocol_id'],
                    protocol_type=protocol['protocol_type'],
                    port=protocol['port'],
                    is_enabled=protocol['is_enabled'],
                    is_primary=protocol['is_primary'],
                    is_verified=protocol.get('is_verified', False),
                    status=protocol.get('status', 'unknown'),
                    version=protocol.get('version'),
                    path=protocol.get('path'),
                    last_tested=protocol.get('last_tested'),
                    last_error=protocol.get('last_error'),
                    response_time_ms=protocol.get('response_time_ms'),
                    capabilities=protocol.get('capabilities'),
                    created_at=protocol['created_at'],
                    updated_at=protocol['updated_at']
                ))
            except Exception as e:
                logger.warning(f"Error procesando protocolo {protocol.get('protocol_id')}: {e}")
        
        response_data = ProtocolListResponse(
            total=len(protocol_responses),
            protocols=protocol_responses
        )
        
        logger.info(f"Devolviendo {len(protocol_responses)} protocolos para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=response_data.dict()
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
        logger.error(f"Error de servicio listando protocolos: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado listando protocolos para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{camera_id}/protocols/{protocol_type}", response_model=ProtocolDetailResponse)
async def update_protocol_config(
    camera_id: str,
    protocol_type: ProtocolType,
    request: UpdateProtocolRequest
):
    """
    Actualizar la configuración de un protocolo específico.
    
    Permite cambiar puerto, habilitar/deshabilitar, establecer como primario,
    actualizar versión o path específico del protocolo.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        protocol_type: Tipo de protocolo (onvif, rtsp, http, etc.)
        request: Datos de configuración a actualizar
        
    Returns:
        ProtocolDetailResponse: Protocolo actualizado
        
    Raises:
        HTTPException 400: Datos inválidos
        HTTPException 404: Si la cámara o protocolo no existe
        HTTPException 409: Si hay conflicto (ej: puerto en uso)
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
        
        logger.info(f"Actualizando protocolo {protocol_type} de cámara {camera_id}")
        
        # Preparar actualizaciones
        updates = {}
        
        if request.port is not None:
            updates['port'] = request.port
            
        if request.is_enabled is not None:
            updates['is_enabled'] = request.is_enabled
            
        if request.is_primary is not None:
            updates['is_primary'] = request.is_primary
            
        if request.version is not None:
            updates['version'] = request.version.strip()
            
        if request.path is not None:
            updates['path'] = request.path.strip()
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )
        
        protocol = await camera_manager_service.update_protocol_config(
            camera_id, protocol_type.value, updates
        )
        
        protocol_response = ProtocolDetailResponse(
            protocol_id=protocol['protocol_id'],
            protocol_type=protocol['protocol_type'],
            port=protocol['port'],
            is_enabled=protocol['is_enabled'],
            is_primary=protocol['is_primary'],
            is_verified=protocol.get('is_verified', False),
            status=protocol.get('status', 'unknown'),
            version=protocol.get('version'),
            path=protocol.get('path'),
            last_tested=protocol.get('last_tested'),
            last_error=protocol.get('last_error'),
            response_time_ms=protocol.get('response_time_ms'),
            capabilities=protocol.get('capabilities'),
            created_at=protocol['created_at'],
            updated_at=protocol['updated_at']
        )
        
        logger.info(f"Protocolo {protocol_type} actualizado exitosamente")
        
        return create_response(
            success=True,
            data=protocol_response.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        if "no encontrad" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "puerto" in str(e).lower() and "en uso" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio actualizando protocolo: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado actualizando protocolo {protocol_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/protocols/{protocol_type}/test", response_model=TestProtocolResponse)
async def test_protocol(
    camera_id: str,
    protocol_type: ProtocolType,
    request: TestProtocolRequest = TestProtocolRequest()
):
    """
    Probar la conectividad de un protocolo específico.
    
    Realiza una prueba activa del protocolo, verificando conectividad,
    detectando versión y capacidades disponibles.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        protocol_type: Tipo de protocolo a probar
        request: Parámetros de la prueba (timeout, credencial)
        
    Returns:
        TestProtocolResponse: Resultado de la prueba con métricas
        
    Raises:
        HTTPException 404: Si la cámara o protocolo no existe
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
        
        # Validar timeout
        if request.timeout < 1 or request.timeout > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timeout debe estar entre 1 y 60 segundos"
            )
        
        logger.info(f"Probando protocolo {protocol_type} de cámara {camera_id}")
        
        result = await camera_manager_service.test_protocol(
            camera_id,
            protocol_type.value,
            timeout=request.timeout,
            credential_id=request.credential_id
        )
        
        return create_response(
            success=result.get('success', False),
            data=result
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        if "no encontrad" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio probando protocolo: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado probando protocolo {protocol_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/protocols/discover", response_model=DiscoverProtocolsResponse)
async def discover_protocols(
    camera_id: str,
    request: DiscoverProtocolsRequest = DiscoverProtocolsRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    Auto-descubrir protocolos disponibles en la cámara.
    
    Escanea puertos comunes, prueba diferentes protocolos y credenciales
    para detectar automáticamente las capacidades de la cámara.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        request: Parámetros del discovery (puertos, timeout, credenciales)
        background_tasks: Para ejecutar discovery largo en background
        
    Returns:
        DiscoverProtocolsResponse: Protocolos descubiertos
        
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
        
        # Validar parámetros de discovery
        if request.timeout < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timeout mínimo para discovery es 5 segundos"
            )
        
        if request.deep_scan and request.timeout < 30:
            logger.warning(
                f"Deep scan con timeout bajo ({request.timeout}s). "
                "Se recomienda al menos 30 segundos para deep scan."
            )
        
        logger.info(f"Iniciando auto-discovery de protocolos para cámara {camera_id}")
        
        # Si es deep scan y hay background tasks, ejecutar en background
        if request.deep_scan and background_tasks:
            background_tasks.add_task(
                camera_manager_service.discover_protocols_async,
                camera_id,
                scan_common_ports=request.scan_common_ports,
                deep_scan=request.deep_scan,
                timeout=request.timeout,
                credential_ids=request.credential_ids
            )
            
            return create_response(
                success=True,
                data={
                    "discovered_count": 0,
                    "scan_duration_ms": 0,
                    "protocols_found": [],
                    "ports_scanned": [],
                    "credentials_tested": 0,
                    "message": "Discovery iniciado en background. Use GET /protocols para ver el progreso."
                }
            )
        
        # Ejecutar discovery sincrónicamente
        result = await camera_manager_service.discover_protocols(
            camera_id,
            scan_common_ports=request.scan_common_ports,
            deep_scan=request.deep_scan,
            timeout=request.timeout,
            credential_ids=request.credential_ids
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
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio en discovery: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado en discovery de protocolos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# === Endpoints de Solo Lectura (Fase 4) ===

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
    except Exception as e:
        logger.error(f"Error obteniendo capacidades: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de página debe ser mayor a 0"
            )
        
        if page_size < 1 or page_size > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tamaño de página debe estar entre 1 y 200"
            )
        
        # Validar rango de fechas
        if start_date and end_date and start_date > end_date:
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha inicial debe ser anterior a la fecha final"
            )
        
        # Validar trigger si se proporciona
        valid_triggers = ["manual", "scheduled", "motion", "event", "api"]
        if trigger and trigger not in valid_triggers:
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
    except Exception as e:
        logger.error(f"Error obteniendo snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )