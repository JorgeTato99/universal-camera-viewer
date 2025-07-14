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

from views.main_view_new import create_main_view
from presenters import get_main_presenter, cleanup_all_presenters
from services.theme_service import theme_service, ThemeMode


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
        self.logger.info(f"Iniciando {self.app_title}")
    
    async def build(self, page: ft.Page):
        """
        Construye la aplicación Flet con arquitectura MVP.
        
        Args:
            page: Página principal de Flet
        """
        try:
            self.logger.info("Construyendo aplicación MVP")
            
            # Configurar página principal
            self._configure_page(page)
            
            # Inicializar arquitectura MVP
            await self._initialize_mvp(page)
            
            # Configurar manejo de cierre
            page.window.on_event = self._on_window_event
            
            self.logger.info("Aplicación MVP inicializada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error construyendo aplicación: {str(e)}")
            await self._show_error_dialog(page, f"Error de inicialización: {str(e)}")
    
    def _configure_page(self, page: ft.Page):
        """Configura las propiedades básicas de la página."""
        page.title = self.app_title
        page.window.width = 1400
        page.window.height = 900
        page.window.min_width = 1000
        page.window.min_height = 700
        page.padding = 0
        page.window.prevent_close = True
        
        # Configuración adicional de ventana
        page.window.title_bar_hidden = False
        page.window.title_bar_buttons_hidden = False
        page.scroll = ft.ScrollMode.ADAPTIVE
        
        # === CONFIGURAR TEMA USANDO THEME SERVICE ===
        # Configurar temas sin actualizar aún
        page.theme = theme_service.get_light_theme()
        page.dark_theme = theme_service.get_dark_theme()
        
        # Establecer modo de tema
        if theme_service.current_theme == ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ft.Colors.GREY_50
        elif theme_service.current_theme == ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ft.Colors.GREY_900
        else:
            page.theme_mode = ft.ThemeMode.SYSTEM
            page.bgcolor = ft.Colors.GREY_50
        
        self.logger.info("Tema Material Design 3 configurado con ThemeService")
    
    async def _initialize_mvp(self, page: ft.Page):
        """Inicializa la arquitectura MVP completa."""
        try:
            # Obtener presenter principal
            self.main_presenter = get_main_presenter()
            
            # Crear vista principal refactorizada (ya inicializada)
            self.main_view = create_main_view(page)
            
            # Construir y agregar vista a la página
            main_view_control = self.main_view.build()
            page.add(main_view_control)
            
            # Aplicar configuración final del tema después de agregar componentes
            # Usar forzar recarga para resolver problemas de inicialización
            theme_service.force_theme_reload(page)
            
            # Configurar callback de resize (no disponible en Flet actual)
            # page.on_window_resize = self._on_window_resize
            
            self.logger.info("Arquitectura MVP refactorizada inicializada")
            self.logger.info("Navegación horizontal implementada")
            
        except Exception as e:
            self.logger.error(f"Error inicializando MVP: {str(e)}")
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
            # La nueva vista se actualiza automáticamente
            pass
    
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
                self.main_view.cleanup()
            
            # Limpiar todos los presenters
            await cleanup_all_presenters()
            
            self.logger.info("Limpieza completada")
            
        except Exception as e:
            self.logger.error(f"Error durante limpieza: {str(e)}")
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
        logging.info("\\nAplicación interrumpida por el usuario")
    except Exception as e:
        logging.error(f"Error fatal en la aplicación: {str(e)}", exc_info=True)
    finally:
        logging.info("👋 Aplicación finalizada")


if __name__ == "__main__":
    main() 