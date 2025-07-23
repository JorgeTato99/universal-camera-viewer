"""
Servicio centralizado de logging con protección de información sensible.

Este servicio proporciona:
- Logging seguro con sanitización automática
- Diferentes niveles según ambiente
- Auditoría de eventos sensibles
- Rotación de logs
- Métricas de logging
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import threading

from services.base_service import BaseService
from utils.logging_filters import (
    SensitiveDataFilter,
    URLSanitizerFilter,
    CommandSanitizerFilter,
    EnvironmentBasedFilter,
    setup_logging_filters
)
from utils.sanitizers import sanitize_config, create_safe_log_context


class LogLevel:
    """Niveles de log personalizados."""
    TRACE = 5
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    AUDIT = 45  # Entre ERROR y CRITICAL


class SecureLogger(logging.Logger):
    """
    Logger personalizado con capacidades de sanitización automática.
    """
    
    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)
        self._audit_handler: Optional[logging.Handler] = None
        
    def audit(self, msg: str, *args, **kwargs):
        """
        Log de auditoría para eventos sensibles.
        
        Args:
            msg: Mensaje de auditoría
            args: Argumentos del mensaje
            kwargs: Argumentos adicionales
        """
        if self.isEnabledFor(LogLevel.AUDIT):
            self._log(LogLevel.AUDIT, msg, args, **kwargs)
            
    def log_secure(self, level: int, msg: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Log con contexto automáticamente sanitizado.
        
        Args:
            level: Nivel de log
            msg: Mensaje principal
            context: Contexto adicional a sanitizar
            kwargs: Argumentos adicionales
        """
        if context:
            # Sanitizar contexto
            safe_context = create_safe_log_context(context)
            extra = kwargs.get('extra', {})
            extra['context'] = safe_context
            kwargs['extra'] = extra
            
        self.log(level, msg, **kwargs)


class LoggingService(BaseService):
    """
    Servicio singleton para gestión centralizada de logging.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "LoggingService":
        """Garantiza una única instancia thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        """Inicializa el servicio de logging."""
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        
        # Configuración
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Estado interno
        self._loggers: Dict[str, SecureLogger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._log_metrics = {
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'audit_events': 0,
            'sanitized_items': 0
        }
        
        # Configurar logging base
        self._setup_base_logging()
        
        # Registrar nivel AUDIT
        logging.addLevelName(LogLevel.AUDIT, "AUDIT")
        
        self._initialized = True
        
    def _setup_base_logging(self) -> None:
        """Configura el sistema de logging base."""
        # Configurar formato según ambiente
        if self.environment == 'production':
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S'
        else:
            # Más detalle en desarrollo
            log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S.%f'[:-3]
            
        # Formatter base
        self.formatter = logging.Formatter(log_format, datefmt=date_format)
        
        # Configurar si usar JSON para ELK
        self.use_json_logs = os.getenv('USE_JSON_LOGS', 'false').lower() == 'true'
        self.elk_enabled = os.getenv('ELK_ENABLED', 'false').lower() == 'true'
        
        # Configurar handlers por defecto
        self._setup_default_handlers()
        
    def _setup_default_handlers(self) -> None:
        """Configura handlers por defecto."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Usar JSON formatter si está habilitado
        if self.use_json_logs:
            from utils.json_formatter import StructuredJSONFormatter
            json_formatter = StructuredJSONFormatter(
                environment=self.environment,
                sanitize=True
            )
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(self.formatter)
            
        console_handler.addFilter(EnvironmentBasedFilter(self.environment))
        self._handlers['console'] = console_handler
        
        # File handler con rotación
        file_path = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.formatter)
        file_handler.addFilter(SensitiveDataFilter(environment=self.environment))
        self._handlers['file'] = file_handler
        
        # Error file handler (solo errores y superior)
        error_path = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.formatter)
        error_handler.addFilter(SensitiveDataFilter(environment=self.environment))
        self._handlers['error'] = error_handler
        
        # Audit handler (eventos de seguridad)
        audit_path = self.log_dir / "audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,  # Mantener más historial de auditoría
            encoding='utf-8'
        )
        audit_handler.setLevel(LogLevel.AUDIT)
        
        # Formato especial para auditoría con más información
        audit_format = '%(asctime)s - %(name)s - AUDIT - %(message)s - %(pathname)s:%(lineno)d'
        audit_handler.setFormatter(logging.Formatter(audit_format))
        self._handlers['audit'] = audit_handler
        
        # ELK Handler si está habilitado
        if self.elk_enabled:
            self._setup_elk_handler()
            
    def _setup_elk_handler(self) -> None:
        """Configura el handler para ELK Stack."""
        try:
            from utils.elk_handler import create_elk_handler
            
            # Configurar tipo de handler según ambiente
            handler_type = os.getenv('ELK_HANDLER_TYPE', 'file')
            
            if handler_type == 'file':
                # Handler basado en archivos (recomendado para producción)
                elk_handler = create_elk_handler(
                    handler_type='file',
                    log_dir=str(self.log_dir / 'elk'),
                    index_prefix='ucv',
                    buffer_size=int(os.getenv('ELK_BUFFER_SIZE', '1000')),
                    flush_interval=float(os.getenv('ELK_FLUSH_INTERVAL', '5.0'))
                )
            else:
                # Handler directo a Elasticsearch (desarrollo/testing)
                elk_handler = create_elk_handler(
                    handler_type='elasticsearch',
                    es_host=os.getenv('ELASTICSEARCH_HOST', 'localhost'),
                    es_port=int(os.getenv('ELASTICSEARCH_PORT', '9200')),
                    index_prefix='ucv',
                    use_ssl=os.getenv('ELASTICSEARCH_SSL', 'false').lower() == 'true',
                    es_user=os.getenv('ELASTICSEARCH_USER'),
                    es_password=os.getenv('ELASTICSEARCH_PASSWORD')
                )
                
            # Agregar filtros de seguridad
            elk_handler.addFilter(SensitiveDataFilter(environment=self.environment))
            
            self._handlers['elk'] = elk_handler
            self.logger.info(f"ELK handler configurado: {handler_type}")
            
        except Exception as e:
            self.logger.error(f"Error configurando ELK handler: {e}")
        
    def get_logger(self, name: str, 
                   additional_filters: Optional[List[str]] = None) -> SecureLogger:
        """
        Obtiene un logger seguro con filtros aplicados.
        
        Args:
            name: Nombre del logger
            additional_filters: Patrones adicionales a filtrar
            
        Returns:
            Logger configurado con protecciones
        """
        if name in self._loggers:
            return self._loggers[name]
            
        # Crear nuevo logger
        logger = SecureLogger(name)
        
        # Establecer nivel según ambiente
        if self.environment == 'production':
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)
            
        # Agregar handlers
        for handler_name, handler in self._handlers.items():
            logger.addHandler(handler)
            
        # Configurar filtros
        setup_logging_filters(logger, self.environment, additional_filters)
        
        # Agregar filtros específicos según el nombre del logger
        self._apply_contextual_filters(logger, name)
        
        # Guardar referencia
        self._loggers[name] = logger
        
        return logger
        
    def _apply_contextual_filters(self, logger: SecureLogger, name: str) -> None:
        """Aplica filtros contextuales según el nombre del logger."""
        # Filtros específicos para diferentes módulos
        if 'rtsp' in name.lower() or 'streaming' in name.lower():
            logger.addFilter(URLSanitizerFilter())
            
        if 'command' in name.lower() or 'ffmpeg' in name.lower():
            logger.addFilter(CommandSanitizerFilter())
            
        if 'protocol' in name.lower() or 'connection' in name.lower():
            logger.addFilter(URLSanitizerFilter())
            logger.addFilter(SensitiveDataFilter(
                additional_patterns=[
                    r'username[=:\s]+(\S+)',
                    r'user[=:\s]+(\S+)',
                ]
            ))
            
    def configure_module_logging(self, module_name: str, 
                               level: Optional[int] = None,
                               filters: Optional[List[str]] = None) -> None:
        """
        Configura logging para un módulo específico.
        
        Args:
            module_name: Nombre del módulo
            level: Nivel de logging (opcional)
            filters: Filtros adicionales (opcional)
        """
        logger = self.get_logger(module_name, filters)
        
        if level is not None:
            logger.setLevel(level)
            
    def add_custom_handler(self, name: str, handler: logging.Handler) -> None:
        """
        Agrega un handler personalizado.
        
        Args:
            name: Nombre del handler
            handler: Handler a agregar
        """
        # Aplicar filtros de seguridad al handler
        handler.addFilter(SensitiveDataFilter(environment=self.environment))
        
        self._handlers[name] = handler
        
        # Agregar a todos los loggers existentes
        for logger in self._loggers.values():
            logger.addHandler(handler)
            
    def log_audit_event(self, event_type: str, 
                       details: Dict[str, Any],
                       user: Optional[str] = None,
                       ip: Optional[str] = None) -> None:
        """
        Registra un evento de auditoría.
        
        Args:
            event_type: Tipo de evento (login, access_credential, etc.)
            details: Detalles del evento
            user: Usuario que realizó la acción
            ip: IP desde donde se realizó
        """
        audit_logger = self.get_logger('audit')
        
        # Construir mensaje de auditoría
        audit_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'user': user or 'system',
            'ip': ip or 'local',
            'details': create_safe_log_context(details)
        }
        
        # Log como JSON para fácil parseo
        audit_logger.audit(json.dumps(audit_data, ensure_ascii=False))
        
        # Actualizar métricas
        self._log_metrics['audit_events'] += 1
        
    def log_metric(self, metric_name: str, value: Any, 
                  tags: Optional[Dict[str, str]] = None) -> None:
        """
        Registra una métrica.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            tags: Tags adicionales
        """
        metrics_logger = self.get_logger('metrics')
        
        metric_data = {
            'metric': metric_name,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'tags': tags or {}
        }
        
        metrics_logger.info(json.dumps(metric_data, ensure_ascii=False))
        
    def get_logging_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de logging.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'environment': self.environment,
            'active_loggers': len(self._loggers),
            'handlers': list(self._handlers.keys()),
            'metrics': self._log_metrics.copy(),
            'log_files': []
        }
        
        # Listar archivos de log
        if self.log_dir.exists():
            for log_file in self.log_dir.glob('*.log'):
                stats['log_files'].append({
                    'name': log_file.name,
                    'size_mb': log_file.stat().st_size / 1024 / 1024,
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
                
        return stats
        
    def rotate_logs(self) -> None:
        """Fuerza la rotación de todos los logs."""
        for name, handler in self._handlers.items():
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
                self.logger.info(f"Log rotado: {name}")
                
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Limpia logs antiguos.
        
        Args:
            days: Días a mantener
            
        Returns:
            Número de archivos eliminados
        """
        if not self.log_dir.exists():
            return 0
            
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        removed = 0
        
        for log_file in self.log_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_date:
                try:
                    log_file.unlink()
                    removed += 1
                except Exception as e:
                    self.logger.error(f"Error eliminando log {log_file}: {e}")
                    
        if removed > 0:
            self.logger.info(f"Eliminados {removed} archivos de log antiguos")
            
        return removed
        
    def set_environment(self, environment: str) -> None:
        """
        Cambia el ambiente y reconfigura los filtros.
        
        Args:
            environment: Nuevo ambiente
        """
        self.environment = environment
        
        # Reconfigurar todos los loggers
        for logger in self._loggers.values():
            setup_logging_filters(logger, environment)
            
        self.logger.info(f"Ambiente cambiado a: {environment}")
        
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        # Cerrar todos los handlers
        for handler in self._handlers.values():
            handler.close()
            
        self.logger.info("Servicio de logging cerrado")


# Instancia global del servicio
logging_service = LoggingService()


# Funciones de conveniencia
def get_secure_logger(name: str) -> SecureLogger:
    """Obtiene un logger seguro."""
    return logging_service.get_logger(name)


def log_audit(event_type: str, details: Dict[str, Any], 
              user: Optional[str] = None, ip: Optional[str] = None) -> None:
    """Registra un evento de auditoría."""
    logging_service.log_audit_event(event_type, details, user, ip)