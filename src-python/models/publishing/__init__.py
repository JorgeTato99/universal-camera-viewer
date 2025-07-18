"""
Modelos de dominio para el sistema de publicación.

Exporta las clases principales para uso externo.
"""

from .publisher_models import (
    PublishStatus,
    PublishErrorType,
    PublisherProcess,
    PublishConfiguration,
    PublishResult
)
from .mediamtx_models import (
    PathInfo,
    PathList,
)

__all__ = [
    # Estados y tipos
    'PublishStatus',
    'PublishErrorType',
    
    # Modelos principales
    'PublisherProcess',
    'PublishConfiguration',
    'PublishResult',
    
    # Modelos MediaMTX
    'PathInfo',
    'PathList',
]