#!/usr/bin/env python3
"""
MainView - Vista principal de la aplicación usando Flet.

Implementa la interfaz principal del visor de cámaras multi-marca
con arquitectura MVP. Proporciona:
- Grilla de cámaras en tiempo real
- Panel de control y configuración
- Herramientas de escaneo de red
- Barra de herramientas y menús
- Panel de estado y métricas
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

import flet as ft

from .camera_view import CameraView
from ..presenters import MainPresenter, get_main_presenter
from ..models import CameraModel, ScanConfig


class MainView:
    """
    Vista principal de la aplicación MVP.
    
    Coordina la interfaz completa del visor de cámaras:
    - Layout responsivo con grilla de cámaras
    - Controles de conexión y escaneo
    - Panel de configuración
    - Barra de estado y progreso
    - Manejo de eventos de usuario
    """
    
    def __init__(self, page: ft.Page):
        """
        Inicializa la vista principal.
        
        Args:
            page: Página principal de Flet
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # Presenter principal
        self.presenter: MainPresenter = get_main_presenter()
        
        # Estado de la vista
        self._camera_views: Dict[str, CameraView] = {}
        self._current_layout = 2
        self._is_scanning = False
        self._scan_progress = 0
        
        # Referencias de UI
        self._toolbar = None
        self._camera_grid = None
        self._status_bar = None
        self._scan_progress_bar = None
        self._layout_controls = None
        self._camera_count_text = None
        self._main_container = None
        
        # Configurar callbacks del presenter
        self._setup_presenter_callbacks()
    
    def _setup_presenter_callbacks(self):
        """Configura los callbacks del presenter."""
        self.presenter.set_cameras_updated_callback(self._on_cameras_updated)
        self.presenter.set_camera_status_changed_callback(self._on_camera_status_changed)
        self.presenter.set_scan_progress_callback(self._on_scan_progress)
        self.presenter.set_scan_completed_callback(self._on_scan_completed)
        self.presenter.set_error_callback(self._on_error)
    
    def build(self) -> ft.Column:
        """Construye la interfaz principal."""
        self._main_container = ft.Column([
            self._build_toolbar(),
            ft.Divider(height=1),
            ft.Container(
                content=ft.Row([
                    # Panel lateral izquierdo
                    ft.Container(
                        content=self._build_side_panel(),
                        width=280,
                        bgcolor=ft.Colors.GREY_100,
                        padding=ft.padding.all(10),
                        border_radius=8
                    ),
                    ft.VerticalDivider(width=1),
                    # Área principal de cámaras
                    ft.Container(
                        content=self._build_camera_area(),
                        expand=True,
                        padding=ft.padding.all(10)
                    )
                ]),
                expand=True
            ),
            ft.Divider(height=1),
            self._build_status_bar()
        ],
        expand=True,
        spacing=0
        )
        
        return self._main_container
    
    def _build_toolbar(self) -> ft.Container:
        """Construye la barra de herramientas."""
        self._toolbar = ft.Row([
            # Logo y título
            ft.Row([
                ft.Icon(ft.Icons.VIDEOCAM, color=ft.Colors.PRIMARY, size=28),
                ft.Text(
                    "Visor Universal de Cámaras",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY
                )
            ]),
            
            ft.Container(expand=True),  # Spacer
            
            # Controles principales
            ft.Row([
                # Botón conectar todas
                ft.ElevatedButton(
                    text="Conectar Todas",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=self._on_connect_all_clicked,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE
                ),
                
                # Botón desconectar todas
                ft.ElevatedButton(
                    text="Desconectar",
                    icon=ft.Icons.STOP,
                    on_click=self._on_disconnect_all_clicked,
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE
                ),
                
                ft.VerticalDivider(width=10),
                
                # Botón escanear red
                ft.ElevatedButton(
                    text="Escanear Red",
                    icon=ft.Icons.SEARCH,
                    on_click=self._on_scan_clicked,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE
                ),
                
                # Botón configuración
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="Configuración",
                    on_click=self._on_settings_clicked
                )
            ], spacing=10)
        ])
        
        return ft.Container(
            content=self._toolbar,
            bgcolor=ft.Colors.SURFACE,
            padding=ft.padding.all(15),
            border_radius=ft.border_radius.only(top_left=8, top_right=8)
        )
    
    def _build_side_panel(self) -> ft.Column:
        """Construye el panel lateral con controles."""
        return ft.Column([
            # Título del panel
            ft.Text(
                "Panel de Control",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.PRIMARY
            ),
            ft.Divider(),
            
            # Controles de layout
            self._build_layout_controls(),
            ft.Divider(),
            
            # Estadísticas
            self._build_statistics_section(),
            ft.Divider(),
            
            # Controles de escaneo
            self._build_scan_controls(),
            
            ft.Container(expand=True),  # Spacer
            
            # Progreso de escaneo
            self._build_scan_progress()
        ], spacing=10)
    
    def _build_layout_controls(self) -> ft.Container:
        """Construye controles de layout de cámaras."""
        self._layout_controls = ft.Column([
            ft.Text("Layout de Cámaras", weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("Columnas:"),
                ft.Dropdown(
                    value=str(self._current_layout),
                    options=[
                        ft.dropdown.Option("1", "1 Columna"),
                        ft.dropdown.Option("2", "2 Columnas"),
                        ft.dropdown.Option("3", "3 Columnas"),
                        ft.dropdown.Option("4", "4 Columnas"),
                        ft.dropdown.Option("6", "6 Columnas"),
                    ],
                    width=120,
                    on_change=self._on_layout_changed
                )
            ])
        ])
        
        return ft.Container(content=self._layout_controls)
    
    def _build_statistics_section(self) -> ft.Container:
        """Construye la sección de estadísticas."""
        self._camera_count_text = ft.Text("Cámaras: 0/0")
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Estadísticas", weight=ft.FontWeight.BOLD),
                self._camera_count_text,
                ft.Text("Estado: Listo"),
                ft.Text("Última conexión: --")
            ]),
            bgcolor=ft.Colors.SURFACE,
            padding=ft.padding.all(10),
            border_radius=8
        )
    
    def _build_scan_controls(self) -> ft.Container:
        """Construye controles de escaneo."""
        self._network_field = ft.TextField(
            label="Red",
            value="192.168.1.0/24",
            width=150
        )
        
        self._ports_field = ft.TextField(
            label="Puertos",
            value="80,8080,554",
            width=150
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Escaneo de Red", weight=ft.FontWeight.BOLD),
                ft.Row([self._network_field]),
                ft.Row([self._ports_field]),
                ft.ElevatedButton(
                    text="Configurar Escaneo",
                    icon=ft.Icons.TUNE,
                    on_click=self._on_configure_scan_clicked,
                    width=200
                )
            ])
        )
    
    def _build_scan_progress(self) -> ft.Container:
        """Construye indicador de progreso de escaneo."""
        self._scan_progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            bgcolor=ft.Colors.SURFACE,
            color=ft.Colors.BLUE
        )
        
        self._scan_progress_text = ft.Text("")
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Progreso de Escaneo", weight=ft.FontWeight.BOLD),
                self._scan_progress_bar,
                self._scan_progress_text
            ])
        )
    
    def _build_camera_area(self) -> ft.Container:
        """Construye el área principal de cámaras."""
        self._camera_grid = ft.GridView(
            expand=True,
            runs_count=self._current_layout,
            max_extent=400,
            child_aspect_ratio=1.3,
            spacing=10,
            run_spacing=10,
            padding=ft.padding.all(10)
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Cámaras Activas",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        tooltip="Agregar Cámara",
                        on_click=self._on_add_camera_clicked
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Actualizar",
                        on_click=self._on_refresh_clicked
                    )
                ]),
                ft.Divider(),
                ft.Container(
                    content=self._camera_grid,
                    expand=True,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                    padding=ft.padding.all(5)
                )
            ]),
            expand=True
        )
    
    def _build_status_bar(self) -> ft.Container:
        """Construye la barra de estado."""
        self._status_bar = ft.Row([
            ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN, size=12),
            ft.Text("Sistema iniciado", expand=True),
            ft.Text("Última actualización: --"),
            ft.Text("v2.0.0-MVP")
        ])
        
        return ft.Container(
            content=self._status_bar,
            bgcolor=ft.Colors.SURFACE,
            padding=ft.padding.all(10),
            border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8)
        )
    
    # === Manejo de Eventos ===
    
    async def _on_connect_all_clicked(self, e):
        """Maneja clic en conectar todas las cámaras."""
        try:
            self._update_status("Conectando cámaras...", ft.Colors.ORANGE)
            results = await self.presenter.connect_all_cameras()
            
            connected_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            if connected_count == total_count:
                self._update_status(f"Todas las cámaras conectadas ({connected_count})", ft.Colors.GREEN)
            else:
                self._update_status(f"Conectadas {connected_count}/{total_count} cámaras", ft.Colors.ORANGE)
                
        except Exception as ex:
            self.logger.error(f"Error conectando cámaras: {str(ex)}")
            self._update_status("Error conectando cámaras", ft.Colors.RED)
    
    async def _on_disconnect_all_clicked(self, e):
        """Maneja clic en desconectar todas las cámaras."""
        try:
            self._update_status("Desconectando cámaras...", ft.Colors.ORANGE)
            await self.presenter.disconnect_all_cameras()
            self._update_status("Cámaras desconectadas", ft.Colors.BLUE)
            
        except Exception as ex:
            self.logger.error(f"Error desconectando cámaras: {str(ex)}")
            self._update_status("Error desconectando cámaras", ft.Colors.RED)
    
    async def _on_scan_clicked(self, e):
        """Maneja clic en escanear red."""
        if self._is_scanning:
            await self.presenter.stop_current_scan()
            self._update_scan_ui(False, 0, "Escaneo detenido")
        else:
            try:
                self._update_status("Iniciando escaneo de red...", ft.Colors.BLUE)
                success = await self.presenter.start_network_scan()
                
                if success:
                    self._update_scan_ui(True, 0, "Escaneo iniciado")
                else:
                    self._update_status("No se pudo iniciar escaneo", ft.Colors.RED)
                    
            except Exception as ex:
                self.logger.error(f"Error iniciando escaneo: {str(ex)}")
                self._update_status("Error iniciando escaneo", ft.Colors.RED)
    
    def _on_settings_clicked(self, e):
        """Maneja clic en configuración."""
        # TODO: Implementar diálogo de configuración
        self.logger.info("Abriendo configuración...")
    
    def _on_layout_changed(self, e):
        """Maneja cambio de layout de cámaras."""
        try:
            new_layout = int(e.control.value)
            asyncio.create_task(self._change_layout(new_layout))
        except Exception as ex:
            self.logger.error(f"Error cambiando layout: {str(ex)}")
    
    async def _change_layout(self, columns: int):
        """Cambia el layout de la grilla de cámaras."""
        success = await self.presenter.set_camera_layout(columns)
        if success:
            self._current_layout = columns
            if self._camera_grid and hasattr(self._camera_grid, 'runs_count'):
                self._camera_grid.runs_count = columns
            self.update()
            self._update_status(f"Layout cambiado a {columns} columnas", ft.Colors.BLUE)
    
    def _on_configure_scan_clicked(self, e):
        """Maneja clic en configurar escaneo."""
        # TODO: Implementar diálogo de configuración de escaneo
        self.logger.info("Configurando escaneo...")
    
    def _on_add_camera_clicked(self, e):
        """Maneja clic en agregar cámara."""
        # TODO: Implementar diálogo de agregar cámara
        self.logger.info("Agregando cámara...")
    
    def _on_refresh_clicked(self, e):
        """Maneja clic en actualizar."""
        self.logger.info("Actualizando vista...")
        self._refresh_camera_views()
    
    # === Callbacks del Presenter ===
    
    def _on_cameras_updated(self, cameras: List[CameraModel]):
        """Callback cuando se actualizan las cámaras."""
        self.logger.info(f"Actualizando vista con {len(cameras)} cámaras")
        self._update_camera_grid(cameras)
        self._update_camera_count(cameras)
    
    def _on_camera_status_changed(self, camera_id: str, status: str):
        """Callback cuando cambia el estado de una cámara."""
        self.logger.info(f"Cámara {camera_id}: {status}")
        
        if camera_id in self._camera_views:
            self._camera_views[camera_id].update()
    
    def _on_scan_progress(self, current: int, total: int, message: str):
        """Callback de progreso de escaneo."""
        if total > 0:
            progress = current / total
            self._update_scan_ui(True, progress, f"{message} ({current}/{total})")
    
    def _on_scan_completed(self, discovered_cameras: List[CameraModel]):
        """Callback cuando se completa el escaneo."""
        self._update_scan_ui(False, 1.0, f"Escaneo completado: {len(discovered_cameras)} cámaras encontradas")
        self._update_status(f"Escaneo completado: {len(discovered_cameras)} cámaras", ft.Colors.GREEN)
        
        # TODO: Mostrar diálogo con cámaras descubiertas
        self.logger.info(f"Escaneo completado: {len(discovered_cameras)} cámaras encontradas")
    
    def _on_error(self, error_message: str):
        """Callback de error."""
        self._update_status(f"Error: {error_message}", ft.Colors.RED)
        self.logger.error(f"Error en presenter: {error_message}")
    
    # === Utilidades de UI ===
    
    def _update_camera_grid(self, cameras: List[CameraModel]):
        """Actualiza la grilla de cámaras."""
        try:
            # Limpiar grilla existente
            if self._camera_grid and hasattr(self._camera_grid, 'controls'):
                self._camera_grid.controls.clear()
                self._camera_views.clear()
                
                # Agregar vistas de cámaras
                for camera in cameras:
                    camera_view = CameraView(camera.camera_id)
                    self._camera_views[camera.camera_id] = camera_view
                    camera_widget = camera_view.build()
                    if camera_widget:
                        self._camera_grid.controls.append(camera_widget)
                
                self.update()
            
        except Exception as e:
            self.logger.error(f"Error actualizando grilla de cámaras: {str(e)}")
    
    def _update_camera_count(self, cameras: List[CameraModel]):
        """Actualiza el contador de cámaras."""
        if self._camera_count_text:
            connected_count = len([c for c in cameras if c.is_connected])
            self._camera_count_text.value = f"Cámaras: {connected_count}/{len(cameras)}"
            self.update()
    
    def _update_status(self, message: str, color=ft.Colors.BLUE):
        """Actualiza la barra de estado."""
        if self._status_bar:
            # Recrear controles de la barra de estado para evitar errores de asignación
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Recrear la barra de estado con los nuevos valores
            self._status_bar.controls = [
                ft.Icon(ft.Icons.CIRCLE, color=color, size=12),
                ft.Text(message, expand=True),
                ft.Text(f"Última actualización: {timestamp}"),
                ft.Text("v2.0.0-MVP")
            ]
            
            self.update()
    
    def _update_scan_ui(self, is_scanning: bool, progress: float, message: str):
        """Actualiza la UI de escaneo."""
        self._is_scanning = is_scanning
        self._scan_progress = progress
        
        if self._scan_progress_bar:
            self._scan_progress_bar.visible = is_scanning
            self._scan_progress_bar.value = progress
            
        if self._scan_progress_text:
            self._scan_progress_text.value = message
            
        self.update()
    
    def _refresh_camera_views(self):
        """Refresca todas las vistas de cámaras."""
        for camera_view in self._camera_views.values():
            if hasattr(camera_view, 'update'):
                camera_view.update()
    
    def update(self):
        """Actualiza la vista."""
        if self.page:
            self.page.update()
    
    # === Inicialización ===
    
    async def initialize_async(self):
        """Inicializa la vista de forma asíncrona."""
        try:
            self.logger.info("🚀 Inicializando MainView")
            
            # Inicializar presenter
            await self.presenter.initialize()
            
            # Configurar página
            self.page.title = "Visor Universal de Cámaras v2.0"
            self.page.window.width = 1400
            self.page.window.height = 900
            self.page.window.min_width = 1000
            self.page.window.min_height = 700
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.padding = 0
            
            # Cargar estado inicial
            await self._load_initial_state()
            
            self.logger.info("✅ MainView inicializada")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando MainView: {str(e)}")
            raise
    
    async def _load_initial_state(self):
        """Carga el estado inicial de la aplicación."""
        try:
            # Obtener layout actual
            self._current_layout = self.presenter.get_current_layout()
            
            # Cargar cámaras activas
            active_cameras = self.presenter.get_active_cameras()
            
            # Actualizar estadísticas
            stats = self.presenter.get_application_stats()
            
            self.logger.info(f"Estado inicial cargado: {len(active_cameras)} cámaras, layout {self._current_layout}")
            
        except Exception as e:
            self.logger.error(f"Error cargando estado inicial: {str(e)}")
    
    async def cleanup_async(self):
        """Limpia recursos de la vista."""
        try:
            self.logger.info("🧹 Limpiando MainView")
            
            # Limpiar vistas de cámaras
            for camera_view in self._camera_views.values():
                if hasattr(camera_view, 'cleanup'):
                    await camera_view.cleanup()
            
            # Limpiar presenter
            await self.presenter.destroy()
            
            self.logger.info("✅ MainView limpiada")
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando MainView: {str(e)}") 