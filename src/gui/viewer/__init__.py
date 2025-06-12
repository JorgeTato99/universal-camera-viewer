"""
Módulo del visor de cámaras en tiempo real.
Contiene los componentes del visor: vista principal, widgets de cámaras y panel de control.
"""

from .real_time_viewer_view import RealTimeViewerView
from .camera_widget import CameraWidget
from .control_panel import ControlPanel

__all__ = ["RealTimeViewerView", "CameraWidget", "ControlPanel"] 