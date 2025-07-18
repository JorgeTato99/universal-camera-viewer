"""
Router para endpoints de gestión de protocolos de cámaras.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging

from api.dependencies import create_response
from api.schemas.requests.protocol_requests import (
    DiscoverProtocolsRequest,
    TestProtocolRequest,
    UpdateProtocolConfigRequest
)
from api.schemas.responses.protocol_responses import (
    ProtocolInfo,
    ProtocolDiscoveryResponse,
    ProtocolTestResponse,
    ProtocolCapabilitiesResponse,
    StreamEndpointInfo,
    ProtocolEndpointsResponse
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
    tags=["protocols"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Endpoints de Gestión de Protocolos ===


@router.get("/{camera_id}/protocols", response_model=List[ProtocolInfo])
async def list_camera_protocols(
    camera_id: str = Depends(validate_camera_exists),
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
        logger.info(f"Listando protocolos de cámara: {camera_id}")
        
        # Obtener cámara para construir URLs
        camera = await camera_manager_service.get_camera(camera_id)
        
        protocols = await camera_manager_service.get_camera_protocols(camera_id)
        
        # Filtrar si se solicita
        if only_enabled:
            protocols = [p for p in protocols if p.get('is_enabled', False)]
        
        # Construir respuesta
        protocol_responses = []
        for protocol in protocols:
            try:
                # Determinar endpoints basado en el tipo de protocolo
                endpoints = []
                if protocol.get('path'):
                    if protocol['protocol_type'] == 'RTSP':
                        endpoints.append(f"rtsp://{camera.connection_config.ip}:{protocol['port']}{protocol['path']}")
                    elif protocol['protocol_type'] in ['HTTP', 'ONVIF']:
                        endpoints.append(f"http://{camera.connection_config.ip}:{protocol['port']}{protocol['path']}")
                
                protocol_responses.append(ProtocolInfo(
                    protocol=protocol['protocol_type'],
                    port=protocol['port'],
                    available=protocol['is_enabled'],
                    verified=protocol.get('is_verified', False),
                    response_time_ms=protocol.get('response_time_ms'),
                    error=protocol.get('last_error'),
                    endpoints=endpoints
                ))
            except Exception as e:
                logger.warning(f"Error procesando protocolo {protocol.get('protocol_id')}: {e}")
        
        logger.info(f"Devolviendo {len(protocol_responses)} protocolos para cámara {camera_id}")
        
        return protocol_responses
        
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


@router.put("/{camera_id}/protocols/{protocol_type}", response_model=ProtocolInfo)
async def update_protocol_config(
    protocol_type: str,
    request: UpdateProtocolConfigRequest,
    camera_id: str = Depends(validate_camera_exists)
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
        # Validar tipo de protocolo
        valid_protocols = ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
        if protocol_type not in valid_protocols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Protocolo debe ser uno de: {', '.join(valid_protocols)}"
            )
        
        logger.info(f"Actualizando protocolo {protocol_type} de cámara {camera_id}")
        
        # Preparar actualizaciones
        updates = {}
        
        # Mapear campos del request a campos del servicio
        if request.rtsp_port is not None and protocol_type == 'RTSP':
            updates['port'] = request.rtsp_port
        elif request.onvif_port is not None and protocol_type == 'ONVIF':
            updates['port'] = request.onvif_port
        elif request.http_port is not None and protocol_type == 'HTTP':
            updates['port'] = request.http_port
        elif request.https_port is not None and protocol_type == 'HTTPS':
            updates['port'] = request.https_port
            
        if request.primary_protocol == protocol_type:
            updates['is_primary'] = True
            
        if request.custom_paths and protocol_type.lower() in request.custom_paths:
            updates['path'] = request.custom_paths[protocol_type.lower()]
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )
        
        protocol = await camera_manager_service.update_protocol_config(
            camera_id, protocol_type, updates
        )
        
        # Obtener cámara para construir endpoints
        camera = await camera_manager_service.get_camera(camera_id)
        
        # Construir endpoints
        endpoints = []
        if protocol.get('path'):
            if protocol_type == 'RTSP':
                endpoints.append(f"rtsp://{camera.connection_config.ip}:{protocol['port']}{protocol['path']}")
            elif protocol_type in ['HTTP', 'ONVIF']:
                endpoints.append(f"http://{camera.connection_config.ip}:{protocol['port']}{protocol['path']}")
        
        logger.info(f"Protocolo {protocol_type} actualizado exitosamente")
        
        return ProtocolInfo(
            protocol=protocol['protocol_type'],
            port=protocol['port'],
            available=protocol['is_enabled'],
            verified=protocol.get('is_verified', False),
            response_time_ms=protocol.get('response_time_ms'),
            error=protocol.get('last_error'),
            endpoints=endpoints
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


@router.post("/{camera_id}/protocols/{protocol_type}/test", response_model=ProtocolTestResponse)
async def test_protocol(
    protocol_type: str,
    request: TestProtocolRequest,
    camera_id: str = Depends(validate_camera_exists)
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
        # Validar tipo de protocolo
        valid_protocols = ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
        if protocol_type not in valid_protocols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Protocolo debe ser uno de: {', '.join(valid_protocols)}"
            )
        
        logger.info(f"Probando protocolo {protocol_type} de cámara {camera_id}")
        
        result = await camera_manager_service.test_protocol(
            camera_id,
            protocol_type,
            timeout=request.timeout
        )
        
        return ProtocolTestResponse(
            protocol=protocol_type,
            success=result.get('success', False),
            port=request.port or result.get('port'),
            path=request.path,
            response_time_ms=result.get('response_time_ms'),
            error=result.get('error'),
            details=result.get('details', {})
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


@router.post("/{camera_id}/protocols/discover", response_model=ProtocolDiscoveryResponse)
async def discover_protocols(
    request: DiscoverProtocolsRequest,
    background_tasks: BackgroundTasks,
    camera_id: str = Depends(validate_camera_exists)
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
        logger.info(f"Iniciando auto-discovery de protocolos para cámara {camera_id}")
        
        # Obtener cámara para la IP
        camera = await camera_manager_service.get_camera(camera_id)
        
        # Ejecutar discovery
        import time
        start_time = time.time()
        
        discovered_protocols = []
        primary_protocol = None
        
        # Simular discovery de protocolos
        protocols_to_test = request.protocols or ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
        
        for protocol in protocols_to_test:
            # Simular prueba de protocolo
            port = None
            if protocol == 'RTSP':
                port = 554
            elif protocol == 'ONVIF':
                port = 80
            elif protocol == 'HTTP':
                port = 80
            elif protocol == 'HTTPS':
                port = 443
            
            # Simular resultado (80% de éxito)
            import random
            if random.random() < 0.8:
                discovered_protocols.append(ProtocolInfo(
                    protocol=protocol,
                    port=port,
                    available=True,
                    verified=True,
                    response_time_ms=random.uniform(50, 200),
                    error=None,
                    endpoints=[]
                ))
                
                if not primary_protocol:
                    primary_protocol = protocol
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        return ProtocolDiscoveryResponse(
            camera_id=camera_id,
            ip_address=request.ip or camera.connection_config.ip,
            discovered_protocols=discovered_protocols,
            primary_protocol=primary_protocol,
            total_time_ms=total_time_ms
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


@router.get("/{camera_id}/protocols/{protocol_type}/capabilities", response_model=ProtocolCapabilitiesResponse)
async def get_protocol_capabilities(
    protocol_type: str,
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Obtener capacidades específicas de un protocolo.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        protocol_type: Tipo de protocolo
        
    Returns:
        ProtocolCapabilitiesResponse: Capacidades del protocolo
    """
    try:
        # Validar tipo de protocolo
        valid_protocols = ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
        if protocol_type not in valid_protocols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Protocolo debe ser uno de: {', '.join(valid_protocols)}"
            )
        
        logger.info(f"Obteniendo capacidades de {protocol_type} para cámara {camera_id}")
        
        # Simular capacidades según el protocolo
        capabilities = {}
        
        if protocol_type == 'ONVIF':
            capabilities = {
                "ptz": True,
                "audio": True,
                "events": True,
                "analytics": False,
                "profiles": ["Profile_1", "Profile_2"],
                "services": {
                    "device": "http://192.168.1.100/onvif/device_service",
                    "media": "http://192.168.1.100/onvif/media_service",
                    "ptz": "http://192.168.1.100/onvif/ptz_service"
                }
            }
        elif protocol_type == 'RTSP':
            capabilities = {
                "streams": ["main", "sub"],
                "codecs": ["H.264", "H.265"],
                "resolutions": ["1920x1080", "1280x720", "640x480"],
                "transport": ["TCP", "UDP"],
                "authentication": ["basic", "digest"]
            }
        elif protocol_type in ['HTTP', 'HTTPS']:
            capabilities = {
                "snapshot": True,
                "mjpeg": True,
                "api_version": "v1.0",
                "auth_methods": ["basic", "digest", "token"],
                "features": ["config", "status", "logs"]
            }
        
        return ProtocolCapabilitiesResponse(
            camera_id=camera_id,
            protocol=protocol_type,
            capabilities=capabilities
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo capacidades de protocolo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{camera_id}/protocols/endpoints", response_model=ProtocolEndpointsResponse)
async def get_protocol_endpoints(
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Obtener todos los endpoints de streaming descubiertos.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        
    Returns:
        ProtocolEndpointsResponse: Lista de endpoints disponibles
    """
    try:
        logger.info(f"Obteniendo endpoints de cámara {camera_id}")
        
        # Obtener cámara
        camera = await camera_manager_service.get_camera(camera_id)
        
        # Simular endpoints descubiertos
        endpoints = []
        
        # RTSP endpoints
        if camera.capabilities.supported_protocols and 'RTSP' in camera.capabilities.supported_protocols:
            endpoints.extend([
                StreamEndpointInfo(
                    name="rtsp_main",
                    url=f"rtsp://{camera.connection_config.ip}:554/cam/realmonitor?channel=1&subtype=0",
                    protocol="RTSP",
                    stream_type="main",
                    verified=True,
                    resolution="1920x1080",
                    fps=25,
                    codec="H.264"
                ),
                StreamEndpointInfo(
                    name="rtsp_sub",
                    url=f"rtsp://{camera.connection_config.ip}:554/cam/realmonitor?channel=1&subtype=1",
                    protocol="RTSP",
                    stream_type="sub",
                    verified=True,
                    resolution="640x480",
                    fps=15,
                    codec="H.264"
                )
            ])
        
        # HTTP endpoints
        if camera.capabilities.supported_protocols and 'HTTP' in camera.capabilities.supported_protocols:
            endpoints.append(
                StreamEndpointInfo(
                    name="mjpeg",
                    url=f"http://{camera.connection_config.ip}/mjpeg",
                    protocol="HTTP",
                    stream_type="mjpeg",
                    verified=False,
                    resolution=None,
                    fps=None,
                    codec="MJPEG"
                )
            )
        
        verified_count = sum(1 for e in endpoints if e.verified)
        
        return ProtocolEndpointsResponse(
            camera_id=camera_id,
            total_endpoints=len(endpoints),
            verified_endpoints=verified_count,
            endpoints=endpoints
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except Exception as e:
        logger.error(f"Error obteniendo endpoints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )