"""
Módulo de utilidades para el visor de cámaras.
Incluye gestión de configuración y marcas de cámaras.
"""

from .config import ConfigurationManager, get_config
from .brand_manager import BrandManager, get_brand_manager

__all__ = ["ConfigurationManager", "get_config", "BrandManager", "get_brand_manager"] 