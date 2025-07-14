"""
Pages - Páginas modulares por funcionalidad
==========================================

Cada página representa un módulo completo de la aplicación:
- cameras_page: Gestión y visualización de cámaras
- scan_page: Escaneo de red y descubrimiento
- analytics_page: Estadísticas y análisis
- settings_page: Configuración de la aplicación

Cada página es auto-contenida y maneja su propio estado.
"""

from .cameras_page import CamerasPage
from .scan_page import ScanPage
from .analytics_page import AnalyticsPage
from .settings_page import SettingsPage

__all__ = [
    "CamerasPage",
    "ScanPage", 
    "AnalyticsPage",
    "SettingsPage"
] 