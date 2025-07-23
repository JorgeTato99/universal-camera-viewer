"""
Utilidades para enriquecer logs con contexto y metadata.

Proporciona decoradores y context managers para agregar
información contextual a los logs automáticamente.
"""
import logging
import functools
import asyncio
import time
import uuid
from typing import Any, Dict, Optional, Callable, TypeVar, Union
from contextvars import ContextVar
import threading

# Variables de contexto para información transversal
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('user_context', default=None)
camera_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('camera_context', default=None)
stream_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('stream_context', default=None)

# Type var para decoradores
F = TypeVar('F', bound=Callable[..., Any])


class LogContext:
    """Context manager para agregar contexto temporal a logs."""
    
    def __init__(self, **kwargs):
        """
        Inicializa el contexto.
        
        Args:
            kwargs: Pares clave-valor para agregar al contexto
        """
        self.context = kwargs
        self.original_values = {}
        
    def __enter__(self):
        """Establece el contexto."""
        # Guardar valores originales
        for key, value in self.context.items():
            if key == 'correlation_id':
                self.original_values[key] = correlation_id.get()
                correlation_id.set(value)
            elif key == 'user':
                self.original_values[key] = user_context.get()
                user_context.set(value)
            elif key == 'camera':
                self.original_values[key] = camera_context.get()
                camera_context.set(value)
            elif key == 'stream':
                self.original_values[key] = stream_context.get()
                stream_context.set(value)
                
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restaura el contexto original."""
        for key, original_value in self.original_values.items():
            if key == 'correlation_id':
                correlation_id.set(original_value)
            elif key == 'user':
                user_context.set(original_value)
            elif key == 'camera':
                camera_context.set(original_value)
            elif key == 'stream':
                stream_context.set(original_value)


def with_correlation_id(func: F) -> F:
    """
    Decorador que genera un correlation ID único para trazabilidad.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        corr_id = str(uuid.uuid4())
        with LogContext(correlation_id=corr_id):
            return func(*args, **kwargs)
            
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        corr_id = str(uuid.uuid4())
        with LogContext(correlation_id=corr_id):
            return await func(*args, **kwargs)
            
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_execution_time(logger: Optional[logging.Logger] = None,
                      level: int = logging.INFO) -> Callable[[F], F]:
    """
    Decorador que registra el tiempo de ejecución de una función.
    
    Args:
        logger: Logger a usar (opcional)
        level: Nivel de logging
        
    Returns:
        Decorador
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                log = logger or logging.getLogger(func.__module__)
                log.log(level, f"{func.__name__} ejecutado en {execution_time:.3f}s",
                       extra={'execution_time_ms': execution_time * 1000})
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log = logger or logging.getLogger(func.__module__)
                log.error(f"{func.__name__} falló después de {execution_time:.3f}s: {e}",
                         extra={'execution_time_ms': execution_time * 1000})
                raise
                
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                log = logger or logging.getLogger(func.__module__)
                log.log(level, f"{func.__name__} ejecutado en {execution_time:.3f}s",
                       extra={'execution_time_ms': execution_time * 1000})
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log = logger or logging.getLogger(func.__module__)
                log.error(f"{func.__name__} falló después de {execution_time:.3f}s: {e}",
                         extra={'execution_time_ms': execution_time * 1000})
                raise
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def log_with_context(func: F) -> F:
    """
    Decorador que agrega automáticamente contexto a los logs.
    
    Busca en las variables de contexto y las agrega como extra
    a todos los logs dentro de la función.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Construir contexto
        extra = build_log_context()
        
        # Agregar contexto al logger
        logger = logging.getLogger(func.__module__)
        for handler in logger.handlers:
            handler.addFilter(ContextFilter(extra))
            
        try:
            return func(*args, **kwargs)
        finally:
            # Remover filtro
            for handler in logger.handlers:
                for filter in handler.filters[:]:
                    if isinstance(filter, ContextFilter):
                        handler.removeFilter(filter)
                        
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Construir contexto
        extra = build_log_context()
        
        # Agregar contexto al logger
        logger = logging.getLogger(func.__module__)
        for handler in logger.handlers:
            handler.addFilter(ContextFilter(extra))
            
        try:
            return await func(*args, **kwargs)
        finally:
            # Remover filtro
            for handler in logger.handlers:
                for filter in handler.filters[:]:
                    if isinstance(filter, ContextFilter):
                        handler.removeFilter(filter)
                        
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class ContextFilter(logging.Filter):
    """Filtro que agrega contexto extra a los records."""
    
    def __init__(self, extra: Dict[str, Any]):
        """
        Inicializa el filtro.
        
        Args:
            extra: Diccionario con campos extra
        """
        super().__init__()
        self.extra = extra
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Agrega campos extra al record.
        
        Args:
            record: Record de logging
            
        Returns:
            True (siempre pasa el filtro)
        """
        for key, value in self.extra.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


def build_log_context() -> Dict[str, Any]:
    """
    Construye el contexto actual desde las variables de contexto.
    
    Returns:
        Diccionario con el contexto
    """
    context = {}
    
    # Correlation ID
    corr_id = correlation_id.get()
    if corr_id:
        context['correlation_id'] = corr_id
        
    # Contexto de usuario
    user = user_context.get()
    if user:
        context['user'] = user.get('name')
        context['user_ip'] = user.get('ip')
        
    # Contexto de cámara
    camera = camera_context.get()
    if camera:
        context['camera_id'] = camera.get('id')
        context['camera_ip'] = camera.get('ip')
        context['camera_brand'] = camera.get('brand')
        
    # Contexto de streaming
    stream = stream_context.get()
    if stream:
        context['stream_id'] = stream.get('id')
        context['protocol'] = stream.get('protocol')
        context['fps'] = stream.get('fps')
        
    # Thread info
    context['thread_id'] = threading.get_ident()
    
    return context


def set_camera_context(camera_id: str, 
                      camera_ip: Optional[str] = None,
                      brand: Optional[str] = None,
                      model: Optional[str] = None) -> None:
    """
    Establece el contexto de cámara para los logs.
    
    Args:
        camera_id: ID de la cámara
        camera_ip: IP de la cámara
        brand: Marca de la cámara
        model: Modelo de la cámara
    """
    camera_context.set({
        'id': camera_id,
        'ip': camera_ip,
        'brand': brand,
        'model': model
    })


def set_stream_context(stream_id: str,
                      protocol: Optional[str] = None,
                      fps: Optional[int] = None,
                      resolution: Optional[str] = None) -> None:
    """
    Establece el contexto de streaming para los logs.
    
    Args:
        stream_id: ID del stream
        protocol: Protocolo usado (RTSP, HTTP, etc)
        fps: Frames por segundo
        resolution: Resolución del stream
    """
    stream_context.set({
        'id': stream_id,
        'protocol': protocol,
        'fps': fps,
        'resolution': resolution
    })


def set_user_context(user_name: str,
                    user_ip: Optional[str] = None,
                    role: Optional[str] = None) -> None:
    """
    Establece el contexto de usuario para los logs.
    
    Args:
        user_name: Nombre del usuario
        user_ip: IP del usuario
        role: Rol del usuario
    """
    user_context.set({
        'name': user_name,
        'ip': user_ip,
        'role': role
    })


class LogContextManager:
    """
    Manager para gestionar contexto de logging en aplicaciones.
    
    Útil para establecer contexto global que persiste entre requests.
    """
    
    def __init__(self):
        """Inicializa el manager."""
        self._global_context: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
    def set_global_context(self, **kwargs) -> None:
        """
        Establece contexto global.
        
        Args:
            kwargs: Pares clave-valor para el contexto
        """
        with self._lock:
            self._global_context.update(kwargs)
            
    def get_global_context(self) -> Dict[str, Any]:
        """
        Obtiene el contexto global.
        
        Returns:
            Diccionario con el contexto
        """
        with self._lock:
            return self._global_context.copy()
            
    def clear_global_context(self) -> None:
        """Limpia el contexto global."""
        with self._lock:
            self._global_context.clear()
            
    def with_context(self, **kwargs) -> LogContext:
        """
        Crea un context manager con contexto adicional.
        
        Args:
            kwargs: Contexto adicional
            
        Returns:
            LogContext configurado
        """
        # Combinar contexto global con el específico
        combined_context = self._global_context.copy()
        combined_context.update(kwargs)
        return LogContext(**combined_context)


# Instancia global del manager
log_context_manager = LogContextManager()