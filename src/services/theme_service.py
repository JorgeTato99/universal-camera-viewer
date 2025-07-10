#!/usr/bin/env python3
"""
Theme Service - Gestión de temas claro/oscuro
============================================

Servicio para manejar la configuración de temas de la aplicación.
Incluye:
- Configuración de tema claro optimizada
- Configuración de tema oscuro
- Persistencia de preferencias
- Notificaciones de cambios
"""

import flet as ft
from typing import Optional, Callable
import json
import os
from pathlib import Path


class ThemeMode:
    """Constantes para modos de tema."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeService:
    """
    Servicio para gestión de temas de la aplicación.
    
    Maneja:
    - Configuración de colores Material Design 3
    - Cambio entre modo claro/oscuro
    - Persistencia de preferencias
    - Notificaciones de cambios
    """
    
    def __init__(self):
        self.current_theme = ThemeMode.LIGHT
        self.theme_change_callbacks = []
        
        # Colores base para temas
        self.primary_color = ft.Colors.BLUE_700
        self.config_file = Path("config/theme_config.json")
        
        # Cargar configuración persistente
        self._load_theme_config()
    
    def _load_theme_config(self):
        """Carga la configuración de tema desde archivo."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_theme = config.get('theme', ThemeMode.LIGHT)
                    self.primary_color = config.get('primary_color', ft.Colors.BLUE_700)
                    print(f"🎨 Tema cargado desde archivo: {self.current_theme}")
            else:
                print(f"🎨 Archivo de configuración no existe, usando tema por defecto: {ThemeMode.LIGHT}")
                self.current_theme = ThemeMode.LIGHT
        except Exception as e:
            # Si hay error, usar valores por defecto
            print(f"🎨 Error cargando configuración, usando tema por defecto: {e}")
            self.current_theme = ThemeMode.LIGHT
    
    def _save_theme_config(self):
        """Guarda la configuración actual de tema."""
        try:
            # Crear directorio si no existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'theme': self.current_theme,
                'primary_color': self.primary_color
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            # Si hay error, continuar silenciosamente
            pass
    
    def get_light_theme(self) -> ft.Theme:
        """Obtiene la configuración del tema claro optimizada."""
        return ft.Theme(
            color_scheme_seed=self.primary_color,
            color_scheme=ft.ColorScheme(
                # === COLORES PRINCIPALES ===
                primary=self.primary_color,
                on_primary=ft.Colors.WHITE,
                primary_container=ft.Colors.BLUE_50,
                on_primary_container=ft.Colors.BLUE_900,
                
                # === COLORES SECUNDARIOS ===
                secondary=ft.Colors.BLUE_600,
                on_secondary=ft.Colors.WHITE,
                secondary_container=ft.Colors.BLUE_100,
                on_secondary_container=ft.Colors.BLUE_800,
                
                # === COLORES TERCIARIOS ===
                tertiary=ft.Colors.INDIGO_600,
                on_tertiary=ft.Colors.WHITE,
                tertiary_container=ft.Colors.INDIGO_50,
                on_tertiary_container=ft.Colors.INDIGO_800,
                
                # === SUPERFICIES - MEJORADAS ===
                surface=ft.Colors.WHITE,
                on_surface=ft.Colors.GREY_900,
                surface_variant=ft.Colors.GREY_50,
                on_surface_variant=ft.Colors.GREY_700,
                
                # === FONDO - MEJORADO ===
                background=ft.Colors.GREY_50,
                on_background=ft.Colors.GREY_900,
                
                # === ERRORES ===
                error=ft.Colors.RED_600,
                on_error=ft.Colors.WHITE,
                error_container=ft.Colors.RED_50,
                on_error_container=ft.Colors.RED_800,
                
                # === BORDES Y SOMBRAS ===
                outline=ft.Colors.GREY_300,
                outline_variant=ft.Colors.GREY_200,
                shadow=ft.Colors.BLACK12,
                scrim=ft.Colors.BLACK54,
                
                # === SUPERFICIES INVERSAS ===
                inverse_surface=ft.Colors.GREY_800,
                on_inverse_surface=ft.Colors.GREY_100,
                inverse_primary=ft.Colors.BLUE_200,
                
                # === TINTE DE SUPERFICIE ===
                surface_tint=self.primary_color,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
            use_material3=True
        )
    
    def get_dark_theme(self) -> ft.Theme:
        """Obtiene la configuración del tema oscuro."""
        return ft.Theme(
            color_scheme_seed=self.primary_color,
            color_scheme=ft.ColorScheme(
                # === COLORES PRINCIPALES ===
                primary=ft.Colors.BLUE_300,
                on_primary=ft.Colors.BLUE_900,
                primary_container=ft.Colors.BLUE_800,
                on_primary_container=ft.Colors.BLUE_100,
                
                # === COLORES SECUNDARIOS ===
                secondary=ft.Colors.BLUE_400,
                on_secondary=ft.Colors.BLUE_900,
                secondary_container=ft.Colors.BLUE_700,
                on_secondary_container=ft.Colors.BLUE_100,
                
                # === COLORES TERCIARIOS ===
                tertiary=ft.Colors.INDIGO_400,
                on_tertiary=ft.Colors.INDIGO_900,
                tertiary_container=ft.Colors.INDIGO_700,
                on_tertiary_container=ft.Colors.INDIGO_100,
                
                # === SUPERFICIES ===
                surface=ft.Colors.GREY_900,
                on_surface=ft.Colors.GREY_100,
                surface_variant=ft.Colors.GREY_800,
                on_surface_variant=ft.Colors.GREY_300,
                
                # === FONDO ===
                background=ft.Colors.GREY_900,
                on_background=ft.Colors.GREY_100,
                
                # === ERRORES ===
                error=ft.Colors.RED_400,
                on_error=ft.Colors.RED_900,
                error_container=ft.Colors.RED_800,
                on_error_container=ft.Colors.RED_100,
                
                # === BORDES Y SOMBRAS ===
                outline=ft.Colors.GREY_600,
                outline_variant=ft.Colors.GREY_700,
                shadow=ft.Colors.BLACK,
                scrim=ft.Colors.BLACK,
                
                # === SUPERFICIES INVERSAS ===
                inverse_surface=ft.Colors.GREY_100,
                on_inverse_surface=ft.Colors.GREY_900,
                inverse_primary=ft.Colors.BLUE_700,
                
                # === TINTE DE SUPERFICIE ===
                surface_tint=ft.Colors.BLUE_400,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
            use_material3=True
        )
    
    def configure_page_theme(self, page: ft.Page, force_update: bool = True):
        """Configura el tema de la página."""
        print(f"🎨 Configurando tema: {self.current_theme}")
        
        # Configurar temas
        page.theme = self.get_light_theme()
        page.dark_theme = self.get_dark_theme()
        
        # Establecer modo de tema
        if self.current_theme == ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ft.Colors.GREY_50
            print("🎨 Aplicando tema CLARO")
        elif self.current_theme == ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ft.Colors.GREY_900
            print("🎨 Aplicando tema OSCURO")
        else:
            page.theme_mode = ft.ThemeMode.SYSTEM
            page.bgcolor = ft.Colors.GREY_50
            print("🎨 Aplicando tema SISTEMA")
        
        # Actualizar página si se solicita
        if force_update:
            page.update()
            print("🎨 Página actualizada")
    
    def toggle_theme(self, page: ft.Page):
        """Cambia entre tema claro y oscuro."""
        if self.current_theme == ThemeMode.LIGHT:
            self.set_theme(ThemeMode.DARK, page)
        else:
            self.set_theme(ThemeMode.LIGHT, page)
    
    def set_theme(self, theme_mode: str, page: ft.Page):
        """
        Establece un tema específico.
        
        Args:
            theme_mode: Modo de tema (LIGHT, DARK, SYSTEM)
            page: Página de Flet para actualizar
        """
        if theme_mode not in [ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SYSTEM]:
            return
        
        self.current_theme = theme_mode
        self._save_theme_config()
        
        # Aplicar tema a la página
        self.configure_page_theme(page)
        
        # Notificar cambio
        self._notify_theme_change(theme_mode)
    
    def get_current_theme(self) -> str:
        """Obtiene el tema actual."""
        return self.current_theme
    
    def is_dark_theme(self) -> bool:
        """Verifica si el tema actual es oscuro."""
        return self.current_theme == ThemeMode.DARK
    
    def add_theme_change_callback(self, callback: Callable[[str], None]):
        """Agrega un callback para notificaciones de cambio de tema."""
        self.theme_change_callbacks.append(callback)
    
    def remove_theme_change_callback(self, callback: Callable[[str], None]):
        """Remueve un callback de notificaciones de cambio de tema."""
        if callback in self.theme_change_callbacks:
            self.theme_change_callbacks.remove(callback)
    
    def _notify_theme_change(self, new_theme: str):
        """Notifica a todos los callbacks sobre el cambio de tema."""
        for callback in self.theme_change_callbacks:
            try:
                callback(new_theme)
            except Exception:
                # Continuar si hay error en algún callback
                pass
    
    def get_theme_colors(self) -> dict:
        """Obtiene los colores del tema actual como diccionario."""
        if self.current_theme == ThemeMode.LIGHT:
            return {
                'primary': self.primary_color,
                'surface': ft.Colors.WHITE,
                'background': ft.Colors.GREY_50,
                'on_surface': ft.Colors.GREY_900,
                'on_background': ft.Colors.GREY_900,
                'outline': ft.Colors.GREY_300,
                'outline_variant': ft.Colors.GREY_200,
            }
        else:
            return {
                'primary': ft.Colors.BLUE_300,
                'surface': ft.Colors.GREY_900,
                'background': ft.Colors.GREY_900,
                'on_surface': ft.Colors.GREY_100,
                'on_background': ft.Colors.GREY_100,
                'outline': ft.Colors.GREY_600,
                'outline_variant': ft.Colors.GREY_700,
            }

    def force_theme_reload(self, page: ft.Page):
        """Fuerza la recarga completa del tema - útil para resolver problemas de inicialización."""
        print(f"🎨 FORZANDO RECARGA DEL TEMA: {self.current_theme}")
        
        # Limpiar configuración actual
        page.theme = None
        page.dark_theme = None
        page.theme_mode = None
        page.bgcolor = None
        
        # Reconfigurar desde cero
        page.theme = self.get_light_theme()
        page.dark_theme = self.get_dark_theme()
        
        # Establecer modo de tema de manera más explícita
        if self.current_theme == ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ft.Colors.GREY_50
            print("🎨 TEMA CLARO APLICADO FORZADAMENTE")
        elif self.current_theme == ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ft.Colors.GREY_900
            print("🎨 TEMA OSCURO APLICADO FORZADAMENTE")
        else:
            page.theme_mode = ft.ThemeMode.SYSTEM
            page.bgcolor = ft.Colors.GREY_50
            print("🎨 TEMA SISTEMA APLICADO FORZADAMENTE")
        
        # Forzar actualización múltiple
        page.update()
        print("🎨 PRIMERA ACTUALIZACIÓN COMPLETADA")
        
        # Segunda actualización para asegurar que todos los componentes se actualicen
        page.update()
        print("🎨 SEGUNDA ACTUALIZACIÓN COMPLETADA")

    def reset_to_light_theme(self, page: ft.Page):
        """Resetea el tema a claro por defecto - útil para debugging."""
        print("🎨 RESETEANDO A TEMA CLARO")
        self.current_theme = ThemeMode.LIGHT
        self._save_theme_config()
        self.force_theme_reload(page)


# Instancia global del servicio de tema
theme_service = ThemeService() 