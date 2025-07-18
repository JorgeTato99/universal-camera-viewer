"""
Validadores personalizados para FastAPI.

Este módulo contiene validadores reutilizables para la validación
de datos en toda la aplicación.
"""

from .common_validators import (
    validate_uuid,
    validate_ip_address,
    validate_port,
    validate_username,
    validate_password,
    validate_camera_name,
    validate_timeout,
    validate_location,
    validate_config_key
)

from .camera_validators import (
    validate_camera_brand,
    validate_camera_model,
    validate_stream_type,
    validate_protocol_type
)

from .connection_validators import (
    validate_connection_data,
    validate_rtsp_url,
    validate_stream_url
)

__all__ = [
    # Common validators
    "validate_uuid",
    "validate_ip_address", 
    "validate_port",
    "validate_username",
    "validate_password",
    "validate_camera_name",
    "validate_timeout",
    "validate_location",
    "validate_config_key",
    
    # Camera validators
    "validate_camera_brand",
    "validate_camera_model",
    "validate_stream_type",
    "validate_protocol_type",
    
    # Connection validators
    "validate_connection_data",
    "validate_rtsp_url",
    "validate_stream_url"
]