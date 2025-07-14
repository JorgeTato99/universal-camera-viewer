#!/usr/bin/env python3
"""
Progress Indicators - Indicadores de progreso modernos con Material Design 3
============================================================================

Componentes para mostrar progreso de operaciones:
- ModernProgressBar: Barra de progreso lineal
- ModernProgressRing: Indicador circular
- Estados determinados e indeterminados
- Colores semánticos y animaciones fluidas
"""

import flet as ft
from typing import Optional, Union, List


class ModernProgressBar(ft.Container):
    """
    Barra de progreso moderna con Material Design 3.
    
    Soporta modo determinado (con valor) e indeterminado (animación continua).
    """
    
    def __init__(
        self,
        value: Optional[float] = None,  # None para indeterminado, 0.0-1.0 para determinado
        label: Optional[str] = None,
        show_percentage: bool = False,
        color_scheme: str = "primary",
        width: Optional[int] = None,
        height: int = 6,
        **kwargs
    ):
        """
        Inicializa la barra de progreso moderna.
        
        Args:
            value: Valor del progreso (0.0-1.0) o None para indeterminado
            label: Etiqueta descriptiva opcional
            show_percentage: Mostrar porcentaje numérico
            color_scheme: Esquema de color
            width: Ancho específico
            height: Alto de la barra
        """
        super().__init__(**kwargs)
        
        self.value = value
        self.label = label
        self.show_percentage = show_percentage
        self.color_scheme = color_scheme
        self.bar_height = height
        
        # Configurar contenido
        colors = self._get_color_scheme()
        self.content = self._build_progress_content(colors)
        
        # Configurar container
        self.width = width
        self.padding = ft.padding.symmetric(vertical=8)
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema especificado."""
        schemes = {
            "primary": {
                "main": ft.Colors.PRIMARY,
                "container": ft.Colors.PRIMARY_CONTAINER
            },
            "secondary": {
                "main": ft.Colors.SECONDARY,
                "container": ft.Colors.SECONDARY_CONTAINER
            },
            "success": {
                "main": ft.Colors.GREEN_600,
                "container": ft.Colors.GREEN_100
            },
            "warning": {
                "main": ft.Colors.ORANGE_600,
                "container": ft.Colors.ORANGE_100
            },
            "error": {
                "main": ft.Colors.RED_600,
                "container": ft.Colors.RED_100
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_progress_content(self, colors: dict) -> ft.Column:
        """Construye el contenido del indicador de progreso."""
        
        content_items = []
        
        # Header con label y porcentaje (si aplica)
        if self.label or (self.show_percentage and self.value is not None):
            header_items = []
            
            if self.label:
                header_items.append(
                    ft.Text(
                        self.label,
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE
                    )
                )
            
            if self.show_percentage and self.value is not None:
                percentage_text = ft.Text(
                    f"{self.value * 100:.0f}%",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=colors["main"]
                )
                
                if self.label:
                    # Agregar spacer y porcentaje a la derecha
                    header_items.extend([ft.Container(expand=True), percentage_text])
                else:
                    header_items.append(percentage_text)
            
            header = ft.Row(header_items, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            content_items.extend([header, ft.Container(height=8)])
        
        # Barra de progreso principal
        progress_bar = ft.ProgressBar(
            value=self.value,
            color=colors["main"],
            bgcolor=colors["container"],
            height=self.bar_height,
            border_radius=self.bar_height // 2,
            # Animación para modo indeterminado
            semantics_label=self.label
        )
        
        # Container con sombra sutil para la barra
        progress_container = ft.Container(
            content=progress_bar,
            border_radius=self.bar_height // 2,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=2,
                color=ft.Colors.with_opacity(0.15, colors["main"]),
                offset=ft.Offset(0, 1)
            )
        )
        
        content_items.append(progress_container)
        
        return ft.Column(content_items, spacing=0, tight=True)
    
    def update_progress(self, new_value: Optional[float], new_label: Optional[str] = None):
        """Actualiza el progreso mostrado."""
        self.value = new_value
        if new_label is not None:
            self.label = new_label
        
        # Reconstruir contenido
        colors = self._get_color_scheme()
        self.content = self._build_progress_content(colors)


class ModernProgressRing(ft.Container):
    """
    Indicador de progreso circular moderno con Material Design 3.
    """
    
    def __init__(
        self,
        value: Optional[float] = None,  # None para indeterminado
        size: int = 48,
        stroke_width: int = 4,
        color_scheme: str = "primary",
        show_percentage: bool = False,
        **kwargs
    ):
        """
        Inicializa el indicador circular.
        
        Args:
            value: Valor del progreso (0.0-1.0) o None para indeterminado
            size: Tamaño del indicador
            stroke_width: Grosor del anillo
            color_scheme: Esquema de color
            show_percentage: Mostrar porcentaje en el centro
        """
        super().__init__(**kwargs)
        
        self.value = value
        self.size = size
        self.stroke_width = stroke_width
        self.color_scheme = color_scheme
        self.show_percentage = show_percentage
        
        # Configurar contenido
        colors = self._get_color_scheme()
        self.content = self._build_ring_content(colors)
        
        # Configurar container
        self.width = size
        self.height = size
        self.alignment = ft.alignment.center
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema especificado."""
        schemes = {
            "primary": {
                "main": ft.Colors.PRIMARY,
                "container": ft.Colors.PRIMARY_CONTAINER
            },
            "secondary": {
                "main": ft.Colors.SECONDARY,
                "container": ft.Colors.SECONDARY_CONTAINER
            },
            "success": {
                "main": ft.Colors.GREEN_600,
                "container": ft.Colors.GREEN_100
            },
            "warning": {
                "main": ft.Colors.ORANGE_600,
                "container": ft.Colors.ORANGE_100
            },
            "error": {
                "main": ft.Colors.RED_600,
                "container": ft.Colors.RED_100
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_ring_content(self, colors: dict) -> ft.Stack:
        """Construye el contenido del indicador circular."""
        
        # Progress ring base
        progress_ring = ft.ProgressRing(
            value=self.value,
            color=colors["main"],
            bgcolor=colors["container"],
            width=self.size,
            height=self.size,
            stroke_width=self.stroke_width
        )
        
        # Lista de controles para el Stack
        stack_controls: List[ft.Control] = [progress_ring]
        
        # Texto de porcentaje en el centro (si está habilitado y hay valor)
        if self.show_percentage and self.value is not None:
            percentage_text = ft.Text(
                f"{self.value * 100:.0f}%",
                size=self.size // 4,  # Tamaño proporcional
                weight=ft.FontWeight.W_600,
                color=colors["main"],
                text_align=ft.TextAlign.CENTER
            )
            percentage_container = ft.Container(
                content=percentage_text,
                alignment=ft.alignment.center,
                width=self.size,
                height=self.size
            )
            stack_controls.append(percentage_container)
        
        return ft.Stack(stack_controls)
    
    def update_progress(self, new_value: Optional[float]):
        """Actualiza el progreso del anillo."""
        self.value = new_value
        
        # Reconstruir contenido
        colors = self._get_color_scheme()
        self.content = self._build_ring_content(colors)


class ProgressWithSteps(ft.Container):
    """
    Indicador de progreso por pasos/etapas.
    """
    
    def __init__(
        self,
        steps: list[str],
        current_step: int = 0,
        color_scheme: str = "primary",
        **kwargs
    ):
        """
        Inicializa el indicador de pasos.
        
        Args:
            steps: Lista de nombres de pasos
            current_step: Paso actual (índice base 0)
            color_scheme: Esquema de color
        """
        super().__init__(**kwargs)
        
        self.steps = steps
        self.current_step = current_step
        self.color_scheme = color_scheme
        
        # Configurar contenido
        colors = self._get_color_scheme()
        self.content = self._build_steps_content(colors)
        
        # Configurar container
        self.padding = ft.padding.symmetric(vertical=16)
    
    def _get_color_scheme(self) -> dict:
        """Obtiene colores según el esquema especificado."""
        schemes = {
            "primary": {
                "main": ft.Colors.PRIMARY,
                "container": ft.Colors.PRIMARY_CONTAINER,
                "on_container": ft.Colors.ON_PRIMARY_CONTAINER
            }
        }
        
        return schemes.get(self.color_scheme, schemes["primary"])
    
    def _build_steps_content(self, colors: dict) -> ft.Row:
        """Construye el contenido de pasos."""
        
        step_items = []
        
        for i, step_name in enumerate(self.steps):
            # Determinar estado del paso
            if i < self.current_step:
                # Completado
                step_color = ft.Colors.GREEN_600
                step_bg = ft.Colors.GREEN_100
                icon = ft.Icons.CHECK
            elif i == self.current_step:
                # Actual
                step_color = colors["main"]
                step_bg = colors["container"]
                icon = str(i + 1)
            else:
                # Pendiente
                step_color = ft.Colors.ON_SURFACE_VARIANT
                step_bg = ft.Colors.GREY_100
                icon = str(i + 1)
            
            # Círculo del paso
            step_circle = ft.Container(
                content=ft.Text(
                    icon if isinstance(icon, str) else "",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=step_color
                ) if isinstance(icon, str) else ft.Icon(
                    icon,
                    color=step_color,
                    size=16
                ),
                bgcolor=step_bg,
                border_radius=16,
                width=32,
                height=32,
                alignment=ft.alignment.center
            )
            
            # Texto del paso
            step_text = ft.Text(
                step_name,
                size=12,
                color=step_color,
                text_align=ft.TextAlign.CENTER
            )
            
            # Columna con círculo y texto
            step_column = ft.Column([
                step_circle,
                ft.Container(height=8),
                step_text
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True
            )
            
            step_items.append(step_column)
            
            # Línea conectora (excepto en el último paso)
            if i < len(self.steps) - 1:
                line_color = colors["main"] if i < self.current_step else ft.Colors.GREY_300
                connector = ft.Container(
                    height=2,
                    bgcolor=line_color,
                    expand=True,
                    margin=ft.margin.only(top=16)  # Alinear con círculos
                )
                step_items.append(connector)
        
        return ft.Row(
            step_items,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            tight=False
        )
    
    def next_step(self):
        """Avanza al siguiente paso."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_content()
    
    def previous_step(self):
        """Retrocede al paso anterior."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_content()
    
    def set_step(self, step_index: int):
        """Establece un paso específico."""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self._update_content()
    
    def _update_content(self):
        """Actualiza el contenido del indicador."""
        colors = self._get_color_scheme()
        self.content = self._build_steps_content(colors) 