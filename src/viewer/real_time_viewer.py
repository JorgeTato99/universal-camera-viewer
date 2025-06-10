"""
Visor en tiempo real para múltiples cámaras Dahua.
Clase principal que integra widgets de cámaras con panel de control.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.viewer.camera_widget import CameraWidget
from src.viewer.control_panel import ControlPanel


class RealTimeViewer:
    """
    Visor principal en tiempo real para múltiples cámaras Dahua.
    Integra el panel de control y los widgets de cámaras individuales.
    """
    
    def __init__(self):
        """
        Inicializa el visor en tiempo real.
        """
        # Configurar logging
        self.logger = logging.getLogger("RealTimeViewer")
        
        # Lista de widgets de cámaras activos
        self.camera_widgets: List[CameraWidget] = []
        
        # Configuración actual de cámaras
        self.cameras_config: List[Dict[str, Any]] = []
        
        # Layout actual
        self.current_layout = "grid_2x2"
        
        # Bandera para evitar doble cierre
        self._closing_app = False
        
        # Crear ventana principal
        self._create_main_window()
        
        # Crear área de visualización PRIMERO
        self._create_viewer_area()
        
        # Crear panel de control DESPUÉS (puede disparar callbacks)
        self._create_control_panel()
        
        # Configurar eventos de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Ahora que todo está listo, procesar la configuración inicial
        self._initialize_default_cameras()
        
        self.logger.info("Visor en tiempo real inicializado")
    
    def _initialize_default_cameras(self):
        """
        Inicializa la configuración por defecto de cámaras después de que todo esté listo.
        """
        try:
            # Obtener la configuración de cámaras del control panel
            default_cameras = self.control_panel.get_cameras_config()
            if default_cameras:
                self.logger.info("Aplicando configuración inicial de cámaras")
                self._on_cameras_config_change(default_cameras)
        except Exception as e:
            self.logger.warning(f"No se pudo aplicar configuración inicial: {str(e)}")
    
    def _create_main_window(self):
        """
        Crea la ventana principal de la aplicación.
        """
        self.root = tk.Tk()
        self.root.title("Visor Universal de Cámaras - Módulo Dahua")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        
        # Configurar el estilo
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
        
        # Configurar colores y estilos
        self.root.configure(bg='#f0f0f0')
        
        # Icono de la ventana (opcional)
        try:
            # Si tienes un icono, puedes agregarlo aquí
            # self.root.iconbitmap('path/to/icon.ico')
            pass
        except Exception:
            pass
    
    def _create_control_panel(self):
        """
        Crea el panel de control superior.
        """
        self.control_panel = ControlPanel(
            parent=self.root,
            on_cameras_change=self._on_cameras_config_change
        )
    
    def _create_viewer_area(self):
        """
        Crea el área principal de visualización de cámaras.
        """
        # Frame principal para el área de visualización
        self.viewer_main_frame = ttk.LabelFrame(self.root, text="Visualización de Cámaras")
        self.viewer_main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame contenedor con scroll
        self.viewer_canvas = tk.Canvas(self.viewer_main_frame, bg='white')
        self.viewer_scrollbar = ttk.Scrollbar(
            self.viewer_main_frame, 
            orient="vertical", 
            command=self.viewer_canvas.yview
        )
        self.viewer_scrollable_frame = ttk.Frame(self.viewer_canvas)
        
        # Configurar scroll
        self.viewer_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.viewer_canvas.configure(scrollregion=self.viewer_canvas.bbox("all"))
        )
        
        self.viewer_canvas.create_window((0, 0), window=self.viewer_scrollable_frame, anchor="nw")
        self.viewer_canvas.configure(yscrollcommand=self.viewer_scrollbar.set)
        
        # Pack canvas y scrollbar
        self.viewer_canvas.pack(side="left", fill="both", expand=True)
        self.viewer_scrollbar.pack(side="right", fill="y")
        
        # Mensaje inicial
        self._show_initial_message()
        
        # Bind eventos de mouse para scroll
        self._bind_mousewheel()
    
    def _show_initial_message(self):
        """
        Muestra un mensaje inicial cuando no hay cámaras configuradas.
        """
        self.initial_message_frame = ttk.Frame(self.viewer_scrollable_frame)
        self.initial_message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=50)
        
        # Mensaje de bienvenida
        welcome_label = ttk.Label(
            self.initial_message_frame,
            text="¡Bienvenido al Visor Universal de Cámaras!",
            font=("Arial", 16, "bold")
        )
        welcome_label.pack(pady=10)
        
        instructions_text = """
Para comenzar:
1. Ve a la pestaña "Cámaras" en el panel de control
2. Agrega una o más cámaras usando el botón "Agregar Cámara"
3. Configura la IP, credenciales y tipo de conexión
4. Selecciona el layout deseado en la pestaña "Layout"
5. ¡Las cámaras aparecerán aquí automáticamente!

Funciones disponibles:
• Visualización en tiempo real de múltiples cámaras
• Soporte para RTSP, HTTP/Amcrest y ONVIF
• Captura de snapshots individuales
• Grabación de video (próximamente)
• Layouts configurables (1x1, 2x2, 3x3, etc.)
• Guardado y carga de configuraciones
        """
        
        instructions_label = ttk.Label(
            self.initial_message_frame,
            text=instructions_text,
            font=("Arial", 10),
            justify=tk.LEFT
        )
        instructions_label.pack(pady=10)
        
        # Botón de ejemplo
        example_button = ttk.Button(
            self.initial_message_frame,
            text="Cargar Configuración de Ejemplo",
            command=self._load_example_config
        )
        example_button.pack(pady=10)
    
    def _load_example_config(self):
        """
        Carga una configuración de ejemplo.
        """
        # La configuración de ejemplo ya está cargada por defecto en el control panel
        messagebox.showinfo(
            "Configuración de Ejemplo", 
            "¡La configuración de ejemplo ya está cargada!\n\n"
            "Ve a la pestaña 'Cámaras' para ver la cámara Dahua Hero-K51H configurada.\n"
            "Puedes modificar la IP y credenciales según tu setup."
        )
    
    def _bind_mousewheel(self):
        """
        Configura el scroll con la rueda del mouse.
        """
        def _on_mousewheel(event):
            self.viewer_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind a diferentes elementos para asegurar compatibilidad
        self.viewer_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.root.bind("<MouseWheel>", _on_mousewheel)
    
    def _on_cameras_config_change(self, cameras_config: List[Dict[str, Any]]):
        """
        Callback que se ejecuta cuando cambia la configuración de cámaras.
        
        Args:
            cameras_config: Nueva configuración de cámaras
        """
        self.logger.info(f"Configuración de cámaras actualizada: {len(cameras_config)} cámaras")
        
        # Actualizar configuración
        self.cameras_config = cameras_config
        
        # Verificar que el área de visualización esté lista
        if not hasattr(self, 'viewer_scrollable_frame'):
            self.logger.warning("Área de visualización no está lista, ignorando cambio de configuración")
            return
        
        # Verificar que el control panel esté listo
        if not hasattr(self, 'control_panel'):
            self.logger.warning("Panel de control no está listo, ignorando cambio de configuración")
            return
        
        # Recrear widgets de cámaras
        self._recreate_camera_widgets()
    
    def _recreate_camera_widgets(self):
        """
        Recrea todos los widgets de cámaras basado en la configuración actual.
        """
        # Limpiar widgets existentes
        self._clear_camera_widgets()
        
        # Si no hay cámaras, mostrar mensaje inicial
        if not self.cameras_config:
            self._show_initial_message()
            return
        
        # Ocultar mensaje inicial si está visible
        if hasattr(self, 'initial_message_frame'):
            self.initial_message_frame.destroy()
        
        # Crear nuevos widgets basados en el layout
        self._create_camera_widgets_with_layout()
    
    def _clear_camera_widgets(self):
        """
        Limpia todos los widgets de cámaras existentes.
        """
        # Desconectar y limpiar widgets existentes
        for widget in self.camera_widgets:
            try:
                widget.cleanup()
            except Exception as e:
                self.logger.error(f"Error al limpiar widget: {str(e)}")
        
        self.camera_widgets.clear()
        
        # Limpiar frame de visualización
        for child in self.viewer_scrollable_frame.winfo_children():
            child.destroy()
    
    def _create_camera_widgets_with_layout(self):
        """
        Crea widgets de cámaras usando el layout especificado.
        """
        if not self.cameras_config:
            return
        
        # Obtener layout actual del control panel (si existe)
        if hasattr(self, 'control_panel') and self.control_panel:
            self.current_layout = self.control_panel.get_current_layout()
        # Si no existe el control panel, usar layout por defecto
        else:
            self.current_layout = "grid_2x2"
        
        # Crear frame contenedor para las cámaras
        cameras_container = ttk.Frame(self.viewer_scrollable_frame)
        cameras_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar layout basado en el tipo
        if self.current_layout == "single":
            self._create_single_layout(cameras_container)
        elif self.current_layout == "horizontal_2":
            self._create_horizontal_layout(cameras_container, 2)
        elif self.current_layout == "vertical_2":
            self._create_vertical_layout(cameras_container, 2)
        elif self.current_layout == "grid_2x2":
            self._create_grid_layout(cameras_container, 2, 2)
        elif self.current_layout == "grid_3x2":
            self._create_grid_layout(cameras_container, 3, 2)
        elif self.current_layout == "grid_3x3":
            self._create_grid_layout(cameras_container, 3, 3)
        elif self.current_layout == "grid_4x3":
            self._create_grid_layout(cameras_container, 4, 3)
        else:
            # Layout por defecto: grid 2x2
            self._create_grid_layout(cameras_container, 2, 2)
        
        self.logger.info(f"Creados {len(self.camera_widgets)} widgets de cámaras con layout {self.current_layout}")
    
    def _create_single_layout(self, container: ttk.Frame):
        """
        Crea layout de una sola cámara.
        """
        if self.cameras_config:
            widget = CameraWidget(container, self.cameras_config[0])
            self.camera_widgets.append(widget)
    
    def _create_horizontal_layout(self, container: ttk.Frame, count: int):
        """
        Crea layout horizontal.
        """
        for i, camera_config in enumerate(self.cameras_config[:count]):
            frame = ttk.Frame(container)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            widget = CameraWidget(frame, camera_config)
            self.camera_widgets.append(widget)
    
    def _create_vertical_layout(self, container: ttk.Frame, count: int):
        """
        Crea layout vertical.
        """
        for i, camera_config in enumerate(self.cameras_config[:count]):
            frame = ttk.Frame(container)
            frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            widget = CameraWidget(frame, camera_config)
            self.camera_widgets.append(widget)
    
    def _create_grid_layout(self, container: ttk.Frame, cols: int, rows: int):
        """
        Crea layout en grilla.
        
        Args:
            container: Frame contenedor
            cols: Número de columnas
            rows: Número de filas
        """
        max_cameras = cols * rows
        cameras_to_show = self.cameras_config[:max_cameras]
        
        # Configurar pesos de filas y columnas para expansión uniforme
        for i in range(rows):
            container.grid_rowconfigure(i, weight=1)
        for j in range(cols):
            container.grid_columnconfigure(j, weight=1)
        
        # Crear widgets en grilla
        for i, camera_config in enumerate(cameras_to_show):
            row = i // cols
            col = i % cols
            
            # Frame para cada cámara
            camera_frame = ttk.Frame(container)
            camera_frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            
            # Configurar expansión del frame
            camera_frame.grid_rowconfigure(0, weight=1)
            camera_frame.grid_columnconfigure(0, weight=1)
            
            # Crear widget de cámara
            widget = CameraWidget(camera_frame, camera_config)
            self.camera_widgets.append(widget)
    
    def _on_closing(self):
        """
        Maneja el evento de cierre de la aplicación.
        """
        # Evitar doble cierre
        if self._closing_app:
            return
            
        self._closing_app = True
        
        try:
            self.logger.info("Cerrando aplicación...")
            
            # Limpiar todos los widgets de cámaras
            self._clear_camera_widgets()
            
            # Verificar si la ventana aún existe antes de destruirla
            if self.root.winfo_exists():
                self.root.destroy()
            
            self.logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {str(e)}")
            try:
                # Intentar forzar cierre solo si la ventana aún existe
                if hasattr(self, 'root') and self.root.winfo_exists():
                    self.root.quit()
            except:
                pass  # Ignorar errores en el cierre forzado
    
    def run(self):
        """
        Inicia el loop principal de la aplicación.
        """
        try:
            self.logger.info("Iniciando aplicación...")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Aplicación interrumpida por usuario")
        except Exception as e:
            self.logger.error(f"Error en aplicación: {str(e)}")
            try:
                messagebox.showerror("Error Fatal", f"Error inesperado:\n{str(e)}")
            except:
                pass  # Si la GUI ya se destruyó, ignorar error del messagebox
        finally:
            # Solo llamar _on_closing si no se ha llamado ya
            if not self._closing_app:
                self._on_closing()


def main():
    """
    Función principal para ejecutar el visor.
    """
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('visor_camaras.log', encoding='utf-8')
        ]
    )
    
    # Crear y ejecutar visor
    try:
        viewer = RealTimeViewer()
        viewer.run()
    except Exception as e:
        logging.error(f"Error fatal al iniciar aplicación: {str(e)}")
        if tk._default_root:
            messagebox.showerror("Error Fatal", f"No se pudo iniciar la aplicación:\n{str(e)}")


if __name__ == "__main__":
    main() 