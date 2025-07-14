#!/usr/bin/env python3
"""
Universal Camera Viewer - Main View Refactorizado
==================================================

Vista principal refactorizada que actúa como coordinador entre:
- Navegación principal horizontal
- Páginas modulares especializadas
- Estado global de la aplicación
- Comunicación entre componentes

Este nuevo diseño separa responsabilidades y mejora la escalabilidad.
"""

import flet as ft
from typing import Dict, List, Optional, Callable
import logging

# Importaciones locales refactorizadas
from .components.navigation_bar import create_main_navigation, NavigationConstants
from .pages import CamerasPage, ScanPage, AnalyticsPage, SettingsPage


class MainView:
    """
    Vista principal refactorizada como coordinador ligero.
    
    Responsabilidades:
    - Gestionar navegación entre módulos
    - Mantener estado global mínimo
    - Coordinar comunicación entre páginas
    - Proporcionar estructura de layout principal
    """
    
    def __init__(self, page: ft.Page):
        """
        Inicializa la vista principal refactorizada.
        
        Args:
            page: Página principal de Flet
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # Estado de navegación
        self.current_module = NavigationConstants.CAMERAS
        
        # Referencias a páginas
        self.pages: Dict[str, ft.Container] = {}
        self._initialize_pages()
        
        # Componentes principales
        self.navigation_bar = None
        self.main_container = None
        
        # Estado global compartido
        self.global_cameras = []  # Lista global de cámaras
        
    def _initialize_pages(self):
        """Inicializa todas las páginas del sistema."""
        
        # Página de cámaras (principal)
        self.pages[NavigationConstants.CAMERAS] = CamerasPage(
            on_scan_request=self._handle_navigation_to_scan
        )
        
        # Página de escaneo
        self.pages[NavigationConstants.SCAN] = ScanPage(
            on_camera_found=self._handle_camera_found,
            on_back_to_cameras=self._handle_navigation_to_cameras
        )
        
        # Página de análisis
        self.pages[NavigationConstants.ANALYTICS] = AnalyticsPage()
        
        # Página de configuración (con acceso a la página)
        self.pages[NavigationConstants.SETTINGS] = SettingsPage(page=self.page)
    
    def build(self) -> ft.Column:
        """
        Construye la interfaz principal moderna y modular.
        
        Layout:
        - Navigation Bar horizontal (superior)
        - Página actual (ocupa resto del espacio)
        """
        
        # Crear barra de navegación
        self.navigation_bar = create_main_navigation(
            selected_key=self.current_module,
            on_change=self._handle_navigation_change,
            page=self.page
        )
        
        # Container principal para páginas
        self.main_container = ft.Container(
            content=self.pages[self.current_module],
            expand=True
        )
        
        # Layout principal
        return ft.Column([
            self.navigation_bar,
            self.main_container
        ],
        spacing=0,
        expand=True
        )
    
    def _handle_navigation_change(self, module_key: str):
        """
        Maneja cambios de navegación entre módulos.
        
        Args:
            module_key: Clave del módulo seleccionado
        """
        if module_key != self.current_module:
            self.logger.info(f"Navegando de {self.current_module} a {module_key}")
            
            # Actualizar módulo actual
            self.current_module = module_key
            
            # Cambiar contenido del container principal
            if self.main_container is not None:
                self.main_container.content = self.pages[module_key]
            
            # Actualizar UI
            if hasattr(self.page, 'update'):
                self.page.update()
            
            # Notificar cambio (para métricas, etc.)
            self._on_module_changed(module_key)
    
    def _handle_navigation_to_scan(self):
        """Maneja navegación programática a la página de escaneo."""
        if self.navigation_bar is not None:
            self.navigation_bar.select_item(NavigationConstants.SCAN)
        self._handle_navigation_change(NavigationConstants.SCAN)
    
    def _handle_navigation_to_cameras(self):
        """Maneja navegación programática a la página de cámaras."""
        if self.navigation_bar is not None:
            self.navigation_bar.select_item(NavigationConstants.CAMERAS)
        self._handle_navigation_change(NavigationConstants.CAMERAS)
    
    def _handle_camera_found(self, camera):
        """
        Maneja cuando se encuentra una nueva cámara en el escaneo.
        
        Args:
            camera: Objeto cámara encontrada
        """
        # Agregar a lista global
        self.global_cameras.append(camera)
        
        # Notificar a página de cámaras si tiene el método
        cameras_page = self.pages[NavigationConstants.CAMERAS]
        if cameras_page and hasattr(cameras_page, 'add_camera') and callable(getattr(cameras_page, 'add_camera')):
            try:
                cameras_page.add_camera(camera)  # type: ignore
            except Exception as e:
                self.logger.warning(f"Error al agregar cámara a la página: {e}")
        
        self.logger.info(f"Cámara encontrada y agregada: {getattr(camera, 'ip', 'Unknown')}")
    
    def _on_module_changed(self, module_key: str):
        """
        Callback interno cuando cambia el módulo activo.
        
        Args:
            module_key: Clave del nuevo módulo
        """
        # Lógica adicional cuando cambia el módulo
        # Por ejemplo: métricas, logging, preparación de datos, etc.
        
        # Actualizar título de la ventana si es necesario
        module_titles = {
            NavigationConstants.CAMERAS: "Cámaras - Visor Universal",
            NavigationConstants.SCAN: "Escaneo - Visor Universal", 
            NavigationConstants.ANALYTICS: "Análisis - Visor Universal",
            NavigationConstants.SETTINGS: "Configuración - Visor Universal"
        }
        
        if module_key in module_titles:
            self.page.title = module_titles[module_key]
    
    # === Métodos Públicos para Integración ===
    
    def get_current_page(self) -> Optional[ft.Container]:
        """Retorna la página actualmente activa."""
        return self.pages.get(self.current_module)
    
    def get_page(self, module_key: str) -> Optional[ft.Container]:
        """
        Retorna una página específica.
        
        Args:
            module_key: Clave del módulo
            
        Returns:
            La página solicitada o None si no existe
        """
        return self.pages.get(module_key)
    
    def update_global_cameras(self, cameras_list: List):
        """
        Actualiza la lista global de cámaras.
        
        Args:
            cameras_list: Nueva lista de cámaras
        """
        self.global_cameras = cameras_list
        
        # Sincronizar con página de cámaras si tiene el método
        cameras_page = self.pages[NavigationConstants.CAMERAS]
        if cameras_page and hasattr(cameras_page, 'update_cameras') and callable(getattr(cameras_page, 'update_cameras')):
            try:
                cameras_page.update_cameras(cameras_list)  # type: ignore
            except Exception as e:
                self.logger.warning(f"Error al actualizar cámaras en la página: {e}")
    
    def navigate_to_module(self, module_key: str):
        """
        Navega programáticamente a un módulo específico.
        
        Args:
            module_key: Clave del módulo destino
        """
        if module_key in self.pages:
            if self.navigation_bar is not None:
                self.navigation_bar.select_item(module_key)
            self._handle_navigation_change(module_key)
    
    def refresh_current_page(self):
        """Refresca la página actualmente activa."""
        current_page = self.get_current_page()
        if current_page and hasattr(current_page, '_refresh_content') and callable(getattr(current_page, '_refresh_content')):
            try:
                current_page._refresh_content()  # type: ignore
            except Exception as e:
                self.logger.warning(f"Error al refrescar página: {e}")
    
    # === Métodos de Ciclo de Vida ===
    
    def initialize(self):
        """Inicializa la vista y sus componentes."""
        self.logger.info("Inicializando MainView refactorizado")
        
        # Configurar página principal
        self.page.title = "Visor Universal de Cámaras"
        # Configurar ventana (estos atributos pueden no estar disponibles en todas las versiones)
        if hasattr(self.page, 'window_width'):
            self.page.window_width = 1200  # type: ignore
        if hasattr(self.page, 'window_height'):
            self.page.window_height = 800  # type: ignore
        if hasattr(self.page, 'window_min_width'):
            self.page.window_min_width = 800  # type: ignore
        if hasattr(self.page, 'window_min_height'):
            self.page.window_min_height = 600  # type: ignore
        
        # Configurar tema moderno
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        
        # Inicializar página de cámaras como predeterminada
        self._on_module_changed(self.current_module)
        
        self.logger.info("MainView refactorizado inicializado correctamente")
    
    def cleanup(self):
        """Limpia recursos y referencias."""
        self.logger.info("Limpiando MainView refactorizado")
        
        # Limpiar páginas si tienen métodos de cleanup
        for page in self.pages.values():
            if page and hasattr(page, 'cleanup') and callable(getattr(page, 'cleanup')):
                try:
                    page.cleanup()  # type: ignore
                except Exception as e:
                    self.logger.warning(f"Error al limpiar página: {e}")
        
        # Limpiar referencias
        self.pages.clear()
        self.global_cameras.clear()
        
        self.logger.info("MainView refactorizado limpiado")


# === Funciones Helper ===

def create_main_view(page: ft.Page) -> MainView:
    """
    Función factory para crear una instancia de MainView.
    
    Args:
        page: Página principal de Flet
        
    Returns:
        Instancia configurada de MainView
    """
    main_view = MainView(page)
    main_view.initialize()
    return main_view


def get_module_info() -> Dict[str, str]:
    """
    Retorna información sobre los módulos disponibles.
    
    Returns:
        Diccionario con información de módulos
    """
    return {
        NavigationConstants.CAMERAS: "Gestión y visualización de cámaras IP",
        NavigationConstants.SCAN: "Escaneo y descubrimiento de dispositivos", 
        NavigationConstants.ANALYTICS: "Análisis y estadísticas de uso",
        NavigationConstants.SETTINGS: "Configuración de la aplicación"
    } 