#!/usr/bin/env python3
"""
ModernButton - Botones modernos con Material Design 3
=====================================================

Implementación de botones consistentes con el sistema de diseño:
- Filled, Outlined, Text, Icon buttons
- Estados interactivos (hover, pressed, disabled)
- Iconos y colores semánticos
- Elevación y sombras apropiadas
"""

import flet as ft
from typing import Optional, Callable


class ModernButton(ft.Container):
    """
    Botón moderno con Material Design 3.
    
    Soporta múltiples variantes:
    - filled: Botón principal con color de fondo
    - outlined: Botón secundario con borde
    - text: Botón terciario sin fondo
    """
    
    def __init__(
        self,
        text: str,
        variant: str = "filled",  # filled, outlined, text
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        color_scheme: str = "primary",  # primary, secondary, tertiary, error
        disabled: bool = False,
        width: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.text = text
        self.variant = variant
        self.icon = icon
        self.on_click = on_click
        self.color_scheme = color_scheme
        self.disabled = disabled
        self.width = width
        
        # Configurar el contenido directamente
        colors = self._get_color_scheme()
        
        # Crear botón según variante y asignarlo como contenido
        if self.variant == "filled":
            self.content = self._build_filled_button(colors)
        elif self.variant == "outlined":
            self.content = self._build_outlined_button(colors)
        elif self.variant == "text":
            self.content = self._build_text_button(colors)
        else:
            # Por defecto: filled
            self.content = self._build_filled_button(colors)
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema de color especificado."""
        schemes = {
            "primary": {
                "main": ft.Colors.PRIMARY,
                "on_main": ft.Colors.ON_PRIMARY,
                "container": ft.Colors.PRIMARY_CONTAINER,
                "on_container": ft.Colors.ON_PRIMARY_CONTAINER
            },
            "secondary": {
                "main": ft.Colors.SECONDARY,
                "on_main": ft.Colors.ON_SECONDARY,
                "container": ft.Colors.SECONDARY_CONTAINER,
                "on_container": ft.Colors.ON_SECONDARY_CONTAINER
            },
            "tertiary": {
                "main": ft.Colors.TERTIARY,
                "on_main": ft.Colors.ON_TERTIARY,
                "container": ft.Colors.TERTIARY_CONTAINER,
                "on_container": ft.Colors.ON_TERTIARY_CONTAINER
            },
            "error": {
                "main": ft.Colors.ERROR,
                "on_main": ft.Colors.ON_ERROR,
                "container": ft.Colors.ERROR_CONTAINER,
                "on_container": ft.Colors.ON_ERROR_CONTAINER
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_filled_button(self, colors: dict) -> ft.FilledButton:
        """Construye botón filled (principal)."""
        return ft.FilledButton(
            text=self.text,
            icon=self.icon,
            on_click=self.on_click,
            disabled=self.disabled,
            width=self.width,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: colors["main"],
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.9, colors["main"]),
                    ft.ControlState.PRESSED: ft.Colors.with_opacity(0.8, colors["main"]),
                    ft.ControlState.DISABLED: ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)
                },
                color={
                    ft.ControlState.DEFAULT: colors["on_main"],
                    ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
                },
                elevation={
                    ft.ControlState.DEFAULT: 1,
                    ft.ControlState.HOVERED: 3,
                    ft.ControlState.PRESSED: 1,
                    ft.ControlState.DISABLED: 0
                },
                shadow_color=colors["main"],
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.padding.symmetric(horizontal=24, vertical=12)
            )
        )
    
    def _build_outlined_button(self, colors: dict) -> ft.OutlinedButton:
        """Construye botón outlined (secundario)."""
        return ft.OutlinedButton(
            text=self.text,
            icon=self.icon,
            on_click=self.on_click,
            disabled=self.disabled,
            width=self.width,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: colors["main"],
                    ft.ControlState.HOVERED: colors["main"],
                    ft.ControlState.PRESSED: colors["main"],
                    ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
                },
                side={
                    ft.ControlState.DEFAULT: ft.BorderSide(1, colors["main"]),
                    ft.ControlState.HOVERED: ft.BorderSide(1, colors["main"]),
                    ft.ControlState.PRESSED: ft.BorderSide(1, colors["main"]),
                    ft.ControlState.DISABLED: ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE))
                },
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.08, colors["main"]),
                    ft.ControlState.PRESSED: ft.Colors.with_opacity(0.12, colors["main"])
                },
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.padding.symmetric(horizontal=24, vertical=12)
            )
        )
    
    def _build_text_button(self, colors: dict) -> ft.TextButton:
        """Construye botón text (terciario)."""
        return ft.TextButton(
            text=self.text,
            icon=self.icon,
            on_click=self.on_click,
            disabled=self.disabled,
            width=self.width,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: colors["main"],
                    ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
                },
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.08, colors["main"]),
                    ft.ControlState.PRESSED: ft.Colors.with_opacity(0.12, colors["main"])
                },
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            )
        )


class ModernIconButton(ft.Container):
    """
    Botón de icono moderno con Material Design 3.
    
    Perfecto para acciones secundarias y controles de UI.
    """
    
    def __init__(
        self,
        icon: str,
        tooltip: Optional[str] = None,
        on_click: Optional[Callable] = None,
        variant: str = "standard",  # standard, filled, outlined
        color_scheme: str = "primary",
        disabled: bool = False,
        size: int = 24,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.icon = icon
        self.tooltip = tooltip
        self.on_click = on_click
        self.variant = variant
        self.color_scheme = color_scheme
        self.disabled = disabled
        self.size = size
        
        # Configurar el contenido directamente
        colors = self._get_color_scheme()
        
        if self.variant == "filled":
            self.content = self._build_filled_icon_button(colors)
        elif self.variant == "outlined":
            self.content = self._build_outlined_icon_button(colors)
        else:
            self.content = self._build_standard_icon_button(colors)
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema especificado."""
        schemes = {
            "primary": {
                "main": ft.Colors.PRIMARY,
                "container": ft.Colors.PRIMARY_CONTAINER,
                "on_container": ft.Colors.ON_PRIMARY_CONTAINER
            },
            "secondary": {
                "main": ft.Colors.SECONDARY,
                "container": ft.Colors.SECONDARY_CONTAINER,
                "on_container": ft.Colors.ON_SECONDARY_CONTAINER
            },
            "surface": {
                "main": ft.Colors.ON_SURFACE_VARIANT,
                "container": ft.Colors.GREY_100,
                "on_container": ft.Colors.ON_SURFACE
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_standard_icon_button(self, colors: dict) -> ft.IconButton:
        """Construye botón de icono estándar."""
        return ft.IconButton(
            icon=self.icon,
            tooltip=self.tooltip,
            on_click=self.on_click,
            disabled=self.disabled,
            icon_size=self.size,
            style=ft.ButtonStyle(
                icon_color={
                    ft.ControlState.DEFAULT: colors["main"],
                    ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
                },
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.08, colors["main"]),
                    ft.ControlState.PRESSED: ft.Colors.with_opacity(0.12, colors["main"])
                },
                shape=ft.CircleBorder(),
                padding=8
            )
        )
    
    def _build_filled_icon_button(self, colors: dict) -> ft.Container:
        """Construye botón de icono con fondo."""
        return ft.Container(
            content=ft.IconButton(
                icon=self.icon,
                tooltip=self.tooltip,
                on_click=self.on_click,
                disabled=self.disabled,
                icon_size=self.size,
                style=ft.ButtonStyle(
                    icon_color={
                        ft.ControlState.DEFAULT: colors["on_container"],
                        ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
                    },
                    shape=ft.CircleBorder(),
                    padding=8
                )
            ),
            bgcolor=colors["container"],
            border_radius=20,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=2,
                color=ft.Colors.with_opacity(0.15, colors["main"]),
                offset=ft.Offset(0, 1)
            )
        )
    
    def _build_outlined_icon_button(self, colors: dict) -> ft.Container:
        """Construye botón de icono con borde."""
        return ft.Container(
            content=ft.IconButton(
                icon=self.icon,
                tooltip=self.tooltip,
                on_click=self.on_click,
                disabled=self.disabled,
                icon_size=self.size,
                style=ft.ButtonStyle(
                    icon_color={
                        ft.ControlState.DEFAULT: colors["main"],
                        ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
                    },
                    bgcolor={
                        ft.ControlState.HOVERED: ft.Colors.with_opacity(0.08, colors["main"]),
                        ft.ControlState.PRESSED: ft.Colors.with_opacity(0.12, colors["main"])
                    },
                    shape=ft.CircleBorder(),
                    padding=8
                )
            ),
            border=ft.border.all(1, colors["main"]),
            border_radius=20
        ) 