"""
Módulo de middlewares para FastAPI.

Este módulo contiene middlewares personalizados para la aplicación,
incluyendo rate limiting, logging, y manejo de errores.
"""

from .rate_limit import RateLimitMiddleware, setup_rate_limiting

__all__ = [
    "RateLimitMiddleware",
    "setup_rate_limiting",
]