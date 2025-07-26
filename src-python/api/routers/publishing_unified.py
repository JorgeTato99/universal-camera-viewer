"""
Router API para endpoint unificado de publicaciones.

Proporciona una vista unificada de publicaciones locales y remotas,
permitiendo al frontend mostrar ambos tipos en un solo dashboard.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from presenters.publishing_presenter import PublishingPresenter, get_publishing_presenter
from presenters.mediamtx_remote_publishing_presenter import (
    MediaMTXRemotePublishingPresenter,
    get_mediamtx_remote_publishing_presenter
)
from services.logging_service import get_secure_logger
from pydantic import BaseModel
from datetime import datetime


logger = get_secure_logger("api.routers.publishing_unified")


# Crear router con prefijo
router = APIRouter(
    prefix="/api/publishing",
    tags=["Publishing Unified"],
    responses={
        500: {"description": "Internal Server Error"}
    }
)


class UnifiedPublication(BaseModel):
    """Schema unificado para publicaciones locales y remotas."""
    
    camera_id: str
    camera_name: str
    status: str
    type: str  # "local" o "remote"
    server_name: str  # "Local MediaMTX" o nombre del servidor remoto
    server_id: int  # 0 para local, ID real para remoto
    publish_url: str
    webrtc_url: str
    started_at: datetime
    viewers: int
    metrics: Dict[str, Any]


class UnifiedPublishingResponse(BaseModel):
    """Respuesta del endpoint unificado."""
    
    local: List[Dict[str, Any]]
    remote: List[Dict[str, Any]]
    summary: Dict[str, Any]


def _calculate_summary(
    local_pubs: List[Dict[str, Any]], 
    remote_pubs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calcula métricas agregadas de publicaciones.
    
    Args:
        local_pubs: Lista de publicaciones locales
        remote_pubs: Lista de publicaciones remotas
        
    Returns:
        Dict con métricas agregadas
    """
    total_viewers = 0
    total_bitrate = 0
    
    # Sumar viewers y bitrate de publicaciones locales
    for pub in local_pubs:
        metrics = pub.get('metrics', {})
        total_viewers += metrics.get('viewers', 0)
        total_bitrate += metrics.get('bitrate_kbps', 0)
    
    # Sumar viewers y bitrate de publicaciones remotas
    for pub in remote_pubs:
        metrics = pub.get('metrics', {})
        total_viewers += metrics.get('viewers', 0)
        total_bitrate += metrics.get('bitrate_kbps', 0)
    
    return {
        'total_active': len(local_pubs) + len(remote_pubs),
        'local_active': len(local_pubs),
        'remote_active': len(remote_pubs),
        'total_viewers': total_viewers,
        'total_bitrate_mbps': round(total_bitrate / 1000, 2),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/all", response_model=UnifiedPublishingResponse)
async def get_all_publications(
    local_presenter: PublishingPresenter = Depends(get_publishing_presenter),
    remote_presenter: MediaMTXRemotePublishingPresenter = Depends(get_mediamtx_remote_publishing_presenter)
) -> UnifiedPublishingResponse:
    """
    Obtiene todas las publicaciones activas (locales y remotas).
    
    Retorna una vista unificada de publicaciones con métricas agregadas,
    permitiendo al frontend mostrar todo en un solo dashboard.
    """
    try:
        # Los presenters ya están inicializados por sus factory methods
        # No es necesario inicializarlos aquí nuevamente
        
        # Obtener publicaciones locales
        local_publications = []
        try:
            local_publications = await local_presenter.get_active_publications()
        except Exception as e:
            logger.error(f"Error obteniendo publicaciones locales: {str(e)}")
            local_publications = []
        
        # Obtener publicaciones remotas
        remote_publications = []
        try:
            # El presenter ya está inicializado por su factory method
            remote_pubs = await remote_presenter.list_remote_streams()
            
            logger.debug(f"Publicaciones remotas obtenidas: {len(remote_pubs)}")
            
            # Formatear publicaciones remotas
            for pub_data in remote_pubs:
                remote_publications.append({
                    'camera_id': pub_data.get('camera_id'),
                    'camera_name': pub_data.get('camera_name', pub_data.get('camera_id')),
                    'camera_ip': pub_data.get('camera_ip', ''),  # Agregar IP de la cámara
                    'status': pub_data.get('status', 'publishing'),
                    'type': 'remote',
                    'server_name': pub_data.get('server_name', 'Unknown Server'),
                    'server_id': pub_data.get('server_id', 0),
                    'publish_url': pub_data.get('publish_url', ''),
                    'webrtc_url': pub_data.get('webrtc_url', ''),
                    'started_at': pub_data.get('started_at'),
                    'viewers': pub_data.get('viewers', 0),
                    'metrics': pub_data.get('metrics', {})
                })
        except Exception as e:
            logger.error(f"Error obteniendo publicaciones remotas: {str(e)}")
            remote_publications = []
        
        # Calcular resumen
        summary = _calculate_summary(local_publications, remote_publications)
        
        logger.info(
            f"Retornando publicaciones unificadas - "
            f"Local: {len(local_publications)}, Remoto: {len(remote_publications)}"
        )
        
        # Log de debug para publicaciones remotas
        if remote_publications:
            logger.debug(f"Publicaciones remotas: {remote_publications}")
        
        return UnifiedPublishingResponse(
            local=local_publications,
            remote=remote_publications,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo publicaciones unificadas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener publicaciones: {str(e)}"
        )


@router.get("/summary")
async def get_publishing_summary(
    local_presenter: PublishingPresenter = Depends(get_publishing_presenter),
    remote_presenter: MediaMTXRemotePublishingPresenter = Depends(get_mediamtx_remote_publishing_presenter)
) -> Dict[str, Any]:
    """
    Obtiene solo el resumen de publicaciones activas.
    
    Útil para widgets y dashboards que solo necesitan métricas agregadas.
    """
    try:
        # Reutilizar lógica del endpoint principal
        response = await get_all_publications(local_presenter, remote_presenter)
        return response.summary
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de publicaciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener resumen: {str(e)}"
        )