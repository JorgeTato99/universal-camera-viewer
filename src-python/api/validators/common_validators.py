"""
Validadores comunes para toda la aplicación.

Estos validadores se usan en múltiples modelos y endpoints
para garantizar consistencia en la validación de datos.
"""

import re
import ipaddress
from typing import Optional, Any
from pydantic import validator
import uuid as uuid_lib


def validate_uuid(v: str, field_name: str = "ID") -> str:
    """
    Valida que un string sea un UUID válido.
    
    Args:
        v: Valor a validar
        field_name: Nombre del campo para mensajes de error
        
    Returns:
        UUID validado como string
        
    Raises:
        ValueError: Si el UUID no es válido
    """
    if not v:
        raise ValueError(f"{field_name} no puede estar vacío")
    
    # Verificar longitud básica
    if len(v) != 36:
        raise ValueError(f"{field_name} debe tener 36 caracteres (formato UUID)")
    
    try:
        # Intentar parsear como UUID
        uuid_obj = uuid_lib.UUID(v)
        return str(uuid_obj)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} debe ser un UUID válido")


def validate_ip_address(v: str) -> str:
    """
    Valida que un string sea una dirección IP válida.
    
    Args:
        v: Dirección IP a validar
        
    Returns:
        IP validada
        
    Raises:
        ValueError: Si la IP no es válida
    """
    if not v:
        raise ValueError("La dirección IP no puede estar vacía")
    
    try:
        # Validar IP
        ip = ipaddress.ip_address(v)
        
        # No permitir IPs especiales
        if ip.is_loopback:
            raise ValueError("No se permiten direcciones loopback (127.0.0.1)")
        if ip.is_multicast:
            raise ValueError("No se permiten direcciones multicast")
        if ip.is_reserved:
            raise ValueError("No se permiten direcciones IP reservadas")
        if str(ip) == "0.0.0.0":
            raise ValueError("0.0.0.0 no es una dirección IP válida")
            
        return str(ip)
    except ipaddress.AddressValueError:
        raise ValueError(f"'{v}' no es una dirección IP válida")


def validate_port(v: int, min_port: int = 1, max_port: int = 65535) -> int:
    """
    Valida que un número de puerto sea válido.
    
    Args:
        v: Puerto a validar
        min_port: Puerto mínimo permitido
        max_port: Puerto máximo permitido
        
    Returns:
        Puerto validado
        
    Raises:
        ValueError: Si el puerto no es válido
    """
    if not isinstance(v, int):
        raise ValueError("El puerto debe ser un número entero")
    
    if v < min_port or v > max_port:
        raise ValueError(f"El puerto debe estar entre {min_port} y {max_port}")
    
    # Advertir sobre puertos bien conocidos
    if v < 1024:
        # Esto es solo una advertencia, no un error
        pass
    
    return v


def validate_username(v: str, min_length: int = 1, max_length: int = 64) -> str:
    """
    Valida un nombre de usuario.
    
    Args:
        v: Nombre de usuario a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
        
    Returns:
        Username validado
        
    Raises:
        ValueError: Si el username no es válido
    """
    if not v:
        raise ValueError("El nombre de usuario no puede estar vacío")
    
    # Eliminar espacios al inicio y final
    v = v.strip()
    
    if len(v) < min_length:
        raise ValueError(f"El nombre de usuario debe tener al menos {min_length} caracteres")
    if len(v) > max_length:
        raise ValueError(f"El nombre de usuario no puede exceder {max_length} caracteres")
    
    # No permitir espacios en el username
    if ' ' in v:
        raise ValueError("El nombre de usuario no puede contener espacios")
    
    # Validar caracteres permitidos (alfanuméricos, _, -, @, .)
    if not re.match(r'^[a-zA-Z0-9._@-]+$', v):
        raise ValueError("El nombre de usuario solo puede contener letras, números, '.', '_', '@' y '-'")
    
    return v


def validate_password(v: str, min_length: int = 4, max_length: int = 128) -> str:
    """
    Valida una contraseña.
    
    Args:
        v: Contraseña a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
        
    Returns:
        Contraseña validada
        
    Raises:
        ValueError: Si la contraseña no es válida
    """
    if not v:
        raise ValueError("La contraseña no puede estar vacía")
    
    # NO hacer strip() en contraseñas - los espacios pueden ser intencionales
    
    if len(v) < min_length:
        raise ValueError(f"La contraseña debe tener al menos {min_length} caracteres")
    if len(v) > max_length:
        raise ValueError(f"La contraseña no puede exceder {max_length} caracteres")
    
    # Advertencia: contraseñas débiles (solo para logging, no error)
    if v.lower() in ['admin', 'password', '1234', '12345', '123456', 'admin123']:
        # Esto debería ser un warning en el log, no un error
        pass
    
    return v


def validate_camera_name(v: str, max_length: int = 128) -> str:
    """
    Valida el nombre/display name de una cámara.
    
    Args:
        v: Nombre a validar
        max_length: Longitud máxima
        
    Returns:
        Nombre validado
        
    Raises:
        ValueError: Si el nombre no es válido
    """
    if not v:
        raise ValueError("El nombre de la cámara no puede estar vacío")
    
    v = v.strip()
    
    if not v:
        raise ValueError("El nombre de la cámara no puede contener solo espacios")
    
    if len(v) > max_length:
        raise ValueError(f"El nombre de la cámara no puede exceder {max_length} caracteres")
    
    # Validar caracteres no permitidos (evitar inyección)
    forbidden_chars = ['<', '>', '"', "'", '\\', '/', '\0', '\n', '\r', '\t']
    for char in forbidden_chars:
        if char in v:
            raise ValueError(f"El nombre de la cámara contiene caracteres no permitidos: {char}")
    
    return v


def validate_timeout(v: float, min_timeout: float = 0.1, max_timeout: float = 300.0) -> float:
    """
    Valida un valor de timeout.
    
    Args:
        v: Timeout a validar
        min_timeout: Timeout mínimo en segundos
        max_timeout: Timeout máximo en segundos
        
    Returns:
        Timeout validado
        
    Raises:
        ValueError: Si el timeout no es válido
    """
    if not isinstance(v, (int, float)):
        raise ValueError("El timeout debe ser un número")
    
    v = float(v)
    
    if v <= 0:
        raise ValueError("El timeout debe ser mayor que 0")
    
    if v < min_timeout:
        raise ValueError(f"El timeout mínimo es {min_timeout} segundos")
    if v > max_timeout:
        raise ValueError(f"El timeout máximo es {max_timeout} segundos")
    
    return v


# Funciones auxiliares para usar con Pydantic @validator

def uuid_validator(field_name: str = "ID"):
    """
    Crea un validador de UUID para usar con Pydantic.
    
    Args:
        field_name: Nombre del campo para mensajes de error
        
    Returns:
        Función validadora para Pydantic
    """
    def validate(cls, v):
        if v is None:
            return v
        return validate_uuid(v, field_name)
    return validate


def ip_validator():
    """Crea un validador de IP para usar con Pydantic."""
    def validate(cls, v):
        if v is None:
            return v
        return validate_ip_address(v)
    return validate


def port_validator(min_port: int = 1, max_port: int = 65535):
    """Crea un validador de puerto para usar con Pydantic."""
    def validate(cls, v):
        if v is None:
            return v
        return validate_port(v, min_port, max_port)
    return validate


def validate_location(v: Optional[str]) -> Optional[str]:
    """
    Valida ubicación/localización de cámara.
    
    Args:
        v: Ubicación a validar
        
    Returns:
        Ubicación validada o None
        
    Raises:
        ValueError: Si la ubicación es inválida
    """
    if v is None:
        return None
    
    v = v.strip()
    if not v:
        return None
    
    if len(v) > 100:
        raise ValueError("La ubicación no puede exceder 100 caracteres")
    
    # Caracteres permitidos: letras, números, espacios, guiones, paréntesis
    if not re.match(r'^[\w\s\-\(\),\.]+$', v, re.UNICODE):
        raise ValueError("La ubicación contiene caracteres no permitidos")
    
    return v


def validate_config_key(v: str) -> str:
    """
    Valida clave de configuración.
    
    Args:
        v: Clave a validar
        
    Returns:
        Clave validada
        
    Raises:
        ValueError: Si la clave es inválida
    """
    if not v:
        raise ValueError("La clave de configuración no puede estar vacía")
    
    # Solo permitir alfanuméricos y guiones bajos
    if not v.replace('_', '').isalnum():
        raise ValueError("La clave debe contener solo letras, números y guiones bajos")
    
    if len(v) > 50:
        raise ValueError("La clave no puede exceder 50 caracteres")
    
    return v