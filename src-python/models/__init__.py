"""
Models Package - MVP Architecture
=================================

Modelos de dominio del sistema de cámaras multi-marca.
Contiene toda la lógica de negocio y estructuras de datos.

Models disponibles:
- CameraModel: Modelo principal de cámara con estado y configuración
- ConnectionModel: Gestión de conexiones individuales por protocolo  
- ScanModel: Escaneo y descubrimiento de cámaras en red
"""

from .camera_model import (
    CameraModel,
    ConnectionStatus,
    ProtocolType,
    ConnectionConfig,
    StreamConfig,
    CameraCapabilities,
    ConnectionStats
)

from .connection_model import (
    ConnectionModel,
    ConnectionType,
    ConnectionAttempt,
    ConnectionHealth
)

from .scan_model import (
    ScanModel,
    ScanStatus,
    ScanMethod,
    ScanRange,
    ScanConfig,
    ScanResult,
    ScanProgress,
    ProtocolDetectionResult
)

__all__ = [
    # Camera Model
    'CameraModel',
    'ConnectionStatus', 
    'ProtocolType',
    'ConnectionConfig',
    'StreamConfig',
    'CameraCapabilities',
    'ConnectionStats',
    
    # Connection Model
    'ConnectionModel',
    'ConnectionType',
    'ConnectionAttempt', 
    'ConnectionHealth',
    
    # Scan Model
    'ScanModel',
    'ScanStatus',
    'ScanMethod',
    'ScanRange',
    'ScanConfig',
    'ScanResult',
    'ScanProgress',
    'ProtocolDetectionResult'
] 