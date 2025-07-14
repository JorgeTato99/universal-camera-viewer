#!/usr/bin/env python3
"""
Modelo de configuración de temas.

Define la estructura de datos para configuración completa de temas,
alineada con el design system del frontend.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ThemeColors:
    """Colores específicos de un tema."""
    # Colores principales
    primary: str
    secondary: str
    
    # Fondos - Jerarquía de niveles
    background: str
    paper: str
    surface: str
    sidebar: Optional[str] = None  # Solo para tema claro
    elevated: str = "#ffffff"
    
    # Estados de alerta
    error: str = "#f44336"
    warning: str = "#ff9800"
    success: str = "#4caf50"
    info: str = "#2196f3"
    
    # Texto
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_disabled: str = "#bdbdbd"
    text_hint: str = "#9e9e9e"
    
    # Bordes
    border_default: str = "#e0e0e0"
    border_focused: str = "#2196f3"
    border_error: str = "#f44336"
    
    # Sombras
    shadow_color: str = "rgba(0, 0, 0, 0.12)"
    shadow_color_dark: str = "rgba(0, 0, 0, 0.24)"


@dataclass  
class CameraStatusColors:
    """Colores para estados de cámaras."""
    connected: str = "#4caf50"
    connecting: str = "#ff9800"
    disconnected: str = "#f44336"
    streaming: str = "#2196f3"
    error: str = "#f44336"
    unavailable: str = "#9e9e9e"


@dataclass
class ThemeConfig:
    """
    Configuración completa de un tema.
    
    Contiene todos los aspectos visuales de un tema incluyendo
    colores, tipografía, espaciado, etc.
    """
    name: str
    mode: str  # "light" o "dark"
    colors: ThemeColors
    camera_status_colors: CameraStatusColors = field(default_factory=CameraStatusColors)
    
    # Configuración adicional
    font_family: str = '"Roboto", "Helvetica", "Arial", sans-serif'
    font_family_mono: str = '"Roboto Mono", "Consolas", "Monaco", monospace'
    
    # Bordes y radios
    border_radius_small: int = 4
    border_radius_medium: int = 8
    border_radius_large: int = 12
    
    # Espaciado
    spacing_unit: int = 8
    
    # Transiciones
    transition_duration: str = "200ms"
    transition_easing: str = "cubic-bezier(0.4, 0, 0.2, 1)"
    
    @classmethod
    def create_light_theme(cls) -> 'ThemeConfig':
        """Crea la configuración para el tema claro."""
        return cls(
            name="light",
            mode="light",
            colors=ThemeColors(
                # Colores principales
                primary="#2196f3",
                secondary="#4caf50",
                
                # Fondos - Jerarquía de 3 niveles
                background="#fafafa",  # Nivel 3: Fondo principal
                paper="#ffffff",       # Elementos paper
                surface="#f8f9fa",     # Nivel 1: TopBar
                sidebar="#f5f5f5",     # Nivel 2: Sidebar
                elevated="#ffffff",    # Elementos elevados
                
                # Texto
                text_primary="#212121",
                text_secondary="#757575",
                text_disabled="#bdbdbd",
                text_hint="#9e9e9e",
                
                # Bordes
                border_default="#e0e0e0",
                border_focused="#2196f3",
                border_error="#f44336",
            )
        )
    
    @classmethod
    def create_dark_theme(cls) -> 'ThemeConfig':
        """Crea la configuración para el tema oscuro."""
        return cls(
            name="dark", 
            mode="dark",
            colors=ThemeColors(
                # Colores principales
                primary="#2196f3",
                secondary="#4caf50",
                
                # Fondos - Jerarquía de 3 niveles
                background="#2a2a2a",   # Nivel 3: Fondo principal
                paper="#1a1a1a",        # Nivel 2: Sidebar
                surface="#121212",      # Nivel 1: TopBar
                elevated="#363636",     # Elementos elevados
                
                # Texto
                text_primary="#fafafa",
                text_secondary="#e0e0e0",
                text_disabled="#757575",
                text_hint="#9e9e9e",
                
                # Bordes
                border_default="#616161",
                border_focused="#42a5f5",
                border_error="#f44336",
                
                # Sombras más intensas para modo oscuro
                shadow_color="rgba(0, 0, 0, 0.3)",
                shadow_color_dark="rgba(0, 0, 0, 0.5)",
            )
        )
    
    def to_dict(self) -> Dict[str, any]:
        """Convierte la configuración a diccionario."""
        return {
            "name": self.name,
            "mode": self.mode,
            "colors": {
                "primary": self.colors.primary,
                "secondary": self.colors.secondary,
                "background": self.colors.background,
                "paper": self.colors.paper,
                "surface": self.colors.surface,
                "sidebar": self.colors.sidebar,
                "elevated": self.colors.elevated,
                "error": self.colors.error,
                "warning": self.colors.warning,
                "success": self.colors.success,
                "info": self.colors.info,
                "text_primary": self.colors.text_primary,
                "text_secondary": self.colors.text_secondary,
                "text_disabled": self.colors.text_disabled,
                "text_hint": self.colors.text_hint,
                "border_default": self.colors.border_default,
                "border_focused": self.colors.border_focused,
                "border_error": self.colors.border_error,
            },
            "camera_status_colors": {
                "connected": self.camera_status_colors.connected,
                "connecting": self.camera_status_colors.connecting,
                "disconnected": self.camera_status_colors.disconnected,
                "streaming": self.camera_status_colors.streaming,
                "error": self.camera_status_colors.error,
                "unavailable": self.camera_status_colors.unavailable,
            },
            "typography": {
                "font_family": self.font_family,
                "font_family_mono": self.font_family_mono,
            },
            "shape": {
                "border_radius_small": self.border_radius_small,
                "border_radius_medium": self.border_radius_medium,
                "border_radius_large": self.border_radius_large,
            },
            "spacing": {
                "unit": self.spacing_unit,
            },
            "transitions": {
                "duration": self.transition_duration,
                "easing": self.transition_easing,
            }
        }


# Temas predefinidos
LIGHT_THEME = ThemeConfig.create_light_theme()
DARK_THEME = ThemeConfig.create_dark_theme()


__all__ = [
    'ThemeColors',
    'CameraStatusColors', 
    'ThemeConfig',
    'LIGHT_THEME',
    'DARK_THEME',
]