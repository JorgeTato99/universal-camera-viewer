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
from .metrics_models import (
    # Enums
    StreamStatus,
    TerminationReason,
    
    # Modelos de métricas
    PublishMetrics,
    PublishingHistorySession,
    MediaMTXPath,
    
    # Modelos de estadísticas
    CameraActivity,
    PublishingStatistics,
    
    # Modelos de analytics
    GeographicDistribution,
    ViewerAnalytics,
    
    # Funciones auxiliares
    calculate_metrics_summary,
    aggregate_camera_activities,
)

__all__ = [
    # Estados y tipos
    'PublishStatus',
    'PublishErrorType',
    'StreamStatus',
    'TerminationReason',
    
    # Modelos principales
    'PublisherProcess',
    'PublishConfiguration',
    'PublishResult',
    
    # Modelos MediaMTX
    'PathInfo',
    'PathList',
    'MediaMTXPath',
    
    # Modelos de métricas
    'PublishMetrics',
    'PublishingHistorySession',
    
    # Modelos de estadísticas
    'CameraActivity',
    'PublishingStatistics',
    
    # Modelos de analytics
    'GeographicDistribution',
    'ViewerAnalytics',
    
    # Funciones auxiliares
    'calculate_metrics_summary',
    'aggregate_camera_activities',
]