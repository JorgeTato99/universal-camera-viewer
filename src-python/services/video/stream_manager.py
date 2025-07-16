"""
Stream Manager con patrón Template Method y Factory.

Gestiona streams individuales con diferentes implementaciones
según el protocolo utilizado.
"""

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Dict
import numpy as np
import logging
from datetime import datetime

from models.streaming import StreamModel, StreamProtocol, StreamStatus
from models import ConnectionConfig
from utils.video import FrameConverter


class StreamManager(ABC):
    """
    Clase base abstracta para gestión de streams.
    
    Implementa el patrón Template Method definiendo el flujo
    general de streaming mientras permite personalización
    en las subclases.
    """
    
    def __init__(
        self,
        stream_model: StreamModel,
        connection_config: ConnectionConfig,
        frame_converter: FrameConverter
    ):
        """
        Inicializa el stream manager.
        
        Args:
            stream_model: Modelo del stream
            connection_config: Configuración de conexión
            frame_converter: Convertidor de frames
        """
        self.stream_model = stream_model
        self.connection_config = connection_config
        self.frame_converter = frame_converter
        
        # Control de streaming
        self._is_streaming = False
        self._capture_thread: Optional[threading.Thread] = None
        self._frame_queue: asyncio.Queue = asyncio.Queue(maxsize=stream_model.buffer_size)
        
        # Callback para notificar frames
        self._frame_callback: Optional[Callable[[str, str], None]] = None
        
        # Recursos específicos del protocolo
        self._connection: Any = None
        
        # Guardar referencia al event loop principal
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            self.logger.warning("No se pudo obtener el event loop actual")
        else:
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def set_frame_callback(self, callback: Callable[[str, str], None]) -> None:
        """Establece el callback para notificar frames."""
        self._frame_callback = callback
    
    async def start_streaming(self) -> None:
        """
        Template method para iniciar streaming.
        
        Define el flujo general mientras permite personalización
        en métodos abstractos.
        """
        try:
            # 1. Inicializar conexión específica
            await self._initialize_connection()
            
            # 2. Validar que el stream es válido
            await self._validate_stream()
            
            # 3. Iniciar captura en thread separado
            self._is_streaming = True
            self._start_capture_thread()
            
            # 4. Iniciar loop de procesamiento async
            await self._processing_loop()
            
        except Exception as e:
            self.logger.error(f"Error en streaming: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Detiene el streaming y libera recursos."""
        self._is_streaming = False
        
        # Detener thread de captura
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=5.0)
        
        # Limpiar cola
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Cerrar conexión específica
        await self._close_connection()
        
        self.logger.info(f"Stream detenido para {self.stream_model.camera_id}")
    
    @abstractmethod
    async def _initialize_connection(self) -> None:
        """Inicializa la conexión específica del protocolo."""
        pass
    
    @abstractmethod
    async def _validate_stream(self) -> None:
        """Valida que el stream está disponible y es válido."""
        pass
    
    @abstractmethod
    def _capture_frame(self) -> Optional[np.ndarray]:
        """
        Captura un frame del stream.
        
        Returns:
            Frame como numpy array o None si falla
        """
        pass
    
    @abstractmethod
    async def _close_connection(self) -> None:
        """Cierra la conexión específica del protocolo."""
        pass
    
    def _start_capture_thread(self) -> None:
        """Inicia el thread de captura de frames."""
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            name=f"capture_{self.stream_model.camera_id}",
            daemon=True
        )
        self._capture_thread.start()
        self.logger.debug(f"Thread de captura iniciado para {self.stream_model.camera_id}")
    
    def _capture_loop(self) -> None:
        """Loop de captura que corre en thread separado."""
        frame_interval = 1.0 / self.stream_model.target_fps
        last_frame_time = 0
        
        while self._is_streaming:
            try:
                current_time = time.time()
                
                # Limitar FPS
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue
                
                # Capturar frame
                frame = self._capture_frame()
                if frame is not None:
                    # Intentar agregar a la cola (no bloqueante)
                    try:
                        # Obtener el loop actual del hilo principal
                        loop = self._main_loop
                        if loop and not loop.is_closed():
                            asyncio.run_coroutine_threadsafe(
                                self._frame_queue.put(frame),
                                loop
                            )
                            last_frame_time = current_time
                        else:
                            self.logger.warning("Event loop no disponible")
                    except Exception as e:
                        # Cola llena o error, descartar frame
                        self.stream_model.dropped_frames += 1
                        self.logger.debug(f"Frame descartado: {e}")
                
            except Exception as e:
                self.logger.error(f"Error en captura de frame: {e}")
                time.sleep(0.1)  # Evitar loop rápido en caso de error
    
    async def _processing_loop(self) -> None:
        """Loop async para procesar frames de la cola."""
        while self._is_streaming:
            try:
                # Obtener frame de la cola con timeout
                frame = await asyncio.wait_for(
                    self._frame_queue.get(),
                    timeout=1.0
                )
                
                # Procesar frame
                await self._process_frame(frame)
                
            except asyncio.TimeoutError:
                # Normal cuando no hay frames
                continue
            except Exception as e:
                self.logger.error(f"Error procesando frame: {e}")
    
    async def _process_frame(self, frame: np.ndarray) -> None:
        """
        Procesa un frame capturado.
        
        Args:
            frame: Frame a procesar
        """
        try:
            # Convertir frame según configuración
            start_time = time.time()
            
            # Redimensionar si es necesario para optimizar
            max_width = 1280  # TODO: Hacer configurable
            height, width = frame.shape[:2]
            if width > max_width:
                resize_to = (max_width, int(height * max_width / width))
            else:
                resize_to = None
            
            # Convertir a base64
            frame_base64 = self.frame_converter.convert_frame(
                frame,
                resize=resize_to,
                quality=85  # TODO: Hacer configurable
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Notificar frame si hay callback
            if self._frame_callback:
                self._frame_callback(self.stream_model.camera_id, frame_base64)
                self.logger.debug(f"Frame enviado para {self.stream_model.camera_id}, tamaño: {len(frame_base64)} bytes")
            else:
                self.logger.warning(f"No hay callback configurado para notificar frames")
            
            # Actualizar métricas
            self.stream_model.metadata['last_processing_time_ms'] = processing_time
            
        except Exception as e:
            self.logger.error(f"Error convirtiendo frame: {e}")


class StreamManagerFactory:
    """
    Factory para crear stream managers según el protocolo.
    
    Implementa el patrón Factory para crear instancias
    específicas de StreamManager.
    """
    
    def __init__(self):
        """Inicializa la factory."""
        self.logger = logging.getLogger(__name__)
    
    def create_stream_manager(
        self,
        protocol: StreamProtocol,
        stream_model: StreamModel,
        connection_config: ConnectionConfig,
        frame_converter: FrameConverter
    ) -> StreamManager:
        """
        Crea un stream manager específico para el protocolo.
        
        Args:
            protocol: Protocolo a utilizar
            stream_model: Modelo del stream
            connection_config: Configuración de conexión
            frame_converter: Convertidor de frames
            
        Returns:
            StreamManager específico para el protocolo
            
        Raises:
            ValueError: Si el protocolo no está soportado
        """
        self.logger.info(f"Creating stream manager for protocol: {protocol.value}")
        
        try:
            if protocol == StreamProtocol.RTSP:
                self.logger.debug("Importing RTSPStreamManager...")
                from services.video.rtsp_stream_manager import RTSPStreamManager
                self.logger.debug("RTSPStreamManager imported successfully")
                return RTSPStreamManager(stream_model, connection_config, frame_converter)
            
            elif protocol == StreamProtocol.ONVIF:
                self.logger.debug("Importing ONVIFStreamManager...")
                from services.video.onvif_stream_manager import ONVIFStreamManager
                self.logger.debug("ONVIFStreamManager imported successfully")
                return ONVIFStreamManager(stream_model, connection_config, frame_converter)
                
            elif protocol == StreamProtocol.HTTP:
                self.logger.debug("Importing HTTPStreamManager...")
                from services.video.http_stream_manager import HTTPStreamManager
                self.logger.debug("HTTPStreamManager imported successfully")
                return HTTPStreamManager(stream_model, connection_config, frame_converter)
                
            elif protocol == StreamProtocol.GENERIC:
                # Generic usa RTSP por defecto
                self.logger.debug("Importing RTSPStreamManager for GENERIC...")
                from services.video.rtsp_stream_manager import RTSPStreamManager
                self.logger.debug("RTSPStreamManager imported successfully for GENERIC")
                return RTSPStreamManager(stream_model, connection_config, frame_converter)
                
            else:
                raise ValueError(f"Protocolo no soportado: {protocol.value}")
                
        except ImportError as e:
            self.logger.error(f"Error importing stream manager for {protocol.value}: {e}")
            self.logger.error(f"Import error details: {e.__class__.__name__}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating stream manager: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def get_supported_protocols() -> list[StreamProtocol]:
        """Obtiene la lista de protocolos soportados."""
        return [
            StreamProtocol.RTSP,
            StreamProtocol.ONVIF,
            StreamProtocol.HTTP,
            StreamProtocol.GENERIC
        ]