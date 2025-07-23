"""
Módulo de dependencias para FastAPI.

Contiene dependencias comunes usadas en los endpoints.
"""

# Importar desde el archivo dependencies.py del módulo api
from ..dependencies import (
    cleanup_services,
    create_response,
    get_current_user
)

# También re-exportar las dependencias de rate limiting
from .rate_limit import (
    rate_limit,
    scan_operation_limit,
    connection_operation_limit,
    critical_operation_limit,
    ws_connection_limit
)

__all__ = [
    "cleanup_services",
    "create_response", 
    "get_current_user",
    "rate_limit",
    "scan_operation_limit",
    "connection_operation_limit",
    "critical_operation_limit",
    "ws_connection_limit"
]