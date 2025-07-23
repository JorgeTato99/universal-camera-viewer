"""
Router para endpoints de conexión de cámaras.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import logging
import ipaddress

from api.dependencies import create_response
from api.dependencies.rate_limit import rate_limit, camera_operation_limit
from api.models.camera_models import (
    TestConnectionRequest,
    TestConnectionResponse,
    ProtocolType
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
    tags=["camera-connections"],
    responses={404: {"description": "Cámara no encontrada"}}
)


@router.post("/{camera_id}/connect")
@camera_operation_limit("connect")  # 5/minute - conexión es costosa
async def connect_camera(camera_id: str, background_tasks: BackgroundTasks):
    """
    Conectar a una cámara.
    
    Args:
        camera_id: ID de la cámara
        background_tasks: Tareas en background de FastAPI
        
    Returns:
        Estado de la conexión
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
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
        logger.warning(f"Cámara no encontrada para conectar: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio conectando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado conectando cámara {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
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
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
        
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
        logger.warning(f"Cámara no encontrada para desconectar: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio desconectando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado desconectando cámara {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/stream-url")
async def get_camera_stream_url(
    camera_id: str,
    stream_type: str = "main",
    protocol: Optional[ProtocolType] = None
):
    """
    Obtener la URL del stream de una cámara.
    
    Args:
        camera_id: ID de la cámara
        stream_type: Tipo de stream (main, sub, etc.)
        protocol: Protocolo específico a usar (RTSP, HTTP, etc.)
        
    Returns:
        URL del stream y metadatos relacionados
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
    
    # Validar stream_type
    valid_stream_types = ["main", "sub", "third"]
    if stream_type not in valid_stream_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de stream inválido. Debe ser uno de: {', '.join(valid_stream_types)}"
        )
        
    try:
        logger.info(f"Obteniendo URL de stream para cámara {camera_id}, tipo: {stream_type}")
        
        # Obtener información de la cámara
        camera = await camera_manager_service.get_camera(camera_id)
        
        if not camera.is_connected:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La cámara debe estar conectada para obtener la URL del stream"
            )
        
        # Obtener URL del stream basado en los endpoints descubiertos
        stream_url = None
        stream_protocol = protocol.value if protocol else "rtsp"
        
        # Buscar en endpoints descubiertos
        for endpoint_type, endpoint_data in camera.discovered_endpoints.items():
            if stream_type in endpoint_type and endpoint_data.get('verified', False):
                stream_url = endpoint_data['url']
                break
        
        # Si no hay endpoint descubierto, construir URL por defecto
        if not stream_url:
            # Usar información de conexión para construir URL RTSP
            username = camera.connection_config.username
            password = camera.connection_config.password
            ip = camera.connection_config.ip
            port = camera.connection_config.rtsp_port
            
            if username and password:
                stream_url = f"rtsp://{username}:{password}@{ip}:{port}/cam/realmonitor?channel=1&subtype=0"
            else:
                stream_url = f"rtsp://{ip}:{port}/cam/realmonitor?channel=1&subtype=0"
        
        return create_response(
            success=True,
            data={
                "camera_id": camera_id,
                "stream_url": stream_url,
                "stream_type": stream_type,
                "protocol": stream_protocol,
                "is_verified": bool(camera.discovered_endpoints.get(f"rtsp_{stream_type}", {}).get('verified', False))
            }
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo URL de stream para {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/test-connection")
@camera_operation_limit("test")  # 20/minute - test es más ligero
async def test_connection(request: TestConnectionRequest):
    """
    Probar conexión a una cámara sin guardarla.
    
    Args:
        request: Datos de conexión
        
    Returns:
        Resultado de la prueba
    """
    # Validar datos de entrada
    if not request.ip:
        logger.warning("IP no proporcionada para prueba de conexión")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La dirección IP es obligatoria"
        )
    
    # Validar formato de IP
    try:
        import ipaddress
        ipaddress.ip_address(request.ip)
    except ValueError:
        logger.warning(f"IP inválida proporcionada: {request.ip}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dirección IP inválida"
        )
    
    try:
        logger.info(f"Probando conexión a {request.ip} - protocolo: {request.protocol}, marca: {request.brand}")
        
        connection_data = {
            'ip': request.ip,
            'username': request.username or '',
            'password': request.password or '',
            'brand': request.brand or 'Generic'
        }
        
        # Asignar puerto según protocolo
        if request.port:
            if request.protocol == ProtocolType.RTSP:
                connection_data['rtsp_port'] = request.port
            elif request.protocol == ProtocolType.ONVIF:
                connection_data['onvif_port'] = request.port
            elif request.protocol == ProtocolType.HTTP:
                connection_data['http_port'] = request.port
            elif request.protocol == ProtocolType.HTTPS:
                connection_data['https_port'] = request.port
            else:
                logger.warning(f"Protocolo no reconocido: {request.protocol}")
        
        success, message = await camera_manager_service.test_camera_connection(connection_data)
        
        if success:
            logger.info(f"Conexión exitosa a {request.ip}: {message}")
        else:
            logger.warning(f"Conexión fallida a {request.ip}: {message}")
        
        response_data = TestConnectionResponse(
            success=success,
            message=message
        )
        
        return create_response(
            success=True,
            data=response_data.dict()
        )
        
    except ServiceError as e:
        logger.error(f"Error de servicio probando conexión a {request.ip}: {e}")
        response_data = TestConnectionResponse(
            success=False,
            message="Servicio temporalmente no disponible"
        )
        
        return create_response(
            success=False,
            error="Servicio temporalmente no disponible",
            data=response_data.dict()
        )
    except ValueError as e:
        logger.error(f"Error de validación probando conexión: {e}")
        response_data = TestConnectionResponse(
            success=False,
            message=f"Error de validación: {str(e)}"
        )
        
        return create_response(
            success=False,
            error=str(e),
            data=response_data.dict()
        )
    except Exception as e:
        logger.error(f"Error inesperado probando conexión a {request.ip}: {e}", exc_info=True)
        response_data = TestConnectionResponse(
            success=False,
            message="Error interno al probar conexión"
        )
        
        return create_response(
            success=False,
            error="Error interno del servidor",
            data=response_data.dict()
        )