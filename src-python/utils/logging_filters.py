"""
Filtros de logging para proteger información sensible.

Este módulo proporciona filtros que se pueden aplicar a los loggers
para automáticamente sanitizar información sensible antes de que
sea escrita a los logs.
"""
import logging
import re
from typing import Set, List, Optional, Dict, Any
import os

from .sanitizers import (
    sanitize_url, 
    sanitize_command, 
    sanitize_error_message,
    sanitize_log_message,
    sanitize_config
)


class SensitiveDataFilter(logging.Filter):
    """
    Filtro de logging que detecta y sanitiza automáticamente información sensible.
    
    Este filtro busca patrones de información sensible en los mensajes de log
    y los reemplaza con versiones sanitizadas.
    """
    
    def __init__(self, name: str = '', 
                 additional_patterns: Optional[List[str]] = None,
                 environment: str = 'production'):
        """
        Inicializa el filtro.
        
        Args:
            name: Nombre del filtro
            additional_patterns: Patrones regex adicionales a filtrar
            environment: Ambiente actual (production, development, etc.)
        """
        super().__init__(name)
        self.environment = environment
        self.additional_patterns = additional_patterns or []
        
        # Compilar patrones para mejor performance
        self._compiled_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> List[re.Pattern]:
        """Compila los patrones regex para detección."""
        patterns = [
            # URLs con credenciales
            r'((?:rtsp|http[s]?|ftp|sftp)://[^:]+:[^@]+@[^\s]+)',
            # Comandos con passwords
            r'(-password\s+\S+)',
            r'(--pass[=\s]+\S+)',
            r'(-p\s+\S+)',  # Común en MySQL y otros
            # API Keys y tokens
            r'([aA][pP][iI][-_]?[kK][eE][yY][=:\s]+\S+)',
            r'([tT][oO][kK][eE][nN][=:\s]+\S+)',
            r'([aA][uU][tT][hH][oO][rR][iI][zZ][aA][tT][iI][oO][nN]:\s*[bB][eE][aA][rR][eE][rR]\s+\S+)',
            # Hashes y claves largas
            r'\b([a-fA-F0-9]{32,})\b',
            # Credenciales en formato key=value
            r'(password[=:]\S+)',
            r'(passwd[=:]\S+)',
            r'(pwd[=:]\S+)',
            r'(secret[=:]\S+)',
        ]
        
        # Agregar patrones adicionales
        patterns.extend(self.additional_patterns)
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra un registro de log.
        
        Args:
            record: Registro a filtrar
            
        Returns:
            True para permitir el log (siempre True, solo modifica el contenido)
        """
        # Sanitizar el mensaje principal
        if hasattr(record, 'msg'):
            record.msg = self._sanitize_message(str(record.msg))
            
        # Sanitizar argumentos si existen
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_config(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize_value(arg) for arg in record.args)
                
        # Sanitizar información de excepción si existe
        if record.exc_info and record.exc_info[1]:
            # Sanitizar el mensaje de la excepción
            exception = record.exc_info[1]
            if hasattr(exception, 'args') and exception.args:
                exception.args = tuple(
                    sanitize_error_message(str(arg)) for arg in exception.args
                )
                
        return True
        
    def _sanitize_message(self, message: str) -> str:
        """Sanitiza un mensaje de log."""
        sanitized = message
        
        # Aplicar cada patrón compilado
        for pattern in self._compiled_patterns:
            matches = pattern.findall(sanitized)
            for match in matches:
                # Determinar tipo de contenido y sanitizar apropiadamente
                if any(proto in match for proto in ['://', 'rtsp:', 'http:']):
                    replacement = sanitize_url(match)
                else:
                    replacement = '[REDACTED]'
                    
                sanitized = sanitized.replace(match, replacement)
                
        # En desarrollo, ser menos agresivo con la sanitización
        if self.environment == 'development':
            # Permitir ver más información pero aún ocultar passwords
            sanitized = self._development_sanitize(sanitized)
            
        return sanitized
        
    def _development_sanitize(self, message: str) -> str:
        """Sanitización menos agresiva para desarrollo."""
        # Solo ocultar passwords y tokens muy obvios
        critical_patterns = [
            (r'password[=:\s]+(\S+)', r'password=[REDACTED]'),
            (r'token[=:\s]+(\S+)', r'token=[REDACTED]'),
            (r'api[-_]?key[=:\s]+(\S+)', r'api_key=[REDACTED]'),
        ]
        
        result = message
        for pattern, replacement in critical_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            
        return result
        
    def _sanitize_value(self, value: Any) -> Any:
        """Sanitiza un valor individual."""
        if isinstance(value, str):
            return self._sanitize_message(value)
        elif isinstance(value, dict):
            return sanitize_config(value)
        else:
            return value


class URLSanitizerFilter(logging.Filter):
    """
    Filtro especializado para sanitizar URLs en logs.
    
    Este filtro es más eficiente que SensitiveDataFilter cuando
    solo se necesita sanitizar URLs.
    """
    
    def __init__(self, name: str = '', show_user: bool = False):
        """
        Inicializa el filtro.
        
        Args:
            name: Nombre del filtro
            show_user: Si mostrar parcialmente el nombre de usuario
        """
        super().__init__(name)
        self.show_user = show_user
        self._url_pattern = re.compile(
            r'((?:rtsp|http[s]?|ftp|sftp|ssh)://[^\s]+)'
        )
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Filtra URLs en el registro."""
        if hasattr(record, 'msg'):
            message = str(record.msg)
            
            # Buscar todas las URLs
            for match in self._url_pattern.findall(message):
                sanitized = sanitize_url(match, show_user=self.show_user)
                message = message.replace(match, sanitized)
                
            record.msg = message
            
        return True


class CommandSanitizerFilter(logging.Filter):
    """
    Filtro especializado para sanitizar comandos del sistema en logs.
    
    Útil cuando se loggean comandos de FFmpeg, curl, etc.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filtra comandos en el registro."""
        if hasattr(record, 'msg'):
            message = str(record.msg)
            
            # Detectar si el mensaje contiene un comando
            command_indicators = [
                'ffmpeg', 'curl', 'wget', 'ssh', 'scp',
                'mysql', 'psql', 'mongo', 'redis-cli'
            ]
            
            if any(cmd in message.lower() for cmd in command_indicators):
                record.msg = sanitize_command(message)
                
        return True


class ContextualFilter(logging.Filter):
    """
    Filtro que aplica sanitización basada en el contexto del logger.
    
    Por ejemplo, diferentes sanitizaciones para diferentes módulos.
    """
    
    def __init__(self, context_rules: Dict[str, str]):
        """
        Inicializa el filtro con reglas contextuales.
        
        Args:
            context_rules: Diccionario de {nombre_logger: tipo_sanitización}
            
        Ejemplo:
            {
                'services.rtsp': 'url',
                'services.ffmpeg': 'command',
                'api.auth': 'config'
            }
        """
        super().__init__()
        self.context_rules = context_rules
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Aplica sanitización según el contexto."""
        logger_name = record.name
        
        # Buscar regla aplicable
        sanitization_type = None
        for pattern, stype in self.context_rules.items():
            if pattern in logger_name:
                sanitization_type = stype
                break
                
        if sanitization_type and hasattr(record, 'msg'):
            record.msg = sanitize_log_message(
                str(record.msg), 
                context=sanitization_type
            )
            
        return True


class EnvironmentBasedFilter(logging.Filter):
    """
    Filtro que ajusta el nivel de sanitización según el ambiente.
    
    - Producción: Sanitización completa
    - Desarrollo: Sanitización parcial
    - Testing: Mínima sanitización
    """
    
    def __init__(self, environment: Optional[str] = None):
        """
        Inicializa el filtro.
        
        Args:
            environment: Ambiente actual (si no se proporciona, se detecta)
        """
        super().__init__()
        self.environment = environment or os.getenv('ENVIRONMENT', 'production')
        
        # Configurar nivel de sanitización
        self.sanitization_levels = {
            'production': 'full',
            'development': 'partial',
            'testing': 'minimal',
            'debug': 'minimal'
        }
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Aplica sanitización según el ambiente."""
        level = self.sanitization_levels.get(self.environment, 'full')
        
        if level == 'minimal':
            # Solo ocultar passwords muy obvios
            return self._minimal_sanitization(record)
        elif level == 'partial':
            # Aplicar URLSanitizerFilter
            url_filter = URLSanitizerFilter(show_user=True)
            return url_filter.filter(record)
        else:
            # Sanitización completa
            full_filter = SensitiveDataFilter(environment=self.environment)
            return full_filter.filter(record)
            
    def _minimal_sanitization(self, record: logging.LogRecord) -> bool:
        """Sanitización mínima para ambientes de desarrollo."""
        if hasattr(record, 'msg'):
            message = str(record.msg)
            # Solo ocultar passwords literales
            message = re.sub(
                r'password[=:\s]+"?([^"\s]+)"?', 
                'password=[REDACTED]', 
                message, 
                flags=re.IGNORECASE
            )
            record.msg = message
            
        return True


def setup_logging_filters(logger: logging.Logger, 
                        environment: str = 'production',
                        additional_patterns: Optional[List[str]] = None) -> None:
    """
    Configura filtros de logging para un logger.
    
    Args:
        logger: Logger a configurar
        environment: Ambiente actual
        additional_patterns: Patrones adicionales a filtrar
    """
    # Remover filtros existentes
    logger.filters.clear()
    
    # Agregar filtros según el ambiente
    if environment == 'production':
        # Máxima protección en producción
        logger.addFilter(SensitiveDataFilter(
            environment=environment,
            additional_patterns=additional_patterns
        ))
        logger.addFilter(URLSanitizerFilter(show_user=False))
        logger.addFilter(CommandSanitizerFilter())
    else:
        # Protección balanceada en desarrollo
        logger.addFilter(EnvironmentBasedFilter(environment))
        
    # Aplicar también a los handlers
    for handler in logger.handlers:
        handler.addFilter(SensitiveDataFilter(
            environment=environment,
            additional_patterns=additional_patterns
        ))