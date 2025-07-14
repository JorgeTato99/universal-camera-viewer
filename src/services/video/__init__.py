"""
Servicios de video para streaming.

Este módulo contiene los servicios necesarios para gestionar
streams de video en tiempo real.
"""

from .video_stream_service import VideoStreamService
from .stream_manager import StreamManager, StreamManagerFactory
from .frame_processor import FrameProcessor

__all__ = [
    'VideoStreamService',
    'StreamManager',
    'StreamManagerFactory',
    'FrameProcessor'
]