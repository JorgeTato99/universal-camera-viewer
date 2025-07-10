#!/usr/bin/env python3
"""
AnalyticsPage - Página de análisis y estadísticas
================================================

Página para mostrar estadísticas y análisis de la actividad de las cámaras.
"""

import flet as ft
from typing import Optional, Callable


class AnalyticsPage(ft.Container):
    """Página de análisis y estadísticas."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.content = self._build_page_content()
        self.expand = True
        self.bgcolor = ft.Colors.GREY_50
    
    def _build_page_content(self) -> ft.Container:
        """Construye el contenido de la página."""
        
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.ANALYTICS,
                    size=80,
                    color=ft.Colors.PRIMARY
                ),
                ft.Container(height=24),
                ft.Text(
                    "Análisis y Estadísticas",
                    size=24,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=16),
                ft.Text(
                    "Próximamente: Estadísticas de uso, análisis de conexiones y métricas de rendimiento",
                    size=16,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            expand=True,
            padding=ft.padding.all(32),
            alignment=ft.alignment.center
        ) 