"""
Router para endpoints de publicaciones de cámaras v2.

Este router implementa el diseño RESTful unificado para gestión de publicaciones,
soportando tanto publicaciones locales (MediaMTX local) como remotas.

Endpoints:
    POST   /cameras/{camera_id}/publications       - Crear publicación
    GET    /cameras/{camera_id}/publications       - Listar publicaciones de una cámara
    GET    /cameras/{camera_id}/publications/{id}  - Detalle de publicación
    DELETE /cameras/{camera_id}/publications/{id}  - Detener publicación

Arquitectura:
    - Sigue estrictamente el patrón MVP
    - View (Router) → Presenter → Service
    - No hay comunicación directa View → Service
"""

from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, status, Request, Depends, BackgroundTasks
from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging

from api.dependencies import create_response
from api.deps.rate_limit import read_limit, write_limit
from presenters.publishing_presenter import PublishingPresenter, get_publishing_presenter
from presenters.mediamtx_remote_publishing_presenter import (
    MediaMTXRemotePublishingPresenter,
    get_mediamtx_remote_publishing_presenter
)
from presenters.mediamtx_publishing_presenter import (
    MediaMTXPublishingPresenter,
    get_mediamtx_publishing_presenter
)
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    ValidationError,
    ServiceError
)

logger = logging.getLogger(__name__)


# ====================================================================
# Modelos Pydantic para Request/Response
# ====================================================================

class CreatePublicationRequest(BaseModel):
    """Request para crear una nueva publicación."""
    
    type: Literal["local", "remote"] = Field(
        ..., 
        description="Tipo de publicación: local (MediaMTX local) o remote (servidor externo)"
    )
    target_server_id: Optional[int] = Field(
        None,
        description="ID del servidor remoto (requerido si type='remote', ignorado si type='local')"
    )
    stream_key: Optional[str] = Field(
        None,
        description="Stream key personalizado (opcional, se genera automáticamente si no se proporciona)"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Opciones adicionales específicas del tipo de publicación"
    )
    
    @validator('target_server_id')
    def validate_server_id(cls, v, values):
        """Valida que server_id esté presente para publicaciones remotas."""
        if values.get('type') == 'remote' and v is None:
            raise ValueError("target_server_id es requerido para publicaciones remotas")
        return v


class PublicationResponse(BaseModel):
    """Response con información de una publicación."""
    
    publication_id: str = Field(..., description="ID único de la publicación")
    camera_id: str = Field(..., description="ID de la cámara")
    type: str = Field(..., description="Tipo de publicación: local o remote")
    status: str = Field(..., description="Estado: publishing, starting, stopping, error")
    server_id: Optional[int] = Field(None, description="ID del servidor (null para local)")
    server_name: str = Field(..., description="Nombre del servidor")
    
    # URLs de streaming
    stream_url: str = Field(..., description="URL principal de streaming")
    publish_url: Optional[str] = Field(None, description="URL de publicación RTMP")
    webrtc_url: Optional[str] = Field(None, description="URL WebRTC para visualización")
    
    # Metadatos
    started_at: datetime = Field(..., description="Timestamp de inicio")
    stream_key: str = Field(..., description="Stream key único")
    
    # Métricas básicas
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métricas de streaming (fps, bitrate, viewers, etc.)"
    )
    
    # Información adicional de la cámara
    camera_name: str = Field(..., description="Nombre de la cámara")
    camera_ip: str = Field(..., description="IP de la cámara")


class PublicationListResponse(BaseModel):
    """Response con lista de publicaciones."""
    
    total: int = Field(..., description="Total de publicaciones")
    publications: List[PublicationResponse] = Field(
        ..., 
        description="Lista de publicaciones activas"
    )


# ====================================================================
# Router Configuration
# ====================================================================

router = APIRouter(
    prefix="/cameras",
    tags=["cameras-v2-publications"],
    responses={
        404: {"description": "Cámara o publicación no encontrada"},
        409: {"description": "Conflicto - publicación ya existe"}
    }
)


# ====================================================================
# Helper Functions
# ====================================================================

async def _build_publication_response(
    camera_id: str,
    publication_type: str,
    publication_data: Dict[str, Any]
) -> PublicationResponse:
    """
    Construye una respuesta de publicación unificada.
    
    Args:
        camera_id: ID de la cámara
        publication_type: Tipo de publicación (local/remote)
        publication_data: Datos crudos de la publicación
        
    Returns:
        PublicationResponse formateada
    """
    # Obtener información de la cámara
    camera = await camera_manager_service.get_camera(camera_id)
    if not camera:
        raise CameraNotFoundError(camera_id)
    
    # Construir ID único de publicación
    # Formato: {type}_{camera_id}_{server_id}
    server_id = publication_data.get('server_id', 0)
    publication_id = f"{publication_type}_{camera_id}_{server_id}"
    
    # Determinar nombre del servidor
    if publication_type == 'local':
        server_name = "MediaMTX Local"
    else:
        server_name = publication_data.get('server_name', f"Remote Server {server_id}")
    
    # Construir respuesta
    return PublicationResponse(
        publication_id=publication_id,
        camera_id=camera_id,
        type=publication_type,
        status=publication_data.get('status', 'publishing'),
        server_id=server_id if publication_type == 'remote' else None,
        server_name=server_name,
        stream_url=publication_data.get('stream_url', ''),
        publish_url=publication_data.get('publish_url'),
        webrtc_url=publication_data.get('webrtc_url'),
        started_at=publication_data.get('started_at', datetime.utcnow()),
        stream_key=publication_data.get('stream_key', ''),
        metrics=publication_data.get('metrics', {}),
        camera_name=camera.display_name,
        camera_ip=camera.ip
    )


# ====================================================================
# Endpoints
# ====================================================================

@router.post("/{camera_id}/publications", response_model=PublicationResponse)
@write_limit()  # Rate limit para operaciones de escritura
async def create_publication(
    request: Request,
    camera_id: str,
    publication_request: CreatePublicationRequest,
    background_tasks: BackgroundTasks,
    local_presenter: PublishingPresenter = Depends(get_publishing_presenter),
    remote_presenter: MediaMTXRemotePublishingPresenter = Depends(get_mediamtx_remote_publishing_presenter)
):
    """
    Crear una nueva publicación para una cámara.
    
    Este endpoint unifica la creación de publicaciones locales y remotas.
    Según el tipo especificado, delegará al presenter correspondiente.
    
    Args:
        camera_id: ID de la cámara a publicar
        publication_request: Datos de la publicación a crear
        
    Returns:
        PublicationResponse con información de la publicación creada
        
    Raises:
        404: Si la cámara no existe
        409: Si ya existe una publicación activa del mismo tipo
        500: Error interno al crear la publicación
    """
    try:
        logger.info(
            f"Creando publicación {publication_request.type} para cámara {camera_id}"
            f"{f' en servidor {publication_request.target_server_id}' if publication_request.type == 'remote' else ''}"
        )
        
        # Verificar que la cámara existe
        camera = await camera_manager_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        # Delegar según el tipo de publicación
        if publication_request.type == "local":
            # TODO: Implementar publicación local cuando el presenter lo soporte
            # Por ahora retornamos un mock para desarrollo
            logger.warning("Publicación local aún no implementada - retornando datos mock")
            
            mock_publication = {
                'success': True,
                'stream_url': f'rtsp://localhost:8554/camera_{camera_id}',
                'stream_key': f'local_{camera_id}',
                'status': 'publishing',
                'started_at': datetime.utcnow(),
                'metrics': {
                    'fps': 0,
                    'bitrate_kbps': 0,
                    'viewers': 0
                }
            }
            
            response = await _build_publication_response(
                camera_id=camera_id,
                publication_type='local',
                publication_data=mock_publication
            )
            
        else:  # remote
            # Publicación remota - usar presenter existente
            result = await remote_presenter.start_remote_stream(
                camera_id=camera_id,
                server_id=publication_request.target_server_id,
                custom_name=publication_request.options.get('custom_name'),
                custom_description=publication_request.options.get('custom_description')
            )
            
            if not result.get('success'):
                # Mapear errores conocidos a códigos HTTP apropiados
                error_code = result.get('error_code', 'UNKNOWN_ERROR')
                error_msg = result.get('error', 'Error desconocido')
                
                if error_code in ['ALREADY_STREAMING', 'CAMERA_ALREADY_EXISTS']:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=error_msg
                    )
                elif error_code == 'NOT_AUTHENTICATED':
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=error_msg
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=error_msg
                    )
            
            # Agregar logs para debug
            logger.debug(f"Resultado de publicación remota: {result}")
            
            # Construir respuesta unificada
            response = await _build_publication_response(
                camera_id=camera_id,
                publication_type='remote',
                publication_data={
                    **result,
                    'server_id': publication_request.target_server_id,
                    'stream_key': result.get('publish_token', ''),
                    'started_at': result.get('started_at') or datetime.utcnow()
                }
            )
        
        logger.info(f"Publicación creada exitosamente: {response.publication_id}")
        
        # Devolver directamente el modelo de respuesta
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando publicación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear publicación: {str(e)}"
        )


@router.get("/{camera_id}/publications", response_model=PublicationListResponse)
@read_limit()
async def list_camera_publications(
    request: Request,
    camera_id: str,
    type_filter: Optional[Literal["local", "remote"]] = None,
    local_presenter: PublishingPresenter = Depends(get_publishing_presenter),
    remote_presenter: MediaMTXRemotePublishingPresenter = Depends(get_mediamtx_remote_publishing_presenter)
):
    """
    Listar todas las publicaciones activas de una cámara.
    
    Args:
        camera_id: ID de la cámara
        type_filter: Filtrar por tipo de publicación (opcional)
        
    Returns:
        Lista de publicaciones activas de la cámara
    """
    try:
        # Verificar que la cámara existe
        camera = await camera_manager_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        publications = []
        
        # Obtener publicaciones locales si no hay filtro o es 'local'
        if not type_filter or type_filter == 'local':
            try:
                # TODO: Implementar cuando el presenter soporte listar por cámara
                # Por ahora verificamos si está en las publicaciones activas
                local_pubs = await local_presenter.get_active_publications()
                
                for pub in local_pubs:
                    if pub.get('camera_id') == camera_id:
                        pub_response = await _build_publication_response(
                            camera_id=camera_id,
                            publication_type='local',
                            publication_data=pub
                        )
                        publications.append(pub_response)
                        
            except Exception as e:
                logger.error(f"Error obteniendo publicaciones locales: {str(e)}")
        
        # Obtener publicaciones remotas si no hay filtro o es 'remote'
        if not type_filter or type_filter == 'remote':
            try:
                # Obtener estado del stream remoto
                remote_status = await remote_presenter.get_remote_stream_status(camera_id)
                
                if remote_status.get('is_streaming'):
                    stream_info = remote_status.get('stream_info', {})
                    
                    pub_response = await _build_publication_response(
                        camera_id=camera_id,
                        publication_type='remote',
                        publication_data={
                            **stream_info,
                            'metrics': remote_status.get('metrics', {}),
                            'status': 'publishing'
                        }
                    )
                    publications.append(pub_response)
                    
            except Exception as e:
                logger.error(f"Error obteniendo publicaciones remotas: {str(e)}")
        
        response = PublicationListResponse(
            total=len(publications),
            publications=publications
        )
        
        return create_response(
            success=True,
            data=response.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando publicaciones: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar publicaciones"
        )


@router.get("/{camera_id}/publications/{publication_id}", response_model=PublicationResponse)
@read_limit()
async def get_publication_detail(
    request: Request,
    camera_id: str,
    publication_id: str,
    local_presenter: PublishingPresenter = Depends(get_publishing_presenter),
    remote_presenter: MediaMTXRemotePublishingPresenter = Depends(get_mediamtx_remote_publishing_presenter)
):
    """
    Obtener detalles de una publicación específica.
    
    Args:
        camera_id: ID de la cámara
        publication_id: ID de la publicación
        
    Returns:
        Detalles completos de la publicación
    """
    try:
        # Parsear el publication_id para determinar el tipo
        # Formato esperado: {type}_{camera_id}_{server_id}
        parts = publication_id.split('_')
        if len(parts) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de publicación inválido"
            )
        
        pub_type = parts[0]
        pub_camera_id = parts[1]
        
        # Verificar que el camera_id coincide
        if pub_camera_id != camera_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada para esta cámara"
            )
        
        # Obtener detalles según el tipo
        if pub_type == 'local':
            # TODO: Implementar cuando el presenter lo soporte
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Detalle de publicaciones locales aún no implementado"
            )
            
        elif pub_type == 'remote':
            # Obtener estado del stream remoto
            remote_status = await remote_presenter.get_remote_stream_status(camera_id)
            
            if not remote_status.get('is_streaming'):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Publicación no encontrada o no activa"
                )
            
            stream_info = remote_status.get('stream_info', {})
            
            response = await _build_publication_response(
                camera_id=camera_id,
                publication_type='remote',
                publication_data={
                    **stream_info,
                    'metrics': remote_status.get('metrics', {}),
                    'status': 'publishing'
                }
            )
            
            return create_response(
                success=True,
                data=response.dict()
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de publicación inválido"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo detalle de publicación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener detalle"
        )


@router.delete("/{camera_id}/publications/{publication_id}")
@write_limit()
async def stop_publication(
    request: Request,
    camera_id: str,
    publication_id: str,
    local_presenter: PublishingPresenter = Depends(get_publishing_presenter),
    remote_presenter: MediaMTXRemotePublishingPresenter = Depends(get_mediamtx_remote_publishing_presenter)
):
    """
    Detener una publicación activa.
    
    Args:
        camera_id: ID de la cámara
        publication_id: ID de la publicación a detener
        
    Returns:
        Confirmación de que la publicación fue detenida
    """
    try:
        # Parsear el publication_id
        parts = publication_id.split('_')
        if len(parts) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de publicación inválido"
            )
        
        pub_type = parts[0]
        pub_camera_id = parts[1]
        
        # Verificar que el camera_id coincide
        if pub_camera_id != camera_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada para esta cámara"
            )
        
        # Detener según el tipo
        if pub_type == 'local':
            # TODO: Implementar cuando el presenter lo soporte
            logger.warning("Detención de publicación local aún no implementada")
            
            return create_response(
                success=True,
                message="Publicación local detenida (mock)"
            )
            
        elif pub_type == 'remote':
            # Detener publicación remota
            result = await remote_presenter.stop_remote_stream(camera_id)
            
            if not result.get('success'):
                error_code = result.get('error_code', 'UNKNOWN_ERROR')
                
                if error_code == 'NOT_STREAMING':
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="La publicación no está activa"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.get('error', 'Error al detener publicación')
                    )
            
            return create_response(
                success=True,
                message="Publicación remota detenida exitosamente"
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de publicación inválido"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deteniendo publicación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al detener publicación"
        )


# ====================================================================
# Métricas y Control de Streaming
# ====================================================================

@router.get("/{camera_id}/publications/{publication_id}/metrics", response_model=Dict[str, Any])
@read_limit()
async def get_publication_metrics(
    request: Request,
    camera_id: str,
    publication_id: str,
    mediamtx_presenter: MediaMTXPublishingPresenter = Depends(get_mediamtx_publishing_presenter)
):
    """
    Obtener métricas en tiempo real de una publicación activa.
    
    Args:
        camera_id: ID de la cámara
        publication_id: ID de la publicación
        
    Returns:
        Métricas del streaming (FPS, bitrate, frames, etc.)
    """
    try:
        # Por ahora solo soportamos publicaciones remotas
        if not publication_id.startswith('remote_'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se soportan métricas para publicaciones remotas"
            )
        
        # Obtener métricas del presenter
        result = await mediamtx_presenter.get_streaming_metrics(camera_id)
        
        if result.get('success'):
            return create_response(
                success=True,
                data=result.get('metrics'),
                message="Métricas obtenidas exitosamente"
            )
        else:
            error_code = result.get('error_code', 'UNKNOWN_ERROR')
            
            if error_code == 'NOT_PUBLISHED':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Publicación no encontrada"
                )
            elif error_code == 'NO_STREAM':
                return create_response(
                    success=False,
                    message="No hay streaming activo",
                    error="Streaming no está activo para esta publicación"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get('error', 'Error obteniendo métricas')
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener métricas"
        )


@router.post("/{camera_id}/publications/{publication_id}/restart")
@write_limit()
async def restart_publication(
    request: Request,
    camera_id: str,
    publication_id: str,
    mediamtx_presenter: MediaMTXPublishingPresenter = Depends(get_mediamtx_publishing_presenter)
):
    """
    Reiniciar el streaming de una publicación activa.
    
    Args:
        camera_id: ID de la cámara
        publication_id: ID de la publicación
        
    Returns:
        Confirmación de reinicio del streaming
    """
    try:
        # Por ahora solo soportamos publicaciones remotas
        if not publication_id.startswith('remote_'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se puede reiniciar streaming de publicaciones remotas"
            )
        
        # Reiniciar streaming
        result = await mediamtx_presenter.restart_streaming(camera_id)
        
        if result.get('success'):
            return create_response(
                success=True,
                message=result.get('message', 'Streaming reiniciado exitosamente')
            )
        else:
            error_code = result.get('error_code', 'UNKNOWN_ERROR')
            
            if error_code == 'NOT_PUBLISHED':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Publicación no encontrada"
                )
            elif error_code == 'NO_STREAM':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hay streaming activo para reiniciar"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get('error', 'Error reiniciando streaming')
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reiniciando streaming: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al reiniciar streaming"
        )


# ====================================================================
# Health Check
# ====================================================================

@router.get("/publications/health")
async def publications_health():
    """
    Verificar el estado del sistema de publicaciones.
    
    Returns:
        Estado de salud del servicio de publicaciones
    """
    try:
        # TODO: Implementar verificación real del estado
        return create_response(
            success=True,
            data={
                'status': 'healthy',
                'service': 'Publications v2',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return create_response(
            success=False,
            data={
                'status': 'unhealthy',
                'service': 'Publications v2',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )