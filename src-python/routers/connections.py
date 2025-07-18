"""
Router para endpoints de conexión de cámaras.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
import logging
import ipaddress

from api.dependencies import create_response
from api.models.camera_models import ProtocolType
from api.schemas.requests.connection_requests import (
    TestConnectionRequest,
    DisconnectRequest,
    ReconnectRequest,
    BatchConnectionRequest
)
from api.schemas.responses.connection_responses import (
    ConnectionStatusResponse,
    TestConnectionResponse,
    ConnectionOperationResponse,
    BatchConnectionResponse,
    ConnectionMetricsResponse,
    ActiveConnectionsResponse
)
from api.dependencies.validation_deps import validate_camera_exists
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


@router.post("/{camera_id}/connect", response_model=ConnectionOperationResponse)
async def connect_camera(
    background_tasks: BackgroundTasks,
    camera_id: str = Depends(validate_camera_exists)
):
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
        
        return ConnectionOperationResponse(
            success=True,
            camera_id=camera_id,
            operation="connect",
            message="Conexión iniciada"
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


@router.post("/{camera_id}/disconnect", response_model=ConnectionOperationResponse)
async def disconnect_camera(
    request: DisconnectRequest = DisconnectRequest(),
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Desconectar una cámara.
    
    Args:
        camera_id: ID de la cámara
        request: Parámetros de desconexión
        
    Returns:
        Estado de la desconexión
    """
    try:
        logger.info(f"Desconectando cámara: {camera_id}, force={request.force}")
        
        success = await camera_manager_service.disconnect_camera(camera_id)
        
        if success:
            logger.info(f"Cámara {camera_id} desconectada exitosamente")
        else:
            logger.warning(f"No se pudo desconectar la cámara {camera_id}")
        
        return ConnectionOperationResponse(
            success=success,
            camera_id=camera_id,
            operation="disconnect",
            message="Cámara desconectada" if success else "No se pudo desconectar la cámara"
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


@router.post("/test-connection", response_model=TestConnectionResponse)
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
        
        return TestConnectionResponse(
            success=success,
            camera_id="test-connection",  # ID temporal para prueba
            protocol=request.protocol.value if hasattr(request, 'protocol') else "RTSP",
            response_time_ms=None,
            error=None if success else message,
            details={
                "ip": request.ip,
                "brand": request.brand or "Generic",
                "message": message
            }
        )
        
    except ServiceError as e:
        logger.error(f"Error de servicio probando conexión a {request.ip}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except ValueError as e:
        logger.error(f"Error de validación probando conexión: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado probando conexión a {request.ip}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/connected", response_model=ActiveConnectionsResponse)
async def get_connected_cameras():
    """
    Obtener lista de cámaras actualmente conectadas.
    
    Returns:
        Lista de IDs de cámaras conectadas con información de conexión
    """
    try:
        logger.info("Obteniendo lista de cámaras conectadas")
        
        # Obtener todas las cámaras
        cameras = await camera_manager_service.get_all_cameras()
        
        # Filtrar solo las conectadas
        connected_cameras = []
        for camera in cameras:
            if camera.is_connected:
                connected_cameras.append({
                    "camera_id": camera.camera_id,
                    "display_name": camera.display_name,
                    "ip_address": camera.connection_config.ip,
                    "protocol": camera.connection_config.primary_protocol,
                    "connected_at": getattr(camera, "connected_at", None),
                    "streaming": camera.is_streaming
                })
        
        logger.info(f"Encontradas {len(connected_cameras)} cámaras conectadas")
        
        # Convertir a ConnectionStatusResponse
        connections = []
        for cam in connected_cameras:
            connections.append(ConnectionStatusResponse(
                camera_id=cam["camera_id"],
                is_connected=True,
                connection_time=cam.get("connected_at"),
                protocol=cam["protocol"],
                stream_active=cam["streaming"],
                error=None
            ))
        
        return ActiveConnectionsResponse(
            total_active=len(connections),
            connections=connections
        )
        
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo cámaras conectadas: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error obteniendo cámaras conectadas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/disconnect-all")
async def disconnect_all_cameras():
    """
    Desconectar todas las cámaras activas.
    
    Returns:
        Resultado de la operación
    """
    try:
        logger.warning("Desconectando todas las cámaras")
        
        # Obtener cámaras conectadas
        cameras = await camera_manager_service.get_all_cameras()
        connected_cameras = [c for c in cameras if c.is_connected]
        
        disconnected_count = 0
        failed_count = 0
        
        for camera in connected_cameras:
            try:
                success = await camera_manager_service.disconnect_camera(camera.camera_id)
                if success:
                    disconnected_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error desconectando cámara {camera.camera_id}: {e}")
                failed_count += 1
        
        logger.info(f"Desconectadas {disconnected_count} cámaras, {failed_count} fallos")
        
        return create_response(
            success=failed_count == 0,
            data={
                "total_cameras": len(connected_cameras),
                "disconnected": disconnected_count,
                "failed": failed_count,
                "message": f"Se desconectaron {disconnected_count} de {len(connected_cameras)} cámaras"
            }
        )
        
    except ServiceError as e:
        logger.error(f"Error de servicio desconectando todas las cámaras: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error desconectando todas las cámaras: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/connection-metrics", response_model=ConnectionMetricsResponse)
async def get_connection_metrics(camera_id: str = Depends(validate_camera_exists)):
    """
    Obtener métricas de conexión de una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Métricas detalladas de conexión
    """
    try:
        logger.info(f"Obteniendo métricas de conexión para cámara {camera_id}")
        
        camera = await camera_manager_service.get_camera(camera_id)
        
        # Calcular tiempo activo si está conectada
        uptime_seconds = None
        if camera.is_connected and hasattr(camera, 'last_connection_time'):
            from datetime import datetime
            uptime_seconds = int((datetime.utcnow() - camera.last_connection_time).total_seconds())
        
        return ConnectionMetricsResponse(
            camera_id=camera_id,
            total_connections=getattr(camera, "total_connections", 0),
            successful_connections=getattr(camera, "successful_connections", 0),
            failed_connections=getattr(camera, "failed_connections", 0),
            average_connection_time_ms=getattr(camera, "average_connection_time_ms", None),
            last_connection_attempt=getattr(camera, "last_connection_attempt", None),
            last_successful_connection=getattr(camera, "last_connection_time", None),
            uptime_seconds=uptime_seconds
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo métricas de conexión: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error obteniendo métricas de conexión para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/connection-status", response_model=ConnectionStatusResponse)
async def get_connection_status(camera_id: str = Depends(validate_camera_exists)):
    """
    Obtener estado detallado de conexión de una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Estado detallado de la conexión
    """
    try:
        logger.info(f"Obteniendo estado de conexión para cámara {camera_id}")
        
        camera = await camera_manager_service.get_camera(camera_id)
        
        # Obtener último error si existe
        last_error = None
        if not camera.is_connected and hasattr(camera, 'last_error'):
            last_error = str(camera.last_error)
        
        return ConnectionStatusResponse(
            camera_id=camera_id,
            is_connected=camera.is_connected,
            connection_time=getattr(camera, "last_connection_time", None),
            protocol=camera.connection_config.primary_protocol if camera.is_connected else None,
            stream_active=camera.is_streaming,
            error=last_error
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo estado de conexión: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error obteniendo estado de conexión para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/batch-connect", response_model=BatchConnectionResponse)
async def batch_connect_cameras(
    request: BatchConnectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Conectar múltiples cámaras en paralelo.
    
    Args:
        request: Request con lista de cámaras y operación
        background_tasks: Tareas en background
        
    Returns:
        Estado de la operación batch
    """
    # La validación ya se hace en el schema
    
    try:
        logger.info(f"Iniciando operación batch '{request.operation}' para {len(request.camera_ids)} cámaras")
        
        results = []
        successful = 0
        failed = 0
        
        for camera_id in request.camera_ids:
            try:
                # Verificar que la cámara existe
                camera = await camera_manager_service.get_camera(camera_id)
                
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
                else:
                    success = False
                    message = f"Operación '{request.operation}' no implementada"
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                results.append(ConnectionOperationResponse(
                    success=success,
                    camera_id=camera_id,
                    operation=request.operation,
                    message=message
                ))
                
            except CameraNotFoundError:
                failed += 1
                results.append(ConnectionOperationResponse(
                    success=False,
                    camera_id=camera_id,
                    operation=request.operation,
                    message=f"Cámara {camera_id} no encontrada"
                ))
            except Exception as e:
                failed += 1
                logger.error(f"Error en operación {request.operation} para cámara {camera_id}: {e}")
                results.append(ConnectionOperationResponse(
                    success=False,
                    camera_id=camera_id,
                    operation=request.operation,
                    message=str(e)
                ))
        
        return BatchConnectionResponse(
            total_requested=len(request.camera_ids),
            successful=successful,
            failed=failed,
            results=results
        )
        
    except ServiceError as e:
        logger.error(f"Error de servicio en conexión batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error en conexión batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )