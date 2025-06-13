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
        
        # Variables para mejoras UX
        self.status_bar = None
        self.toolbar = None
        
        # Crear interfaz según el modo
        if self.is_embedded:
            self._create_embedded_interface()
        else:
            self._create_standalone_interface()
        
        # Crear barra de herramientas PRIMERO
        self._create_toolbar()
        
        # Crear PanedWindow para permitir redimensionamiento manual
        self.main_paned = ttk.PanedWindow(self.main_container, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Crear panel de control PRIMERO (sin agregar al PanedWindow aún)
        self._create_control_panel()
        
        # Crear área de visualización DESPUÉS (sin agregar al PanedWindow aún)
        self._create_viewer_area()
        
        # Ahora configurar el PanedWindow con el orden correcto
        self._setup_paned_window()
        
        # Crear barra de estado
        self._create_status_bar()
        
        # Configurar shortcuts de teclado
        self._setup_keyboard_shortcuts()
        
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
        self.root.title("🎥 Visor Universal de Cámaras - Módulo Principal")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        
        # Configurar el estilo
        self._setup_styles()
        
        # Configurar colores y estilos mejorados
        self.root.configure(bg='#f8f9fa')
        
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
        
        # Configurar estilos también en modo embebido
        self._setup_styles()
    
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
            
            # Configurar estilos personalizados
            style.configure('Title.TLabel', font=('Arial', 12, 'bold'), foreground='#2c3e50')
            style.configure('Status.TLabel', font=('Arial', 9), foreground='#7f8c8d')
            style.configure('Success.TLabel', font=('Arial', 9), foreground='#27ae60')
            style.configure('Error.TLabel', font=('Arial', 9), foreground='#e74c3c')
            style.configure('Warning.TLabel', font=('Arial', 9), foreground='#f39c12')
            
            # Estilos para botones
            style.configure('Action.TButton', font=('Arial', 9, 'bold'))
            style.configure('Success.TButton', foreground='#27ae60')
            style.configure('Danger.TButton', foreground='#e74c3c')
            
        except Exception as e:
            self.logger.warning(f"No se pudo configurar tema: {str(e)}")
    
    def _create_toolbar(self):
        """
        Crea la barra de herramientas superior con acciones rápidas.
        """
        self.toolbar_frame = ttk.Frame(self.main_container)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Separador visual
        ttk.Separator(self.toolbar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)
        
        # Frame para botones de la toolbar
        buttons_frame = ttk.Frame(self.toolbar_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botones de acción rápida
        self.connect_all_btn = ttk.Button(
            buttons_frame,
            text="🔗 Conectar Todas",
            command=self._connect_all_cameras,
            style='Success.TButton'
        )
        self.connect_all_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(self.connect_all_btn, "Conectar todas las cámaras configuradas (F5)")
        
        self.disconnect_all_btn = ttk.Button(
            buttons_frame,
            text="🔌 Desconectar Todas",
            command=self._disconnect_all_cameras,
            style='Danger.TButton'
        )
        self.disconnect_all_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(self.disconnect_all_btn, "Desconectar todas las cámaras (F6)")
        
        ttk.Separator(buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        self.snapshot_all_btn = ttk.Button(
            buttons_frame,
            text="📸 Capturar Todas",
            command=self._snapshot_all_cameras,
            style='Action.TButton'
        )
        self.snapshot_all_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(self.snapshot_all_btn, "Capturar snapshot de todas las cámaras conectadas (F8)")
        
        self.refresh_btn = ttk.Button(
            buttons_frame,
            text="🔄 Refrescar",
            command=self._refresh_all_cameras,
            style='Action.TButton'
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(self.refresh_btn, "Refrescar estado de todas las cámaras (F9)")
        
        ttk.Separator(buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Indicador de estado global
        self.global_status_label = ttk.Label(
            buttons_frame,
            text="⚪ Sistema Iniciado",
            style='Status.TLabel'
        )
        self.global_status_label.pack(side=tk.LEFT, padx=10)
        
        # Contador de cámaras
        self.cameras_count_label = ttk.Label(
            buttons_frame,
            text="📹 0 cámaras",
            style='Status.TLabel'
        )
        self.cameras_count_label.pack(side=tk.RIGHT, padx=5)
        
        # Separador visual inferior
        ttk.Separator(self.toolbar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)
    
    def _create_status_bar(self):
        """
        Crea la barra de estado inferior con información detallada.
        """
        self.status_frame = ttk.Frame(self.main_container)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # Separador visual superior
        ttk.Separator(self.status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)
        
        # Frame para elementos de estado
        status_elements_frame = ttk.Frame(self.status_frame)
        status_elements_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Estado de conexión
        self.connection_status_label = ttk.Label(
            status_elements_frame,
            text="🔴 Desconectado",
            style='Error.TLabel'
        )
        self.connection_status_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(status_elements_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # FPS promedio
        self.fps_label = ttk.Label(
            status_elements_frame,
            text="📊 FPS: 0.0",
            style='Status.TLabel'
        )
        self.fps_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(status_elements_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Memoria utilizada
        self.memory_label = ttk.Label(
            status_elements_frame,
            text="💾 RAM: 0 MB",
            style='Status.TLabel'
        )
        self.memory_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(status_elements_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Tiempo de actividad
        self.uptime_label = ttk.Label(
            status_elements_frame,
            text="⏱️ Tiempo: 00:00:00",
            style='Status.TLabel'
        )
        self.uptime_label.pack(side=tk.LEFT, padx=5)
        
        # Ayuda de shortcuts (lado derecho)
        self.shortcuts_label = ttk.Label(
            status_elements_frame,
            text="💡 F1: Ayuda | F5: Conectar | F6: Desconectar | F8: Capturar",
            style='Status.TLabel'
        )
        self.shortcuts_label.pack(side=tk.RIGHT, padx=5)
    
    def _setup_keyboard_shortcuts(self):
        """
        Configura los shortcuts de teclado para acciones rápidas.
        """
        if not self.is_embedded and self.root:
            # Shortcuts globales
            self.root.bind('<F1>', lambda e: self._show_help_dialog())
            self.root.bind('<F5>', lambda e: self._connect_all_cameras())
            self.root.bind('<F6>', lambda e: self._disconnect_all_cameras())
            self.root.bind('<F8>', lambda e: self._snapshot_all_cameras())
            self.root.bind('<F9>', lambda e: self._refresh_all_cameras())
            self.root.bind('<Control-q>', lambda e: self._on_closing())
            self.root.bind('<Control-s>', lambda e: self._save_config_shortcut())
            self.root.bind('<Control-o>', lambda e: self._load_config_shortcut())
            
            self.logger.info("Shortcuts de teclado configurados")
    
    def _add_tooltip(self, widget, text):
        """
        Agrega un tooltip a un widget.
        
        Args:
            widget: Widget al que agregar el tooltip
            text: Texto del tooltip
        """
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("Arial", 8)
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
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
        Crea el panel de control integrado.
        """
        from src.viewer.control_panel import ControlPanel
        
        # Crear el panel de control en el PanedWindow
        self.control_panel = ControlPanel(
            parent=self.main_paned,  # Usar el PanedWindow como padre
            on_cameras_change=self._on_cameras_config_change
        )
        
        # NOTA: Se agregará al PanedWindow en _setup_paned_window() para controlar el orden
    
    def _create_viewer_area(self):
        """
        Crea el área principal de visualización de cámaras.
        """
        # Frame principal para el área de visualización - PRIORIDAD MÁXIMA
        self.viewer_main_frame = ttk.LabelFrame(
            self.main_paned,  # Usar el PanedWindow como padre
            text="📹 Visualización de Cámaras en Tiempo Real"
        )
        
        # NOTA: Se agregará al PanedWindow en _setup_paned_window() para controlar el orden
        
        # Frame contenedor con scroll
        self.viewer_canvas = tk.Canvas(self.viewer_main_frame, bg='#ffffff', highlightthickness=0)
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
        
        # IMPORTANTE: Procesar configuración pendiente si existe
        self.logger.info("🎯 Área de visualización creada, verificando configuración pendiente...")
        if hasattr(self, '_pending_cameras_config'):
            self.logger.info(f"📋 Procesando configuración pendiente: {len(self._pending_cameras_config)} cámaras")
            # Procesar la configuración que estaba esperando
            pending_config = self._pending_cameras_config
            delattr(self, '_pending_cameras_config')  # Limpiar la configuración pendiente
            
            # Procesar la configuración ahora que el área está lista
            self._on_cameras_config_change(pending_config)
        else:
            self.logger.info("📝 No hay configuración pendiente")
    
    def _show_initial_message(self):
        """
        Muestra un mensaje inicial mejorado cuando no hay cámaras configuradas.
        """
        self.initial_message_frame = ttk.Frame(self.viewer_scrollable_frame)
        self.initial_message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=50)
        
        # Icono y mensaje de bienvenida
        welcome_frame = ttk.Frame(self.initial_message_frame)
        welcome_frame.pack(pady=20)
        
        icon_label = ttk.Label(
            welcome_frame,
            text="🎥",
            font=("Arial", 48)
        )
        icon_label.pack(pady=10)
        
        welcome_label = ttk.Label(
            welcome_frame,
            text="¡Bienvenido al Visor Universal de Cámaras!",
            font=("Arial", 18, "bold"),
            style='Title.TLabel'
        )
        welcome_label.pack(pady=5)
        
        subtitle_label = ttk.Label(
            welcome_frame,
            text="Sistema profesional de videovigilancia multi-marca",
            font=("Arial", 11),
            style='Status.TLabel'
        )
        subtitle_label.pack(pady=2)
        
        # Instrucciones mejoradas con iconos
        instructions_frame = ttk.LabelFrame(self.initial_message_frame, text="🚀 Guía de Inicio Rápido")
        instructions_frame.pack(fill=tk.X, pady=20)
        
        instructions = [
            ("1️⃣", "Ve a la pestaña 'Cámaras' en el panel de control"),
            ("2️⃣", "Agrega una o más cámaras usando 'Agregar Cámara'"),
            ("3️⃣", "Configura IP, credenciales y protocolo (ONVIF recomendado)"),
            ("4️⃣", "Selecciona el layout deseado en la pestaña 'Layout'"),
            ("5️⃣", "¡Las cámaras aparecerán aquí automáticamente!")
        ]
        
        for icon, text in instructions:
            instruction_frame = ttk.Frame(instructions_frame)
            instruction_frame.pack(fill=tk.X, padx=10, pady=3)
            
            ttk.Label(instruction_frame, text=icon, font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
            ttk.Label(instruction_frame, text=text, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Características destacadas
        features_frame = ttk.LabelFrame(self.initial_message_frame, text="✨ Características Principales")
        features_frame.pack(fill=tk.X, pady=20)
        
        features = [
            ("🎯", "Soporte multi-marca: Dahua, TP-Link, Steren, cámaras genéricas"),
            ("⚡", "Protocolos optimizados: ONVIF, RTSP, HTTP/CGI"),
            ("📱", "Layouts configurables: 1x1, 2x2, 3x3, 4x4"),
            ("📸", "Captura de snapshots HD instantánea"),
            ("🔧", "Configuración persistente y perfiles guardados"),
            ("⌨️", "Shortcuts de teclado para acciones rápidas")
        ]
        
        # Crear dos columnas para las características
        left_features = ttk.Frame(features_frame)
        left_features.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        right_features = ttk.Frame(features_frame)
        right_features.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        for i, (icon, text) in enumerate(features):
            container = left_features if i < 3 else right_features
            feature_frame = ttk.Frame(container)
            feature_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(feature_frame, text=icon, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
            ttk.Label(feature_frame, text=text, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Botones de acción
        actions_frame = ttk.Frame(self.initial_message_frame)
        actions_frame.pack(pady=20)
        
        example_button = ttk.Button(
            actions_frame,
            text="📋 Cargar Configuración de Ejemplo",
            command=self._load_example_config,
            style='Action.TButton'
        )
        example_button.pack(side=tk.LEFT, padx=5)
        self._add_tooltip(example_button, "Carga una configuración de ejemplo con cámara Dahua")
        
        help_button = ttk.Button(
            actions_frame,
            text="❓ Mostrar Ayuda",
            command=self._show_help_dialog,
            style='Action.TButton'
        )
        help_button.pack(side=tk.LEFT, padx=5)
        self._add_tooltip(help_button, "Muestra ayuda detallada y shortcuts (F1)")
    
    def _load_example_config(self):
        """
        Carga una configuración de ejemplo mejorada.
        """
        # La configuración de ejemplo ya está cargada por defecto en el control panel
        messagebox.showinfo(
            "📋 Configuración de Ejemplo", 
            "¡La configuración de ejemplo ya está cargada!\n\n"
            "🎥 Ve a la pestaña 'Cámaras' para ver las cámaras configuradas.\n"
            "⚙️ Puedes modificar IPs y credenciales según tu setup.\n"
            "🚀 Usa F5 para conectar todas las cámaras rápidamente."
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
        self.logger.info(f"🔄 CALLBACK: Configuración de cámaras actualizada: {len(cameras_config)} cámaras")
        
        # Debug: Mostrar configuración recibida
        for i, camera in enumerate(cameras_config):
            self.logger.info(f"  📹 Cámara {i+1}: {camera.get('name', 'Sin nombre')} - {camera.get('ip', 'Sin IP')}")
        
        # Actualizar configuración SIEMPRE
        self.cameras_config = cameras_config
        
        # Actualizar contador en toolbar
        self._update_cameras_count(len(cameras_config))
        
        # Verificar que el área de visualización esté lista
        if not hasattr(self, 'viewer_scrollable_frame'):
            self.logger.warning("⏳ Área de visualización no está lista, guardando configuración para procesar después")
            # Guardar configuración para procesar después
            self._pending_cameras_config = cameras_config
            return
        
        self.logger.info("✅ Área de visualización lista, procediendo a recrear widgets...")
        
        # Recrear widgets de cámaras
        self._recreate_camera_widgets()
        
        # Actualizar estado global
        if cameras_config:
            self._update_global_status(f"📹 {len(cameras_config)} cámaras configuradas", "Success")
        else:
            self._update_global_status("⚪ Sin cámaras configuradas", "Status")
    
    def _update_cameras_count(self, count: int):
        """
        Actualiza el contador de cámaras en la toolbar.
        
        Args:
            count: Número de cámaras configuradas
        """
        if hasattr(self, 'cameras_count_label'):
            if count == 0:
                text = "📹 Sin cámaras"
            elif count == 1:
                text = "📹 1 cámara"
            else:
                text = f"📹 {count} cámaras"
            
            self.cameras_count_label.config(text=text)
    
    def _recreate_camera_widgets(self):
        """
        Recrea todos los widgets de cámaras basado en la configuración actual.
        """
        self.logger.info(f"🔄 Recreando widgets de cámaras...")
        
        # Limpiar widgets existentes
        self._clear_camera_widgets()
        
        # Si no hay cámaras, mostrar mensaje inicial
        if not self.cameras_config:
            self.logger.info("📝 No hay cámaras configuradas, mostrando mensaje inicial")
            self._show_initial_message()
            return
        
        # Ocultar mensaje inicial si está visible
        if hasattr(self, 'initial_message_frame'):
            self.initial_message_frame.destroy()
        
        # Crear nuevos widgets basados en el layout
        self._create_camera_widgets_with_layout()
        
        # Actualizar estado de conexión
        self._update_connection_status()
    
    def _update_connection_status(self):
        """
        Actualiza el estado de conexión en la barra de estado.
        """
        if not hasattr(self, 'connection_status_label'):
            return
        
        if not self.camera_widgets:
            self.connection_status_label.config(text="🔴 Sin cámaras", style="Error.TLabel")
            return
        
        connected_count = 0
        total_count = len(self.camera_widgets)
        
        for widget in self.camera_widgets:
            if hasattr(widget, 'is_connected') and widget.is_connected():
                connected_count += 1
        
        if connected_count == 0:
            self.connection_status_label.config(text="🔴 Desconectado", style="Error.TLabel")
        elif connected_count == total_count:
            self.connection_status_label.config(text="🟢 Todas conectadas", style="Success.TLabel")
        else:
            self.connection_status_label.config(
                text=f"🟡 {connected_count}/{total_count} conectadas", 
                style="Warning.TLabel"
            )
    
    def _clear_camera_widgets(self):
        """
        Limpia todos los widgets de cámaras existentes.
        """
        self.logger.info(f"🧹 Limpiando {len(self.camera_widgets)} widgets existentes...")
        
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
        
        self.logger.info("✅ Widgets limpiados correctamente")

    def _create_camera_widgets_with_layout(self):
        """
        Crea widgets de cámaras usando el layout especificado (basado en columnas).
        """
        self.logger.info(f"📱 Iniciando creación de widgets con layout...")
        
        if not self.cameras_config:
            self.logger.warning("❌ No hay configuración de cámaras")
            return
        
        # Obtener layout actual del control panel (número de columnas)
        if hasattr(self, 'control_panel') and self.control_panel:
            self.current_layout = self.control_panel.get_current_layout()
        else:
            self.current_layout = 2  # Por defecto 2 columnas
        
        self.logger.info(f"📐 Layout seleccionado: {self.current_layout} columnas")
        
        # Crear frame contenedor para las cámaras
        cameras_container = ttk.Frame(self.viewer_scrollable_frame)
        cameras_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.logger.info(f"📦 Frame contenedor creado y empaquetado")
        
        # Crear layout dinámico basado en columnas
        self._create_dynamic_grid_layout(cameras_container, self.current_layout)
        
        self.logger.info(f"✅ Proceso completado: {len(self.camera_widgets)} widgets de cámara creados con {self.current_layout} columnas")
    
    def _create_dynamic_grid_layout(self, container: ttk.Frame, columns: int):
        """
        Crea layout dinámico basado en número de columnas.
        Las cámaras se distribuyen automáticamente en filas según sea necesario.
        
        Args:
            container: Frame contenedor
            columns: Número de columnas por fila
        """
        self.logger.info(f"🏗️ Creando layout dinámico: {len(self.cameras_config)} cámaras en {columns} columnas")
        
        if not self.cameras_config:
            self.logger.warning("❌ No hay configuración de cámaras para crear layout")
            return
        
        # Calcular número de filas necesarias
        total_cameras = len(self.cameras_config)
        rows = (total_cameras + columns - 1) // columns  # Redondeo hacia arriba
        
        self.logger.info(f"📐 Layout calculado: {rows} filas x {columns} columnas para {total_cameras} cámaras")
        
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
        
        self.logger.info(f"🎯 Iniciando creación de {total_cameras} widgets de cámara...")
        
        # Crear widgets en grilla
        for i, camera_config in enumerate(self.cameras_config):
            row = i // columns
            col = i % columns
            
            self.logger.info(f"🔧 Creando widget {i+1}/{total_cameras}: {camera_config.get('name', 'Sin nombre')} en posición ({row}, {col})")
            
            # Calcular columnspan para la última fila si hay menos cámaras que columnas
            columnspan = 1
            if row == rows - 1:  # Última fila
                cameras_in_last_row = total_cameras - (row * columns)
                if cameras_in_last_row < columns:
                    # Si es la única cámara en la última fila y hay menos cámaras que columnas
                    if cameras_in_last_row == 1 and col == 0:
                        columnspan = columns  # Ocupar todas las columnas
            
            # Crear widget de cámara mejorado
            try:
                self.logger.info(f"🏭 Instanciando CameraWidget para {camera_config.get('name', 'Sin nombre')}...")
                
                camera_widget = CameraWidget(
                    parent=grid_frame,
                    camera_config=camera_config,
                    on_status_change=self._on_camera_status_change
                )
                
                self.logger.info(f"✅ CameraWidget creado exitosamente para {camera_config.get('name', 'Sin nombre')}")
                
                # Posicionar en grid con columnspan calculado
                camera_widget.grid(
                    row=row, 
                    column=col, 
                    columnspan=columnspan,
                    sticky="nsew", 
                    padx=3, 
                    pady=3
                )
            
                # Agregar a la lista
                self.camera_widgets.append(camera_widget)
                
                self.logger.info(f"🎉 Widget de cámara agregado exitosamente: {camera_config.get('name', 'Sin nombre')} en posición ({row}, {col})")
                
            except Exception as e:
                self.logger.error(f"❌ ERROR creando widget de cámara {camera_config.get('name', 'Sin nombre')}: {str(e)}")
                self.logger.error(f"❌ Traceback completo:", exc_info=True)
                
                # Crear widget de error como fallback
                error_frame = ttk.LabelFrame(grid_frame, text=f"❌ Error: {camera_config.get('name', 'Cámara')}")
                error_frame.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=3, pady=3)
                
                error_label = ttk.Label(
                    error_frame,
                    text=f"Error al crear widget:\n{str(e)}",
                    style="Error.TLabel",
                    justify=tk.CENTER
                )
                error_label.pack(expand=True)
        
        self.logger.info(f"🏁 Proceso de creación completado. Total widgets creados: {len(self.camera_widgets)}")
    
    def _on_camera_status_change(self, camera_name: str, status: str):
        """
        Callback cuando cambia el estado de una cámara individual.
        
        Args:
            camera_name: Nombre de la cámara
            status: Nuevo estado
        """
        self.logger.info(f"Estado de cámara '{camera_name}' cambió a: {status}")
        
        # Actualizar estado global de conexión
        self._update_connection_status()
        
        # Actualizar métricas si es necesario
        self._update_metrics()
    
    def _update_metrics(self):
        """
        Actualiza las métricas en la barra de estado.
        """
        try:
            # Actualizar FPS promedio
            if self.camera_widgets:
                total_fps = 0
                active_cameras = 0
                
                for widget in self.camera_widgets:
                    if hasattr(widget, 'get_fps'):
                        fps = widget.get_fps()
                        if fps > 0:
                            total_fps += fps
                            active_cameras += 1
                
                avg_fps = total_fps / active_cameras if active_cameras > 0 else 0
                self.fps_label.config(text=f"📊 FPS: {avg_fps:.1f}")
            else:
                self.fps_label.config(text="📊 FPS: 0.0")
            
            # Actualizar memoria (si psutil está disponible)
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_label.config(text=f"💾 RAM: {memory_mb:.0f} MB")
            except ImportError:
                self.memory_label.config(text="💾 RAM: N/A")
            
        except Exception as e:
            self.logger.error(f"Error actualizando métricas: {e}")
    
    def _on_closing(self):
        """
        Maneja el cierre de la aplicación.
        """
        if self._closing_app:
            return
            
        self._closing_app = True
        
        try:
            self.logger.info("Cerrando aplicación...")
            
            # Actualizar estado
            self._update_global_status("🔄 Cerrando aplicación...", "Warning")
            
            # Limpiar widgets de cámaras
            self._clear_camera_widgets()
            
            # Limpiar panel de control si tiene método cleanup
            if hasattr(self.control_panel, 'cleanup'):
                self.control_panel.cleanup()
            
            # Solo destruir root si estamos en modo standalone
            if not self.is_embedded and self.root:
                self.root.quit()
                self.root.destroy()
            
            self.logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {str(e)}")
    
    def run(self):
        """
        Inicia el loop principal de la aplicación (solo modo standalone).
        """
        if self.is_embedded:
            self.logger.warning("run() llamado en modo embebido - ignorando")
            return
            
        try:
            self.logger.info("Iniciando aplicación...")
            self._update_global_status("✅ Aplicación iniciada", "Success")
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
            
            # Actualizar métricas
            self._update_metrics()
            
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
            self._update_global_status(f"📱 Layout cambiado a {columns} columnas", "Success")
            self.logger.info(f"Layout cambiado a {columns} columnas")
    
    # Métodos de acción para la toolbar
    def _connect_all_cameras(self):
        """Conecta todas las cámaras configuradas."""
        if not self.camera_widgets:
            messagebox.showinfo("Información", "No hay cámaras configuradas para conectar.")
            return
        
        self._update_global_status("🔄 Conectando cámaras...", "Warning")
        connected_count = 0
        
        for widget in self.camera_widgets:
            try:
                if hasattr(widget, 'connect'):
                    widget.connect()
                    connected_count += 1
            except Exception as e:
                self.logger.error(f"Error conectando cámara: {e}")
        
        if connected_count > 0:
            self._update_global_status(f"✅ {connected_count} cámaras conectadas", "Success")
        else:
            self._update_global_status("❌ Error conectando cámaras", "Error")
    
    def _disconnect_all_cameras(self):
        """Desconecta todas las cámaras."""
        if not self.camera_widgets:
            return
        
        self._update_global_status("🔄 Desconectando cámaras...", "Warning")
        disconnected_count = 0
        
        for widget in self.camera_widgets:
            try:
                if hasattr(widget, 'disconnect'):
                    widget.disconnect()
                    disconnected_count += 1
            except Exception as e:
                self.logger.error(f"Error desconectando cámara: {e}")
        
        if disconnected_count > 0:
            self._update_global_status(f"🔌 {disconnected_count} cámaras desconectadas", "Status")
        
    def _snapshot_all_cameras(self):
        """Captura snapshot de todas las cámaras conectadas."""
        if not self.camera_widgets:
            messagebox.showinfo("Información", "No hay cámaras configuradas.")
            return
        
        self._update_global_status("📸 Capturando snapshots...", "Warning")
        captured_count = 0
        
        for widget in self.camera_widgets:
            try:
                if hasattr(widget, 'capture_snapshot'):
                    widget.capture_snapshot()
                    captured_count += 1
            except Exception as e:
                self.logger.error(f"Error capturando snapshot: {e}")
        
        if captured_count > 0:
            self._update_global_status(f"📸 {captured_count} snapshots capturados", "Success")
            messagebox.showinfo("Éxito", f"Se capturaron {captured_count} snapshots exitosamente.")
        else:
            self._update_global_status("❌ Error capturando snapshots", "Error")
    
    def _refresh_all_cameras(self):
        """Refresca el estado de todas las cámaras."""
        if not self.camera_widgets:
            return
        
        self._update_global_status("🔄 Refrescando cámaras...", "Warning")
        
        for widget in self.camera_widgets:
            try:
                if hasattr(widget, 'refresh'):
                    widget.refresh()
            except Exception as e:
                self.logger.error(f"Error refrescando cámara: {e}")
        
        self._update_global_status("✅ Cámaras refrescadas", "Success")
    
    def _update_global_status(self, message: str, status_type: str = "Status"):
        """
        Actualiza el estado global en la toolbar.
        
        Args:
            message: Mensaje a mostrar
            status_type: Tipo de estado (Status, Success, Error, Warning)
        """
        if hasattr(self, 'global_status_label'):
            self.global_status_label.config(text=message)
            
            # Cambiar estilo según el tipo
            style_map = {
                "Status": "Status.TLabel",
                "Success": "Success.TLabel", 
                "Error": "Error.TLabel",
                "Warning": "Warning.TLabel"
            }
            
            if status_type in style_map:
                self.global_status_label.config(style=style_map[status_type])
    
    def _show_help_dialog(self):
        """Muestra un diálogo de ayuda con shortcuts y funciones."""
        help_window = tk.Toplevel(self.root if self.root else self.main_container)
        help_window.title("❓ Ayuda - Visor Universal de Cámaras")
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        # Centrar ventana
        help_window.transient(self.root if self.root else self.main_container)
        help_window.grab_set()
        
        # Notebook para organizar la ayuda
        help_notebook = ttk.Notebook(help_window)
        help_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de shortcuts
        shortcuts_frame = ttk.Frame(help_notebook)
        help_notebook.add(shortcuts_frame, text="⌨️ Shortcuts")
        
        shortcuts_text = """
SHORTCUTS DE TECLADO:

F1          - Mostrar esta ayuda
F5          - Conectar todas las cámaras
F6          - Desconectar todas las cámaras  
F8          - Capturar snapshots de todas las cámaras
F9          - Refrescar estado de todas las cámaras
Ctrl+S      - Guardar configuración actual
Ctrl+O      - Cargar configuración desde archivo
Ctrl+Q      - Salir de la aplicación

NAVEGACIÓN:
Tab         - Navegar entre controles
Enter       - Activar botón seleccionado
Escape      - Cancelar diálogos
        """
        
        shortcuts_label = ttk.Label(shortcuts_frame, text=shortcuts_text, font=("Courier", 10), justify=tk.LEFT)
        shortcuts_label.pack(padx=10, pady=10)
        
        # Pestaña de funciones
        functions_frame = ttk.Frame(help_notebook)
        help_notebook.add(functions_frame, text="🔧 Funciones")
        
        functions_text = """
FUNCIONES PRINCIPALES:

🎥 GESTIÓN DE CÁMARAS:
   • Agregar/editar/eliminar cámaras
   • Soporte multi-protocolo (ONVIF, RTSP, HTTP)
   • Configuración automática por marca
   
📱 LAYOUTS DINÁMICOS:
   • 1x1, 2x2, 3x3, 4x4 columnas
   • Redimensionado automático
   • Columnspan inteligente
   
📸 CAPTURA Y GRABACIÓN:
   • Snapshots HD instantáneos
   • Grabación de video (próximamente)
   • Exportación en múltiples formatos
   
⚙️ CONFIGURACIÓN:
   • Perfiles guardados
   • Configuración persistente
   • Importar/exportar configuraciones
        """
        
        functions_label = ttk.Label(functions_frame, text=functions_text, font=("Arial", 10), justify=tk.LEFT)
        functions_label.pack(padx=10, pady=10)
        
        # Botón cerrar
        close_button = ttk.Button(help_window, text="Cerrar", command=help_window.destroy)
        close_button.pack(pady=10)
    
    def _save_config_shortcut(self):
        """Shortcut para guardar configuración."""
        if hasattr(self.control_panel, '_save_config'):
            self.control_panel._save_config()
    
    def _load_config_shortcut(self):
        """Shortcut para cargar configuración."""
        if hasattr(self.control_panel, '_load_config'):
            self.control_panel._load_config()

    def _setup_paned_window(self):
        """
        Configura el PanedWindow con el orden correcto.
        Viewer area arriba (70%), control panel abajo (30%).
        """
        # Agregar PRIMERO el viewer area (arriba) con peso mayor
        self.main_paned.add(self.viewer_main_frame, weight=3)
        
        # Agregar DESPUÉS el control panel (abajo) con peso menor  
        self.main_paned.add(self.control_panel.main_frame, weight=1)
        
        # Configurar proporción inicial después de un breve delay
        self.main_container.after(100, self._configure_paned_proportions)
        
    def _configure_paned_proportions(self):
        """
        Configura las proporciones iniciales del PanedWindow.
        70% para el visor (arriba), 30% para el panel de control (abajo).
        """
        try:
            # Obtener altura total del contenedor
            total_height = self.main_paned.winfo_height()
            if total_height > 100:  # Solo si ya se ha renderizado
                # Configurar 70% para visor (arriba), 30% para control (abajo)
                viewer_height = int(total_height * 0.7)
                # El sashpos define dónde está el divisor - debe estar al 70% desde arriba
                self.main_paned.sashpos(0, viewer_height)
                self.logger.info(f"Proporciones configuradas: Visor {viewer_height}px (70%), Control {total_height - viewer_height}px (30%)")
            else:
                # Si no se ha renderizado, intentar de nuevo en 200ms
                self.main_container.after(200, self._configure_paned_proportions)
        except Exception as e:
            self.logger.warning(f"No se pudieron configurar proporciones: {e}")
            # Intentar de nuevo en 500ms
            self.main_container.after(500, self._configure_paned_proportions)


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