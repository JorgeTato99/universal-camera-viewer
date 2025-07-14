"""
Dependencias compartidas para FastAPI
"""

from typing import Dict, Any, AsyncGenerator
from fastapi import Depends, HTTPException, status
from datetime import datetime
import logging

# Importar servicios existentes
# TODO: Descomentar cuando los servicios estén correctamente configurados
# from services.scan_service import ScanService
# from services.connection_service import ConnectionService
# from services.config_service import ConfigService
# from services.video.video_stream_service import VideoStreamService
# from presenters.camera_presenter import CameraPresenter
# from presenters.streaming.video_stream_presenter import VideoStreamPresenter

logger = logging.getLogger(__name__)


# Instancias singleton de servicios
# TODO: Descomentar cuando los servicios estén correctamente configurados
# _scan_service: ScanService = None
# _connection_service: ConnectionService = None
# _config_service: ConfigService = None
# _video_service: VideoStreamService = None
# _camera_presenter: CameraPresenter = None
# _video_presenter: VideoStreamPresenter = None


# def get_scan_service() -> ScanService:
#     """Obtener instancia singleton de ScanService."""
#     global _scan_service
#     if _scan_service is None:
#         _scan_service = ScanService()
#         logger.info("ScanService inicializado")
#     return _scan_service


# def get_connection_service() -> ConnectionService:
#     """Obtener instancia singleton de ConnectionService."""
#     global _connection_service
#     if _connection_service is None:
#         _connection_service = ConnectionService()
#         logger.info("ConnectionService inicializado")
#     return _connection_service


# def get_config_service() -> ConfigService:
#     """Obtener instancia singleton de ConfigService."""
#     global _config_service
#     if _config_service is None:
#         _config_service = ConfigService()
#         logger.info("ConfigService inicializado")
#     return _config_service


# def get_video_stream_service() -> VideoStreamService:
#     """Obtener instancia singleton de VideoStreamService."""
#     global _video_service
#     if _video_service is None:
#         _video_service = VideoStreamService()
#         logger.info("VideoStreamService inicializado")
#     return _video_service


# def get_camera_presenter(
#     scan_service: ScanService = Depends(get_scan_service),
#     connection_service: ConnectionService = Depends(get_connection_service)
# ) -> CameraPresenter:
#     """Obtener instancia de CameraPresenter con dependencias."""
#     global _camera_presenter
#     if _camera_presenter is None:
#         _camera_presenter = CameraPresenter(scan_service, connection_service)
#         logger.info("CameraPresenter inicializado")
#     return _camera_presenter


# def get_video_presenter(
#     video_service: VideoStreamService = Depends(get_video_stream_service)
# ) -> VideoStreamPresenter:
#     """Obtener instancia de VideoStreamPresenter con dependencias."""
#     global _video_presenter
#     if _video_presenter is None:
#         _video_presenter = VideoStreamPresenter(video_service)
#         logger.info("VideoStreamPresenter inicializado")
#     return _video_presenter


def create_response(
    success: bool = True,
    data: Any = None,
    error: str = None,
    message: str = None
) -> Dict[str, Any]:
    """
    Crear respuesta estándar de la API.
    
    Args:
        success: Si la operación fue exitosa
        data: Datos de respuesta
        error: Mensaje de error si hubo
        message: Mensaje adicional
        
    Returns:
        Dict con formato estándar de respuesta
    """
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if data is not None:
        response["data"] = data
    
    if error is not None:
        response["error"] = error
        
    if message is not None:
        response["message"] = message
        
    return response


async def cleanup_services():
    """Limpiar servicios al cerrar la aplicación."""
    logger.info("Limpiando servicios...")
    
    # TODO: Descomentar cuando los servicios estén configurados
    # if _video_service:
    #     await _video_service.cleanup()
    #     
    # if _connection_service:
    #     await _connection_service.cleanup()
    
    logger.info("Servicios limpiados correctamente")