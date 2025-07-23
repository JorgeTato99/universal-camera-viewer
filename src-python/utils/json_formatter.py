"""
Formateador JSON para logs estructurados compatibles con ELK Stack.

Este módulo proporciona formateadores JSON que mantienen la sanitización
de datos sensibles mientras estructuran los logs para agregación.
"""
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import socket
import os

from utils.sanitizers import create_safe_log_context
from config.settings import settings


class StructuredJSONFormatter(logging.Formatter):
    """
    Formateador que genera logs en formato JSON estructurado para ELK.
    
    Características:
    - Formato JSON consistente
    - Campos estandarizados para búsqueda
    - Metadatos enriquecidos
    - Sanitización integrada
    - Compatible con Logstash/Filebeat
    """
    
    # Campos estándar ELK
    STANDARD_FIELDS = {
        'timestamp': '@timestamp',
        'level': 'level',
        'logger': 'logger_name',
        'message': 'message',
        'module': 'module',
        'function': 'function',
        'line': 'line_number',
        'thread': 'thread_name',
        'process': 'process_id'
    }
    
    def __init__(self, 
                 app_name: Optional[str] = None,
                 environment: Optional[str] = None,
                 include_hostname: bool = True,
                 include_extra_fields: bool = True,
                 sanitize: bool = True):
        """
        Inicializa el formateador JSON.
        
        Args:
            app_name: Nombre de la aplicación
            environment: Ambiente (production/development)
            include_hostname: Si incluir el hostname
            include_extra_fields: Si incluir campos extra del record
            sanitize: Si aplicar sanitización a los campos
        """
        super().__init__()
        self.app_name = app_name or settings.APP_NAME
        self.environment = environment or os.getenv('ENVIRONMENT', 'production')
        self.include_hostname = include_hostname
        self.include_extra_fields = include_extra_fields
        self.sanitize = sanitize
        self.hostname = socket.gethostname() if include_hostname else None
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro de log en JSON.
        
        Args:
            record: Registro de logging
            
        Returns:
            String JSON con el log estructurado
        """
        # Construir documento base
        log_data = {
            '@timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno,
            'thread_name': record.threadName,
            'process_id': record.process,
            'app': {
                'name': self.app_name,
                'version': settings.APP_VERSION,
                'environment': self.environment
            }
        }
        
        # Agregar hostname si está habilitado
        if self.include_hostname:
            log_data['host'] = {
                'name': self.hostname
            }
            
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data['error'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stack_trace': self.formatException(record.exc_info)
            }
            
        # Agregar campos extra del record
        if self.include_extra_fields:
            # Campos estándar a excluir
            skip_fields = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'
            }
            
            # Agregar campos personalizados
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in skip_fields:
                    extra_fields[key] = value
                    
            if extra_fields:
                # Sanitizar si está habilitado
                if self.sanitize:
                    extra_fields = create_safe_log_context(extra_fields)
                log_data['extra'] = extra_fields
                
        # Agregar campos específicos según el tipo de log
        if record.levelname == 'AUDIT':
            log_data['audit'] = True
            log_data['event_type'] = 'audit'
            
        # Sanitizar el mensaje principal si es necesario
        if self.sanitize and 'password' in log_data['message'].lower():
            log_data['message'] = self._sanitize_message(log_data['message'])
            
        # Convertir a JSON
        return json.dumps(log_data, ensure_ascii=False, default=str)
        
    def _sanitize_message(self, message: str) -> str:
        """
        Sanitiza el mensaje principal del log.
        
        Args:
            message: Mensaje a sanitizar
            
        Returns:
            Mensaje sanitizado
        """
        # Patrones comunes a sanitizar
        import re
        
        patterns = [
            (r'password[=:\s]+\S+', 'password=***'),
            (r'token[=:\s]+\S+', 'token=***'),
            (r'key[=:\s]+\S+', 'key=***'),
            (r'secret[=:\s]+\S+', 'secret=***')
        ]
        
        sanitized = message
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            
        return sanitized


class ElasticCommonSchema(StructuredJSONFormatter):
    """
    Formateador que sigue el Elastic Common Schema (ECS).
    
    ECS es un conjunto de campos comunes para estructurar logs
    de manera consistente en el Elastic Stack.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro siguiendo ECS.
        
        Args:
            record: Registro de logging
            
        Returns:
            String JSON compatible con ECS
        """
        # Timestamp en formato ISO8601
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Documento ECS base
        ecs_doc = {
            '@timestamp': timestamp,
            'log': {
                'level': record.levelname.lower(),
                'logger': record.name,
                'origin': {
                    'file': {
                        'name': record.filename,
                        'line': record.lineno
                    },
                    'function': record.funcName
                }
            },
            'message': record.getMessage(),
            'service': {
                'name': self.app_name,
                'version': settings.APP_VERSION,
                'environment': self.environment
            },
            'process': {
                'pid': record.process,
                'thread': {
                    'id': record.thread,
                    'name': record.threadName
                }
            },
            'event': {
                'created': timestamp,
                'kind': 'event',
                'category': ['process'],
                'type': ['info']
            }
        }
        
        # Agregar host si está habilitado
        if self.include_hostname:
            ecs_doc['host'] = {
                'hostname': self.hostname
            }
            
        # Manejar diferentes niveles
        if record.levelname in ['ERROR', 'CRITICAL']:
            ecs_doc['event']['type'] = ['error']
            if record.exc_info:
                ecs_doc['error'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'stack_trace': self.formatException(record.exc_info)
                }
                
        elif record.levelname == 'WARNING':
            ecs_doc['event']['type'] = ['warning']
            
        elif record.levelname == 'AUDIT':
            ecs_doc['event']['kind'] = 'audit'
            ecs_doc['event']['category'] = ['authentication', 'process']
            
        # Agregar campos extra si existen
        if hasattr(record, 'camera_id'):
            ecs_doc['camera'] = {
                'id': record.camera_id,
                'ip': getattr(record, 'camera_ip', None),
                'brand': getattr(record, 'camera_brand', None)
            }
            
        if hasattr(record, 'user'):
            ecs_doc['user'] = {
                'name': record.user,
                'ip': getattr(record, 'user_ip', None)
            }
            
        # Agregar contexto extra
        if self.include_extra_fields and hasattr(record, 'context'):
            context = record.context
            if self.sanitize:
                context = create_safe_log_context(context)
            ecs_doc['labels'] = context
            
        return json.dumps(ecs_doc, ensure_ascii=False, default=str)


class CameraStreamingJSONFormatter(StructuredJSONFormatter):
    """
    Formateador especializado para logs de streaming de cámaras.
    
    Agrega campos específicos relevantes para el análisis de
    streaming y conexiones de cámaras.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea con campos específicos de streaming.
        
        Args:
            record: Registro de logging
            
        Returns:
            String JSON con campos de streaming
        """
        # Obtener formato base
        log_data = json.loads(super().format(record))
        
        # Agregar campos específicos de streaming
        streaming_fields = {}
        
        # Extraer información de cámara si está disponible
        if hasattr(record, 'camera_id'):
            streaming_fields['camera'] = {
                'id': record.camera_id,
                'ip': getattr(record, 'camera_ip', None),
                'brand': getattr(record, 'camera_brand', None),
                'model': getattr(record, 'camera_model', None)
            }
            
        # Información de streaming
        if hasattr(record, 'stream_id'):
            streaming_fields['stream'] = {
                'id': record.stream_id,
                'protocol': getattr(record, 'protocol', None),
                'fps': getattr(record, 'fps', None),
                'resolution': getattr(record, 'resolution', None),
                'bitrate': getattr(record, 'bitrate', None),
                'codec': getattr(record, 'codec', None)
            }
            
        # Métricas de rendimiento
        if hasattr(record, 'latency'):
            streaming_fields['performance'] = {
                'latency_ms': record.latency,
                'dropped_frames': getattr(record, 'dropped_frames', 0),
                'buffer_size': getattr(record, 'buffer_size', None)
            }
            
        # Estado de conexión
        if hasattr(record, 'connection_state'):
            streaming_fields['connection'] = {
                'state': record.connection_state,
                'duration_seconds': getattr(record, 'connection_duration', None),
                'retry_count': getattr(record, 'retry_count', 0)
            }
            
        # Agregar campos de streaming al log
        if streaming_fields:
            log_data['streaming'] = streaming_fields
            
        # Categorizar el evento para facilitar búsquedas
        if 'event' not in log_data:
            log_data['event'] = {}
            
        log_data['event']['dataset'] = 'camera.streaming'
        log_data['event']['module'] = 'camera'
        
        return json.dumps(log_data, ensure_ascii=False, default=str)