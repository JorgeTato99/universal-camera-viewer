"""
Visor Universal de Cámaras Multi-Marca - Arquitectura MVP
=======================================================

Aplicación desktop multiplataforma para visualización de cámaras IP de múltiples marcas
utilizando arquitectura Model-View-Presenter (MVP) con Flet como frontend.

Arquitectura:
- Models: Lógica de negocio y modelos de datos
- Views: Componentes UI en Flet
- Presenters: Lógica de presentación y gestión de estado
- Services: Servicios de datos e infraestructura
- Utils: Utilidades y helpers

Marcas soportadas: Dahua, TP-Link, Steren, Generic
Protocolos: ONVIF, RTSP, HTTP/CGI
"""

__version__ = "2.0.0"
__author__ = "AI Agent"
__description__ = "Universal Multi-Brand Camera Viewer - MVP Architecture"

# Imports principales para acceso rápido
from .models import *
from .services import *
from .utils import *

__all__ = [
    "__version__",
    "__author__", 
    "__description__"
] 