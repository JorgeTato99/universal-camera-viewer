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
from ...design_system import (
    MaterialColors as MD3,
    MaterialElevation,
    create_semantic_color_scheme,
    BorderRadius,
    Spacing,
    Elevation
)


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
        return create_semantic_color_scheme(self.color_scheme)
    
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
                shape=ft.RoundedRectangleBorder(radius=BorderRadius.MEDIUM),
                padding=ft.padding.symmetric(horizontal=Spacing.XXL, vertical=Spacing.MEDIUM)
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
                shape=ft.RoundedRectangleBorder(radius=BorderRadius.MEDIUM),
                padding=ft.padding.symmetric(horizontal=Spacing.XXL, vertical=Spacing.MEDIUM)
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
                shape=ft.RoundedRectangleBorder(radius=BorderRadius.MEDIUM),
                padding=ft.padding.symmetric(horizontal=Spacing.LARGE, vertical=Spacing.SMALL)
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
        return create_semantic_color_scheme(self.color_scheme)
    
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
            border_radius=BorderRadius.EXTRA_LARGE,
            shadow=MaterialElevation.create_shadow(Elevation.LEVEL_1)
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
            border_radius=BorderRadius.EXTRA_LARGE
        ) 