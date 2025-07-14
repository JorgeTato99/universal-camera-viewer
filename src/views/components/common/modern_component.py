#!/usr/bin/env python3
"""
ModernComponent - Componente base con Material Design 3
=======================================================

Componente base que implementa los principios de Material Design 3:
- Sistema de colores semántico
- Elevación consistente
- Tipografía estandarizada
- Responsive design
- Accesibilidad integrada

Basado en la guía de desarrollo UI/UX moderna.
"""

import flet as ft
from typing import Optional, Union, Dict, Any
from dataclasses import dataclass
from ...design_system import (
    MaterialColors as MD3,
    MaterialElevation,
    BorderRadius,
    Spacing,
    create_semantic_color_scheme,
    create_text
)


@dataclass
class ModernComponentConfig:
    """Configuración para componentes modernos."""
    color_scheme: str = "surface"
    elevation: int = 0
    border_radius: int = BorderRadius.MEDIUM
    padding: int = Spacing.MEDIUM
    responsive: bool = True
    tooltip: Optional[str] = None


class ModernComponent(ft.Container):
    """
    Componente base con Material Design 3.
    
    Proporciona configuración consistente para:
    - Colores semánticos
    - Elevación y sombras
    - Bordes redondeados
    - Espaciado
    - Responsive design
    """
    
    def __init__(
        self,
        content: ft.Control,
        config: Optional[ModernComponentConfig] = None,
        **kwargs
    ):
        """
        Inicializa el componente moderno.
        
        Args:
            content: Contenido del componente
            config: Configuración del componente
            **kwargs: Argumentos adicionales para ft.Container
        """
        self.config = config or ModernComponentConfig()
        
        # Aplicar configuración del sistema de diseño
        self._apply_design_system(kwargs)
        
        # Configurar contenido
        kwargs['content'] = content
        
        super().__init__(**kwargs)
    
    def _apply_design_system(self, kwargs: Dict[str, Any]):
        """Aplica el sistema de diseño al componente."""
        
        # Colores semánticos
        colors = create_semantic_color_scheme(self.config.color_scheme)
        if 'bgcolor' not in kwargs:
            kwargs['bgcolor'] = colors['container']
        
        # Elevación y sombra
        if self.config.elevation > 0:
            shadow = MaterialElevation.create_shadow(self.config.elevation)
            if shadow and 'shadow' not in kwargs:
                kwargs['shadow'] = shadow
        
        # Bordes redondeados
        if 'border_radius' not in kwargs:
            kwargs['border_radius'] = self.config.border_radius
        
        # Padding
        if 'padding' not in kwargs:
            kwargs['padding'] = ft.padding.all(self.config.padding)
        
        # Borde sutil
        if 'border' not in kwargs and self.config.elevation == 0:
            kwargs['border'] = ft.border.all(1, MD3.OUTLINE_VARIANT)
        
        # Tooltip
        if self.config.tooltip and 'tooltip' not in kwargs:
            kwargs['tooltip'] = self.config.tooltip


class ModernCard(ModernComponent):
    """Card moderna con Material Design 3."""
    
    def __init__(
        self,
        content: ft.Control,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        actions: Optional[list[ft.Control]] = None,
        **kwargs
    ):
        """
        Inicializa la card moderna.
        
        Args:
            content: Contenido principal
            title: Título opcional
            subtitle: Subtítulo opcional
            actions: Lista de acciones (botones)
            **kwargs: Argumentos adicionales
        """
        
        # Configuración por defecto para cards
        config = ModernComponentConfig(
            color_scheme="surface",
            elevation=1,
            border_radius=BorderRadius.LARGE,
            padding=Spacing.EXTRA_LARGE
        )
        
        # Construir contenido de la card
        card_content = self._build_card_content(content, title, subtitle, actions)
        
        super().__init__(card_content, config, **kwargs)
    
    def _build_card_content(
        self,
        content: ft.Control,
        title: Optional[str],
        subtitle: Optional[str],
        actions: Optional[list[ft.Control]]
    ) -> ft.Column:
        """Construye el contenido de la card."""
        
        card_elements = []
        
        # Header con título y subtítulo
        if title or subtitle:
            header_elements = []
            
            if title:
                header_elements.append(
                    create_text(title, "title_large", MD3.ON_SURFACE)
                )
            
            if subtitle:
                header_elements.append(
                    ft.Container(height=Spacing.SMALL)
                )
                header_elements.append(
                    create_text(subtitle, "body_medium", MD3.ON_SURFACE_VARIANT)
                )
            
            header = ft.Column(header_elements, spacing=0, tight=True)
            card_elements.extend([
                header,
                ft.Container(height=Spacing.LARGE)
            ])
        
        # Contenido principal
        card_elements.append(content)
        
        # Acciones
        if actions:
            card_elements.extend([
                ft.Container(height=Spacing.LARGE),
                ft.Row(actions, alignment=ft.MainAxisAlignment.END)
            ])
        
        return ft.Column(card_elements, spacing=0, tight=True)


class ModernSurface(ModernComponent):
    """Superficie moderna para agrupación de contenido."""
    
    def __init__(
        self,
        content: ft.Control,
        variant: str = "primary",  # primary, secondary, tertiary
        **kwargs
    ):
        """
        Inicializa la superficie moderna.
        
        Args:
            content: Contenido de la superficie
            variant: Variante de color
            **kwargs: Argumentos adicionales
        """
        
        config = ModernComponentConfig(
            color_scheme=variant,
            elevation=0,
            border_radius=BorderRadius.MEDIUM,
            padding=Spacing.LARGE
        )
        
        super().__init__(content, config, **kwargs)


class ModernPanel(ModernComponent):
    """Panel moderno con header y contenido."""
    
    def __init__(
        self,
        content: ft.Control,
        title: str,
        icon: Optional[str] = None,
        header_actions: Optional[list[ft.Control]] = None,
        collapsible: bool = False,
        **kwargs
    ):
        """
        Inicializa el panel moderno.
        
        Args:
            content: Contenido del panel
            title: Título del panel
            icon: Icono opcional
            header_actions: Acciones del header
            collapsible: Si el panel es colapsable
            **kwargs: Argumentos adicionales
        """
        
        self.is_collapsed = False
        self.collapsible = collapsible
        
        # Configuración del panel
        config = ModernComponentConfig(
            color_scheme="surface",
            elevation=1,
            border_radius=BorderRadius.LARGE,
            padding=0  # El padding se maneja internamente
        )
        
        # Construir contenido del panel
        panel_content = self._build_panel_content(
            content, title, icon, header_actions
        )
        
        super().__init__(panel_content, config, **kwargs)
    
    def _build_panel_content(
        self,
        content: ft.Control,
        title: str,
        icon: Optional[str],
        header_actions: Optional[list[ft.Control]]
    ) -> ft.Column:
        """Construye el contenido del panel."""
        
        # Header del panel
        header = self._build_panel_header(title, icon, header_actions)
        
        # Contenido con padding
        content_container = ft.Container(
            content=content,
            padding=ft.padding.all(Spacing.EXTRA_LARGE)
        )
        
        return ft.Column([
            header,
            ft.Divider(height=1, color=MD3.OUTLINE_VARIANT),
            content_container
        ], spacing=0)
    
    def _build_panel_header(
        self,
        title: str,
        icon: Optional[str],
        header_actions: Optional[list[ft.Control]]
    ) -> ft.Container:
        """Construye el header del panel."""
        
        header_elements = []
        
        # Icono y título
        title_row = []
        
        if icon:
            title_row.append(
                ft.Icon(icon, size=20, color=MD3.PRIMARY)
            )
            title_row.append(ft.Container(width=Spacing.SMALL))
        
        title_row.append(
            create_text(title, "title_medium", MD3.ON_SURFACE)
        )
        
        header_elements.append(
            ft.Row(title_row, tight=True)
        )
        
        # Acciones del header
        if header_actions:
            header_elements.append(
                ft.Row(header_actions, tight=True)
            )
        
        # Botón de colapsar si es necesario
        if self.collapsible:
            collapse_button = ft.IconButton(
                icon=ft.Icons.EXPAND_LESS if not self.is_collapsed else ft.Icons.EXPAND_MORE,
                icon_size=16,
                on_click=self._toggle_collapse,
                tooltip="Expandir/Contraer"
            )
            if len(header_elements) == 1:
                header_elements.append(collapse_button)
            else:
                header_elements[-1].controls.append(collapse_button)
        
        return ft.Container(
            content=ft.Row(
                header_elements,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.all(Spacing.EXTRA_LARGE),
            bgcolor=MD3.SURFACE
        )
    
    def _toggle_collapse(self, e):
        """Alterna el estado de colapso del panel."""
        self.is_collapsed = not self.is_collapsed
        # TODO: Implementar lógica de colapso
        # Esto requeriría reconstruir el contenido


# Funciones helper para crear componentes comunes

def create_modern_card(
    content: ft.Control,
    title: Optional[str] = None,
    **kwargs
) -> ModernCard:
    """Crea una card moderna con configuración estándar."""
    return ModernCard(content=content, title=title, **kwargs)


def create_info_card(
    title: str,
    description: str,
    icon: str,
    actions: Optional[list[ft.Control]] = None
) -> ModernCard:
    """Crea una card informativa estándar."""
    
    content = ft.Column([
        ft.Row([
            ft.Icon(icon, size=24, color=MD3.PRIMARY),
            ft.Container(width=Spacing.MEDIUM),
            ft.Column([
                create_text(title, "title_medium", MD3.ON_SURFACE),
                ft.Container(height=Spacing.SMALL),
                create_text(description, "body_medium", MD3.ON_SURFACE_VARIANT)
            ], spacing=0, tight=True)
        ], tight=True)
    ], tight=True)
    
    return ModernCard(content=content, actions=actions)


def create_status_surface(
    content: ft.Control,
    status: str = "info"  # success, warning, error, info
) -> ModernSurface:
    """Crea una superficie con color de estado."""
    
    status_schemes = {
        "success": "success",
        "warning": "warning", 
        "error": "error",
        "info": "info"
    }
    
    scheme = status_schemes.get(status, "info")
    return ModernSurface(content=content, variant=scheme) 