"""
Router para gestión de cámaras en servidores MediaMTX remotos.

Proporciona endpoints para publicar cámaras locales en servidores remotos,
gestionar el ciclo de vida de las publicaciones y consultar estados.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from presenters.mediamtx_publishing_presenter import get_mediamtx_publishing_presenter
# from api.dependencies import get_current_user  # TODO: Implementar autenticación si es necesaria
from services.logging_service import get_secure_logger


logger = get_secure_logger("api.routers.mediamtx_cameras")

router = APIRouter(
    prefix="/api/mediamtx/cameras",
    tags=["mediamtx-cameras"],
    responses={
        404: {"description": "Recurso no encontrado"},
        401: {"description": "No autorizado"},
        500: {"description": "Error interno del servidor"}
    }
)


# === Modelos Pydantic ===

class PublishCameraRequest(BaseModel):
    """Request para publicar una cámara a servidor remoto."""
    camera_id: str = Field(..., description="ID de la cámara local")
    server_id: int = Field(..., description="ID del servidor MediaMTX destino")
    custom_name: Optional[str] = Field(None, description="Nombre personalizado para la cámara remota")
    custom_description: Optional[str] = Field(None, description="Descripción personalizada")


class PublishCameraResponse(BaseModel):
    """Response con información de publicación."""
    success: bool
    camera_id: str
    remote_camera_id: Optional[str] = None
    publish_url: Optional[str] = None
    webrtc_url: Optional[str] = None
    agent_command: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class UnpublishCameraRequest(BaseModel):
    """Request para despublicar una cámara."""
    camera_id: str = Field(..., description="ID de la cámara local")


class PublicationStatusResponse(BaseModel):
    """Response con estado de publicación."""
    is_published: bool
    camera_id: str
    server_id: Optional[int] = None
    remote_camera_id: Optional[str] = None
    publish_url: Optional[str] = None
    webrtc_url: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


class PublishedCameraInfo(BaseModel):
    """Información de una cámara publicada."""
    camera_id: str
    camera_name: str
    server_id: int
    remote_id: str
    publish_url: str
    webrtc_url: str
    status: str
    created_at: str


class ListPublishedResponse(BaseModel):
    """Response con lista de cámaras publicadas."""
    total: int
    cameras: List[PublishedCameraInfo]


# === Endpoints ===

@router.post(
    "/publish",
    response_model=PublishCameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar cámara a servidor remoto",
    description="Crea una cámara en un servidor MediaMTX remoto y obtiene las URLs de publicación"
)
async def publish_camera(
    request: PublishCameraRequest,
    presenter = Depends(get_mediamtx_publishing_presenter)
) -> PublishCameraResponse:
    """
    Publica una cámara local en un servidor MediaMTX remoto.
    
    El servidor debe estar previamente configurado y autenticado.
    La cámara se creará en el servidor remoto con la configuración
    proporcionada y se devolverán las URLs necesarias para el streaming.
    """
    logger.info(
        f"Publicando cámara {request.camera_id} a servidor {request.server_id}"
    )
    
    try:
        result = await presenter.publish_camera_to_remote(
            camera_id=request.camera_id,
            server_id=request.server_id,
            custom_name=request.custom_name,
            custom_description=request.custom_description
        )
        
        if result['success']:
            return PublishCameraResponse(**result)
        else:
            # Manejar errores específicos
            error_code = result.get('error_code', 'UNKNOWN_ERROR')
            
            if error_code == 'VALIDATION_ERROR':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get('error', 'Error de validación')
                )
            elif error_code == 'NOT_AUTHENTICATED':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get('error', 'No autenticado con el servidor')
                )
            elif error_code == 'API_ERROR':
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=result.get('error', 'Error del servidor remoto')
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get('error', 'Error interno')
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publicando cámara: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.delete(
    "/unpublish",
    response_model=PublishCameraResponse,
    status_code=status.HTTP_200_OK,
    summary="Despublicar cámara",
    description="Elimina una cámara del servidor remoto"
)
async def unpublish_camera(
    request: UnpublishCameraRequest,
    presenter = Depends(get_mediamtx_publishing_presenter)
) -> PublishCameraResponse:
    """
    Elimina una cámara del servidor MediaMTX remoto.
    
    La cámara se eliminará completamente del servidor remoto
    y se liberarán todos los recursos asociados.
    """
    logger.info(f"Despublicando cámara {request.camera_id}")
    
    try:
        result = await presenter.unpublish_camera(request.camera_id)
        
        return PublishCameraResponse(
            success=result['success'],
            camera_id=request.camera_id,
            message=result.get('message'),
            error=result.get('error'),
            error_code=result.get('error_code')
        )
        
    except Exception as e:
        logger.error(f"Error despublicando cámara: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/status/{camera_id}",
    response_model=PublicationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener estado de publicación",
    description="Consulta si una cámara está publicada y sus detalles"
)
async def get_publication_status(
    camera_id: str,
    presenter = Depends(get_mediamtx_publishing_presenter)
) -> PublicationStatusResponse:
    """
    Obtiene el estado de publicación de una cámara específica.
    
    Devuelve información sobre si la cámara está publicada,
    en qué servidor y las URLs de acceso.
    """
    logger.debug(f"Consultando estado de publicación para cámara {camera_id}")
    
    try:
        result = await presenter.get_publication_status(camera_id)
        
        response = PublicationStatusResponse(
            is_published=result['is_published'],
            camera_id=camera_id
        )
        
        if result['is_published'] and result['publication']:
            pub = result['publication']
            response.server_id = pub.get('server_id')
            response.remote_camera_id = pub.get('remote_id')
            response.publish_url = pub.get('publish_url')
            response.webrtc_url = pub.get('webrtc_url')
            response.status = pub.get('status')
            response.created_at = pub.get('created_at').isoformat() if pub.get('created_at') else None
        
        return response
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de publicación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/published",
    response_model=ListPublishedResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar cámaras publicadas",
    description="Obtiene la lista de todas las cámaras publicadas en servidores remotos"
)
async def list_published_cameras(
    server_id: Optional[int] = None,
    presenter = Depends(get_mediamtx_publishing_presenter)
) -> ListPublishedResponse:
    """
    Lista todas las cámaras publicadas en servidores remotos.
    
    Opcionalmente se puede filtrar por servidor específico.
    """
    logger.debug(
        f"Listando cámaras publicadas" + 
        (f" para servidor {server_id}" if server_id else "")
    )
    
    try:
        cameras = await presenter.list_published_cameras(server_id)
        
        # Convertir a modelos Pydantic
        camera_list = []
        for cam in cameras:
            camera_list.append(PublishedCameraInfo(
                camera_id=cam['camera_id'],
                camera_name=cam['camera_name'],
                server_id=cam['server_id'],
                remote_id=cam['remote_id'],
                publish_url=cam['publish_url'],
                webrtc_url=cam['webrtc_url'],
                status=cam['status'],
                created_at=cam['created_at'].isoformat() if cam.get('created_at') else ''
            ))
        
        return ListPublishedResponse(
            total=len(camera_list),
            cameras=camera_list
        )
        
    except Exception as e:
        logger.error(f"Error listando cámaras publicadas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post(
    "/sync/{camera_id}",
    response_model=PublicationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Sincronizar estado de cámara",
    description="Sincroniza el estado de una cámara con el servidor remoto"
)
async def sync_camera_status(
    camera_id: str,
    presenter = Depends(get_mediamtx_publishing_presenter)
) -> PublicationStatusResponse:
    """
    Sincroniza el estado de una cámara con el servidor remoto.
    
    Útil para actualizar el estado local con el estado real
    en el servidor MediaMTX remoto.
    """
    logger.info(f"Sincronizando estado de cámara {camera_id}")
    
    try:
        # Primero obtener estado actual
        result = await presenter.get_publication_status(camera_id)
        
        if not result['is_published']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La cámara no está publicada"
            )
        
        # TODO: Implementar sincronización real con servidor remoto
        # Por ahora solo devolvemos el estado actual
        
        pub = result['publication']
        return PublicationStatusResponse(
            is_published=True,
            camera_id=camera_id,
            server_id=pub.get('server_id'),
            remote_camera_id=pub.get('remote_id'),
            publish_url=pub.get('publish_url'),
            webrtc_url=pub.get('webrtc_url'),
            status=pub.get('status'),
            created_at=pub.get('created_at').isoformat() if pub.get('created_at') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sincronizando estado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )