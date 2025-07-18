"""
Validadores para conexiones y URLs.
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from .common_validators import validate_ip_address, validate_port


def validate_rtsp_url(v: str) -> str:
    """
    Valida una URL RTSP.
    
    Args:
        v: URL RTSP a validar
        
    Returns:
        URL validada
        
    Raises:
        ValueError: Si la URL no es válida
    """
    if not v:
        raise ValueError("La URL RTSP no puede estar vacía")
    
    # Parsear la URL
    try:
        parsed = urlparse(v)
    except Exception:
        raise ValueError("URL RTSP mal formada")
    
    # Validar esquema
    if parsed.scheme not in ['rtsp', 'rtsps']:
        raise ValueError("La URL debe usar esquema rtsp:// o rtsps://")
    
    # Validar que tenga host
    if not parsed.hostname:
        raise ValueError("La URL RTSP debe incluir una dirección IP o hostname")
    
    # Validar puerto (si está presente)
    if parsed.port:
        validate_port(parsed.port)
    
    # Validar que no tenga caracteres peligrosos en la ruta
    if parsed.path:
        forbidden_chars = ['<', '>', '"', '{', '}', '|', '\\', '^', '`', ' ']
        for char in forbidden_chars:
            if char in parsed.path:
                raise ValueError(f"La URL contiene caracteres no permitidos: {char}")
    
    return v


def validate_stream_url(v: str) -> str:
    """
    Valida una URL de streaming (RTSP, HTTP, HTTPS).
    
    Args:
        v: URL a validar
        
    Returns:
        URL validada
        
    Raises:
        ValueError: Si la URL no es válida
    """
    if not v:
        raise ValueError("La URL de streaming no puede estar vacía")
    
    # Parsear la URL
    try:
        parsed = urlparse(v)
    except Exception:
        raise ValueError("URL de streaming mal formada")
    
    # Validar esquema
    valid_schemes = ['rtsp', 'rtsps', 'http', 'https', 'rtmp', 'rtmps']
    if parsed.scheme not in valid_schemes:
        raise ValueError(
            f"Esquema '{parsed.scheme}' no válido. "
            f"Esquemas soportados: {', '.join(valid_schemes)}"
        )
    
    # Validar host
    if not parsed.hostname:
        raise ValueError("La URL debe incluir una dirección IP o hostname")
    
    # Si es IP, validarla
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', parsed.hostname):
        validate_ip_address(parsed.hostname)
    
    # Validar puerto
    if parsed.port:
        validate_port(parsed.port)
    
    # Longitud máxima
    if len(v) > 2048:
        raise ValueError("La URL no puede exceder 2048 caracteres")
    
    return v


def validate_connection_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida los datos de conexión completos.
    
    Args:
        data: Diccionario con datos de conexión
        
    Returns:
        Datos validados
        
    Raises:
        ValueError: Si los datos no son válidos
    """
    if not data:
        raise ValueError("Los datos de conexión no pueden estar vacíos")
    
    # Validar IP (obligatoria)
    if 'ip' not in data:
        raise ValueError("La dirección IP es obligatoria")
    data['ip'] = validate_ip_address(data['ip'])
    
    # Validar puertos si están presentes
    port_fields = ['rtsp_port', 'onvif_port', 'http_port', 'https_port']
    for field in port_fields:
        if field in data and data[field] is not None:
            data[field] = validate_port(data[field])
    
    # Validar credenciales si están presentes
    if 'username' in data and data['username']:
        from .common_validators import validate_username
        data['username'] = validate_username(data['username'])
    
    if 'password' in data and data['password']:
        from .common_validators import validate_password
        data['password'] = validate_password(data['password'])
    
    # Validar marca si está presente
    if 'brand' in data and data['brand']:
        from .camera_validators import validate_camera_brand
        data['brand'] = validate_camera_brand(data['brand'])
    
    return data


def validate_network_path(v: str) -> str:
    """
    Valida una ruta de red (para snapshots, recordings, etc).
    
    Args:
        v: Ruta a validar
        
    Returns:
        Ruta validada
        
    Raises:
        ValueError: Si la ruta no es válida
    """
    if not v:
        raise ValueError("La ruta de red no puede estar vacía")
    
    v = v.strip()
    
    # No permitir rutas absolutas del sistema
    if v.startswith('/') or (len(v) > 1 and v[1] == ':'):
        raise ValueError("No se permiten rutas absolutas del sistema")
    
    # Validar caracteres
    forbidden_chars = ['..', '<', '>', '|', '\0', '\n', '\r']
    for char in forbidden_chars:
        if char in v:
            raise ValueError(f"La ruta contiene caracteres no permitidos: {char}")
    
    # Longitud máxima
    if len(v) > 255:
        raise ValueError("La ruta no puede exceder 255 caracteres")
    
    return v


def validate_onvif_scope(v: str) -> str:
    """
    Valida un scope ONVIF.
    
    Args:
        v: Scope a validar
        
    Returns:
        Scope validado
        
    Raises:
        ValueError: Si el scope no es válido
    """
    valid_scopes = [
        "onvif://www.onvif.org/Profile/S",
        "onvif://www.onvif.org/Profile/G",
        "onvif://www.onvif.org/Profile/T",
        "onvif://www.onvif.org/Profile/A",
        "onvif://www.onvif.org/Profile/C",
        "onvif://www.onvif.org/Profile/Q",
        "onvif://www.onvif.org/Profile/M"
    ]
    
    if not v:
        return ""
    
    v = v.strip()
    
    # Puede ser una lista de scopes separados por espacios
    scopes = v.split()
    
    for scope in scopes:
        if not scope.startswith("onvif://"):
            raise ValueError(f"Scope ONVIF inválido: {scope}")
    
    return v