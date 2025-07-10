"""
Services Layer - Capa de servicios del patrón MVP.

Contiene la lógica de negocio y orquestación de la aplicación:
- ConnectionService: Gestión de conexiones de cámaras
- ScanService: Servicios de escaneo y descubrimiento
- DataService: Persistencia y gestión de datos
- ConfigService: Gestión avanzada de configuración
- ProtocolService: Gestión de protocolos de cámara
"""

from .connection_service import ConnectionService, ConnectionServiceConfig, get_connection_service
from .scan_service import ScanService, ScanServiceConfig, get_scan_service
from .data_service import DataService, DataServiceConfig, get_data_service
from .config_service import ConfigService, ConfigServiceConfig, get_config_service
from .protocol_service import ProtocolService, get_protocol_service

__all__ = [
    # Connection Service
    "ConnectionService",
    "ConnectionServiceConfig", 
    "get_connection_service",
    
    # Scan Service
    "ScanService",
    "ScanServiceConfig",
    "get_scan_service",
    
    # Data Service
    "DataService",
    "DataServiceConfig",
    "get_data_service",
    
    # Config Service
    "ConfigService",
    "ConfigServiceConfig",
    "get_config_service",
    
    # Protocol Service
    "ProtocolService",
    "get_protocol_service",
] 