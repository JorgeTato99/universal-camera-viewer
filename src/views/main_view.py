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
        """Construye la interfaz principal moderna."""
        self._main_container = ft.Column([
            # === BARRA DE HERRAMIENTAS MODERNA ===
            self._build_toolbar(),
            
            # === CONTENIDO PRINCIPAL ===
            ft.Row([
                # === PANEL LATERAL IZQUIERDO ===
                ft.Container(
                    content=self._build_side_panel(),
                    width=300,
                    padding=ft.padding.all(16),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=ft.border_radius.only(
                        bottom_left=12,
                        top_right=12,
                        bottom_right=12
                    ),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=8,
                        color=ft.Colors.with_opacity(0.06, ft.Colors.SHADOW),
                        offset=ft.Offset(2, 0)
                    ),
                    border=ft.border.only(
                        right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                    )
                    # REMOVIDO expand=True porque está en Row
                ),
                
                # === ÁREA PRINCIPAL DE CÁMARAS ===
                ft.Container(
                    content=self._build_camera_area(),
                    expand=True,
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.WHITE
                )
            ], 
            spacing=0,
            expand=True  # CORRECCIÓN: Row se expande verticalmente
            ),
            
            # === BARRA DE ESTADO MODERNA ===
            self._build_status_bar()
        ],
        expand=True,
        spacing=0
        )
        
        return self._main_container
    
    def _build_toolbar(self) -> ft.Container:
        """Construye la barra de herramientas moderna."""
        self._toolbar = ft.Row([
            # === LOGO Y BRANDING MODERNO ===
            ft.Container(
                content=ft.Row([
                    # Icono principal con mejor diseño
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.VIDEO_CAMERA_FRONT_ROUNDED,
                            color=ft.Colors.PRIMARY,
                            size=32
                        ),
                        padding=ft.padding.all(8),
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        border_radius=12,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY),
                            offset=ft.Offset(0, 2)
                        )
                    ),
                    
                    ft.Container(width=12),  # Spacing moderno
                    
                    # Título con mejor tipografía
                    ft.Column([
                        ft.Text(
                            "Visor Universal de Cámaras",
                            size=22,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE
                        ),
                        ft.Text(
                            "Multi-Marca v2.0",
                            size=12,
                            weight=ft.FontWeight.W_400,
                            color=ft.Colors.ON_SURFACE_VARIANT
                        )
                    ], spacing=0, tight=True)
                ], tight=True),
                padding=ft.padding.symmetric(horizontal=8)
            ),
            
            ft.Container(expand=True),  # Spacer flexible
            
            # === CONTROLES PRINCIPALES MODERNOS ===
            ft.Container(
                content=ft.Row([
                    # Botón conectar todas - Estilo Filled
                    ft.FilledButton(
                        text="Conectar Todas",
                        icon=ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED,
                        on_click=self._on_connect_all_clicked,
                        style=ft.ButtonStyle(
                            bgcolor={
                                ft.ControlState.DEFAULT: ft.Colors.GREEN_600,
                                ft.ControlState.HOVERED: ft.Colors.GREEN_700,
                            },
                            color={
                                ft.ControlState.DEFAULT: ft.Colors.WHITE,
                            },
                            elevation={
                                ft.ControlState.DEFAULT: 2,
                                ft.ControlState.HOVERED: 4,
                            },
                            shadow_color=ft.Colors.GREEN_400,
                            shape=ft.RoundedRectangleBorder(radius=12)
                        )
                    ),
                    
                    ft.Container(width=8),  # Spacing
                    
                    # Botón desconectar - Estilo Outlined
                    ft.OutlinedButton(
                        text="Desconectar",
                        icon=ft.Icons.STOP_CIRCLE_ROUNDED,
                        on_click=self._on_disconnect_all_clicked,
                        style=ft.ButtonStyle(
                            color={
                                ft.ControlState.DEFAULT: ft.Colors.RED_600,
                                ft.ControlState.HOVERED: ft.Colors.RED_700,
                            },
                            side={
                                ft.ControlState.DEFAULT: ft.BorderSide(2, ft.Colors.RED_600),
                                ft.ControlState.HOVERED: ft.BorderSide(2, ft.Colors.RED_700),
                            },
                            bgcolor={
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.08, ft.Colors.RED_600),
                            },
                            shape=ft.RoundedRectangleBorder(radius=12)
                        )
                    ),
                    
                    ft.Container(width=16),  # Separador visual
                    
                    # Botón escanear red - Estilo Filled Tonal
                    ft.FilledTonalButton(
                        text="Escanear Red",
                        icon=ft.Icons.RADAR_ROUNDED,
                        on_click=self._on_scan_clicked,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            elevation={
                                ft.ControlState.DEFAULT: 1,
                                ft.ControlState.HOVERED: 3,
                            }
                        )
                    ),
                    
                    ft.Container(width=8),  # Spacing
                    
                    # Botón configuración - Estilo Icon Button moderno
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.SETTINGS_ROUNDED,
                            tooltip="Configuración",
                            on_click=self._on_settings_clicked,
                            icon_color=ft.Colors.PRIMARY,
                            bgcolor=ft.Colors.GREY_100,
                            style=ft.ButtonStyle(
                                shape=ft.CircleBorder(),
                                elevation={
                                    ft.ControlState.DEFAULT: 0,
                                    ft.ControlState.HOVERED: 2,
                                }
                            )
                        ),
                        tooltip="Configuración de la aplicación"
                    )
                ], tight=True),
                padding=ft.padding.symmetric(horizontal=8)
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        return ft.Container(
            content=self._toolbar,
            bgcolor=ft.Colors.SURFACE,
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, ft.Colors.SHADOW),
                offset=ft.Offset(0, 2)
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        )
    
    def _build_side_panel(self) -> ft.Column:
        """Construye el panel lateral moderno con controles."""
        return ft.Column([
            # === HEADER DEL PANEL ===
            ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.CONTROL_CAMERA_ROUNDED,
                        color=ft.Colors.PRIMARY,
                        size=24
                    ),
                    ft.Container(width=8),
                    ft.Text(
                        "Panel de Control",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE
                    )
                ], tight=True),
                padding=ft.padding.all(16),
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                border_radius=12,
                margin=ft.margin.only(bottom=12)
            ),
            
            # === CONTROLES DE LAYOUT MODERNOS ===
            self._build_layout_controls(),
            
            ft.Container(height=8),  # Spacing consistente
            
            # === ESTADÍSTICAS MEJORADAS ===
            self._build_statistics_section(),
            
            ft.Container(height=8),  # Spacing consistente
            
            # === CONTROLES DE ESCANEO MODERNOS ===
            self._build_scan_controls(),
            
            ft.Container(expand=True),  # Spacer flexible
            
            # === PROGRESO DE ESCANEO ===
            self._build_scan_progress()
        ], spacing=0, tight=True)
    
    def _build_layout_controls(self) -> ft.Container:
        """Construye controles modernos de layout de cámaras."""
        self._layout_controls = ft.Column([
            # Header con icono
            ft.Row([
                ft.Icon(
                    ft.Icons.VIEW_MODULE_ROUNDED,
                    color=ft.Colors.SECONDARY,
                    size=20
                ),
                ft.Container(width=8),
                ft.Text(
                    "Layout de Cámaras",
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.ON_SURFACE,
                    size=16
                )
            ], tight=True),
            
            ft.Container(height=12),
            
            # Selector de columnas mejorado
            ft.Row([
                ft.Icon(
                    ft.Icons.VIEW_COLUMN_ROUNDED,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    size=16
                ),
                ft.Container(width=8),
                ft.Text(
                    "Columnas:",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    size=14,
                    weight=ft.FontWeight.W_500
                ),
                ft.Container(width=8),
                ft.Dropdown(
                    value=str(self._current_layout),
                    options=[
                        ft.dropdown.Option("1", "1 Col"),
                        ft.dropdown.Option("2", "2 Cols"),
                        ft.dropdown.Option("3", "3 Cols"),
                        ft.dropdown.Option("4", "4 Cols"),
                        ft.dropdown.Option("6", "6 Cols"),
                    ],
                    width=80,
                    on_change=self._on_layout_changed,
                    border_color=ft.Colors.OUTLINE_VARIANT,
                    bgcolor=ft.Colors.SURFACE
                )
            ], tight=True)
        ], spacing=0, tight=True)
        
        return ft.Container(
            content=self._layout_controls,
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.SURFACE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.08, ft.Colors.SHADOW),
                offset=ft.Offset(0, 1)
            )
        )
    
    def _build_statistics_section(self) -> ft.Container:
        """Construye la sección moderna de estadísticas."""
        self._camera_count_text = ft.Text(
            "Cámaras: 0/0",
            size=14,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.ON_SURFACE
        )
        
        return ft.Container(
            content=ft.Column([
                # Header con icono
                ft.Row([
                    ft.Icon(
                        ft.Icons.ANALYTICS_ROUNDED,
                        color=ft.Colors.TERTIARY,
                        size=20
                    ),
                    ft.Container(width=8),
                    ft.Text(
                        "Estadísticas",
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE,
                        size=16
                    )
                ], tight=True),
                
                ft.Container(height=12),
                
                # Métricas con iconos
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.VIDEOCAM_ROUNDED, size=16, color=ft.Colors.GREEN_600),
                        ft.Container(width=8),
                        self._camera_count_text
                    ], tight=True),
                    
                    ft.Container(height=8),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=16, color=ft.Colors.BLUE_600),
                        ft.Container(width=8),
                        ft.Text(
                            "Estado: Listo",
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT
                        )
                    ], tight=True),
                    
                    ft.Container(height=8),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=16, color=ft.Colors.ORANGE_600),
                        ft.Container(width=8),
                        ft.Text(
                            "Última conexión: --",
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT
                        )
                    ], tight=True)
                ], spacing=0, tight=True)
            ], spacing=0, tight=True),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.SURFACE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.08, ft.Colors.SHADOW),
                offset=ft.Offset(0, 1)
            )
        )
    
    def _build_scan_controls(self) -> ft.Container:
        """Construye controles modernos de escaneo."""
        self._network_field = ft.TextField(
            label="Red a escanear",
            value="192.168.1.0/24",
            hint_text="Ej: 192.168.1.0/24",
            prefix_icon=ft.Icons.NETWORK_CHECK_ROUNDED,
            border_color=ft.Colors.OUTLINE_VARIANT,
            bgcolor=ft.Colors.SURFACE,
            border_radius=8
        )
        
        self._ports_field = ft.TextField(
            label="Puertos",
            value="80,8080,554",
            hint_text="Ej: 80,8080,554",
            prefix_icon=ft.Icons.SETTINGS_ETHERNET_ROUNDED,
            border_color=ft.Colors.OUTLINE_VARIANT,
            bgcolor=ft.Colors.SURFACE,
            border_radius=8
        )
        
        return ft.Container(
            content=ft.Column([
                # Header con icono
                ft.Row([
                    ft.Icon(
                        ft.Icons.NETWORK_PING_ROUNDED,
                        color=ft.Colors.SECONDARY,
                        size=20
                    ),
                    ft.Container(width=8),
                    ft.Text(
                        "Escaneo de Red",
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE,
                        size=16
                    )
                ], tight=True),
                
                ft.Container(height=12),
                
                # Campos de entrada mejorados
                self._network_field,
                ft.Container(height=8),
                self._ports_field,
                
                ft.Container(height=16),
                
                # Botón de configuración mejorado
                ft.FilledTonalButton(
                    text="Configurar Escaneo",
                    icon=ft.Icons.TUNE_ROUNDED,
                    on_click=self._on_configure_scan_clicked,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        elevation={
                            ft.ControlState.DEFAULT: 1,
                            ft.ControlState.HOVERED: 2,
                        }
                    )
                )
            ], spacing=0, tight=True),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.SURFACE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.08, ft.Colors.SHADOW),
                offset=ft.Offset(0, 1)
            )
        )
    
    def _build_scan_progress(self) -> ft.Container:
        """Construye indicador moderno de progreso de escaneo."""
        self._scan_progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            bgcolor=ft.Colors.GREY_200,
            color=ft.Colors.PRIMARY,
            border_radius=8
        )
        
        self._scan_progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER
        )
        
        return ft.Container(
            content=ft.Column([
                # Header con icono
                ft.Row([
                    ft.Icon(
                        ft.Icons.SYNC_ROUNDED,
                        color=ft.Colors.PRIMARY,
                        size=20
                    ),
                    ft.Container(width=8),
                    ft.Text(
                        "Progreso de Escaneo",
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE,
                        size=16
                    )
                ], tight=True),
                
                ft.Container(height=12),
                
                # Barra de progreso con diseño moderno
                ft.Container(
                    content=self._scan_progress_bar,
                    border_radius=8,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=2,
                        color=ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY),
                        offset=ft.Offset(0, 1)
                    )
                ),
                
                ft.Container(height=8),
                
                # Texto de progreso
                self._scan_progress_text
            ], spacing=0, tight=True),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.SURFACE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.08, ft.Colors.SHADOW),
                offset=ft.Offset(0, 1)
            )
        )
    
    def _build_camera_area(self) -> ft.Container:
        """Construye el área principal moderna de cámaras."""
        self._camera_grid = ft.GridView(
            expand=True,
            runs_count=self._current_layout,
            max_extent=400,
            child_aspect_ratio=1.3,
            spacing=16,
            run_spacing=16,
            padding=ft.padding.all(16)
        )
        
        return ft.Container(
            content=ft.Column([
                # === HEADER DEL ÁREA DE CÁMARAS ===
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(
                                ft.Icons.VIDEOCAM_ROUNDED,
                                color=ft.Colors.PRIMARY,
                                size=28
                            ),
                            ft.Container(width=12),
                            ft.Column([
                                ft.Text(
                                    "Cámaras Activas",
                                    size=20,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.ON_SURFACE
                                ),
                                ft.Text(
                                    "Monitor en tiempo real",
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT
                                )
                            ], spacing=0, tight=True)
                        ], tight=True),
                        
                        ft.Container(expand=True),
                        
                        # Controles de acción rápida
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_ROUNDED,
                                tooltip="Agregar cámara",
                                on_click=self._on_add_camera_clicked,
                                icon_color=ft.Colors.PRIMARY,
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                style=ft.ButtonStyle(
                                    shape=ft.CircleBorder(),
                                    elevation={
                                        ft.ControlState.DEFAULT: 2,
                                        ft.ControlState.HOVERED: 4,
                                    }
                                )
                            ),
                            ft.Container(width=8),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH_ROUNDED,
                                tooltip="Actualizar vista",
                                on_click=self._on_refresh_clicked,
                                icon_color=ft.Colors.SECONDARY,
                                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                style=ft.ButtonStyle(
                                    shape=ft.CircleBorder(),
                                    elevation={
                                        ft.ControlState.DEFAULT: 2,
                                        ft.ControlState.HOVERED: 4,
                                    }
                                )
                            )
                        ], tight=True)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.SURFACE,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    margin=ft.margin.only(bottom=16),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=4,
                        color=ft.Colors.with_opacity(0.08, ft.Colors.SHADOW),
                        offset=ft.Offset(0, 2)
                    )
                ),
                
                # === GRILLA DE CÁMARAS ===
                ft.Container(
                    content=self._camera_grid,
                    expand=True,
                    bgcolor=ft.Colors.SURFACE,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=6,
                        color=ft.Colors.with_opacity(0.10, ft.Colors.SHADOW),
                        offset=ft.Offset(0, 2)
                    )
                )
            ], spacing=0, tight=True)
        )
    
    def _build_status_bar(self) -> ft.Container:
        """Construye la barra de estado moderna."""
        self._status_text = ft.Text(
            "Listo para conectar",
            size=14,
            color=ft.Colors.ON_SURFACE_VARIANT
        )
        
        return ft.Container(
            content=ft.Row([
                # Indicador de estado con icono
                ft.Row([
                    ft.Icon(
                        ft.Icons.CIRCLE,
                        size=12,
                        color=ft.Colors.GREEN_500
                    ),
                    ft.Container(width=8),
                    self._status_text
                ], tight=True),
                
                ft.Container(expand=True),
                
                # Información del sistema
                ft.Row([
                    ft.Icon(
                        ft.Icons.COMPUTER_ROUNDED,
                        size=16,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Container(width=8),
                    ft.Text(
                        "Visor Universal v2.0",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(width=16),
                    ft.Icon(
                        ft.Icons.UPDATE_ROUNDED,
                        size=16,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Container(width=8),
                    ft.Text(
                        "Conectado",
                        size=12,
                        color=ft.Colors.GREEN_600,
                        weight=ft.FontWeight.W_500
                    )
                ], tight=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor=ft.Colors.SURFACE,
            border_radius=ft.border_radius.only(bottom_left=12, bottom_right=12),
            border=ft.border.only(
                top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.06, ft.Colors.SHADOW),
                offset=ft.Offset(0, -1)
            )
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
        """Actualiza el mensaje de estado en la barra inferior."""
        try:
            if hasattr(self, '_status_text') and self._status_text:
                self._status_text.value = message
                self._status_text.color = color
                
                if hasattr(self.page, 'update'):
                    self.page.update()
                    
        except Exception as e:
            self.logger.error(f"Error actualizando estado: {e}")
    
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