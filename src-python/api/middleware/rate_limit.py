"""
Middleware de Rate Limiting para FastAPI.

Este módulo implementa protección contra abuso mediante límites de peticiones
utilizando SlowAPI. Soporta almacenamiento en memoria con arquitectura preparada
para migración a Redis.
"""

import time
import logging
import yaml
import os
from typing import Dict, Any, Optional, Callable, Tuple
from pathlib import Path
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
import asyncio
from abc import ABC, abstractmethod

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.config import settings

logger = logging.getLogger(__name__)


# === Almacenamiento de Rate Limits ===

class RateLimitStorage(ABC):
    """
    Interfaz abstracta para almacenamiento de rate limits.
    Permite cambiar entre memoria y Redis sin modificar el código.
    """
    
    @abstractmethod
    async def increment(self, key: str, window: int) -> Tuple[int, int]:
        """
        Incrementa el contador para una clave.
        
        Args:
            key: Identificador único (IP + endpoint)
            window: Ventana de tiempo en segundos
            
        Returns:
            Tuple de (count, reset_time)
        """
        pass
    
    @abstractmethod
    async def get_count(self, key: str) -> int:
        """Obtiene el contador actual para una clave."""
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> None:
        """Resetea el contador para una clave."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Limpia entradas expiradas."""
        pass


class MemoryStorage(RateLimitStorage):
    """
    Implementación de almacenamiento en memoria.
    
    ADVERTENCIA: No es compartido entre procesos/workers.
    Para producción con múltiples workers, usar RedisStorage.
    """
    
    def __init__(self, max_entries: int = 100000):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._max_entries = max_entries
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()
        
    async def increment(self, key: str, window: int) -> Tuple[int, int]:
        """Incrementa contador con ventana deslizante."""
        async with self._lock:
            now = time.time()
            
            # Limpiar si es necesario
            if now - self._last_cleanup > 300:  # 5 minutos
                await self._cleanup_expired(now)
            
            if key not in self._storage:
                self._storage[key] = {
                    'count': 1,
                    'reset_time': now + window,
                    'window': window
                }
                return 1, int(now + window)
            
            entry = self._storage[key]
            
            # Si la ventana expiró, resetear
            if now >= entry['reset_time']:
                entry['count'] = 1
                entry['reset_time'] = now + window
                return 1, int(now + window)
            
            # Incrementar contador
            entry['count'] += 1
            return entry['count'], int(entry['reset_time'])
    
    async def get_count(self, key: str) -> int:
        """Obtiene contador actual."""
        async with self._lock:
            if key not in self._storage:
                return 0
            
            entry = self._storage[key]
            if time.time() >= entry['reset_time']:
                return 0
                
            return entry['count']
    
    async def reset(self, key: str) -> None:
        """Resetea contador."""
        async with self._lock:
            if key in self._storage:
                del self._storage[key]
    
    async def cleanup(self) -> None:
        """Limpia todas las entradas expiradas."""
        async with self._lock:
            await self._cleanup_expired(time.time())
    
    async def _cleanup_expired(self, now: float) -> None:
        """Limpia entradas expiradas y previene memory leaks."""
        expired_keys = [
            key for key, entry in self._storage.items()
            if now >= entry['reset_time']
        ]
        
        for key in expired_keys:
            del self._storage[key]
        
        # Prevenir crecimiento excesivo
        if len(self._storage) > self._max_entries:
            # Eliminar las entradas más antiguas
            sorted_items = sorted(
                self._storage.items(),
                key=lambda x: x[1]['reset_time']
            )
            
            to_remove = len(self._storage) - self._max_entries
            for key, _ in sorted_items[:to_remove]:
                del self._storage[key]
        
        self._last_cleanup = now
        
        if expired_keys or to_remove > 0:
            logger.debug(
                f"Rate limit cleanup: removed {len(expired_keys)} expired, "
                f"{to_remove if 'to_remove' in locals() else 0} overflow entries"
            )


class RedisStorage(RateLimitStorage):
    """
    Implementación con Redis para escalabilidad.
    
    TODO: Implementar cuando se requiera escalabilidad horizontal.
    
    Ejemplo de implementación futura:
    ```python
    def __init__(self, redis_url: str, key_prefix: str = "rate_limit"):
        import aioredis
        self.redis = aioredis.from_url(redis_url)
        self.key_prefix = key_prefix
    
    async def increment(self, key: str, window: int) -> Tuple[int, int]:
        full_key = f"{self.key_prefix}:{key}"
        
        # Usar pipeline para operación atómica
        async with self.redis.pipeline() as pipe:
            pipe.incr(full_key)
            pipe.expire(full_key, window)
            count, _ = await pipe.execute()
            
        ttl = await self.redis.ttl(full_key)
        reset_time = int(time.time() + ttl)
        
        return count, reset_time
    ```
    """
    
    def __init__(self, redis_url: str, key_prefix: str = "rate_limit"):
        raise NotImplementedError(
            "RedisStorage no está implementado aún. "
            "Use MemoryStorage o implemente RedisStorage según el ejemplo en el docstring."
        )
    
    async def increment(self, key: str, window: int) -> Tuple[int, int]:
        raise NotImplementedError
    
    async def get_count(self, key: str) -> int:
        raise NotImplementedError
    
    async def reset(self, key: str) -> None:
        raise NotImplementedError
    
    async def cleanup(self) -> None:
        # Redis maneja TTL automáticamente
        pass


# === Configuración de Rate Limiting ===

class RateLimitConfig:
    """Gestión de configuración de rate limits desde YAML."""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "rate_limit_settings.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self) -> None:
        """Carga configuración desde archivo YAML."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                logger.info(f"Rate limit config loaded from {self.config_path}")
            else:
                logger.warning(
                    f"Rate limit config not found at {self.config_path}, "
                    "using defaults"
                )
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading rate limit config: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto si no se encuentra el archivo."""
        return {
            'development': {'enabled': True, 'multiplier': 10, 'storage': 'memory'},
            'production': {'enabled': True, 'multiplier': 1, 'storage': 'memory'},
            'limits': {
                'global': {'rate': '1000/hour', 'burst': 50},
                'read': {'rate': '100/minute', 'burst': 10},
                'write': {'rate': '10/minute', 'burst': 2},
                'camera_connect': {'rate': '5/minute', 'burst': 1},
                'network_scan': {'rate': '1/minute', 'burst': 1},
            },
            'excluded_paths': ['/health', '/docs', '/redoc', '/openapi.json'],
            'trusted_ips': ['127.0.0.1', '::1'],
        }
    
    def get_environment(self) -> str:
        """Detecta el ambiente actual."""
        # TODO: Mejorar detección de ambiente
        return 'development' if settings.reload else 'production'
    
    def get_limit(self, limit_name: str) -> Optional[str]:
        """
        Obtiene un límite específico con el multiplicador del ambiente.
        
        Args:
            limit_name: Nombre del límite (e.g., 'read', 'camera_connect')
            
        Returns:
            String de límite (e.g., '1000/minute')
        """
        env = self.get_environment()
        env_config = self._config.get(env, {})
        
        if not env_config.get('enabled', True):
            return None
        
        multiplier = env_config.get('multiplier', 1)
        limit_config = self._config.get('limits', {}).get(limit_name, {})
        
        if not limit_config:
            return None
        
        rate_str = limit_config.get('rate', '100/minute')
        
        # Parsear y aplicar multiplicador
        try:
            count, period = rate_str.split('/')
            count = int(count) * multiplier
            return f"{count}/{period}"
        except:
            logger.error(f"Invalid rate limit format: {rate_str}")
            return rate_str
    
    def get_burst(self, limit_name: str) -> int:
        """Obtiene el burst permitido para un límite."""
        limit_config = self._config.get('limits', {}).get(limit_name, {})
        return limit_config.get('burst', 1)
    
    def get_message(self, limit_name: str) -> str:
        """Obtiene mensaje personalizado para un límite."""
        limit_config = self._config.get('limits', {}).get(limit_name, {})
        return limit_config.get(
            'message',
            self._config.get('error_messages', {}).get(
                'default',
                'Límite de peticiones excedido. Por favor, intente más tarde.'
            )
        )
    
    def is_excluded(self, path: str) -> bool:
        """Verifica si un path está excluido de rate limiting."""
        excluded = self._config.get('excluded_paths', [])
        return any(path.startswith(ex) for ex in excluded)
    
    def is_trusted_ip(self, ip: str) -> bool:
        """Verifica si una IP está en la lista de confiables."""
        trusted = self._config.get('trusted_ips', [])
        return ip in trusted
    
    @property
    def storage_type(self) -> str:
        """Tipo de almacenamiento según ambiente."""
        env = self.get_environment()
        return self._config.get(env, {}).get('storage', 'memory')


# === Funciones de identificación de cliente ===

def get_client_identifier(request: Request) -> str:
    """
    Obtiene identificador único del cliente considerando proxies.
    
    Prioridad:
    1. X-Real-IP header
    2. X-Forwarded-For header (primera IP)
    3. IP directa de la conexión
    
    Args:
        request: Request de FastAPI
        
    Returns:
        IP del cliente como string
    """
    # Verificar X-Real-IP (común en Nginx)
    if real_ip := request.headers.get("X-Real-IP"):
        return real_ip.strip()
    
    # Verificar X-Forwarded-For (puede contener múltiples IPs)
    if forwarded := request.headers.get("X-Forwarded-For"):
        # Tomar la primera IP (cliente original)
        ips = [ip.strip() for ip in forwarded.split(",")]
        if ips and ips[0]:
            return ips[0]
    
    # Usar IP directa
    if request.client and request.client.host:
        return request.client.host
    
    # Fallback (no debería ocurrir)
    return "unknown"


# === Estadísticas de Rate Limiting ===

class RateLimitStats:
    """Recolección de estadísticas de rate limiting."""
    
    def __init__(self):
        self.requests_total = 0
        self.requests_blocked = 0
        self.requests_by_ip: Dict[str, int] = defaultdict(int)
        self.blocks_by_ip: Dict[str, int] = defaultdict(int)
        self.blocks_by_limit: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
        
    async def record_request(self, ip: str, blocked: bool = False, limit_name: str = None):
        """Registra una petición."""
        async with self._lock:
            self.requests_total += 1
            self.requests_by_ip[ip] += 1
            
            if blocked:
                self.requests_blocked += 1
                self.blocks_by_ip[ip] += 1
                if limit_name:
                    self.blocks_by_limit[limit_name] += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas actuales."""
        async with self._lock:
            # Top IPs por peticiones
            top_ips = sorted(
                self.requests_by_ip.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Top IPs bloqueadas
            top_blocked = sorted(
                self.blocks_by_ip.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                'total_requests': self.requests_total,
                'blocked_requests': self.requests_blocked,
                'block_rate': (
                    self.requests_blocked / self.requests_total * 100
                    if self.requests_total > 0 else 0
                ),
                'top_ips': dict(top_ips),
                'top_blocked_ips': dict(top_blocked),
                'blocks_by_limit': dict(self.blocks_by_limit),
            }
    
    async def reset(self):
        """Resetea estadísticas."""
        async with self._lock:
            self.requests_total = 0
            self.requests_blocked = 0
            self.requests_by_ip.clear()
            self.blocks_by_ip.clear()
            self.blocks_by_limit.clear()


# === Instancias globales ===

rate_limit_config = RateLimitConfig()
rate_limit_stats = RateLimitStats()

# Crear storage según configuración
if rate_limit_config.storage_type == "redis":
    # TODO: Implementar RedisStorage
    logger.warning("RedisStorage no implementado, usando MemoryStorage")
    rate_limit_storage = MemoryStorage()
else:
    rate_limit_storage = MemoryStorage()


# === Limiter principal ===

def rate_limit_key_func(request: Request) -> str:
    """Función para generar key de rate limit."""
    return get_client_identifier(request)


# Crear limiter con storage personalizado
limiter = Limiter(
    key_func=rate_limit_key_func,
    storage_uri=None  # Usaremos nuestro storage personalizado
)


# === Middleware de Rate Limiting ===

class RateLimitMiddleware:
    """
    Middleware global de rate limiting.
    
    Aplica límite global a todas las peticiones y registra estadísticas.
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.stats_task = None
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Procesa cada petición."""
        # Verificar si el path está excluido
        if rate_limit_config.is_excluded(request.url.path):
            return await call_next(request)
        
        # Obtener IP del cliente
        client_ip = get_client_identifier(request)
        
        # Verificar si es IP confiable
        if rate_limit_config.is_trusted_ip(client_ip):
            logger.debug(f"Trusted IP {client_ip}, bypassing rate limit")
            return await call_next(request)
        
        # Aplicar límite global
        limit_str = rate_limit_config.get_limit('global')
        if limit_str:
            try:
                # Verificar límite manualmente
                key = f"global:{client_ip}"
                window = self._parse_window(limit_str)
                count, reset_time = await rate_limit_storage.increment(key, window)
                limit = self._parse_limit(limit_str)
                
                # Registrar estadísticas
                blocked = count > limit
                await rate_limit_stats.record_request(
                    client_ip, 
                    blocked=blocked,
                    limit_name='global'
                )
                
                if blocked:
                    # Log detallado cuando se alcanza límite
                    logger.warning(
                        f"Rate limit exceeded: "
                        f"IP={client_ip}, "
                        f"Path={request.url.path}, "
                        f"Method={request.method}, "
                        f"Limit=global ({limit_str}), "
                        f"Count={count}/{limit}"
                    )
                    
                    return self._create_rate_limit_response(
                        limit, count, reset_time, 'global'
                    )
                
                # Agregar headers informativos
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
                response.headers["X-RateLimit-Reset"] = str(reset_time)
                response.headers["X-RateLimit-Window"] = str(window)
                
                return response
                
            except Exception as e:
                logger.error(f"Error in rate limit middleware: {e}")
                # En caso de error, permitir la petición
                return await call_next(request)
        
        return await call_next(request)
    
    def _parse_limit(self, limit_str: str) -> int:
        """Extrae el número de peticiones del string de límite."""
        try:
            count, _ = limit_str.split('/')
            return int(count)
        except:
            return 100  # Default
    
    def _parse_window(self, limit_str: str) -> int:
        """Extrae la ventana de tiempo en segundos."""
        try:
            _, period = limit_str.split('/')
            
            multipliers = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            
            for unit, mult in multipliers.items():
                if unit in period:
                    return mult
                    
            return 60  # Default: 1 minuto
        except:
            return 60
    
    def _create_rate_limit_response(
        self, 
        limit: int, 
        count: int, 
        reset_time: int,
        limit_name: str
    ) -> JSONResponse:
        """Crea respuesta 429 con información detallada."""
        retry_after = max(1, reset_time - int(time.time()))
        
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": rate_limit_config.get_message(limit_name),
                "error_code": "RATE_LIMIT_EXCEEDED",
                "detail": {
                    "limit": limit,
                    "current": count,
                    "remaining": 0,
                    "reset_at": datetime.fromtimestamp(reset_time).isoformat() + "Z",
                    "retry_after": retry_after
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
            }
        )


# === Tarea de estadísticas ===

async def log_rate_limit_stats():
    """Tarea periódica para loggear estadísticas."""
    while True:
        try:
            await asyncio.sleep(60)  # Cada minuto
            
            stats = await rate_limit_stats.get_stats()
            if stats['total_requests'] > 0:
                logger.info(
                    f"Rate limit stats: "
                    f"Total={stats['total_requests']}, "
                    f"Blocked={stats['blocked_requests']} ({stats['block_rate']:.1f}%), "
                    f"Top IPs={list(stats['top_ips'].items())[:3]}"
                )
                
                if stats['blocked_requests'] > 0:
                    logger.info(
                        f"Blocks by limit: {stats['blocks_by_limit']}, "
                        f"Top blocked IPs: {stats['top_blocked_ips']}"
                    )
            
            # Limpiar storage periódicamente
            await rate_limit_storage.cleanup()
            
        except Exception as e:
            logger.error(f"Error in stats task: {e}")


# === Setup function ===

def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configura rate limiting en la aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI
    """
    logger.info("Configurando rate limiting...")
    
    # Registrar manejador de errores 429
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Agregar middleware global
    app.add_middleware(SlowAPIMiddleware)
    
    # Agregar nuestro middleware personalizado
    # Nota: Se debe agregar después de SlowAPIMiddleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        middleware = RateLimitMiddleware(app)
        return await middleware(request, call_next)
    
    # Iniciar tarea de estadísticas
    @app.on_event("startup")
    async def start_stats_task():
        asyncio.create_task(log_rate_limit_stats())
        logger.info("Rate limiting configurado correctamente")
    
    # Limpiar al cerrar
    @app.on_event("shutdown")
    async def cleanup_rate_limiting():
        await rate_limit_storage.cleanup()
        logger.info("Rate limiting cleanup completado")