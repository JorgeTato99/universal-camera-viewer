"""
Aplicación principal del Visor Universal de Cámaras.
Maneja el sistema de menús y la navegación entre diferentes vistas.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from .viewer.real_time_viewer_view import RealTimeViewerView
from .discovery.port_discovery_view import PortDiscoveryView

# cspell:disable
class MainApplication:
    """
    Aplicación principal con sistema de menús y vistas modulares.
    Implementa el patrón de navegación entre diferentes funcionalidades.
    """
    
    def __init__(self):
        """
        Inicializa la aplicación principal.
        """
        # Configurar logging
        self.logger = logging.getLogger("MainApplication")
        
        # Crear ventana principal
        self._create_main_window()
        
        # Crear sistema de menús
        self._create_menu_system()
        
        # Estado de la aplicación
        self.current_view: Optional[tk.Widget] = None
        self.views: Dict[str, Any] = {}
        
        # Contenedor principal para las vistas
        self._create_main_container()
        
        # Configurar eventos de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Cargar vista inicial (Viewer)
        self._show_viewer()
        
        self.logger.info("Aplicación principal inicializada")
    
    def _create_main_window(self):
        """
        Crea la ventana principal de la aplicación.
        """
        self.root = tk.Tk()
        self.root.title("Visor Universal de Cámaras - Aplicación Principal")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 700)
        
        # Configurar el estilo
        self._setup_styles()
        
        # Configurar colores y tema
        self.root.configure(bg='#f0f0f0')
        
        # Centrar ventana en pantalla
        self._center_window()
        
        self.logger.info("Ventana principal creada")
    
    def _setup_styles(self):
        """
        Configura los estilos de la aplicación.
        """
        style = ttk.Style()
        try:
            # Intentar usar un tema moderno
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
        except Exception as e:
            self.logger.warning(f"No se pudo configurar tema: {str(e)}")
        
        # Configurar estilos personalizados
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10))
        style.configure('Menu.TButton', padding=(10, 5))
    
    def _center_window(self):
        """
        Centra la ventana en la pantalla.
        """
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_menu_system(self):
        """
        Crea el sistema de menús superior.
        """
        # Crear barra de menús
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú principal
        main_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aplicación", menu=main_menu)
        main_menu.add_command(label="Acerca de", command=self._show_about)
        main_menu.add_separator()
        main_menu.add_command(label="Salir", command=self._on_closing)
        
        # Menú de vistas
        views_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Vistas", menu=views_menu)
        views_menu.add_command(label="📹 Viewer", command=self._show_viewer)
        views_menu.add_command(label="🔍 Port Discovery", command=self._show_port_discovery)
        
        # Menú de herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Configuración", command=self._show_configuration)
        tools_menu.add_command(label="Logs", command=self._show_logs)
        
        # Menú de ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Documentación", command=self._show_documentation)
        help_menu.add_command(label="Soporte", command=self._show_support)
        
        self.logger.info("Sistema de menús creado")
    
    def _create_main_container(self):
        """
        Crea el contenedor principal para las vistas.
        """
        # Frame principal que contendrá todas las vistas
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Barra de navegación (opcional, para complementar el menú)
        self._create_navigation_bar()
    
    def _create_navigation_bar(self):
        """
        Crea una barra de navegación opcional con botones rápidos.
        """
        nav_frame = ttk.Frame(self.main_container)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Título de la sección actual
        self.current_section_label = ttk.Label(
            nav_frame, 
            text="📹 Visor de Cámaras", 
            style='Title.TLabel'
        )
        self.current_section_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de navegación rápida
        button_frame = ttk.Frame(nav_frame)
        button_frame.pack(side=tk.RIGHT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="📹 Viewer",
            style='Menu.TButton',
            command=self._show_viewer
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="🔍 Port Discovery",
            style='Menu.TButton',
            command=self._show_port_discovery
        ).pack(side=tk.LEFT, padx=2)
        
        # Separador visual
        separator = ttk.Separator(self.main_container, orient='horizontal')
        separator.pack(fill=tk.X, pady=2)
    
    def _clear_current_view(self):
        """
        Limpia la vista actual del contenedor principal.
        """
        if self.current_view:
            try:
                # Solo ocultar la vista, no destruirla (para reutilización)
                self.current_view.pack_forget()
                
            except Exception as e:
                self.logger.error(f"Error ocultando vista actual: {e}")
            
            finally:
                self.current_view = None
    
    def _show_viewer(self):
        """
        Muestra la vista del visor de cámaras.
        """
        self.logger.info("Cambiando a vista Viewer")
        
        # Limpiar vista actual
        self._clear_current_view()
        
        # Actualizar título de sección
        self.current_section_label.config(text="📹 Visor de Cámaras")
        
        try:
            # Crear o reutilizar vista del viewer
            if 'viewer' not in self.views:
                # Crear nueva vista
                viewer_container = ttk.Frame(self.main_container)
                viewer_view = RealTimeViewerView(viewer_container)
                
                # Almacenar tanto el contenedor como la vista
                self.views['viewer'] = {
                    'container': viewer_container,
                    'view': viewer_view
                }
                
                viewer_container.pack(fill=tk.BOTH, expand=True)
                self.current_view = viewer_container
            else:
                # Reutilizar vista existente
                viewer_data = self.views['viewer']
                viewer_container = viewer_data['container']
                viewer_view = viewer_data['view']
                
                # Reactivar el contenedor
                viewer_container.pack(fill=tk.BOTH, expand=True)
                self.current_view = viewer_container
                
                # Refrescar la vista si tiene el método
                if hasattr(viewer_view, 'refresh'):
                    viewer_view.refresh()
            
            self.logger.info("Vista Viewer cargada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error cargando vista Viewer: {e}")
            messagebox.showerror("Error", f"No se pudo cargar el Viewer:\n{str(e)}")
    
    def _show_port_discovery(self):
        """
        Muestra la vista de descubrimiento de puertos.
        """
        self.logger.info("Cambiando a vista Port Discovery")
        
        # Limpiar vista actual
        self._clear_current_view()
        
        # Actualizar título de sección
        self.current_section_label.config(text="🔍 Descubrimiento de Puertos")
        
        try:
            # Crear o reutilizar vista de port discovery
            if 'port_discovery' not in self.views:
                # Crear nueva vista
                discovery_container = ttk.Frame(self.main_container)
                discovery_view = PortDiscoveryView(discovery_container)
                
                # Almacenar tanto el contenedor como la vista
                self.views['port_discovery'] = {
                    'container': discovery_container,
                    'view': discovery_view
                }
                
                discovery_container.pack(fill=tk.BOTH, expand=True)
                self.current_view = discovery_container
            else:
                # Reutilizar vista existente
                discovery_data = self.views['port_discovery']
                discovery_container = discovery_data['container']
                discovery_view = discovery_data['view']
                
                # Reactivar el contenedor
                discovery_container.pack(fill=tk.BOTH, expand=True)
                self.current_view = discovery_container
                
                # Refrescar la vista si tiene el método
                if hasattr(discovery_view, 'refresh'):
                    discovery_view.refresh()
            
            self.logger.info("Vista Port Discovery cargada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error cargando vista Port Discovery: {e}")
            messagebox.showerror("Error", f"No se pudo cargar Port Discovery:\n{str(e)}")
    
    def _show_about(self):
        """
        Muestra información sobre la aplicación.
        """
        about_text = """
Visor Universal de Cámaras Multi-Marca
Versión 1.0.0

Soporta:
• Dahua Hero-K51H
• TP-Link Tapo C520WS  
• Steren CCTV-235

Protocolos:
• ONVIF (Principal)
• RTSP (Respaldo)
• HTTP/CGI (Según modelo)

Desarrollado con Python y Tkinter
Arquitectura SOLID • Clean Code
        """
        
        messagebox.showinfo("Acerca de", about_text.strip())
    
    def _show_configuration(self):
        """
        Placeholder para configuración (implementar en el futuro).
        """
        messagebox.showinfo("Configuración", "Funcionalidad de configuración próximamente.")
    
    def _show_logs(self):
        """
        Placeholder para visualización de logs (implementar en el futuro).
        """
        messagebox.showinfo("Logs", "Visualizador de logs próximamente.")
    
    def _show_documentation(self):
        """
        Placeholder para documentación (implementar en el futuro).
        """
        messagebox.showinfo("Documentación", "Documentación disponible en README.md")
    
    def _show_support(self):
        """
        Placeholder para soporte (implementar en el futuro).
        """
        messagebox.showinfo("Soporte", "Para soporte, consulte la documentación del proyecto.")
    
    def _on_closing(self):
        """
        Maneja el evento de cierre de la aplicación.
        """
        try:
            self.logger.info("Cerrando aplicación principal...")
            
            # Limpiar vista actual
            self._clear_current_view()
            
            # Limpiar vistas almacenadas
            for view_name, view_data in self.views.items():
                try:
                    if isinstance(view_data, dict):
                        # Nueva estructura con container y view
                        if 'view' in view_data and hasattr(view_data['view'], 'cleanup'):
                            view_data['view'].cleanup()
                        if 'container' in view_data:
                            view_data['container'].destroy()
                    else:
                        # Estructura antigua (por compatibilidad)
                        if hasattr(view_data, 'cleanup'):
                            view_data.cleanup()
                except Exception as e:
                    self.logger.error(f"Error limpiando vista {view_name}: {e}")
            
            # Cerrar ventana principal
            if self.root.winfo_exists():
                self.root.destroy()
            
            self.logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {str(e)}")
            try:
                if hasattr(self, 'root') and self.root.winfo_exists():
                    self.root.quit()
            except:
                pass
    
    def run(self):
        """
        Inicia el loop principal de la aplicación.
        """
        try:
            self.logger.info("Iniciando aplicación principal...")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Aplicación interrumpida por usuario")
        except Exception as e:
            self.logger.error(f"Error en aplicación principal: {str(e)}")
            try:
                messagebox.showerror("Error Fatal", f"Error inesperado:\n{str(e)}")
            except:
                pass
        finally:
            if not hasattr(self, '_closing_called'):
                self._closing_called = True
                self._on_closing()


def main():
    """
    Función principal para ejecutar la aplicación.
    """
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('visor_universal.log', encoding='utf-8')
        ]
    )
    
    # Crear y ejecutar aplicación
    try:
        app = MainApplication()
        app.run()
    except Exception as e:
        logging.error(f"Error fatal al iniciar aplicación: {str(e)}")
        if tk._default_root:
            messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicación:\n{str(e)}")


if __name__ == "__main__":
    main() 