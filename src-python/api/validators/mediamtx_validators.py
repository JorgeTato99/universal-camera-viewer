"""
Validadores específicos para endpoints de MediaMTX.

Proporciona funciones de validación reutilizables para datos
relacionados con publicación, métricas, viewers y paths.
"""

import re
from typing import Optional, List, Any
from datetime import datetime, timedelta
from ipaddress import ip_address, IPv4Address, IPv6Address

from utils.exceptions import ValidationError


def validate_session_id(value: str) -> str:
    """
    Valida un ID de sesión de publicación.
    
    Args:
        value: ID de sesión a validar
        
    Returns:
        ID de sesión validado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not value or not isinstance(value, str):
        raise ValidationError("session_id no puede estar vacío")
    
    # Formato esperado: UUID o timestamp-based ID
    if len(value) < 8:
        raise ValidationError("session_id demasiado corto")
    
    # Validar caracteres permitidos (alfanuméricos, guiones, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError("session_id contiene caracteres inválidos")
    
    return value.strip()


def validate_publish_path(value: str) -> str:
    """
    Valida un path de publicación MediaMTX.
    
    Args:
        value: Path a validar
        
    Returns:
        Path validado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not value or not isinstance(value, str):
        raise ValidationError("publish_path no puede estar vacío")
    
    # Remover espacios
    value = value.strip()
    
    # No debe empezar con /
    if value.startswith('/'):
        value = value[1:]
    
    # Validar formato: solo alfanuméricos, guiones, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError(
            "publish_path solo puede contener letras, números, guiones y underscores"
        )
    
    # Longitud
    if len(value) < 3:
        raise ValidationError("publish_path debe tener al menos 3 caracteres")
    if len(value) > 100:
        raise ValidationError("publish_path no puede exceder 100 caracteres")
    
    return value


def validate_metric_time_range(start: datetime, end: datetime) -> tuple:
    """
    Valida un rango de tiempo para consultas de métricas.
    
    Args:
        start: Tiempo de inicio
        end: Tiempo de fin
        
    Returns:
        Tupla (start, end) validada
        
    Raises:
        ValidationError: Si el rango es inválido
    """
    if start >= end:
        raise ValidationError("start_time debe ser anterior a end_time")
    
    # Validar que no sea un rango demasiado amplio (máx 90 días)
    max_range = timedelta(days=90)
    if end - start > max_range:
        raise ValidationError("El rango de tiempo no puede exceder 90 días")
    
    # No permitir fechas futuras
    now = datetime.utcnow()
    if start > now:
        raise ValidationError("start_time no puede ser en el futuro")
    if end > now:
        # Ajustar end al momento actual
        end = now
    
    return start, end


def validate_bitrate(value: Optional[float]) -> Optional[float]:
    """
    Valida un valor de bitrate en kbps.
    
    Args:
        value: Bitrate a validar
        
    Returns:
        Bitrate validado o None
        
    Raises:
        ValidationError: Si el valor es inválido
    """
    if value is None:
        return None
    
    try:
        bitrate = float(value)
    except (TypeError, ValueError):
        raise ValidationError("bitrate_kbps debe ser un número")
    
    # Validar rango razonable (0.1 - 50000 kbps)
    if bitrate < 0.1:
        raise ValidationError("bitrate_kbps debe ser mayor a 0.1")
    if bitrate > 50000:
        raise ValidationError("bitrate_kbps no puede exceder 50000 (50 Mbps)")
    
    return bitrate


def validate_fps(value: Optional[float]) -> Optional[float]:
    """
    Valida un valor de FPS (frames por segundo).
    
    Args:
        value: FPS a validar
        
    Returns:
        FPS validado o None
        
    Raises:
        ValidationError: Si el valor es inválido
    """
    if value is None:
        return None
    
    try:
        fps = float(value)
    except (TypeError, ValueError):
        raise ValidationError("fps debe ser un número")
    
    # Validar rango razonable (0.1 - 120 fps)
    if fps < 0.1:
        raise ValidationError("fps debe ser mayor a 0.1")
    if fps > 120:
        raise ValidationError("fps no puede exceder 120")
    
    return fps


def validate_quality_score(value: Optional[float]) -> Optional[float]:
    """
    Valida un score de calidad (0-100).
    
    Args:
        value: Score a validar
        
    Returns:
        Score validado o None
        
    Raises:
        ValidationError: Si el valor es inválido
    """
    if value is None:
        return None
    
    try:
        score = float(value)
    except (TypeError, ValueError):
        raise ValidationError("quality_score debe ser un número")
    
    if score < 0 or score > 100:
        raise ValidationError("quality_score debe estar entre 0 y 100")
    
    return score


def validate_viewer_ip(value: str) -> str:
    """
    Valida una dirección IP de viewer.
    
    Args:
        value: IP a validar
        
    Returns:
        IP validada
        
    Raises:
        ValidationError: Si la IP es inválida
    """
    if not value or not isinstance(value, str):
        raise ValidationError("viewer_ip no puede estar vacía")
    
    try:
        # Validar formato IP
        ip = ip_address(value.strip())
        
        # Opcionalmente, rechazar IPs privadas o especiales
        # if ip.is_private:
        #     raise ValidationError("No se permiten IPs privadas")
        
        return str(ip)
    except ValueError:
        raise ValidationError(f"'{value}' no es una dirección IP válida")


def validate_user_agent(value: Optional[str]) -> Optional[str]:
    """
    Valida y sanitiza un user agent.
    
    Args:
        value: User agent a validar
        
    Returns:
        User agent validado o None
        
    Raises:
        ValidationError: Si el valor es demasiado largo
    """
    if not value:
        return None
    
    if not isinstance(value, str):
        raise ValidationError("user_agent debe ser una cadena de texto")
    
    # Truncar si es muy largo
    max_length = 500
    if len(value) > max_length:
        return value[:max_length]
    
    return value.strip()


def validate_mediamtx_url(value: str) -> str:
    """
    Valida una URL de servidor MediaMTX.
    
    Args:
        value: URL a validar
        
    Returns:
        URL validada
        
    Raises:
        ValidationError: Si la URL es inválida
    """
    if not value or not isinstance(value, str):
        raise ValidationError("mediamtx_url no puede estar vacía")
    
    value = value.strip()
    
    # Debe ser rtsp:// o rtmp://
    if not value.startswith(('rtsp://', 'rtmp://')):
        raise ValidationError("mediamtx_url debe comenzar con rtsp:// o rtmp://")
    
    # Validar formato básico de URL
    url_pattern = re.compile(
        r'^(rtsp|rtmp)://'  # protocolo
        r'([a-zA-Z0-9.-]+)'  # host
        r'(:(\d+))?'         # puerto opcional
        r'(/.*)?$'           # path opcional
    )
    
    if not url_pattern.match(value):
        raise ValidationError("mediamtx_url tiene formato inválido")
    
    return value


def validate_path_name(value: str) -> str:
    """
    Valida un nombre de path MediaMTX.
    
    Args:
        value: Nombre del path
        
    Returns:
        Nombre validado
        
    Raises:
        ValidationError: Si el nombre es inválido
    """
    if not value or not isinstance(value, str):
        raise ValidationError("path_name no puede estar vacío")
    
    value = value.strip()
    
    # Solo alfanuméricos, guiones y underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError(
            "path_name solo puede contener letras, números, guiones y underscores"
        )
    
    # Longitud
    if len(value) < 1:
        raise ValidationError("path_name debe tener al menos 1 caracter")
    if len(value) > 100:
        raise ValidationError("path_name no puede exceder 100 caracteres")
    
    # No debe empezar con números
    if value[0].isdigit():
        raise ValidationError("path_name no puede empezar con números")
    
    return value


def validate_ffmpeg_command(value: Optional[str]) -> Optional[str]:
    """
    Valida y sanitiza un comando FFmpeg.
    
    Args:
        value: Comando a validar
        
    Returns:
        Comando validado o None
        
    Raises:
        ValidationError: Si contiene elementos peligrosos
    """
    if not value:
        return None
    
    if not isinstance(value, str):
        raise ValidationError("ffmpeg_command debe ser una cadena de texto")
    
    # Verificar que empiece con ffmpeg
    if not value.strip().startswith('ffmpeg'):
        raise ValidationError("El comando debe empezar con 'ffmpeg'")
    
    # Detectar intentos de inyección de comandos
    dangerous_patterns = [
        ';', '&&', '||', '|', '`', '$(',  # Command chaining/substitution
        '>', '<', '>>', '2>',              # Redirection
        'rm ', 'del ', 'format',           # Destructive commands
        '../', '..\\',                     # Path traversal
    ]
    
    command_lower = value.lower()
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            raise ValidationError(f"Comando contiene patrón peligroso: {pattern}")
    
    # Limitar longitud
    if len(value) > 2000:
        raise ValidationError("ffmpeg_command es demasiado largo (máx 2000 caracteres)")
    
    return value.strip()


def validate_export_format(value: str) -> str:
    """
    Valida un formato de exportación.
    
    Args:
        value: Formato solicitado
        
    Returns:
        Formato validado
        
    Raises:
        ValidationError: Si el formato no es soportado
    """
    if not value or not isinstance(value, str):
        raise ValidationError("format no puede estar vacío")
    
    value = value.strip().lower()
    
    allowed_formats = ['csv', 'json', 'excel', 'xlsx']
    if value not in allowed_formats:
        raise ValidationError(
            f"Formato '{value}' no soportado. Use: {', '.join(allowed_formats)}"
        )
    
    # Normalizar excel/xlsx
    if value == 'xlsx':
        value = 'excel'
    
    return value


def validate_page_params(page: int, page_size: int) -> tuple:
    """
    Valida parámetros de paginación.
    
    Args:
        page: Número de página
        page_size: Tamaño de página
        
    Returns:
        Tupla (page, page_size) validada
        
    Raises:
        ValidationError: Si los valores son inválidos
    """
    # Validar page
    if page < 1:
        raise ValidationError("page debe ser mayor o igual a 1")
    if page > 10000:
        raise ValidationError("page no puede exceder 10000")
    
    # Validar page_size
    if page_size < 1:
        raise ValidationError("page_size debe ser mayor o igual a 1")
    if page_size > 200:
        raise ValidationError("page_size no puede exceder 200")
    
    return page, page_size


def validate_allowed_ips(ips: Optional[List[str]]) -> Optional[List[str]]:
    """
    Valida una lista de IPs permitidas.
    
    Args:
        ips: Lista de direcciones IP
        
    Returns:
        Lista validada o None
        
    Raises:
        ValidationError: Si alguna IP es inválida
    """
    if not ips:
        return None
    
    if not isinstance(ips, list):
        raise ValidationError("allowed_ips debe ser una lista")
    
    validated_ips = []
    for ip_str in ips:
        if not isinstance(ip_str, str):
            raise ValidationError("Cada IP debe ser una cadena de texto")
        
        try:
            # Validar formato IP o CIDR
            if '/' in ip_str:
                # Es una red CIDR
                parts = ip_str.split('/')
                if len(parts) != 2:
                    raise ValueError("Formato CIDR inválido")
                ip_address(parts[0])  # Validar parte IP
                prefix = int(parts[1])  # Validar prefijo
                if prefix < 0 or prefix > 128:
                    raise ValueError("Prefijo CIDR inválido")
            else:
                # Es una IP individual
                ip_address(ip_str)
            
            validated_ips.append(ip_str.strip())
        except ValueError:
            raise ValidationError(f"'{ip_str}' no es una IP o CIDR válido")
    
    return validated_ips


def validate_server_id(value: Any) -> int:
    """
    Valida un ID de servidor MediaMTX.
    
    Args:
        value: ID a validar
        
    Returns:
        ID validado
        
    Raises:
        ValidationError: Si el ID es inválido
    """
    try:
        server_id = int(value)
    except (TypeError, ValueError):
        raise ValidationError("server_id debe ser un número entero")
    
    if server_id < 1:
        raise ValidationError("server_id debe ser mayor a 0")
    
    return server_id


def validate_health_status(value: str) -> str:
    """
    Valida un estado de salud.
    
    Args:
        value: Estado a validar
        
    Returns:
        Estado validado
        
    Raises:
        ValidationError: Si el estado es inválido
    """
    if not value or not isinstance(value, str):
        raise ValidationError("health_status no puede estar vacío")
    
    value = value.strip().lower()
    
    allowed_statuses = ['healthy', 'unhealthy', 'degraded', 'unknown']
    if value not in allowed_statuses:
        raise ValidationError(
            f"health_status '{value}' inválido. Use: {', '.join(allowed_statuses)}"
        )
    
    return value