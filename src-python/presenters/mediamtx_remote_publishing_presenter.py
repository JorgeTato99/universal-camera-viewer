"""
Presenter para coordinar publicación FFmpeg hacia servidores MediaMTX remotos.

Este presenter extiende la funcionalidad del MediaMTXPublishingPresenter
agregando la gestión real de procesos FFmpeg para publicación remota.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from presenters.base_presenter import BasePresenter
from presenters.mediamtx_publishing_presenter import get_mediamtx_publishing_presenter
from services.mediamtx.remote_publisher import get_mediamtx_remote_publisher
from services.publishing.rtsp_publisher_service import get_publisher_service
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.mediamtx.api_client import get_mediamtx_api_client
from models.publishing import PublishConfiguration
from services.logging_service import get_secure_logger
from utils.exceptions import ValidationError, ServiceError
from utils.sanitizers import sanitize_url


logger = get_secure_logger("presenters.mediamtx_remote_publishing")


class MediaMTXRemotePublishingPresenter(BasePresenter):
    """
    Presenter que coordina la publicación FFmpeg real hacia servidores remotos.
    
    Este presenter trabaja en conjunto con MediaMTXPublishingPresenter:
    - MediaMTXPublishingPresenter: Gestiona registro de cámaras en servidor remoto
    - MediaMTXRemotePublishingPresenter: Gestiona procesos FFmpeg locales
    
    Sigue estrictamente el patrón MVP:
    - View (API) → Presenter → Services
    - No hay comunicación directa View → Service
    """
    
    def __init__(self):
        """Inicializa el presenter con sus dependencias."""
        super().__init__()
        self.logger = logger
        
        # Presenters colaboradores
        self._publishing_presenter = get_mediamtx_publishing_presenter()
        
        # Servicios
        self._remote_publisher = None  # Se inicializa async
        self._db_service = get_mediamtx_db_service()
        self._api_client = get_mediamtx_api_client()
        
        # Estado interno
        self._active_remote_streams: Dict[str, Dict[str, Any]] = {}
        
    async def _initialize_presenter(self) -> None:
        """Inicialización específica del presenter."""
        self.logger.info("Inicializando MediaMTXRemotePublishingPresenter")
        
        # Obtener servicio de publicación remota
        self._remote_publisher = await get_mediamtx_remote_publisher()
        
        # Cargar streams remotos activos
        await self._load_active_remote_streams()
        
    async def _cleanup_presenter(self) -> None:
        """Limpieza específica del presenter."""
        self.logger.info("Limpiando MediaMTXRemotePublishingPresenter")
        
        # Detener todos los streams remotos activos
        for camera_id in list(self._active_remote_streams.keys()):
            await self.stop_remote_stream(camera_id)
        
        self._active_remote_streams.clear()
    
    async def _load_active_remote_streams(self) -> None:
        """Carga streams remotos activos desde la base de datos."""
        try:
            # Obtener publicaciones remotas activas
            publications = await self._db_service.get_active_remote_publications()
            
            for pub in publications:
                # Solo cargar las que tienen proceso FFmpeg activo
                if pub.get('status', '').lower() == 'publishing':
                    self._active_remote_streams[pub['camera_id']] = {
                        'server_id': pub['server_id'],
                        'remote_camera_id': pub['remote_camera_id'],
                        'publish_url': pub['publish_url'],
                        'session_id': pub['session_id'],
                        'started_at': pub['start_time']
                    }
            
            self.logger.info(
                f"Cargados {len(self._active_remote_streams)} streams remotos activos"
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando streams activos: {str(e)}")
    
    async def start_remote_stream(
        self,
        camera_id: str,
        server_id: int,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inicia streaming FFmpeg hacia servidor MediaMTX remoto.
        
        Este método coordina:
        1. Crear/verificar cámara en servidor remoto (via MediaMTXPublishingPresenter)
        2. Obtener URLs de publicación
        3. Iniciar proceso FFmpeg local
        4. Monitorear estado
        
        Args:
            camera_id: ID de la cámara local
            server_id: ID del servidor MediaMTX destino
            custom_name: Nombre personalizado para la cámara remota
            custom_description: Descripción personalizada
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            await self.set_busy(True)
            
            # Verificar si ya está streaming
            if camera_id in self._active_remote_streams:
                return {
                    'success': False,
                    'error': 'La cámara ya está transmitiendo a un servidor remoto',
                    'error_code': 'ALREADY_STREAMING'
                }
            
            self.logger.info(
                f"Iniciando stream remoto para cámara {camera_id} "
                f"hacia servidor {server_id}"
            )
            
            # Paso 1: Crear/obtener cámara en servidor remoto
            publish_result = await self._publishing_presenter.publish_camera_to_remote(
                camera_id=camera_id,
                server_id=server_id,
                custom_name=custom_name,
                custom_description=custom_description
            )
            
            if not publish_result.get('success'):
                return publish_result
            
            # Extraer URLs de publicación
            publish_url = publish_result.get('publish_url')
            webrtc_url = publish_result.get('webrtc_url')
            agent_command = publish_result.get('agent_command')
            
            if not publish_url:
                return {
                    'success': False,
                    'error': 'No se obtuvo URL de publicación del servidor remoto',
                    'error_code': 'NO_PUBLISH_URL'
                }
            
            # Paso 2: Iniciar publicación FFmpeg real
            self.logger.info(
                f"Iniciando FFmpeg para publicar a {sanitize_url(publish_url)}"
            )
            
            # Usar el servicio remoto de publicación
            stream_result = await self._remote_publisher.publish_camera(
                camera_id=camera_id,
                server_id=server_id,
                custom_name=custom_name,
                custom_description=custom_description
            )
            
            if stream_result.success:
                # Actualizar estado interno
                self._active_remote_streams[camera_id] = {
                    'server_id': server_id,
                    'remote_camera_id': publish_result.get('remote_camera_id'),
                    'publish_url': publish_url,
                    'webrtc_url': webrtc_url,
                    'session_id': stream_result.session_id if hasattr(stream_result, 'session_id') else None,
                    'started_at': datetime.utcnow()
                }
                
                # Emitir evento de inicio exitoso
                await self._emit_event('remote_stream_started', {
                    'camera_id': camera_id,
                    'server_id': server_id,
                    'publish_url': sanitize_url(publish_url),
                    'webrtc_url': sanitize_url(webrtc_url) if webrtc_url else None
                })
                
                return {
                    'success': True,
                    'camera_id': camera_id,
                    'publish_url': publish_url,
                    'webrtc_url': webrtc_url,
                    'message': 'Stream remoto iniciado correctamente'
                }
            else:
                # Si falla el FFmpeg, limpiar la cámara remota creada
                # TODO: Decidir si eliminar cámara remota en caso de fallo
                
                return {
                    'success': False,
                    'error': stream_result.error or 'Error iniciando proceso FFmpeg',
                    'error_code': 'FFMPEG_START_FAILED'
                }
                
        except Exception as e:
            self.logger.error(f"Error iniciando stream remoto: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
            
        finally:
            await self.set_busy(False)
    
    async def stop_remote_stream(self, camera_id: str) -> Dict[str, Any]:
        """
        Detiene el streaming FFmpeg hacia servidor remoto.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            await self.set_busy(True)
            
            if camera_id not in self._active_remote_streams:
                return {
                    'success': False,
                    'error': 'La cámara no está transmitiendo remotamente',
                    'error_code': 'NOT_STREAMING'
                }
            
            stream_info = self._active_remote_streams[camera_id]
            
            self.logger.info(
                f"Deteniendo stream remoto para cámara {camera_id}"
            )
            
            # Detener proceso FFmpeg
            stop_result = await self._remote_publisher.stop_publishing(camera_id)
            
            if stop_result.success:
                # Actualizar estado
                del self._active_remote_streams[camera_id]
                
                # Emitir evento
                await self._emit_event('remote_stream_stopped', {
                    'camera_id': camera_id,
                    'server_id': stream_info['server_id']
                })
                
                # Opcionalmente, despublicar del servidor remoto
                # Depende de la política de negocio
                # await self._publishing_presenter.unpublish_camera(camera_id)
                
                return {
                    'success': True,
                    'message': 'Stream remoto detenido correctamente'
                }
            else:
                return {
                    'success': False,
                    'error': stop_result.error or 'Error deteniendo proceso FFmpeg',
                    'error_code': 'STOP_FAILED'
                }
                
        except Exception as e:
            self.logger.error(f"Error deteniendo stream remoto: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
            
        finally:
            await self.set_busy(False)
    
    async def get_remote_stream_status(
        self,
        camera_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene el estado del streaming remoto de una cámara.
        
        Args:
            camera_id: ID de la cámara local
            
        Returns:
            Dict con información de estado
        """
        if camera_id in self._active_remote_streams:
            stream_info = self._active_remote_streams[camera_id]
            
            # Obtener estado detallado del servicio
            detailed_status = await self._remote_publisher.get_remote_publication_status(
                camera_id
            )
            
            # TODO: Obtener métricas reales del proceso FFmpeg
            # Por ahora retornar información básica
            
            return {
                'is_streaming': True,
                'stream_info': {
                    **stream_info,
                    'status': detailed_status.get('status', 'publishing'),
                    'duration': self._calculate_duration(stream_info['started_at'])
                },
                'metrics': {
                    'fps': 0,  # TODO: Obtener de FFmpeg
                    'bitrate': 0,  # TODO: Obtener de FFmpeg
                    'frames_sent': 0  # TODO: Obtener de FFmpeg
                }
            }
        
        return {
            'is_streaming': False,
            'stream_info': None,
            'metrics': None
        }
    
    async def list_remote_streams(
        self,
        server_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista los streams remotos activos.
        
        Args:
            server_id: Filtrar por servidor (opcional)
            
        Returns:
            Lista de streams activos
        """
        streams = []
        
        for camera_id, stream_info in self._active_remote_streams.items():
            if server_id is None or stream_info['server_id'] == server_id:
                status = await self.get_remote_stream_status(camera_id)
                streams.append({
                    'camera_id': camera_id,
                    **status['stream_info'],
                    'metrics': status.get('metrics', {})
                })
        
        return streams
    
    def _calculate_duration(self, start_time: datetime) -> int:
        """
        Calcula duración en segundos desde el inicio.
        
        Args:
            start_time: Tiempo de inicio
            
        Returns:
            Duración en segundos
        """
        if not start_time:
            return 0
            
        delta = datetime.utcnow() - start_time
        return int(delta.total_seconds())


# Instancia singleton
_presenter: Optional[MediaMTXRemotePublishingPresenter] = None


def get_mediamtx_remote_publishing_presenter() -> MediaMTXRemotePublishingPresenter:
    """
    Obtiene la instancia singleton del presenter.
    
    Returns:
        MediaMTXRemotePublishingPresenter singleton
    """
    global _presenter
    
    if _presenter is None:
        _presenter = MediaMTXRemotePublishingPresenter()
        
    return _presenter