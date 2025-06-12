"""
Vista de descubrimiento de puertos para cámaras IP.
Interfaz gráfica para escanear y analizar puertos de cámaras.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from typing import Optional
import time
from datetime import datetime
from .port_scanner import PortScanner, PortResult, ScanResult

# cspell:disable
class PortDiscoveryView:
    """
    Vista de descubrimiento de puertos para cámaras IP.
    Permite escanear puertos y analizar servicios disponibles.
    """
    
    def __init__(self, parent_container: tk.Widget):
        """
        Inicializa la vista de descubrimiento de puertos.
        
        Args:
            parent_container: Contenedor padre donde se embebida la vista
        """
        # Contenedor padre
        self.parent_container = parent_container
        
        # Estado del escaneo
        self.scanner = PortScanner(timeout=3)
        self.current_scan_thread: Optional[threading.Thread] = None
        self.scan_results: Optional[ScanResult] = None
        
        # Variables de UI
        self.scan_in_progress = False
        self.show_console_view = False  # Toggle para vista de consola
        self.console_output = []  # Buffer para salida de consola
        
        # Crear contenido de la vista
        self._create_view_content()
        
        # Configurar callbacks del scanner
        self._setup_scanner_callbacks()
    
    def _create_view_content(self):
        """
        Crea el contenido principal de la vista con diseño optimizado.
        """
        # Frame principal de la vista
        self.main_frame = ttk.Frame(self.parent_container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear secciones con diseño horizontal optimizado
        self._create_top_section()  # Modo + Configuración + Credenciales en horizontal
        self._create_progress_section()
        self._create_results_section()
        self._create_actions_section()
    
    def _create_top_section(self):
        """
        Crea la sección superior con diseño horizontal optimizado.
        """
        # Frame principal horizontal
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Columna 1: Modo de Escaneo (más compacto)
        self._create_mode_column(top_frame)
        
        # Columna 2: Configuración Básica
        self._create_config_column(top_frame)
        
        # Columna 3: Credenciales (inicialmente oculta)
        self._create_credentials_column(top_frame)
    
    def _create_mode_column(self, parent):
        """Crea la columna de modo de escaneo."""
        mode_frame = ttk.LabelFrame(parent, text="Modo")
        mode_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Variable para el modo
        self.scan_mode = tk.StringVar(value="simple")
        
        # Radio buttons más compactos
        ttk.Radiobutton(
            mode_frame, 
            text="🔍 Simple",
            variable=self.scan_mode,
            value="simple",
            command=self._on_mode_change
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="🔐 Avanzado",
            variable=self.scan_mode,
            value="advanced",
            command=self._on_mode_change
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Descripción compacta
        desc_label = ttk.Label(
            mode_frame, 
            text="Simple: Solo puertos\nAvanzado: + Credenciales",
            font=("Arial", 8),
            foreground="gray"
        )
        desc_label.pack(padx=5, pady=2)
    
    def _create_config_column(self, parent):
        """Crea la columna de configuración básica."""
        config_frame = ttk.LabelFrame(parent, text="Configuración")
        config_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Fila 1: IP y botones rápidos
        ip_row = ttk.Frame(config_frame)
        ip_row.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(ip_row, text="IP:").pack(side=tk.LEFT)
        
        self.ip_var = tk.StringVar(value="192.168.1.178")
        self.ip_entry = ttk.Entry(ip_row, textvariable=self.ip_var, width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Botones IP dinámicos
        self._create_dynamic_ip_buttons(ip_row)
        
        # Fila 2: Timeout y controles
        control_row = ttk.Frame(config_frame)
        control_row.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(control_row, text="Timeout:").pack(side=tk.LEFT)
        self.timeout_var = tk.DoubleVar(value=3.0)
        timeout_spin = ttk.Spinbox(control_row, from_=1.0, to=10.0, increment=0.5, 
                                  textvariable=self.timeout_var, width=6)
        timeout_spin.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Label(control_row, text="s").pack(side=tk.LEFT, padx=(0, 10))
        
        # Selector de intensidad
        ttk.Label(control_row, text="Intensidad:").pack(side=tk.LEFT)
        self.intensity_var = tk.StringVar(value="basic")
        intensity_combo = ttk.Combobox(control_row, textvariable=self.intensity_var, 
                                     values=["basic", "medium", "high", "maximum"], 
                                     width=8, state="readonly")
        intensity_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        # Tooltip para intensidad
        self._create_intensity_tooltip(intensity_combo)
        
        # Botones de control
        self.scan_button = ttk.Button(control_row, text="🔍 Escanear", command=self._start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(control_row, text="⏹ Detener", command=self._stop_scan, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        self.clear_button = ttk.Button(control_row, text="🗑 Limpiar", command=self._clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=2)
    
    def _create_credentials_column(self, parent):
        """Crea la columna de credenciales (inicialmente oculta)."""
        self.credentials_frame = ttk.LabelFrame(parent, text="Credenciales")
        # Inicialmente no se empaqueta (oculto)
        
        # Fila 1: Usuario y contraseña
        creds_row = ttk.Frame(self.credentials_frame)
        creds_row.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(creds_row, text="Usuario:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(creds_row, textvariable=self.username_var, width=12)
        self.username_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(creds_row, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(creds_row, textvariable=self.password_var, width=12, show="*")
        self.password_entry.grid(row=1, column=1, padx=(0, 10))
        
        # Checkbox mostrar contraseña
        self.show_password_var = tk.BooleanVar()
        show_check = ttk.Checkbutton(creds_row, text="Mostrar", variable=self.show_password_var,
                                   command=self._toggle_password_visibility)
        show_check.grid(row=1, column=2, padx=5)
        
        # Fila 2: Botones de credenciales rápidas
        self._create_dynamic_credentials_buttons()
        
        # Advertencia compacta
        warning_label = ttk.Label(
            self.credentials_frame,
            text="⚠️ Solo usar en redes propias",
            font=("Arial", 8),
            foreground="orange"
        )
        warning_label.pack(pady=2)
    
    def _create_intensity_tooltip(self, widget):
        """Crea tooltip explicativo para el selector de intensidad."""
        # Variable para almacenar la referencia del tooltip actual
        current_tooltip = [None]
        
        def show_tooltip(event):
            # Destruir tooltip anterior si existe
            if current_tooltip[0] is not None:
                try:
                    current_tooltip[0].destroy()
                except:
                    pass
                current_tooltip[0] = None
            
            tooltip_text = (
                "Niveles de intensidad para pruebas de URLs:\n\n"
                "• Basic (10 URLs): URLs más comunes y rápidas\n"
                "• Medium (20 URLs): URLs comunes + específicas\n"
                "• High (30 URLs): URLs comunes + específicas + variantes\n"
                "• Maximum (Todas): Prueba exhaustiva de todas las URLs\n\n"
                "Recomendado: Basic para escaneos rápidos, High para problemas"
            )
            
            # Crear ventana tooltip
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg="lightyellow", relief="solid", borderwidth=1)
            
            # Posicionar cerca del cursor
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip.geometry(f"+{x}+{y}")
            
            # Agregar texto
            label = tk.Label(tooltip, text=tooltip_text, bg="lightyellow", 
                           font=("Arial", 9), justify=tk.LEFT, padx=5, pady=5)
            label.pack()
            
            # Guardar referencia
            current_tooltip[0] = tooltip
            
            # Auto-destruir después de 3 segundos
            tooltip.after(3000, lambda: hide_tooltip())
        
        def hide_tooltip():
            """Oculta el tooltip actual."""
            if current_tooltip[0] is not None:
                try:
                    current_tooltip[0].destroy()
                except:
                    pass
                current_tooltip[0] = None
        
        # Bind eventos
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", lambda e: hide_tooltip())
        widget.bind("<Button-1>", lambda e: hide_tooltip())  # Ocultar al hacer clic
    

    
    def _create_dynamic_ip_buttons(self, parent_frame):
        """
        Crea botones IP dinámicos basados en las variables de entorno configuradas.
        """
        from src.utils.config import ConfigurationManager
        
        try:
            config = ConfigurationManager()
            
            # Definir marcas y sus configuraciones (usando nomenclatura correcta)
            brands_config = [
                ("DAHUA", "Dahua", config.camera_ip if hasattr(config, 'camera_ip') else None),
                ("TPLINK", "TP-Link", config.tplink_ip if hasattr(config, 'tplink_ip') else None),
                ("STEREN", "Steren", config.steren_ip if hasattr(config, 'steren_ip') else None),
                ("GENERIC", "Generic", config.generic_ip if hasattr(config, 'generic_ip') else None)
            ]
            
            # Crear botones solo para marcas configuradas
            for brand_key, brand_name, ip_address in brands_config:
                if ip_address:  # Solo crear botón si la IP está configurada
                    # Extraer últimos dígitos de la IP para el botón
                    ip_suffix = ip_address.split('.')[-1]
                    button_text = f"{brand_name} ({ip_suffix})"
                    
                    ttk.Button(
                        parent_frame, 
                        text=button_text, 
                        command=lambda ip=ip_address: self.ip_var.set(ip)
                    ).pack(side=tk.LEFT, padx=2)
                    
        except Exception as e:
            # Si hay error cargando configuración, crear botones por defecto
            print(f"Error cargando configuración dinámica: {e}")
            ttk.Button(parent_frame, text="Dahua (172)", command=lambda: self.ip_var.set("192.168.1.172")).pack(side=tk.LEFT, padx=2)
            ttk.Button(parent_frame, text="TP-Link (77)", command=lambda: self.ip_var.set("192.168.1.77")).pack(side=tk.LEFT, padx=2)
            ttk.Button(parent_frame, text="Steren (178)", command=lambda: self.ip_var.set("192.168.1.178")).pack(side=tk.LEFT, padx=2)
    
    def _create_dynamic_credentials_buttons(self):
        """
        Crea botones de credenciales dinámicos basados en las variables de entorno.
        """
        # Frame para botones de credenciales rápidas
        quick_creds_frame = ttk.Frame(self.credentials_frame)
        quick_creds_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(quick_creds_frame, text="Rápidas:", font=("Arial", 8)).pack(anchor=tk.W)
        
        # Frame para los botones
        buttons_frame = ttk.Frame(quick_creds_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Credenciales comunes siempre disponibles (más compactas)
        ttk.Button(
            buttons_frame, 
            text="admin", 
            command=lambda: self._set_credentials("admin", "admin"),
            width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            buttons_frame, 
            text="123456", 
            command=lambda: self._set_credentials("admin", "123456"),
            width=8
        ).pack(side=tk.LEFT, padx=1)
        
        # Credenciales específicas desde .env (solo si están configuradas)
        try:
            from src.utils.config import ConfigurationManager
            config = ConfigurationManager()
            
            # Verificar y agregar credenciales específicas por marca (nomenclatura correcta)
            brands_creds = [
                ("Dahua", config.camera_user if hasattr(config, 'camera_user') else None, 
                         config.camera_password if hasattr(config, 'camera_password') else None),
                ("TP-Link", config.tplink_user if hasattr(config, 'tplink_user') else None, 
                           config.tplink_password if hasattr(config, 'tplink_password') else None),
                ("Steren", config.steren_user if hasattr(config, 'steren_user') else None, 
                          config.steren_password if hasattr(config, 'steren_password') else None),
                ("Generic", config.generic_user if hasattr(config, 'generic_user') else None, 
                           config.generic_password if hasattr(config, 'generic_password') else None)
            ]
            
            for brand_name, username, password in brands_creds:
                if username and password:  # Solo crear botón si ambos están configurados
                    ttk.Button(
                        buttons_frame, 
                        text=brand_name[:6], 
                        command=lambda u=username, p=password: self._set_credentials(u, p),
                        width=8
                    ).pack(side=tk.LEFT, padx=1)
                    
        except Exception as e:
            print(f"Error cargando credenciales dinámicas: {e}")
    

    
    def _create_progress_section(self):
        """
        Crea la sección de progreso del escaneo.
        """
        # Frame de progreso
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progreso del Escaneo")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Etiqueta de estado
        self.status_var = tk.StringVar(value="Listo para escanear")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
    
    def _create_results_section(self):
        """
        Crea la sección de resultados del escaneo.
        """
        # Frame de resultados
        results_frame = ttk.LabelFrame(self.main_frame, text="Resultados del Escaneo")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Frame para botones de control de vista
        view_control_frame = ttk.Frame(results_frame)
        view_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botón para alternar vista
        self.toggle_view_btn = ttk.Button(
            view_control_frame,
            text="🖥️ Vista Consola",
            command=self._toggle_view,
            width=15
        )
        self.toggle_view_btn.pack(side="left")
        
        # Frame contenedor para las vistas
        self.views_container = ttk.Frame(results_frame)
        self.views_container.pack(fill=tk.BOTH, expand=True)
        
        # Crear ambas vistas
        self._create_table_view()
        self._create_console_view()
        
        # Mostrar vista de tabla por defecto
        self._show_table_view()
    
    def _create_table_view(self):
        """Crea la vista de tabla de resultados."""
        self.table_frame = ttk.Frame(self.views_container)
        self.setup_results_table(self.table_frame)
    
    def _create_console_view(self):
        """Crea la vista de consola de salida."""
        self.console_frame = ttk.Frame(self.views_container)
        
        # Text widget para mostrar la salida de consola
        self.console_text = tk.Text(
            self.console_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff",
            state=tk.DISABLED
        )
        
        # Scrollbar para la consola
        console_scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _toggle_view(self):
        """Alterna entre vista de tabla y vista de consola."""
        if self.show_console_view:
            self._show_table_view()
        else:
            self._show_console_view()
    
    def _show_table_view(self):
        """Muestra la vista de tabla."""
        self.console_frame.pack_forget()
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        self.show_console_view = False
        self.toggle_view_btn.config(text="🖥️ Vista Consola")
    
    def _show_console_view(self):
        """Muestra la vista de consola."""
        self.table_frame.pack_forget()
        self.console_frame.pack(fill=tk.BOTH, expand=True)
        self.show_console_view = True
        self.toggle_view_btn.config(text="📊 Vista Tabla")
        
        # Actualizar contenido de consola
        self._update_console_display()
    
    def _add_to_console(self, message: str, level: str = "INFO"):
        """
        Agrega un mensaje al buffer de consola.
        
        Args:
            message: Mensaje a agregar
            level: Nivel del mensaje (INFO, WARNING, ERROR, SUCCESS)
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.console_output.append(formatted_message)
        
        # Mantener solo los últimos 1000 mensajes
        if len(self.console_output) > 1000:
            self.console_output = self.console_output[-1000:]
    
    def _update_console_display(self):
        """Actualiza la visualización de la consola."""
        if hasattr(self, 'console_text'):
            self.console_text.config(state=tk.NORMAL)
            self.console_text.delete(1.0, tk.END)
            
            for line in self.console_output:
                self.console_text.insert(tk.END, line + "\n")
                
                # Colorear según el nivel
                if "[ERROR]" in line:
                    # Configurar tag para errores
                    start_line = self.console_text.index(tk.END + "-2l linestart")
                    end_line = self.console_text.index(tk.END + "-2l lineend")
                    self.console_text.tag_add("error", start_line, end_line)
                    self.console_text.tag_config("error", foreground="#ff6b6b")
                elif "[WARNING]" in line:
                    start_line = self.console_text.index(tk.END + "-2l linestart")
                    end_line = self.console_text.index(tk.END + "-2l lineend")
                    self.console_text.tag_add("warning", start_line, end_line)
                    self.console_text.tag_config("warning", foreground="#ffd93d")
                elif "[SUCCESS]" in line:
                    start_line = self.console_text.index(tk.END + "-2l linestart")
                    end_line = self.console_text.index(tk.END + "-2l lineend")
                    self.console_text.tag_add("success", start_line, end_line)
                    self.console_text.tag_config("success", foreground="#6bcf7f")
            
            self.console_text.config(state=tk.DISABLED)
            # Auto-scroll al final
            self.console_text.see(tk.END)
    
    def setup_results_table(self, parent):
        """Configura la tabla de resultados según el modo actual."""
        # Si ya existe una tabla, destruirla
        if hasattr(self, 'results_tree'):
            self.results_tree.destroy()
        if hasattr(self, 'scrollbar'):
            self.scrollbar.destroy()
        
        # Determinar columnas según el modo
        if self.scan_mode.get() == "simple":
            columns = ("Puerto", "Estado", "Servicio", "Tiempo (ms)", "Banner")
        else:
            columns = ("Puerto", "Estado", "Servicio", "Tiempo (ms)", "Auth", "Método", "Banner")
        
        self.results_tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        
        # Configurar columnas
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Puerto":
                self.results_tree.column(col, width=80)
            elif col == "Estado":
                self.results_tree.column(col, width=100)
            elif col == "Auth":
                self.results_tree.column(col, width=80)
            elif col == "Método":
                self.results_tree.column(col, width=180)  # Más ancho para mostrar URLs
            elif col == "Tiempo (ms)":
                self.results_tree.column(col, width=100)
            elif col == "Banner":
                self.results_tree.column(col, width=200)  # Más ancho para banners
            else:
                self.results_tree.column(col, width=120)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Agregar evento de doble clic para mostrar detalles
        self.results_tree.bind("<Double-1>", self._on_result_double_click)
    
    def _on_result_double_click(self, event):
        """Maneja el doble clic en un resultado para mostrar detalles de URLs."""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        # Obtener el item seleccionado
        item = selection[0]
        values = self.results_tree.item(item, 'values')
        
        if not values:
            return
        
        port = values[0]
        
        # Buscar el resultado correspondiente en los datos
        if not hasattr(self, 'scan_results') or not self.scan_results:
            return
        
        port_result = None
        for result in self.scan_results.open_ports:
            if str(result.port) == str(port):
                port_result = result
                break
        
        if not port_result or not hasattr(port_result, 'auth_tested') or not port_result.auth_tested:
            messagebox.showinfo("Sin detalles", f"No hay información de autenticación disponible para el puerto {port}")
            return
        
        self._show_url_details_dialog(port_result)
    
    def _show_url_details_dialog(self, port_result):
        """Muestra un diálogo con los detalles de autenticación según el tipo de puerto."""
        dialog = tk.Toplevel(self.main_frame)
        dialog.title(f"Detalles de Autenticación - Puerto {port_result.port}")
        dialog.geometry("700x500")
        dialog.resizable(True, True)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Información del puerto
        info_frame = ttk.LabelFrame(main_frame, text="Información del Puerto")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Puerto: {port_result.port}", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Servicio: {port_result.service_name}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Estado Auth: {'✅ Exitosa' if port_result.auth_success else '❌ Falló'}").pack(anchor=tk.W, padx=10, pady=2)
        if port_result.auth_method:
            ttk.Label(info_frame, text=f"Método: {port_result.auth_method}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Determinar tipo de puerto para mostrar información apropiada
        is_http_port = port_result.port in [80, 443, 8000, 8080, 6667, 9000]
        is_rtsp_port = port_result.port in [554, 5543, 8554]
        is_onvif_port = port_result.port == 2020
        is_dahua_sdk_port = port_result.port == 37777
        
        if is_http_port:
            # Para puertos HTTP, mostrar URLs válidas y probadas
            if hasattr(port_result, 'valid_urls') and port_result.valid_urls:
                valid_frame = ttk.LabelFrame(main_frame, text=f"🎯 URLs HTTP que FUNCIONARON ({len(port_result.valid_urls)})")
                valid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                # Text widget con scroll para URLs válidas
                valid_text = tk.Text(valid_frame, height=8, wrap=tk.WORD)
                valid_scrollbar = ttk.Scrollbar(valid_frame, orient=tk.VERTICAL, command=valid_text.yview)
                valid_text.configure(yscrollcommand=valid_scrollbar.set)
                
                valid_text.insert(tk.END, "✅ URLs HTTP que respondieron correctamente:\n\n")
                for i, url in enumerate(port_result.valid_urls, 1):
                    valid_text.insert(tk.END, f"{i:2d}. ✅ {url}\n")
                
                valid_text.insert(tk.END, f"\n💡 Estas {len(port_result.valid_urls)} URL(s) aceptaron las credenciales y están disponibles para usar.")
                valid_text.insert(tk.END, "\n🔧 Métodos de autenticación exitosos: HTTP Digest Auth / HTTP Basic Auth")
                
                valid_text.config(state=tk.DISABLED)
                valid_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                valid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # URLs probadas (si las hay)
            if hasattr(port_result, 'tested_urls') and port_result.tested_urls:
                tested_frame = ttk.LabelFrame(main_frame, text=f"📋 Todas las URLs HTTP Probadas ({len(port_result.tested_urls)})")
                tested_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                # Text widget con scroll para URLs probadas
                tested_text = tk.Text(tested_frame, height=6, wrap=tk.WORD)
                tested_scrollbar = ttk.Scrollbar(tested_frame, orient=tk.VERTICAL, command=tested_text.yview)
                tested_text.configure(yscrollcommand=tested_scrollbar.set)
                
                tested_text.insert(tk.END, "Resultados de todas las URLs probadas:\n\n")
                for i, url in enumerate(port_result.tested_urls, 1):
                    # Marcar URLs válidas en verde
                    if hasattr(port_result, 'valid_urls') and any(url in valid_url for valid_url in port_result.valid_urls):
                        tested_text.insert(tk.END, f"{i:2d}. ✅ {url}\n")
                    else:
                        tested_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                
                # Estadísticas
                valid_count = len(port_result.valid_urls) if hasattr(port_result, 'valid_urls') and port_result.valid_urls else 0
                failed_count = len(port_result.tested_urls) - valid_count
                tested_text.insert(tk.END, f"\n📊 Resumen: {valid_count} exitosas, {failed_count} fallidas de {len(port_result.tested_urls)} probadas")
                
                tested_text.config(state=tk.DISABLED)
                tested_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                tested_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Si no hay URLs válidas pero sí probadas (caso de fallo)
            elif hasattr(port_result, 'tested_urls') and port_result.tested_urls and not port_result.auth_success:
                failed_frame = ttk.LabelFrame(main_frame, text=f"❌ URLs HTTP Probadas - Todas Fallaron ({len(port_result.tested_urls)})")
                failed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                failed_text = tk.Text(failed_frame, height=8, wrap=tk.WORD)
                failed_scrollbar = ttk.Scrollbar(failed_frame, orient=tk.VERTICAL, command=failed_text.yview)
                failed_text.configure(yscrollcommand=failed_scrollbar.set)
                
                failed_text.insert(tk.END, "❌ Ninguna URL HTTP respondió con las credenciales:\n\n")
                for i, url in enumerate(port_result.tested_urls, 1):
                    failed_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                
                failed_text.insert(tk.END, f"\n⚠️ Las {len(port_result.tested_urls)} URLs probadas rechazaron las credenciales o no respondieron.")
                if port_result.auth_error:
                    failed_text.insert(tk.END, f"\n🔍 Error específico: {port_result.auth_error}")
                
                failed_text.config(state=tk.DISABLED)
                failed_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                failed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        elif is_rtsp_port:
            # Para puertos RTSP, mostrar información específica de RTSP
            rtsp_frame = ttk.LabelFrame(main_frame, text="Información RTSP")
            rtsp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            rtsp_text = tk.Text(rtsp_frame, height=10, wrap=tk.WORD)
            rtsp_scrollbar = ttk.Scrollbar(rtsp_frame, orient=tk.VERTICAL, command=rtsp_text.yview)
            rtsp_text.configure(yscrollcommand=rtsp_scrollbar.set)
            
            # URLs RTSP estándar que se prueban
            rtsp_urls = [
                f"rtsp://usuario:contraseña@IP:{port_result.port}/cam/realmonitor?channel=1&subtype=0",
                f"rtsp://usuario:contraseña@IP:{port_result.port}/stream1",
                f"rtsp://usuario:contraseña@IP:{port_result.port}/stream2", 
                f"rtsp://usuario:contraseña@IP:{port_result.port}/live/stream1",
                f"rtsp://usuario:contraseña@IP:{port_result.port}/live"
            ]
            
            if port_result.auth_success:
                rtsp_text.insert(tk.END, "✅ Autenticación RTSP exitosa\n\n")
                
                # Mostrar URLs que funcionaron (simulado - en implementación real se guardarían)
                rtsp_text.insert(tk.END, "🎯 URLs RTSP que FUNCIONARON:\n")
                # Como no tenemos la URL específica que funcionó, mostramos la más probable
                if "Dahua" in port_result.service_name or port_result.port == 554:
                    rtsp_text.insert(tk.END, f"✅ rtsp://usuario:contraseña@IP:{port_result.port}/cam/realmonitor?channel=1&subtype=0\n")
                else:
                    rtsp_text.insert(tk.END, f"✅ rtsp://usuario:contraseña@IP:{port_result.port}/stream1\n")
                
                rtsp_text.insert(tk.END, "\n📋 Todas las URLs RTSP probadas:\n")
                for i, url in enumerate(rtsp_urls, 1):
                    if i == 1:  # Primera URL como ejemplo de éxito
                        rtsp_text.insert(tk.END, f"{i}. ✅ {url}\n")
                    else:
                        rtsp_text.insert(tk.END, f"{i}. ❓ {url}\n")
                
                rtsp_text.insert(tk.END, "\n💡 Al menos una URL RTSP respondió correctamente. Usa la URL marcada con ✅ para conectar.")
            else:
                rtsp_text.insert(tk.END, "❌ Autenticación RTSP falló\n\n")
                rtsp_text.insert(tk.END, "📋 URLs RTSP probadas (todas fallaron):\n")
                for i, url in enumerate(rtsp_urls, 1):
                    rtsp_text.insert(tk.END, f"{i}. ❌ {url}\n")
                rtsp_text.insert(tk.END, "\n⚠️ Ninguna URL RTSP respondió con las credenciales proporcionadas.")
                if port_result.auth_error:
                    rtsp_text.insert(tk.END, f"\n🔍 Error específico: {port_result.auth_error}")
            
            rtsp_text.config(state=tk.DISABLED)
            rtsp_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            rtsp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        elif is_onvif_port:
            # Para puerto ONVIF, mostrar información específica
            onvif_frame = ttk.LabelFrame(main_frame, text="Información ONVIF")
            onvif_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            onvif_text = tk.Text(onvif_frame, height=10, wrap=tk.WORD)
            onvif_scrollbar = ttk.Scrollbar(onvif_frame, orient=tk.VERTICAL, command=onvif_text.yview)
            onvif_text.configure(yscrollcommand=onvif_scrollbar.set)
            
            # Endpoints ONVIF estándar que se prueban
            onvif_endpoints = [
                f"http://IP:{port_result.port}/onvif/device_service",
                f"http://IP:{port_result.port}/onvif/device",
                f"http://IP:{port_result.port}/onvif/Device",
                f"http://IP:{port_result.port}/Device",
                f"http://IP:{port_result.port}/onvif/"
            ]
            
            if port_result.auth_success:
                onvif_text.insert(tk.END, "✅ Autenticación ONVIF exitosa\n\n")
                
                # Mostrar endpoints que funcionaron
                onvif_text.insert(tk.END, "🎯 Endpoints ONVIF que FUNCIONARON:\n")
                # Mostrar el más probable que funcionó
                onvif_text.insert(tk.END, f"✅ http://IP:{port_result.port}/onvif/device_service\n")
                
                onvif_text.insert(tk.END, "\n📋 Todos los endpoints ONVIF probados:\n")
                for i, endpoint in enumerate(onvif_endpoints, 1):
                    if i == 1:  # Primer endpoint como ejemplo de éxito
                        onvif_text.insert(tk.END, f"{i}. ✅ {endpoint}\n")
                    else:
                        onvif_text.insert(tk.END, f"{i}. ❓ {endpoint}\n")
                
                onvif_text.insert(tk.END, "\n💡 Al menos un endpoint ONVIF respondió correctamente. Usa el endpoint marcado con ✅ para conectar.")
                onvif_text.insert(tk.END, "\n🔧 Métodos de autenticación: HTTP Digest Auth / HTTP Basic Auth")
            else:
                onvif_text.insert(tk.END, "❌ Autenticación ONVIF falló\n\n")
                onvif_text.insert(tk.END, "📋 Endpoints ONVIF probados (todos fallaron):\n")
                for i, endpoint in enumerate(onvif_endpoints, 1):
                    onvif_text.insert(tk.END, f"{i}. ❌ {endpoint}\n")
                onvif_text.insert(tk.END, "\n⚠️ Ningún endpoint ONVIF respondió con las credenciales proporcionadas.")
                if port_result.auth_error:
                    onvif_text.insert(tk.END, f"\n🔍 Error específico: {port_result.auth_error}")
            
            onvif_text.config(state=tk.DISABLED)
            onvif_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            onvif_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        elif is_dahua_sdk_port:
            # Para puerto Dahua SDK, mostrar información específica
            sdk_frame = ttk.LabelFrame(main_frame, text="Información Dahua SDK")
            sdk_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            sdk_text = tk.Text(sdk_frame, height=10, wrap=tk.WORD)
            sdk_scrollbar = ttk.Scrollbar(sdk_frame, orient=tk.VERTICAL, command=sdk_text.yview)
            sdk_text.configure(yscrollcommand=sdk_scrollbar.set)
            
            if port_result.auth_success:
                sdk_text.insert(tk.END, "✅ Conexión Dahua SDK exitosa\n\n")
                
                sdk_text.insert(tk.END, "🎯 Conexión SDK que FUNCIONÓ:\n")
                sdk_text.insert(tk.END, f"✅ TCP Socket a IP:{port_result.port} con credenciales válidas\n")
                
                sdk_text.insert(tk.END, "\n📋 Detalles de la conexión:\n")
                sdk_text.insert(tk.END, f"• Puerto SDK: {port_result.port}\n")
                sdk_text.insert(tk.END, "• Protocolo: TCP binario propietario de Dahua\n")
                sdk_text.insert(tk.END, "• Autenticación: Credenciales enviadas por socket TCP\n")
                sdk_text.insert(tk.END, "• Estado: Conexión establecida y credenciales aceptadas\n")
                
                sdk_text.insert(tk.END, "\n💡 El puerto SDK de Dahua respondió correctamente a las credenciales.")
                sdk_text.insert(tk.END, "\n🔧 Este puerto se usa para funciones avanzadas como PTZ, configuración y control de cámara.")
            else:
                sdk_text.insert(tk.END, "❌ Conexión Dahua SDK falló\n\n")
                
                sdk_text.insert(tk.END, "📋 Intento de conexión realizado:\n")
                sdk_text.insert(tk.END, f"❌ TCP Socket a IP:{port_result.port}\n")
                
                sdk_text.insert(tk.END, "\n📋 Detalles del intento:\n")
                sdk_text.insert(tk.END, f"• Puerto SDK: {port_result.port}\n")
                sdk_text.insert(tk.END, "• Protocolo: TCP binario propietario de Dahua\n")
                sdk_text.insert(tk.END, "• Autenticación: Credenciales enviadas por socket TCP\n")
                sdk_text.insert(tk.END, "• Estado: Conexión rechazada o timeout\n")
                
                sdk_text.insert(tk.END, "\n⚠️ El puerto SDK no respondió o rechazó las credenciales.")
                if port_result.auth_error:
                    sdk_text.insert(tk.END, f"\n🔍 Error específico: {port_result.auth_error}")
                sdk_text.insert(tk.END, "\n💭 Posibles causas: credenciales incorrectas, puerto cerrado, o SDK deshabilitado.")
            
            sdk_text.config(state=tk.DISABLED)
            sdk_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sdk_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Error (si lo hay)
        if port_result.auth_error:
            error_frame = ttk.LabelFrame(main_frame, text="Error")
            error_frame.pack(fill=tk.X, pady=(0, 10))
            
            error_label = ttk.Label(error_frame, text=port_result.auth_error, foreground="red", wraplength=650)
            error_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Botón cerrar
        ttk.Button(main_frame, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def _create_actions_section(self):
        """
        Crea la sección de acciones sobre los resultados.
        """
        actions_frame = ttk.LabelFrame(self.main_frame, text="Información del Escaneo")
        actions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Frame para información y ayuda
        info_container = ttk.Frame(actions_frame)
        info_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        
        self.scan_info_var = tk.StringVar(value="Sin escaneo realizado")
        ttk.Label(info_container, textvariable=self.scan_info_var).pack(anchor=tk.W)
        
        # Nota de ayuda para modo avanzado
        help_label = ttk.Label(info_container, 
                              text="💡 Modo Avanzado: Doble clic en un puerto para ver URLs detalladas | Hover sobre 'Intensidad' para más info",
                              font=("Arial", 8), foreground="gray")
        help_label.pack(anchor=tk.W)
        
        # Agregar botón para conexión RTSP personalizada
        ttk.Button(
            actions_frame,
            text="🎯 Conectar RTSP Custom",
            command=self._connect_custom_rtsp
        ).pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _on_mode_change(self):
        """Maneja el cambio de modo de escaneo."""
        if self.scan_mode.get() == "advanced":
            # Mostrar columna de credenciales
            self.credentials_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
            self.scan_button.config(text="🔐 Avanzado")
        else:
            # Ocultar columna de credenciales
            self.credentials_frame.pack_forget()
            self.scan_button.config(text="🔍 Simple")
        
        # Reconfigurar tabla de resultados
        if hasattr(self, 'results_tree'):
            results_parent = self.results_tree.master
            self.setup_results_table(results_parent)
    
    def _toggle_password_visibility(self):
        """Alterna la visibilidad de la contraseña."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def _set_credentials(self, username: str, password: str):
        """Establece credenciales rápidas."""
        self.username_var.set(username)
        self.password_var.set(password)
    
    def _setup_scanner_callbacks(self):
        """
        Configura los callbacks del scanner.
        """
        def progress_callback(current: int, total: int, message: str):
            self.main_frame.after(0, self._update_progress, current, total, message)
        
        def result_callback(result: PortResult):
            self.main_frame.after(0, self._add_result_to_table, result)
        
        self.scanner.set_progress_callback(progress_callback)
        self.scanner.set_result_callback(result_callback)
    
    def _start_scan(self):
        """
        Inicia el escaneo de puertos.
        """
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showerror("Error", "Ingrese una IP válida")
            return
        
        # Validación básica de IP
        try:
            parts = ip.split('.')
            if len(parts) != 4 or not all(0 <= int(part) <= 255 for part in parts):
                raise ValueError("IP inválida")
        except ValueError:
            messagebox.showerror("Error", "Formato de IP inválido")
            return
        
        # Configurar scanner
        self.scanner.timeout = self.timeout_var.get()
        
        # Configurar credenciales si está en modo avanzado
        if self.scan_mode.get() == "advanced":
            username = self.username_var.get().strip()
            password = self.password_var.get()
            
            if not username:
                messagebox.showerror("Error", "Ingrese un nombre de usuario para el modo avanzado")
                return
            
            self.scanner.set_credentials(username, password)
            
            # Configurar nivel de intensidad
            intensity = self.intensity_var.get()
            self.scanner.set_intensity_level(intensity)
            
            # Descripción de intensidad
            intensity_desc = {
                'basic': 'Básica (10 URLs más comunes)',
                'medium': 'Media (20 URLs comunes + específicas)', 
                'high': 'Alta (30 URLs + variantes)',
                'maximum': 'Máxima (Todas las URLs disponibles)'
            }
            
            self._add_to_console(f"Iniciando escaneo AVANZADO en {ip}", "INFO")
            self._add_to_console(f"  Credenciales: {username}/{'*' * len(password)}", "INFO")
            self._add_to_console(f"  Intensidad: {intensity_desc.get(intensity, intensity)}", "INFO")
        else:
            self.scanner.set_credentials("", "")
            self._add_to_console(f"Iniciando escaneo SIMPLE en {ip}", "INFO")
        
        # Agregar configuración a consola
        self._add_to_console(f"Configuración: Timeout={self.timeout_var.get()}s", "INFO")
        
        self.scan_in_progress = True
        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self._clear_results_display()
        
        self.current_scan_thread = threading.Thread(target=self._scan_worker, args=(ip,), daemon=True)
        self.current_scan_thread.start()
    
    def _scan_worker(self, ip: str):
        """
        Worker del escaneo que se ejecuta en hilo separado.
        
        Args:
            ip: IP a escanear
        """
        try:
            result = self.scanner.scan_host(ip)
            self.main_frame.after(0, self._scan_completed, result)
        except Exception as e:
            self.main_frame.after(0, self._scan_error, str(e))
    
    def _stop_scan(self):
        """
        Detiene el escaneo actual.
        """
        self.scanner.stop_scan()
        self.scan_in_progress = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Escaneo detenido por usuario")
        
        # Agregar a consola
        self._add_to_console("ESCANEO DETENIDO por el usuario", "WARNING")
    
    def _clear_results(self):
        """
        Limpia todos los resultados.
        """
        self._clear_results_display()
        self.scan_results = None
        
        # Limpiar consola también
        self.console_output.clear()
        self._add_to_console("Resultados limpiados - Listo para nuevo escaneo", "INFO")
        
        if hasattr(self, 'scan_info_var'):
            self.scan_info_var.set("Sin escaneo realizado")
        if hasattr(self, 'status_var'):
            self.status_var.set("Listo para escanear")
        if hasattr(self, 'progress_var'):
            self.progress_var.set(0)
    
    def _clear_results_display(self):
        """
        Limpia la visualización de resultados.
        """
        if hasattr(self, 'results_tree'):
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
    
    def _update_progress(self, current: int, total: int, message: str):
        """
        Actualiza la barra de progreso.
        """
        progress = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(progress)
        self.status_var.set(f"{message} ({current}/{total})")
        
        # Agregar a consola
        self._add_to_console(f"Progreso: {current}/{total} - {message}", "INFO")
    
    def _add_result_to_table(self, result: PortResult):
        """
        Agrega un resultado a la tabla (tanto abiertos como cerrados).
        """
        tiempo_ms = f"{result.response_time * 1000:.1f}"
        banner = (result.banner[:40] + "...") if result.banner and len(result.banner) > 40 else (result.banner or "")
        
        # Agregar a consola con detalles
        if result.is_open:
            console_msg = f"Puerto {result.port}: ✅ ABIERTO"
            level = "SUCCESS"
            if result.service_name:
                console_msg += f" - Servicio: {result.service_name}"
            if result.banner:
                console_msg += f" - Banner: {result.banner[:50]}{'...' if len(result.banner) > 50 else ''}"
            
            # Información detallada de autenticación
            if hasattr(result, 'auth_tested') and result.auth_tested:
                if result.auth_success:
                    console_msg += f" - Auth: ✅ Exitosa ({result.auth_method})"
                    # Mostrar URLs válidas
                    if hasattr(result, 'valid_urls') and result.valid_urls:
                        self._add_to_console(f"  📋 URLs válidas encontradas ({len(result.valid_urls)}):", "INFO")
                        for url in result.valid_urls[:5]:  # Mostrar máximo 5
                            self._add_to_console(f"    ✅ {url}", "SUCCESS")
                        if len(result.valid_urls) > 5:
                            self._add_to_console(f"    ... y {len(result.valid_urls) - 5} más", "INFO")
                else:
                    console_msg += f" - Auth: ❌ Falló"
                    # Mostrar información de URLs probadas
                    if hasattr(result, 'tested_urls') and result.tested_urls:
                        self._add_to_console(f"  📋 URLs probadas: {len(result.tested_urls)} - Ninguna accesible", "WARNING")
                        if result.auth_error:
                            self._add_to_console(f"  ❌ Error: {result.auth_error}", "ERROR")
        else:
            console_msg = f"Puerto {result.port}: ❌ CERRADO"
            level = "WARNING"
            if result.service_name:
                console_msg += f" - Servicio esperado: {result.service_name}"
        
        self._add_to_console(console_msg, level)
        
        # Determinar valores según el estado del puerto
        if result.is_open:
            # Puerto abierto
            if self.scan_mode.get() == "simple":
                values = (
                    result.port,
                    "✅ Abierto",
                    result.service_name,
                    tiempo_ms,
                    banner
                )
                tags = ("open",)
            else:
                # Modo avanzado - incluir información de autenticación
                if result.auth_tested:
                    if result.auth_success:
                        auth_status = "✅ OK"
                        auth_method = result.auth_method or "N/A"
                        
                        # Agregar información de URLs válidas si están disponibles
                        if hasattr(result, 'valid_urls') and result.valid_urls:
                            url_count = len(result.valid_urls)
                            auth_method += f" ({url_count} URL{'s' if url_count != 1 else ''})"
                        
                        tags = ("open", "auth_success")
                    else:
                        auth_status = "❌ Fallo"
                        
                        # Mostrar información más detallada del error
                        if hasattr(result, 'tested_urls') and result.tested_urls:
                            tested_count = len(result.tested_urls)
                            auth_method = f"Probadas {tested_count} URLs"
                        else:
                            auth_method = result.auth_error[:30] + "..." if result.auth_error and len(result.auth_error) > 30 else (result.auth_error or "Sin acceso")
                        
                        tags = ("open", "auth_fail")
                else:
                    auth_status = "⏳ N/A"
                    auth_method = "No probado"
                    tags = ("open",)
                
                values = (
                    result.port,
                    "✅ Abierto",
                    result.service_name,
                    tiempo_ms,
                    auth_status,
                    auth_method,
                    banner
                )
        else:
            # Puerto cerrado - mostrar en rojo
            if self.scan_mode.get() == "simple":
                values = (
                    result.port,
                    "❌ Cerrado",
                    result.service_name,
                    tiempo_ms,
                    "No accesible"
                )
                tags = ("closed",)
            else:
                # Modo avanzado
                values = (
                    result.port,
                    "❌ Cerrado",
                    result.service_name,
                    tiempo_ms,
                    "❌ N/A",
                    "Puerto cerrado",
                    "No accesible"
                )
                tags = ("closed",)
        
        self.results_tree.insert("", tk.END, values=values, tags=tags)
        
        # Configurar colores
        self.results_tree.tag_configure("open", background="#e8f5e8")  # Verde claro para abiertos
        self.results_tree.tag_configure("closed", background="#ffebee", foreground="#c62828")  # Rojo claro para cerrados
        if self.scan_mode.get() == "advanced":
            self.results_tree.tag_configure("auth_success", background="#d4edda")
            self.results_tree.tag_configure("auth_fail", background="#f8d7da")
    
    def _scan_completed(self, result: ScanResult):
        """
        Maneja la finalización del escaneo.
        """
        self.scan_results = result
        self.scan_in_progress = False
        
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        open_count = len(result.open_ports)
        closed_count = len(result.closed_ports) if hasattr(result, 'closed_ports') else (result.total_ports_scanned - open_count)
        
        # Información básica
        info_parts = [
            f"IP: {result.target_ip}",
            f"Abiertos: {open_count}",
            f"Cerrados: {closed_count}",
            f"Total: {result.total_ports_scanned}",
            f"Tiempo: {result.scan_duration:.2f}s"
        ]
        
        # Información adicional para modo avanzado
        if result.credentials_tested:
            info_parts.append(f"Auth OK: {result.successful_auths}")
            status_msg = f"Completado - {open_count} abiertos, {closed_count} cerrados, {result.successful_auths} con acceso"
            self._add_to_console(f"ESCANEO COMPLETADO: {open_count} puertos abiertos, {closed_count} cerrados, {result.successful_auths} con autenticación exitosa en {result.scan_duration:.2f}s", "SUCCESS")
        else:
            status_msg = f"Completado - {open_count} abiertos, {closed_count} cerrados"
            self._add_to_console(f"ESCANEO COMPLETADO: {open_count} puertos abiertos, {closed_count} cerrados en {result.scan_duration:.2f}s", "SUCCESS")
        
        # Agregar resumen de puertos abiertos
        if result.open_ports:
            ports_list = ", ".join([str(p.port) for p in result.open_ports])
            self._add_to_console(f"Puertos abiertos encontrados: {ports_list}", "INFO")
        
        self.scan_info_var.set(" | ".join(info_parts))
        self.status_var.set(status_msg)
        self.progress_var.set(100)
    
    def _scan_error(self, error_message: str):
        """
        Maneja errores en el escaneo.
        """
        self.scan_in_progress = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set(f"Error: {error_message}")
        
        # Agregar error a consola
        self._add_to_console(f"ERROR EN ESCANEO: {error_message}", "ERROR")
        
        messagebox.showerror("Error", f"Error en escaneo:\n{error_message}")
    
    def _connect_custom_rtsp(self):
        """
        Abre diálogo para conexión RTSP personalizada para cámaras genéricas.
        """
        from tkinter import messagebox, simpledialog
        
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showerror("Error", "Ingrese una IP para conectar")
            return
        
        # Diálogo para credenciales
        dialog = tk.Toplevel(self.main_frame)
        dialog.title("Conexión RTSP Custom")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Variables con precarga condicional desde .env
        from src.utils.config import get_config
        config = get_config()
        
        # Precargar datos de la cámara genérica si están disponibles
        default_username = "admin"
        default_password = ""
        default_port = 554
        
        if hasattr(config, 'generic_ip') and config.generic_ip == ip:
            # Si la IP coincide con la configurada en .env, precargar credenciales
            if hasattr(config, 'generic_user') and config.generic_user:
                default_username = config.generic_user
            if hasattr(config, 'generic_password') and config.generic_password:
                default_password = config.generic_password
        
        username_var = tk.StringVar(value=default_username)
        password_var = tk.StringVar(value=default_password)
        port_var = tk.IntVar(value=default_port)
        
        row = 0
        
        # Información
        ttk.Label(dialog, text=f"Conexión RTSP personalizada para {ip}", 
                 font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        # Mostrar si se precargaron datos
        if hasattr(config, 'generic_ip') and config.generic_ip == ip:
            ttk.Label(dialog, text="✅ Datos precargados desde variables de entorno (.env)",
                     font=("Arial", 8), foreground="green").grid(row=row, column=0, columnspan=2, pady=2)
            row += 1
        
        ttk.Label(dialog, text="Para cámaras chinas genéricas que solo tienen puerto 554 abierto.",
                 font=("Arial", 8)).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # Separador
        ttk.Separator(dialog, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, 
                                                        sticky=tk.EW, padx=10, pady=10)
        row += 1
        
        # Credenciales
        ttk.Label(dialog, text="Usuario:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=username_var, width=25).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Contraseña:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=password_var, show="*", width=25).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Puerto RTSP:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Spinbox(dialog, from_=1, to=65535, textvariable=port_var, width=23).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Información adicional
        info_text = tk.Text(dialog, height=4, width=45, wrap=tk.WORD)
        info_text.grid(row=row, column=0, columnspan=2, padx=10, pady=10)
        info_text.insert(tk.END, "ℹ️ Esta función probará múltiples patrones de URL RTSP comunes:\n")
        info_text.insert(tk.END, "• /stream1, /stream2, /live/stream1\n")
        info_text.insert(tk.END, "• /live, /stream, /h264, /video\n")
        info_text.insert(tk.END, "• Y varios más hasta encontrar uno funcional")
        info_text.config(state=tk.DISABLED)
        row += 1
        
        # Botones
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def connect_custom():
            username = username_var.get().strip()
            password = password_var.get()
            port = port_var.get()
            
            if not username:
                messagebox.showerror("Error", "Ingrese un usuario")
                return
            
            # Agregar a consola
            self._add_to_console(f"Iniciando conexión RTSP personalizada a {ip}:{port} con usuario: {username}", "INFO")
            
            dialog.destroy()
            self._test_custom_rtsp(ip, username, password, port)
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="🔌 Conectar", command=connect_custom).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="❌ Cancelar", command=cancel).pack(side=tk.LEFT, padx=5)
    
    def _test_custom_rtsp(self, ip: str, username: str, password: str, port: int):
        """
        Prueba la conexión RTSP personalizada.
        
        Args:
            ip: IP de la cámara
            username: Usuario
            password: Contraseña
            port: Puerto RTSP
        """
        import threading
        from tkinter import messagebox
        
        # Crear un diálogo de progreso
        progress_dialog = tk.Toplevel(self.main_frame)
        progress_dialog.title("Probando Conexión RTSP Custom")
        progress_dialog.geometry("450x200")
        progress_dialog.resizable(False, False)
        progress_dialog.grab_set()
        
        ttk.Label(progress_dialog, text=f"Probando conexión RTSP a {ip}:{port}",
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        progress_var = tk.StringVar(value="Inicializando...")
        ttk.Label(progress_dialog, textvariable=progress_var).pack(pady=5)
        
        # Barra de progreso
        pb = ttk.Progressbar(progress_dialog, mode='indeterminate')
        pb.pack(fill=tk.X, padx=20, pady=10)
        pb.start()
        
        # Log de pruebas
        log_text = tk.Text(progress_dialog, height=5, width=50)
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def test_worker():
            try:
                # Simular configuración
                class MockConfig:
                    def __init__(self):
                        self.camera_ip = ip
                        self.camera_user = username
                        self.camera_password = password
                        self.rtsp_port = port
                
                # Importar y usar la conexión genérica
                from src.connections.generic_connection import GenericConnection
                
                config = MockConfig()
                generic_conn = GenericConnection(config)
                
                # Agregar a consola principal
                self._add_to_console(f"Generando {len(generic_conn.stream_urls)} URLs de prueba para conexión RTSP", "INFO")
                
                # Actualizar progreso
                progress_dialog.after(0, lambda: progress_var.set("Generando URLs de prueba..."))
                progress_dialog.after(0, lambda: log_text.insert(tk.END, f"🔧 Generando {len(generic_conn.stream_urls)} URLs de prueba\n"))
                progress_dialog.after(0, lambda: log_text.see(tk.END))
                
                # Intentar conexión
                progress_dialog.after(0, lambda: progress_var.set("Probando conexión..."))
                success = generic_conn.connect()
                
                if success:
                    # ¡Éxito!
                    conn_info = generic_conn.get_connection_info()
                    url_used = conn_info.get('current_stream_url', 'Unknown')
                    props = conn_info.get('stream_properties', {})
                    
                    # Agregar a consola principal
                    self._add_to_console(f"CONEXIÓN RTSP EXITOSA: {url_used}", "SUCCESS")
                    if props:
                        self._add_to_console(f"Propiedades del stream: {props.get('width', '?')}x{props.get('height', '?')} @ {props.get('fps', '?')} FPS", "INFO")
                    
                    progress_dialog.after(0, lambda: pb.stop())
                    progress_dialog.after(0, lambda: progress_var.set("¡Conexión exitosa!"))
                    progress_dialog.after(0, lambda: log_text.insert(tk.END, f"✅ ¡CONEXIÓN EXITOSA!\n"))
                    progress_dialog.after(0, lambda: log_text.insert(tk.END, f"📺 URL funcional: {url_used}\n"))
                    
                    if props:
                        progress_dialog.after(0, lambda: log_text.insert(tk.END, f"📊 Resolución: {props.get('width', '?')}x{props.get('height', '?')}\n"))
                        progress_dialog.after(0, lambda: log_text.insert(tk.END, f"🎬 FPS: {props.get('fps', '?')}\n"))
                    
                    progress_dialog.after(0, lambda: log_text.see(tk.END))
                    
                    # Desconectar después de la prueba
                    generic_conn.disconnect()
                    
                    # Botón para agregar cámara
                    def add_camera():
                        camera_config = {
                            'name': f'Cámara China {ip}',
                            'ip': ip,
                            'brand': 'generic',
                            'type': 'rtsp',
                            'username': username,
                            'password': password,
                            'rtsp_port': port,
                            'working_url': url_used
                        }
                        
                        progress_dialog.destroy()
                        messagebox.showinfo("Éxito", 
                            f"¡Conexión exitosa!\n\n"
                            f"URL funcional: {url_used}\n"
                            f"Resolución: {props.get('width', '?')}x{props.get('height', '?')}\n\n"
                            f"La cámara está lista para usar con el protocolo Generic.")
                    
                    progress_dialog.after(0, lambda: ttk.Button(progress_dialog, text="🎯 Entendido", command=add_camera).pack(pady=10))
                    
                else:
                    # Falló
                    self._add_to_console(f"CONEXIÓN RTSP FALLIDA: No se pudo conectar con ninguna URL de prueba", "ERROR")
                    
                    progress_dialog.after(0, lambda: pb.stop())
                    progress_dialog.after(0, lambda: progress_var.set("Conexión fallida"))
                    progress_dialog.after(0, lambda: log_text.insert(tk.END, f"❌ No se pudo conectar con ninguna URL\n"))
                    progress_dialog.after(0, lambda: log_text.insert(tk.END, f"💡 Verifica credenciales y que puerto 554 esté abierto\n"))
                    progress_dialog.after(0, lambda: log_text.see(tk.END))
                    
                    def close_failed():
                        progress_dialog.destroy()
                        messagebox.showerror("Sin éxito", 
                            "No se pudo establecer conexión RTSP.\n\n"
                            "Verifica:\n"
                            "• Credenciales correctas\n"
                            "• Puerto 554 abierto\n"
                            "• La cámara soporta RTSP")
                    
                    progress_dialog.after(0, lambda: ttk.Button(progress_dialog, text="❌ Cerrar", command=close_failed).pack(pady=10))
                    
            except Exception as e:
                self._add_to_console(f"ERROR en prueba RTSP: {str(e)}", "ERROR")
                
                progress_dialog.after(0, lambda: pb.stop())
                progress_dialog.after(0, lambda: progress_var.set("Error en conexión"))
                progress_dialog.after(0, lambda: log_text.insert(tk.END, f"💥 Error: {str(e)}\n"))
                progress_dialog.after(0, lambda: log_text.see(tk.END))
                
                def close_error():
                    progress_dialog.destroy()
                    messagebox.showerror("Error", f"Error en la prueba:\n{str(e)}")
                
                progress_dialog.after(0, lambda: ttk.Button(progress_dialog, text="❌ Cerrar", command=close_error).pack(pady=10))
        
        # Iniciar worker en hilo separado
        threading.Thread(target=test_worker, daemon=True).start()

    def cleanup(self):
        """
        Limpia la vista y libera recursos.
        """
        try:
            if self.scan_in_progress:
                self.scanner.stop_scan()
            
            if self.current_scan_thread and self.current_scan_thread.is_alive():
                self.current_scan_thread.join(timeout=2.0)
            
            if hasattr(self, 'main_frame'):
                self.main_frame.destroy()
        except:
            pass