#!/usr/bin/env python3
"""
CameraPresenter - Presenter para gestión de cámaras individuales.

Coordina la lógica de negocio para:
- Conexión y desconexión de cámaras
- Gestión de streams de video
- Control de configuración de cámaras
- Monitoreo de estado y métricas
- Operaciones de captura (snapshots)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .base_presenter import BasePresenter, PresenterState
from ..models import CameraModel, ConnectionModel, ConnectionConfig, ProtocolType, ConnectionType
from ..models.streaming import StreamModel, StreamProtocol
from ..services import get_connection_service, get_data_service, get_config_service
from .streaming import VideoStreamPresenter


class CameraPresenter(BasePresenter):
    """
    Presenter para gestión de cámaras individuales.
    
    Coordina todas las operaciones relacionadas con una cámara específica:
    - Gestión de conexión y estado
    - Control de streaming de video
    - Configuración y ajustes
    - Captura de snapshots
    - Monitoreo y métricas
    """
    
    def __init__(self, camera_id: str):
        """
        Inicializa el presenter para una cámara específica.
        
        Args:
            camera_id: Identificador único de la cámara
        """
        super().__init__()
        
        self.camera_id = camera_id
        self._camera_model: Optional[CameraModel] = None
        self._connection_model: Optional[ConnectionModel] = None
        self._stream_model: Optional[StreamModel] = None
        
        # Servicios
        self._connection_service = get_connection_service()
        self._data_service = get_data_service()
        
        # Presenter de streaming
        self._video_stream_presenter: Optional[VideoStreamPresenter] = None
        self._config_service = get_config_service()
        
        # Estado de streaming
        self._is_streaming = False
        self._stream_quality = "medium"
        self._stream_fps = 0.0
        
        # Métricas de cámara
        self._connection_attempts = 0
        self._successful_connections = 0
        self._last_frame_time: Optional[datetime] = None
        self._total_frames = 0
        
        # Callbacks para la view
        self._on_connection_change: Optional[Callable[[bool, str], None]] = None
        self._on_frame_received: Optional[Callable[[Any], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        self._on_metrics_update: Optional[Callable[[Dict[str, Any]], None]] = None
        
    async def initialize_async(self) -> bool:
        """
        Inicialización asíncrona del presenter.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.logger.info(f"🎥 Inicializando CameraPresenter para cámara {self.camera_id}")
            
            # Cargar modelo de cámara desde configuración o datos
            await self._load_camera_model()
            
            # Configurar métricas iniciales
            await self._setup_metrics()
            
            # Inicializar conexión si está configurada para auto-conectar
            if await self._should_auto_connect():
                await self.connect_camera()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando CameraPresenter: {str(e)}")
            self._set_state(PresenterState.ERROR)
            return False
    
    async def _load_camera_model(self) -> None:
        """Carga el modelo de cámara desde datos persistidos o configuración."""
        try:
            # Intentar cargar desde DataService
            camera_data = await self._data_service.get_camera_data(self.camera_id)
            
            if camera_data:
                # Convertir datos persistidos a modelo
                connection_config = ConnectionConfig(
                    ip=camera_data.ip,
                    username="admin",  # Valor por defecto
                    password=""  # Se obtendrá del ConfigService
                )
                self._camera_model = CameraModel(
                    brand=camera_data.brand,
                    model=camera_data.model,
                    display_name=camera_data.camera_id,
                    connection_config=connection_config
                )
                self.logger.info(f"📊 Modelo de cámara cargado desde datos: {self.camera_id}")
            else:
                # Crear modelo básico si no existe
                connection_config = ConnectionConfig(
                    ip="",
                    username="admin",
                    password=""
                )
                self._camera_model = CameraModel(
                    brand="Unknown",
                    model="Unknown", 
                    display_name=self.camera_id,
                    connection_config=connection_config
                )
                self.logger.info(f"🆕 Creado modelo básico para cámara: {self.camera_id}")
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando modelo de cámara: {str(e)}")
            # Crear modelo de fallback
            connection_config = ConnectionConfig(
                ip="",
                username="admin",
                password=""
            )
            self._camera_model = CameraModel(
                brand="Unknown",
                model="Unknown",
                display_name=self.camera_id,
                connection_config=connection_config
            )
    
    async def _setup_metrics(self) -> None:
        """Configura las métricas de monitoreo de la cámara."""
        self.add_metric("connection_attempts", 0)
        self.add_metric("successful_connections", 0)
        self.add_metric("total_frames", 0)
        self.add_metric("current_fps", 0.0)
        self.add_metric("stream_quality", self._stream_quality)
        self.add_metric("is_streaming", False)
        self.add_metric("last_frame_time", None)
        self.add_metric("uptime_seconds", 0)
    
    async def _should_auto_connect(self) -> bool:
        """Determina si la cámara debe conectarse automáticamente."""
        try:
            auto_connect = await self._config_service.get_config_value(
                f"camera.{self.camera_id}.auto_connect", 
                default=False
            )
            return bool(auto_connect)
        except Exception:
            return False
    
    # === Operaciones de Conexión ===
    
    async def connect_camera(self, config: Optional[ConnectionConfig] = None) -> bool:
        """
        Conecta la cámara con la configuración especificada.
        
        Args:
            config: Configuración de conexión (opcional)
            
        Returns:
            True si la conexión fue exitosa
        """
        await self.set_busy(True)
        
        try:
            self._connection_attempts += 1
            self.add_metric("connection_attempts", self._connection_attempts)
            
            # Usar configuración proporcionada o crear desde modelo
            if config:
                # Actualizar modelo con nueva configuración
                if self._camera_model:
                    self._camera_model.update_connection_config(
                        ip=config.ip,
                        username=config.username,
                        password=config.password
                    )
            
            if not self._camera_model:
                raise ValueError("No se pudo crear configuración de conexión")
            
            # Intentar conexión a través del servicio
            success = await self._connection_service.connect_camera_async(
                camera=self._camera_model,
                connection_type=ConnectionType.RTSP_STREAM
            )
            
            if success:
                self._successful_connections += 1
                self.add_metric("successful_connections", self._successful_connections)
                
                # Notificar cambio de conexión
                if self._on_connection_change:
                    await self.execute_safely(
                        self._on_connection_change,
                        True,
                        "Conectado exitosamente"
                    )
                
                # Iniciar streaming si está habilitado
                if await self._should_auto_stream():
                    await self.start_streaming()
                
                self._set_state(PresenterState.READY)
                self.logger.info(f"✅ Cámara {self.camera_id} conectada exitosamente")
                
                # Guardar datos de conexión exitosa
                await self._save_connection_data()
                
                return True
            else:
                raise ConnectionError("Conexión fallida")
                
        except Exception as e:
            error_msg = f"Error conectando cámara: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            if self._on_connection_change:
                await self.execute_safely(self._on_connection_change, False, error_msg)
            
            await self.set_error(error_msg)
            return False
    
    async def disconnect_camera(self) -> bool:
        """
        Desconecta la cámara.
        
        Returns:
            True si la desconexión fue exitosa
        """
        await self.set_busy(True)
        
        try:
            # Detener streaming primero
            if self._is_streaming:
                await self.stop_streaming()
            
            # Desconectar a través del servicio
            success = self._connection_service.disconnect_camera(self.camera_id)
            
            if success:
                self._connection_model = None
                
                # Notificar cambio de conexión
                if self._on_connection_change:
                    await self.execute_safely(
                        self._on_connection_change,
                        False,
                        "Desconectado"
                    )
                
                self._set_state(PresenterState.READY)
                self.logger.info(f"✅ Cámara {self.camera_id} desconectada")
                return True
            else:
                raise ConnectionError("Error en desconexión del servicio")
                
        except Exception as e:
            error_msg = f"Error desconectando cámara: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def _should_auto_stream(self) -> bool:
        """Determina si debe iniciar streaming automáticamente."""
        try:
            auto_stream = await self._config_service.get_config_value(
                f"camera.{self.camera_id}.auto_stream",
                default=True
            )
            return bool(auto_stream)
        except Exception:
            return True
    
    # === Operaciones de Streaming ===
    
    async def start_streaming(self, quality: str = "medium") -> bool:
        """
        Inicia el streaming de video.
        
        Args:
            quality: Calidad del stream ("low", "medium", "high")
            
        Returns:
            True si el streaming se inició correctamente
        """
        if not self._camera_model or not self._camera_model.is_connected:
            await self.set_error("No hay conexión de cámara para streaming")
            return False
        
        if self._is_streaming:
            self.logger.warning(f"⚠️ Streaming ya está activo para cámara {self.camera_id}")
            return True
        
        await self.set_busy(True)
        
        try:
            self._stream_quality = quality
            self.add_metric("stream_quality", quality)
            
            # Configurar streaming a través del servicio de conexión
            # (Esta funcionalidad se implementará cuando se migre el código de streaming)
            
            self._is_streaming = True
            self.add_metric("is_streaming", True)
            
            # Iniciar tarea de monitoreo de frames
            self._add_background_task(self._frame_monitor_task())
            
            self._set_state(PresenterState.READY)
            self.logger.info(f"📹 Streaming iniciado para cámara {self.camera_id}")
            return True
            
        except Exception as e:
            error_msg = f"Error iniciando streaming: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def stop_streaming(self) -> bool:
        """
        Detiene el streaming de video.
        
        Returns:
            True si el streaming se detuvo correctamente
        """
        if not self._is_streaming:
            return True
        
        await self.set_busy(True)
        
        try:
            # Detener streaming a través del servicio
            # (Esta funcionalidad se implementará cuando se migre el código de streaming)
            
            self._is_streaming = False
            self._stream_fps = 0.0
            self.add_metric("is_streaming", False)
            self.add_metric("current_fps", 0.0)
            
            self._set_state(PresenterState.READY)
            self.logger.info(f"⏹️ Streaming detenido para cámara {self.camera_id}")
            return True
            
        except Exception as e:
            error_msg = f"Error deteniendo streaming: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def _frame_monitor_task(self) -> None:
        """Tarea de fondo para monitorear frames y calcular FPS."""
        
        while self._is_streaming and not self._shutdown_event.is_set():
            try:
                # Obtener métricas del stream model si existe
                if self._stream_model:
                    # Usar FPS real del stream
                    self._stream_fps = self._stream_model.fps
                    self._total_frames = self._stream_model.frame_count
                    self._last_frame_time = self._stream_model.last_frame_time or datetime.now()
                    
                    # Actualizar métricas desde el modelo
                    self.add_metric("current_fps", self._stream_fps)
                    self.add_metric("total_frames", self._total_frames)
                    self.add_metric("dropped_frames", self._stream_model.dropped_frames)
                    
                    # Verificar salud del stream
                    if self._stream_model.status.value == "error":
                        await self.set_error(f"Error en stream: {self._stream_model.error_message}")
                        self._is_streaming = False
                        break
                else:
                    # Sin modelo de stream, usar valores por defecto
                    self._stream_fps = 0.0
                    self.add_metric("current_fps", 0.0)
                
                # Actualizar métricas generales
                self.add_metric("current_fps", round(self._stream_fps, 2))
                self.add_metric("total_frames", self._total_frames)
                self.add_metric("last_frame_time", current_time.isoformat())
                
                # Notificar frame recibido (placeholder)
                if self._on_frame_received:
                    await self.execute_safely(self._on_frame_received, None)
                
                # Notificar actualización de métricas
                if self._on_metrics_update:
                    await self.execute_safely(
                        self._on_metrics_update,
                        self.get_metrics()
                    )
                
            except Exception as e:
                if not self._shutdown_event.is_set():
                    self.logger.error(f"❌ Error en monitoreo de frames: {str(e)}")
                break
    
    # === Operaciones de Captura ===
    
    async def take_snapshot(self, save_to_disk: bool = True) -> Optional[str]:
        """
        Captura un snapshot de la cámara.
        
        Args:
            save_to_disk: Si guardar el snapshot en disco
            
        Returns:
            Ruta del archivo guardado o None si falló
        """
        if not self._camera_model or not self._camera_model.is_connected:
            await self.set_error("No hay conexión de cámara para captura")
            return None
        
        await self.set_busy(True)
        
        try:
            # Capturar snapshot a través del servicio
            # (Esta funcionalidad se implementará cuando se migre el código de captura)
            
            if save_to_disk:
                # Generar nombre de archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshot_{self.camera_id}_{timestamp}.jpg"
                filepath = f"snapshots/{filename}"
                
                # Guardar datos del snapshot
                await self._save_snapshot_data(filepath)
                
                self._set_state(PresenterState.READY)
                self.logger.info(f"📸 Snapshot capturado: {filepath}")
                return filepath
            else:
                self._set_state(PresenterState.READY)
                return None
                
        except Exception as e:
            error_msg = f"Error capturando snapshot: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return None
    
    async def _save_snapshot_data(self, filepath: str) -> None:
        """Guarda metadatos del snapshot en el DataService."""
        try:
            # Esta funcionalidad se implementará cuando se integre con DataService
            pass
        except Exception as e:
            self.logger.error(f"❌ Error guardando datos de snapshot: {str(e)}")
    
    async def _save_connection_data(self) -> None:
        """Guarda datos de conexión en el DataService."""
        try:
            if self._camera_model:
                await self._data_service.save_camera_data(self._camera_model)
        except Exception as e:
            self.logger.error(f"❌ Error guardando datos de conexión: {str(e)}")
    
    # === Gestión de Estado ===
    
    def is_connected(self) -> bool:
        """Retorna si la cámara está conectada."""
        return (self._camera_model is not None and 
                self._camera_model.is_connected)
    
    def is_streaming(self) -> bool:
        """Retorna si la cámara está haciendo streaming."""
        return self._is_streaming
    
    def get_camera_model(self) -> Optional[CameraModel]:
        """Retorna el modelo de cámara."""
        return self._camera_model
    
    def get_connection_model(self) -> Optional[ConnectionModel]:
        """Retorna el modelo de conexión."""
        return self._connection_model
    
    def get_stream_fps(self) -> float:
        """Retorna el FPS actual del stream."""
        return self._stream_fps
    
    def get_stream_quality(self) -> str:
        """Retorna la calidad actual del stream."""
        return self._stream_quality
    
    # === Callbacks de View ===
    
    def set_connection_change_callback(self, callback: Callable[[bool, str], None]) -> None:
        """Establece callback para cambios de conexión."""
        self._on_connection_change = callback
    
    def set_frame_received_callback(self, callback: Callable[[Any], None]) -> None:
        """Establece callback para frames recibidos."""
        self._on_frame_received = callback
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Establece callback para errores."""
        self._on_error = callback
    
    def set_metrics_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Establece callback para actualizaciones de métricas."""
        self._on_metrics_update = callback
    
    # === Abstract Methods Implementation ===
    
    async def _initialize_presenter(self) -> None:
        """Implementación de inicialización específica del presenter."""
        # La inicialización específica se maneja en initialize_async()
        pass
    
    async def _cleanup_presenter(self) -> None:
        """Implementación de limpieza específica del presenter."""
        try:
            # Detener streaming si está activo
            if self._is_streaming:
                await self.stop_streaming()
            
            # Limpiar video stream presenter si existe
            if self._video_stream_presenter:
                await self._video_stream_presenter.deactivate()
                self._video_stream_presenter = None
            
            # Desconectar si está conectado
            if self.is_connected():
                await self.disconnect_camera()
            
            self.logger.info(f"🧹 CameraPresenter para {self.camera_id} limpiado")
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza de CameraPresenter: {str(e)}")
    
    # === Cleanup ===
    
    async def cleanup_async(self) -> None:
        """Limpieza asíncrona del presenter."""
        await self._cleanup_presenter() 