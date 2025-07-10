#!/usr/bin/env python3
"""
Theme Toggle Component - Selector de tema claro/oscuro
====================================================

Componente para cambiar entre modo claro y oscuro de la aplicación.
Incluye:
- Toggle switch visual
- Iconos y etiquetas
- Integración con ThemeService
"""

import flet as ft
from typing import Optional, Callable
from ....services.theme_service import theme_service, ThemeMode


class ThemeToggle(ft.Row):
    """
    Componente para cambiar entre tema claro y oscuro.
    
    Proporciona una interfaz visual intuitiva para alternar
    entre los modos de tema disponibles.
    """
    
    def __init__(
        self,
        page: ft.Page,
        on_theme_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        Inicializa el toggle de tema.
        
        Args:
            page: Página de Flet para aplicar cambios
            on_theme_change: Callback opcional para notificar cambios
        """
        super().__init__(**kwargs)
        
        self.page = page
        self.on_theme_change = on_theme_change
        
        # Componentes
        self.theme_switch = None
        self.theme_icon = None
        self.theme_label = None
        
        # Configurar contenido
        self._build_toggle()
        
        # Configurar row
        self.spacing = 12
        self.alignment = ft.MainAxisAlignment.START
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
    
    def _build_toggle(self):
        """Construye el toggle de tema."""
        
        # Obtener estado actual
        is_dark = theme_service.is_dark_theme()
        
        # Icono de tema
        self.theme_icon = ft.Icon(
            name=ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE,
            size=20,
            color=ft.Colors.ON_SURFACE
        )
        
        # Etiqueta del tema
        self.theme_label = ft.Text(
            "Tema oscuro" if is_dark else "Tema claro",
            size=14,
            color=ft.Colors.ON_SURFACE
        )
        
        # Switch para cambiar tema
        self.theme_switch = ft.Switch(
            value=is_dark,
            on_change=self._handle_theme_change,
            active_color=ft.Colors.PRIMARY,
            inactive_track_color=ft.Colors.OUTLINE_VARIANT,
            width=48,
            height=24
        )
        
        # Agregar controles al Row
        self.controls = [
            self.theme_icon,
            self.theme_label,
            ft.Container(width=8),  # Espaciado
            self.theme_switch
        ]
    
    def _handle_theme_change(self, e):
        """Maneja el cambio de tema."""
        if self.theme_switch is None:
            return
            
        is_dark = self.theme_switch.value
        
        # Cambiar tema
        new_theme = ThemeMode.DARK if is_dark else ThemeMode.LIGHT
        if self.page is not None:
            theme_service.set_theme(new_theme, self.page)
        
        # Actualizar componentes visuales
        self._update_visual_state(is_dark)
        
        # Notificar cambio si hay callback
        if self.on_theme_change:
            self.on_theme_change(new_theme)
    
    def _update_visual_state(self, is_dark: bool):
        """Actualiza el estado visual del toggle."""
        if self.theme_icon:
            self.theme_icon.name = ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE
        
        if self.theme_label:
            self.theme_label.value = "Tema oscuro" if is_dark else "Tema claro"
        
        # Actualizar componente
        self.update()
    
    def refresh(self):
        """Refresca el estado del toggle según el tema actual."""
        is_dark = theme_service.is_dark_theme()
        
        if self.theme_switch:
            self.theme_switch.value = is_dark
        
        self._update_visual_state(is_dark)


class ThemeSelector(ft.Column):
    """
    Selector de tema más completo con opciones adicionales.
    
    Incluye:
    - Selector de tema (claro/oscuro/sistema)
    - Información sobre el tema actual
    - Opciones de personalización
    """
    
    def __init__(
        self,
        page: ft.Page,
        on_theme_change: Optional[Callable[[str], None]] = None,
        show_system_option: bool = False,
        **kwargs
    ):
        """
        Inicializa el selector de tema.
        
        Args:
            page: Página de Flet para aplicar cambios
            on_theme_change: Callback opcional para notificar cambios
            show_system_option: Si mostrar opción "Seguir sistema"
        """
        super().__init__(**kwargs)
        
        self.page = page
        self.on_theme_change = on_theme_change
        self.show_system_option = show_system_option
        
        # Configurar columna
        self.spacing = 16
        self.tight = True
        
        # Construir contenido
        self._build_selector()
    
    def _build_selector(self):
        """Construye el selector de tema."""
        current_theme = theme_service.get_current_theme()
        
        # Título
        title = ft.Text(
            "Apariencia",
            size=16,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_SURFACE
        )
        
        # Descripción
        description = ft.Text(
            "Personaliza cómo se ve la aplicación",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT
        )
        
        # RadioGroup para opciones de tema
        radio_options = [
            ft.Radio(value=ThemeMode.LIGHT, label="Tema claro"),
            ft.Radio(value=ThemeMode.DARK, label="Tema oscuro")
        ]
        
        if self.show_system_option:
            radio_options.append(
                ft.Radio(value=ThemeMode.SYSTEM, label="Seguir sistema")
            )
        
        theme_radio_group = ft.RadioGroup(
            content=ft.Column(radio_options),
            value=current_theme,
            on_change=self._handle_option_change
        )
        
        # Contenedor con información adicional
        theme_info = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHT_MODE, size=16),
                    ft.Text("Tema claro - Interfaz clara y brillante", size=12)
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.DARK_MODE, size=16),
                    ft.Text("Tema oscuro - Interfaz oscura y elegante", size=12)
                ])
            ]),
            padding=ft.padding.all(8),
            bgcolor=ft.Colors.GREY_100,
            border_radius=8
        )
        
        theme_options = [theme_radio_group, theme_info]
        
        # Agregar controles
        self.controls = [
            title,
            description,
            ft.Container(height=8),
            *theme_options
        ]
    
    def _handle_option_change(self, e):
        """Maneja el cambio de opción de tema."""
        selected_theme = e.control.value
        
        # Cambiar tema
        if self.page is not None:
            theme_service.set_theme(selected_theme, self.page)
        
        # Notificar cambio si hay callback
        if self.on_theme_change:
            self.on_theme_change(selected_theme)
    
    def refresh(self):
        """Refresca el estado del selector."""
        # Reconstruir selector con estado actual
        self.controls.clear()
        self._build_selector()
        self.update()


def create_theme_toggle(page: ft.Page, **kwargs) -> ThemeToggle:
    """
    Función helper para crear un toggle de tema.
    
    Args:
        page: Página de Flet
        **kwargs: Argumentos adicionales para el toggle
        
    Returns:
        ThemeToggle configurado
    """
    return ThemeToggle(page, **kwargs)


def create_theme_selector(page: ft.Page, **kwargs) -> ThemeSelector:
    """
    Función helper para crear un selector de tema.
    
    Args:
        page: Página de Flet
        **kwargs: Argumentos adicionales para el selector
        
    Returns:
        ThemeSelector configurado
    """
    return ThemeSelector(page, **kwargs) 