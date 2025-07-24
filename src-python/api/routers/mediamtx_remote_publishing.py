"""
Router API para publicación FFmpeg hacia servidores MediaMTX remotos.

Expone endpoints para gestionar el streaming real de cámaras locales
hacia servidores MediaMTX remotos usando procesos FFmpeg.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from presenters.mediamtx_remote_publishing_presenter import (
    get_mediamtx_remote_publishing_presenter
)
from services.logging_service import get_secure_logger
from utils.sanitizers import sanitize_url


logger = get_secure_logger("api.routers.mediamtx_remote_publishing")
router = APIRouter(
    prefix="/api/mediamtx/remote-publishing",
    tags=["MediaMTX Remote Publishing"]
)


# Modelos Pydantic para requests/responses
class StartRemoteStreamRequest(BaseModel):
    """Request para iniciar streaming remoto."""
    camera_id: str = Field(..., description="ID de la cámara local")
    server_id: int = Field(..., description="ID del servidor MediaMTX destino")
    custom_name: Optional[str] = Field(None, description="Nombre personalizado para la cámara remota")
    custom_description: Optional[str] = Field(None, description="Descripción personalizada")


class StopRemoteStreamRequest(BaseModel):
    """Request para detener streaming remoto."""
    camera_id: str = Field(..., description="ID de la cámara a detener")


class RemoteStreamStatusResponse(BaseModel):
    """Response con estado de streaming remoto."""
    is_streaming: bool
    stream_info: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None


class RemoteStreamListResponse(BaseModel):
    """Response con lista de streams remotos."""
    streams: List[Dict[str, Any]]
    total: int


# Endpoints
@router.post("/start", summary="Iniciar streaming remoto")
async def start_remote_stream(
    request: StartRemoteStreamRequest,
    presenter=Depends(get_mediamtx_remote_publishing_presenter)
) -> Dict[str, Any]:
    """
    Inicia el streaming FFmpeg de una cámara local hacia un servidor MediaMTX remoto.
    
    Este endpoint coordina:
    1. Crear/verificar cámara en servidor remoto
    2. Obtener URLs de publicación
    3. Iniciar proceso FFmpeg local
    4. Retornar URLs para visualización
    
    Args:
        request: Datos de la solicitud
        presenter: Presenter inyectado
        
    Returns:
        Dict con resultado de la operación incluyendo URLs
        
    Raises:
        HTTPException: En caso de error
    """
    try:
        logger.info(
            f"Iniciando stream remoto - Cámara: {request.camera_id}, "
            f"Servidor: {request.server_id}"
        )
        
        result = await presenter.start_remote_stream(
            camera_id=request.camera_id,
            server_id=request.server_id,
            custom_name=request.custom_name,
            custom_description=request.custom_description
        )
        
        if not result.get('success'):
            error_code = result.get('error_code', 'UNKNOWN_ERROR')
            
            # Mapear códigos de error a HTTP status codes
            status_map = {
                'ALREADY_STREAMING': 409,  # Conflict
                'NOT_AUTHENTICATED': 401,  # Unauthorized
                'VALIDATION_ERROR': 400,   # Bad Request
                'NO_PUBLISH_URL': 502,     # Bad Gateway
                'FFMPEG_START_FAILED': 500 # Internal Server Error
            }
            
            raise HTTPException(
                status_code=status_map.get(error_code, 500),
                detail=result.get('error', 'Error desconocido')
            )
        
        # Sanitizar URLs en la respuesta
        if 'publish_url' in result:
            result['publish_url_display'] = sanitize_url(result['publish_url'])
        if 'webrtc_url' in result:
            result['webrtc_url_display'] = sanitize_url(result['webrtc_url'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error iniciando stream remoto: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.post("/stop", summary="Detener streaming remoto")
async def stop_remote_stream(
    request: StopRemoteStreamRequest,
    presenter=Depends(get_mediamtx_remote_publishing_presenter)
) -> Dict[str, Any]:
    """
    Detiene el streaming FFmpeg hacia servidor remoto.
    
    Args:
        request: Datos de la solicitud
        presenter: Presenter inyectado
        
    Returns:
        Dict con resultado de la operación
        
    Raises:
        HTTPException: En caso de error
    """
    try:
        logger.info(f"Deteniendo stream remoto - Cámara: {request.camera_id}")
        
        result = await presenter.stop_remote_stream(request.camera_id)
        
        if not result.get('success'):
            error_code = result.get('error_code', 'UNKNOWN_ERROR')
            
            if error_code == 'NOT_STREAMING':
                raise HTTPException(
                    status_code=404,
                    detail="La cámara no está transmitiendo remotamente"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=result.get('error', 'Error desconocido')
                )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deteniendo stream remoto: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.get("/status/{camera_id}", summary="Obtener estado de streaming remoto")
async def get_remote_stream_status(
    camera_id: str,
    presenter=Depends(get_mediamtx_remote_publishing_presenter)
) -> RemoteStreamStatusResponse:
    """
    Obtiene el estado del streaming remoto de una cámara.
    
    Args:
        camera_id: ID de la cámara
        presenter: Presenter inyectado
        
    Returns:
        RemoteStreamStatusResponse con información de estado
    """
    try:
        status = await presenter.get_remote_stream_status(camera_id)
        
        # Sanitizar URLs en la respuesta
        if status.get('stream_info') and 'publish_url' in status['stream_info']:
            status['stream_info']['publish_url_display'] = sanitize_url(
                status['stream_info']['publish_url']
            )
        
        return RemoteStreamStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de stream: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.get("/list", summary="Listar streams remotos activos")
async def list_remote_streams(
    server_id: Optional[int] = None,
    presenter=Depends(get_mediamtx_remote_publishing_presenter)
) -> RemoteStreamListResponse:
    """
    Lista los streams remotos activos.
    
    Args:
        server_id: Filtrar por servidor (opcional)
        presenter: Presenter inyectado
        
    Returns:
        RemoteStreamListResponse con lista de streams
    """
    try:
        streams = await presenter.list_remote_streams(server_id=server_id)
        
        # Sanitizar URLs en cada stream
        for stream in streams:
            if 'publish_url' in stream:
                stream['publish_url_display'] = sanitize_url(stream['publish_url'])
            if 'webrtc_url' in stream:
                stream['webrtc_url_display'] = sanitize_url(stream['webrtc_url'])
        
        return RemoteStreamListResponse(
            streams=streams,
            total=len(streams)
        )
        
    except Exception as e:
        logger.error(f"Error listando streams remotos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


@router.post("/restart/{camera_id}", summary="Reiniciar streaming remoto")
async def restart_remote_stream(
    camera_id: str,
    presenter=Depends(get_mediamtx_remote_publishing_presenter)
) -> Dict[str, Any]:
    """
    Reinicia el streaming remoto de una cámara.
    
    Útil cuando hay problemas de conexión o se necesita actualizar configuración.
    
    Args:
        camera_id: ID de la cámara
        presenter: Presenter inyectado
        
    Returns:
        Dict con resultado de la operación
    """
    try:
        logger.info(f"Reiniciando stream remoto - Cámara: {camera_id}")
        
        # Obtener información actual del stream
        status = await presenter.get_remote_stream_status(camera_id)
        
        if not status.get('is_streaming'):
            raise HTTPException(
                status_code=404,
                detail="La cámara no está transmitiendo remotamente"
            )
        
        stream_info = status.get('stream_info', {})
        server_id = stream_info.get('server_id')
        
        if not server_id:
            raise HTTPException(
                status_code=500,
                detail="No se pudo obtener información del servidor"
            )
        
        # Detener stream actual
        stop_result = await presenter.stop_remote_stream(camera_id)
        
        if not stop_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Error deteniendo stream: {stop_result.get('error')}"
            )
        
        # Esperar un momento para asegurar limpieza
        import asyncio
        await asyncio.sleep(1)
        
        # Reiniciar stream
        start_result = await presenter.start_remote_stream(
            camera_id=camera_id,
            server_id=server_id
        )
        
        if not start_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Error reiniciando stream: {start_result.get('error')}"
            )
        
        return {
            'success': True,
            'message': 'Stream remoto reiniciado correctamente',
            **start_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reiniciando stream remoto: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


# Health check específico para publicación remota
@router.get("/health", summary="Estado del servicio de publicación remota")
async def remote_publishing_health(
    presenter=Depends(get_mediamtx_remote_publishing_presenter)
) -> Dict[str, Any]:
    """
    Verifica el estado del servicio de publicación remota.
    
    Returns:
        Dict con información de salud del servicio
    """
    try:
        # Obtener lista de streams activos
        streams = await presenter.list_remote_streams()
        
        return {
            'status': 'healthy',
            'active_streams': len(streams),
            'service': 'MediaMTX Remote Publishing'
        }
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'service': 'MediaMTX Remote Publishing'
        }