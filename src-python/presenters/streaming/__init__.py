"""
Presenters específicos para streaming de video.

Estos presenters están adaptados para trabajar con Tauri,
emitiendo eventos que el frontend puede capturar.
"""

from presenters.streaming.video_stream_presenter import VideoStreamPresenter
from presenters.streaming.tauri_event_emitter import TauriEventEmitter

__all__ = [
    'VideoStreamPresenter',
    'TauriEventEmitter'
]