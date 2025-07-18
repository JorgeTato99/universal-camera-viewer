"""
Validadores específicos para cámaras.
"""

from typing import List, Optional
import re


# Marcas de cámaras soportadas
SUPPORTED_BRANDS = [
    "Dahua", "Hikvision", "TP-Link", "Steren", "Amcrest",
    "Foscam", "Axis", "Bosch", "Panasonic", "Sony",
    "Samsung", "Honeywell", "Avigilon", "Milestone",
    "Generic", "Unknown"
]

# Tipos de stream soportados
SUPPORTED_STREAM_TYPES = ["main", "sub", "third", "mjpeg", "snapshot"]

# Protocolos soportados
SUPPORTED_PROTOCOLS = ["ONVIF", "RTSP", "HTTP", "HTTPS", "CGI", "MJPEG"]


def validate_camera_brand(v: str, allow_unknown: bool = True) -> str:
    """
    Valida la marca de una cámara.
    
    Args:
        v: Marca a validar
        allow_unknown: Si permitir marcas desconocidas
        
    Returns:
        Marca validada
        
    Raises:
        ValueError: Si la marca no es válida
    """
    if not v:
        if allow_unknown:
            return "Unknown"
        raise ValueError("La marca de la cámara es obligatoria")
    
    v = v.strip()
    
    # Normalizar capitalización
    v_lower = v.lower()
    for brand in SUPPORTED_BRANDS:
        if brand.lower() == v_lower:
            return brand
    
    if not allow_unknown:
        raise ValueError(
            f"Marca '{v}' no soportada. Marcas válidas: {', '.join(SUPPORTED_BRANDS)}"
        )
    
    # Si es desconocida pero permitida, capitalizar primera letra
    return v.capitalize()


def validate_camera_model(v: Optional[str], max_length: int = 64) -> Optional[str]:
    """
    Valida el modelo de una cámara.
    
    Args:
        v: Modelo a validar
        max_length: Longitud máxima
        
    Returns:
        Modelo validado o None
        
    Raises:
        ValueError: Si el modelo no es válido
    """
    if not v:
        return None
    
    v = v.strip()
    
    if not v:
        return None
    
    if len(v) > max_length:
        raise ValueError(f"El modelo no puede exceder {max_length} caracteres")
    
    # Validar caracteres permitidos (alfanuméricos, espacios, guiones, puntos)
    if not re.match(r'^[a-zA-Z0-9\s\-._()]+$', v):
        raise ValueError(
            "El modelo solo puede contener letras, números, espacios, '-', '_', '.', '(', ')'"
        )
    
    return v


def validate_stream_type(v: str) -> str:
    """
    Valida el tipo de stream.
    
    Args:
        v: Tipo de stream a validar
        
    Returns:
        Tipo de stream validado
        
    Raises:
        ValueError: Si el tipo no es válido
    """
    if not v:
        raise ValueError("El tipo de stream es obligatorio")
    
    v = v.lower().strip()
    
    if v not in SUPPORTED_STREAM_TYPES:
        raise ValueError(
            f"Tipo de stream '{v}' no válido. Tipos soportados: {', '.join(SUPPORTED_STREAM_TYPES)}"
        )
    
    return v


def validate_protocol_type(v: str) -> str:
    """
    Valida el tipo de protocolo.
    
    Args:
        v: Protocolo a validar
        
    Returns:
        Protocolo validado
        
    Raises:
        ValueError: Si el protocolo no es válido
    """
    if not v:
        raise ValueError("El protocolo es obligatorio")
    
    v = v.upper().strip()
    
    if v not in SUPPORTED_PROTOCOLS:
        raise ValueError(
            f"Protocolo '{v}' no válido. Protocolos soportados: {', '.join(SUPPORTED_PROTOCOLS)}"
        )
    
    return v


def validate_resolution(v: str) -> str:
    """
    Valida un string de resolución (ej: "1920x1080").
    
    Args:
        v: Resolución a validar
        
    Returns:
        Resolución validada
        
    Raises:
        ValueError: Si la resolución no es válida
    """
    if not v:
        return "Unknown"
    
    # Patrón para resolución: WIDTHxHEIGHT
    pattern = r'^\d{3,4}x\d{3,4}$'
    
    if not re.match(pattern, v):
        raise ValueError(
            "La resolución debe tener el formato WIDTHxHEIGHT (ej: 1920x1080)"
        )
    
    # Validar valores razonables
    width, height = map(int, v.split('x'))
    
    if width < 320 or width > 7680:
        raise ValueError("El ancho debe estar entre 320 y 7680 píxeles")
    if height < 240 or height > 4320:
        raise ValueError("La altura debe estar entre 240 y 4320 píxeles")
    
    return v


def validate_fps(v: int) -> int:
    """
    Valida los frames por segundo.
    
    Args:
        v: FPS a validar
        
    Returns:
        FPS validado
        
    Raises:
        ValueError: Si los FPS no son válidos
    """
    if not isinstance(v, int):
        raise ValueError("Los FPS deben ser un número entero")
    
    if v < 1 or v > 120:
        raise ValueError("Los FPS deben estar entre 1 y 120")
    
    return v


def validate_quality(v: str) -> str:
    """
    Valida el nivel de calidad de video.
    
    Args:
        v: Calidad a validar
        
    Returns:
        Calidad validada
        
    Raises:
        ValueError: Si la calidad no es válida
    """
    valid_qualities = ["low", "medium", "high", "ultra"]
    
    if not v:
        return "medium"
    
    v = v.lower().strip()
    
    if v not in valid_qualities:
        raise ValueError(
            f"Calidad '{v}' no válida. Valores permitidos: {', '.join(valid_qualities)}"
        )
    
    return v


def validate_codec(v: str) -> str:
    """
    Valida el codec de video.
    
    Args:
        v: Codec a validar
        
    Returns:
        Codec validado
        
    Raises:
        ValueError: Si el codec no es válido
    """
    valid_codecs = ["h264", "h265", "hevc", "mjpeg", "mpeg4"]
    
    if not v:
        return "h264"
    
    v = v.lower().strip()
    
    # h265 y hevc son lo mismo
    if v == "hevc":
        v = "h265"
    
    if v not in valid_codecs:
        raise ValueError(
            f"Codec '{v}' no válido. Codecs soportados: {', '.join(valid_codecs)}"
        )
    
    return v