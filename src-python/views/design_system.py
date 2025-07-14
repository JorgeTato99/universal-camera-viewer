#!/usr/bin/env python3
"""
Design System - Sistema de Diseño Material Design 3
==================================================

Sistema de diseño centralizado que implementa Material Design 3 (Material You)
con tokens de diseño, colores semánticos, tipografía y constantes.

Basado en la guía de desarrollo UI/UX moderna.
"""

import flet as ft
from typing import Dict, Any
from dataclasses import dataclass


class MaterialColors:
    """Colores semánticos de Material Design 3."""
    
    # Colores primarios
    PRIMARY = ft.Colors.PRIMARY
    ON_PRIMARY = ft.Colors.ON_PRIMARY
    PRIMARY_CONTAINER = ft.Colors.PRIMARY_CONTAINER
    ON_PRIMARY_CONTAINER = ft.Colors.ON_PRIMARY_CONTAINER
    
    # Colores secundarios
    SECONDARY = ft.Colors.SECONDARY
    ON_SECONDARY = ft.Colors.ON_SECONDARY
    SECONDARY_CONTAINER = ft.Colors.SECONDARY_CONTAINER
    ON_SECONDARY_CONTAINER = ft.Colors.ON_SECONDARY_CONTAINER
    
    # Colores terciarios
    TERTIARY = ft.Colors.TERTIARY
    ON_TERTIARY = ft.Colors.ON_TERTIARY
    TERTIARY_CONTAINER = ft.Colors.TERTIARY_CONTAINER
    ON_TERTIARY_CONTAINER = ft.Colors.ON_TERTIARY_CONTAINER
    
    # Colores de superficie
    SURFACE = ft.Colors.SURFACE
    ON_SURFACE = ft.Colors.ON_SURFACE
    SURFACE_VARIANT = ft.Colors.GREY_100
    ON_SURFACE_VARIANT = ft.Colors.ON_SURFACE
    
    # Colores de estado semánticos
    ERROR = ft.Colors.ERROR
    ON_ERROR = ft.Colors.ON_ERROR
    ERROR_CONTAINER = ft.Colors.ERROR_CONTAINER
    ON_ERROR_CONTAINER = ft.Colors.ON_ERROR_CONTAINER
    
    # Colores de outline
    OUTLINE = ft.Colors.OUTLINE
    OUTLINE_VARIANT = ft.Colors.OUTLINE_VARIANT
    
    # Colores de sombra
    SHADOW = ft.Colors.SHADOW
    SCRIM = ft.Colors.SCRIM


class SemanticColors:
    """Colores semánticos para estados de la aplicación."""
    
    # Estados de conexión
    SUCCESS = MaterialColors.PRIMARY
    SUCCESS_CONTAINER = MaterialColors.PRIMARY_CONTAINER
    ON_SUCCESS = MaterialColors.ON_PRIMARY
    ON_SUCCESS_CONTAINER = MaterialColors.ON_PRIMARY_CONTAINER
    
    # Estados de advertencia
    WARNING = MaterialColors.TERTIARY
    WARNING_CONTAINER = MaterialColors.TERTIARY_CONTAINER
    ON_WARNING = MaterialColors.ON_TERTIARY
    ON_WARNING_CONTAINER = MaterialColors.ON_TERTIARY_CONTAINER
    
    # Estados de error
    ERROR = MaterialColors.ERROR
    ERROR_CONTAINER = MaterialColors.ERROR_CONTAINER
    ON_ERROR = MaterialColors.ON_ERROR
    ON_ERROR_CONTAINER = MaterialColors.ON_ERROR_CONTAINER
    
    # Estados informativos
    INFO = MaterialColors.SECONDARY
    INFO_CONTAINER = MaterialColors.SECONDARY_CONTAINER
    ON_INFO = MaterialColors.ON_SECONDARY
    ON_INFO_CONTAINER = MaterialColors.ON_SECONDARY_CONTAINER


class Typography:
    """Jerarquía tipográfica Material Design 3."""
    
    DISPLAY_LARGE = {"size": 57, "weight": ft.FontWeight.W_400}
    DISPLAY_MEDIUM = {"size": 45, "weight": ft.FontWeight.W_400}
    DISPLAY_SMALL = {"size": 36, "weight": ft.FontWeight.W_400}
    
    HEADLINE_LARGE = {"size": 32, "weight": ft.FontWeight.W_600}
    HEADLINE_MEDIUM = {"size": 28, "weight": ft.FontWeight.W_600}
    HEADLINE_SMALL = {"size": 24, "weight": ft.FontWeight.W_600}
    
    TITLE_LARGE = {"size": 22, "weight": ft.FontWeight.W_500}
    TITLE_MEDIUM = {"size": 16, "weight": ft.FontWeight.W_500}
    TITLE_SMALL = {"size": 14, "weight": ft.FontWeight.W_500}
    
    BODY_LARGE = {"size": 16, "weight": ft.FontWeight.W_400}
    BODY_MEDIUM = {"size": 14, "weight": ft.FontWeight.W_400}
    BODY_SMALL = {"size": 12, "weight": ft.FontWeight.W_400}
    
    LABEL_LARGE = {"size": 14, "weight": ft.FontWeight.W_500}
    LABEL_MEDIUM = {"size": 12, "weight": ft.FontWeight.W_500}
    LABEL_SMALL = {"size": 11, "weight": ft.FontWeight.W_500}


class BorderRadius:
    """Bordes redondeados Material Design 3."""
    
    NONE = 0
    EXTRA_SMALL = 4
    SMALL = 8
    MEDIUM = 12
    LARGE = 16
    EXTRA_LARGE = 28
    FULL = 50


class Elevation:
    """Niveles de elevación Material Design 3."""
    
    SURFACE = 0      # Superficie base
    LEVEL_1 = 1      # Cards y elementos
    LEVEL_2 = 2      # Barras de navegación
    LEVEL_3 = 3      # Botones flotantes
    LEVEL_4 = 4      # Navigation drawer
    LEVEL_5 = 5      # Diálogos y modales


class Spacing:
    """Sistema de espaciado consistente."""
    
    NONE = 0
    EXTRA_SMALL = 4
    SMALL = 8
    MEDIUM = 12
    LARGE = 16
    EXTRA_LARGE = 20
    XXL = 24
    XXXL = 32


class Breakpoints:
    """Breakpoints para responsive design."""
    
    MOBILE = 480
    TABLET = 768
    DESKTOP = 1024
    WIDE = 1440


@dataclass
class ElevationStyle:
    """Configuración de elevación con sombra."""
    level: int
    blur_radius: int
    spread_radius: int
    offset_y: int
    opacity: float


class MaterialElevation:
    """Sistema de elevación Material Design 3."""
    
    LEVELS = {
        Elevation.SURFACE: ElevationStyle(0, 0, 0, 0, 0.0),
        Elevation.LEVEL_1: ElevationStyle(1, 2, 0, 1, 0.05),
        Elevation.LEVEL_2: ElevationStyle(2, 4, 0, 2, 0.08),
        Elevation.LEVEL_3: ElevationStyle(3, 6, 0, 3, 0.10),
        Elevation.LEVEL_4: ElevationStyle(4, 8, 0, 4, 0.12),
        Elevation.LEVEL_5: ElevationStyle(5, 12, 0, 6, 0.15)
    }
    
    @staticmethod
    def create_shadow(elevation_level: int) -> ft.BoxShadow | None:
        """Crea sombra según nivel de elevación."""
        if elevation_level not in MaterialElevation.LEVELS:
            elevation_level = Elevation.SURFACE
            
        style = MaterialElevation.LEVELS[elevation_level]
        
        if style.level == 0:
            return None
        
        return ft.BoxShadow(
            spread_radius=style.spread_radius,
            blur_radius=style.blur_radius,
            color=ft.Colors.with_opacity(style.opacity, MaterialColors.SHADOW),
            offset=ft.Offset(0, style.offset_y)
        )


def create_text(
    text: str,
    style: str = "body_medium",
    color: str | None = None,
    **kwargs
) -> ft.Text:
    """
    Crea texto con tipografía Material Design 3.
    
    Args:
        text: Texto a mostrar
        style: Estilo tipográfico (ej: "headline_large")
        color: Color del texto (opcional)
        **kwargs: Argumentos adicionales para ft.Text
    """
    text_color = color if color is not None else MaterialColors.ON_SURFACE
    style_name = style.upper()
    
    if hasattr(Typography, style_name):
        typography = getattr(Typography, style_name)
        return ft.Text(
            text,
            size=typography["size"],
            weight=typography["weight"],
            color=text_color,
            **kwargs
        )
    else:
        # Fallback a body_medium
        return ft.Text(
            text,
            size=Typography.BODY_MEDIUM["size"],
            weight=Typography.BODY_MEDIUM["weight"],
            color=text_color,
            **kwargs
        )


def get_screen_size(page_width: int) -> str:
    """Determina el tamaño de pantalla según breakpoints."""
    if page_width < Breakpoints.MOBILE:
        return "mobile"
    elif page_width < Breakpoints.TABLET:
        return "tablet"
    elif page_width < Breakpoints.DESKTOP:
        return "desktop"
    else:
        return "wide"


def create_semantic_color_scheme(scheme_type: str) -> Dict[str, Any]:
    """
    Crea esquema de colores semántico.
    
    Args:
        scheme_type: Tipo de esquema ("primary", "success", "warning", "error", "info")
    """
    schemes = {
        "primary": {
            "main": MaterialColors.PRIMARY,
            "container": MaterialColors.PRIMARY_CONTAINER,
            "on_main": MaterialColors.ON_PRIMARY,
            "on_container": MaterialColors.ON_PRIMARY_CONTAINER
        },
        "secondary": {
            "main": MaterialColors.SECONDARY,
            "container": MaterialColors.SECONDARY_CONTAINER,
            "on_main": MaterialColors.ON_SECONDARY,
            "on_container": MaterialColors.ON_SECONDARY_CONTAINER
        },
        "tertiary": {
            "main": MaterialColors.TERTIARY,
            "container": MaterialColors.TERTIARY_CONTAINER,
            "on_main": MaterialColors.ON_TERTIARY,
            "on_container": MaterialColors.ON_TERTIARY_CONTAINER
        },
        "success": {
            "main": SemanticColors.SUCCESS,
            "container": SemanticColors.SUCCESS_CONTAINER,
            "on_main": SemanticColors.ON_SUCCESS,
            "on_container": SemanticColors.ON_SUCCESS_CONTAINER
        },
        "warning": {
            "main": SemanticColors.WARNING,
            "container": SemanticColors.WARNING_CONTAINER,
            "on_main": SemanticColors.ON_WARNING,
            "on_container": SemanticColors.ON_WARNING_CONTAINER
        },
        "error": {
            "main": SemanticColors.ERROR,
            "container": SemanticColors.ERROR_CONTAINER,
            "on_main": SemanticColors.ON_ERROR,
            "on_container": SemanticColors.ON_ERROR_CONTAINER
        },
        "info": {
            "main": SemanticColors.INFO,
            "container": SemanticColors.INFO_CONTAINER,
            "on_main": SemanticColors.ON_INFO,
            "on_container": SemanticColors.ON_INFO_CONTAINER
        },
        "surface": {
            "main": MaterialColors.SURFACE,
            "container": MaterialColors.SURFACE_VARIANT,
            "on_main": MaterialColors.ON_SURFACE,
            "on_container": MaterialColors.ON_SURFACE_VARIANT
        }
    }
    
    return schemes.get(scheme_type, schemes["primary"])


# Alias para facilidad de uso
MD3 = MaterialColors
Typo = Typography
Radius = BorderRadius
Space = Spacing 