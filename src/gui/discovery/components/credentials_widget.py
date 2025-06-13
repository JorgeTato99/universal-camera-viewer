"""
Widget de credenciales para autenticación en escaneo de puertos.
Permite configurar usuario, contraseña y credenciales rápidas.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple

# cspell:disable
class CredentialsWidget:
    """
    Widget para configurar credenciales de autenticación.
    
    Incluye campos de usuario/contraseña y botones de credenciales rápidas
    basados en la configuración del .env.
    """
    
    def __init__(self, parent_frame: tk.Widget):
        """
        Inicializa el widget de credenciales.
        
        Args:
            parent_frame: Frame padre donde se colocará el widget
        """
        self.parent_frame = parent_frame
        
        # Variables de credenciales
        self.username_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar()
        
        # Callbacks
        self.on_credentials_change_callback: Optional[Callable] = None
        
        self._create_widget()
    
    def _create_widget(self):
        """Crea el widget de credenciales."""
        # Fila 1: Usuario y contraseña
        creds_row = ttk.Frame(self.parent_frame)
        creds_row.pack(fill=tk.X, padx=5, pady=2)
        
        # Usuario
        ttk.Label(creds_row, text="Usuario:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_entry = ttk.Entry(creds_row, textvariable=self.username_var, width=12)
        self.username_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Contraseña
        ttk.Label(creds_row, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.password_entry = ttk.Entry(creds_row, textvariable=self.password_var, width=12, show="*")
        self.password_entry.grid(row=1, column=1, padx=(0, 10))
        
        # Checkbox mostrar contraseña
        show_check = ttk.Checkbutton(
            creds_row, 
            text="Mostrar", 
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_check.grid(row=1, column=2, padx=5)
        
        # Bind para detectar cambios
        self.username_var.trace_add("write", self._on_credentials_changed)
        self.password_var.trace_add("write", self._on_credentials_changed)
        
        # Fila 2: Botones de credenciales rápidas
        self._create_quick_credentials_buttons()
        
        # Advertencia
        warning_label = ttk.Label(
            self.parent_frame,
            text="⚠️ Solo usar en redes propias",
            font=("Arial", 8),
            foreground="orange"
        )
        warning_label.pack(pady=2)
    
    def _create_quick_credentials_buttons(self):
        """Crea botones de credenciales rápidas."""
        # Frame para botones de credenciales rápidas
        quick_creds_frame = ttk.Frame(self.parent_frame)
        quick_creds_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(quick_creds_frame, text="Rápidas:", font=("Arial", 8)).pack(anchor=tk.W)
        
        # Frame para los botones
        buttons_frame = ttk.Frame(quick_creds_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Credenciales comunes siempre disponibles
        ttk.Button(
            buttons_frame, 
            text="admin", 
            command=lambda: self.set_credentials("admin", "admin"),
            width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            buttons_frame, 
            text="123456", 
            command=lambda: self.set_credentials("admin", "123456"),
            width=8
        ).pack(side=tk.LEFT, padx=1)
        
        # Credenciales específicas desde .env
        self._create_dynamic_credentials_buttons(buttons_frame)
    
    def _create_dynamic_credentials_buttons(self, buttons_frame: tk.Widget):
        """
        Crea botones de credenciales dinámicos basados en las variables de entorno.
        
        Args:
            buttons_frame: Frame donde colocar los botones
        """
        try:
            from src.utils.config import ConfigurationManager
            config = ConfigurationManager()
            
            # Verificar y agregar credenciales específicas por marca
            brands_creds = [
                ("Dahua", getattr(config, 'camera_user', None), 
                         getattr(config, 'camera_password', None)),
                ("TP-Link", getattr(config, 'tplink_user', None), 
                           getattr(config, 'tplink_password', None)),
                ("Steren", getattr(config, 'steren_user', None), 
                          getattr(config, 'steren_password', None)),
                ("Generic", getattr(config, 'generic_user', None), 
                           getattr(config, 'generic_password', None))
            ]
            
            for brand_name, username, password in brands_creds:
                if username and password:  # Solo crear botón si ambos están configurados
                    ttk.Button(
                        buttons_frame, 
                        text=brand_name[:6], 
                        command=lambda u=username, p=password: self.set_credentials(u, p),
                        width=8
                    ).pack(side=tk.LEFT, padx=1)
                    
        except Exception as e:
            print(f"Error cargando credenciales dinámicas: {e}")
    
    def _toggle_password_visibility(self):
        """Alterna la visibilidad de la contraseña."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def _on_credentials_changed(self, *args):
        """Callback interno cuando cambian las credenciales."""
        if self.on_credentials_change_callback:
            self.on_credentials_change_callback(self.get_credentials())
    
    def set_credentials(self, username: str, password: str):
        """
        Establece las credenciales.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
        """
        self.username_var.set(username)
        self.password_var.set(password)
    
    def get_credentials(self) -> Tuple[str, str]:
        """
        Obtiene las credenciales actuales.
        
        Returns:
            Tupla con (usuario, contraseña)
        """
        return self.username_var.get().strip(), self.password_var.get()
    
    def set_credentials_change_callback(self, callback: Callable[[Tuple[str, str]], None]):
        """
        Establece el callback para cuando cambien las credenciales.
        
        Args:
            callback: Función a llamar cuando cambien las credenciales
        """
        self.on_credentials_change_callback = callback
    
    def validate_credentials(self) -> bool:
        """
        Valida que las credenciales estén configuradas.
        
        Returns:
            True si las credenciales son válidas
        """
        username, password = self.get_credentials()
        return bool(username and password)
    
    def clear_credentials(self):
        """Limpia las credenciales."""
        self.username_var.set("")
        self.password_var.set("")
    
    def set_enabled(self, enabled: bool):
        """
        Habilita o deshabilita el widget.
        
        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self.username_entry.config(state=state)
        self.password_entry.config(state=state) 