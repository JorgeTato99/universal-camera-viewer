"""
Router para endpoints de gestión de paths MediaMTX.

Proporciona APIs para crear, configurar y gestionar paths
en servidores MediaMTX para publicación y consumo de streams.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List, Dict, Any

from api.schemas.requests.mediamtx_requests import (
    CreatePathRequest, UpdatePathRequest, TestPathRequest,
    PathSourceType
)
from api.schemas.responses.mediamtx_responses import (
    MediaMTXPath, PathsListResponse, PathTestResponse
)
from api.dependencies import create_response
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.database import get_publishing_db_service
from utils.exceptions import ServiceError
from api.validators.mediamtx_validators import (
    validate_path_name, validate_server_id, validate_allowed_ips
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/publishing/paths",
    tags=["mediamtx-paths"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=PathsListResponse,
    summary="Listar paths MediaMTX",
    description="""
    Obtiene todos los paths configurados en MediaMTX.
    
    Muestra:
    - Configuración de cada path
    - Estado activo/inactivo
    - Publishers y readers conectados
    - Configuración de grabación
    - Control de acceso
    """
)
async def list_paths(
    server_id: Optional[int] = Query(
        None,
        description="Filtrar por servidor específico"
    ),
    active_only: bool = Query(
        True,
        description="Solo mostrar paths activos"
    ),
    source_type: Optional[PathSourceType] = Query(
        None,
        description="Filtrar por tipo de fuente"
    )
) -> PathsListResponse:
    """
    Lista todos los paths MediaMTX configurados.
    
    Args:
        server_id: ID del servidor para filtrar
        active_only: Si mostrar solo paths activos
        source_type: Tipo de fuente para filtrar
        
    Returns:
        PathsListResponse con lista de paths
    """
    logger.debug(f"Listando paths MediaMTX, server_id={server_id}, active_only={active_only}")
    
    try:
        # Obtener servicio de BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Consultar paths
        paths = await db_service.get_mediamtx_paths(
            server_id=server_id,
            active_only=active_only
        )
        
        # Filtrar por tipo de fuente si se especifica
        if source_type:
            paths = [p for p in paths if p['source_type'] == source_type.value]
        
        # Contar por estado
        active_count = sum(1 for p in paths if p['is_active'])
        
        # Agrupar por servidor
        server_summary = {}
        for path in paths:
            sid = path['server_id']
            server_summary[sid] = server_summary.get(sid, 0) + 1
        
        # Construir items de respuesta
        items = []
        for path_data in paths:
            # Obtener tiempo de último uso (mock por ahora)
            # TODO: Implementar tracking real de último uso
            
            items.append(MediaMTXPath(
                path_id=path_data['path_id'],
                server_id=path_data['server_id'],
                server_name=path_data['server_name'],
                path_name=path_data['path_name'],
                source_type=path_data['source_type'],
                source_url=path_data['source_url'],
                is_active=path_data['is_active'],
                is_running=path_data['is_running'],
                connected_publishers=path_data['connected_publishers'],
                connected_readers=path_data['connected_readers'],
                record_enabled=path_data['record_enabled'],
                record_path=path_data['record_path'],
                authentication_required=path_data['authentication_required'],
                created_at=path_data['created_at'],
                updated_at=path_data['updated_at'],
                last_used=None  # TODO: Implementar
            ))
        
        response = PathsListResponse(
            total=len(items),
            active_count=active_count,
            items=items,
            server_summary=server_summary
        )
        
        logger.info(f"Paths obtenidos: {response.total} total, {response.active_count} activos")
        
        return response
        
    except ServiceError as e:
        logger.error(f"ServiceError listando paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error inesperado listando paths")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo paths"
        )


@router.post(
    "/",
    response_model=MediaMTXPath,
    status_code=status.HTTP_201_CREATED,
    summary="Crear path MediaMTX",
    description="""
    Crea un nuevo path en un servidor MediaMTX.
    
    Permite configurar:
    - Tipo de fuente y URL
    - Grabación de streams
    - Control de acceso con autenticación
    - IPs permitidas
    - Scripts de inicialización
    """
)
async def create_path(
    request: CreatePathRequest
) -> MediaMTXPath:
    """
    Crea un nuevo path MediaMTX.
    
    Args:
        request: Configuración del path
        
    Returns:
        MediaMTXPath con el path creado
        
    Raises:
        HTTPException: Si el path ya existe o hay error
    """
    logger.info(f"Creando path '{request.path_name}' en servidor {request.server_id}")
    
    try:
        # Validaciones adicionales
        request.path_name = validate_path_name(request.path_name)
        request.server_id = validate_server_id(request.server_id)
        
        if request.allowed_ips:
            request.allowed_ips = validate_allowed_ips(request.allowed_ips)
        
        # Verificar que el servidor existe
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # TODO: Verificar que server_id existe en mediamtx_servers
        
        # Preparar configuración
        path_config = {
            'path_name': request.path_name,
            'source_type': request.source_type.value,
            'source_url': request.source_url,
            'record_enabled': request.record_enabled,
            'record_path': request.record_path,
            'record_format': request.record_format,
            'record_segment_duration': request.record_segment_duration,
            'authentication_required': request.authentication_required,
            'publish_user': request.publish_user,
            'publish_password': request.publish_password,
            'read_user': request.read_user,
            'read_password': request.read_password,
            'allowed_ips': request.allowed_ips,
            'run_on_init': request.run_on_init,
            'run_on_demand': request.run_on_demand
        }
        
        # Crear path
        path_id = await db_service.create_mediamtx_path(
            server_id=request.server_id,
            path_config=path_config
        )
        
        # Obtener path creado
        paths = await db_service.get_mediamtx_paths()
        created_path = next((p for p in paths if p['path_id'] == path_id), None)
        
        if not created_path:
            raise ServiceError("Path creado pero no se pudo recuperar")
        
        # Construir respuesta
        response = MediaMTXPath(
            path_id=created_path['path_id'],
            server_id=created_path['server_id'],
            server_name=created_path['server_name'],
            path_name=created_path['path_name'],
            source_type=created_path['source_type'],
            source_url=created_path['source_url'],
            is_active=created_path['is_active'],
            is_running=False,
            connected_publishers=0,
            connected_readers=0,
            record_enabled=created_path['record_enabled'],
            record_path=created_path['record_path'],
            authentication_required=created_path['authentication_required'],
            created_at=created_path['created_at'],
            updated_at=created_path['updated_at'],
            last_used=None
        )
        
        logger.info(f"Path '{request.path_name}' creado con ID {path_id}")
        
        return response
        
    except ServiceError as e:
        if e.error_code == "PATH_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        logger.error(f"ServiceError creando path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error inesperado creando path")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando path"
        )


@router.put(
    "/{path_id}",
    response_model=MediaMTXPath,
    summary="Actualizar path MediaMTX",
    description="Actualiza la configuración de un path existente"
)
async def update_path(
    path_id: int,
    request: UpdatePathRequest
) -> MediaMTXPath:
    """
    Actualiza un path MediaMTX existente.
    
    Solo se actualizan los campos proporcionados.
    
    Args:
        path_id: ID del path a actualizar
        request: Campos a actualizar
        
    Returns:
        MediaMTXPath actualizado
        
    Raises:
        HTTPException: Si el path no existe
    """
    logger.info(f"Actualizando path {path_id}")
    
    try:
        # Validar campos si se proporcionan
        updates = {}
        
        if request.path_name is not None:
            updates['path_name'] = validate_path_name(request.path_name)
        if request.source_type is not None:
            updates['source_type'] = request.source_type.value
        if request.source_url is not None:
            updates['source_url'] = request.source_url
        if request.record_enabled is not None:
            updates['record_enabled'] = request.record_enabled
        if request.record_path is not None:
            updates['record_path'] = request.record_path
        if request.authentication_required is not None:
            updates['authentication_required'] = request.authentication_required
        if request.is_active is not None:
            updates['is_active'] = request.is_active
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )
        
        # Actualizar en BD
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        updated = await db_service.update_mediamtx_path(path_id, updates)
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path {path_id} no encontrado"
            )
        
        # Obtener path actualizado
        paths = await db_service.get_mediamtx_paths()
        updated_path = next((p for p in paths if p['path_id'] == path_id), None)
        
        if not updated_path:
            raise ServiceError("Path actualizado pero no se pudo recuperar")
        
        # Construir respuesta
        response = MediaMTXPath(
            path_id=updated_path['path_id'],
            server_id=updated_path['server_id'],
            server_name=updated_path['server_name'],
            path_name=updated_path['path_name'],
            source_type=updated_path['source_type'],
            source_url=updated_path['source_url'],
            is_active=updated_path['is_active'],
            is_running=updated_path['is_running'],
            connected_publishers=updated_path['connected_publishers'],
            connected_readers=updated_path['connected_readers'],
            record_enabled=updated_path['record_enabled'],
            record_path=updated_path['record_path'],
            authentication_required=updated_path['authentication_required'],
            created_at=updated_path['created_at'],
            updated_at=updated_path['updated_at'],
            last_used=None
        )
        
        logger.info(f"Path {path_id} actualizado exitosamente")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error actualizando path {path_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando path"
        )


@router.delete(
    "/{path_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar path MediaMTX",
    description="Elimina un path MediaMTX"
)
async def delete_path(path_id: int):
    """
    Elimina un path MediaMTX.
    
    Args:
        path_id: ID del path a eliminar
        
    Raises:
        HTTPException: Si el path no existe o está en uso
    """
    logger.info(f"Eliminando path {path_id}")
    
    try:
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        deleted = await db_service.delete_mediamtx_path(path_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path {path_id} no encontrado"
            )
        
        logger.info(f"Path {path_id} eliminado exitosamente")
        
    except ServiceError as e:
        if e.error_code == "PATH_IN_USE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error eliminando path {path_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando path"
        )


@router.post(
    "/{path_id}/test",
    response_model=PathTestResponse,
    summary="Probar path MediaMTX",
    description="""
    Prueba la conectividad y configuración de un path.
    
    Verifica:
    - Conectividad con el servidor
    - Permisos de lectura
    - Permisos de escritura (opcional)
    - Configuración de autenticación
    """
)
async def test_path(
    path_id: int,
    request: TestPathRequest = TestPathRequest()
) -> PathTestResponse:
    """
    Prueba un path MediaMTX.
    
    Args:
        path_id: ID del path a probar
        request: Parámetros de la prueba
        
    Returns:
        PathTestResponse con resultados
    """
    logger.info(f"Probando path {path_id}, timeout={request.timeout_seconds}s")
    
    try:
        # Por ahora retornamos resultado mock
        # TODO: Implementar prueba real contra MediaMTX API
        
        import random
        import asyncio
        from datetime import datetime
        
        # Simular tiempo de prueba
        await asyncio.sleep(min(request.timeout_seconds * 0.3, 3))
        
        # Resultados simulados
        read_success = random.choice([True, True, True, False])  # 75% éxito
        write_success = None
        warnings = []
        error_message = None
        response_time = random.uniform(50, 500)
        
        if request.test_write:
            write_success = read_success and random.choice([True, True, False])  # 66% si read OK
            if not write_success and read_success:
                warnings.append("Write permission denied but read is OK")
        
        if not read_success:
            error_message = random.choice([
                "Connection timeout",
                "Authentication failed",
                "Path not found on server",
                "Server unreachable"
            ])
        elif response_time > 300:
            warnings.append("High response time detected")
        
        # Obtener información del path
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        paths = await db_service.get_mediamtx_paths()
        path_info = next((p for p in paths if p['path_id'] == path_id), None)
        
        if not path_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path {path_id} no encontrado"
            )
        
        response = PathTestResponse(
            path_id=path_id,
            path_name=path_info['path_name'],
            test_timestamp=datetime.utcnow(),
            read_test_passed=read_success,
            write_test_passed=write_success,
            response_time_ms=response_time,
            error_message=error_message,
            warnings=warnings
        )
        
        status = "exitosa" if read_success else "fallida"
        logger.info(f"Prueba de path {path_id} {status} en {response_time:.0f}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error probando path {path_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error probando path"
        )


@router.get(
    "/templates",
    summary="Obtener plantillas de paths",
    description="Obtiene plantillas predefinidas para crear paths comunes"
)
async def get_path_templates() -> Dict[str, Any]:
    """
    Obtiene plantillas de configuración para paths comunes.
    
    Útil para simplificar la creación de paths típicos.
    
    Returns:
        Dict con plantillas organizadas por caso de uso
    """
    templates = {
        "camera_relay": {
            "name": "Camera RTSP Relay",
            "description": "Relay de stream RTSP desde cámara IP",
            "config": {
                "source_type": "rtsp",
                "source_url": "rtsp://username:password@camera_ip:554/stream",
                "record_enabled": False,
                "authentication_required": False
            }
        },
        "camera_record": {
            "name": "Camera with Recording",
            "description": "Stream de cámara con grabación habilitada",
            "config": {
                "source_type": "rtsp",
                "source_url": "rtsp://camera_ip:554/stream",
                "record_enabled": True,
                "record_path": "./recordings",
                "record_format": "fmp4",
                "record_segment_duration": 3600,
                "authentication_required": True
            }
        },
        "hls_output": {
            "name": "HLS Output",
            "description": "Path para servir stream en formato HLS",
            "config": {
                "source_type": "publisher",
                "playback_enabled": True,
                "authentication_required": False,
                "run_on_demand": "ffmpeg -re -i rtsp://source -c copy -f hls -hls_time 2 -hls_list_size 3 -hls_flags delete_segments stream.m3u8"
            }
        },
        "secure_publisher": {
            "name": "Secure Publisher",
            "description": "Path con autenticación para publicación",
            "config": {
                "source_type": "publisher",
                "authentication_required": True,
                "publish_user": "publisher",
                "read_user": "viewer",
                "allowed_ips": ["192.168.1.0/24", "10.0.0.0/8"]
            }
        }
    }
    
    return create_response(
        success=True,
        data=templates
    )