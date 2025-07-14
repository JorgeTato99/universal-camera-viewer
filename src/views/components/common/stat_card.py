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
from ...design_system import (
    MaterialColors as MD3,
    MaterialElevation,
    create_semantic_color_scheme,
    create_text,
    BorderRadius,
    Spacing,
    Elevation
)


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
        self.padding = ft.padding.all(Spacing.EXTRA_LARGE)
        self.bgcolor = MD3.SURFACE
        self.border_radius = BorderRadius.LARGE
        self.border = ft.border.all(1, MD3.OUTLINE_VARIANT)
        
        # Sombra Material 3
        self.shadow = MaterialElevation.create_shadow(Elevation.LEVEL_1)
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema especificado."""
        return create_semantic_color_scheme(self.color_scheme)
    
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
                border_radius=BorderRadius.MEDIUM,
                padding=ft.padding.all(Spacing.MEDIUM),
                shadow=MaterialElevation.create_shadow(Elevation.LEVEL_1)
            ),
            ft.Container(expand=True)  # Spacer para alinear icono a la izquierda
        ])
        
        # Valor principal - prominente
        value_text = create_text(
            self.value,
            "display_small",
            MD3.ON_SURFACE
        )
        
        # Título de la estadística
        title_text = create_text(
            self.title,
            "title_medium",
            MD3.ON_SURFACE_VARIANT
        )
        
        # Descripción opcional
        content_items = [
            header,
            ft.Container(height=Spacing.LARGE),  # Spacing
            value_text,
            ft.Container(height=Spacing.EXTRA_SMALL),   # Spacing menor
            title_text
        ]
        
        if self.description:
            description_text = create_text(
                self.description,
                "body_small",
                MD3.ON_SURFACE_VARIANT
            )
            content_items.extend([
                ft.Container(height=Spacing.SMALL),  # Spacing
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
        self.padding = ft.padding.all(Spacing.MEDIUM)
        self.bgcolor = MD3.SURFACE
        self.border_radius = BorderRadius.MEDIUM
        self.border = ft.border.all(1, MD3.OUTLINE_VARIANT)
        
        # Sombra más sutil
        self.shadow = MaterialElevation.create_shadow(Elevation.LEVEL_1)
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema especificado."""
        return create_semantic_color_scheme(self.color_scheme)
    
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
        value_text = create_text(
            self.value,
            "title_large",
            MD3.ON_SURFACE
        )
        
        # Título más pequeño
        title_text = create_text(
            self.title,
            "body_small",
            MD3.ON_SURFACE_VARIANT
        )
        
        return ft.Column([
            header,
            ft.Container(height=Spacing.SMALL),
            value_text,
            ft.Container(height=Spacing.EXTRA_SMALL),
            title_text
        ],
        spacing=0,
        tight=True
        ) 