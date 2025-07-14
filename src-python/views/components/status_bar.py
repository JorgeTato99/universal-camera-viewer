#!/usr/bin/env python3
"""
Status Bar Component - Barra de estado moderna con Material Design 3
===================================================================

Componente para mostrar información de estado en la parte inferior:
- StatusBar: Barra de estado principal
- StatusItem: Elemento individual de estado
- Indicadores de conexión, rendimiento y actividad
- Actualizaciones en tiempo real
"""

import flet as ft
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum


class StatusLevel(Enum):
    """Niveles de estado."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class StatusItem:
    """Elemento individual de estado."""
    
    def __init__(
        self,
        key: str,
        label: str,
        value: str,
        icon: Optional[str] = None,
        level: StatusLevel = StatusLevel.INFO,
        tooltip: Optional[str] = None,
        clickable: bool = False,
        on_click: Optional[Callable] = None
    ):
        self.key = key
        self.label = label
        self.value = value
        self.icon = icon
        self.level = level
        self.tooltip = tooltip or f"{label}: {value}"
        self.clickable = clickable
        self.on_click = on_click
        self.last_updated = datetime.now()


class StatusBar(ft.Container):
    """
    Barra de estado moderna con Material Design 3.
    
    Muestra información de estado de la aplicación.
    """
    
    def __init__(
        self,
        items: Optional[List[StatusItem]] = None,
        show_timestamp: bool = True,
        height: int = 40,
        **kwargs
    ):
        """
        Inicializa la barra de estado.
        
        Args:
            items: Lista de elementos de estado
            show_timestamp: Mostrar timestamp de actualización
            height: Altura de la barra
        """
        super().__init__(**kwargs)
        
        self.items = items or []
        self.show_timestamp = show_timestamp
        self.status_height = height
        self.last_update = datetime.now()
        
        # Configurar estilo del contenedor
        self.bgcolor = ft.Colors.SURFACE
        self.border = ft.border.only(
            top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
        )
        self.height = height
        self.padding = ft.padding.symmetric(horizontal=16, vertical=8)
        
        # Construir contenido
        self.content = self._build_status_content()
    
    def _build_status_content(self) -> ft.Row:
        """Construye el contenido de la barra de estado."""
        
        # Elementos del lado izquierdo
        left_items = self._build_status_items()
        
        # Elementos del lado derecho
        right_items = self._build_right_section()
        
        return ft.Row([
            ft.Row(left_items, spacing=24),
            ft.Container(expand=True),  # Spacer
            ft.Row(right_items, spacing=16)
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _build_status_items(self) -> List[ft.Control]:
        """Construye los elementos de estado."""
        
        if not self.items:
            return []
        
        status_widgets = []
        
        for item in self.items:
            # Contenedor del elemento
            item_content = []
            
            # Icono (si existe)
            if item.icon:
                icon_color = self._get_level_color(item.level)
                icon_widget = ft.Icon(
                    item.icon,
                    size=16,
                    color=icon_color
                )
                item_content.append(icon_widget)
            
            # Texto del elemento
            item_text = ft.Text(
                f"{item.label}: {item.value}",
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
            item_content.append(item_text)
            
            # Crear widget del elemento
            item_widget = ft.Row(
                item_content,
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
            
            # Hacer clickeable si es necesario
            if item.clickable and item.on_click:
                item_container = ft.Container(
                    content=item_widget,
                    on_click=item.on_click,
                    tooltip=item.tooltip,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4
                )
                status_widgets.append(item_container)
            else:
                # Solo tooltip
                item_container = ft.Container(
                    content=item_widget,
                    tooltip=item.tooltip if item.tooltip != f"{item.label}: {item.value}" else None
                )
                status_widgets.append(item_container)
        
        return status_widgets
    
    def _build_right_section(self) -> List[ft.Control]:
        """Construye la sección derecha con información general."""
        
        right_widgets = []
        
        # Timestamp de última actualización
        if self.show_timestamp:
            timestamp_text = ft.Text(
                f"Actualizado: {self.last_update.strftime('%H:%M:%S')}",
                size=10,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
            right_widgets.append(timestamp_text)
        
        return right_widgets
    
    def _get_level_color(self, level: StatusLevel) -> str:
        """Obtiene el color según el nivel."""
        
        level_colors = {
            StatusLevel.INFO: ft.Colors.BLUE_600,
            StatusLevel.SUCCESS: ft.Colors.GREEN_600,
            StatusLevel.WARNING: ft.Colors.ORANGE_600,
            StatusLevel.ERROR: ft.Colors.RED_600
        }
        
        return level_colors.get(level, ft.Colors.GREY_600)
    
    def add_item(self, item: StatusItem):
        """Agrega un elemento de estado."""
        # Remover si ya existe
        self.items = [i for i in self.items if i.key != item.key]
        # Agregar nuevo
        self.items.append(item)
        self._update_content()
    
    def remove_item(self, key: str):
        """Remueve un elemento de estado."""
        self.items = [i for i in self.items if i.key != key]
        self._update_content()
    
    def update_item(self, key: str, value: str, level: Optional[StatusLevel] = None):
        """Actualiza un elemento de estado."""
        for item in self.items:
            if item.key == key:
                item.value = value
                item.last_updated = datetime.now()
                if level:
                    item.level = level
                break
        self._update_content()
    
    def clear_items(self):
        """Limpia todos los elementos."""
        self.items.clear()
        self._update_content()
    
    def _update_content(self):
        """Actualiza el contenido de la barra."""
        self.last_update = datetime.now()
        self.content = self._build_status_content()


class NetworkStatusBar(StatusBar):
    """
    Barra de estado especializada para información de red.
    """
    
    def __init__(self, **kwargs):
        """Inicializa la barra de estado de red."""
        
        # Elementos iniciales
        initial_items = [
            StatusItem(
                key="network_status",
                label="Red",
                value="Desconectado",
                icon=ft.Icons.WIFI_OFF,
                level=StatusLevel.ERROR
            ),
            StatusItem(
                key="cameras_online",
                label="Cámaras",
                value="0/0",
                icon=ft.Icons.VIDEOCAM,
                level=StatusLevel.INFO
            ),
            StatusItem(
                key="scan_status",
                label="Escaneo",
                value="Inactivo",
                icon=ft.Icons.SEARCH,
                level=StatusLevel.INFO
            )
        ]
        
        super().__init__(items=initial_items, **kwargs)
    
    def update_network_status(self, connected: bool):
        """Actualiza el estado de la red."""
        if connected:
            self.update_item(
                "network_status",
                "Conectado",
                StatusLevel.SUCCESS
            )
            # Actualizar icono
            for item in self.items:
                if item.key == "network_status":
                    item.icon = ft.Icons.WIFI
                    break
        else:
            self.update_item(
                "network_status",
                "Desconectado",
                StatusLevel.ERROR
            )
            # Actualizar icono
            for item in self.items:
                if item.key == "network_status":
                    item.icon = ft.Icons.WIFI_OFF
                    break
        
        self._update_content()
    
    def update_cameras_status(self, online: int, total: int):
        """Actualiza el estado de las cámaras."""
        level = StatusLevel.SUCCESS if online > 0 else StatusLevel.WARNING
        self.update_item(
            "cameras_online",
            f"{online}/{total}",
            level
        )
    
    def update_scan_status(self, is_scanning: bool, devices_found: int = 0):
        """Actualiza el estado del escaneo."""
        if is_scanning:
            self.update_item(
                "scan_status",
                f"Activo ({devices_found} encontrados)",
                StatusLevel.INFO
            )
            # Actualizar icono
            for item in self.items:
                if item.key == "scan_status":
                    item.icon = ft.Icons.SEARCH
                    break
        else:
            self.update_item(
                "scan_status",
                "Inactivo",
                StatusLevel.INFO
            )
            # Actualizar icono
            for item in self.items:
                if item.key == "scan_status":
                    item.icon = ft.Icons.SEARCH_OFF
                    break
        
        self._update_content()


class PerformanceStatusBar(StatusBar):
    """
    Barra de estado especializada para información de rendimiento.
    """
    
    def __init__(self, **kwargs):
        """Inicializa la barra de estado de rendimiento."""
        
        # Elementos iniciales
        initial_items = [
            StatusItem(
                key="cpu_usage",
                label="CPU",
                value="0%",
                icon=ft.Icons.MEMORY,
                level=StatusLevel.INFO
            ),
            StatusItem(
                key="memory_usage",
                label="RAM",
                value="0 MB",
                icon=ft.Icons.STORAGE,
                level=StatusLevel.INFO
            ),
            StatusItem(
                key="fps",
                label="FPS",
                value="0",
                icon=ft.Icons.SPEED,
                level=StatusLevel.INFO
            )
        ]
        
        super().__init__(items=initial_items, **kwargs)
    
    def update_cpu_usage(self, percentage: float):
        """Actualiza el uso de CPU."""
        level = StatusLevel.ERROR if percentage > 80 else StatusLevel.WARNING if percentage > 60 else StatusLevel.SUCCESS
        self.update_item(
            "cpu_usage",
            f"{percentage:.1f}%",
            level
        )
    
    def update_memory_usage(self, mb_used: float):
        """Actualiza el uso de memoria."""
        level = StatusLevel.ERROR if mb_used > 500 else StatusLevel.WARNING if mb_used > 300 else StatusLevel.SUCCESS
        self.update_item(
            "memory_usage",
            f"{mb_used:.0f} MB",
            level
        )
    
    def update_fps(self, fps: float):
        """Actualiza los FPS."""
        level = StatusLevel.SUCCESS if fps > 15 else StatusLevel.WARNING if fps > 5 else StatusLevel.ERROR
        self.update_item(
            "fps",
            f"{fps:.1f}",
            level
        )


# === Funciones Helper ===

def create_camera_status_bar(
    cameras_online: int = 0,
    cameras_total: int = 0,
    is_scanning: bool = False,
    network_connected: bool = False
) -> NetworkStatusBar:
    """
    Crea una barra de estado específica para el visor de cámaras.
    
    Args:
        cameras_online: Número de cámaras en línea
        cameras_total: Total de cámaras
        is_scanning: Estado de escaneo
        network_connected: Estado de red
    
    Returns:
        NetworkStatusBar configurada
    """
    
    status_bar = NetworkStatusBar()
    
    # Actualizar estados
    status_bar.update_network_status(network_connected)
    status_bar.update_cameras_status(cameras_online, cameras_total)
    status_bar.update_scan_status(is_scanning)
    
    return status_bar


def create_performance_status_bar(
    cpu_usage: float = 0.0,
    memory_usage: float = 0.0,
    fps: float = 0.0
) -> PerformanceStatusBar:
    """
    Crea una barra de estado de rendimiento.
    
    Args:
        cpu_usage: Uso de CPU en porcentaje
        memory_usage: Uso de memoria en MB
        fps: Frames por segundo
    
    Returns:
        PerformanceStatusBar configurada
    """
    
    status_bar = PerformanceStatusBar()
    
    # Actualizar métricas
    status_bar.update_cpu_usage(cpu_usage)
    status_bar.update_memory_usage(memory_usage)
    status_bar.update_fps(fps)
    
    return status_bar


def create_combined_status_bar(
    cameras_online: int = 0,
    cameras_total: int = 0,
    is_scanning: bool = False,
    network_connected: bool = False,
    cpu_usage: float = 0.0,
    memory_usage: float = 0.0,
    fps: float = 0.0
) -> StatusBar:
    """
    Crea una barra de estado combinada con información de red y rendimiento.
    
    Args:
        cameras_online: Número de cámaras en línea
        cameras_total: Total de cámaras
        is_scanning: Estado de escaneo
        network_connected: Estado de red
        cpu_usage: Uso de CPU en porcentaje
        memory_usage: Uso de memoria en MB
        fps: Frames por segundo
    
    Returns:
        StatusBar con información completa
    """
    
    # Crear elementos combinados
    items = [
        # Información de red
        StatusItem(
            key="network_status",
            label="Red",
            value="Conectado" if network_connected else "Desconectado",
            icon=ft.Icons.WIFI if network_connected else ft.Icons.WIFI_OFF,
            level=StatusLevel.SUCCESS if network_connected else StatusLevel.ERROR
        ),
        StatusItem(
            key="cameras_online",
            label="Cámaras",
            value=f"{cameras_online}/{cameras_total}",
            icon=ft.Icons.VIDEOCAM,
            level=StatusLevel.SUCCESS if cameras_online > 0 else StatusLevel.WARNING
        ),
        StatusItem(
            key="scan_status",
            label="Escaneo",
            value="Activo" if is_scanning else "Inactivo",
            icon=ft.Icons.SEARCH if is_scanning else ft.Icons.SEARCH_OFF,
            level=StatusLevel.INFO
        ),
        # Información de rendimiento
        StatusItem(
            key="cpu_usage",
            label="CPU",
            value=f"{cpu_usage:.1f}%",
            icon=ft.Icons.MEMORY,
            level=StatusLevel.ERROR if cpu_usage > 80 else StatusLevel.WARNING if cpu_usage > 60 else StatusLevel.SUCCESS
        ),
        StatusItem(
            key="memory_usage",
            label="RAM",
            value=f"{memory_usage:.0f} MB",
            icon=ft.Icons.STORAGE,
            level=StatusLevel.ERROR if memory_usage > 500 else StatusLevel.WARNING if memory_usage > 300 else StatusLevel.SUCCESS
        ),
        StatusItem(
            key="fps",
            label="FPS",
            value=f"{fps:.1f}",
            icon=ft.Icons.SPEED,
            level=StatusLevel.SUCCESS if fps > 15 else StatusLevel.WARNING if fps > 5 else StatusLevel.ERROR
        )
    ]
    
    return StatusBar(items=items) 