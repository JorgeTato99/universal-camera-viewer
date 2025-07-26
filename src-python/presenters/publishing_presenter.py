"""
Presenter para coordinar la publicación de streams a MediaMTX.

Implementa la lógica de negocio entre la vista (API/WebSocket) y
los servicios de publicación.
"""

from typing import Dict, List, Optional
import asyncio
import logging

from presenters.base_presenter import BasePresenter
from services.publishing import get_publisher_service, MediaMTXClient
from services.mediamtx_metrics_service import get_mediamtx_metrics_service
from services.publishing.viewer_analytics_service import get_viewer_analytics_service
from models.publishing import (
    PublishConfiguration, PublishResult, PublishStatus, PublisherProcess,
    PublishErrorType
)

logger = logging.getLogger(__name__)


class PublishingPresenter(BasePresenter):
    """
    Presenter para gestión de publicación a MediaMTX.
    
    Responsabilidades:
    - Coordinar servicios de publicación
    - Validar operaciones de negocio
    - Transformar datos para la vista
    - Emitir eventos por WebSocket
    """
    
    def __init__(self):
        """Inicializa el presenter."""
        super().__init__()
        self._config: Optional[PublishConfiguration] = None
        self._publisher_service = None
        self._mediamtx_client: Optional[MediaMTXClient] = None
        self._metrics_service = None
        self._viewer_service = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def _initialize_presenter(self) -> None:
        """
        Inicialización específica del presenter.
        Implementación requerida por BasePresenter.
        """
        # La inicialización real se hace en el método initialize()
        pass
    
    async def _cleanup_presenter(self) -> None:
        """
        Cleanup específico del presenter.
        Implementación requerida por BasePresenter.
        """
        # El cleanup real se hace en el método cleanup()
        await self.cleanup()
        
    async def initialize(self, config: PublishConfiguration) -> None:
        """
        Inicializa el presenter con configuración.
        
        Args:
            config: Configuración de publicación
            
        Raises:
            ServiceError: Si falla la inicialización de servicios
            ConnectionError: Si no se puede conectar con MediaMTX API
        """
        self.logger.info("Inicializando PublishingPresenter")
        
        try:
            self._config = config
            self._publisher_service = get_publisher_service(config)
            
            self.logger.debug(f"Configuración cargada: MediaMTX={config.mediamtx_url}, "
                           f"API habilitada={config.api_enabled}")
            
            # Conectar con MediaMTX API si está habilitada
            if config.api_enabled:
                api_url = config.get_api_url()
                self.logger.info(f"Conectando con MediaMTX API en {api_url}")
                self._mediamtx_client = MediaMTXClient(api_url)
                await self._mediamtx_client.connect()
                self.logger.info("Conexión con MediaMTX API establecida")
            else:
                self.logger.warning("MediaMTX API deshabilitada, funcionalidad limitada")
                
            # Inicializar servicio de publicación
            await self._publisher_service.initialize()
            
            # Inicializar servicio de métricas
            self._metrics_service = get_mediamtx_metrics_service()
            await self._metrics_service.initialize()
            self.logger.info("Servicio de métricas inicializado")
            
            # Inicializar servicio de viewers analytics
            self._viewer_service = get_viewer_analytics_service()
            await self._viewer_service.initialize()
            self.logger.info("Servicio de viewer analytics inicializado")
            
            self.logger.info("PublishingPresenter inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante inicialización: {e}")
            raise
        
    async def start_publishing(
        self,
        camera_id: str,
        force_restart: bool = False
    ) -> PublishResult:
        """
        Inicia publicación de una cámara.
        
        Coordina el inicio de publicación validando el estado actual,
        delegando al servicio y verificando el resultado en MediaMTX.
        
        Args:
            camera_id: ID de la cámara
            force_restart: Forzar reinicio si ya publica
            
        Returns:
            PublishResult con estado de la operación
            
        Raises:
            ValueError: Si camera_id es inválido
            ServiceError: Si falla el servicio de publicación
        """
        self.logger.info(f"Solicitando inicio de publicación para {camera_id} "
                        f"(force_restart={force_restart})")
        
        try:
            # Validar entrada
            if not camera_id or not camera_id.strip():
                raise ValueError("camera_id no puede estar vacío")
                
            # Validar estado actual
            if not force_restart and self._publisher_service.is_publishing(camera_id):
                self.logger.warning(f"Cámara {camera_id} ya está publicando, rechazando solicitud")
                return PublishResult(
                    success=False,
                    camera_id=camera_id,
                    error="La cámara ya está publicando",
                    error_type=PublishErrorType.ALREADY_PUBLISHING
                )
                
            # Delegar al servicio
            self.logger.debug(f"Delegando inicio de publicación al servicio para {camera_id}")
            result = await self._publisher_service.start_publishing(
                camera_id=camera_id,
                force_restart=force_restart
            )
            
            # Procesar resultado
            if result.success:
                self.logger.info(f"Publicación iniciada exitosamente para {camera_id}")
                
                # Emitir evento de éxito
                await self._emit_event("publishing_started", {
                    "camera_id": camera_id,
                    "publish_path": result.publish_path,
                    "process_id": result.process_id
                })
                
                # Iniciar recolección de métricas
                if self._metrics_service and self._config:
                    api_url = self._config.get_api_url() if self._config.api_enabled else None
                    if api_url and result.publish_path:
                        self.logger.info(f"Iniciando recolección de métricas para {camera_id}")
                        await self._metrics_service.start_metric_collection(
                            camera_id=camera_id,
                            mediamtx_api_url=api_url,
                            publish_path=result.publish_path.lstrip('/'),
                            interval_seconds=5.0
                        )
                
                # Iniciar tracking de viewers
                if self._viewer_service and result.publish_path:
                    try:
                        self.logger.info(f"Iniciando tracking de viewers para {camera_id}")
                        await self._viewer_service.start_tracking(
                            camera_id=camera_id,
                            publish_path=result.publish_path.lstrip('/')
                        )
                    except Exception as e:
                        self.logger.error(f"Error iniciando tracking de viewers: {e}")
                        # No fallar la publicación por error en viewers
                
                # Verificar en MediaMTX si está configurado
                if self._mediamtx_client and result.publish_path:
                    self.logger.debug(f"Programando verificación de path en MediaMTX para {camera_id}")
                    asyncio.create_task(
                        self._verify_path_active(camera_id, result.publish_path),
                        name=f"verify_path_{camera_id}"
                    )
            else:
                self.logger.error(f"Fallo al iniciar publicación para {camera_id}: {result.error}")
                
                # Emitir evento de error
                await self._emit_event("publishing_failed", {
                    "camera_id": camera_id,
                    "error": result.error,
                    "error_type": result.error_type
                })
                
            return result
            
        except ValueError as e:
            self.logger.error(f"Error de validación: {e}")
            return PublishResult(
                success=False,
                camera_id=camera_id,
                error=str(e),
                error_type=PublishErrorType.INVALID_INPUT
            )
        except Exception as e:
            self.logger.exception(f"Error inesperado iniciando publicación para {camera_id}")
            return PublishResult(
                success=False,
                camera_id=camera_id,
                error=f"Error interno: {str(e)}",
                error_type=PublishErrorType.UNKNOWN
            )
        
    async def stop_publishing(self, camera_id: str) -> bool:
        """
        Detiene publicación de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se detuvo exitosamente, False si no estaba publicando
            
        Raises:
            ValueError: Si camera_id es inválido
        """
        self.logger.info(f"Solicitando detención de publicación para {camera_id}")
        
        try:
            # Validar entrada
            if not camera_id or not camera_id.strip():
                raise ValueError("camera_id no puede estar vacío")
                
            # Verificar si está publicando
            if not self._publisher_service.is_publishing(camera_id):
                self.logger.warning(f"Cámara {camera_id} no está publicando")
                return False
                
            # Delegar al servicio
            success = await self._publisher_service.stop_publishing(camera_id)
            
            if success:
                self.logger.info(f"Publicación detenida exitosamente para {camera_id}")
                
                # Detener recolección de métricas
                if self._metrics_service:
                    await self._metrics_service.stop_metric_collection(camera_id)
                    self.logger.info(f"Recolección de métricas detenida para {camera_id}")
                
                # Detener tracking de viewers
                if self._viewer_service:
                    await self._viewer_service.stop_tracking(camera_id)
                    self.logger.info(f"Tracking de viewers detenido para {camera_id}")
                
                await self._emit_event("publishing_stopped", {
                    "camera_id": camera_id
                })
            else:
                self.logger.error(f"Fallo al detener publicación para {camera_id}")
                await self._emit_event("publishing_stop_failed", {
                    "camera_id": camera_id
                })
                
            return success
            
        except ValueError as e:
            self.logger.error(f"Error de validación: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"Error inesperado deteniendo publicación para {camera_id}")
            return False
        
    async def get_camera_status(
        self,
        camera_id: str
    ) -> Optional[PublisherProcess]:
        """Obtiene estado de publicación de una cámara."""
        if not self._publisher_service:
            return None
        return self._publisher_service.get_camera_status(camera_id)
        
    async def get_all_status(self) -> Dict[str, PublisherProcess]:
        """Obtiene estado de todas las publicaciones."""
        if not self._publisher_service:
            # Si el servicio aún no está inicializado, retornar diccionario vacío
            return {}
        return self._publisher_service.get_publishing_status()
        
    async def get_active_count(self) -> int:
        """Obtiene el número de publicaciones activas."""
        if not self._publisher_service:
            return 0
        all_status = self._publisher_service.get_publishing_status()
        return sum(1 for p in all_status.values() if p.is_active)
    
    async def get_active_publications(self) -> List[Dict]:
        """
        Obtiene las publicaciones activas en el servidor MediaMTX local.
        
        Returns:
            Lista de publicaciones activas con información detallada
        """
        try:
            # Obtener estado de todas las publicaciones
            if not self._publisher_service:
                return []
            all_status = self._publisher_service.get_publishing_status()
            
            active_publications = []
            
            for camera_id, process_info in all_status.items():
                if process_info.is_active:
                    # Obtener métricas si están disponibles
                    metrics = None
                    if self._metrics_service:
                        try:
                            latest_metrics = await self._metrics_service.get_latest_metrics(camera_id)
                            if latest_metrics:
                                metrics = {
                                    'fps': latest_metrics.get('fps', 0),
                                    'bitrate_kbps': latest_metrics.get('bitrate_kbps', 0),
                                    'viewers': latest_metrics.get('readers', 0),
                                    'uptime_seconds': latest_metrics.get('uptime_seconds', 0)
                                }
                        except Exception as e:
                            self.logger.warning(f"Error obteniendo métricas para {camera_id}: {e}")
                    
                    # Obtener información de viewers
                    viewer_info = None
                    if self._viewer_service:
                        try:
                            viewer_data = await self._viewer_service.get_current_viewers(camera_id)
                            if viewer_data:
                                viewer_info = {
                                    'current': viewer_data.get('current_viewers', 0),
                                    'peak': viewer_data.get('peak_viewers', 0),
                                    'total_sessions': viewer_data.get('total_sessions', 0)
                                }
                        except Exception as e:
                            self.logger.warning(f"Error obteniendo viewers para {camera_id}: {e}")
                    
                    # Por ahora usar valores por defecto para evitar problemas de importación
                    camera_name = camera_id
                    camera_ip = ''
                    
                    publication = {
                        'publication_id': process_info.process_id,  # Usar PID como ID temporal
                        'camera_id': camera_id,
                        'camera_name': camera_name,
                        'camera_ip': camera_ip,
                        'publish_path': process_info.publish_path or f"ucv_{camera_id}",
                        'status': process_info.status.value,
                        'start_time': process_info.started_at.isoformat() if process_info.started_at else None,
                        'process_pid': process_info.process_id,
                        'error_count': process_info.error_count,
                        'last_error': process_info.last_error,
                        'metrics': metrics,
                        'viewer_info': viewer_info,
                        'server_type': 'local',  # Indicar que es del servidor local
                        'server_name': 'Local MediaMTX'
                    }
                    
                    active_publications.append(publication)
            
            self.logger.info(f"Obtenidas {len(active_publications)} publicaciones locales activas")
            return active_publications
            
        except Exception as e:
            self.logger.error(f"Error obteniendo publicaciones activas: {e}")
            return []
        
    async def _verify_path_active(
        self,
        camera_id: str,
        path: str
    ) -> None:
        """
        Verifica que un path esté activo en MediaMTX.
        
        Espera hasta 10 segundos para que el path se active y emite
        eventos según el resultado.
        
        Args:
            camera_id: ID de la cámara
            path: Path a verificar en MediaMTX
        """
        self.logger.debug(f"Iniciando verificación de path {path} para cámara {camera_id}")
        
        try:
            # Normalizar path
            path_name = path.lstrip('/')
            
            # Esperar activación con timeout
            self.logger.debug(f"Esperando activación de path {path_name} (máx 10s)")
            is_active = await self._mediamtx_client.wait_for_path(
                path_name,
                timeout=10.0
            )
            
            if is_active:
                self.logger.info(f"Path {path_name} verificado activo para {camera_id}")
                await self._emit_event("path_verified", {
                    "camera_id": camera_id,
                    "path": path,
                    "active": True
                })
            else:
                self.logger.warning(f"Path {path_name} no se activó después de 10s para {camera_id}")
                await self._emit_event("path_verification_failed", {
                    "camera_id": camera_id,
                    "path": path,
                    "error": "Path no activo después de 10 segundos"
                })
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout verificando path {path} para {camera_id}")
            await self._emit_event("path_verification_timeout", {
                "camera_id": camera_id,
                "path": path
            })
        except Exception as e:
            self.logger.exception(f"Error inesperado verificando path {path} para {camera_id}")
            await self._emit_event("path_verification_error", {
                "camera_id": camera_id,
                "path": path,
                "error": str(e)
            })
            
    async def _emit_event(self, event_type: str, data: Dict) -> None:
        """Emite evento por WebSocket."""
        try:
            # Importar dinámicamente para evitar dependencias circulares
            from websocket.handlers.publishing_handler import get_publishing_ws_handler
            
            handler = get_publishing_ws_handler()
            await handler.emit_publishing_event(event_type, data)
            
        except ImportError:
            # Si el handler no está disponible, solo loguear
            self.logger.debug(f"WebSocket handler no disponible. Evento: {event_type} - {data}")
        except Exception as e:
            self.logger.error(f"Error emitiendo evento {event_type}: {e}")
        
    async def cleanup(self) -> None:
        """
        Limpia recursos del presenter.
        
        Debe llamarse durante el shutdown de la aplicación para
        liberar correctamente todos los recursos.
        """
        self.logger.info("Iniciando limpieza de PublishingPresenter")
        
        try:
            # Cerrar cliente MediaMTX
            if self._mediamtx_client:
                self.logger.debug("Cerrando conexión con MediaMTX API")
                await self._mediamtx_client.close()
                self._mediamtx_client = None
                
            # Limpiar servicio de métricas
            if self._metrics_service:
                self.logger.debug("Limpiando servicio de métricas")
                await self._metrics_service.shutdown()
                self._metrics_service = None
                
            # Limpiar servicio de publicación
            if self._publisher_service:
                self.logger.debug("Limpiando servicio de publicación")
                await self._publisher_service.cleanup()
                
            self.logger.info("PublishingPresenter limpiado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante limpieza: {e}")
            # No re-lanzar para permitir shutdown graceful


# Instancia singleton
_presenter: Optional[PublishingPresenter] = None


async def get_publishing_presenter() -> PublishingPresenter:
    """Obtiene instancia del presenter."""
    global _presenter
    
    if _presenter is None:
        _presenter = PublishingPresenter()
        
        # Cargar configuración desde DB
        from services.database import get_publishing_db_service
        
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        # Obtener configuración activa
        config_data = await db_service.get_active_configuration()
        
        if not config_data:
            # Usar configuración por defecto si no hay ninguna en BD
            logger.warning("No hay configuración activa en BD, usando valores por defecto")
            config = PublishConfiguration(
                mediamtx_url="rtsp://localhost:8554",
                api_port=9997,
                api_enabled=True,
                max_reconnects=3,
                reconnect_delay=5
            )
            
            # Guardar configuración por defecto
            await db_service.save_configuration(
                config,
                name="Default Configuration",
                set_active=True,
                created_by="system"
            )
        else:
            # Extraer configuración del resultado
            config = config_data['config']
            
        await _presenter.initialize(config)
        
    return _presenter