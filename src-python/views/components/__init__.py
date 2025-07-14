"""
Components - Componentes UI Reutilizables
========================================

Componentes modulares y reutilizables implementados con Flet + Material Design 3.
Organizados por categoría y responsabilidad para facilitar mantenimiento.

Estructura:
- common/: Componentes básicos (botones, cards, indicadores)
- layout/: Componentes de layout (toolbar, panels, grids) 
- navigation/: Componentes de navegación
"""

# Componentes comunes básicos
from .common.modern_button import ModernButton, ModernIconButton
from .common.stat_card import StatCard
from .common.progress_indicator import ModernProgressBar, ModernProgressRing

# Componentes de layout
from .toolbar import ModernToolbar, ToolbarAction, SearchToolbar
from .side_panel import SidePanel, SidePanelItem, CollapsibleSidePanel
from .camera_grid import CameraGrid, CameraCard, CameraInfo, CameraStatus
from .status_bar import StatusBar, StatusItem, StatusLevel, NetworkStatusBar, PerformanceStatusBar

# Navegación
from .navigation_bar import ModernNavigationBar

__all__ = [
    # Common components
    "ModernButton",
    "ModernIconButton", 
    "StatCard",
    "ModernProgressBar",
    "ModernProgressRing",
    
    # Layout components
    "ModernToolbar",
    "ToolbarAction",
    "SearchToolbar",
    "SidePanel",
    "SidePanelItem",
    "CollapsibleSidePanel",
    "CameraGrid",
    "CameraCard",
    "CameraInfo",
    "CameraStatus",
    "StatusBar",
    "StatusItem",
    "StatusLevel",
    "NetworkStatusBar",
    "PerformanceStatusBar",
    
    # Navigation
    "ModernNavigationBar"
] 