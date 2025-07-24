"""
Router API para gestión de servidores MediaMTX remotos.

Expone endpoints REST para operaciones CRUD de servidores MediaMTX,
incluyendo autenticación, pruebas de conexión y obtención de estado.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas.mediamtx_server_schemas import (
    MediaMTXServerCreate,
    MediaMTXServerUpdate,
    MediaMTXServerResponse,
    MediaMTXServerListResponse,
    MediaMTXServerStatus,
    MediaMTXServerTestResult
)
from presenters.mediamtx_servers_presenter import (
    MediaMTXServersPresenter,
    get_mediamtx_servers_presenter
)
from services.logging_service import get_secure_logger
from utils.exceptions import ValidationError, ServiceError


logger = get_secure_logger("api.routers.mediamtx_servers")


# Crear router con prefijo y tags
router = APIRouter(
    prefix="/api/mediamtx/servers",
    tags=["MediaMTX Servers"],
    responses={
        400: {"description": "Bad Request - Datos inválidos"},
        404: {"description": "Not Found - Servidor no encontrado"},
        500: {"description": "Internal Server Error"}
    }
)


@router.get("/", response_model=MediaMTXServerListResponse)
async def list_servers(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    include_auth: bool = Query(True, description="Incluir estado de autenticación"),
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> MediaMTXServerListResponse:
    """
    Lista todos los servidores MediaMTX configurados.
    
    Retorna una lista paginada de servidores con información básica
    y opcionalmente el estado de autenticación.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        result = await presenter.get_servers(
            page=page,
            page_size=page_size,
            include_auth_status=include_auth
        )
        
        logger.info(f"Listando servidores - página {page}/{(result['total'] + page_size - 1) // page_size}")
        
        return MediaMTXServerListResponse(**result)
        
    except Exception as e:
        logger.error(f"Error listando servidores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servidores: {str(e)}"
        )


@router.post("/", response_model=MediaMTXServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server: MediaMTXServerCreate,
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> MediaMTXServerResponse:
    """
    Crea un nuevo servidor MediaMTX.
    
    Valida los datos del servidor y lo registra en el sistema.
    Las credenciales se almacenan de forma segura encriptadas.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        logger.info(f"Creando servidor: {server.server_name}")
        
        # Crear servidor
        result = await presenter.create_server(server.model_dump())
        
        # TODO: Convertir resultado a MediaMTXServerResponse cuando se implemente en DB
        # Por ahora retornar respuesta simulada
        return MediaMTXServerResponse(
            server_id=result['server_id'],
            server_name=result['server_name'],
            rtsp_url=server.rtsp_url,
            rtsp_port=server.rtsp_port,
            api_url=result['api_url'],
            api_port=server.api_port,
            api_enabled=server.api_enabled,
            username=server.username,
            auth_enabled=server.auth_enabled,
            use_tcp=server.use_tcp,
            max_reconnects=server.max_reconnects,
            reconnect_delay=server.reconnect_delay,
            publish_path_template=server.publish_path_template,
            health_check_interval=server.health_check_interval,
            is_active=server.is_active,
            is_default=server.is_default,
            is_authenticated=result.get('is_authenticated', False),
            last_health_status="unknown",
            created_at=result.get('created_at'),
            updated_at=result.get('created_at'),
            metadata=server.metadata
        )
        
    except ValidationError as e:
        logger.warning(f"Validación fallida al crear servidor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creando servidor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear servidor: {str(e)}"
        )


@router.get("/{server_id}", response_model=MediaMTXServerResponse)
async def get_server(
    server_id: int,
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> MediaMTXServerResponse:
    """
    Obtiene detalles de un servidor específico.
    
    Retorna información completa del servidor incluyendo
    estado de autenticación y métricas básicas.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        result = await presenter.get_server(server_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servidor {server_id} no encontrado"
            )
        
        logger.info(f"Obteniendo detalles del servidor {server_id}")
        
        # Mapear resultado a schema de respuesta
        return MediaMTXServerResponse(
            server_id=result['server_id'],
            server_name=result['server_name'],
            rtsp_url=result['rtsp_url'],
            rtsp_port=result.get('rtsp_port', 8554),
            api_url=result['api_url'],
            api_port=result.get('api_port', 8000),
            api_enabled=result.get('api_enabled', True),
            username=result.get('username'),
            auth_enabled=result.get('auth_enabled', True),
            use_tcp=result.get('use_tcp', True),
            max_reconnects=result.get('max_reconnects', 3),
            reconnect_delay=result.get('reconnect_delay', 5.0),
            publish_path_template=result.get('publish_path_template', 'ucv_{camera_code}'),
            health_check_interval=result.get('health_check_interval', 30),
            is_active=result.get('is_active', True),
            is_default=result.get('is_default', False),
            is_authenticated=result.get('is_authenticated', False),
            auth_expires_at=result.get('auth_expires_at'),
            last_health_status=result.get('last_health_status', 'unknown'),
            last_health_check=result.get('last_health_check'),
            created_at=result.get('created_at'),
            updated_at=result.get('updated_at'),
            metadata=result.get('metadata', {}),
            metrics=result.get('metrics')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo servidor {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener servidor: {str(e)}"
        )


@router.put("/{server_id}", response_model=MediaMTXServerResponse)
async def update_server(
    server_id: int,
    server: MediaMTXServerUpdate,
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> MediaMTXServerResponse:
    """
    Actualiza configuración de un servidor.
    
    Permite actualización parcial de campos. Si se actualizan
    credenciales o URLs, se invalida la autenticación existente.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        # Obtener solo campos no nulos para actualización parcial
        update_data = server.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )
        
        logger.info(f"Actualizando servidor {server_id} con campos: {list(update_data.keys())}")
        
        result = await presenter.update_server(server_id, update_data)
        
        # Obtener servidor actualizado completo
        updated_server = await presenter.get_server(server_id)
        
        if not updated_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servidor {server_id} no encontrado"
            )
        
        # Mapear a schema de respuesta
        return MediaMTXServerResponse(
            server_id=updated_server['server_id'],
            server_name=updated_server['server_name'],
            rtsp_url=updated_server['rtsp_url'],
            rtsp_port=updated_server.get('rtsp_port', 8554),
            api_url=updated_server['api_url'],
            api_port=updated_server.get('api_port', 8000),
            api_enabled=updated_server.get('api_enabled', True),
            username=updated_server.get('username'),
            auth_enabled=updated_server.get('auth_enabled', True),
            use_tcp=updated_server.get('use_tcp', True),
            max_reconnects=updated_server.get('max_reconnects', 3),
            reconnect_delay=updated_server.get('reconnect_delay', 5.0),
            publish_path_template=updated_server.get('publish_path_template', 'ucv_{camera_code}'),
            health_check_interval=updated_server.get('health_check_interval', 30),
            is_active=updated_server.get('is_active', True),
            is_default=updated_server.get('is_default', False),
            is_authenticated=updated_server.get('is_authenticated', False),
            auth_expires_at=updated_server.get('auth_expires_at'),
            last_health_status=updated_server.get('last_health_status', 'unknown'),
            last_health_check=updated_server.get('last_health_check'),
            created_at=updated_server.get('created_at'),
            updated_at=result.get('updated_at'),
            metadata=updated_server.get('metadata', {})
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validación fallida al actualizar servidor {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error actualizando servidor {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar servidor: {str(e)}"
        )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> None:
    """
    Elimina un servidor MediaMTX.
    
    Verifica que no tenga publicaciones activas antes de eliminar.
    También limpia tokens de autenticación asociados.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        logger.info(f"Eliminando servidor {server_id}")
        
        success = await presenter.delete_server(server_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar servidor"
            )
        
    except ValidationError as e:
        logger.warning(f"No se puede eliminar servidor {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error eliminando servidor {server_id}: {str(e)}")
        
        # Si es error de no encontrado
        if "no encontrado" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servidor {server_id} no encontrado"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar servidor: {str(e)}"
        )


@router.get("/{server_id}/status", response_model=MediaMTXServerStatus)
async def get_server_status(
    server_id: int,
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> MediaMTXServerStatus:
    """
    Obtiene estado detallado y métricas del servidor.
    
    Incluye información de conexión, autenticación, publicaciones
    activas y estado de salud del servidor.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        result = await presenter.get_server_status(server_id)
        
        logger.info(f"Obteniendo estado del servidor {server_id}")
        
        return MediaMTXServerStatus(**result)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo estado del servidor {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado: {str(e)}"
        )


@router.post("/{server_id}/test", response_model=MediaMTXServerTestResult)
async def test_server_connection(
    server_id: int,
    presenter: MediaMTXServersPresenter = Depends(get_mediamtx_servers_presenter)
) -> MediaMTXServerTestResult:
    """
    Prueba la conexión con un servidor.
    
    Verifica conectividad y opcionalmente autenticación si el
    servidor tiene credenciales configuradas.
    """
    try:
        # Asegurar que el presenter esté inicializado
        if not presenter.is_ready:
            await presenter.initialize()
        
        logger.info(f"Probando conexión con servidor {server_id}")
        
        result = await presenter.test_connection(server_id)
        
        return MediaMTXServerTestResult(**result)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error probando conexión con servidor {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al probar conexión: {str(e)}"
        )