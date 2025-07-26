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
        
        try:
            # Obtener servicio de publicación remota
            self._remote_publisher = await get_mediamtx_remote_publisher()
        except Exception as e:
            self.logger.error(f"Error inicializando remote publisher: {e}")
        
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
            self.logger.info("Cargando streams remotos activos desde BD...")
            # Obtener publicaciones remotas activas
            publications = await self._db_service.get_active_remote_publications()
            
            self.logger.info(f"Publicaciones activas desde BD: {len(publications)}")
            
            for pub in publications:
                # Cargar todas las publicaciones activas, no solo las 'publishing'
                self.logger.debug(f"Procesando publicación: {pub}")
                
                # Obtener el nombre del servidor
                server_name = 'Unknown Server'
                if pub.get('server_id'):
                    try:
                        server = await self._db_service.get_server_by_id(pub['server_id'])
                        if server:
                            server_name = server.get('server_name', f'Server {pub["server_id"]}')
                    except:
                        pass
                
                self._active_remote_streams[pub['camera_id']] = {
                    'server_id': pub['server_id'],
                    'server_name': server_name,
                    'remote_camera_id': pub.get('remote_camera_id', ''),
                    'publish_url': pub.get('publish_url', ''),
                    'webrtc_url': pub.get('webrtc_url', ''),
                    'session_id': pub.get('session_id', ''),
                    'started_at': pub.get('start_time'),
                    'status': pub.get('status', 'publishing')
                }
            
            self.logger.info(
                f"Cargados {len(self._active_remote_streams)} streams remotos activos"
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando streams activos: {str(e)}", exc_info=True)
    
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
                self.logger.warning(
                    f"Cámara {camera_id} ya está publicando al servidor {server_id}"
                )
                return {
                    'success': False,
                    'error': 'La cámara ya está siendo publicada',
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
            
            # Paso 2: El streaming ya fue iniciado por publish_camera_to_remote
            # Solo necesitamos verificar el estado
            self.logger.info(
                f"Stream ya iniciado por publishing presenter para {sanitize_url(publish_url)}"
            )
            
            # Verificar si el stream está activo mediante la sesión
            session_id = publish_result.get('session_id')
            streaming = publish_result.get('streaming', False)
            
            self.logger.info(
                f"Estado de publicación - session_id: {session_id}, "
                f"streaming: {streaming}, publish_result: {publish_result}"
            )
            
            if streaming and session_id:
                # Obtener nombre del servidor
                server = await self._db_service.get_server_by_id(server_id)
                server_name = server['server_name'] if server else f'Server {server_id}'
                
                # Actualizar estado interno
                self._active_remote_streams[camera_id] = {
                    'server_id': server_id,
                    'server_name': server_name,
                    'remote_camera_id': publish_result.get('remote_camera_id'),
                    'publish_url': publish_url,
                    'webrtc_url': webrtc_url,
                    'session_id': session_id,
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
                # Si no se inició el streaming correctamente
                return {
                    'success': False,
                    'error': publish_result.get('message', 'No se pudo iniciar el streaming'),
                    'error_code': 'STREAMING_NOT_STARTED'
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
            
            # Detener proceso FFmpeg a través del publishing presenter
            stop_result = await self._publishing_presenter.unpublish_camera(camera_id)
            
            if stop_result.get('success', False):
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
                    'error': stop_result.get('error', 'Error deteniendo proceso FFmpeg'),
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
            
            # Obtener estado detallado del publishing presenter
            detailed_status = await self._publishing_presenter.get_publication_status(
                camera_id
            )
            
            # Por ahora, no intentar obtener información adicional de la cámara
            # para evitar problemas de importación
            
            # Obtener métricas del proceso FFmpeg si está disponible
            metrics = {'fps': 0, 'bitrate_kbps': 0, 'frames_sent': 0, 'viewers': 0}
            
            # Si tenemos session_id, intentar obtener métricas del stream service
            if 'session_id' in stream_info and stream_info['session_id']:
                try:
                    from services.publishing.stream_service import get_publishing_stream_service
                    stream_service = get_publishing_stream_service()
                    stream_metrics = await stream_service.get_stream_metrics(stream_info['session_id'])
                    
                    if stream_metrics and stream_metrics.get('metrics'):
                        metrics = {
                            'fps': stream_metrics['metrics'].get('fps', 0),
                            'bitrate_kbps': stream_metrics['metrics'].get('bitrate_kbps', 0),
                            'frames_sent': stream_metrics['metrics'].get('frames_sent', 0),
                            'viewers': 0  # TODO: Implementar viewers cuando esté disponible
                        }
                except Exception as e:
                    self.logger.debug(f"No se pudieron obtener métricas del stream: {str(e)}")
            
            return {
                'is_streaming': True,
                'stream_info': {
                    **stream_info,
                    'camera_name': stream_info.get('camera_name', camera_id),
                    'camera_ip': stream_info.get('camera_ip', ''),
                    'status': detailed_status.get('publication', {}).get('status', 'publishing') if detailed_status.get('publication') else 'publishing',
                    'duration': self._calculate_duration(stream_info['started_at'])
                },
                'metrics': metrics
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
        
        self.logger.info(
            f"list_remote_streams - Active streams en memoria: {len(self._active_remote_streams)}"
        )
        
        # No necesitamos el servicio de cámaras aquí
        
        for camera_id, stream_info in self._active_remote_streams.items():
            self.logger.debug(f"Procesando stream para cámara {camera_id}")
            if server_id is None or stream_info['server_id'] == server_id:
                status = await self.get_remote_stream_status(camera_id)
                self.logger.debug(f"Status obtenido para {camera_id}: is_streaming={status['is_streaming']}")
                if status['is_streaming'] and status['stream_info']:
                    # El stream_info ya incluye camera_name y camera_ip desde get_remote_stream_status
                    streams.append({
                        'camera_id': camera_id,
                        **status['stream_info'],
                        'metrics': status.get('metrics', {})
                    })
        
        self.logger.info(
            f"list_remote_streams devolviendo {len(streams)} streams"
        )
        
        # Debug: mostrar contenido de active_streams
        self.logger.debug(
            f"Active streams actual: {list(self._active_remote_streams.keys())}"
        )
        
        # Si no hay streams en memoria, intentar cargar desde BD
        if len(streams) == 0:
            self.logger.info("No hay streams en memoria, cargando desde BD...")
            await self._load_active_remote_streams()
            
            # Intentar de nuevo después de cargar
            streams = []
            for camera_id, stream_info in self._active_remote_streams.items():
                if server_id is None or stream_info['server_id'] == server_id:
                    status = await self.get_remote_stream_status(camera_id)
                    if status['is_streaming'] and status['stream_info']:
                        streams.append({
                            'camera_id': camera_id,
                            **status['stream_info'],
                            'metrics': status.get('metrics', {})
                        })
            
            self.logger.info(
                f"Después de cargar desde BD: {len(streams)} streams"
            )
        
        return streams
    
    def _calculate_duration(self, start_time: datetime) -> int:
        """
        Calcula duración en segundos desde el inicio.
        
        Args:
            start_time: Tiempo de inicio (datetime o string ISO)
            
        Returns:
            Duración en segundos
        """
        if not start_time:
            return 0
        
        # Convertir string a datetime si es necesario
        if isinstance(start_time, str):
            try:
                # Parsear fecha ISO con o sin timezone
                if 'T' in start_time:
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                self.logger.warning(f"Error parseando fecha {start_time}: {e}")
                return 0
            
        delta = datetime.utcnow() - start_time
        return int(delta.total_seconds())


# Instancia singleton
_presenter: Optional[MediaMTXRemotePublishingPresenter] = None


async def get_mediamtx_remote_publishing_presenter() -> MediaMTXRemotePublishingPresenter:
    """
    Obtiene la instancia singleton del presenter.
    
    Returns:
        MediaMTXRemotePublishingPresenter singleton inicializado
    """
    global _presenter
    
    if _presenter is None:
        _presenter = MediaMTXRemotePublishingPresenter()
        # Inicializar el presenter
        await _presenter.initialize()
        
    return _presenter