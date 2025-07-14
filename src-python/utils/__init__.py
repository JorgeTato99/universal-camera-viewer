"""
Utils - Utilidades y Helpers (MVP Architecture)
===============================================

Esta capa contiene utilidades transversales y helpers que pueden ser utilizados
por cualquier otra capa de la aplicación.

Utilidades principales:
- config.py: Gestión de configuración (migrado de src_old)
- brand_manager.py: Gestión de marcas de cámaras (migrado de src_old)  
- logger.py: Sistema de logging centralizado
- validators.py: Validadores de datos
- formatters.py: Formateadores de datos
- constants.py: Constantes de la aplicación

Principios para Utils:
- Funciones puras sin estado cuando sea posible
- Reutilizables entre diferentes capas
- Sin dependencias circulares
- Bien documentadas y testeable
"""

# Importaciones futuras - se irán agregando conforme se migren/implementen
# from .config import ConfigurationManager
# from .brand_manager import BrandManager
# from .logger import setup_logger
# from .validators import *
# from .formatters import *
# from .constants import *

__all__ = [
    # Se agregará conforme se implementen las utils
] 