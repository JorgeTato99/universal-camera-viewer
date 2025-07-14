#!/usr/bin/env python3
"""
Side Panel Component - Panel lateral moderno con Material Design 3
=================================================================

Componente para crear paneles laterales flexibles y modernos:
- SidePanel: Panel lateral principal con navegación
- CollapsibleSidePanel: Panel que se puede contraer/expandir
- Soporte para secciones, iconos, y contenido adaptativo
"""

import flet as ft
from typing import List, Optional, Callable, Union, Dict
from .common.modern_button import ModernButton, ModernIconButton
from .common.stat_card import StatCard


class SidePanelItem:
    """Representa un elemento del panel lateral."""
    
    def __init__(
        self,
        title: str,
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        badge: Optional[str] = None,
        is_selected: bool = False,
        is_divider: bool = False,
        children: Optional[List['SidePanelItem']] = None
    ):
        self.title = title
        self.icon = icon
        self.on_click = on_click
        self.badge = badge
        self.is_selected = is_selected
        self.is_divider = is_divider
        self.children = children or []
        self.is_expanded = False


class SidePanel(ft.Container):
    """
    Panel lateral moderno con Material Design 3.
    
    Soporta navegación, información y contenido flexible.
    """
    
    def __init__(
        self,
        title: str = "Panel",
        items: Optional[List[SidePanelItem]] = None,
        width: int = 280,
        show_header: bool = True,
        header_actions: Optional[List[ft.Control]] = None,
        footer_content: Optional[ft.Control] = None,
        **kwargs
    ):
        """
        Inicializa el panel lateral moderno.
        
        Args:
            title: Título del panel
            items: Lista de elementos de navegación
            width: Ancho del panel
            show_header: Mostrar header del panel
            header_actions: Acciones adicionales en el header
            footer_content: Contenido del footer
        """
        super().__init__(**kwargs)
        
        self.title = title
        self.items = items or []
        self.panel_width = width
        self.show_header = show_header
        self.header_actions = header_actions or []
        self.footer_content = footer_content
        
        # Configurar estilo del contenedor
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = ft.border_radius.only(
            top_right=12,
            bottom_right=12
        )
        self.border = ft.border.only(
            right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
        )
        self.width = width
        self.padding = ft.padding.all(16)
        self.expand = True  # Hacer que el panel se expanda verticalmente
        
        # Construir contenido
        self.content = self._build_panel_content()
    
    def _build_panel_content(self) -> ft.Column:
        """Construye el contenido del panel lateral."""
        
        panel_elements: List[ft.Control] = []
        
        # Header (si está habilitado)
        if self.show_header:
            header = self._build_header()
            panel_elements.append(header)
            panel_elements.append(ft.Container(height=16))
        
        # Elementos de navegación
        navigation_section = self._build_navigation_section()
        panel_elements.append(navigation_section)
        
        # Spacer para empujar footer al final
        panel_elements.append(ft.Container(expand=True))
        
        # Footer (si existe)
        if self.footer_content:
            panel_elements.append(ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT))
            panel_elements.append(ft.Container(height=16))
            panel_elements.append(self.footer_content)
        
        return ft.Column(
            panel_elements,
            spacing=0,
            expand=True
        )
    
    def _build_header(self) -> ft.Row:
        """Construye el header del panel."""
        
        # Título
        title_text = ft.Text(
            self.title,
            size=18,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_SURFACE
        )
        
        # Elementos del header
        header_elements: List[ft.Control] = [title_text]
        
        # Spacer si hay acciones
        if self.header_actions:
            header_elements.append(ft.Container(expand=True))
            header_elements.extend(self.header_actions)
        
        return ft.Row(
            header_elements,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _build_navigation_section(self) -> ft.Column:
        """Construye la sección de navegación."""
        
        if not self.items:
            return ft.Column([])
        
        nav_elements = []
        
        for item in self.items:
            if item.is_divider:
                # Divider
                divider = ft.Divider(
                    height=1,
                    color=ft.Colors.OUTLINE_VARIANT
                )
                nav_elements.extend([
                    ft.Container(height=8),
                    divider,
                    ft.Container(height=8)
                ])
            else:
                # Elemento de navegación
                nav_item = self._build_nav_item(item)
                nav_elements.append(nav_item)
        
        return ft.Column(nav_elements, spacing=2)
    
    def _build_nav_item(self, item: SidePanelItem) -> ft.Container:
        """Construye un elemento de navegación."""
        
        # Contenido del elemento
        item_content = []
        
        # Icono
        if item.icon:
            icon_widget = ft.Icon(
                item.icon,
                size=20,
                color=ft.Colors.PRIMARY if item.is_selected else ft.Colors.ON_SURFACE_VARIANT
            )
            item_content.append(icon_widget)
        
        # Título
        title_text = ft.Text(
            item.title,
            size=14,
            weight=ft.FontWeight.W_500 if item.is_selected else ft.FontWeight.W_400,
            color=ft.Colors.ON_SURFACE if item.is_selected else ft.Colors.ON_SURFACE_VARIANT
        )
        item_content.append(title_text)
        
        # Spacer
        item_content.append(ft.Container(expand=True))
        
        # Badge (si existe)
        if item.badge:
            badge_widget = ft.Container(
                content=ft.Text(
                    item.badge,
                    size=12,
                    color=ft.Colors.ON_PRIMARY,
                    weight=ft.FontWeight.W_600
                ),
                bgcolor=ft.Colors.PRIMARY,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=8, vertical=4)
            )
            item_content.append(badge_widget)
        
        # Crear row del elemento
        item_row = ft.Row(
            item_content,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12
        )
        
        # Container clickeable
        return ft.Container(
            content=item_row,
            bgcolor=ft.Colors.PRIMARY_CONTAINER if item.is_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=item.on_click
        )
    
    def add_item(self, item: SidePanelItem):
        """Agrega un elemento al panel."""
        self.items.append(item)
        self.content = self._build_panel_content()
    
    def remove_item(self, item_title: str):
        """Remueve un elemento por título."""
        self.items = [item for item in self.items if item.title != item_title]
        self.content = self._build_panel_content()
    
    def select_item(self, item_title: str):
        """Selecciona un elemento por título."""
        for item in self.items:
            item.is_selected = (item.title == item_title)
        self.content = self._build_panel_content()
    
    def update_badge(self, item_title: str, badge_text: Optional[str]):
        """Actualiza el badge de un elemento."""
        for item in self.items:
            if item.title == item_title:
                item.badge = badge_text
                break
        self.content = self._build_panel_content()


class CollapsibleSidePanel(ft.Container):
    """
    Panel lateral que se puede contraer/expandir.
    """
    
    def __init__(
        self,
        title: str = "Panel",
        items: Optional[List[SidePanelItem]] = None,
        expanded_width: int = 280,
        collapsed_width: int = 60,
        is_expanded: bool = True,
        **kwargs
    ):
        """
        Inicializa el panel lateral colapsable.
        
        Args:
            title: Título del panel
            items: Lista de elementos
            expanded_width: Ancho expandido
            collapsed_width: Ancho contraído
            is_expanded: Estado inicial
        """
        super().__init__(**kwargs)
        
        self.title = title
        self.items = items or []
        self.expanded_width = expanded_width
        self.collapsed_width = collapsed_width
        self.is_expanded = is_expanded
        
        # Configurar estilo del contenedor
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = ft.border_radius.only(
            top_right=12,
            bottom_right=12
        )
        self.border = ft.border.only(
            right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
        )
        self.width = expanded_width if is_expanded else collapsed_width
        self.padding = ft.padding.all(16)
        self.expand = True  # Hacer que el panel se expanda verticalmente
        # Animación removida por compatibilidad
        
        # Construir contenido
        self.content = self._build_collapsible_content()
    
    def _build_collapsible_content(self) -> ft.Column:
        """Construye el contenido del panel colapsable."""
        
        panel_elements = []
        
        # Header con botón de toggle
        header = self._build_collapsible_header()
        panel_elements.extend([header, ft.Container(height=16)])
        
        # Elementos de navegación
        if self.is_expanded:
            navigation_section = self._build_navigation_section()
            panel_elements.append(navigation_section)
        else:
            # Versión compacta de navegación
            compact_nav = self._build_compact_navigation()
            panel_elements.append(compact_nav)
        
        return ft.Column(
            panel_elements,
            spacing=0,
            expand=True
        )
    
    def _build_collapsible_header(self) -> ft.Row:
        """Construye el header del panel colapsable."""
        
        header_elements = []
        
        # Título (solo si está expandido)
        if self.is_expanded:
            title_text = ft.Text(
                self.title,
                size=18,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE
            )
            header_elements.append(title_text)
            header_elements.append(ft.Container(expand=True))
        
        # Botón de toggle
        toggle_icon = ft.Icons.CHEVRON_LEFT if self.is_expanded else ft.Icons.CHEVRON_RIGHT
        toggle_button = ModernIconButton(
            icon=toggle_icon,
            on_click=self._toggle_panel,
            tooltip="Contraer panel" if self.is_expanded else "Expandir panel"
        )
        header_elements.append(toggle_button)
        
        return ft.Row(
            header_elements,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _build_navigation_section(self) -> ft.Column:
        """Construye la sección de navegación expandida."""
        
        if not self.items:
            return ft.Column([])
        
        nav_elements = []
        
        for item in self.items:
            if not item.is_divider:
                nav_item = self._build_nav_item(item)
                nav_elements.append(nav_item)
        
        return ft.Column(nav_elements, spacing=2)
    
    def _build_compact_navigation(self) -> ft.Column:
        """Construye la navegación compacta (solo iconos)."""
        
        if not self.items:
            return ft.Column([])
        
        nav_elements = []
        
        for item in self.items:
            if not item.is_divider and item.icon:
                compact_item = ft.Container(
                    content=ft.Icon(
                        item.icon,
                        size=20,
                        color=ft.Colors.PRIMARY if item.is_selected else ft.Colors.ON_SURFACE_VARIANT
                    ),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER if item.is_selected else ft.Colors.TRANSPARENT,
                    border_radius=8,
                    padding=ft.padding.all(8),
                    on_click=item.on_click,
                    tooltip=item.title,

                )
                nav_elements.append(compact_item)
        
        return ft.Column(nav_elements, spacing=4)
    
    def _build_nav_item(self, item: SidePanelItem) -> ft.Container:
        """Construye un elemento de navegación expandido."""
        
        # Reutilizar lógica del SidePanel regular
        # Contenido del elemento
        item_content = []
        
        # Icono
        if item.icon:
            icon_widget = ft.Icon(
                item.icon,
                size=20,
                color=ft.Colors.PRIMARY if item.is_selected else ft.Colors.ON_SURFACE_VARIANT
            )
            item_content.append(icon_widget)
        
        # Título
        title_text = ft.Text(
            item.title,
            size=14,
            weight=ft.FontWeight.W_500 if item.is_selected else ft.FontWeight.W_400,
            color=ft.Colors.ON_SURFACE if item.is_selected else ft.Colors.ON_SURFACE_VARIANT
        )
        item_content.append(title_text)
        
        # Spacer
        item_content.append(ft.Container(expand=True))
        
        # Badge (si existe)
        if item.badge:
            badge_widget = ft.Container(
                content=ft.Text(
                    item.badge,
                    size=12,
                    color=ft.Colors.ON_PRIMARY,
                    weight=ft.FontWeight.W_600
                ),
                bgcolor=ft.Colors.PRIMARY,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=8, vertical=4)
            )
            item_content.append(badge_widget)
        
        # Crear row del elemento
        item_row = ft.Row(
            item_content,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12
        )
        
        # Container clickeable
        return ft.Container(
            content=item_row,
            bgcolor=ft.Colors.PRIMARY_CONTAINER if item.is_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=item.on_click
        )
    
    def _toggle_panel(self, e):
        """Alterna el estado del panel."""
        self.is_expanded = not self.is_expanded
        self.width = self.expanded_width if self.is_expanded else self.collapsed_width
        self.content = self._build_collapsible_content()
    
    def expand_panel(self):
        """Expande el panel."""
        if not self.is_expanded:
            self._toggle_panel(None)
    
    def collapse_panel(self):
        """Contrae el panel."""
        if self.is_expanded:
            self._toggle_panel(None)


# === Funciones Helper ===

def create_camera_side_panel(
    connected_cameras: int = 0,
    scanning_status: str = "idle",
    on_camera_click: Optional[Callable] = None,
    on_scan_click: Optional[Callable] = None,
    on_settings_click: Optional[Callable] = None
) -> SidePanel:
    """
    Crea un panel lateral específico para la gestión de cámaras.
    
    Args:
        connected_cameras: Número de cámaras conectadas
        scanning_status: Estado del escaneo
        on_camera_click: Callback para click en cámaras
        on_scan_click: Callback para click en escaneo
        on_settings_click: Callback para click en configuración
    
    Returns:
        SidePanel configurado para cámaras
    """
    
    # Crear elementos del panel
    items = [
        SidePanelItem(
            title="Cámaras",
            icon=ft.Icons.VIDEOCAM,
            on_click=on_camera_click,
            badge=str(connected_cameras) if connected_cameras > 0 else None,
            is_selected=True
        ),
        SidePanelItem(
            title="Escaneo",
            icon=ft.Icons.WIFI_FIND,
            on_click=on_scan_click,
            badge="●" if scanning_status == "active" else None
        ),
        SidePanelItem(
            title="",
            is_divider=True
        ),
        SidePanelItem(
            title="Configuración",
            icon=ft.Icons.SETTINGS,
            on_click=on_settings_click
        )
    ]
    
    # Crear estadísticas para el footer
    stats = ft.Column([
        StatCard(
            title="Activas",
            value=str(connected_cameras),
            icon=ft.Icons.VIDEOCAM,
            color_scheme="primary"
        ),
        ft.Container(height=8),
        StatCard(
            title="Estado",
            value="Online" if connected_cameras > 0 else "Offline",
            icon=ft.Icons.SIGNAL_WIFI_4_BAR,
            color_scheme="success" if connected_cameras > 0 else "error"
        )
    ])
    
    return SidePanel(
        title="Navegación",
        items=items,
        footer_content=stats
    )


def create_scan_side_panel(
    devices_found: int = 0,
    scan_progress: float = 0.0,
    on_back_click: Optional[Callable] = None
) -> SidePanel:
    """
    Crea un panel lateral específico para escaneo.
    
    Args:
        devices_found: Número de dispositivos encontrados
        scan_progress: Progreso del escaneo (0.0-1.0)
        on_back_click: Callback para volver
    
    Returns:
        SidePanel configurado para escaneo
    """
    
    # Crear elementos del panel
    items = [
        SidePanelItem(
            title="← Volver",
            icon=ft.Icons.ARROW_BACK,
            on_click=on_back_click
        )
    ]
    
    # Crear estadísticas para el footer
    stats = ft.Column([
        StatCard(
            title="Encontrados",
            value=str(devices_found),
            icon=ft.Icons.DEVICES,
            color_scheme="success"
        ),
        ft.Container(height=8),
        StatCard(
            title="Progreso",
            value=f"{scan_progress*100:.0f}%",
            icon=ft.Icons.TIMELINE,
            color_scheme="primary"
        )
    ])
    
    return SidePanel(
        title="Escaneo",
        items=items,
        footer_content=stats
    ) 