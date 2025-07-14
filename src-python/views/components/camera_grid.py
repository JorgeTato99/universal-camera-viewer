#!/usr/bin/env python3
"""
Camera Grid Component - Grid de cámaras moderno con Material Design 3
====================================================================

Componente para mostrar cámaras en una cuadrícula flexible:
- CameraGrid: Grid principal con soporte para múltiples cámaras
- CameraCard: Tarjeta individual para cada cámara
- Layouts adaptativos y responsivos
- Controles de reproducción y configuración
"""

import flet as ft
from typing import List, Optional, Callable, Union, Dict
from enum import Enum
from .common.modern_button import ModernButton, ModernIconButton
from .common.stat_card import StatCard


class CameraStatus(Enum):
    """Estados posibles de una cámara."""
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ONLINE = "online"
    ERROR = "error"


class CameraInfo:
    """Información de una cámara."""
    
    def __init__(
        self,
        id: str,
        name: str,
        ip: str,
        port: int = 554,
        status: CameraStatus = CameraStatus.OFFLINE,
        brand: str = "Unknown",
        model: str = "Unknown",
        stream_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        fps: int = 0,
        resolution: str = "Unknown"
    ):
        self.id = id
        self.name = name
        self.ip = ip
        self.port = port
        self.status = status
        self.brand = brand
        self.model = model
        self.stream_url = stream_url
        self.thumbnail_url = thumbnail_url
        self.fps = fps
        self.resolution = resolution


class CameraCard(ft.Container):
    """
    Tarjeta individual para mostrar una cámara.
    """
    
    def __init__(
        self,
        camera: CameraInfo,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_fullscreen: Optional[Callable] = None,
        width: int = 280,
        height: int = 200,
        **kwargs
    ):
        """
        Inicializa la tarjeta de cámara.
        
        Args:
            camera: Información de la cámara
            on_connect: Callback para conectar
            on_disconnect: Callback para desconectar
            on_settings: Callback para configuración
            on_fullscreen: Callback para pantalla completa
            width: Ancho de la tarjeta
            height: Alto de la tarjeta
        """
        super().__init__(**kwargs)
        
        self.camera = camera
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_settings = on_settings
        self.on_fullscreen = on_fullscreen
        self.card_width = width
        self.card_height = height
        
        # Configurar estilo del contenedor
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = 12
        self.border = ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.width = width
        self.height = height
        self.padding = ft.padding.all(8)
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ft.Colors.with_opacity(0.1, ft.Colors.SHADOW),
            offset=ft.Offset(0, 2)
        )
        
        # Construir contenido
        self.content = self._build_card_content()
    
    def _build_card_content(self) -> ft.Column:
        """Construye el contenido de la tarjeta."""
        
        # Header con información y controles
        header = self._build_header()
        
        # Área de video/imagen
        video_area = self._build_video_area()
        
        # Footer con estadísticas
        footer = self._build_footer()
        
        return ft.Column([
            header,
            ft.Container(height=8),
            video_area,
            ft.Container(height=8),
            footer
        ],
        spacing=0,
        expand=True
        )
    
    def _build_header(self) -> ft.Row:
        """Construye el header de la tarjeta."""
        
        # Información de la cámara
        camera_info = ft.Column([
            ft.Text(
                self.camera.name,
                size=14,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE
            ),
            ft.Text(
                f"{self.camera.ip}:{self.camera.port}",
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
        ],
        spacing=2,
        tight=True
        )
        
        # Indicador de estado
        status_color = self._get_status_color()
        status_icon = ft.Container(
            content=ft.Icon(
                ft.Icons.CIRCLE,
                size=12,
                color=status_color
            ),
            tooltip=self.camera.status.value.title()
        )
        
        # Botón de configuración
        settings_button = ModernIconButton(
            icon=ft.Icons.MORE_VERT,
            on_click=self._show_menu,
            tooltip="Opciones"
        )
        
        return ft.Row([
            camera_info,
            ft.Container(expand=True),
            status_icon,
            settings_button
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _build_video_area(self) -> ft.Container:
        """Construye el área de video."""
        
        video_content = None
        
        if self.camera.status == CameraStatus.ONLINE:
            # Mostrar video en vivo (placeholder)
            video_content = self._build_live_video()
        elif self.camera.status == CameraStatus.CONNECTING:
            # Mostrar indicador de conexión
            video_content = self._build_connecting_indicator()
        else:
            # Mostrar placeholder offline
            video_content = self._build_offline_placeholder()
        
        return ft.Container(
            content=video_content,
                         bgcolor=ft.Colors.SURFACE,
            border_radius=8,
            expand=True,
            alignment=ft.alignment.center
        )
    
    def _build_live_video(self) -> ft.Stack:
        """Construye el área de video en vivo."""
        
        # Placeholder para video (se reemplazará con video real)
        video_placeholder = ft.Container(
            bgcolor=ft.Colors.GREY_800,
            border_radius=8,
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Icon(
                ft.Icons.VIDEOCAM,
                size=48,
                color=ft.Colors.WHITE70
            )
        )
        
        # Overlay con controles
        controls_overlay = ft.Container(
            content=ft.Row([
                ModernIconButton(
                    icon=ft.Icons.FULLSCREEN,
                    on_click=self._on_fullscreen_click,
                    tooltip="Pantalla completa"
                )
            ],
            alignment=ft.MainAxisAlignment.END
            ),
            alignment=ft.alignment.bottom_right,
            padding=ft.padding.all(8)
        )
        
        return ft.Stack([
            video_placeholder,
            controls_overlay
        ])
    
    def _build_connecting_indicator(self) -> ft.Column:
        """Construye el indicador de conexión."""
        
        return ft.Column([
            ft.ProgressRing(
                width=40,
                height=40,
                color=ft.Colors.PRIMARY
            ),
            ft.Container(height=8),
            ft.Text(
                "Conectando...",
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        tight=True
        )
    
    def _build_offline_placeholder(self) -> ft.Column:
        """Construye el placeholder offline."""
        
        return ft.Column([
            ft.Icon(
                ft.Icons.VIDEOCAM_OFF,
                size=48,
                color=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Container(height=8),
            ft.Text(
                "Desconectado",
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Container(height=8),
            ModernButton(
                text="Conectar",
                on_click=self._on_connect_click,
                style="outlined"
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        tight=True
        )
    
    def _build_footer(self) -> ft.Row:
        """Construye el footer con estadísticas."""
        
        # Estadísticas de la cámara
        stats = []
        
        if self.camera.status == CameraStatus.ONLINE:
            stats.extend([
                ft.Text(
                    f"{self.camera.fps} FPS",
                    size=10,
                    color=ft.Colors.ON_SURFACE_VARIANT
                ),
                ft.Text(
                    self.camera.resolution,
                    size=10,
                    color=ft.Colors.ON_SURFACE_VARIANT
                )
            ])
        else:
            stats.append(
                ft.Text(
                    f"{self.camera.brand} {self.camera.model}",
                    size=10,
                    color=ft.Colors.ON_SURFACE_VARIANT
                )
            )
        
        return ft.Row(
            stats,
            spacing=12
        )
    
    def _get_status_color(self) -> str:
        """Obtiene el color según el estado."""
        
        status_colors = {
            CameraStatus.OFFLINE: ft.Colors.GREY_400,
            CameraStatus.CONNECTING: ft.Colors.ORANGE_400,
            CameraStatus.ONLINE: ft.Colors.GREEN_400,
            CameraStatus.ERROR: ft.Colors.RED_400
        }
        
        return status_colors.get(self.camera.status, ft.Colors.GREY_400)
    
    def _show_menu(self, e):
        """Muestra el menú de opciones."""
        # Implementar menú contextual
        pass
    
    def _on_connect_click(self, e):
        """Maneja click en conectar."""
        if self.on_connect:
            self.on_connect(self.camera)
    
    def _on_disconnect_click(self, e):
        """Maneja click en desconectar."""
        if self.on_disconnect:
            self.on_disconnect(self.camera)
    
    def _on_fullscreen_click(self, e):
        """Maneja click en pantalla completa."""
        if self.on_fullscreen:
            self.on_fullscreen(self.camera)
    
    def update_camera_info(self, camera: CameraInfo):
        """Actualiza la información de la cámara."""
        self.camera = camera
        self.content = self._build_card_content()
    
    def update_status(self, status: CameraStatus):
        """Actualiza solo el estado de la cámara."""
        self.camera.status = status
        self.content = self._build_card_content()


class CameraGrid(ft.Container):
    """
    Grid principal para mostrar múltiples cámaras.
    """
    
    def __init__(
        self,
        cameras: Optional[List[CameraInfo]] = None,
        columns: int = 3,
        card_width: int = 280,
        card_height: int = 200,
        spacing: int = 16,
        on_camera_connect: Optional[Callable] = None,
        on_camera_disconnect: Optional[Callable] = None,
        on_camera_settings: Optional[Callable] = None,
        on_camera_fullscreen: Optional[Callable] = None,
        **kwargs
    ):
        """
        Inicializa el grid de cámaras.
        
        Args:
            cameras: Lista de cámaras
            columns: Número de columnas
            card_width: Ancho de tarjetas
            card_height: Alto de tarjetas
            spacing: Espaciado entre tarjetas
            on_camera_connect: Callback para conectar cámara
            on_camera_disconnect: Callback para desconectar cámara
            on_camera_settings: Callback para configuración
            on_camera_fullscreen: Callback para pantalla completa
        """
        super().__init__(**kwargs)
        
        self.cameras = cameras or []
        self.columns = columns
        self.card_width = card_width
        self.card_height = card_height
        self.spacing = spacing
        self.on_camera_connect = on_camera_connect
        self.on_camera_disconnect = on_camera_disconnect
        self.on_camera_settings = on_camera_settings
        self.on_camera_fullscreen = on_camera_fullscreen
        
        # Configurar contenedor
        self.padding = ft.padding.all(16)
        self.expand = True
        
        # Construir contenido
        self.content = self._build_grid_content()
    
    def _build_grid_content(self) -> ft.Column:
        """Construye el contenido del grid."""
        
        if not self.cameras:
            return self._build_empty_state()
        
        # Crear filas del grid
        grid_rows = []
        
        for i in range(0, len(self.cameras), self.columns):
            row_cameras = self.cameras[i:i + self.columns]
            row_cards = []
            
            for camera in row_cameras:
                card = CameraCard(
                    camera=camera,
                    on_connect=self.on_camera_connect,
                    on_disconnect=self.on_camera_disconnect,
                    on_settings=self.on_camera_settings,
                    on_fullscreen=self.on_camera_fullscreen,
                    width=self.card_width,
                    height=self.card_height
                )
                row_cards.append(card)
            
            # Agregar espaciadores si es necesario
            while len(row_cards) < self.columns:
                row_cards.append(ft.Container(width=self.card_width))
            
            grid_row = ft.Row(
                row_cards,
                spacing=self.spacing,
                alignment=ft.MainAxisAlignment.START
            )
            grid_rows.append(grid_row)
        
        return ft.Column(
            grid_rows,
            spacing=self.spacing,
            scroll=ft.ScrollMode.AUTO
        )
    
    def _build_empty_state(self) -> ft.Column:
        """Construye el estado vacío."""
        
        return ft.Column([
            ft.Icon(
                ft.Icons.VIDEOCAM_OFF,
                size=64,
                color=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Container(height=16),
            ft.Text(
                "No hay cámaras disponibles",
                size=18,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Container(height=8),
            ft.Text(
                "Usa el botón 'Escanear' para buscar cámaras en tu red",
                size=14,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True
        )
    
    def add_camera(self, camera: CameraInfo):
        """Agrega una nueva cámara al grid."""
        self.cameras.append(camera)
        self.content = self._build_grid_content()
    
    def remove_camera(self, camera_id: str):
        """Remueve una cámara del grid."""
        self.cameras = [c for c in self.cameras if c.id != camera_id]
        self.content = self._build_grid_content()
    
    def update_camera(self, camera: CameraInfo):
        """Actualiza una cámara existente."""
        for i, c in enumerate(self.cameras):
            if c.id == camera.id:
                self.cameras[i] = camera
                break
        self.content = self._build_grid_content()
    
    def update_camera_status(self, camera_id: str, status: CameraStatus):
        """Actualiza el estado de una cámara."""
        for camera in self.cameras:
            if camera.id == camera_id:
                camera.status = status
                break
        self.content = self._build_grid_content()
    
    def set_columns(self, columns: int):
        """Cambia el número de columnas."""
        self.columns = columns
        self.content = self._build_grid_content()
    
    def clear_cameras(self):
        """Limpia todas las cámaras."""
        self.cameras.clear()
        self.content = self._build_grid_content()
    
    def get_online_cameras(self) -> List[CameraInfo]:
        """Obtiene las cámaras online."""
        return [c for c in self.cameras if c.status == CameraStatus.ONLINE]
    
    def get_offline_cameras(self) -> List[CameraInfo]:
        """Obtiene las cámaras offline."""
        return [c for c in self.cameras if c.status == CameraStatus.OFFLINE]


# === Funciones Helper ===

def create_demo_cameras() -> List[CameraInfo]:
    """Crea cámaras de demostración."""
    
    return [
        CameraInfo(
            id="cam001",
            name="Cámara Entrada",
            ip="192.168.1.100",
            status=CameraStatus.ONLINE,
            brand="Dahua",
            model="IPC-HDW2831T",
            fps=20,
            resolution="1920x1080"
        ),
        CameraInfo(
            id="cam002",
            name="Cámara Garaje",
            ip="192.168.1.101",
            status=CameraStatus.CONNECTING,
            brand="TP-Link",
            model="Tapo C200"
        ),
        CameraInfo(
            id="cam003",
            name="Cámara Jardín",
            ip="192.168.1.102",
            status=CameraStatus.OFFLINE,
            brand="Steren",
            model="CCTV-240"
        )
    ]


def create_responsive_grid(
    cameras: List[CameraInfo],
    page_width: int,
    min_card_width: int = 280
) -> CameraGrid:
    """
    Crea un grid responsivo basado en el ancho de la página.
    
    Args:
        cameras: Lista de cámaras
        page_width: Ancho de la página
        min_card_width: Ancho mínimo de tarjeta
    
    Returns:
        CameraGrid configurado responsivamente
    """
    
    # Calcular número de columnas basado en el ancho
    columns = max(1, page_width // (min_card_width + 16))
    
    return CameraGrid(
        cameras=cameras,
        columns=columns,
        card_width=min_card_width,
        card_height=200
    ) 