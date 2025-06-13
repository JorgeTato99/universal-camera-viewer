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

# cspell:disable
class RealTimeViewer:
    """
    Visor principal en tiempo real para múltiples cámaras.
    Integra el panel de control y los widgets de cámaras individuales.
    
    Soporta dos modos de operación:
    - Standalone: Crea su propia ventana principal
    - Embedded: Se embebe en un contenedor padre
    """
    
    def __init__(self, parent_container: Optional[tk.Widget] = None):
        """
        Inicializa el visor en tiempo real.
        
        Args:
            parent_container: Contenedor padre para modo embebido.
                            Si es None, funciona en modo standalone.
        """
        # Configurar logging
        self.logger = logging.getLogger("RealTimeViewer")
        
        # Determinar modo de operación
        self.is_embedded = parent_container is not None
        self.parent_container = parent_container
        
        # Lista de widgets de cámaras activos
        self.camera_widgets: List[CameraWidget] = []
        
        # Configuración actual de cámaras
        self.cameras_config: List[Dict[str, Any]] = []
        
        # Layout actual (número de columnas)
        self.current_layout = 2
        
        # Bandera para evitar doble cierre
        self._closing_app = False
        
        # Crear interfaz según el modo
        if self.is_embedded:
            self._create_embedded_interface()
        else:
            self._create_standalone_interface()
        
        # Crear área de visualización PRIMERO
        self._create_viewer_area()
        
        # Crear panel de control DESPUÉS (puede disparar callbacks)
        self._create_control_panel()
        
        # Configurar eventos de cierre solo en modo standalone
        if not self.is_embedded and hasattr(self, 'root'):
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Ahora que todo está listo, procesar la configuración inicial
        self._initialize_default_cameras()
        
        self.logger.info(f"Visor en tiempo real inicializado en modo {'embebido' if self.is_embedded else 'standalone'}")
    
    def _create_standalone_interface(self):
        """
        Crea la interfaz para modo standalone (ventana independiente).
        """
        self.root = tk.Tk()
        self.root.title("Visor Universal de Cámaras - Módulo Dahua")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        
        # Configurar el estilo
        self._setup_styles()
        
        # Configurar colores y estilos
        self.root.configure(bg='#f0f0f0')
        
        # El contenedor principal es la ventana root
        self.main_container = self.root
        
        # Icono de la ventana (opcional)
        try:
            # Si tienes un icono, puedes agregarlo aquí
            # self.root.iconbitmap('path/to/icon.ico')
            pass
        except Exception:
            pass
    
    def _create_embedded_interface(self):
        """
        Crea la interfaz para modo embebido (dentro de otro contenedor).
        """
        # Crear frame principal dentro del contenedor padre
        self.main_frame = ttk.Frame(self.parent_container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # El contenedor principal es el frame embebido
        self.main_container = self.main_frame
        
        # No hay root en modo embebido
        self.root = None
    
    def _setup_styles(self):
        """
        Configura los estilos de la aplicación (solo en modo standalone).
        """
        if not self.is_embedded:
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
    
    def _initialize_default_cameras(self):
        """
        Inicializa la configuración por defecto de cámaras después de que todo esté listo.
        
        Nota: El ControlPanel ya notifica automáticamente cuando carga la configuración
        por defecto, por lo que no necesitamos hacer nada aquí.
        """
        # El ControlPanel ya ha cargado y notificado la configuración por defecto
        # a través del callback on_cameras_change, por lo que no necesitamos
        # hacer nada adicional aquí.
        self.logger.info("Sistema de cámaras inicializado - esperando configuración del panel de control")
    
    def _create_control_panel(self):
        """
        Crea el panel de control superior.
        """
        self.control_panel = ControlPanel(
            parent=self.main_container,
            on_cameras_change=self._on_cameras_config_change
        )
    
    def _create_viewer_area(self):
        """
        Crea el área principal de visualización de cámaras.
        """
        # Frame principal para el área de visualización
        self.viewer_main_frame = ttk.LabelFrame(self.main_container, text="Visualización de Cámaras")
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
        
        # Solo hacer bind al root si estamos en modo standalone
        if not self.is_embedded and self.root:
            self.root.bind("<MouseWheel>", _on_mousewheel)
        elif self.is_embedded and self.main_container:
            # En modo embebido, hacer bind al contenedor principal
            self.main_container.bind("<MouseWheel>", _on_mousewheel)
    
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
        Crea widgets de cámaras usando el layout especificado (basado en columnas).
        """
        if not self.cameras_config:
            return
        
        # Obtener layout actual del control panel (número de columnas)
        if hasattr(self, 'control_panel') and self.control_panel:
            self.current_layout = self.control_panel.get_current_layout()
        else:
            self.current_layout = 2  # Por defecto 2 columnas
        
        # Crear frame contenedor para las cámaras
        cameras_container = ttk.Frame(self.viewer_scrollable_frame)
        cameras_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear layout dinámico basado en columnas
        self._create_dynamic_grid_layout(cameras_container, self.current_layout)
        
        self.logger.info(f"Creados {len(self.camera_widgets)} widgets de cámaras con {self.current_layout} columnas")
    
    def _create_dynamic_grid_layout(self, container: ttk.Frame, columns: int):
        """
        Crea layout dinámico basado en número de columnas.
        Las cámaras se distribuyen automáticamente en filas según sea necesario.
        
        Args:
            container: Frame contenedor
            columns: Número de columnas por fila
        """
        if not self.cameras_config:
            return
        
        # Calcular número de filas necesarias
        total_cameras = len(self.cameras_config)
        rows = (total_cameras + columns - 1) // columns  # Redondeo hacia arriba
        
        # Configurar el contenedor para que se expanda completamente
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Crear un frame interno para el grid
        grid_frame = ttk.Frame(container)
        grid_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configurar pesos de filas y columnas para expansión uniforme en el grid
        for i in range(rows):
            grid_frame.grid_rowconfigure(i, weight=1)
        for j in range(columns):
            grid_frame.grid_columnconfigure(j, weight=1)
        
        # Crear widgets en grilla
        for i, camera_config in enumerate(self.cameras_config):
            row = i // columns
            col = i % columns
            
            # Calcular columnspan para la última fila si hay menos cámaras que columnas
            columnspan = 1
            if row == rows - 1:  # Última fila
                cameras_in_last_row = total_cameras - (row * columns)
                if cameras_in_last_row < columns:
                    # Si es la única cámara en la última fila y hay menos cámaras que columnas
                    if cameras_in_last_row == 1 and col == 0:
                        columnspan = columns  # Ocupar todas las columnas
            
            # Frame para cada cámara
            camera_frame = ttk.Frame(grid_frame)
            camera_frame.grid(
                row=row, 
                column=col, 
                columnspan=columnspan,
                sticky="nsew", 
                padx=2, 
                pady=2
            )
            
            # Configurar expansión del frame
            camera_frame.grid_rowconfigure(0, weight=1)
            camera_frame.grid_columnconfigure(0, weight=1)
            
            # Crear widget de cámara
            widget = CameraWidget(camera_frame, camera_config)
            self.camera_widgets.append(widget)
        
        self.logger.info(f"Layout creado: {total_cameras} cámaras en {rows} filas x {columns} columnas")
    
    def _on_closing(self):
        """
        Maneja el evento de cierre de la aplicación (solo modo standalone).
        """
        # Solo aplicar en modo standalone
        if self.is_embedded:
            return
            
        # Evitar doble cierre
        if self._closing_app:
            return
            
        self._closing_app = True
        
        try:
            self.logger.info("Cerrando aplicación...")
            
            # Limpiar todos los widgets de cámaras
            self._clear_camera_widgets()
            
            # Verificar si la ventana aún existe antes de destruirla
            if self.root and self.root.winfo_exists():
                self.root.destroy()
            
            self.logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {str(e)}")
            try:
                # Intentar forzar cierre solo si la ventana aún existe
                if hasattr(self, 'root') and self.root and self.root.winfo_exists():
                    self.root.quit()
            except:
                pass  # Ignorar errores en el cierre forzado
    
    def run(self):
        """
        Inicia el loop principal de la aplicación (solo modo standalone).
        """
        if self.is_embedded:
            self.logger.warning("run() llamado en modo embebido - ignorando")
            return
            
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
    
    def cleanup(self):
        """
        Limpia recursos del visor (para modo embebido).
        """
        try:
            self.logger.info("Limpiando recursos del visor...")
            
            # Limpiar widgets de cámaras
            self._clear_camera_widgets()
            
            # Limpiar panel de control si tiene método cleanup
            if hasattr(self.control_panel, 'cleanup'):
                self.control_panel.cleanup()
            
            # En modo embebido, destruir el frame principal
            if self.is_embedded and hasattr(self, 'main_frame'):
                self.main_frame.destroy()
            
            self.logger.info("Recursos del visor limpiados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error limpiando recursos del visor: {str(e)}")
    
    def refresh(self):
        """
        Refresca la vista del visor (para modo embebido).
        """
        try:
            self.logger.info("Refrescando vista del visor...")
            
            # Refrescar configuración de cámaras
            if hasattr(self.control_panel, 'refresh'):
                self.control_panel.refresh()
            
            # Recrear widgets de cámaras si es necesario
            if self.cameras_config:
                self._recreate_camera_widgets()
            
            self.logger.info("Vista del visor refrescada")
            
        except Exception as e:
            self.logger.error(f"Error refrescando vista del visor: {str(e)}")
    
    def get_current_config(self) -> List[Dict[str, Any]]:
        """
        Obtiene la configuración actual de cámaras.
        
        Returns:
            Lista con la configuración actual de cámaras
        """
        return self.cameras_config.copy()
    
    def set_layout(self, columns: int):
        """
        Establece el layout de columnas.
        
        Args:
            columns: Número de columnas para el layout
        """
        if columns > 0:
            self.current_layout = columns
            self._recreate_camera_widgets()
            self.logger.info(f"Layout cambiado a {columns} columnas")


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