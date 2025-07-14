"""
Modelos de dominio para streaming de video.

Este módulo contiene las entidades relacionadas con el streaming:
- StreamModel: Estado y configuración de un stream
- FrameModel: Datos de un frame individual
- StreamMetrics: Métricas de rendimiento
"""

from .stream_model import StreamModel, StreamStatus, StreamProtocol
from .frame_model import FrameModel, FrameMetadata
from .stream_metrics import StreamMetrics

__all__ = [
    'StreamModel',
    'StreamStatus', 
    'StreamProtocol',
    'FrameModel',
    'FrameMetadata',
    'StreamMetrics'
]