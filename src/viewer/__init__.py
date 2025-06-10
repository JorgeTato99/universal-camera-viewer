"""
Módulo de visor en tiempo real para cámaras Dahua.
Interfaz gráfica principal del proyecto.
"""

from .real_time_viewer import RealTimeViewer
from .camera_widget import CameraWidget
from .control_panel import ControlPanel

__all__ = ["RealTimeViewer", "CameraWidget", "ControlPanel"] 