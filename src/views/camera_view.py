#!/usr/bin/env python3
"""
CameraView - Vista de cámara individual para streaming en tiempo real.

Proporciona la interfaz de usuario para:
- Visualización de streaming de cámara individual
- Controles de cámara (conectar/desconectar, snapshot, etc.)
- Información de estado y métricas
- Configuración de calidad de video
"""

import flet as ft
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from ..presenters import CameraPresenter


class CameraView:
    """
    Vista de cámara individual con streaming en tiempo real.
    
    Proporciona interfaz completa para:
    - Stream de video en tiempo real
    - Controles de conexión y configuración  
    - Métricas de rendimiento
    - Manejo de estados (conectado, desconectado, error)
    """
    
    def __init__(self, camera_id: str, width: int = 320, height: int = 240):
        """
        Inicializa la vista de cámara.
        
        Args:
            camera_id: Identificador único de la cámara
            width: Ancho del widget de cámara
            height: Alto del widget de cámara
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        
        self.logger = logging.getLogger(f"CameraView_{camera_id}")
        
        # Presenter
        self.presenter: Optional[CameraPresenter] = None
        
        # Estado de la vista
        self._is_connected = False
        self._is_streaming = False
        self._last_frame_time: Optional[datetime] = None
        self._fps = 0.0
        
        # Callbacks externos
        self.on_camera_selected: Optional[Callable[[str], None]] = None
        self.on_status_changed: Optional[Callable[[str, str], None]] = None
        
        # Referencias de UI
        self._main_container = None
        self._video_area = None
        self._camera_name = None
        self._status_indicator = None
        self._metrics_text = None
        self._connect_btn = None
        self._disconnect_btn = None
        self._snapshot_btn = None
        self._settings_btn = None
        
        # Crear componentes UI
        self._create_ui_components()
        
    def _create_ui_components(self):
        """Crea todos los componentes de la interfaz."""
        
        # === Área de video ===
        self._video_area = ft.Container(
             content=ft.Column([
                 ft.Icon(
                     ft.Icons.VIDEOCAM_OFF,
                     size=64,
                     color=ft.Colors.GREY_400
                 ),
                 ft.Text(
                     "Sin conexión",
                     size=14,
                     color=ft.Colors.GREY_600,
                     text_align=ft.TextAlign.CENTER
                 )
             ], 
                          alignment=ft.MainAxisAlignment.CENTER,
             horizontal_alignment=ft.CrossAxisAlignment.CENTER),
             width=self.width - 10 if self.width else 310,
             height=self.height - 10 if self.height else 230,
             bgcolor=ft.Colors.GREY_100,
             border_radius=4,
             alignment=ft.alignment.center
         )
        
        # === Información de cámara ===
        self._camera_name = ft.Text(
            f"Cámara {self.camera_id}",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
            text_align=ft.TextAlign.CENTER
        )
        
        self._status_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.RED),
                ft.Text("Desconectado", size=10, color=ft.Colors.RED)
            ], tight=True),
            padding=ft.padding.symmetric(horizontal=4, vertical=2),
            border_radius=10,
            bgcolor=ft.Colors.RED_50
        )
        
        self._metrics_text = ft.Text(
            "0 FPS",
            size=10,
            color=ft.Colors.GREY_600
        )
        
        # === Controles ===
        self._connect_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE,
            icon_color=ft.Colors.GREEN,
            tooltip="Conectar cámara",
            on_click=self._on_connect_click
        )
        
        self._disconnect_btn = ft.IconButton(
            icon=ft.Icons.STOP_CIRCLE,
            icon_color=ft.Colors.RED,
            tooltip="Desconectar cámara",
            on_click=self._on_disconnect_click,
            visible=False
        )
        
        self._snapshot_btn = ft.IconButton(
            icon=ft.Icons.CAMERA_ALT,
            icon_color=ft.Colors.BLUE,
            tooltip="Capturar snapshot",
            on_click=self._on_snapshot_click,
            visible=False
        )
        
        self._settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color=ft.Colors.GREY_700,
            tooltip="Configuración",
            on_click=self._on_settings_click
        )
        
        # === Header de la cámara ===
        self._header = ft.Container(
            content=ft.Row([
                self._camera_name,
                ft.Container(expand=True),
                self._status_indicator
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=5)
        )
        
        # === Footer con controles ===
        self._footer = ft.Container(
            content=ft.Row([
                self._connect_btn,
                self._disconnect_btn,
                self._snapshot_btn,
                ft.Container(expand=True),
                self._metrics_text,
                self._settings_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=5)
        )
        
        # === Contenido principal ===
        self._main_content = ft.Column([
            self._header,
            self._video_area,
            self._footer
        ], spacing=0)
        
        # === Contenedor principal ===
        self._main_container = ft.Container(
            content=self._main_content,
            width=self.width,
            height=self.height + 80,  # Espacio extra para controles
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=5,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 1)
            )
        )
    
    def build(self) -> ft.Container:
        """Retorna el contenedor principal para ser agregado a la UI."""
        if self._main_container is None:
            raise ValueError("UI components not initialized")
        return self._main_container
    
    # === Callbacks síncronos para el presenter ===
    
    def _on_connection_change_sync(self, connected: bool, message: str):
        """Callback síncrono para cambios de conexión."""
        self._is_connected = connected
        # TODO: Implementar actualización de UI síncrona
        
        # Notificar cambio de estado externamente
        if self.on_status_changed:
            status = "connected" if connected else "disconnected"
            self.on_status_changed(self.camera_id, status)
        
        self.logger.info(f"Conexión cambiada: {connected} - {message}")
    
    def _on_frame_received_sync(self, frame_data):
        """Callback síncrono para frames recibidos."""
        self._last_frame_time = datetime.now()
        
        # TODO: Mostrar frame real cuando se implemente streaming
        # Por ahora solo actualizar estado visual
        if not self._is_streaming:
            self._is_streaming = True
            # TODO: Implementar actualización de UI síncrona
    
    def _on_metrics_update_sync(self, metrics: Dict[str, Any]):
        """Callback síncrono para actualización de métricas."""
        if "current_fps" in metrics and self._metrics_text:
            self._fps = metrics["current_fps"]
            self._metrics_text.value = f"{self._fps:.1f} FPS"
    
    async def initialize_async(self, presenter: CameraPresenter):
        """
        Inicializa la vista de forma asíncrona con el presenter.
        
        Args:
            presenter: Presenter de la cámara
        """
        try:
            self.presenter = presenter
            
            # Configurar callbacks del presenter (síncronos)
            self.presenter.set_connection_change_callback(self._on_connection_change_sync)
            self.presenter.set_frame_received_callback(self._on_frame_received_sync)
            self.presenter.set_metrics_update_callback(self._on_metrics_update_sync)
            
            # Inicializar presenter
            await self.presenter.initialize_async()
            
            # Actualizar UI con estado inicial
            await self._update_ui_state()
            
            self.logger.info(f"Vista de cámara {self.camera_id} inicializada")
            
        except Exception as e:
            self.logger.error(f"Error inicializando vista: {str(e)}")
            await self._show_error(f"Error de inicialización: {str(e)}")
    
    async def _update_ui_state(self):
        """Actualiza el estado de la UI basado en el presenter."""
        if not self.presenter:
            return
        
        # Actualizar información de la cámara
        camera_model = self.presenter.get_camera_model()
        if camera_model and self._camera_name:
            self._camera_name.value = camera_model.display_name
        
        # Actualizar estado de conexión
        self._is_connected = self.presenter.is_connected()
        self._is_streaming = self.presenter.is_streaming()
        
        await self._update_connection_status()
        await self._update_controls_visibility()
        await self._update_metrics()
    
    async def _update_connection_status(self):
        """Actualiza el indicador de estado de conexión."""
        if not self._status_indicator or not self._video_area:
            return
            
        if self._is_streaming:
            self._status_indicator.content = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.GREEN),
                ft.Text("Streaming", size=10, color=ft.Colors.GREEN)
            ], tight=True)
            self._status_indicator.bgcolor = ft.Colors.GREEN_50
            
            # Actualizar área de video para streaming
            self._video_area.content = ft.Column([
                ft.Icon(
                    ft.Icons.VIDEOCAM,
                    size=64,
                    color=ft.Colors.GREEN
                ),
                ft.Text(
                    "Streaming activo",
                    size=14,
                    color=ft.Colors.GREEN,
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self._video_area.bgcolor = ft.Colors.GREEN_50
            
        elif self._is_connected:
            self._status_indicator.content = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.ORANGE),
                ft.Text("Conectado", size=10, color=ft.Colors.ORANGE)
            ], tight=True)
            self._status_indicator.bgcolor = ft.Colors.ORANGE_50
            
            # Actualizar área de video para conectado
            self._video_area.content = ft.Column([
                ft.Icon(
                    ft.Icons.VIDEOCAM_OFF,
                    size=64,
                    color=ft.Colors.ORANGE
                ),
                ft.Text(
                    "Conectado - Sin streaming",
                    size=14,
                    color=ft.Colors.ORANGE,
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self._video_area.bgcolor = ft.Colors.ORANGE_50
            
        else:
            self._status_indicator.content = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.RED),
                ft.Text("Desconectado", size=10, color=ft.Colors.RED)
            ], tight=True)
            self._status_indicator.bgcolor = ft.Colors.RED_50
            
            # Actualizar área de video para desconectado
            self._video_area.content = ft.Column([
                ft.Icon(
                    ft.Icons.VIDEOCAM_OFF,
                    size=64,
                    color=ft.Colors.GREY_400
                ),
                ft.Text(
                    "Sin conexión",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self._video_area.bgcolor = ft.Colors.GREY_100
        
        # Actualizar UI
        self.update()
    
    def update(self):
        """Actualiza la interfaz de la cámara."""
        # TODO: Implementar actualización de página si está disponible
        pass
    
    async def _update_controls_visibility(self):
        """Actualiza la visibilidad de los controles según el estado."""
        if self._connect_btn:
            self._connect_btn.visible = not self._is_connected
        if self._disconnect_btn:
            self._disconnect_btn.visible = self._is_connected
        if self._snapshot_btn:
            self._snapshot_btn.visible = self._is_streaming
        
        self.update()
    
    async def _update_metrics(self):
        """Actualiza las métricas mostradas."""
        if not self._metrics_text:
            return
            
        if self.presenter:
            self._fps = self.presenter.get_stream_fps()
            self._metrics_text.value = f"{self._fps:.1f} FPS"
        else:
            self._metrics_text.value = "0 FPS"
        
        self.update()
    
    # === Callbacks del Presenter ===
    
    async def _on_connection_change(self, connected: bool, message: str):
        """Callback para cambios de conexión."""
        self._is_connected = connected
        await self._update_connection_status()
        await self._update_controls_visibility()
        
        # Notificar cambio de estado externamente
        if self.on_status_changed:
            status = "connected" if connected else "disconnected"
            self.on_status_changed(self.camera_id, status)
        
        self.logger.info(f"Conexión cambiada: {connected} - {message}")
    
    async def _on_frame_received(self, frame_data):
        """Callback para frames recibidos."""
        self._last_frame_time = datetime.now()
        
        # TODO: Mostrar frame real cuando se implemente streaming
        # Por ahora solo actualizar estado visual
        if not self._is_streaming:
            self._is_streaming = True
            await self._update_connection_status()
            await self._update_controls_visibility()
    
    async def _on_metrics_update(self, metrics: Dict[str, Any]):
        """Callback para actualización de métricas."""
        if "current_fps" in metrics:
            self._fps = metrics["current_fps"]
            await self._update_metrics()
    
    # === Event Handlers ===
    
    async def _on_connect_click(self, e):
        """Maneja clic en botón de conectar."""
        if self.presenter:
            try:
                await self.presenter.connect_camera()
            except Exception as ex:
                await self._show_error(f"Error conectando: {str(ex)}")
    
    async def _on_disconnect_click(self, e):
        """Maneja clic en botón de desconectar."""
        if self.presenter:
            try:
                await self.presenter.disconnect_camera()
            except Exception as ex:
                await self._show_error(f"Error desconectando: {str(ex)}")
    
    async def _on_snapshot_click(self, e):
        """Maneja clic en botón de snapshot."""
        if self.presenter:
            try:
                filepath = await self.presenter.take_snapshot()
                if filepath:
                    await self._show_success(f"Snapshot guardado: {filepath}")
                else:
                    await self._show_error("No se pudo capturar snapshot")
            except Exception as ex:
                await self._show_error(f"Error capturando snapshot: {str(ex)}")
    
    async def _on_settings_click(self, e):
        """Maneja clic en botón de configuración."""
        # TODO: Abrir diálogo de configuración de cámara
        await self._show_info("Configuración próximamente disponible")
    
    async def _on_video_area_click(self, e):
        """Maneja clic en el área de video."""
        # Notificar selección de cámara
        if self.on_camera_selected:
            self.on_camera_selected(self.camera_id)
    
    # === Métodos de utilidad ===
    
    async def _show_error(self, message: str):
        """Muestra un mensaje de error."""
        # TODO: Implementar sistema de notificaciones
        self.logger.error(message)
    
    async def _show_success(self, message: str):
        """Muestra un mensaje de éxito."""
        # TODO: Implementar sistema de notificaciones
        self.logger.info(message)
    
    async def _show_info(self, message: str):
        """Muestra un mensaje informativo."""
        # TODO: Implementar sistema de notificaciones
        self.logger.info(message)
    
    # === Métodos públicos ===
    
    def set_camera_name(self, name: str):
        """Establece el nombre de la cámara."""
        if self._camera_name:
            self._camera_name.value = name
            self.update()
    
    def set_size(self, width: int, height: int):
        """Cambia el tamaño del widget."""
        self.width = width
        self.height = height
        
        if self._video_area:
            self._video_area.width = width - 10
            self._video_area.height = height - 10
        
        if self._main_container:
            self._main_container.width = width
            self._main_container.height = height + 80
            
        self.update()
    
    def get_camera_id(self) -> str:
        """Retorna el ID de la cámara."""
        return self.camera_id
    
    def is_connected(self) -> bool:
        """Retorna si la cámara está conectada."""
        return self._is_connected
    
    def is_streaming(self) -> bool:
        """Retorna si la cámara está haciendo streaming."""
        return self._is_streaming
    
    def get_fps(self) -> float:
        """Retorna el FPS actual."""
        return self._fps
    
    async def cleanup(self):
        """Limpia recursos de la vista."""
        try:
            if self.presenter:
                await self.presenter.cleanup_async()
            
            self.logger.info(f"Vista de cámara {self.camera_id} limpiada")
            
        except Exception as e:
            self.logger.error(f"Error limpiando vista: {str(e)}") 