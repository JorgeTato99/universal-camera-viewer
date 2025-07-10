#!/usr/bin/env python3
"""
Toolbar Component - Barra de herramientas moderna con Material Design 3
======================================================================

Componente para crear barras de herramientas flexibles y modernas:
- ModernToolbar: Barra principal con acciones primarias
- Soporte para botones, iconos, títulos y separadores
- Adaptable a diferentes contextos y módulos
"""

import flet as ft
from typing import List, Optional, Callable, Union
from .common.modern_button import ModernButton, ModernIconButton


class ToolbarAction:
    """Representa una acción en la barra de herramientas."""
    
    def __init__(
        self,
        title: str,
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        tooltip: Optional[str] = None,
        is_primary: bool = False,
        disabled: bool = False
    ):
        self.title = title
        self.icon = icon
        self.on_click = on_click
        self.tooltip = tooltip or title
        self.is_primary = is_primary
        self.disabled = disabled


class ModernToolbar(ft.Container):
    """
    Barra de herramientas moderna con Material Design 3.
    
    Soporta título, subtítulo, acciones primarias y secundarias.
    """
    
    def __init__(
        self,
        title: str,
        subtitle: Optional[str] = None,
        actions: Optional[List[ToolbarAction]] = None,
        show_back_button: bool = False,
        on_back: Optional[Callable] = None,
        height: int = 64,
        **kwargs
    ):
        """
        Inicializa la barra de herramientas moderna.
        
        Args:
            title: Título principal
            subtitle: Subtítulo opcional
            actions: Lista de acciones disponibles
            show_back_button: Mostrar botón de retroceso
            on_back: Callback para botón de retroceso
            height: Altura de la barra
        """
        super().__init__(**kwargs)
        
        self.title = title
        self.subtitle = subtitle
        self.actions = actions or []
        self.show_back_button = show_back_button
        self.on_back = on_back
        self.toolbar_height = height
        
        # Configurar estilo del contenedor
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = ft.border_radius.only(
            top_left=12,
            top_right=12
        )
        self.padding = ft.padding.symmetric(horizontal=16, vertical=8)
        self.height = height
        
        # Construir contenido
        self.content = self._build_toolbar_content()
    
    def _build_toolbar_content(self) -> ft.Row:
        """Construye el contenido de la barra de herramientas."""
        
        # Elementos del lado izquierdo
        left_elements = []
        
        # Botón de retroceso
        if self.show_back_button:
            back_button = ModernIconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self.on_back,
                tooltip="Volver"
            )
            left_elements.append(back_button)
        
        # Título y subtítulo
        title_column = self._build_title_section()
        left_elements.append(title_column)
        
        # Elementos del lado derecho (acciones)
        right_elements = self._build_actions_section()
        
        # Row principal
        return ft.Row([
            ft.Row(left_elements, tight=True),
            ft.Container(expand=True),  # Spacer
            ft.Row(right_elements, tight=True)
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _build_title_section(self) -> ft.Column:
        """Construye la sección de título."""
        
        title_elements = []
        
        # Título principal
        title_text = ft.Text(
            self.title,
            size=20,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_SURFACE
        )
        title_elements.append(title_text)
        
        # Subtítulo (si existe)
        if self.subtitle:
            subtitle_text = ft.Text(
                self.subtitle,
                size=14,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
            title_elements.append(subtitle_text)
        
        return ft.Column(
            title_elements,
            spacing=2,
            tight=True
        )
    
    def _build_actions_section(self) -> List[ft.Control]:
        """Construye la sección de acciones."""
        
        if not self.actions:
            return []
        
        action_elements = []
        
        for action in self.actions:
            if action.icon:
                # Acción con icono
                action_btn = ModernIconButton(
                    icon=action.icon,
                    on_click=action.on_click,
                    tooltip=action.tooltip,
                    disabled=action.disabled
                )
            else:
                # Acción con texto
                action_btn = ModernButton(
                    text=action.title,
                    on_click=action.on_click,
                    style="filled" if action.is_primary else "outlined",
                    disabled=action.disabled
                )
            
            action_elements.append(action_btn)
        
        return action_elements
    
    def add_action(self, action: ToolbarAction):
        """Agrega una nueva acción a la barra."""
        self.actions.append(action)
        self.content = self._build_toolbar_content()
    
    def remove_action(self, action_title: str):
        """Remueve una acción por título."""
        self.actions = [a for a in self.actions if a.title != action_title]
        self.content = self._build_toolbar_content()
    
    def update_title(self, new_title: str, new_subtitle: Optional[str] = None):
        """Actualiza el título y subtítulo."""
        self.title = new_title
        if new_subtitle is not None:
            self.subtitle = new_subtitle
        self.content = self._build_toolbar_content()
    
    def set_actions(self, actions: List[ToolbarAction]):
        """Establece una nueva lista de acciones."""
        self.actions = actions
        self.content = self._build_toolbar_content()


class SearchToolbar(ft.Container):
    """
    Barra de herramientas especializada para búsqueda.
    """
    
    def __init__(
        self,
        placeholder: str = "Buscar...",
        on_search: Optional[Callable[[str], None]] = None,
        on_clear: Optional[Callable] = None,
        show_filters: bool = False,
        **kwargs
    ):
        """
        Inicializa la barra de búsqueda.
        
        Args:
            placeholder: Texto placeholder
            on_search: Callback para búsqueda
            on_clear: Callback para limpiar
            show_filters: Mostrar botón de filtros
        """
        super().__init__(**kwargs)
        
        self.placeholder = placeholder
        self.on_search = on_search
        self.on_clear = on_clear
        self.show_filters = show_filters
        self.search_query = ""
        
        # Configurar contenedor
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = 12
        self.padding = ft.padding.all(16)
        self.height = 64
        
        # Construir contenido
        self.content = self._build_search_content()
    
    def _build_search_content(self) -> ft.Row:
        """Construye el contenido de búsqueda."""
        
        # Campo de búsqueda
        self.search_field = ft.TextField(
            hint_text=self.placeholder,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            filled=True,
            bgcolor=ft.Colors.SURFACE,
            on_change=self._on_search_change,
            on_submit=self._on_search_submit,
            expand=True
        )
        
        search_elements: List[ft.Control] = [self.search_field]
        
        # Botón de limpiar
        if self.search_query:
            clear_button = ModernIconButton(
                icon=ft.Icons.CLEAR,
                on_click=self._on_clear_click,
                tooltip="Limpiar búsqueda"
            )
            search_elements.append(clear_button)
        
        # Botón de filtros
        if self.show_filters:
            filter_button = ModernIconButton(
                icon=ft.Icons.FILTER_LIST,
                on_click=self._on_filter_click,
                tooltip="Filtros"
            )
            search_elements.append(filter_button)
        
        return ft.Row(
            search_elements,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _on_search_change(self, e):
        """Maneja cambios en el campo de búsqueda."""
        self.search_query = e.control.value
        if self.on_search:
            self.on_search(self.search_query)
    
    def _on_search_submit(self, e):
        """Maneja envío de búsqueda."""
        if self.on_search:
            self.on_search(self.search_query)
    
    def _on_clear_click(self, e):
        """Maneja click en limpiar."""
        self.search_query = ""
        self.search_field.value = ""
        if self.on_clear:
            self.on_clear()
        self.content = self._build_search_content()
    
    def _on_filter_click(self, e):
        """Maneja click en filtros."""
        # Implementar lógica de filtros según necesidad
        pass
    
    def clear_search(self):
        """Limpia la búsqueda programáticamente."""
        self._on_clear_click(None)


# === Funciones Helper ===

def create_camera_toolbar(
    camera_count: int = 0,
    on_add_camera: Optional[Callable] = None,
    on_scan_network: Optional[Callable] = None,
    on_refresh: Optional[Callable] = None
) -> ModernToolbar:
    """
    Crea una barra de herramientas específica para la gestión de cámaras.
    
    Args:
        camera_count: Número de cámaras conectadas
        on_add_camera: Callback para agregar cámara
        on_scan_network: Callback para escanear red
        on_refresh: Callback para refrescar
    
    Returns:
        ModernToolbar configurada para cámaras
    """
    
    subtitle = f"{camera_count} cámaras conectadas" if camera_count > 0 else "Sin cámaras conectadas"
    
    actions = [
        ToolbarAction(
            title="Agregar",
            icon=ft.Icons.ADD,
            on_click=on_add_camera,
            tooltip="Agregar cámara manualmente"
        ),
        ToolbarAction(
            title="Escanear",
            icon=ft.Icons.WIFI_FIND,
            on_click=on_scan_network,
            tooltip="Escanear red para encontrar cámaras",
            is_primary=True
        ),
        ToolbarAction(
            title="Refrescar",
            icon=ft.Icons.REFRESH,
            on_click=on_refresh,
            tooltip="Refrescar lista de cámaras"
        )
    ]
    
    return ModernToolbar(
        title="Cámaras",
        subtitle=subtitle,
        actions=actions
    )


def create_scan_toolbar(
    is_scanning: bool = False,
    on_start_scan: Optional[Callable] = None,
    on_stop_scan: Optional[Callable] = None,
    on_back: Optional[Callable] = None
) -> ModernToolbar:
    """
    Crea una barra de herramientas específica para escaneo.
    
    Args:
        is_scanning: Estado de escaneo activo
        on_start_scan: Callback para iniciar escaneo
        on_stop_scan: Callback para detener escaneo
        on_back: Callback para volver
    
    Returns:
        ModernToolbar configurada para escaneo
    """
    
    subtitle = "Escaneando dispositivos..." if is_scanning else "Listo para escanear"
    
    actions = []
    
    if is_scanning:
        actions.append(
            ToolbarAction(
                title="Detener",
                icon=ft.Icons.STOP,
                on_click=on_stop_scan,
                tooltip="Detener escaneo",
                is_primary=True
            )
        )
    else:
        actions.append(
            ToolbarAction(
                title="Iniciar",
                icon=ft.Icons.PLAY_ARROW,
                on_click=on_start_scan,
                tooltip="Iniciar escaneo",
                is_primary=True
            )
        )
    
    return ModernToolbar(
        title="Escaneo de Red",
        subtitle=subtitle,
        actions=actions,
        show_back_button=True,
        on_back=on_back
    ) 