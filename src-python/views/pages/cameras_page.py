#!/usr/bin/env python3
"""
CamerasPage - Página principal de gestión de cámaras
====================================================

Página principal donde los usuarios ven y gestionan sus cámaras conectadas.
Incluye:
- Grid de cámaras con streams en vivo
- Panel lateral con controles
- Toolbar con acciones principales
- Vista limpia y enfocada en contenido
"""

import flet as ft
from typing import Optional, List, Callable
from ..components.common.modern_button import ModernButton, ModernIconButton
from ..components.common.stat_card import StatCard


class CamerasPage(ft.Container):
    """
    Página principal de cámaras - Vista limpia y enfocada.
    
    Esta página reemplaza la funcionalidad principal del main_view original
    pero de forma modular y organizada.
    """
    
    def __init__(
        self,
        on_scan_request: Optional[Callable] = None,
        **kwargs
    ):
        """
        Inicializa la página de cámaras.
        
        Args:
            on_scan_request: Callback para solicitar ir a página de escaneo
        """
        super().__init__(**kwargs)
        
        self.on_scan_request = on_scan_request
        
        # Estados de la página
        self.cameras = []  # Lista de cámaras conectadas
        self.selected_camera = None
        self.is_recording = False
        
        # Configurar contenido
        self.content = self._build_page_content()
        
        # Configurar container principal
        self.expand = True
        # Usar color dinámico en lugar de hardcodeado
        self.bgcolor = None  # Permitir que use el color de fondo del tema
    
    def _build_page_content(self) -> ft.Row:
        """Construye el layout principal de la página."""
        
        # Panel lateral izquierdo con controles
        side_panel = self._build_side_panel()
        
        # Área principal de contenido
        main_content = self._build_main_content()
        
        return ft.Row([
            side_panel,
            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
            main_content
        ],
        spacing=0,
        expand=True  # Row se expande verticalmente
        )
    
    def _build_side_panel(self) -> ft.Container:
        """Construye el panel lateral con controles."""
        
        # Header del panel
        panel_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.VIDEOCAM, size=20, color=ft.Colors.PRIMARY),
                ft.Container(width=8),
                ft.Text(
                    "Cámaras Activas",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE
                )
            ]),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.only(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            )
        )
        
        # Estadísticas rápidas
        stats_section = self._build_stats_section()
        
        # Acciones rápidas
        actions_section = self._build_actions_section()
        
        # Lista de cámaras
        cameras_list = self._build_cameras_list()
        
        return ft.Container(
            content=ft.Column([
                panel_header,
                stats_section,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                actions_section,
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                cameras_list
            ],
            spacing=0,
            expand=True
            ),
            width=320,
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.only(
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            )
            # REMOVIDO expand=True porque está en Row
        )
    
    def _build_stats_section(self) -> ft.Container:
        """Construye la sección de estadísticas."""
        
        # Datos de ejemplo - en implementación real vendría del presenter
        active_cameras = len(self.cameras)
        recording_count = sum(1 for cam in self.cameras if getattr(cam, 'is_recording', False))
        
        stats_row = ft.Row([
            StatCard(
                title="Activas",
                value=active_cameras,
                icon=ft.Icons.VIDEOCAM,
                color_scheme="primary",
                width=140
            ),
            ft.Container(width=8),
            StatCard(
                title="Grabando", 
                value=recording_count,
                icon=ft.Icons.FIBER_MANUAL_RECORD,
                color_scheme="error" if recording_count > 0 else "surface",
                width=140
            )
        ])
        
        return ft.Container(
            content=stats_row,
            padding=ft.padding.all(16)
        )
    
    def _build_actions_section(self) -> ft.Container:
        """Construye la sección de acciones rápidas."""
        
        # Botón principal para buscar más cámaras
        scan_button = ModernButton(
            text="Buscar Cámaras",
            icon=ft.Icons.SEARCH,
            variant="filled",
            color_scheme="primary",
            on_click=self._handle_scan_request,
            width=280
        )
        
        # Botones secundarios
        actions_row = ft.Row([
            ModernIconButton(
                icon=ft.Icons.REFRESH,
                tooltip="Actualizar conexiones",
                variant="outlined",
                on_click=self._handle_refresh
            ),
            ModernIconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Configuración rápida",
                variant="outlined", 
                on_click=self._handle_quick_settings
            ),
            ModernIconButton(
                icon=ft.Icons.FULLSCREEN,
                tooltip="Vista completa",
                variant="outlined",
                on_click=self._handle_fullscreen
            )
        ],
        spacing=8
        )
        
        return ft.Container(
            content=ft.Column([
                scan_button,
                ft.Container(height=16),
                actions_row
            ]),
            padding=ft.padding.all(16)
        )
    
    def _build_cameras_list(self) -> ft.Container:
        """Construye la lista de cámaras conectadas."""
        
        if not self.cameras:
            # Estado vacío
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.VIDEOCAM_OFF,
                        size=48,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "No hay cámaras conectadas",
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Haz clic en 'Buscar Cámaras' para encontrar dispositivos en la red",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
                ),
                padding=ft.padding.all(32),
                alignment=ft.alignment.center
            )
            
            return ft.Container(
                content=empty_state,
                expand=True
            )
        
        # Lista de cámaras (implementación futura)
        cameras_items = []
        for camera in self.cameras:
            camera_item = self._build_camera_item(camera)
            cameras_items.append(camera_item)
        
        return ft.Container(
            content=ft.ListView(
                cameras_items,
                spacing=8,
                padding=ft.padding.all(16)
            ),
            expand=True
        )
    
    def _build_camera_item(self, camera) -> ft.Container:
        """Construye un item individual de cámara."""
        
        # Información de la cámara
        camera_info = ft.Column([
            ft.Text(
                getattr(camera, 'name', 'Cámara IP'),
                size=14,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.ON_SURFACE
            ),
            ft.Text(
                getattr(camera, 'ip', '192.168.1.100'),
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
        ],
        spacing=4,
        tight=True
        )
        
        # Estado de conexión
        is_connected = getattr(camera, 'is_connected', True)
        status_icon = ft.Icon(
            ft.Icons.CIRCLE,
            size=12,
            color=ft.Colors.GREEN_500 if is_connected else ft.Colors.RED_500
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.VIDEOCAM, size=20, color=ft.Colors.PRIMARY),
                ft.Container(width=12),
                camera_info,
                ft.Container(expand=True),
                status_icon
            ]),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
            ink=True,
            on_click=lambda e, cam=camera: self._handle_camera_select(cam)
        )
    
    def _build_main_content(self) -> ft.Container:
        """Construye el área principal de contenido."""
        
        if not self.cameras:
            # Vista de bienvenida
            welcome_content = self._build_welcome_content()
            return ft.Container(
                content=welcome_content,
                expand=True,
                padding=ft.padding.all(32),
                alignment=ft.alignment.center
            )
        
        # Grid de cámaras (implementación futura)
        return self._build_cameras_grid()
    
    def _build_welcome_content(self) -> ft.Column:
        """Construye el contenido de bienvenida."""
        
        return ft.Column([
            ft.Icon(
                ft.Icons.VIDEOCAM,
                size=80,
                color=ft.Colors.PRIMARY
            ),
            ft.Container(height=24),
            ft.Text(
                "Bienvenido al Visor Universal de Cámaras",
                size=24,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=16),
            ft.Text(
                "Conecta y visualiza cámaras IP de múltiples marcas en una sola interfaz",
                size=16,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=32),
            ModernButton(
                text="Comenzar Escaneo",
                icon=ft.Icons.PLAY_ARROW,
                variant="filled",
                color_scheme="primary",
                on_click=self._handle_scan_request,
                width=200
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0
        )
    
    def _build_cameras_grid(self) -> ft.Container:
        """Construye el grid de cámaras con streams."""
        
        # Implementación futura del grid de cámaras
        # Por ahora mostrar placeholder
        
        placeholder = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Grid de Cámaras",
                    size=20,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE
                ),
                ft.Text(
                    "Aquí se mostrarán los streams de las cámaras conectadas",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            expand=True,
            padding=ft.padding.all(32),
            alignment=ft.alignment.center
        )
        
        return placeholder
    
    # Event Handlers
    def _handle_scan_request(self, e):
        """Maneja solicitud de escaneo."""
        if self.on_scan_request:
            self.on_scan_request()
    
    def _handle_refresh(self, e):
        """Maneja actualización de conexiones."""
        # TODO: Implementar refresh de cámaras
        pass
    
    def _handle_quick_settings(self, e):
        """Maneja configuración rápida."""
        # TODO: Mostrar dialog de configuración rápida
        pass
    
    def _handle_fullscreen(self, e):
        """Maneja vista completa."""
        # TODO: Implementar vista fullscreen
        pass
    
    def _handle_camera_select(self, camera):
        """Maneja selección de cámara."""
        self.selected_camera = camera
        # TODO: Actualizar vista principal con cámara seleccionada
    
    # Public Methods
    def add_camera(self, camera):
        """Agrega una nueva cámara."""
        self.cameras.append(camera)
        self._refresh_content()
    
    def remove_camera(self, camera):
        """Elimina una cámara."""
        if camera in self.cameras:
            self.cameras.remove(camera)
            self._refresh_content()
    
    def update_cameras(self, cameras_list: List):
        """Actualiza la lista completa de cámaras."""
        self.cameras = cameras_list
        self._refresh_content()
    
    def _refresh_content(self):
        """Refresca el contenido de la página."""
        self.content = self._build_page_content() 