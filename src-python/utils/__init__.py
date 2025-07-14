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
- exceptions.py: Excepciones personalizadas del dominio
- error_handlers.py: Decoradores y utilidades para manejo de errores
- constants.py: Constantes centralizadas de la aplicación

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

# Excepciones del dominio
from .exceptions import (
    # Base
    CameraViewerError,
    # Conexión
    ConnectionError,
    CameraConnectionError,
    ConnectionTimeoutError,
    # Escaneo
    ScanError,
    NetworkScanTimeoutError,
    InvalidNetworkRangeError,
    # Configuración
    ConfigurationError,
    MissingConfigurationError,
    InvalidConfigurationError,
    # Validación
    ValidationError,
    InvalidIPAddressError,
    InvalidPortError,
    MissingRequiredFieldError,
    # Protocolos
    ProtocolError,
    ONVIFError,
    ONVIFAuthenticationError,
    ONVIFServiceError,
    RTSPError,
    RTSPConnectionError,
    RTSPAuthenticationError,
    # Streaming
    StreamingError,
    StreamNotAvailableError,
    StreamDecodingError,
    # Persistencia
    PersistenceError,
    DatabaseError,
    FileAccessError,
    # Utilidades
    format_error_for_user,
    is_retryable_error,
)

# Manejo de errores
from .error_handlers import (
    handle_service_errors,
    handle_presenter_errors,
    retry_with_backoff,
    CircuitBreaker,
)

# Constantes
from .constants import (
    DefaultPorts,
    DefaultCredentials,
    RTSPPaths,
    Timeouts,
    SystemLimits,
    NetworkConfig,
    StreamingConfig,
    SupportedBrands,
    ErrorMessages,
    ValidationPatterns,
    UIConfig,
    LoggingConfig,
)

__all__ = [
    # Excepciones
    'CameraViewerError',
    'ConnectionError',
    'CameraConnectionError',
    'ConnectionTimeoutError',
    'ScanError',
    'NetworkScanTimeoutError',
    'InvalidNetworkRangeError',
    'ConfigurationError',
    'MissingConfigurationError',
    'InvalidConfigurationError',
    'ValidationError',
    'InvalidIPAddressError',
    'InvalidPortError',
    'MissingRequiredFieldError',
    'ProtocolError',
    'ONVIFError',
    'ONVIFAuthenticationError',
    'ONVIFServiceError',
    'RTSPError',
    'RTSPConnectionError',
    'RTSPAuthenticationError',
    'StreamingError',
    'StreamNotAvailableError',
    'StreamDecodingError',
    'PersistenceError',
    'DatabaseError',
    'FileAccessError',
    'format_error_for_user',
    'is_retryable_error',
    # Error handlers
    'handle_service_errors',
    'handle_presenter_errors',
    'retry_with_backoff',
    'CircuitBreaker',
    # Constants
    'DefaultPorts',
    'DefaultCredentials',
    'RTSPPaths',
    'Timeouts',
    'SystemLimits',
    'NetworkConfig',
    'StreamingConfig',
    'SupportedBrands',
    'ErrorMessages',
    'ValidationPatterns',
    'UIConfig',
    'LoggingConfig',
] 