#!/usr/bin/env python3
"""
ModernNavigationBar - Barra de navegación horizontal moderna
===========================================================

Implementación de navegación superior horizontal con Material Design 3:
- Tabs/pestañas para módulos principales
- Estados activos/inactivos con animaciones
- Iconos y textos opcionales
- Colores semánticos y sombras
- Responsive y accesible
"""

import flet as ft
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass

# Importaciones para el theme toggle
try:
    from ...services.theme_service import theme_service
except ImportError:
    # Si no está disponible, theme_service será None
    theme_service = None

# Importar design system
try:
    from ..design_system import Spacing, BorderRadius, MaterialElevation
except ImportError:
    # Fallback si no está disponible
    Spacing = None
    BorderRadius = None
    MaterialElevation = None


@dataclass
class NavItem:
    """Representa un elemento de navegación."""
    key: str
    label: str
    icon: str
    tooltip: Optional[str] = None


class ModernNavigationBar(ft.Container):
    """
    Barra de navegación horizontal moderna con Material Design 3.
    
    Perfecta para aplicaciones de escritorio con múltiples módulos
    donde se necesita navegación rápida y visible.
    """
    
    def __init__(
        self,
        nav_items: List[NavItem],
        selected_key: str,
        on_change: Optional[Callable[[str], None]] = None,
        show_labels: bool = True,
        height: int = 72,
        page: Optional[ft.Page] = None,
        show_theme_toggle: bool = True,
        **kwargs
    ):
        """
        Inicializa la barra de navegación.
        
        Args:
            nav_items: Lista de elementos de navegación
            selected_key: Clave del elemento seleccionado
            on_change: Callback cuando se selecciona un elemento
            show_labels: Mostrar etiquetas de texto
            height: Altura de la barra
        """
        super().__init__(**kwargs)
        
        self.nav_items = nav_items
        self.selected_key = selected_key
        self.on_change = on_change
        self.show_labels = show_labels
        self.page = page
        self.show_theme_toggle = show_theme_toggle
        
        # Configurar contenido
        self.content = self._build_navigation_content()
        
        # Configurar propiedades del container
        self.height = height
        self.bgcolor = ft.Colors.SURFACE
        # Usar spacing del design system o fallback
        horizontal_padding = Spacing.EXTRA_LARGE if Spacing else 20
        vertical_padding = Spacing.MEDIUM if Spacing else 12
        self.padding = ft.padding.symmetric(horizontal=horizontal_padding, vertical=vertical_padding)
        
        # Sombra inferior Material 3
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ft.Colors.with_opacity(0.12, ft.Colors.SHADOW),
            offset=ft.Offset(0, 2)
        )
        
        # Borde inferior sutil
        self.border = ft.border.only(
            bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
        )
    
    def _build_navigation_content(self) -> ft.Row:
        """Construye el contenido de la barra de navegación."""
        
        # Controles de navegación principales
        nav_controls = []
        
        for item in self.nav_items:
            nav_tab = self._create_nav_tab(item)
            nav_controls.append(nav_tab)
        
        # Crear Row principal con navegación
        main_nav = ft.Row(
            nav_controls,
            alignment=ft.MainAxisAlignment.START,
            spacing=8
        )
        
        # Controles adicionales (theme toggle, etc.)
        additional_controls = []
        
        if self.show_theme_toggle and self.page and theme_service:
            theme_button = self._create_theme_button()
            additional_controls.append(theme_button)
        
        # Row completo con navegación y controles adicionales
        return ft.Row([
            main_nav,
            ft.Row(additional_controls, spacing=8) if additional_controls else ft.Container()
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    
    def _create_nav_tab(self, item: NavItem) -> ft.Container:
        """Crea un tab individual de navegación."""
        
        is_selected = item.key == self.selected_key
        
        # Colores según estado
        if is_selected:
            text_color = ft.Colors.PRIMARY
            icon_color = ft.Colors.PRIMARY
            bg_color = ft.Colors.PRIMARY_CONTAINER
            border_color = ft.Colors.PRIMARY
        else:
            text_color = ft.Colors.ON_SURFACE_VARIANT
            icon_color = ft.Colors.ON_SURFACE_VARIANT
            bg_color = ft.Colors.TRANSPARENT
            border_color = ft.Colors.TRANSPARENT
        
        # Contenido del tab
        tab_content = []
        
        # Icono
        icon_widget = ft.Icon(
            item.icon,
            color=icon_color,
            size=24
        )
        
        if self.show_labels:
            # Layout vertical: icono arriba, texto abajo
            text_widget = ft.Text(
                item.label,
                size=12,
                weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
                color=text_color,
                text_align=ft.TextAlign.CENTER
            )
            
            # Usar spacing del design system o fallback
            icon_text_spacing = Spacing.SMALL if Spacing else 6
            
            tab_content = ft.Column([
                icon_widget,
                ft.Container(height=icon_text_spacing),
                text_widget
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True
            )
        else:
            # Solo icono
            tab_content = icon_widget
        
        # Container del tab con estados interactivos
        # Usar spacing del design system o fallback
        tab_h_padding = Spacing.EXTRA_LARGE if Spacing else 20
        tab_v_padding = Spacing.MEDIUM if Spacing else 12
        tab_radius = BorderRadius.MEDIUM if BorderRadius else 12
        
        return ft.Container(
            content=tab_content,
            padding=ft.padding.symmetric(horizontal=tab_h_padding, vertical=tab_v_padding),
            border_radius=tab_radius,
            bgcolor=bg_color,
            border=ft.border.all(2, border_color) if is_selected else None,
            tooltip=item.tooltip or item.label,
            ink=True,
            on_click=lambda e, key=item.key: self._handle_tab_click(key)
        )
    
    def _handle_tab_click(self, key: str):
        """Maneja el click en un tab."""
        if key != self.selected_key and self.on_change:
            self.selected_key = key
            # Reconstruir contenido para reflejar nueva selección
            self.content = self._build_navigation_content()
            # Notificar cambio
            self.on_change(key)
    
    def _create_theme_button(self) -> ft.Container:
        """Crea el botón para cambiar el tema."""
        if not self.page or not theme_service:
            return ft.Container()
        
        # Determinar icono según tema actual
        is_dark = theme_service.is_dark_theme()
        icon = ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE
        tooltip = "Cambiar a tema claro" if is_dark else "Cambiar a tema oscuro"
        
        return ft.Container(
            content=ft.IconButton(
                icon=icon,
                icon_size=20,
                tooltip=tooltip,
                on_click=self._handle_theme_toggle
            ),
            padding=ft.padding.all(4)
        )
    
    def _handle_theme_toggle(self, e):
        """Maneja el cambio de tema."""
        if self.page and theme_service:
            theme_service.toggle_theme(self.page)
            # Forzar recarga para asegurar que todos los componentes se actualicen
            theme_service.force_theme_reload(self.page)
            # Actualizar el botón
            self.content = self._build_navigation_content()
            self.update()
    
    def select_item(self, key: str):
        """Selecciona un elemento programáticamente."""
        if key in [item.key for item in self.nav_items]:
            self.selected_key = key
            self.content = self._build_navigation_content()
    
    def update_badge(self, key: str, badge_text: Optional[str] = None):
        """Actualiza el badge de un elemento (futuro)."""
        # Implementación futura para badges/notificaciones
        pass


class ModernNavigationBarCompact(ft.Container):
    """
    Versión compacta de la barra de navegación para espacios reducidos.
    """
    
    def __init__(
        self,
        nav_items: List[NavItem],
        selected_key: str,
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.nav_items = nav_items
        self.selected_key = selected_key
        self.on_change = on_change
        
        # Configurar contenido
        self.content = self._build_compact_content()
        
        # Configurar propiedades
        self.height = 48
        self.bgcolor = ft.Colors.SURFACE
        self.padding = ft.padding.symmetric(horizontal=8, vertical=4)
        
        # Borde inferior
        self.border = ft.border.only(
            bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
        )
    
    def _build_compact_content(self) -> ft.Row:
        """Construye contenido compacto."""
        
        # Crear chips para cada item
        chips = []
        
        for item in self.nav_items:
            is_selected = item.key == self.selected_key
            
            chip = ft.Container(
                content=ft.Row([
                    ft.Icon(item.icon, size=16),
                    ft.Container(width=8),
                    ft.Text(
                        item.label,
                        size=14,
                        weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400
                    )
                ], tight=True),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=16,
                bgcolor=ft.Colors.PRIMARY_CONTAINER if is_selected else ft.Colors.TRANSPARENT,
                border=ft.border.all(1, ft.Colors.PRIMARY if is_selected else ft.Colors.OUTLINE),
                ink=True,
                on_click=lambda e, key=item.key: self._handle_chip_click(key)
            )
            
            chips.append(chip)
        
        return ft.Row(chips, spacing=8)
    
    def _handle_chip_click(self, key: str):
        """Maneja click en chip."""
        if key != self.selected_key and self.on_change:
            self.selected_key = key
            self.content = self._build_compact_content()
            self.on_change(key)


class NavigationConstants:
    """Constantes para la navegación de la aplicación."""
    
    # Definición de módulos principales
    CAMERAS = "cameras"
    SCAN = "scan"  
    ANALYTICS = "analytics"
    SETTINGS = "settings"
    
    # Items de navegación predefinidos para Universal Camera Viewer
    DEFAULT_ITEMS = [
        NavItem(
            key=CAMERAS,
            label="Cámaras",
            icon=ft.Icons.VIDEOCAM,
            tooltip="Ver y gestionar cámaras conectadas"
        ),
        NavItem(
            key=SCAN,
            label="Escaneo",
            icon=ft.Icons.NETWORK_CHECK,
            tooltip="Escanear red en busca de cámaras"
        ),
        NavItem(
            key=ANALYTICS,
            label="Análisis",
            icon=ft.Icons.ANALYTICS,
            tooltip="Estadísticas y análisis de conexiones"
        ),
        NavItem(
            key=SETTINGS,
            label="Configuración",
            icon=ft.Icons.SETTINGS,
            tooltip="Configuración de la aplicación"
        )
    ]


def create_main_navigation(
    selected_key: str = NavigationConstants.CAMERAS,
    on_change: Optional[Callable[[str], None]] = None,
    page: Optional[ft.Page] = None
) -> ModernNavigationBar:
    """
    Función helper para crear la navegación principal.
    
    Args:
        selected_key: Módulo seleccionado inicialmente
        on_change: Callback de cambio de navegación
        
    Returns:
        Instancia configurada de ModernNavigationBar
    """
    return ModernNavigationBar(
        nav_items=NavigationConstants.DEFAULT_ITEMS,
        selected_key=selected_key,
        on_change=on_change,
        show_labels=True,
        page=page
    )


def create_compact_navigation(
    selected_key: str = NavigationConstants.CAMERAS,
    on_change: Optional[Callable[[str], None]] = None
) -> ModernNavigationBarCompact:
    """
    Función helper para crear la navegación compacta.
    """
    return ModernNavigationBarCompact(
        nav_items=NavigationConstants.DEFAULT_ITEMS,
        selected_key=selected_key,
        on_change=on_change
    ) 