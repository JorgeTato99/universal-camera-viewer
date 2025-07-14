"""
Presenter para gestión de temas de la aplicación.

Este presenter coordina las operaciones de tema entre la vista y el servicio,
manteniendo la separación de responsabilidades del patrón MVP.
"""

import logging
from typing import Dict, Any, Optional, Callable
import flet as ft

from presenters.base_presenter import BasePresenter
from services.theme_service import theme_service


class ThemePresenter(BasePresenter):
    """
    Presenter para la gestión de temas de la interfaz.
    
    Coordina entre las vistas de tema (ThemeToggle, NavigationBar, etc.)
    y el ThemeService, asegurando que las vistas no accedan directamente
    al servicio.
    """
    
    def __init__(self):
        """Inicializa el presenter de temas."""
        super().__init__()
        self._theme_service = theme_service
        self._current_theme: Optional[str] = None
        self._theme_change_callbacks: list[Callable[[str], None]] = []
        
    async def _initialize_presenter(self) -> None:
        """Inicialización específica del presenter."""
        self.logger.info("Inicializando ThemePresenter")
        
        # Cargar tema actual
        self._current_theme = self._theme_service.current_theme
        
        # Por ahora no hay suscripción a eventos del servicio
        # TODO: Implementar cuando theme_service tenga sistema de eventos
        
    async def _cleanup_presenter(self) -> None:
        """Limpieza específica del presenter."""
        self.logger.info("Limpiando ThemePresenter")
        
        # Por ahora no hay desuscripción necesaria
        pass
        
    # === MANEJO DE ACCIONES DE LA VISTA ===
    
    async def _handle_view_action(self, action: str, params: Dict[str, Any]) -> None:
        """
        Maneja acciones desde la vista.
        
        Args:
            action: Nombre de la acción
            params: Parámetros de la acción
        """
        try:
            if action == "toggle_theme":
                await self._toggle_theme()
            elif action == "set_theme":
                await self._set_theme(params.get("theme", "light"))
            elif action == "get_current_theme":
                await self._get_current_theme()
            elif action == "get_theme_config":
                await self._get_theme_config()
            else:
                self.logger.warning(f"Acción no reconocida: {action}")
                
        except Exception as e:
            self.logger.error(f"Error manejando acción {action}: {e}")
            await self._handle_error(e)
    
    # === OPERACIONES DE TEMA ===
    
    async def toggle_theme(self) -> None:
        """Alterna entre tema claro y oscuro."""
        await self._handle_view_action("toggle_theme", {})
    
    async def set_theme(self, theme_name: str) -> None:
        """
        Establece un tema específico.
        
        Args:
            theme_name: Nombre del tema ('light' o 'dark')
        """
        await self._handle_view_action("set_theme", {"theme": theme_name})
    
    async def get_current_theme(self) -> str:
        """
        Obtiene el tema actual.
        
        Returns:
            Nombre del tema actual
        """
        return self._current_theme or "light"
    
    async def get_theme_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración completa del tema actual.
        
        Returns:
            Diccionario con la configuración del tema
        """
        # Por ahora retornar configuración básica
        return self.get_theme_colors()
    
    # === MÉTODOS PRIVADOS ===
    
    async def _toggle_theme(self) -> None:
        """Implementación de alternar tema."""
        try:
            new_theme = "dark" if self._current_theme == "light" else "light"
            await self._set_theme(new_theme)
            
        except Exception as e:
            self.logger.error(f"Error alternando tema: {e}")
            raise
    
    async def _set_theme(self, theme_name: str) -> None:
        """
        Implementación de establecer tema.
        
        Args:
            theme_name: Nombre del tema
        """
        try:
            if theme_name not in ["light", "dark"]:
                raise ValueError(f"Tema inválido: {theme_name}")
            
            if theme_name == self._current_theme:
                self.logger.debug(f"Tema {theme_name} ya está activo")
                return
            
            # Cambiar tema en el servicio
            self._theme_service.apply_theme(theme_name)
            self._current_theme = theme_name
            
            # Notificar a las vistas
            await self._notify_theme_changed(theme_name)
            
            self.logger.info(f"Tema cambiado a: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Error estableciendo tema {theme_name}: {e}")
            raise
    
    async def _get_current_theme(self) -> None:
        """Implementación de obtener tema actual."""
        # Este método es síncrono, retorna directamente
        return self._current_theme
    
    async def _get_theme_config(self) -> Dict[str, Any]:
        """Implementación de obtener configuración del tema."""
        return self.get_theme_colors()
    
    # === CALLBACKS Y NOTIFICACIONES ===
    
    def _on_theme_changed(self, theme_name: str) -> None:
        """
        Callback cuando el tema cambia en el servicio.
        
        Args:
            theme_name: Nombre del nuevo tema
        """
        if theme_name and theme_name != self._current_theme:
            self._current_theme = theme_name
            # Notificar a las vistas de forma asíncrona
            import asyncio
            asyncio.create_task(self._notify_theme_changed(theme_name))
    
    async def _notify_theme_changed(self, theme_name: str) -> None:
        """
        Notifica a todas las vistas del cambio de tema.
        
        Args:
            theme_name: Nuevo tema
        """
        # Notificar a callbacks registrados
        for callback in self._theme_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(theme_name)
                else:
                    callback(theme_name)
            except Exception as e:
                self.logger.error(f"Error en callback de cambio de tema: {e}")
        
        # Emitir evento para vistas
        await self._emit_view_event("theme_changed", {"theme": theme_name})
    
    # === REGISTRO DE CALLBACKS ===
    
    def on_theme_change(self, callback: Callable[[str], None]) -> None:
        """
        Registra un callback para cambios de tema.
        
        Args:
            callback: Función a llamar cuando cambie el tema
        """
        if callback not in self._theme_change_callbacks:
            self._theme_change_callbacks.append(callback)
    
    def remove_theme_change_callback(self, callback: Callable[[str], None]) -> None:
        """
        Elimina un callback de cambio de tema.
        
        Args:
            callback: Función a eliminar
        """
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)
    
    # === MÉTODOS DE UTILIDAD ===
    
    def is_dark_theme(self) -> bool:
        """
        Verifica si el tema actual es oscuro.
        
        Returns:
            True si el tema es oscuro
        """
        return self._current_theme == "dark"
    
    def get_theme_colors(self) -> Dict[str, str]:
        """
        Obtiene los colores del tema actual.
        
        Alineado con el design system del frontend en src/design-system/tokens.ts
        
        Returns:
            Diccionario con colores del tema
        """
        # Configuración de colores alineada con el frontend
        if self._current_theme == "dark":
            return {
                # Colores principales
                "primary": "#2196f3",  # colorTokens.primary[500]
                "secondary": "#4caf50",  # colorTokens.secondary[500]
                
                # Fondos - Jerarquía de 3 niveles
                "background": "#2a2a2a",  # colorTokens.background.dark
                "paper": "#1a1a1a",  # colorTokens.background.darkPaper
                "surface": "#121212",  # colorTokens.background.darkSurface
                "elevated": "#363636",  # colorTokens.background.darkElevated
                
                # Estados de alerta
                "error": "#f44336",  # colorTokens.alert.error
                "warning": "#ff9800",  # colorTokens.alert.warning
                "success": "#4caf50",  # colorTokens.alert.success
                "info": "#2196f3",  # colorTokens.alert.info
                
                # Texto
                "text_primary": "#fafafa",  # colorTokens.neutral[50]
                "text_secondary": "#e0e0e0",  # colorTokens.neutral[300]
                "text_disabled": "#757575",  # colorTokens.neutral[600]
                
                # Bordes
                "border_default": "#616161",  # colorTokens.neutral[700]
                "border_focused": "#42a5f5",  # colorTokens.primary[400]
            }
        else:
            return {
                # Colores principales
                "primary": "#2196f3",  # colorTokens.primary[500]
                "secondary": "#4caf50",  # colorTokens.secondary[500]
                
                # Fondos - Jerarquía de 3 niveles  
                "background": "#fafafa",  # colorTokens.background.light
                "paper": "#ffffff",  # colorTokens.background.paper
                "surface": "#f8f9fa",  # colorTokens.background.surface
                "sidebar": "#f5f5f5",  # colorTokens.background.lightSidebar
                "elevated": "#ffffff",  # colorTokens.background.lightElevated
                
                # Estados de alerta
                "error": "#f44336",  # colorTokens.alert.error
                "warning": "#ff9800",  # colorTokens.alert.warning
                "success": "#4caf50",  # colorTokens.alert.success
                "info": "#2196f3",  # colorTokens.alert.info
                
                # Texto
                "text_primary": "#212121",  # colorTokens.neutral[900]
                "text_secondary": "#757575",  # colorTokens.neutral[600]
                "text_disabled": "#bdbdbd",  # colorTokens.neutral[400]
                
                # Bordes
                "border_default": "#e0e0e0",  # colorTokens.neutral[300]
                "border_focused": "#2196f3",  # colorTokens.primary[500]
            }
    
    def get_camera_status_colors(self) -> Dict[str, str]:
        """
        Obtiene los colores de estado de cámaras.
        
        Alineado con CAMERA_STATUS_COLORS del frontend.
        
        Returns:
            Diccionario con colores por estado
        """
        return {
            "connected": "#4caf50",  # colorTokens.status.connected
            "connecting": "#ff9800",  # colorTokens.status.connecting  
            "disconnected": "#f44336",  # colorTokens.status.disconnected
            "streaming": "#2196f3",  # colorTokens.status.streaming
            "error": "#f44336",  # colorTokens.status.error
            "unavailable": "#9e9e9e",  # colorTokens.status.unavailable
        }
    
    async def apply_theme_to_page(self, page: ft.Page) -> None:
        """
        Aplica el tema actual a una página Flet.
        
        Args:
            page: Página Flet a la que aplicar el tema
        """
        try:
            self._theme_service.apply_theme_to_page(page, self._current_theme)
            self.logger.debug(f"Tema {self._current_theme} aplicado a la página")
        except Exception as e:
            self.logger.error(f"Error aplicando tema a la página: {e}")
            raise


# Instancia singleton del presenter
theme_presenter = ThemePresenter()