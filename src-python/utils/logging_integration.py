"""
Integración de logging mejorado con contexto para servicios de cámara.

Este módulo proporciona funciones de utilidad para integrar
el logging enriquecido en los servicios existentes.
"""
from typing import Optional, Dict, Any, Callable
import functools
import logging

from utils.log_context import (
    LogContext, 
    set_camera_context,
    set_stream_context,
    with_correlation_id,
    log_execution_time,
    build_log_context
)
from services.logging_service import get_secure_logger


def camera_operation(camera_id: str, 
                    camera_ip: Optional[str] = None,
                    brand: Optional[str] = None) -> Callable:
    """
    Decorador para operaciones de cámara que agrega contexto automáticamente.
    
    Args:
        camera_id: ID de la cámara
        camera_ip: IP de la cámara
        brand: Marca de la cámara
        
    Returns:
        Decorador configurado
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Establecer contexto de cámara
            with LogContext(camera={
                'id': camera_id,
                'ip': camera_ip,
                'brand': brand
            }):
                # Obtener logger con contexto
                logger = get_secure_logger(func.__module__)
                
                # Log de inicio de operación
                logger.info(
                    f"Iniciando operación {func.__name__} para cámara",
                    extra=build_log_context()
                )
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log de éxito
                    logger.info(
                        f"Operación {func.__name__} completada exitosamente",
                        extra=build_log_context()
                    )
                    
                    return result
                    
                except Exception as e:
                    # Log de error con contexto
                    logger.error(
                        f"Error en operación {func.__name__}: {e}",
                        extra=build_log_context(),
                        exc_info=True
                    )
                    raise
                    
        return wrapper
    return decorator


def stream_operation(stream_id: str,
                    protocol: str,
                    camera_id: Optional[str] = None) -> Callable:
    """
    Decorador para operaciones de streaming con contexto.
    
    Args:
        stream_id: ID del stream
        protocol: Protocolo de streaming
        camera_id: ID de la cámara asociada
        
    Returns:
        Decorador configurado
    """
    def decorator(func):
        @functools.wraps(func)
        @with_correlation_id
        @log_execution_time()
        async def wrapper(*args, **kwargs):
            # Establecer contexto de streaming
            context_data = {
                'stream': {
                    'id': stream_id,
                    'protocol': protocol
                }
            }
            
            if camera_id:
                context_data['camera'] = {'id': camera_id}
                
            with LogContext(**context_data):
                logger = get_secure_logger(func.__module__)
                
                # Agregar métricas de streaming
                logger.info(
                    f"Stream {stream_id} - Iniciando {func.__name__}",
                    extra={
                        **build_log_context(),
                        'event_type': 'stream_operation_start',
                        'operation': func.__name__
                    }
                )
                
                return await func(*args, **kwargs)
                
        return wrapper
    return decorator


class EnhancedLogger:
    """
    Logger mejorado que automáticamente incluye contexto en todos los mensajes.
    
    Wrapper sobre el logger estándar que agrega contexto de forma transparente.
    """
    
    def __init__(self, name: str):
        """
        Inicializa el logger mejorado.
        
        Args:
            name: Nombre del logger
        """
        self.logger = get_secure_logger(name)
        self.name = name
        
    def _log_with_context(self, level: int, msg: str, 
                         extra: Optional[Dict[str, Any]] = None,
                         **kwargs) -> None:
        """
        Log con contexto automático.
        
        Args:
            level: Nivel de logging
            msg: Mensaje
            extra: Campos extra adicionales
            kwargs: Argumentos adicionales
        """
        # Construir contexto completo
        context = build_log_context()
        
        # Agregar campos extra si existen
        if extra:
            context.update(extra)
            
        # Log con contexto
        self.logger.log(level, msg, extra=context, **kwargs)
        
    def debug(self, msg: str, **kwargs) -> None:
        """Log de debug con contexto."""
        self._log_with_context(logging.DEBUG, msg, **kwargs)
        
    def info(self, msg: str, **kwargs) -> None:
        """Log de info con contexto."""
        self._log_with_context(logging.INFO, msg, **kwargs)
        
    def warning(self, msg: str, **kwargs) -> None:
        """Log de warning con contexto."""
        self._log_with_context(logging.WARNING, msg, **kwargs)
        
    def error(self, msg: str, **kwargs) -> None:
        """Log de error con contexto."""
        self._log_with_context(logging.ERROR, msg, **kwargs)
        
    def critical(self, msg: str, **kwargs) -> None:
        """Log crítico con contexto."""
        self._log_with_context(logging.CRITICAL, msg, **kwargs)
        
    def audit(self, event_type: str, details: Dict[str, Any], **kwargs) -> None:
        """
        Log de auditoría con contexto.
        
        Args:
            event_type: Tipo de evento
            details: Detalles del evento
            kwargs: Argumentos adicionales
        """
        context = build_log_context()
        context['audit_event_type'] = event_type
        context['audit_details'] = details
        
        self.logger.audit(
            f"AUDIT: {event_type}",
            extra=context,
            **kwargs
        )
        
    def camera_event(self, camera_id: str, event: str, 
                    details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log específico para eventos de cámara.
        
        Args:
            camera_id: ID de la cámara
            event: Tipo de evento
            details: Detalles adicionales
        """
        extra = {
            'camera_id': camera_id,
            'camera_event': event,
            'event_details': details or {}
        }
        
        self._log_with_context(
            logging.INFO,
            f"Cámara {camera_id}: {event}",
            extra=extra
        )
        
    def stream_metric(self, stream_id: str, metric_name: str, 
                     value: Any, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Log de métrica de streaming.
        
        Args:
            stream_id: ID del stream
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            tags: Tags adicionales
        """
        extra = {
            'stream_id': stream_id,
            'metric_name': metric_name,
            'metric_value': value,
            'metric_tags': tags or {},
            'event_type': 'stream_metric'
        }
        
        self._log_with_context(
            logging.INFO,
            f"Stream {stream_id} - {metric_name}: {value}",
            extra=extra
        )


def get_enhanced_logger(name: str) -> EnhancedLogger:
    """
    Obtiene un logger mejorado con capacidades de contexto.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger mejorado
    """
    return EnhancedLogger(name)


# Ejemplo de uso en servicios
"""
# En un servicio de cámara:
from utils.logging_integration import get_enhanced_logger, camera_operation

class CameraConnectionService:
    def __init__(self):
        self.logger = get_enhanced_logger(__name__)
        
    @camera_operation(camera_id="cam_123", camera_ip="192.168.1.100", brand="Dahua")
    async def connect_camera(self, camera_id: str):
        # El contexto ya está establecido por el decorador
        self.logger.info("Estableciendo conexión ONVIF")
        
        # Agregar métricas
        self.logger.stream_metric(
            stream_id=f"stream_{camera_id}",
            metric_name="connection_latency",
            value=125,
            tags={"protocol": "ONVIF"}
        )
        
        # Evento de cámara
        self.logger.camera_event(
            camera_id=camera_id,
            event="connection_established",
            details={"protocol": "ONVIF", "port": 80}
        )
"""


# TODO: Funcionalidad pendiente - Integración con OpenTelemetry
# La integración completa con trazas distribuidas requiere:
# 1. Instalación de opentelemetry-api y opentelemetry-sdk
# 2. Configuración de exportadores (Jaeger, Zipkin, etc)
# 3. Instrumentación automática de frameworks (FastAPI, aiohttp)
# 4. Propagación de contexto entre servicios
#
# Por ahora, el correlation_id proporciona trazabilidad básica
# que es suficiente para la agregación de logs en ELK