"""
Funciones de sanitización para proteger información sensible en logs y salidas.

Este módulo proporciona funciones para sanitizar:
- URLs con credenciales
- Comandos del sistema
- Direcciones IP
- Headers HTTP
- Configuraciones sensibles
"""
import re
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def sanitize_url(url: str, show_user: bool = False, mask_char: str = '*') -> str:
    """
    Sanitiza una URL removiendo o enmascarando credenciales.
    
    Args:
        url: URL a sanitizar
        show_user: Si mostrar el nombre de usuario (enmascarado parcialmente)
        mask_char: Carácter a usar para enmascarar
        
    Returns:
        URL sanitizada
        
    Ejemplos:
        rtsp://admin:pass123@192.168.1.1/stream -> rtsp://***:***@192.168.1.1/stream
        http://user:secret@api.com/path -> http://***:***@api.com/path
    """
    if not url:
        return url
        
    try:
        # Parsear URL
        parsed = urlparse(url)
        
        # Si no tiene credenciales, retornar como está
        if not parsed.username and not parsed.password:
            return url
            
        # Preparar credenciales sanitizadas
        if show_user and parsed.username:
            # Mostrar primeras 2 letras del usuario
            if len(parsed.username) > 2:
                sanitized_user = parsed.username[:2] + mask_char * (len(parsed.username) - 2)
            else:
                sanitized_user = mask_char * len(parsed.username)
        else:
            sanitized_user = mask_char * 3 if parsed.username else None
            
        sanitized_pass = mask_char * 3 if parsed.password else None
        
        # Reconstruir netloc
        if sanitized_user and sanitized_pass:
            netloc = f"{sanitized_user}:{sanitized_pass}@{parsed.hostname}"
        elif sanitized_user:
            netloc = f"{sanitized_user}@{parsed.hostname}"
        else:
            netloc = parsed.hostname
            
        # Agregar puerto si existe
        if parsed.port:
            netloc += f":{parsed.port}"
            
        # Reconstruir URL
        sanitized = urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return sanitized
        
    except Exception:
        # Si falla el parseo, aplicar regex como fallback
        return sanitize_url_regex(url, mask_char)


def sanitize_url_regex(url: str, mask_char: str = '*') -> str:
    """
    Sanitiza URL usando regex (fallback cuando urlparse falla).
    
    Args:
        url: URL a sanitizar
        mask_char: Carácter para enmascarar
        
    Returns:
        URL sanitizada
    """
    # Patrón para detectar credenciales en URLs
    # Formato: protocol://username:password@host
    pattern = r'((?:rtsp|http|https|ftp|sftp|ssh)://)[^:]+:[^@]+@'
    replacement = r'\1' + mask_char * 3 + ':' + mask_char * 3 + '@'
    
    return re.sub(pattern, replacement, url)


def sanitize_command(command: str, patterns: Optional[List[str]] = None) -> str:
    """
    Sanitiza un comando del sistema removiendo información sensible.
    
    Args:
        command: Comando a sanitizar
        patterns: Patrones adicionales a buscar y sanitizar
        
    Returns:
        Comando sanitizado
        
    Ejemplo:
        ffmpeg -i rtsp://admin:pass@cam/stream -> ffmpeg -i rtsp://***:***@cam/stream
    """
    if not command:
        return command
        
    # Sanitizar URLs en el comando
    # Buscar URLs comunes
    url_patterns = [
        r'(rtsp://[^\s]+)',
        r'(http[s]?://[^\s]+)',
        r'(ftp://[^\s]+)'
    ]
    
    sanitized = command
    for pattern in url_patterns:
        matches = re.findall(pattern, sanitized)
        for match in matches:
            sanitized_url = sanitize_url(match)
            sanitized = sanitized.replace(match, sanitized_url)
            
    # Sanitizar argumentos específicos de FFmpeg y otros comandos
    sensitive_args = [
        r'-headers\s+"[^"]*Authorization:[^"]*"',  # Headers de autorización
        r'-password\s+\S+',                         # Argumentos de password
        r'-user\s+\S+\s+-pass\s+\S+',              # Usuario y password
        r'--password[=\s]+\S+',                     # Formato alternativo
        r'--api-key[=\s]+\S+',                      # API keys
        r'--token[=\s]+\S+',                        # Tokens
    ]
    
    for arg_pattern in sensitive_args:
        sanitized = re.sub(arg_pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
    # Sanitizar patrones personalizados
    if patterns:
        for pattern in patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
            
    return sanitized


def sanitize_ip(ip: str, level: str = 'partial') -> str:
    """
    Sanitiza una dirección IP según el nivel especificado.
    
    Args:
        ip: Dirección IP a sanitizar
        level: Nivel de sanitización ('none', 'partial', 'full')
        
    Returns:
        IP sanitizada
        
    Ejemplos:
        192.168.1.100 + partial -> 192.168.1.xxx
        192.168.1.100 + full -> xxx.xxx.xxx.xxx
    """
    if not ip or level == 'none':
        return ip
        
    try:
        # Validar que sea una IP válida
        parts = ip.split('.')
        if len(parts) != 4:
            return ip
            
        if level == 'partial':
            # Ocultar último octeto
            return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
        elif level == 'full':
            # Ocultar toda la IP
            return "xxx.xxx.xxx.xxx"
        else:
            return ip
            
    except Exception:
        return ip


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitiza headers HTTP removiendo valores sensibles.
    
    Args:
        headers: Diccionario de headers
        
    Returns:
        Headers sanitizados
    """
    if not headers:
        return headers
        
    sensitive_headers = [
        'authorization',
        'x-api-key',
        'x-auth-token',
        'cookie',
        'set-cookie',
        'x-csrf-token',
        'x-forwarded-for',  # Puede contener IPs internas
        'x-real-ip',
        'proxy-authorization'
    ]
    
    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        
        if key_lower in sensitive_headers:
            # Mostrar solo tipo de autenticación si es Authorization
            if key_lower == 'authorization' and value:
                auth_type = value.split(' ')[0] if ' ' in value else 'Unknown'
                sanitized[key] = f"{auth_type} [REDACTED]"
            else:
                sanitized[key] = '[REDACTED]'
        else:
            sanitized[key] = value
            
    return sanitized


def sanitize_config(config: Dict[str, Any], 
                   sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Sanitiza un diccionario de configuración.
    
    Args:
        config: Configuración a sanitizar
        sensitive_keys: Llaves adicionales consideradas sensibles
        
    Returns:
        Configuración sanitizada
    """
    if not config:
        return config
        
    # Llaves sensibles por defecto
    default_sensitive = [
        'password', 'passwd', 'pwd', 'secret',
        'api_key', 'apikey', 'token', 'auth',
        'credential', 'private_key', 'privatekey',
        'access_key', 'accesskey', 'secret_key',
        'secretkey', 'passphrase', 'pin'
    ]
    
    # Combinar con llaves personalizadas
    all_sensitive = default_sensitive + (sensitive_keys or [])
    
    def _sanitize_value(key: str, value: Any) -> Any:
        """Sanitiza un valor según su llave."""
        key_lower = key.lower()
        
        # Verificar si la llave contiene palabras sensibles
        if any(sensitive in key_lower for sensitive in all_sensitive):
            if isinstance(value, str):
                return '[REDACTED]'
            elif isinstance(value, (int, float)):
                return 0
            elif isinstance(value, bool):
                return False
            elif isinstance(value, list):
                return ['[REDACTED]'] * len(value)
            elif isinstance(value, dict):
                return {k: '[REDACTED]' for k in value}
            else:
                return '[REDACTED]'
                
        # Si el valor es una URL, sanitizarla
        if isinstance(value, str) and any(proto in value for proto in ['://', 'rtsp:', 'http:']):
            return sanitize_url(value)
            
        # Si es un diccionario, recursión
        if isinstance(value, dict):
            return sanitize_config(value, sensitive_keys)
            
        # Si es una lista, verificar cada elemento
        if isinstance(value, list):
            return [_sanitize_value(key, item) for item in value]
            
        return value
        
    # Sanitizar configuración
    sanitized = {}
    for key, value in config.items():
        sanitized[key] = _sanitize_value(key, value)
        
    return sanitized


def sanitize_error_message(error: str) -> str:
    """
    Sanitiza un mensaje de error removiendo información sensible.
    
    Args:
        error: Mensaje de error
        
    Returns:
        Error sanitizado
    """
    if not error:
        return error
        
    # Patrones a buscar y reemplazar
    patterns = [
        # URLs con credenciales
        (r'(rtsp|http[s]?)://[^:]+:[^@]+@[^\s]+', r'\1://***:***@[URL]'),
        # Rutas de archivo que pueden contener nombres de usuario
        (r'[cC]:\\[Uu]sers\\[^\\]+\\', r'C:\\Users\\[USER]\\'),
        (r'/home/[^/]+/', r'/home/[USER]/'),
        # IPs internas
        (r'\b(?:192\.168|10\.0|172\.16)\.\d+\.\d+\b', r'[INTERNAL_IP]'),
        # Emails
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r'[EMAIL]'),
        # Números que parecen IDs o keys
        (r'\b[a-fA-F0-9]{32,}\b', r'[HASH]'),
        (r'\b[a-zA-Z0-9]{20,}\b', r'[KEY]')
    ]
    
    sanitized = error
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)
        
    return sanitized


def sanitize_log_message(message: str, context: Optional[str] = None) -> str:
    """
    Sanitiza un mensaje de log completo aplicando todas las sanitizaciones necesarias.
    
    Args:
        message: Mensaje a sanitizar
        context: Contexto del mensaje (comando, url, config, etc.)
        
    Returns:
        Mensaje sanitizado
    """
    if not message:
        return message
        
    # Aplicar sanitización según contexto
    if context == 'command':
        return sanitize_command(message)
    elif context == 'url':
        return sanitize_url(message)
    elif context == 'error':
        return sanitize_error_message(message)
    else:
        # Aplicar sanitización general
        # Buscar y sanitizar URLs
        url_pattern = r'((?:rtsp|http[s]?|ftp)://[^\s]+)'
        sanitized = message
        
        for match in re.findall(url_pattern, sanitized):
            sanitized = sanitized.replace(match, sanitize_url(match))
            
        # Buscar y sanitizar IPs sospechosas
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        for match in re.findall(ip_pattern, sanitized):
            # Solo sanitizar IPs privadas
            if match.startswith(('192.168.', '10.', '172.16.')):
                sanitized = sanitized.replace(match, sanitize_ip(match, 'partial'))
                
        return sanitized


# Funciones de utilidad para logging
def create_safe_log_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un contexto seguro para logging a partir de datos arbitrarios.
    
    Args:
        data: Datos a incluir en el log
        
    Returns:
        Datos sanitizados seguros para logging
    """
    return sanitize_config(data)