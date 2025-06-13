"""
Widget selector de IP con botones dinámicos basados en configuración.
Permite seleccionar IPs de cámaras configuradas en el .env con UX mejorada.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List
import re

# cspell:disable
class IPSelectorWidget:
    """
    Widget para seleccionar direcciones IP de cámaras con UX mejorada.
    
    Incluye validación en tiempo real, historial y botones dinámicos.
    """
    
    def __init__(self, parent_frame: tk.Widget, ip_var: tk.StringVar):
        """
        Inicializa el widget selector de IP.
        
        Args:
            parent_frame: Frame padre donde se colocará el widget
            ip_var: Variable tkinter para almacenar la IP seleccionada
        """
        self.parent_frame = parent_frame
        self.ip_var = ip_var
        self.on_ip_change_callback: Optional[Callable] = None
        
        # Estado de validación
        self.is_valid = tk.BooleanVar(value=True)
        self.validation_message = tk.StringVar(value="")
        
        # Historial de IPs
        self.ip_history: List[str] = []
        self.max_history = 10
        
        # Estado de habilitación
        self.enabled = True
        
        self._create_widget()
        self._setup_validation()
    
    def _create_widget(self):
        """Crea el widget con entrada de IP y botones dinámicos mejorados."""
        # Contenedor principal
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.X)
        
        # Fila 1: Label y entrada con validación
        input_row = ttk.Frame(main_container)
        input_row.pack(fill=tk.X, pady=(0, 2))
        
        # Label con indicador de estado
        label_frame = ttk.Frame(input_row)
        label_frame.pack(side=tk.LEFT)
        
        ttk.Label(label_frame, text="IP:").pack(side=tk.LEFT)
        
        # Indicador de validación
        self.validation_indicator = ttk.Label(
            label_frame, 
            text="✅", 
            font=("Arial", 8),
            foreground="#2e7d32"
        )
        self.validation_indicator.pack(side=tk.LEFT, padx=(3, 5))
        
        # Entrada de IP con validación visual
        self.ip_entry = ttk.Entry(
            input_row, 
            textvariable=self.ip_var, 
            width=15,
            font=("Consolas", 9)
        )
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 8))
        
        # Botón de historial
        self.history_btn = ttk.Button(
            input_row,
            text="📋",
            width=3,
            command=self._show_history_menu
        )
        self.history_btn.pack(side=tk.LEFT, padx=2)
        
        # Fila 2: Botones dinámicos
        buttons_row = ttk.Frame(main_container)
        buttons_row.pack(fill=tk.X, pady=(2, 0))
        
        # Crear botones dinámicos
        self._create_dynamic_ip_buttons(buttons_row)
        
        # Fila 3: Mensaje de validación (inicialmente oculto)
        self.validation_frame = ttk.Frame(main_container)
        # No se empaqueta inicialmente
        
        self.validation_label = ttk.Label(
            self.validation_frame,
            textvariable=self.validation_message,
            font=("Arial", 7),
            foreground="#d32f2f"
        )
        self.validation_label.pack()
        
        # Configurar tooltips
        self._setup_tooltips()
    
    def _setup_validation(self):
        """Configura la validación en tiempo real."""
        # Validar cuando cambie el valor
        self.ip_var.trace_add("write", self._validate_ip_realtime)
        
        # Validar al perder el foco
        self.ip_entry.bind("<FocusOut>", self._on_focus_out)
        
        # Autocompletado con Tab
        self.ip_entry.bind("<Tab>", self._try_autocomplete)
        
        # Validación inicial
        self._validate_ip_realtime()
    
    def _validate_ip_realtime(self, *args):
        """Valida la IP en tiempo real y actualiza indicadores visuales."""
        ip = self.ip_var.get().strip()
        
        if not ip:
            # IP vacía - estado neutral
            self._set_validation_state(True, "")
            self.ip_entry.config(style="")
            return
        
        # Validar formato de IP
        is_valid, message = self._validate_ip_format(ip)
        
        if is_valid:
            # IP válida
            self._set_validation_state(True, "IP válida")
            self.ip_entry.config(style="")
            
            # Agregar al historial si es nueva
            self._add_to_history(ip)
        else:
            # IP inválida
            self._set_validation_state(False, message)
            # Cambiar estilo visual para indicar error
            self._configure_error_style()
    
    def _validate_ip_format(self, ip: str) -> tuple[bool, str]:
        """
        Valida el formato de una dirección IP.
        
        Args:
            ip: Dirección IP a validar
            
        Returns:
            Tupla (es_válida, mensaje_error)
        """
        # Patrón regex para IP
        ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ip_pattern, ip)
        
        if not match:
            return False, "Formato de IP inválido (ej: 192.168.1.1)"
        
        # Validar rangos de octetos
        octets = [int(x) for x in match.groups()]
        
        for i, octet in enumerate(octets):
            if not (0 <= octet <= 255):
                return False, f"Octeto {i+1} fuera de rango (0-255)"
        
        # Validaciones adicionales
        if octets[0] == 0:
            return False, "La IP no puede comenzar con 0"
        
        if octets == [127, 0, 0, 1]:
            return True, "Localhost detectado"
        
        if octets[0] in [10] or (octets[0] == 172 and 16 <= octets[1] <= 31) or (octets[0] == 192 and octets[1] == 168):
            return True, "IP privada válida"
        
        return True, "IP pública válida"
    
    def _set_validation_state(self, is_valid: bool, message: str):
        """Actualiza el estado visual de validación."""
        self.is_valid.set(is_valid)
        
        if is_valid:
            self.validation_indicator.config(text="✅", foreground="#2e7d32")
            self.validation_frame.pack_forget()
        else:
            self.validation_indicator.config(text="❌", foreground="#d32f2f")
            self.validation_message.set(message)
            self.validation_frame.pack(fill=tk.X, pady=(2, 0))
    
    def _configure_error_style(self):
        """Configura el estilo visual para errores."""
        # Crear estilo personalizado si no existe
        style = ttk.Style()
        style.configure("Error.TEntry", fieldbackground="#ffebee")
        self.ip_entry.config(style="Error.TEntry")
    
    def _add_to_history(self, ip: str):
        """Agrega una IP al historial."""
        if ip and ip not in self.ip_history:
            self.ip_history.insert(0, ip)
            # Mantener solo las últimas N IPs
            if len(self.ip_history) > self.max_history:
                self.ip_history = self.ip_history[:self.max_history]
    
    def _show_history_menu(self):
        """Muestra el menú de historial de IPs."""
        if not self.ip_history:
            # Mostrar mensaje si no hay historial
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg="#ffffcc")
            
            x = self.history_btn.winfo_rootx()
            y = self.history_btn.winfo_rooty() + self.history_btn.winfo_height()
            tooltip.geometry(f"+{x}+{y}")
            
            ttk.Label(
                tooltip, 
                text="No hay historial de IPs",
                background="#ffffcc",
                font=("Arial", 8)
            ).pack(padx=5, pady=3)
            
            tooltip.after(2000, tooltip.destroy)
            return
        
        # Crear menú contextual
        history_menu = tk.Menu(self.parent_frame, tearoff=0)
        
        # Agregar IPs del historial
        for ip in self.ip_history:
            history_menu.add_command(
                label=f"📍 {ip}",
                command=lambda selected_ip=ip: self._select_ip_from_history(selected_ip)
            )
        
        history_menu.add_separator()
        history_menu.add_command(
            label="🗑️ Limpiar historial",
            command=self._clear_history
        )
        
        # Mostrar menú
        try:
            x = self.history_btn.winfo_rootx()
            y = self.history_btn.winfo_rooty() + self.history_btn.winfo_height()
            history_menu.tk_popup(x, y)
        finally:
            history_menu.grab_release()
    
    def _select_ip_from_history(self, ip: str):
        """Selecciona una IP del historial."""
        self.ip_var.set(ip)
    
    def _clear_history(self):
        """Limpia el historial de IPs."""
        self.ip_history.clear()
    
    def _try_autocomplete(self, event):
        """Intenta autocompletar la IP basándose en patrones comunes."""
        current_ip = self.ip_var.get().strip()
        
        # Patrones de autocompletado comunes
        autocomplete_patterns = {
            "192.168.1.": ["192.168.1.1", "192.168.1.100", "192.168.1.254"],
            "192.168.0.": ["192.168.0.1", "192.168.0.100", "192.168.0.254"],
            "10.0.0.": ["10.0.0.1", "10.0.0.100", "10.0.0.254"],
            "172.16.": ["172.16.0.1", "172.16.1.1"]
        }
        
        # Buscar patrón coincidente
        for pattern, suggestions in autocomplete_patterns.items():
            if current_ip.startswith(pattern) and current_ip != pattern:
                # Encontrar la primera sugerencia que coincida
                for suggestion in suggestions:
                    if suggestion.startswith(current_ip):
                        self.ip_var.set(suggestion)
                        # Seleccionar la parte autocompletada
                        self.ip_entry.selection_range(len(current_ip), len(suggestion))
                        break
                break
        
        return "break"  # Prevenir el comportamiento normal del Tab
    
    def _on_focus_out(self, event):
        """Maneja el evento de perder el foco."""
        # Validación final al perder el foco
        self._validate_ip_realtime()
    
    def _create_dynamic_ip_buttons(self, parent_frame: tk.Widget):
        """
        Crea botones IP dinámicos basados en las variables de entorno configuradas.
        """
        try:
            from src.utils.config import ConfigurationManager
            config = ConfigurationManager()
            
            # Definir marcas y sus configuraciones
            brands_config = [
                ("DAHUA", "Dahua", getattr(config, 'camera_ip', None), "#1976d2"),
                ("TPLINK", "TP-Link", getattr(config, 'tplink_ip', None), "#ff9800"),
                ("STEREN", "Steren", getattr(config, 'steren_ip', None), "#4caf50"),
                ("GENERIC", "Generic", getattr(config, 'generic_ip', None), "#9c27b0")
            ]
            
            # Crear botones solo para marcas configuradas
            for brand_key, brand_name, ip_address, color in brands_config:
                if ip_address:  # Solo crear botón si la IP está configurada
                    # Extraer últimos dígitos de la IP para el botón
                    ip_suffix = ip_address.split('.')[-1]
                    button_text = f"{brand_name} ({ip_suffix})"
                    
                    btn = ttk.Button(
                        parent_frame, 
                        text=button_text, 
                        command=lambda ip=ip_address: self._set_ip_with_animation(ip),
                        width=12
                    )
                    btn.pack(side=tk.LEFT, padx=2)
                    
                    # Agregar tooltip con IP completa
                    self._add_tooltip(btn, f"IP completa: {ip_address}\nClic para seleccionar")
                    
        except Exception as e:
            # Si hay error cargando configuración, crear botones por defecto
            print(f"Error cargando configuración dinámica: {e}")
            self._create_default_buttons(parent_frame)
    
    def _create_default_buttons(self, parent_frame: tk.Widget):
        """Crea botones por defecto si falla la carga de configuración."""
        default_ips = [
            ("Dahua (172)", "192.168.1.172"),
            ("TP-Link (77)", "192.168.1.77"),
            ("Steren (178)", "192.168.1.178")
        ]
        
        for button_text, ip in default_ips:
            btn = ttk.Button(
                parent_frame, 
                text=button_text, 
                command=lambda ip_addr=ip: self._set_ip_with_animation(ip_addr),
                width=12
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            self._add_tooltip(btn, f"IP: {ip}\nClic para seleccionar")
    
    def _set_ip_with_animation(self, ip: str):
        """
        Establece la IP con una pequeña animación visual.
        
        Args:
            ip: Dirección IP a establecer
        """
        # Limpiar entrada actual
        self.ip_var.set("")
        
        # Simular escritura gradual
        self._animate_ip_input(ip, 0)
    
    def _animate_ip_input(self, target_ip: str, current_pos: int):
        """Anima la entrada de IP carácter por carácter."""
        if current_pos <= len(target_ip):
            self.ip_var.set(target_ip[:current_pos])
            current_pos += 1
            
            # Programar siguiente carácter
            self.parent_frame.after(50, lambda: self._animate_ip_input(target_ip, current_pos))
    
    def _setup_tooltips(self):
        """Configura tooltips para los elementos."""
        self._add_tooltip(
            self.ip_entry, 
            "Ingrese una dirección IP válida\n"
            "Ejemplos: 192.168.1.1, 10.0.0.1\n"
            "Use Tab para autocompletar"
        )
        
        self._add_tooltip(
            self.history_btn,
            "Historial de IPs utilizadas\n"
            "Clic para ver IPs recientes"
        )
    
    def _add_tooltip(self, widget, text):
        """Agrega tooltip a un widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg="#ffffcc", relief="solid", borderwidth=1)
            
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip.geometry(f"+{x}+{y}")
            
            label = tk.Label(
                tooltip, 
                text=text, 
                bg="#ffffcc",
                font=("Arial", 8),
                justify=tk.LEFT,
                padx=5,
                pady=3
            )
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                try:
                    widget.tooltip.destroy()
                except:
                    pass
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def set_ip_change_callback(self, callback: Callable[[str], None]):
        """
        Establece el callback para cuando cambie la IP.
        
        Args:
            callback: Función a llamar cuando cambie la IP
        """
        self.on_ip_change_callback = callback
    
    def _on_ip_changed(self, *args):
        """Callback interno cuando cambia la IP."""
        if self.on_ip_change_callback:
            self.on_ip_change_callback(self.ip_var.get())
    
    def get_ip(self) -> str:
        """
        Obtiene la IP actual.
        
        Returns:
            Dirección IP actual
        """
        return self.ip_var.get().strip()
    
    def set_ip(self, ip: str):
        """
        Establece la IP programáticamente.
        
        Args:
            ip: Dirección IP a establecer
        """
        self.ip_var.set(ip)
    
    def validate_ip(self) -> bool:
        """
        Valida que la IP actual sea válida.
        
        Returns:
            True si la IP es válida
        """
        return self.is_valid.get()
    
    def set_enabled(self, enabled: bool):
        """
        Habilita o deshabilita el widget.
        
        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        self.enabled = enabled
        state = tk.NORMAL if enabled else tk.DISABLED
        
        self.ip_entry.config(state=state)
        self.history_btn.config(state=state)
        
        # Actualizar estilo visual
        if not enabled:
            self.ip_entry.config(style="Disabled.TEntry")
        else:
            self.ip_entry.config(style="")
    
    def get_validation_status(self) -> tuple[bool, str]:
        """
        Obtiene el estado de validación actual.
        
        Returns:
            Tupla (es_válida, mensaje)
        """
        return self.is_valid.get(), self.validation_message.get() 