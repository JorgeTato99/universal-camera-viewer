"""
Protocol Handlers - Manejadores específicos de protocolos de cámara.

Este módulo contiene implementaciones especializadas para diferentes protocolos
de comunicación con cámaras IP, migrando funcionalidad desde src_old/connections/
hacia la nueva arquitectura MVP.

Handlers disponibles:
- BaseHandler: Clase base abstracta para todos los handlers
- ONVIFHandler: Manejo de protocolo ONVIF
- RTSPHandler: Manejo de protocolo RTSP (incluye TP-Link/Steren)
- AmcrestHandler: Manejo de protocolo HTTP/CGI + PTZ para Amcrest/Dahua
"""

# Importar handlers solo cuando estén disponibles
# Esto permite ejecución gradual durante la migración

try:
    from .base_handler import BaseHandler
    BASE_HANDLER_AVAILABLE = True
except ImportError:
    BASE_HANDLER_AVAILABLE = False

try:
    from .onvif_handler import ONVIFHandler
    ONVIF_HANDLER_AVAILABLE = True
except ImportError:
    ONVIF_HANDLER_AVAILABLE = False

try:
    from .rtsp_handler import RTSPHandler
    RTSP_HANDLER_AVAILABLE = True
except ImportError:
    RTSP_HANDLER_AVAILABLE = False

try:
    from .amcrest_handler import AmcrestHandler
    AMCREST_HANDLER_AVAILABLE = True
except ImportError:
    AMCREST_HANDLER_AVAILABLE = False

# Configurar __all__ dinámicamente
__all__ = []

if BASE_HANDLER_AVAILABLE:
    __all__.append('BaseHandler')

if ONVIF_HANDLER_AVAILABLE:
    __all__.append('ONVIFHandler')

if RTSP_HANDLER_AVAILABLE:
    __all__.append('RTSPHandler')

if AMCREST_HANDLER_AVAILABLE:
    __all__.append('AmcrestHandler')

# Version info
__version__ = '1.0.0'
__author__ = 'Universal Camera Viewer Team' 