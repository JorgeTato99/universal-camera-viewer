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
        self.scanner = PortScanner()
        self.current_scan_thread: Optional[threading.Thread] = None
        self.scan_results: Optional[ScanResult] = None
        
        # Variables de UI
        self.scan_in_progress = False
        
        # Crear contenido de la vista
        self._create_view_content()
        
        # Configurar callbacks del scanner
        self._setup_scanner_callbacks()
    
    def _create_view_content(self):
        """
        Crea el contenido principal de la vista.
        """
        # Frame principal de la vista
        self.main_frame = ttk.Frame(self.parent_container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear secciones
        self._create_mode_section()
        self._create_input_section()
        self._create_credentials_section()
        self._create_progress_section()
        self._create_results_section()
        self._create_actions_section()
    
    def _create_mode_section(self):
        """Crea la sección de selección de modo."""
        mode_frame = ttk.LabelFrame(self.main_frame, text="Modo de Escaneo")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Variable para el modo
        self.scan_mode = tk.StringVar(value="simple")
        
        # Radio buttons para seleccionar modo
        ttk.Radiobutton(
            mode_frame, 
            text="🔍 Escaneo Simple - Solo detectar puertos abiertos",
            variable=self.scan_mode,
            value="simple",
            command=self._on_mode_change
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="🔐 Escaneo Avanzado - Detectar puertos + probar credenciales",
            variable=self.scan_mode,
            value="advanced",
            command=self._on_mode_change
        ).pack(anchor=tk.W, padx=10, pady=5)
    
    def _create_input_section(self):
        """
        Crea la sección de entrada de datos.
        """
        # Frame de entrada
        input_frame = ttk.LabelFrame(self.main_frame, text="Configuración Básica")
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # IP Frame
        ip_frame = ttk.Frame(input_frame)
        ip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ip_frame, text="IP Objetivo:").pack(side=tk.LEFT)
        
        self.ip_var = tk.StringVar(value="192.168.1.178")
        self.ip_entry = ttk.Entry(ip_frame, textvariable=self.ip_var, width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        # Botones IP rápida
        ttk.Button(ip_frame, text="Dahua (172)", command=lambda: self.ip_var.set("192.168.1.172")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ip_frame, text="TP-Link (77)", command=lambda: self.ip_var.set("192.168.1.77")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ip_frame, text="Steren (178)", command=lambda: self.ip_var.set("192.168.1.178")).pack(side=tk.LEFT, padx=2)
        
        # Timeout
        timeout_frame = ttk.Frame(input_frame)
        timeout_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="Timeout (s):").pack(side=tk.LEFT)
        self.timeout_var = tk.DoubleVar(value=3.0)
        timeout_spin = ttk.Spinbox(timeout_frame, from_=1.0, to=10.0, increment=0.5, textvariable=self.timeout_var, width=8)
        timeout_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        # Botones de control
        control_frame = ttk.Frame(input_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.scan_button = ttk.Button(control_frame, text="🔍 Iniciar Escaneo", command=self._start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏹ Detener", command=self._stop_scan, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="🗑 Limpiar", command=self._clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)
    
    def _create_credentials_section(self):
        """Crea la sección de credenciales (solo visible en modo avanzado)."""
        self.credentials_frame = ttk.LabelFrame(self.main_frame, text="Credenciales de Acceso")
        # Inicialmente oculto
        
        # Frame para campos de entrada
        fields_frame = ttk.Frame(self.credentials_frame)
        fields_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Usuario
        user_frame = ttk.Frame(fields_frame)
        user_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(user_frame, text="Usuario:", width=12).pack(side=tk.LEFT)
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(user_frame, textvariable=self.username_var, width=20)
        self.username_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Contraseña
        pass_frame = ttk.Frame(fields_frame)
        pass_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(pass_frame, text="Contraseña:", width=12).pack(side=tk.LEFT)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(pass_frame, textvariable=self.password_var, width=20, show="*")
        self.password_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Checkbox para mostrar/ocultar contraseña
        self.show_password_var = tk.BooleanVar()
        show_pass_check = ttk.Checkbutton(
            pass_frame, 
            text="Mostrar", 
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_pass_check.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de credenciales rápidas
        quick_creds_frame = ttk.Frame(self.credentials_frame)
        quick_creds_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(quick_creds_frame, text="Credenciales comunes:").pack(side=tk.LEFT)
        
        ttk.Button(
            quick_creds_frame, 
            text="admin/admin", 
            command=lambda: self._set_credentials("admin", "admin")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            quick_creds_frame, 
            text="admin/123456", 
            command=lambda: self._set_credentials("admin", "123456")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            quick_creds_frame, 
            text="admin/password", 
            command=lambda: self._set_credentials("admin", "password")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            quick_creds_frame, 
            text="Steren", 
            command=lambda: self._set_credentials("admin", "-wFNC2tR_dTVqxyGsTE.p2Zihy.ZgH")
        ).pack(side=tk.LEFT, padx=5)
        
        # Advertencia de seguridad
        warning_frame = ttk.Frame(self.credentials_frame)
        warning_frame.pack(fill=tk.X, padx=10, pady=5)
        
        warning_label = ttk.Label(
            warning_frame,
            text="⚠️ Las credenciales se probarán en los puertos detectados. Use solo en redes propias.",
            foreground="orange"
        )
        warning_label.pack(side=tk.LEFT)
    
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
        
        # Tabla de resultados - columnas variables según el modo
        self.setup_results_table(results_frame)
    
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
                self.results_tree.column(col, width=120)
            elif col == "Tiempo (ms)":
                self.results_tree.column(col, width=100)
            else:
                self.results_tree.column(col, width=120)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_actions_section(self):
        """
        Crea la sección de acciones sobre los resultados.
        """
        actions_frame = ttk.LabelFrame(self.main_frame, text="Información del Escaneo")
        actions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.scan_info_var = tk.StringVar(value="Sin escaneo realizado")
        ttk.Label(actions_frame, textvariable=self.scan_info_var).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Agregar botón para conexión RTSP personalizada
        ttk.Button(
            actions_frame,
            text="🎯 Conectar RTSP Custom",
            command=self._connect_custom_rtsp
        ).pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _on_mode_change(self):
        """Maneja el cambio de modo de escaneo."""
        if self.scan_mode.get() == "advanced":
            # Mostrar sección de credenciales
            self.credentials_frame.pack(fill=tk.X, padx=10, pady=5, after=self.main_frame.winfo_children()[1])
            self.scan_button.config(text="🔐 Escaneo Avanzado")
        else:
            # Ocultar sección de credenciales
            self.credentials_frame.pack_forget()
            self.scan_button.config(text="🔍 Escaneo Simple")
        
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
        else:
            self.scanner.set_credentials("", "")
        
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
    
    def _clear_results(self):
        """
        Limpia todos los resultados.
        """
        self._clear_results_display()
        self.scan_results = None
        self.scan_info_var.set("Sin escaneo realizado")
        self.status_var.set("Listo para escanear")
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
    
    def _add_result_to_table(self, result: PortResult):
        """
        Agrega un resultado a la tabla.
        """
        if not result.is_open:
            return
        
        tiempo_ms = f"{result.response_time * 1000:.1f}"
        banner = (result.banner[:40] + "...") if result.banner and len(result.banner) > 40 else (result.banner or "")
        
        # Determinar valores según el modo
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
                    tags = ("open", "auth_success")
                else:
                    auth_status = "❌ Fallo"
                    auth_method = result.auth_error[:20] + "..." if result.auth_error and len(result.auth_error) > 20 else (result.auth_error or "Sin acceso")
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
        
        self.results_tree.insert("", tk.END, values=values, tags=tags)
        
        # Configurar colores
        self.results_tree.tag_configure("open", background="#e8f5e8")
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
        
        # Información básica
        info_parts = [
            f"IP: {result.target_ip}",
            f"Abiertos: {open_count}/{result.total_ports_scanned}",
            f"Tiempo: {result.scan_duration:.2f}s"
        ]
        
        # Información adicional para modo avanzado
        if result.credentials_tested:
            info_parts.append(f"Auth OK: {result.successful_auths}")
            status_msg = f"Completado - {open_count} puertos, {result.successful_auths} con acceso"
        else:
            status_msg = f"Completado - {open_count} puertos abiertos"
        
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
                            'type': 'generic',
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