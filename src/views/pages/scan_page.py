#!/usr/bin/env python3
"""
ScanPage - Página de escaneo de red para descubrimiento de cámaras
================================================================

Página dedicada exclusivamente al escaneo y descubrimiento de cámaras IP.
Incluye:
- Configuración de rango de escaneo
- Progreso de escaneo en tiempo real
- Resultados con detalles de cámaras encontradas
- Opciones de conexión rápida
"""

import flet as ft
from typing import Optional, List, Callable
from ..components.common.modern_button import ModernButton, ModernIconButton
from ..components.common.stat_card import StatCard
from ..components.common.progress_indicator import ModernProgressBar


class ScanPage(ft.Container):
    """
    Página de escaneo de red - Funcionalidad limpia y enfocada.
    
    Esta página contiene toda la funcionalidad de escaneo que antes
    estaba mezclada en la vista principal.
    """
    
    def __init__(
        self,
        on_camera_found: Optional[Callable] = None,
        on_back_to_cameras: Optional[Callable] = None,
        **kwargs
    ):
        """
        Inicializa la página de escaneo.
        
        Args:
            on_camera_found: Callback cuando se encuentra una cámara
            on_back_to_cameras: Callback para volver a página principal
        """
        super().__init__(**kwargs)
        
        self.on_camera_found = on_camera_found
        self.on_back_to_cameras = on_back_to_cameras
        
        # Estados del escaneo
        self.is_scanning = False
        self.scan_progress = 0.0
        self.found_cameras = []
        self.scan_range = "192.168.1.1-254"
        
        # Configurar contenido
        self.content = self._build_page_content()
        
        # Configurar container principal
        self.expand = True
        self.bgcolor = ft.Colors.GREY_50
    
    def _build_page_content(self) -> ft.Column:
        """Construye el layout principal de la página."""
        
        # Header de la página
        page_header = self._build_page_header()
        
        # Contenido principal en dos columnas
        main_content = ft.Row([
            # Panel izquierdo: Configuración
            self._build_config_panel(),
            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
            # Panel derecho: Resultados
            self._build_results_panel()
        ],
        spacing=0,
        expand=True
        )
        
        return ft.Column([
            page_header,
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            main_content
        ],
        spacing=0,
        expand=True
        )
    
    def _build_page_header(self) -> ft.Container:
        """Construye el header de la página."""
        
        return ft.Container(
            content=ft.Row([
                # Botón de regreso
                ModernIconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Volver a cámaras",
                    variant="outlined",
                    on_click=self._handle_back
                ),
                ft.Container(width=16),
                # Título e información
                ft.Column([
                    ft.Text(
                        "Escaneo de Red",
                        size=20,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE
                    ),
                    ft.Text(
                        "Buscar cámaras IP en la red local",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ],
                spacing=4,
                tight=True
                ),
                ft.Container(expand=True),
                # Estado del escaneo
                self._build_scan_status()
            ]),
            padding=ft.padding.all(24),
            bgcolor=ft.Colors.SURFACE
        )
    
    def _build_scan_status(self) -> ft.Row:
        """Construye el indicador de estado del escaneo."""
        
        if self.is_scanning:
            status_text = "Escaneando..."
            status_color = ft.Colors.ORANGE_600
            status_icon = ft.Icons.SEARCH
        elif self.found_cameras:
            status_text = f"{len(self.found_cameras)} cámaras encontradas"
            status_color = ft.Colors.GREEN_600
            status_icon = ft.Icons.CHECK_CIRCLE
        else:
            status_text = "Listo para escanear"
            status_color = ft.Colors.ON_SURFACE_VARIANT
            status_icon = ft.Icons.NETWORK_CHECK
        
        return ft.Row([
            ft.Icon(status_icon, size=16, color=status_color),
            ft.Container(width=8),
            ft.Text(
                status_text,
                size=14,
                weight=ft.FontWeight.W_500,
                color=status_color
            )
        ])
    
    def _build_config_panel(self) -> ft.Container:
        """Construye el panel de configuración del escaneo."""
        
        return ft.Container(
            content=ft.Column([
                # Título del panel
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.PRIMARY),
                        ft.Container(width=8),
                        ft.Text(
                            "Configuración de Escaneo",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE
                        )
                    ]),
                    padding=ft.padding.all(16),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                    )
                ),
                
                # Configuración de rango
                self._build_range_config(),
                
                # Estadísticas rápidas
                self._build_scan_stats(),
                
                # Controles de escaneo
                self._build_scan_controls(),
                
                # Progreso del escaneo
                self._build_scan_progress()
                
            ],
            spacing=0,
            expand=True
            ),
            width=400,
            bgcolor=ft.Colors.SURFACE
        )
    
    def _build_range_config(self) -> ft.Container:
        """Construye la configuración del rango de escaneo."""
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Rango de IP",
                    size=14,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.ON_SURFACE
                ),
                ft.Container(height=8),
                ft.TextField(
                    value=self.scan_range,
                    hint_text="192.168.1.1-254",
                    prefix_icon=ft.Icons.ROUTER,
                    border_radius=8,
                    on_change=self._handle_range_change
                ),
                ft.Container(height=12),
                ft.Text(
                    "Formatos soportados:\n• 192.168.1.1-254\n• 192.168.1.0/24\n• 192.168.1.100",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT
                )
            ]),
            padding=ft.padding.all(16)
        )
    
    def _build_scan_stats(self) -> ft.Container:
        """Construye las estadísticas del escaneo."""
        
        return ft.Container(
            content=ft.Row([
                StatCard(
                    title="Encontradas",
                    value=len(self.found_cameras),
                    icon=ft.Icons.VIDEOCAM,
                    color_scheme="success",
                    width=120
                ),
                ft.Container(width=8),
                StatCard(
                    title="Progreso",
                    value=f"{self.scan_progress * 100:.0f}%",
                    icon=ft.Icons.SPEED,
                    color_scheme="primary",
                    width=120
                )
            ]),
            padding=ft.padding.all(16)
        )
    
    def _build_scan_controls(self) -> ft.Container:
        """Construye los controles del escaneo."""
        
        if self.is_scanning:
            primary_button = ModernButton(
                text="Detener Escaneo",
                icon=ft.Icons.STOP,
                variant="filled",
                color_scheme="error",
                on_click=self._handle_stop_scan,
                width=350
            )
        else:
            primary_button = ModernButton(
                text="Iniciar Escaneo",
                icon=ft.Icons.PLAY_ARROW,
                variant="filled",
                color_scheme="primary",
                on_click=self._handle_start_scan,
                width=350
            )
        
        return ft.Container(
            content=ft.Column([
                primary_button,
                ft.Container(height=12),
                ft.Row([
                    ModernButton(
                        text="Escaneo Rápido",
                        variant="outlined",
                        on_click=self._handle_quick_scan,
                        width=170
                    ),
                    ft.Container(width=10),
                    ModernButton(
                        text="Limpiar",
                        variant="text",
                        on_click=self._handle_clear_results,
                        width=170
                    )
                ])
            ]),
            padding=ft.padding.all(16)
        )
    
    def _build_scan_progress(self) -> ft.Container:
        """Construye el indicador de progreso del escaneo."""
        
        if not self.is_scanning and self.scan_progress == 0:
            return ft.Container()
        
        return ft.Container(
            content=ModernProgressBar(
                value=self.scan_progress if self.is_scanning else None,
                label="Escaneando red...",
                show_percentage=True,
                color_scheme="primary"
            ),
            padding=ft.padding.all(16)
        )
    
    def _build_results_panel(self) -> ft.Container:
        """Construye el panel de resultados."""
        
        return ft.Container(
            content=ft.Column([
                # Título del panel
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LIST, size=20, color=ft.Colors.PRIMARY),
                        ft.Container(width=8),
                        ft.Text(
                            "Cámaras Encontradas",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            f"{len(self.found_cameras)} dispositivos",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT
                        )
                    ]),
                    padding=ft.padding.all(16),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                    )
                ),
                
                # Lista de resultados
                self._build_results_list()
            ],
            spacing=0,
            expand=True
            ),
            expand=True,
            bgcolor=ft.Colors.SURFACE
        )
    
    def _build_results_list(self) -> ft.Container:
        """Construye la lista de resultados."""
        
        if not self.found_cameras:
            # Estado vacío
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(
                        ft.Icons.SEARCH_OFF,
                        size=48,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    ft.Container(height=16),
                    ft.Text(
                        "No se han encontrado cámaras",
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Inicia un escaneo para buscar dispositivos en la red",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=ft.padding.all(32),
                alignment=ft.alignment.center,
                expand=True
            )
            
            return empty_state
        
        # Lista con resultados
        camera_items = []
        for camera in self.found_cameras:
            camera_item = self._build_camera_result_item(camera)
            camera_items.append(camera_item)
        
        return ft.Container(
            content=ft.ListView(
                camera_items,
                spacing=8,
                padding=ft.padding.all(16)
            ),
            expand=True
        )
    
    def _build_camera_result_item(self, camera) -> ft.Container:
        """Construye un item de resultado de cámara."""
        
        return ft.Container(
            content=ft.Row([
                # Icono de cámara
                ft.Container(
                    content=ft.Icon(ft.Icons.VIDEOCAM, color=ft.Colors.PRIMARY),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    border_radius=8,
                    padding=ft.padding.all(8)
                ),
                ft.Container(width=12),
                
                # Información de la cámara
                ft.Column([
                    ft.Text(
                        getattr(camera, 'brand', 'Cámara IP'),
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
                ),
                
                ft.Container(expand=True),
                
                # Botón de conexión
                ModernButton(
                    text="Conectar",
                    variant="outlined",
                    color_scheme="primary",
                    on_click=lambda e, cam=camera: self._handle_connect_camera(cam),
                    width=100
                )
            ]),
            padding=ft.padding.all(16),
            bgcolor=None,  # Usar color dinámico del tema
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        )
    
    # Event Handlers
    def _handle_back(self, e):
        """Maneja el botón de regreso."""
        if self.on_back_to_cameras:
            self.on_back_to_cameras()
    
    def _handle_range_change(self, e):
        """Maneja cambio en el rango de escaneo."""
        self.scan_range = e.control.value
    
    def _handle_start_scan(self, e):
        """Maneja inicio del escaneo."""
        self.is_scanning = True
        self.scan_progress = 0.0
        self.found_cameras = []
        self._refresh_content()
        # TODO: Iniciar escaneo real
    
    def _handle_stop_scan(self, e):
        """Maneja detención del escaneo."""
        self.is_scanning = False
        self._refresh_content()
        # TODO: Detener escaneo real
    
    def _handle_quick_scan(self, e):
        """Maneja escaneo rápido."""
        # TODO: Implementar escaneo rápido
        pass
    
    def _handle_clear_results(self, e):
        """Maneja limpieza de resultados."""
        self.found_cameras = []
        self.scan_progress = 0.0
        self._refresh_content()
    
    def _handle_connect_camera(self, camera):
        """Maneja conexión a una cámara."""
        if self.on_camera_found:
            self.on_camera_found(camera)
    
    # Public Methods
    def update_scan_progress(self, progress: float):
        """Actualiza el progreso del escaneo."""
        self.scan_progress = progress
        self._refresh_content()
    
    def add_found_camera(self, camera):
        """Agrega una cámara encontrada."""
        self.found_cameras.append(camera)
        self._refresh_content()
    
    def finish_scan(self):
        """Finaliza el escaneo."""
        self.is_scanning = False
        self.scan_progress = 1.0
        self._refresh_content()
    
    def _refresh_content(self):
        """Refresca el contenido de la página."""
        self.content = self._build_page_content() 