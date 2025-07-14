"""
Utilidades para procesamiento de video.

Este módulo contiene herramientas para:
- Conversión de frames entre formatos
- Monitoreo de performance
- Optimización de recursos
"""

from .frame_converter import (
    FrameConverter,
    FrameConversionStrategy,
    Base64JPEGStrategy,
    Base64PNGStrategy,
    BytesJPEGStrategy
)

__all__ = [
    'FrameConverter',
    'FrameConversionStrategy',
    'Base64JPEGStrategy',
    'Base64PNGStrategy',
    'BytesJPEGStrategy'
]