"""
Servicio singleton para gestión central de streams de video.

Coordina todos los streams activos y proporciona una interfaz
unificada para el control de streaming.
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, List, Any
from datetime import datetime
import uuid

from services.base_service import BaseService
from models.streaming import StreamModel, StreamStatus, StreamProtocol
from models import ConnectionConfig
from utils.video import FrameConverter, Base64JPEGStrategy
from utils.video.performance_monitor import StreamPerformanceMonitor
from services.video.stream_manager import StreamManagerFactory, StreamManager


class VideoStreamService(BaseService):
    """
    Servicio singleton para gestión de streams de video.
    
    Implementa el patrón Singleton para asegurar una única instancia
    que gestione todos los streams de la aplicación.
    """
    
    _instance: Optional['VideoStreamService'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'VideoStreamService':
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio (solo se ejecuta una vez)."""
        if not VideoStreamService._initialized:
            super().__init__()
            
            # Gestión de streams
            self._active_streams: Dict[str, StreamManager] = {}
            self._stream_models: Dict[str, StreamModel] = {}
            
            # Callbacks para notificar frames
            self._frame_callbacks: Dict[str, List[Callable]] = {}
            
            # Conversión de frames
            self._frame_converter = FrameConverter(Base64JPEGStrategy())
            
            # Monitor de performance
            self._performance_monitor = StreamPerformanceMonitor()
            
            # Control de tareas async
            self._tasks: Dict[str, asyncio.Task] = {}
            
            # Factory para crear stream managers
            self._manager_factory = StreamManagerFactory()
            
            VideoStreamService._initialized = True
            self.logger.info("VideoStreamService inicializado (Singleton)")
    
    async def start_stream(
        self,
        camera_id: str,
        connection_config: ConnectionConfig,
        protocol: StreamProtocol = StreamProtocol.RTSP,
        on_frame_callback: Optional[Callable[[str, str], None]] = None,
        target_fps: int = 30,
        buffer_size: int = 5
    ) -> StreamModel:
        """
        Inicia un nuevo stream de video.
        
        Args:
            camera_id: ID de la cámara
            connection_config: Configuración de conexión
            protocol: Protocolo a utilizar
            on_frame_callback: Callback para notificar frames (camera_id, frame_base64)
            target_fps: FPS objetivo
            buffer_size: Tamaño del buffer de frames
            
        Returns:
            StreamModel con información del stream iniciado
            
        Raises:
            ValueError: Si ya existe un stream activo para la cámara
        """
        if camera_id in self._active_streams:
            existing = self._stream_models.get(camera_id)
            if existing and existing.is_active():
                raise ValueError(f"Ya existe un stream activo para la cámara {camera_id}")
        
        try:
            # Crear modelo de stream
            stream_model = StreamModel(
                camera_id=camera_id,
                protocol=protocol,
                target_fps=target_fps,
                buffer_size=buffer_size
            )
            stream_model.start()
            
            # Registrar callback si se proporciona
            if on_frame_callback:
                self.add_frame_callback(camera_id, on_frame_callback)
            
            # Crear stream manager específico según protocolo
            stream_manager = self._manager_factory.create_stream_manager(
                protocol=protocol,
                stream_model=stream_model,
                connection_config=connection_config,
                frame_converter=self._frame_converter
            )
            
            # Configurar callback interno para recibir frames
            stream_manager.set_frame_callback(self._on_frame_received)
            
            # Guardar referencias
            self._active_streams[camera_id] = stream_manager
            self._stream_models[camera_id] = stream_model
            
            # Registrar en monitor de performance
            self._performance_monitor.register_stream(stream_model.stream_id)
            
            # Iniciar streaming en tarea async
            task = asyncio.create_task(
                self._run_stream(camera_id, stream_manager),
                name=f"stream_{camera_id}"
            )
            self._tasks[camera_id] = task
            
            self.logger.info(f"Stream iniciado para cámara {camera_id} con protocolo {protocol.value}")
            
            return stream_model
            
        except Exception as e:
            # Limpiar en caso de error
            await self._cleanup_stream(camera_id)
            self.logger.error(f"Error iniciando stream para cámara {camera_id}: {e}")
            raise
    
    async def stop_stream(self, camera_id: str) -> bool:
        """
        Detiene un stream activo.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se detuvo exitosamente
        """
        if camera_id not in self._active_streams:
            self.logger.warning(f"No hay stream activo para cámara {camera_id}")
            return False
        
        try:
            # Cancelar tarea async
            if camera_id in self._tasks:
                task = self._tasks[camera_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Detener stream manager
            stream_manager = self._active_streams.get(camera_id)
            if stream_manager:
                await stream_manager.stop()
            
            # Actualizar modelo
            stream_model = self._stream_models.get(camera_id)
            if stream_model:
                stream_model.stop()
            
            # Limpiar referencias
            await self._cleanup_stream(camera_id)
            
            self.logger.info(f"Stream detenido para cámara {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo stream para cámara {camera_id}: {e}")
            return False
    
    async def stop_all_streams(self) -> None:
        """Detiene todos los streams activos."""
        camera_ids = list(self._active_streams.keys())
        
        for camera_id in camera_ids:
            await self.stop_stream(camera_id)
        
        self.logger.info("Todos los streams han sido detenidos")
    
    def add_frame_callback(self, camera_id: str, callback: Callable[[str, str], None]) -> None:
        """
        Agrega un callback para recibir frames de una cámara.
        
        Args:
            camera_id: ID de la cámara
            callback: Función a llamar con (camera_id, frame_base64)
        """
        if camera_id not in self._frame_callbacks:
            self._frame_callbacks[camera_id] = []
        
        if callback not in self._frame_callbacks[camera_id]:
            self._frame_callbacks[camera_id].append(callback)
            self.logger.debug(f"Callback agregado para cámara {camera_id}")
    
    def remove_frame_callback(self, camera_id: str, callback: Callable[[str, str], None]) -> None:
        """
        Remueve un callback de frames.
        
        Args:
            camera_id: ID de la cámara
            callback: Callback a remover
        """
        if camera_id in self._frame_callbacks:
            callbacks = self._frame_callbacks[camera_id]
            if callback in callbacks:
                callbacks.remove(callback)
                self.logger.debug(f"Callback removido para cámara {camera_id}")
    
    def get_stream_model(self, camera_id: str) -> Optional[StreamModel]:
        """Obtiene el modelo de stream para una cámara."""
        return self._stream_models.get(camera_id)
    
    def get_active_streams(self) -> Dict[str, StreamModel]:
        """Obtiene todos los streams activos."""
        return {
            camera_id: model
            for camera_id, model in self._stream_models.items()
            if model.is_active()
        }
    
    def get_stream_metrics(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas de un stream específico.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Diccionario con métricas o None si no existe
        """
        stream_model = self._stream_models.get(camera_id)
        if not stream_model:
            return None
        
        return {
            'stream_id': stream_model.stream_id,
            'status': stream_model.status.value,
            'fps': stream_model.fps,
            'frame_count': stream_model.frame_count,
            'dropped_frames': stream_model.dropped_frames,
            'uptime_seconds': stream_model.get_uptime_seconds(),
            'error_message': stream_model.error_message
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas globales de performance."""
        return self._performance_monitor.get_current_metrics()
    
    async def _run_stream(self, camera_id: str, stream_manager: StreamManager) -> None:
        """
        Ejecuta el loop de streaming para una cámara.
        
        Args:
            camera_id: ID de la cámara
            stream_manager: Manager del stream
        """
        try:
            # Iniciar el streaming
            await stream_manager.start_streaming()
            
        except asyncio.CancelledError:
            self.logger.info(f"Stream cancelado para cámara {camera_id}")
            raise
            
        except Exception as e:
            self.logger.error(f"Error en stream de cámara {camera_id}: {e}")
            
            # Actualizar modelo con error
            stream_model = self._stream_models.get(camera_id)
            if stream_model:
                stream_model.mark_error(str(e))
            
            # Notificar error a callbacks
            await self._notify_stream_error(camera_id, str(e))
            
        finally:
            # Asegurar limpieza
            await stream_manager.stop()
    
    def _on_frame_received(self, camera_id: str, frame_data: str) -> None:
        """
        Callback interno cuando se recibe un frame.
        
        Args:
            camera_id: ID de la cámara
            frame_data: Frame en base64
        """
        # Actualizar modelo
        stream_model = self._stream_models.get(camera_id)
        if stream_model:
            stream_model.update_frame()
            
            # Actualizar métricas de performance
            self._performance_monitor.update_stream_metrics(
                stream_model.stream_id,
                fps=stream_model.calculate_fps(),
                frames=1
            )
        
        # Notificar a callbacks registrados
        callbacks = self._frame_callbacks.get(camera_id, [])
        for callback in callbacks:
            try:
                callback(camera_id, frame_data)
            except Exception as e:
                self.logger.error(f"Error en callback de frame: {e}")
    
    async def _cleanup_stream(self, camera_id: str) -> None:
        """Limpia recursos de un stream."""
        # Remover de estructuras
        self._active_streams.pop(camera_id, None)
        self._tasks.pop(camera_id, None)
        
        # Desregistrar del monitor
        stream_model = self._stream_models.get(camera_id)
        if stream_model:
            self._performance_monitor.unregister_stream(stream_model.stream_id)
        
        # Limpiar callbacks
        self._frame_callbacks.pop(camera_id, None)
    
    async def _notify_stream_error(self, camera_id: str, error_message: str) -> None:
        """Notifica error a callbacks con frame de error."""
        # TODO: Generar frame de error visual
        error_frame = f"ERROR:{error_message}"
        
        callbacks = self._frame_callbacks.get(camera_id, [])
        for callback in callbacks:
            try:
                callback(camera_id, error_frame)
            except Exception as e:
                self.logger.error(f"Error notificando error de stream: {e}")
    
    async def cleanup(self) -> None:
        """Limpieza completa del servicio."""
        await self.stop_all_streams()
        self._performance_monitor.stop_monitoring()
        
        # Reset singleton
        VideoStreamService._instance = None
        VideoStreamService._initialized = False