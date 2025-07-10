#!/usr/bin/env python3
"""
StatCard - Card de estadísticas con Material Design 3
====================================================

Componente para mostrar métricas y estadísticas de forma visual:
- Icono representativo
- Título y valor numérico
- Texto de descripción opcional
- Estados de color semánticos
- Elevación y sombras Material 3
"""

import flet as ft
from typing import Optional, Union


class StatCard(ft.Container):
    """
    Card de estadística moderna con Material Design 3.
    
    Perfecto para mostrar métricas, contadores y valores importantes
    con una presentación visual atractiva y consistente.
    """
    
    def __init__(
        self,
        title: str,
        value: Union[str, int, float],
        icon: str,
        description: Optional[str] = None,
        color_scheme: str = "primary",  # primary, secondary, tertiary, success, warning, error
        width: Optional[int] = None,
        **kwargs
    ):
        """
        Inicializa la StatCard.
        
        Args:
            title: Título de la estadística
            value: Valor numérico o texto principal
            icon: Icono que representa la estadística
            description: Descripción opcional adicional
            color_scheme: Esquema de color para el card
            width: Ancho específico del card
        """
        super().__init__(**kwargs)
        
        self.title = title
        self.value = str(value)
        self.icon = icon
        self.description = description
        self.color_scheme = color_scheme
        
        # Configurar el contenido del card
        colors = self._get_color_scheme()
        self.content = self._build_card_content(colors)
        
        # Configurar propiedades del container
        self.width = width or 280
        self.padding = ft.padding.all(20)
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = 16
        self.border = ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        
        # Sombra Material 3
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=6,
            color=ft.Colors.with_opacity(0.10, ft.Colors.SHADOW),
            offset=ft.Offset(0, 2)
        )
    
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
            "tertiary": {
                "main": ft.Colors.TERTIARY,
                "container": ft.Colors.TERTIARY_CONTAINER,
                "on_container": ft.Colors.ON_TERTIARY_CONTAINER
            },
            "success": {
                "main": ft.Colors.GREEN_600,
                "container": ft.Colors.GREEN_100,
                "on_container": ft.Colors.GREEN_800
            },
            "warning": {
                "main": ft.Colors.ORANGE_600,
                "container": ft.Colors.ORANGE_100,
                "on_container": ft.Colors.ORANGE_800
            },
            "error": {
                "main": ft.Colors.RED_600,
                "container": ft.Colors.RED_100,
                "on_container": ft.Colors.RED_800
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_card_content(self, colors: dict) -> ft.Column:
        """Construye el contenido interno del card."""
        
        # Header con icono
        header = ft.Row([
            ft.Container(
                content=ft.Icon(
                    self.icon,
                    color=colors["on_container"],
                    size=24
                ),
                bgcolor=colors["container"],
                border_radius=12,
                padding=ft.padding.all(12),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=2,
                    color=ft.Colors.with_opacity(0.15, colors["main"]),
                    offset=ft.Offset(0, 1)
                )
            ),
            ft.Container(expand=True)  # Spacer para alinear icono a la izquierda
        ])
        
        # Valor principal - prominente
        value_text = ft.Text(
            self.value,
            size=32,
            weight=ft.FontWeight.W_700,
            color=ft.Colors.ON_SURFACE
        )
        
        # Título de la estadística
        title_text = ft.Text(
            self.title,
            size=16,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.ON_SURFACE_VARIANT
        )
        
        # Descripción opcional
        content_items = [
            header,
            ft.Container(height=16),  # Spacing
            value_text,
            ft.Container(height=4),   # Spacing menor
            title_text
        ]
        
        if self.description:
            description_text = ft.Text(
                self.description,
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
            content_items.extend([
                ft.Container(height=8),  # Spacing
                description_text
            ])
        
        return ft.Column(
            content_items,
            spacing=0,
            tight=True
        )
    
    def update_value(self, new_value: Union[str, int, float]):
        """Actualiza el valor mostrado en el card."""
        self.value = str(new_value)
        # Reconstruir contenido con nuevo valor
        colors = self._get_color_scheme()
        self.content = self._build_card_content(colors)
    
    def update_description(self, new_description: str):
        """Actualiza la descripción del card."""
        self.description = new_description
        # Reconstruir contenido si es necesario
        colors = self._get_color_scheme()
        self.content = self._build_card_content(colors)


class StatCardMini(ft.Container):
    """
    Versión compacta de StatCard para espacios reducidos.
    """
    
    def __init__(
        self,
        title: str,
        value: Union[str, int, float],
        icon: str,
        color_scheme: str = "primary",
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.title = title
        self.value = str(value)
        self.icon = icon
        self.color_scheme = color_scheme
        
        # Configurar contenido
        colors = self._get_color_scheme()
        self.content = self._build_mini_content(colors)
        
        # Configurar propiedades del container
        self.width = 140
        self.padding = ft.padding.all(12)
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = 12
        self.border = ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        
        # Sombra más sutil
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=3,
            color=ft.Colors.with_opacity(0.08, ft.Colors.SHADOW),
            offset=ft.Offset(0, 1)
        )
    
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
            "success": {
                "main": ft.Colors.GREEN_600,
                "container": ft.Colors.GREEN_100,
                "on_container": ft.Colors.GREEN_800
            },
            "error": {
                "main": ft.Colors.RED_600,
                "container": ft.Colors.RED_100,
                "on_container": ft.Colors.RED_800
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_mini_content(self, colors: dict) -> ft.Column:
        """Construye contenido compacto del card."""
        
        # Header con icono más pequeño
        header = ft.Row([
            ft.Icon(
                self.icon,
                color=colors["main"],
                size=16
            ),
            ft.Container(expand=True)
        ])
        
        # Valor con menor prominencia
        value_text = ft.Text(
            self.value,
            size=20,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_SURFACE
        )
        
        # Título más pequeño
        title_text = ft.Text(
            self.title,
            size=12,
            weight=ft.FontWeight.W_400,
            color=ft.Colors.ON_SURFACE_VARIANT
        )
        
        return ft.Column([
            header,
            ft.Container(height=8),
            value_text,
            ft.Container(height=2),
            title_text
        ],
        spacing=0,
        tight=True
        ) 