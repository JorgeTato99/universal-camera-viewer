"""
Panel de configuración para el escaneo de puertos.
Agrupa controles de modo, IP, timeout, intensidad y credenciales.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple
from .ip_selector_widget import IPSelectorWidget
from .credentials_widget import CredentialsWidget

# cspell:disable
class ScanConfigPanel:
    """
    Panel de configuración para el escaneo de puertos.
    
    Agrupa todos los controles de configuración en un diseño horizontal
    optimizado con modo, configuración básica y credenciales.
    """
    
    def __init__(self, parent_container: tk.Widget):
        """
        Inicializa el panel de configuración.
        
        Args:
            parent_container: Contenedor padre donde se colocará el panel
        """
        self.parent_container = parent_container
        
        # Variables de configuración
        self.scan_mode = tk.StringVar(value="simple")
        self.ip_var = tk.StringVar(value="192.168.1.178")
        self.timeout_var = tk.DoubleVar(value=3.0)
        self.intensity_var = tk.StringVar(value="basic")
        
        # Variables de estado para UX mejorada
        self.validation_status = tk.StringVar(value="✅ Configuración válida")
        self.scan_in_progress = False
        
        # Widgets especializados
        self.ip_selector: Optional[IPSelectorWidget] = None
        self.credentials_widget: Optional[CredentialsWidget] = None
        
        # Callbacks
        self.on_mode_change_callback: Optional[Callable] = None
        self.on_config_change_callback: Optional[Callable] = None
        
        # Callbacks para botones de control
        self.on_start_scan_callback: Optional[Callable] = None
        self.on_stop_scan_callback: Optional[Callable] = None
        self.on_clear_results_callback: Optional[Callable] = None
        
        self._create_panel()
        self._setup_keyboard_shortcuts()
        self._setup_validation()
    
    def _create_panel(self):
        """Crea el panel de configuración con diseño horizontal optimizado."""
        # Frame principal con mejor espaciado
        self.main_frame = ttk.Frame(self.parent_container)
        self.main_frame.pack(fill=tk.X, padx=8, pady=3)
        
        # Barra de estado de validación
        self._create_validation_bar()
        
        # Contenedor de configuración
        config_container = ttk.Frame(self.main_frame)
        config_container.pack(fill=tk.X, pady=(5, 0))
        
        # Columna 1: Modo de Escaneo (más compacta)
        self._create_mode_column(config_container)
        
        # Columna 2: Configuración Básica (optimizada)
        self._create_config_column(config_container)
        
        # Columna 3: Credenciales (inicialmente oculta)
        self._create_credentials_column(config_container)
        
        # Barra de acciones rápidas
        self._create_quick_actions_bar()
    
    def _create_validation_bar(self):
        """Crea una barra de estado de validación en tiempo real."""
        validation_frame = ttk.Frame(self.main_frame)
        validation_frame.pack(fill=tk.X, pady=(0, 3))
        
        # Indicador de estado
        self.validation_label = ttk.Label(
            validation_frame, 
            textvariable=self.validation_status,
            font=("Arial", 8),
            foreground="#2e7d32"
        )
        self.validation_label.pack(side=tk.LEFT)
        
        # Indicador de modo actual
        self.mode_indicator = ttk.Label(
            validation_frame,
            text="🔍 Modo Simple",
            font=("Arial", 8, "bold"),
            foreground="#1976d2"
        )
        self.mode_indicator.pack(side=tk.RIGHT)
    
    def _create_quick_actions_bar(self):
        """Crea una barra de acciones rápidas con shortcuts."""
        actions_frame = ttk.Frame(self.main_frame)
        actions_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Separador visual
        ttk.Separator(actions_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
        
        # Frame para botones
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack()
        
        # Botones de control del escaneo con shortcuts
        self.scan_button = ttk.Button(
            buttons_frame, 
            text="🔍 Escanear (F5)", 
            command=self._on_start_scan,
            width=15
        )
        self.scan_button.pack(side=tk.LEFT, padx=3)
        
        self.stop_button = ttk.Button(
            buttons_frame, 
            text="⏹ Detener (Esc)", 
            command=self._on_stop_scan, 
            state=tk.DISABLED,
            width=15
        )
        self.stop_button.pack(side=tk.LEFT, padx=3)
        
        self.clear_button = ttk.Button(
            buttons_frame, 
            text="🗑 Limpiar (Ctrl+L)", 
            command=self._on_clear_results,
            width=15
        )
        self.clear_button.pack(side=tk.LEFT, padx=3)
        
        # Botón de configuración avanzada
        self.advanced_config_btn = ttk.Button(
            buttons_frame,
            text="⚙️ Configuración",
            command=self._show_advanced_config,
            width=15
        )
        self.advanced_config_btn.pack(side=tk.LEFT, padx=3)
    
    def _create_mode_column(self, parent):
        """Crea la columna de modo de escaneo más compacta."""
        mode_frame = ttk.LabelFrame(parent, text="Modo", padding=5)
        mode_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        
        # Radio buttons con mejor diseño
        simple_radio = ttk.Radiobutton(
            mode_frame, 
            text="🔍 Simple",
            variable=self.scan_mode,
            value="simple",
            command=self._on_mode_change
        )
        simple_radio.pack(anchor=tk.W, pady=1)
        self._add_tooltip(simple_radio, "Escaneo básico de puertos\nRápido y eficiente")
        
        advanced_radio = ttk.Radiobutton(
            mode_frame,
            text="🔐 Avanzado",
            variable=self.scan_mode,
            value="advanced",
            command=self._on_mode_change
        )
        advanced_radio.pack(anchor=tk.W, pady=1)
        self._add_tooltip(advanced_radio, "Escaneo con autenticación\nIncluye pruebas de URLs y servicios")
        
        # Descripción más compacta
        desc_label = ttk.Label(
            mode_frame, 
            text="Simple: Puertos básicos\nAvanzado: + Autenticación",
            font=("Arial", 7),
            foreground="#666666"
        )
        desc_label.pack(pady=(5, 0))
    
    def _create_config_column(self, parent):
        """Crea la columna de configuración básica optimizada."""
        config_frame = ttk.LabelFrame(parent, text="Configuración", padding=5)
        config_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        
        # Fila 1: IP y botones rápidos (más compacta)
        ip_row = ttk.Frame(config_frame)
        ip_row.pack(fill=tk.X, pady=1)
        
        # Widget selector de IP
        self.ip_selector = IPSelectorWidget(ip_row, self.ip_var)
        self.ip_selector.set_ip_change_callback(self._on_config_change)
        
        # Fila 2: Controles de escaneo (reorganizada)
        control_row = ttk.Frame(config_frame)
        control_row.pack(fill=tk.X, pady=2)
        
        # Timeout con mejor UX
        timeout_frame = ttk.Frame(control_row)
        timeout_frame.pack(side=tk.LEFT)
        
        ttk.Label(timeout_frame, text="Timeout:").pack(side=tk.LEFT)
        self.timeout_spin = ttk.Spinbox(
            timeout_frame, 
            from_=1.0, 
            to=10.0, 
            increment=0.5, 
            textvariable=self.timeout_var, 
            width=5,
            command=self._on_config_change
        )
        self.timeout_spin.pack(side=tk.LEFT, padx=(3, 2))
        ttk.Label(timeout_frame, text="s").pack(side=tk.LEFT)
        self._add_tooltip(self.timeout_spin, "Tiempo límite por puerto\nRecomendado: 3-5 segundos")
        
        # Separador visual
        ttk.Separator(control_row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        
        # Selector de intensidad mejorado
        intensity_frame = ttk.Frame(control_row)
        intensity_frame.pack(side=tk.LEFT)
        
        ttk.Label(intensity_frame, text="Intensidad:").pack(side=tk.LEFT)
        self.intensity_combo = ttk.Combobox(
            intensity_frame, 
            textvariable=self.intensity_var, 
            values=["basic", "medium", "high", "maximum"], 
            width=8, 
            state="readonly"
        )
        self.intensity_combo.pack(side=tk.LEFT, padx=(3, 0))
        self.intensity_combo.bind("<<ComboboxSelected>>", lambda e: self._on_config_change())
        
        # Tooltip mejorado para intensidad
        self._add_tooltip(self.intensity_combo, self._get_intensity_tooltip())
        
        # Indicador visual de configuración
        self.config_status_frame = ttk.Frame(config_frame)
        self.config_status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.config_status_label = ttk.Label(
            self.config_status_frame,
            text="⚡ Configuración optimizada para velocidad",
            font=("Arial", 7),
            foreground="#1976d2"
        )
        self.config_status_label.pack()
    
    def _create_credentials_column(self, parent):
        """Crea la columna de credenciales (inicialmente oculta)."""
        self.credentials_frame = ttk.LabelFrame(parent, text="Credenciales", padding=5)
        # Inicialmente no se empaqueta (oculto)
        
        # Widget de credenciales
        self.credentials_widget = CredentialsWidget(self.credentials_frame)
        self.credentials_widget.set_credentials_change_callback(self._on_credentials_change)
    
    def _setup_keyboard_shortcuts(self):
        """Configura shortcuts de teclado para mejor UX."""
        # Obtener la ventana principal
        root = self.parent_container.winfo_toplevel()
        
        # F5 para escanear
        root.bind('<F5>', lambda e: self._on_start_scan() if not self.scan_in_progress else None)
        
        # Escape para detener
        root.bind('<Escape>', lambda e: self._on_stop_scan() if self.scan_in_progress else None)
        
        # Ctrl+L para limpiar
        root.bind('<Control-l>', lambda e: self._on_clear_results())
        
        # Ctrl+1 y Ctrl+2 para cambiar modo
        root.bind('<Control-Key-1>', lambda e: self._set_mode("simple"))
        root.bind('<Control-Key-2>', lambda e: self._set_mode("advanced"))
    
    def _setup_validation(self):
        """Configura validación en tiempo real."""
        # Validar cuando cambien los valores
        self.ip_var.trace_add("write", self._validate_config_realtime)
        self.timeout_var.trace_add("write", self._validate_config_realtime)
        self.intensity_var.trace_add("write", self._validate_config_realtime)
    
    def _validate_config_realtime(self, *args):
        """Valida la configuración en tiempo real y actualiza el estado visual."""
        is_valid, message = self.validate_config()
        
        if is_valid:
            self.validation_status.set("✅ Configuración válida")
            self.validation_label.config(foreground="#2e7d32")
            self.scan_button.config(state=tk.NORMAL)
        else:
            self.validation_status.set(f"⚠️ {message}")
            self.validation_label.config(foreground="#d32f2f")
            self.scan_button.config(state=tk.DISABLED)
        
        # Actualizar indicador de configuración
        self._update_config_indicator()
    
    def _update_config_indicator(self):
        """Actualiza el indicador visual de configuración."""
        timeout = self.timeout_var.get()
        intensity = self.intensity_var.get()
        
        if timeout <= 2 and intensity == "basic":
            status = "⚡ Configuración optimizada para velocidad"
            color = "#1976d2"
        elif timeout >= 5 and intensity in ["high", "maximum"]:
            status = "🔍 Configuración optimizada para precisión"
            color = "#7b1fa2"
        else:
            status = "⚖️ Configuración balanceada"
            color = "#f57c00"
        
        self.config_status_label.config(text=status, foreground=color)
    
    def _add_tooltip(self, widget, text):
        """Agrega tooltip a un widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(
                tooltip, 
                text=text, 
                background="#ffffcc",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Arial", 8)
            )
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)  # Auto-hide después de 3 segundos
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def _get_intensity_tooltip(self):
        """Obtiene el texto del tooltip para intensidad."""
        return (
            "Niveles de intensidad para pruebas:\n\n"
            "• Basic: URLs más comunes (rápido)\n"
            "• Medium: URLs comunes + específicas\n"
            "• High: Pruebas exhaustivas (lento)\n"
            "• Maximum: Todas las URLs disponibles\n\n"
            "💡 Recomendado: Basic para escaneos rápidos"
        )
    
    def _show_advanced_config(self):
        """Muestra diálogo de configuración avanzada."""
        # Crear ventana de configuración avanzada
        config_window = tk.Toplevel(self.parent_container.winfo_toplevel())
        config_window.title("Configuración Avanzada")
        config_window.geometry("400x300")
        config_window.transient(self.parent_container.winfo_toplevel())
        config_window.grab_set()
        
        # Centrar ventana
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (config_window.winfo_screenheight() // 2) - (300 // 2)
        config_window.geometry(f"400x300+{x}+{y}")
        
        # Contenido de configuración avanzada
        notebook = ttk.Notebook(config_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de rendimiento
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Rendimiento")
        
        ttk.Label(perf_frame, text="Configuraciones de rendimiento:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Opciones de rendimiento
        ttk.Checkbutton(perf_frame, text="Escaneo paralelo (más rápido)").pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(perf_frame, text="Cache de resultados DNS").pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(perf_frame, text="Optimización de red").pack(anchor=tk.W, pady=2)
        
        # Pestaña de logging
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Logging")
        
        ttk.Label(log_frame, text="Configuración de logs:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        ttk.Checkbutton(log_frame, text="Log detallado de conexiones").pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(log_frame, text="Guardar logs en archivo").pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(log_frame, text="Log de errores de red").pack(anchor=tk.W, pady=2)
        
        # Botones
        button_frame = ttk.Frame(config_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Aplicar", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=config_window.destroy).pack(side=tk.RIGHT)
    
    def _set_mode(self, mode: str):
        """Establece el modo de escaneo programáticamente."""
        self.scan_mode.set(mode)
        self._on_mode_change()
    
    def _on_mode_change(self):
        """Maneja el cambio de modo de escaneo con mejor feedback visual."""
        mode = self.scan_mode.get()
        
        # Actualizar indicador visual
        if mode == "simple":
            self.mode_indicator.config(text="🔍 Modo Simple", foreground="#1976d2")
            self.credentials_frame.pack_forget()
        else:
            self.mode_indicator.config(text="🔐 Modo Avanzado", foreground="#7b1fa2")
            self.credentials_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))
        
        # Callback externo
        if self.on_mode_change_callback:
            self.on_mode_change_callback(mode)
        
        # Revalidar configuración
        self._validate_config_realtime()
    
    def _on_config_change(self, *args):
        """Callback cuando cambia la configuración."""
        if self.on_config_change_callback:
            self.on_config_change_callback(self.get_config())
    
    def _on_credentials_change(self, *args):
        """Callback cuando cambian las credenciales."""
        self._on_config_change()
    
    def _on_start_scan(self):
        """Callback interno para iniciar escaneo."""
        if self.on_start_scan_callback:
            self.on_start_scan_callback()
    
    def _on_stop_scan(self):
        """Callback interno para detener escaneo."""
        if self.on_stop_scan_callback:
            self.on_stop_scan_callback()
    
    def _on_clear_results(self):
        """Callback interno para limpiar resultados."""
        if self.on_clear_results_callback:
            self.on_clear_results_callback()
    
    def get_config(self) -> dict:
        """
        Obtiene la configuración actual.
        
        Returns:
            Diccionario con toda la configuración
        """
        config = {
            "mode": self.scan_mode.get(),
            "ip": self.ip_var.get().strip(),
            "timeout": self.timeout_var.get(),
            "intensity": self.intensity_var.get()
        }
        
        if self.scan_mode.get() == "advanced" and self.credentials_widget:
            username, password = self.credentials_widget.get_credentials()
            config.update({
                "username": username,
                "password": password
            })
        
        return config
    
    def set_mode_change_callback(self, callback: Callable[[str], None]):
        """Establece el callback para cambios de modo."""
        self.on_mode_change_callback = callback
    
    def set_config_change_callback(self, callback: Callable[[dict], None]):
        """Establece el callback para cambios de configuración."""
        self.on_config_change_callback = callback
    
    def set_scan_callbacks(self, 
                          start_callback: Callable = None,
                          stop_callback: Callable = None,
                          clear_callback: Callable = None):
        """
        Establece los callbacks para las acciones de escaneo.
        
        Args:
            start_callback: Función para iniciar escaneo
            stop_callback: Función para detener escaneo
            clear_callback: Función para limpiar resultados
        """
        if start_callback:
            self.on_start_scan_callback = start_callback
        if stop_callback:
            self.on_stop_scan_callback = stop_callback
        if clear_callback:
            self.on_clear_results_callback = clear_callback
    
    def validate_config(self) -> Tuple[bool, str]:
        """
        Valida la configuración actual.
        
        Returns:
            Tupla con (es_válida, mensaje_error)
        """
        # Validar IP
        if not self.ip_selector or not self.ip_selector.validate_ip():
            return False, "Ingrese una IP válida"
        
        # Validar credenciales en modo avanzado
        if self.scan_mode.get() == "advanced":
            if not self.credentials_widget or not self.credentials_widget.validate_credentials():
                return False, "Ingrese credenciales válidas para el modo avanzado"
        
        return True, ""
    
    def set_enabled(self, enabled: bool):
        """
        Habilita o deshabilita el panel.
        
        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        
        # Deshabilitar controles principales
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if hasattr(child, 'config'):
                        try:
                            child.config(state=state)
                        except:
                            pass
        
        # Deshabilitar widgets especializados
        if self.credentials_widget:
            self.credentials_widget.set_enabled(enabled)
    
    def start_scan_mode(self, scan_mode: str = "simple"):
        """
        Configura la UI para modo de escaneo con mejor feedback visual.
        
        Args:
            scan_mode: Modo de escaneo actual
        """
        self.scan_in_progress = True
        
        # Actualizar botones con animación visual
        self.scan_button.config(state=tk.DISABLED, text="🔄 Escaneando...")
        self.stop_button.config(state=tk.NORMAL)
        
        # Deshabilitar controles de configuración
        self.timeout_spin.config(state=tk.DISABLED)
        self.intensity_combo.config(state=tk.DISABLED)
        
        # Actualizar estado visual
        self.validation_status.set("🔄 Escaneo en progreso...")
        self.validation_label.config(foreground="#ff9800")
        
        # Deshabilitar widgets especializados
        if self.ip_selector:
            self.ip_selector.set_enabled(False)
        if self.credentials_widget and scan_mode == "advanced":
            self.credentials_widget.set_enabled(False)
    
    def stop_scan_mode(self):
        """
        Restaura la UI después del escaneo con transición suave.
        """
        self.scan_in_progress = False
        
        # Restaurar botones
        self.scan_button.config(state=tk.NORMAL, text="🔍 Escanear (F5)")
        self.stop_button.config(state=tk.DISABLED)
        
        # Rehabilitar controles
        self.timeout_spin.config(state=tk.NORMAL)
        self.intensity_combo.config(state=tk.NORMAL)
        
        # Rehabilitar widgets especializados
        if self.ip_selector:
            self.ip_selector.set_enabled(True)
        if self.credentials_widget:
            self.credentials_widget.set_enabled(True)
        
        # Revalidar configuración
        self._validate_config_realtime() 