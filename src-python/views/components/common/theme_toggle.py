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
import asyncio

# Importar el presenter de tema
try:
    from ....presenters import get_theme_presenter
except ImportError:
    get_theme_presenter = None

# ThemeMode para compatibilidad
class ThemeMode:
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


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
        
        # Obtener presenter
        self.theme_presenter = get_theme_presenter() if get_theme_presenter else None
        
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
        
        # Obtener estado actual del presenter
        is_dark = self.theme_presenter.is_dark_theme() if self.theme_presenter else False
        
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
        
        # Cambiar tema a través del presenter
        new_theme = ThemeMode.DARK if is_dark else ThemeMode.LIGHT
        if self.page is not None and self.theme_presenter:
            # Usar el presenter para cambiar el tema
            import asyncio
            asyncio.create_task(self._change_theme_async(new_theme))
        
        # Actualizar componentes visuales
        self._update_visual_state(is_dark)
        
        # Notificar cambio si hay callback
        if self.on_theme_change:
            self.on_theme_change(new_theme)
    
    async def _change_theme_async(self, theme_name: str):
        """Cambia el tema de forma asíncrona a través del presenter."""
        if self.theme_presenter:
            await self.theme_presenter.set_theme(theme_name)
            await self.theme_presenter.apply_theme_to_page(self.page)
    
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
        is_dark = self.theme_presenter.is_dark_theme() if self.theme_presenter else False
        
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
        
        # Obtener presenter
        self.theme_presenter = get_theme_presenter() if get_theme_presenter else None
        
        # Configurar columna
        self.spacing = 16
        self.tight = True
        
        # Construir contenido
        self._build_selector()
    
    def _build_selector(self):
        """Construye el selector de tema."""
        current_theme = self._get_current_theme()
        
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
    
    def _get_current_theme(self) -> str:
        """Obtiene el tema actual del presenter."""
        if self.theme_presenter:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si estamos en un contexto async, usar create_task
                future = asyncio.create_task(self.theme_presenter.get_current_theme())
                # Por ahora retornar light como default
                return "light"
            else:
                # Si no hay loop corriendo, ejecutar sync
                return loop.run_until_complete(self.theme_presenter.get_current_theme())
        return "light"
    
    def _handle_option_change(self, e):
        """Maneja el cambio de opción de tema."""
        selected_theme = e.control.value
        
        # Cambiar tema a través del presenter
        if self.page is not None and self.theme_presenter:
            import asyncio
            asyncio.create_task(self._change_theme_async(selected_theme))
        
        # Notificar cambio si hay callback
        if self.on_theme_change:
            self.on_theme_change(selected_theme)
    
    async def _change_theme_async(self, theme_name: str):
        """Cambia el tema de forma asíncrona a través del presenter."""
        if self.theme_presenter:
            await self.theme_presenter.set_theme(theme_name)
            await self.theme_presenter.apply_theme_to_page(self.page)
    
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