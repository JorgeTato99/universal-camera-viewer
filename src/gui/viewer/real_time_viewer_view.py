"""
Vista del visor en tiempo real para múltiples cámaras.
Versión adaptada para funcionar como componente embebido en la aplicación principal.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .camera_widget import CameraWidget
from .control_panel import ControlPanel


class RealTimeViewerView:
    """
    Vista del visor en tiempo real para múltiples cámaras.
    Funciona como componente embebido sin crear ventana propia.
    """
    
    def __init__(self, parent_container: tk.Widget):
        """
        Inicializa la vista del visor.
        
        Args:
            parent_container: Contenedor padre donde se embebida la vista
        """
        # Configurar logging
        self.logger = logging.getLogger("RealTimeViewerView")
        
        # Contenedor padre
        self.parent_container = parent_container
        
        # Lista de widgets de cámaras activos
        self.camera_widgets: List[CameraWidget] = []
        
        # Configuración actual de cámaras
        self.cameras_config: List[Dict[str, Any]] = []
        
        # Layout actual
        self.current_layout = "grid_2x2"
        
        # Bandera para evitar doble cierre
        self._closing_view = False
        
        # Crear contenido de la vista
        self._create_view_content()
        
        # Crear panel de control
        self._create_control_panel()
        
        # Crear área de visualización
        self._create_viewer_area()
        
        # Inicializar configuración por defecto
        self._initialize_default_cameras()
        
        self.logger.info("Vista del visor en tiempo real inicializada")
    
    def _create_view_content(self):
        """
        Crea el contenido principal de la vista.
        """
        # Frame principal de la vista
        self.main_frame = ttk.Frame(self.parent_container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_control_panel(self):
        """
        Crea el panel de control de la vista.
        """
        self.control_panel = ControlPanel(
            parent=self.main_frame,
            on_cameras_change=self._on_cameras_config_change
        )
    
    def _create_viewer_area(self):
        """
        Crea el área de visualización de cámaras.
        """
        # Frame principal para el área de visualización
        self.viewer_main_frame = ttk.LabelFrame(self.main_frame, text="Visualización de Cámaras")
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
• Soporte para ONVIF, RTSP y conexiones especializadas
• Captura de snapshots individuales
• Grabación de video (próximamente)
• Layouts configurables (1x1, 2x2, 3x3, etc.)
• Guardado y carga de configuraciones
• Soporte multi-marca: Dahua, TP-Link, Steren
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
        messagebox.showinfo(
            "Configuración de Ejemplo", 
            "¡La configuración de ejemplo ya está cargada!\n\n"
            "Ve a la pestaña 'Cámaras' para ver las cámaras configuradas.\n"
            "Puedes modificar las IPs y credenciales según tu setup.\n\n"
            "Marcas soportadas:\n"
            "• Dahua Hero-K51H\n"
            "• TP-Link Tapo C520WS\n"
            "• Steren CCTV-235"
        )
    
    def _bind_mousewheel(self):
        """
        Configura el scroll con la rueda del mouse.
        """
        def _on_mousewheel(event):
            self.viewer_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind a diferentes elementos para asegurar compatibilidad
        self.viewer_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.main_frame.bind("<MouseWheel>", _on_mousewheel)
    
    def _initialize_default_cameras(self):
        """
        Inicializa la configuración por defecto de cámaras.
        """
        try:
            # Obtener la configuración de cámaras del control panel
            default_cameras = self.control_panel.get_cameras_config()
            if default_cameras:
                self.logger.info("Aplicando configuración inicial de cámaras")
                self._on_cameras_config_change(default_cameras)
        except Exception as e:
            self.logger.warning(f"No se pudo aplicar configuración inicial: {str(e)}")
    
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
        
        # Obtener layout actual del control panel
        if hasattr(self, 'control_panel') and self.control_panel:
            self.current_layout = self.control_panel.get_current_layout()
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
        """Crea layout de una sola cámara."""
        if self.cameras_config:
            widget = CameraWidget(container, self.cameras_config[0])
            self.camera_widgets.append(widget)
    
    def _create_horizontal_layout(self, container: ttk.Frame, count: int):
        """Crea layout horizontal."""
        for i, camera_config in enumerate(self.cameras_config[:count]):
            frame = ttk.Frame(container)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            widget = CameraWidget(frame, camera_config)
            self.camera_widgets.append(widget)
    
    def _create_vertical_layout(self, container: ttk.Frame, count: int):
        """Crea layout vertical."""
        for i, camera_config in enumerate(self.cameras_config[:count]):
            frame = ttk.Frame(container)
            frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            widget = CameraWidget(frame, camera_config)
            self.camera_widgets.append(widget)
    
    def _create_grid_layout(self, container: ttk.Frame, cols: int, rows: int):
        """Crea layout en grilla."""
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
    
    def cleanup(self):
        """
        Limpia la vista y libera recursos.
        """
        if self._closing_view:
            return
            
        self._closing_view = True
        
        try:
            self.logger.info("Limpiando vista del visor...")
            
            # Limpiar todos los widgets de cámaras
            self._clear_camera_widgets()
            
            # Limpiar el frame principal
            if hasattr(self, 'main_frame'):
                self.main_frame.destroy()
            
            self.logger.info("Vista del visor limpiada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar vista del visor: {str(e)}")
    
    def refresh(self):
        """
        Refresca la vista del visor.
        """
        try:
            self.logger.info("Refrescando vista del visor...")
            self._recreate_camera_widgets()
        except Exception as e:
            self.logger.error(f"Error refrescando vista: {str(e)}")
    
    def get_current_config(self) -> List[Dict[str, Any]]:
        """
        Obtiene la configuración actual de cámaras.
        
        Returns:
            Lista con configuración de cámaras
        """
        return self.cameras_config.copy()
    
    def set_layout(self, layout: str):
        """
        Cambia el layout de visualización.
        
        Args:
            layout: Nuevo layout a aplicar
        """
        self.current_layout = layout
        if hasattr(self, 'control_panel'):
            self.control_panel.set_current_layout(layout)
        self._recreate_camera_widgets() 