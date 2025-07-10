"""
Módulo de conexiones para cámaras IP multi-marca.
Implementa diferentes protocolos de conexión para múltiples fabricantes.
Soporta Dahua, TP-Link, Steren y otras marcas compatibles.
"""

from .base_connection import BaseConnection, ConnectionFactory
from .rtsp_connection import RTSPConnection
from .amcrest_connection import AmcrestConnection
from .onvif_connection import ONVIFConnection
from .tplink_connection import TPLinkConnection
from .steren_connection import SterenConnection
from .generic_connection import GenericConnection

__all__ = ["BaseConnection", "ConnectionFactory", "RTSPConnection", "AmcrestConnection", "ONVIFConnection", "TPLinkConnection", "SterenConnection", "GenericConnection"] 