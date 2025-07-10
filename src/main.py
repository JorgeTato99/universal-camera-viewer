"""
Visor Universal de Cámaras Multi-Marca - Entry Point
====================================================

Punto de entrada principal de la aplicación con arquitectura MVP.
Utiliza Flet como framework de UI para crear una aplicación desktop multiplataforma.

Arquitectura MVP:
- Models: Lógica de negocio independiente de UI
- Views: Componentes Flet para renderizado 
- Presenters: Coordinación entre Models y Views

Ejecución:
    python src/main.py              # Desarrollo
    flet pack src/main.py           # Empaquetado para distribución
"""

import flet as ft
import logging
import sys
import asyncio
from pathlib import Path

# Configurar path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

from src.views.main_view import MainView
from src.presenters import get_main_presenter, cleanup_all_presenters


class CameraViewerApp:
    """
    Clase principal de la aplicación MVP.
    
    Actúa como punto de entrada y coordina la inicialización
    de la arquitectura MVP completa.
    """
    
    def __init__(self):
        self.app_title = "Visor Universal de Cámaras v2.0"
        self.app_version = "2.0.0-MVP"
        
        # Referencias a componentes MVP
        self.main_presenter = None
        self.main_view = None
        
        # Configuración de la aplicación
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('camera_viewer.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🚀 Iniciando {self.app_title}")
    
    async def build(self, page: ft.Page):
        """
        Construye la aplicación Flet con arquitectura MVP.
        
        Args:
            page: Página principal de Flet
        """
        try:
            self.logger.info("📱 Construyendo aplicación MVP")
            
            # Configurar página principal
            self._configure_page(page)
            
            # Inicializar arquitectura MVP
            await self._initialize_mvp(page)
            
            # Configurar manejo de cierre
            page.window.on_event = self._on_window_event
            
            self.logger.info("✅ Aplicación MVP inicializada exitosamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error construyendo aplicación: {str(e)}")
            await self._show_error_dialog(page, f"Error de inicialización: {str(e)}")
    
    def _configure_page(self, page: ft.Page):
        """Configura las propiedades básicas de la página."""
        page.title = self.app_title
        page.window.width = 1400
        page.window.height = 900
        page.window.min_width = 1000
        page.window.min_height = 700
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.window.prevent_close = True
        
        # === TEMA MODERNO MATERIAL DESIGN 3 ===
        # Color primario de la marca (tecnología/cámaras)
        primary_color = ft.Colors.BLUE_700  # Azul profesional
        
        # Configurar tema moderno con Material Design 3
        page.theme = ft.Theme(
            # Esquema de colores moderno usando seed color como base
            color_scheme_seed=primary_color,
            # Configurar ColorScheme personalizado
            color_scheme=ft.ColorScheme(
                # Colores principales
                primary=primary_color,
                on_primary=ft.Colors.WHITE,
                primary_container=ft.Colors.BLUE_100,
                on_primary_container=ft.Colors.BLUE_900,
                
                # Colores secundarios
                secondary=ft.Colors.BLUE_600,
                on_secondary=ft.Colors.WHITE,
                secondary_container=ft.Colors.BLUE_50,
                on_secondary_container=ft.Colors.BLUE_800,
                
                # Colores terciarios para acentos
                tertiary=ft.Colors.INDIGO_600,
                on_tertiary=ft.Colors.WHITE,
                tertiary_container=ft.Colors.INDIGO_50,
                on_tertiary_container=ft.Colors.INDIGO_800,
                
                # Superficies
                surface=ft.Colors.GREY_50,
                on_surface=ft.Colors.GREY_900,
                surface_variant=ft.Colors.GREY_100,
                on_surface_variant=ft.Colors.GREY_700,
                
                # Fondo
                background=ft.Colors.WHITE,
                on_background=ft.Colors.BLACK,
                
                # Errores
                error=ft.Colors.RED_600,
                on_error=ft.Colors.WHITE,
                error_container=ft.Colors.RED_50,
                on_error_container=ft.Colors.RED_800,
                
                # Outlines y sombras
                outline=ft.Colors.GREY_400,
                outline_variant=ft.Colors.GREY_200,
                shadow=ft.Colors.BLACK,
                scrim=ft.Colors.BLACK,
                
                # Superficie inversa para elementos como SnackBar
                inverse_surface=ft.Colors.GREY_800,
                on_inverse_surface=ft.Colors.GREY_100,
                inverse_primary=ft.Colors.BLUE_200,
                
                # Surface tint para elevación
                surface_tint=primary_color,
            ),
            # Visual density optimizada para desktop
            visual_density=ft.VisualDensity.COMFORTABLE,
            # Usar Material 3
            use_material3=True
        )
        
        # Tema oscuro moderno
        page.dark_theme = ft.Theme(
            color_scheme_seed=primary_color,
            color_scheme=ft.ColorScheme(
                # Colores principales en modo oscuro
                primary=ft.Colors.BLUE_200,
                on_primary=ft.Colors.BLUE_900,
                primary_container=ft.Colors.BLUE_800,
                on_primary_container=ft.Colors.BLUE_100,
                
                # Colores secundarios en modo oscuro
                secondary=ft.Colors.BLUE_300,
                on_secondary=ft.Colors.BLUE_900,
                secondary_container=ft.Colors.BLUE_700,
                on_secondary_container=ft.Colors.BLUE_100,
                
                # Colores terciarios en modo oscuro
                tertiary=ft.Colors.INDIGO_300,
                on_tertiary=ft.Colors.INDIGO_900,
                tertiary_container=ft.Colors.INDIGO_700,
                on_tertiary_container=ft.Colors.INDIGO_100,
                
                # Superficies en modo oscuro
                surface=ft.Colors.GREY_900,
                on_surface=ft.Colors.GREY_100,
                surface_variant=ft.Colors.GREY_800,
                on_surface_variant=ft.Colors.GREY_300,
                
                # Fondo en modo oscuro
                background=ft.Colors.BLACK,
                on_background=ft.Colors.WHITE,
                
                # Errores en modo oscuro
                error=ft.Colors.RED_300,
                on_error=ft.Colors.RED_900,
                error_container=ft.Colors.RED_800,
                on_error_container=ft.Colors.RED_100,
                
                # Outlines y sombras en modo oscuro
                outline=ft.Colors.GREY_600,
                outline_variant=ft.Colors.GREY_700,
                shadow=ft.Colors.BLACK,
                scrim=ft.Colors.BLACK,
                
                # Superficie inversa en modo oscuro
                inverse_surface=ft.Colors.GREY_100,
                on_inverse_surface=ft.Colors.GREY_900,
                inverse_primary=ft.Colors.BLUE_700,
                
                # Surface tint para elevación en modo oscuro
                surface_tint=ft.Colors.BLUE_200,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
            use_material3=True
        )
        
        # Configuración adicional de ventana
        page.window.title_bar_hidden = False
        page.window.title_bar_buttons_hidden = False
        page.scroll = ft.ScrollMode.ADAPTIVE
        
        # Configurar fondo según el tema
        page.bgcolor = ft.Colors.SURFACE
        
        self.logger.info("🎨 Tema Material Design 3 configurado")
    
    async def _initialize_mvp(self, page: ft.Page):
        """Inicializa la arquitectura MVP completa."""
        try:
            # Obtener presenter principal
            self.main_presenter = get_main_presenter()
            
            # Crear vista principal
            self.main_view = MainView(page)
            
            # Inicializar vista de forma asíncrona
            await self.main_view.initialize_async()
            
            # Construir y agregar vista a la página
            main_view_control = self.main_view.build()
            page.add(main_view_control)
            page.update()
            
            # Configurar callback de resize (no disponible en Flet actual)
            # page.on_window_resize = self._on_window_resize
            
            self.logger.info("🏗️ Arquitectura MVP inicializada")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando MVP: {str(e)}")
            raise
    
    async def _show_error_dialog(self, page: ft.Page, message: str):
        """Muestra diálogo de error."""
        def close_dialog(e):
            dialog.open = False
            page.update()
            page.window.close()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Error de Aplicación"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cerrar", on_click=close_dialog)
            ]
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
    
    def _on_window_resize(self, e):
        """Maneja redimensionamiento de ventana."""
        if self.main_view:
            self.main_view.update()
    
    async def _on_window_event(self, e):
        """
        Maneja eventos de ventana.
        
        Args:
            e: Evento de ventana
        """
        if e.data == "close":
            await self._cleanup_and_close()
    
    async def _cleanup_and_close(self):
        """Limpia recursos y cierra la aplicación."""
        try:
            self.logger.info("🧹 Limpiando recursos de la aplicación...")
            
            # Limpiar vista principal
            if self.main_view:
                await self.main_view.cleanup_async()
            
            # Limpiar todos los presenters
            await cleanup_all_presenters()
            
            self.logger.info("✅ Limpieza completada")
            
        except Exception as e:
            self.logger.error(f"❌ Error durante limpieza: {str(e)}")
        finally:
            # Cerrar aplicación
            pass  # La página se cerrará automáticamente


async def main_async():
    """Función principal asíncrona."""
    app = CameraViewerApp()
    
    async def app_main(page: ft.Page):
        """Wrapper para la función build."""
        await app.build(page)
    
    # Iniciar aplicación Flet
    await ft.app_async(target=app_main)


def main():
    """
    Función main síncrona - punto de entrada principal.
    
    Esta función:
    1. Configura el entorno de ejecución
    2. Inicializa el event loop de asyncio
    3. Ejecuta la aplicación MVP
    """
    try:
        # Configurar política de event loop para Windows
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Ejecutar aplicación
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        print("\\n🛑 Aplicación interrumpida por el usuario")
    except Exception as e:
        print(f"❌ Error fatal en la aplicación: {str(e)}")
        logging.error(f"Error fatal: {str(e)}", exc_info=True)
    finally:
        print("👋 Aplicación finalizada")


if __name__ == "__main__":
    main() 