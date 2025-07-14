"""
Presenter para streaming de video adaptado para Tauri.

Coordina entre los servicios de streaming y el frontend Tauri,
emitiendo eventos que el frontend JavaScript/TypeScript puede capturar.
"""

import asyncio
import logging
from typing import Dict, Optional, Set, Any, Callable
from datetime import datetime

from presenters.base_presenter import BasePresenter
from services.video import VideoStreamService
from models.streaming import StreamModel, StreamStatus, StreamProtocol
from models import ConnectionConfig
from presenters.streaming.tauri_event_emitter import TauriEventEmitter, EventEmitter


class VideoStreamPresenter(BasePresenter):
    """
    Presenter específico para streaming de video.
    
    Implementa el patrón Observer emitiendo eventos Tauri
    que el frontend puede escuchar.
    """
    
    def __init__(
        self,
        video_service: Optional[VideoStreamService] = None,
        event_emitter: Optional[EventEmitter] = None
    ):
        """
        Inicializa el presenter.
        
        Args:
            video_service: Servicio de video (usa singleton si no se proporciona)
            event_emitter: Emisor de eventos (usa TauriEventEmitter por defecto)
        """
        super().__init__()
        
        # Servicios
        self._video_service = video_service or VideoStreamService()
        self._event_emitter = event_emitter or TauriEventEmitter()
        
        # Estado del presenter
        self._active_streams: Dict[str, StreamModel] = {}
        self._stream_subscriptions: Set[str] = set()
        
        # Control de métricas
        self._metrics_interval = 1.0  # Enviar métricas cada segundo
        self._metrics_tasks: Dict[str, asyncio.Task] = {}
    
    async def _initialize_presenter(self) -> None:
        """Inicialización específica del presenter."""
        self.logger.info("VideoStreamPresenter inicializado para Tauri")
        
        # Emitir evento de inicialización
        await self._event_emitter.emit('presenter-ready', {
            'presenter': 'VideoStreamPresenter',
            'capabilities': {
                'protocols': ['rtsp', 'onvif', 'http'],
                'maxStreams': 16,
                'features': ['motion-detection', 'recording', 'snapshot']
            }
        })
    
    async def _cleanup_presenter(self) -> None:
        """Cleanup específico del presenter."""
        # Detener todos los streams
        await self.stop_all_streams()
        
        # Cancelar tareas de métricas
        for task in self._metrics_tasks.values():
            if not task.done():
                task.cancel()
        
        # Esperar que terminen
        if self._metrics_tasks:
            await asyncio.gather(*self._metrics_tasks.values(), return_exceptions=True)
        
        self._metrics_tasks.clear()
        
        self.logger.info("VideoStreamPresenter cleanup completado")
    
    # === MANEJO DE ACCIONES ===
    
    async def _handle_view_action(self, action: str, params: Dict[str, Any]) -> None:
        """
        Maneja acciones desde el frontend Tauri.
        
        Args:
            action: Nombre de la acción
            params: Parámetros de la acción
        """
        try:
            if action == "start_stream":
                await self._start_stream_action(params)
            elif action == "stop_stream":
                await self._stop_stream_action(params)
            elif action == "stop_all_streams":
                await self.stop_all_streams()
            elif action == "get_stream_status":
                await self._get_stream_status_action(params)
            elif action == "capture_snapshot":
                await self._capture_snapshot_action(params)
            else:
                self.logger.warning(f"Acción no reconocida: {action}")
                
        except Exception as e:
            await self._handle_action_error(action, params, e)
    
    # === OPERACIONES DE STREAMING ===
    
    async def start_camera_stream(
        self,
        camera_id: str,
        connection_config: ConnectionConfig,
        protocol: StreamProtocol = StreamProtocol.RTSP,
        options: Optional[Dict[str, Any]] = None,
        on_frame_callback: Optional[Callable[[str, str], None]] = None
    ) -> bool:
        """
        Inicia streaming para una cámara.
        
        Args:
            camera_id: ID de la cámara
            connection_config: Configuración de conexión
            protocol: Protocolo a usar
            options: Opciones adicionales (fps, quality, etc)
            
        Returns:
            True si se inició exitosamente
        """
        try:
            # Notificar inicio
            await self._event_emitter.emit_stream_status(
                camera_id, 
                'connecting',
                {'protocol': protocol.value}
            )
            
            # Configurar opciones
            target_fps = options.get('targetFps', 30) if options else 30
            buffer_size = options.get('bufferSize', 5) if options else 5
            
            # Usar callback externo si se proporciona, sino usar el interno
            frame_callback = on_frame_callback or self._on_frame_received
            
            # Iniciar stream con callback
            stream_model = await self._video_service.start_stream(
                camera_id=camera_id,
                connection_config=connection_config,
                protocol=protocol,
                on_frame_callback=frame_callback,
                target_fps=target_fps,
                buffer_size=buffer_size
            )
            
            # Guardar referencia
            self._active_streams[camera_id] = stream_model
            self._stream_subscriptions.add(camera_id)
            
            # Iniciar tarea de métricas
            self._start_metrics_task(camera_id)
            
            # Notificar éxito
            await self._event_emitter.emit_stream_status(
                camera_id,
                'connected',
                {
                    'streamId': stream_model.stream_id,
                    'protocol': protocol.value,
                    'metadata': stream_model.metadata
                }
            )
            
            self.logger.info(f"Stream iniciado para cámara {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando stream para {camera_id}: {e}")
            
            # Notificar error
            await self._event_emitter.emit_error(
                camera_id,
                'connection_failed',
                str(e)
            )
            
            # Limpiar
            self._active_streams.pop(camera_id, None)
            self._stream_subscriptions.discard(camera_id)
            
            return False
    
    async def stop_camera_stream(self, camera_id: str) -> bool:
        """
        Detiene el streaming de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se detuvo exitosamente
        """
        try:
            # Verificar si está activo
            if camera_id not in self._active_streams:
                self.logger.warning(f"No hay stream activo para {camera_id}")
                return False
            
            # Cancelar tarea de métricas
            self._stop_metrics_task(camera_id)
            
            # Detener stream
            success = await self._video_service.stop_stream(camera_id)
            
            if success:
                # Limpiar referencias
                self._active_streams.pop(camera_id, None)
                self._stream_subscriptions.discard(camera_id)
                
                # Notificar
                await self._event_emitter.emit_stream_status(
                    camera_id,
                    'disconnected',
                    {'reason': 'user_requested'}
                )
                
                self.logger.info(f"Stream detenido para cámara {camera_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deteniendo stream para {camera_id}: {e}")
            return False
    
    async def stop_all_streams(self) -> None:
        """Detiene todos los streams activos."""
        camera_ids = list(self._active_streams.keys())
        
        for camera_id in camera_ids:
            await self.stop_camera_stream(camera_id)
        
        self.logger.info("Todos los streams detenidos")
    
    # === CALLBACKS DE FRAMES ===
    
    def _on_frame_received(self, camera_id: str, frame_base64: str) -> None:
        """
        Callback cuando se recibe un frame.
        
        Args:
            camera_id: ID de la cámara
            frame_base64: Frame en base64
        """
        # Verificar suscripción
        if camera_id not in self._stream_subscriptions:
            return
        
        # Emitir frame de forma async
        asyncio.create_task(
            self._emit_frame_update(camera_id, frame_base64)
        )
    
    async def _emit_frame_update(self, camera_id: str, frame_base64: str) -> None:
        """Emite actualización de frame a Tauri."""
        try:
            await self._event_emitter.emit_frame_update(camera_id, frame_base64)
        except Exception as e:
            self.logger.error(f"Error emitiendo frame para {camera_id}: {e}")
    
    # === TAREAS DE MÉTRICAS ===
    
    def _start_metrics_task(self, camera_id: str) -> None:
        """Inicia tarea periódica de métricas."""
        if camera_id in self._metrics_tasks:
            return
        
        task = asyncio.create_task(
            self._metrics_loop(camera_id),
            name=f"metrics_{camera_id}"
        )
        self._metrics_tasks[camera_id] = task
    
    def _stop_metrics_task(self, camera_id: str) -> None:
        """Detiene tarea de métricas."""
        task = self._metrics_tasks.pop(camera_id, None)
        if task and not task.done():
            task.cancel()
    
    async def _metrics_loop(self, camera_id: str) -> None:
        """Loop que envía métricas periódicamente."""
        while camera_id in self._active_streams:
            try:
                # Obtener métricas
                metrics = self._video_service.get_stream_metrics(camera_id)
                
                if metrics:
                    # Emitir métricas
                    await self._event_emitter.emit_stream_metrics(
                        camera_id,
                        metrics
                    )
                
                # Esperar intervalo
                await asyncio.sleep(self._metrics_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en loop de métricas para {camera_id}: {e}")
                await asyncio.sleep(self._metrics_interval)
    
    # === ACCIONES ESPECÍFICAS ===
    
    async def _start_stream_action(self, params: Dict[str, Any]) -> None:
        """Maneja acción de iniciar stream."""
        camera_id = params.get('cameraId')
        if not camera_id:
            raise ValueError("cameraId es requerido")
        
        # Crear configuración desde params
        config = ConnectionConfig(
            ip=params.get('ip', ''),
            port=params.get('port'),
            username=params.get('username', ''),
            password=params.get('password', ''),
            timeout=params.get('timeout', 10.0)
        )
        
        # Protocolo
        protocol_str = params.get('protocol', 'rtsp').lower()
        protocol = StreamProtocol(protocol_str)
        
        # Opciones
        options = params.get('options', {})
        
        # Iniciar stream
        await self.start_camera_stream(camera_id, config, protocol, options)
    
    async def _stop_stream_action(self, params: Dict[str, Any]) -> None:
        """Maneja acción de detener stream."""
        camera_id = params.get('cameraId')
        if not camera_id:
            raise ValueError("cameraId es requerido")
        
        await self.stop_camera_stream(camera_id)
    
    async def _get_stream_status_action(self, params: Dict[str, Any]) -> None:
        """Obtiene y emite el estado de un stream."""
        camera_id = params.get('cameraId')
        if not camera_id:
            raise ValueError("cameraId es requerido")
        
        stream_model = self._active_streams.get(camera_id)
        
        if stream_model:
            await self._event_emitter.emit('stream-status-response', {
                'cameraId': camera_id,
                'status': stream_model.status.value,
                'metrics': stream_model.to_dict()
            })
        else:
            await self._event_emitter.emit('stream-status-response', {
                'cameraId': camera_id,
                'status': 'not_found'
            })
    
    async def _capture_snapshot_action(self, params: Dict[str, Any]) -> None:
        """Captura un snapshot del stream actual."""
        camera_id = params.get('cameraId')
        if not camera_id:
            raise ValueError("cameraId es requerido")
        
        # TODO: Implementar captura de snapshot
        self.logger.warning("Captura de snapshot no implementada aún")
    
    async def _handle_action_error(self, action: str, params: Dict[str, Any], error: Exception) -> None:
        """Maneja errores en acciones."""
        self.logger.error(f"Error en acción {action}: {error}")
        
        await self._event_emitter.emit_error(
            params.get('cameraId', 'unknown'),
            'action_error',
            str(error)
        )
    
    # === MÉTODOS DE COMPATIBILIDAD PARA STREAMHANDLER ===
    
    async def connect_camera(self, config: ConnectionConfig) -> bool:
        """
        Conecta a una cámara (wrapper para compatibilidad).
        
        Args:
            config: Configuración de conexión
            
        Returns:
            True si la conexión fue exitosa
        """
        try:
            # Generar camera_id desde la IP
            camera_id = f"cam_{config.ip.replace('.', '_')}"
            
            # Determinar protocolo
            protocol = config.protocol if hasattr(config, 'protocol') else StreamProtocol.RTSP
            
            # Iniciar stream
            success = await self.start_camera_stream(
                camera_id=camera_id,
                connection_config=config,
                protocol=protocol,
                options={
                    'targetFps': 30,
                    'bufferSize': 5
                }
            )
            
            # Guardar configuración para uso posterior
            if success:
                self._current_camera_id = camera_id
                self._current_config = config
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error conectando cámara: {e}")
            return False
    
    async def start_streaming(self) -> None:
        """
        Inicia el streaming (compatibilidad con StreamHandler).
        El streaming ya se inicia en connect_camera, así que este método
        solo verifica el estado.
        """
        if hasattr(self, '_current_camera_id') and self._current_camera_id:
            stream = self._active_streams.get(self._current_camera_id)
            if stream and stream.status == StreamStatus.STREAMING:
                self.logger.info(f"Streaming ya activo para {self._current_camera_id}")
            else:
                self.logger.warning("Stream no está activo")
        else:
            raise RuntimeError("No hay cámara conectada")
    
    async def stop_streaming(self) -> None:
        """
        Detiene el streaming actual (compatibilidad).
        """
        if hasattr(self, '_current_camera_id') and self._current_camera_id:
            await self.stop_camera_stream(self._current_camera_id)
    
    async def disconnect_camera(self) -> None:
        """
        Desconecta la cámara actual (compatibilidad).
        """
        if hasattr(self, '_current_camera_id') and self._current_camera_id:
            # Detener stream si está activo
            if self._current_camera_id in self._active_streams:
                await self.stop_camera_stream(self._current_camera_id)
            
            # Limpiar referencias
            self._current_camera_id = None
            self._current_config = None
    
    @property
    def on_frame_update(self):
        """Getter para callback de frames."""
        return getattr(self, '_on_frame_callback', None)
    
    @on_frame_update.setter
    def on_frame_update(self, callback):
        """
        Setter para callback de frames (compatibilidad).
        
        Args:
            callback: Función async que recibe bytes del frame
        """
        self._on_frame_callback = callback
        
        # Configurar el callback en el servicio
        if hasattr(self, '_current_camera_id') and self._current_camera_id:
            self._video_service.set_frame_callback(
                self._current_camera_id,
                callback
            )
    
    @property
    def is_streaming(self) -> bool:
        """Verifica si hay streaming activo."""
        if hasattr(self, '_current_camera_id') and self._current_camera_id:
            stream = self._active_streams.get(self._current_camera_id)
            return stream and stream.status == StreamStatus.STREAMING
        return False
    
    # === MÉTODOS DE UTILIDAD ===
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene información de todos los streams activos.
        
        Returns:
            Diccionario con información de streams
        """
        return {
            camera_id: stream.to_dict()
            for camera_id, stream in self._active_streams.items()
        }
    
    def is_streaming(self, camera_id: str) -> bool:
        """Verifica si una cámara está transmitiendo."""
        return camera_id in self._active_streams
    
    async def update_stream_options(self, camera_id: str, options: Dict[str, Any]) -> bool:
        """
        Actualiza opciones de un stream activo.
        
        Args:
            camera_id: ID de la cámara
            options: Nuevas opciones
            
        Returns:
            True si se actualizó exitosamente
        """
        # TODO: Implementar actualización dinámica de opciones
        self.logger.warning("Actualización de opciones no implementada aún")
        return False