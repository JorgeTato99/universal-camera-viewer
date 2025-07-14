#!/usr/bin/env python3
"""
Utilidades para manejo de errores.

Proporciona decoradores y helpers para manejo consistente de errores
siguiendo las reglas de la arquitectura.
"""

import asyncio
import logging
from typing import TypeVar, Optional, Callable, Any
from functools import wraps

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from utils.exceptions import (
    CameraViewerError,
    ConnectionError,
    ConnectionTimeoutError,
    CameraConnectionError,
    StreamingError
)

T = TypeVar('T')


def handle_service_errors(
    error_message: str = "Operación fallida",
    error_code: str = "SERVICE_ERROR",
    reraise: bool = True
):
    """
    Decorator para manejo consistente de errores en servicios.
    
    Args:
        error_message: Mensaje base del error
        error_code: Código del error
        reraise: Si debe re-lanzar el error envuelto
        
    Returns:
        Función decorada con manejo de errores
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except CameraViewerError:
                # Re-lanzar errores de dominio sin modificar
                raise
            except asyncio.TimeoutError as e:
                raise ConnectionTimeoutError(
                    ip=kwargs.get('ip', 'unknown'),
                    timeout=kwargs.get('timeout', 0)
                )
            except Exception as e:
                # Manejar errores de aiohttp si está disponible
                if AIOHTTP_AVAILABLE and isinstance(e, aiohttp.ClientError):
                    raise ConnectionError(
                        message=f"{error_message}: Error de cliente HTTP - {str(e)}",
                        error_code="HTTP_CLIENT_ERROR",
                        context={'http_error': str(e), 'error_type': type(e).__name__}
                    )
                # Verificar por nombre de clase si aiohttp no está disponible
                elif type(e).__module__ == 'aiohttp' and 'ClientError' in type(e).__name__:
                    raise ConnectionError(
                        message=f"{error_message}: Error de cliente HTTP - {str(e)}",
                        error_code="HTTP_CLIENT_ERROR",
                        context={'http_error': str(e), 'error_type': type(e).__name__}
                    )
                else:
                    # No es un error de aiohttp, continuar con el manejo normal
                    raise
            except Exception as e:
                if reraise:
                    raise CameraViewerError(
                        message=f"{error_message}: {str(e)}",
                        error_code=error_code,
                        context={'original_error': str(e), 'error_type': type(e).__name__}
                    )
                else:
                    # Log y retornar valor por defecto
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
                    return None
        return wrapper
    return decorator


def handle_presenter_errors(action_name: str):
    """
    Decorator para manejo de errores en presenters.
    
    Convierte errores técnicos en mensajes amigables para el usuario.
    
    Args:
        action_name: Nombre de la acción para logging
        
    Returns:
        Función decorada con manejo de errores
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            try:
                return await func(self, *args, **kwargs)
            except CameraViewerError as e:
                # Errores del dominio - mostrar mensaje específico
                self.logger.warning(f"Error en {action_name}: {e.to_dict()}")
                if hasattr(self, '_show_user_error'):
                    self._show_user_error(e.message)
                raise
            except Exception as e:
                # Errores inesperados - mensaje genérico
                self.logger.error(f"Error inesperado en {action_name}: {e}", exc_info=True)
                if hasattr(self, '_show_user_error'):
                    self._show_user_error("Ha ocurrido un error inesperado. Por favor intente nuevamente.")
                raise CameraViewerError(
                    message=f"Error inesperado en {action_name}",
                    error_code="UNEXPECTED_ERROR",
                    context={'action': action_name, 'original_error': str(e)}
                )
        return wrapper
    return decorator


async def retry_with_backoff(
    operation: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> T:
    """
    Ejecuta operación con exponential backoff.
    
    Args:
        operation: Función async a ejecutar
        max_retries: Número máximo de reintentos
        base_delay: Delay inicial en segundos
        max_delay: Delay máximo en segundos
        exponential_base: Base para cálculo exponencial
        jitter: Si añadir jitter aleatorio
        
    Returns:
        Resultado de la operación
        
    Raises:
        La última excepción si todos los intentos fallan
    """
    import random
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            
            if attempt >= max_retries:
                break
            
            # Calcular delay con exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Añadir jitter aleatorio
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            logger = logging.getLogger(__name__)
            logger.debug(f"Reintentando operación después de {delay:.2f}s (intento {attempt + 1}/{max_retries})")
            
            await asyncio.sleep(delay)
    
    # Si llegamos aquí, todos los intentos fallaron
    raise last_exception


class CircuitBreaker:
    """
    Implementación simple de Circuit Breaker para protección de servicios.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """
        Inicializa el circuit breaker.
        
        Args:
            failure_threshold: Número de fallas antes de abrir el circuito
            recovery_timeout: Tiempo en segundos antes de intentar recuperación
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    def call(self, func: Callable[[], T]) -> T:
        """
        Ejecuta función a través del circuit breaker.
        
        Args:
            func: Función a ejecutar
            
        Returns:
            Resultado de la función
            
        Raises:
            ConnectionError si el circuito está abierto
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker en estado HALF_OPEN, intentando recuperación")
            else:
                raise ConnectionError(
                    message="Servicio temporalmente no disponible",
                    error_code="CIRCUIT_BREAKER_OPEN",
                    context={'state': self.state, 'failures': self.failure_count}
                )
        
        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si debe intentar recuperación."""
        import time
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Maneja éxito de operación."""
        if self.state == "HALF_OPEN":
            self.logger.info("Circuit breaker recuperado, volviendo a CLOSED")
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None
    
    def _on_failure(self):
        """Maneja falla de operación."""
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker ABIERTO después de {self.failure_count} fallas")
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.logger.warning("Circuit breaker vuelve a OPEN después de falla en recuperación")


__all__ = [
    'handle_service_errors',
    'handle_presenter_errors',
    'retry_with_backoff',
    'CircuitBreaker',
]