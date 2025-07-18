"""
Validador de URLs y configuraciones de streaming.

Proporciona validación y normalización de URLs RTSP.
"""

import re
from urllib.parse import urlparse, urlunparse
from typing import Optional, Tuple
import ipaddress


class StreamValidator:
    """
    Valida y normaliza URLs de streaming.
    
    Soporta validación de:
    - URLs RTSP/RTSPS
    - Direcciones IP
    - Puertos
    - Credenciales
    """
    
    @staticmethod
    def validate_rtsp_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Valida una URL RTSP.
        
        Args:
            url: URL a validar
            
        Returns:
            Tupla (es_valida, mensaje_error)
        """
        if not url:
            return False, "URL vacía"
            
        try:
            parsed = urlparse(url)
            
            # Verificar esquema
            if parsed.scheme not in ['rtsp', 'rtsps']:
                return False, f"Esquema inválido: {parsed.scheme}"
                
            # Verificar host
            if not parsed.hostname:
                return False, "Host no especificado"
                
            # Validar IP si es el caso
            try:
                ipaddress.ip_address(parsed.hostname)
            except ValueError:
                # No es IP, verificar que sea hostname válido
                if not re.match(r'^[a-zA-Z0-9.-]+$', parsed.hostname):
                    return False, f"Hostname inválido: {parsed.hostname}"
                    
            # Verificar puerto
            if parsed.port:
                if not 1 <= parsed.port <= 65535:
                    return False, f"Puerto inválido: {parsed.port}"
                    
            return True, None
            
        except Exception as e:
            return False, f"Error parseando URL: {str(e)}"
            
    @staticmethod
    def normalize_rtsp_url(url: str) -> str:
        """
        Normaliza una URL RTSP.
        
        - Agrega puerto por defecto si no existe
        - Limpia espacios
        - Normaliza path
        
        Args:
            url: URL a normalizar
            
        Returns:
            URL normalizada
        """
        url = url.strip()
        parsed = urlparse(url)
        
        # Puerto por defecto
        if not parsed.port:
            if parsed.scheme == 'rtsp':
                netloc = f"{parsed.hostname}:554"
            else:  # rtsps
                netloc = f"{parsed.hostname}:322"
                
            if parsed.username:
                netloc = f"{parsed.username}:{parsed.password}@{netloc}"
                
            parsed = parsed._replace(netloc=netloc)
            
        # Path por defecto
        if not parsed.path:
            parsed = parsed._replace(path='/')
            
        return urlunparse(parsed)
        
    @staticmethod
    def extract_credentials(url: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Extrae credenciales de una URL.
        
        Args:
            url: URL con posibles credenciales
            
        Returns:
            Tupla (url_sin_credenciales, username, password)
        """
        parsed = urlparse(url)
        
        username = parsed.username
        password = parsed.password
        
        # Reconstruir URL sin credenciales
        if username:
            netloc = parsed.hostname
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            parsed = parsed._replace(netloc=netloc)
            
        clean_url = urlunparse(parsed)
        
        return clean_url, username, password
        
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Valida una dirección IP."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False