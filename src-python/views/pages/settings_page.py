#!/usr/bin/env python3
"""
SettingsPage - Página de configuración de la aplicación
======================================================

Página para gestionar todas las configuraciones de la aplicación.
Incluye:
- Configuración de apariencia (tema claro/oscuro)
- Configuración de red
- Preferencias de usuario
- Ajustes avanzados
"""

import flet as ft
from typing import Optional, Callable
from ..components.common.theme_toggle import ThemeToggle, ThemeSelector
from ..components.common.modern_button import ModernButton


class SettingsPage(ft.Container):
    """Página de configuración de la aplicación."""
    
    def __init__(self, page: Optional[ft.Page] = None, **kwargs):
        super().__init__(**kwargs)
        
        self.page = page
        self.content = self._build_page_content()
        self.expand = True
        # Usar color dinámico en lugar de hardcodeado
        self.bgcolor = None  # Permitir que use el color de fondo del tema
    
    def _build_page_content(self) -> ft.Row:
        """Construye el contenido de la página."""
        
        # Panel lateral con navegación de configuración
        side_panel = self._build_side_panel()
        
        # Área principal de configuración
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
        """Construye el panel lateral con navegación."""
        
        # Header del panel
        panel_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.PRIMARY),
                ft.Container(width=8),
                ft.Text(
                    "Configuración",
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
        
        # Opciones de navegación
        nav_options = ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PALETTE),
                title=ft.Text("Apariencia"),
                selected=True,
                on_click=self._handle_nav_click
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.NETWORK_WIFI),
                title=ft.Text("Red"),
                on_click=self._handle_nav_click
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PERSON),
                title=ft.Text("Usuario"),
                on_click=self._handle_nav_click
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.TUNE),
                title=ft.Text("Avanzado"),
                on_click=self._handle_nav_click
            )
        ])
        
        return ft.Container(
            content=ft.Column([
                panel_header,
                nav_options
            ],
            spacing=0,
            expand=True
            ),
            width=250,
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.only(
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            )
            # REMOVIDO expand=True porque está en Row
        )
    
    def _build_main_content(self) -> ft.Container:
        """Construye el área principal de configuración."""
        
        # Título de la sección
        section_title = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PALETTE, size=24, color=ft.Colors.PRIMARY),
                ft.Container(width=12),
                ft.Text(
                    "Configuración de Apariencia",
                    size=20,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE
                )
            ]),
            padding=ft.padding.all(24),
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.only(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            )
        )
        
        # Contenido de configuración
        config_content = self._build_appearance_config()
        
        return ft.Container(
            content=ft.Column([
                section_title,
                config_content
            ],
            spacing=0,
            expand=True
            ),
            expand=True,
            bgcolor=None  # Usar color dinámico del tema
        )
    
    def _build_appearance_config(self) -> ft.Container:
        """Construye la configuración de apariencia."""
        
        # Selector de tema
        theme_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Tema de la aplicación",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE
                ),
                ft.Container(height=8),
                ft.Text(
                    "Cambia entre modo claro y oscuro",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT
                ),
                ft.Container(height=16),
                # Toggle de tema (si tenemos acceso a page)
                self._create_theme_control(),
                ft.Container(height=32),
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT),
                ft.Container(height=16),
                ft.Text(
                    "Configuraciones adicionales",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE
                ),
                ft.Container(height=16),
                ft.Text(
                    "Próximamente: Configuración de colores personalizados, tamaño de fuente y opciones de accesibilidad",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT
                )
            ]),
            padding=ft.padding.all(24),
            bgcolor=ft.Colors.SURFACE,
            border_radius=8
        )
        
        return ft.Container(
            content=ft.Column([
                theme_section
            ]),
            padding=ft.padding.all(24),
            expand=True
        )
    
    def _create_theme_control(self) -> ft.Container:
        """Crea el control para cambiar el tema."""
        if self.page is not None:
            # Usar ThemeToggle si tenemos acceso a la página
            theme_toggle = ThemeToggle(
                self.page,
                on_theme_change=self._handle_theme_change
            )
            return ft.Container(
                content=theme_toggle,
                padding=ft.padding.all(16),
                bgcolor=ft.Colors.GREY_100,
                border_radius=8
            )
        else:
            # Placeholder si no tenemos acceso a la página
            return ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Toggle de tema",
                        size=14,
                        color=ft.Colors.ON_SURFACE
                    ),
                    ft.Text(
                        "Configuración de tema no disponible",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ]),
                padding=ft.padding.all(16),
                bgcolor=ft.Colors.GREY_100,
                border_radius=8
            )
    
    def _handle_nav_click(self, e):
        """Maneja clics en la navegación."""
        # TODO: Implementar navegación entre secciones
        pass
    
    def _handle_theme_change(self, new_theme: str):
        """Maneja cambios en el tema."""
        # El theme_service ya maneja el cambio, aquí podríamos
        # agregar lógica adicional si es necesario
        pass
    
    def set_page(self, page: ft.Page):
        """Establece la página para habilitar funcionalidades de tema."""
        self.page = page
        # Reconstruir contenido con acceso a la página
        self.content = self._build_page_content()
        self.update() 