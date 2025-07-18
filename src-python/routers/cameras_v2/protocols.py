"""
Router para endpoints de gestión de protocolos de cámaras.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging

from api.dependencies import create_response
from api.models.camera_models import (
    ProtocolType,
    # Protocol management models
    ProtocolStatus,
    UpdateProtocolRequest,
    TestProtocolRequest,
    DiscoverProtocolsRequest,
    ProtocolDetailResponse,
    ProtocolListResponse,
    TestProtocolResponse,
    DiscoverProtocolsResponse
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
    tags=["protocols"],
    responses={404: {"description": "Cámara no encontrada"}}
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
                    protocol_id=protocol.get('protocol_id', 0),
                    protocol_type=protocol.get('protocol_type', 'unknown'),
                    port=protocol.get('port', 0),
                    is_enabled=protocol.get('is_enabled', False),
                    is_primary=protocol.get('is_primary', False),
                    is_verified=protocol.get('is_verified', False),
                    status=protocol.get('status', 'unknown'),
                    version=protocol.get('version'),
                    path=protocol.get('path'),
                    last_tested=protocol.get('last_tested'),
                    last_error=protocol.get('last_error'),
                    response_time_ms=protocol.get('response_time_ms'),
                    capabilities=protocol.get('capabilities'),
                    created_at=protocol.get('created_at'),
                    updated_at=protocol.get('updated_at')
                ))
            except Exception as e:
                logger.warning(f"Error procesando protocolo {protocol.get('protocol_id', 'unknown')}: {e}", exc_info=True)
                # Continuar con los demás protocolos
        
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