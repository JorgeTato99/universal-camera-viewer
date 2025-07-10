#!/usr/bin/env python3
"""
Visor Universal de Cámaras Multi-Marca - Main Entry Point
=========================================================

Aplicación principal que ejecuta la interfaz Flet usando la arquitectura MVP implementada.
Este es el entry point clásico que permite ver la interfaz visual inmediatamente.

Ejecución:
    python main.py
    
Funcionalidades actuales:
- Visualización de configuración de cámaras
- Estado de marcas soportadas  
- Interfaz de navegación moderna
- Integración con ConfigurationManager y BrandManager
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import flet as ft
from src.utils.config import get_config
from src.utils.brand_manager import get_brand_manager
from src.models import CameraModel, ConnectionConfig, ProtocolType, ConnectionStatus

import asyncio
from src.services.connection_service import ConnectionService, ConnectionServiceConfig
from src.services.scan_service import ScanService, ScanServiceConfig
from src.models.scan_model import ScanRange

# Configuración de cámaras demo
CAMERAS_CONFIG = [
    {
        "id": "dahua_001",
        "brand": "Dahua",
        "model": "IPC-HDW2231T-ZS",
        "ip": "192.168.1.100",
        "protocol": "onvif",
        "username": "admin",
        "password": "admin123"
    },
    {
        "id": "tplink_001", 
        "brand": "TP-Link",
        "model": "Tapo C200",
        "ip": "192.168.1.101", 
        "protocol": "rtsp",
        "username": "admin",
        "password": "admin"
    },
    {
        "id": "steren_001",
        "brand": "Steren",
        "model": "CCTV-240",
        "ip": "192.168.1.102",
        "protocol": "http",
        "username": "admin", 
        "password": "123456"
    }
]

# Global services
connection_service: Optional[ConnectionService] = None
scan_service: Optional[ScanService] = None

def initialize_services():
    """Inicializa los servicios de la aplicación."""
    global connection_service, scan_service
    
    try:
        # Configurar servicios
        conn_config = ConnectionServiceConfig(
            max_concurrent_connections=20,
            connection_timeout=8.0,
            auto_reconnect=True
        )
        
        scan_config = ScanServiceConfig(
            max_concurrent_scans=2,
            enable_scan_cache=True,
            enable_network_analysis=True
        )
        
        # Inicializar servicios
        connection_service = ConnectionService(conn_config)
        scan_service = ScanService(scan_config)
        
        # Iniciar servicios
        connection_service.start()
        scan_service.start()
        
        print("✅ Services initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        return False

async def real_connect_camera(camera_id: str):
    """Conecta una cámara usando el ConnectionService real."""
    try:
        # Buscar cámara en configuración
        camera_config = next(
            (cam for cam in CAMERAS_CONFIG if cam["id"] == camera_id), 
            None
        )
        
        if not camera_config:
            return False
        
        # Crear CameraModel con parámetros correctos
        connection_config = ConnectionConfig(
            ip=camera_config["ip"],
            username=camera_config.get("username", "admin"),
            password=camera_config.get("password", "admin"),
            rtsp_port=554 if camera_config["protocol"] == "rtsp" else 554,
            onvif_port=80 if camera_config["protocol"] == "onvif" else 80,
            http_port=80 if camera_config["protocol"] == "http" else 80
        )
        
        camera = CameraModel(
            brand=camera_config["brand"],
            model=camera_config["model"],
            display_name=f"{camera_config['brand']} {camera_config['model']}",
            connection_config=connection_config
        )
        
        # Establecer configuración adicional
        camera.camera_id = camera_id
        camera.protocol = ProtocolType(camera_config["protocol"])
        
        # Conectar usando service
        if connection_service:
            success = await connection_service.connect_camera_async(camera)
            if success:
                print(f"✅ Camera {camera_id} connected via real service")
                return True
            else:
                print(f"❌ Failed to connect camera {camera_id}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error connecting camera {camera_id}: {e}")
        return False

async def real_scan_network():
    """Ejecuta un escaneo de red real usando ScanService."""
    try:
        if not scan_service:
            print("❌ Scan service not available")
            return []
        
        # Configurar rango de escaneo
        scan_range = ScanRange(
            start_ip="192.168.1.1",
            end_ip="192.168.1.50",
            ports=[80, 554, 8080, 8000]
        )
        
        print("🔍 Starting network scan...")
        
        # Iniciar escaneo
        scan_id = await scan_service.start_scan_async(scan_range)
        
        if scan_id:
            print(f"📡 Scan {scan_id} started successfully")
            
            # Simular espera de resultados (en implementación real usaríamos callbacks)
            await asyncio.sleep(3)
            
            # Obtener resultados
            if scan_id in scan_service.active_scans:
                scan_model = scan_service.active_scans[scan_id]
                cameras_found = scan_model.get_camera_results()
                print(f"✅ Scan completed. Found {len(cameras_found)} cameras")
                return cameras_found
        
        return []
        
    except Exception as e:
        print(f"❌ Error in network scan: {e}")
        return []

def show_service_metrics():
    """Muestra métricas de los servicios en consola."""
    try:
        if connection_service:
            conn_metrics = connection_service.get_service_metrics()
            print("\n📊 CONNECTION SERVICE METRICS:")
            print(f"  Status: {conn_metrics['service_status']}")
            print(f"  Active Connections: {conn_metrics['active_connections']}")
            print(f"  Total Connections: {conn_metrics['total_connections']}")
        
        if scan_service:
            scan_metrics = scan_service.get_service_metrics()
            print("\n📡 SCAN SERVICE METRICS:")
            print(f"  Status: {scan_metrics['service_status']}")
            print(f"  Active Scans: {scan_metrics['active_scans']}")
            print(f"  Cache Entries: {scan_metrics['cache_entries']}")
            print(f"  Total Cameras Discovered: {scan_metrics['total_cameras_discovered']}")
        
    except Exception as e:
        print(f"Error getting metrics: {e}")


class CameraViewerApp:
    """Aplicación principal de visor de cámaras."""
    
    def __init__(self):
        """Inicializa la aplicación."""
        self.page = None
        self.brand_manager = get_brand_manager()
        self.config_manager = get_config()
        self.cameras = []  # Lista de cámaras
        self.current_tab = 0  # Tab actual
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("CameraViewerApp initialized")
        
        # Cargar cámaras desde configuración
        self.load_cameras_from_config()
    
    def setup_page(self, page: ft.Page):
        """Configura la página principal."""
        self.page = page
        page.title = "Visor Universal de Cámaras Multi-Marca - MVP Architecture"
        page.theme_mode = ft.ThemeMode.LIGHT
        
        # Configurar ventana (API correcta de Flet)
        page.window.width = 1200
        page.window.height = 800
        page.window.center()
        
        # Crear interfaz con tabs
        self.create_interface()
        self.page.update()

    def setup_logging(self):
        """Configura el sistema de logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('camera_viewer.log')
            ]
        )
    
    def load_cameras_from_config(self):
        """Carga cámaras desde la configuración."""
        cameras_config = self.config_manager.get_cameras_config()
        
        for cam_config in cameras_config:
            try:
                # Crear ConnectionConfig
                connection_config = ConnectionConfig(
                    ip=cam_config['ip'],
                    username=cam_config['username'],
                    password=cam_config['password'],
                    rtsp_port=cam_config.get('rtsp_port', 554),
                    onvif_port=cam_config.get('onvif_port', 80),
                    http_port=cam_config.get('http_port', 80)
                )
                
                # Obtener info de marca para display name
                brand_info = self.brand_manager.get_brand_info(cam_config['brand'])
                display_name = f"{brand_info.name if brand_info else cam_config['brand'].title()} - {cam_config['ip']}"
                
                # Crear CameraModel
                camera = CameraModel(
                    brand=cam_config['brand'],
                    model=cam_config.get('model', 'generic'),
                    display_name=display_name,
                    connection_config=connection_config
                )
                
                # Simular algunos protocolos soportados
                camera.capabilities.supported_protocols = [ProtocolType.RTSP, ProtocolType.ONVIF]
                
                self.cameras.append(camera)
                
            except Exception as e:
                self.logger.error(f"Error creando cámara {cam_config.get('ip', 'unknown')}: {e}")
    
    def create_header(self) -> ft.Container:
        """Crea el header de la aplicación."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.VIDEOCAM, color=ft.Colors.WHITE, size=32),
                ft.Text(
                    "Visor Universal de Cámaras Multi-Marca",
                    size=24,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ARCHITECTURE, color=ft.Colors.WHITE70, size=16),
                        ft.Text("MVP Architecture", color=ft.Colors.WHITE70, size=12)
                    ]),
                    padding=ft.padding.all(8),
                    bgcolor=ft.Colors.BLUE_800,
                    border_radius=8
                )
            ]),
            bgcolor=ft.Colors.BLUE_700,
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
        )
    
    def create_camera_card(self, camera: CameraModel) -> ft.Card:
        """Crea una tarjeta para mostrar información de cámara."""
        # Determinar color del estado
        status_color = ft.Colors.GREY_400
        status_icon = ft.Icons.HELP_OUTLINE
        
        if camera.status == ConnectionStatus.CONNECTED:
            status_color = ft.Colors.GREEN_500
            status_icon = ft.Icons.CHECK_CIRCLE
        elif camera.status == ConnectionStatus.ERROR:
            status_color = ft.Colors.RED_500
            status_icon = ft.Icons.ERROR
        elif camera.status == ConnectionStatus.CONNECTING:
            status_color = ft.Colors.ORANGE_500
            status_icon = ft.Icons.SYNC
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header de la tarjeta
                    ft.Row([
                        ft.Icon(ft.Icons.VIDEOCAM, color=ft.Colors.BLUE_700, size=20),
                        ft.Text(
                            camera.display_name,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            expand=True
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(status_icon, color=status_color, size=16),
                                ft.Text(camera.status.value.title(), color=status_color, size=12)
                            ]),
                            padding=ft.padding.all(4),
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8
                        )
                    ]),
                    
                    ft.Divider(height=1),
                    
                    # Información de conexión
                    ft.Row([
                        ft.Icon(ft.Icons.NETWORK_CHECK, color=ft.Colors.GREY_600, size=16),
                        ft.Text(f"IP: {camera.connection_config.ip}", size=14),
                        ft.Container(expand=True),
                        ft.Text(f"Marca: {camera.brand.title()}", size=14, color=ft.Colors.GREY_600)
                    ]),
                    
                    # Puertos
                    ft.Row([
                        ft.Icon(ft.Icons.SETTINGS_ETHERNET, color=ft.Colors.GREY_600, size=16),
                        ft.Text(f"RTSP: {camera.connection_config.rtsp_port}", size=12),
                        ft.Text(f"ONVIF: {camera.connection_config.onvif_port}", size=12),
                        ft.Text(f"HTTP: {camera.connection_config.http_port}", size=12),
                    ]),
                    
                    # Protocolos soportados
                    ft.Row([
                        ft.Icon(ft.Icons.SWAP_HORIZ, color=ft.Colors.GREY_600, size=16),
                        ft.Text("Protocolos:", size=12, color=ft.Colors.GREY_600),
                        *[
                            ft.Container(
                                content=ft.Text(protocol.value.upper(), size=10, color=ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                bgcolor=ft.Colors.BLUE_600,
                                border_radius=4
                            )
                            for protocol in camera.capabilities.supported_protocols
                        ]
                    ]),
                    
                    # Estadísticas
                    ft.Row([
                        ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.GREY_600, size=16),
                        ft.Text(f"Intentos: {camera.stats.connection_attempts}", size=12),
                        ft.Text(f"Éxitos: {camera.stats.successful_connections}", size=12),
                        ft.Text(f"Tasa: {camera.stats.get_success_rate():.1f}%", size=12),
                    ]),
                    
                    # Botones de acción
                    ft.Row([
                        ft.ElevatedButton(
                            "Conectar",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=lambda e, cam=camera: self.simulate_connection(cam),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN_500,
                                color=ft.Colors.WHITE
                            )
                        ),
                        ft.ElevatedButton(
                            "Ver Stream",
                            icon=ft.Icons.VISIBILITY,
                            disabled=not camera.is_connected,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_500,
                                color=ft.Colors.WHITE
                            )
                        ),
                        ft.IconButton(
                            ft.Icons.SETTINGS,
                            tooltip="Configuración",
                            icon_color=ft.Colors.GREY_600
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                    
                ], spacing=8),
                padding=ft.padding.all(16),
                width=350
            ),
            elevation=2
        )
    
    def simulate_connection(self, camera: CameraModel):
        """Simula una conexión a la cámara para demo."""
        import random
        
        # Simular diferentes estados
        camera.status = ConnectionStatus.CONNECTING
        self.page.update()
        
        # Simular delay de conexión
        import time
        time.sleep(1)
        
        # Resultado aleatorio para demo
        if random.random() > 0.3:  # 70% de éxito
            camera.set_connection_status(ConnectionStatus.CONNECTED, ProtocolType.RTSP)
        else:
            camera.set_connection_status(ConnectionStatus.ERROR, error="Timeout de conexión")
        
        self.page.update()

    def create_cameras_tab(self) -> ft.Container:
        """Crea la pestaña de cámaras."""
        if not self.cameras:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.VIDEOCAM_OFF, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No hay cámaras configuradas", size=18, color=ft.Colors.GREY_600),
                    ft.Text("Configura variables de entorno para agregar cámaras", size=14, color=ft.Colors.GREY_400),
                    ft.ElevatedButton(
                        "Ver Documentación",
                        icon=ft.Icons.HELP,
                        on_click=lambda e: print("TODO: Abrir documentación")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        
        # Crear grid de cámaras
        camera_cards = [self.create_camera_card(camera) for camera in self.cameras]
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"Cámaras Configuradas ({len(self.cameras)})", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Actualizar",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: self.refresh_cameras()
                    ),
                    ft.ElevatedButton(
                        "Agregar Cámara",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
                    )
                ]),
                
                ft.Divider(),
                
                # Grid de cámaras
                ft.Container(
                    content=ft.GridView(
                        camera_cards,
                        runs_count=3,
                        max_extent=380,
                        child_aspect_ratio=1.2,
                        spacing=10,
                        run_spacing=10
                    ),
                    expand=True
                )
            ], spacing=10),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def create_brands_tab(self) -> ft.Container:
        """Crea la pestaña de marcas."""
        brands_summary = self.brand_manager.get_summary()
        
        brand_cards = []
        for brand_info in brands_summary['brands']:
            brand_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.BLUE_700),
                            ft.Text(brand_info['name'], size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(f"{brand_info['models_count']} modelos", size=12),
                                padding=ft.padding.all(4),
                                bgcolor=ft.Colors.BLUE_100,
                                border_radius=4
                            )
                        ]),
                        
                        ft.Text(f"ID: {brand_info['id']}", size=12, color=ft.Colors.GREY_600),
                        
                        ft.Row([
                            ft.Text("Protocolos:", size=12, weight=ft.FontWeight.BOLD),
                            *[
                                ft.Container(
                                    content=ft.Text(protocol.upper(), size=10, color=ft.Colors.WHITE),
                                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                    bgcolor=ft.Colors.GREEN_600,
                                    border_radius=4
                                )
                                for protocol in brand_info['protocols']
                            ]
                        ])
                    ], spacing=8),
                    padding=ft.padding.all(16),
                    width=300
                )
            )
            brand_cards.append(brand_card)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Marcas Soportadas", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Total: {brands_summary['total_brands']} marcas, {brands_summary['total_models']} modelos", 
                       color=ft.Colors.GREY_600),
                
                ft.Divider(),
                
                ft.Container(
                    content=ft.GridView(
                        brand_cards,
                        runs_count=4,
                        max_extent=320,
                        child_aspect_ratio=2,
                        spacing=10,
                        run_spacing=10
                    ),
                    expand=True
                )
            ], spacing=10),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def create_config_tab(self) -> ft.Container:
        """Crea la pestaña de configuración."""
        config_summary = self.config_manager.get_summary()
        
        config_items = [
            ("Cámaras configuradas", str(config_summary['cameras_count'])),
            ("Marcas detectadas", ", ".join(config_summary['cameras_brands'])),
            ("Timeout de conexión", f"{config_summary['connection_timeout']}s"),
            ("Nivel de logging", config_summary['logging_level']),
            ("Auto-conectar", "Sí" if config_summary['auto_connect'] else "No"),
            ("Tamaño de ventana", config_summary['window_size'])
        ]
        
        config_list = []
        for key, value in config_items:
            config_list.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(key, size=14, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(str(value), size=14, color=ft.Colors.GREY_700)
                    ]),
                    padding=ft.padding.all(12),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8,
                    margin=ft.margin.only(bottom=8)
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Configuración del Sistema", size=20, weight=ft.FontWeight.BOLD),
                
                ft.Divider(),
                
                ft.Column(config_list),
                
                ft.Divider(),
                
                ft.Row([
                    ft.ElevatedButton(
                        "Recargar Configuración",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: self.reload_config()
                    ),
                    ft.ElevatedButton(
                        "Exportar Configuración",
                        icon=ft.Icons.DOWNLOAD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
                    )
                ])
            ], spacing=10),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def create_status_tab(self) -> ft.Container:
        """Crea la pestaña de estado."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Estado del Sistema", size=20, weight=ft.FontWeight.BOLD),
                
                ft.Divider(),
                
                # Estado de la migración MVP
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.ARCHITECTURE, color=ft.Colors.BLUE_700, size=24),
                                ft.Text("Migración MVP", size=18, weight=ft.FontWeight.BOLD)
                            ]),
                            
                            ft.Text("✅ Estructura base MVP creada", size=14),
                            ft.Text("✅ Configuration Manager migrado", size=14),
                            ft.Text("✅ Brand Manager implementado", size=14),
                            ft.Text("✅ CameraModel fundamental completo", size=14),
                            ft.Text("🔄 ConnectionModel en desarrollo", size=14),
                            ft.Text("⏳ Services layer pendiente", size=14),
                            ft.Text("⏳ Presenters pendientes", size=14),
                            
                            ft.ProgressBar(value=0.4, color=ft.Colors.BLUE_600),
                            ft.Text("Progreso: 40% completado", size=12, color=ft.Colors.GREY_600)
                        ], spacing=8),
                        padding=ft.padding.all(16)
                    )
                ),
                
                # Información del sistema
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.INFO, color=ft.Colors.GREEN_700, size=24),
                                ft.Text("Información del Sistema", size=18, weight=ft.FontWeight.BOLD)
                            ]),
                            
                            ft.Text(f"Python Path: {sys.executable}", size=12),
                            ft.Text(f"Flet Version: Instalado", size=12),
                            ft.Text(f"Logs: camera_viewer.log", size=12),
                            ft.Text(f"Config Source: Variables de entorno + defaults", size=12),
                        ], spacing=8),
                        padding=ft.padding.all(16)
                    )
                )
            ], spacing=10),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def refresh_cameras(self):
        """Actualiza la lista de cámaras."""
        self.cameras.clear()
        self.load_cameras_from_config()
        self.page.update()
    
    def reload_config(self):
        """Recarga la configuración."""
        self.config_manager.reload_configuration()
        self.brand_manager.reload_configuration()
        self.refresh_cameras()
    
    def on_tab_change(self, e):
        """Maneja el cambio de pestaña."""
        self.current_tab = e.control.selected_index
        self.page.update()
    
    def create_interface(self):
        """Crea la interfaz principal con tabs."""
        # Crear navegación con tabs
        tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(
                    text="Cámaras",
                    icon=ft.Icons.VIDEOCAM,
                    content=self.create_cameras_tab()
                ),
                ft.Tab(
                    text="Marcas",
                    icon=ft.Icons.BUSINESS,
                    content=self.create_brands_tab()
                ),
                ft.Tab(
                    text="Configuración",
                    icon=ft.Icons.SETTINGS,
                    content=self.create_config_tab()
                ),
                ft.Tab(
                    text="Estado",
                    icon=ft.Icons.INFO,
                    content=self.create_status_tab()
                )
            ]
        )
        
        # Layout principal
        main_content = ft.Column([
            self.create_header(),
            ft.Container(content=tabs, expand=True)
        ], spacing=0)
        
        self.page.add(main_content)
        self.page.update()


def main():
    """Función principal que inicia la aplicación."""
    print("🚀 Iniciando Visor Universal de Cámaras Multi-Marca...")
    print("📱 Arquitectura: MVP (Model-View-Presenter)")
    print("🖥️  Framework UI: Flet")
    print("⚡ Estado: Migración en progreso (40% completado)")
    print()
    
    app = CameraViewerApp()
    
    # Inicializar servicios al inicio
    services_ready = initialize_services()
    
    if services_ready:
        app.page.update() # Ensure page is updated after service initialization
        app.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("🚀 Servicios MVP Activos", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.LINK, color=ft.colors.GREEN),
                        title=ft.Text("ConnectionService"),
                        subtitle=ft.Text("Orquestación de conexiones activa"),
                        trailing=ft.Chip(label=ft.Text("RUNNING"), bgcolor=ft.colors.GREEN_100)
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.NETWORK_CHECK, color=ft.colors.BLUE),
                        title=ft.Text("ScanService"), 
                        subtitle=ft.Text("Descubrimiento de red activo"),
                        trailing=ft.Chip(label=ft.Text("RUNNING"), bgcolor=ft.colors.BLUE_100)
                    ),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        text="📊 Ver Métricas de Servicios",
                        on_click=lambda _: show_service_metrics(),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.PURPLE
                    )
                ]),
                padding=20
            )
        )
    
    # Ejecutar aplicación Flet
    ft.app(
        target=app.setup_page,
        name="Visor Universal de Cámaras",
        assets_dir="assets"
    )


if __name__ == "__main__":
    main() 