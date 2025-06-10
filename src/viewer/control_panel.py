"""
Panel de control global para el visor de cámaras.
Permite configurar múltiples cámaras, layouts y opciones avanzadas.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# cspell: disable
class ControlPanel:
    """
    Panel de control global para gestionar múltiples cámaras y configuraciones.
    """
    
    def __init__(self, parent: tk.Tk, on_cameras_change: Optional[Callable] = None):
        """
        Inicializa el panel de control.
        
        Args:
            parent: Ventana principal
            on_cameras_change: Callback cuando cambian las configuraciones de cámaras
        """
        self.parent = parent
        self.on_cameras_change = on_cameras_change
        self.cameras_config: List[Dict[str, Any]] = []
        self.current_layout = "grid_2x2"
        
        # Configurar logging
        self.logger = logging.getLogger("ControlPanel")
        
        # Crear interfaz
        self._create_ui()
        
        # Cargar configuración por defecto
        self._load_default_config()
    
    def _create_ui(self):
        """
        Crea la interfaz del panel de control.
        """
        # Frame principal del panel
        self.main_frame = ttk.LabelFrame(self.parent, text="Panel de Control")
        self.main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña de cámaras
        self._create_cameras_tab()
        
        # Pestaña de layout
        self._create_layout_tab()
        
        # Pestaña de configuración
        self._create_config_tab()
    
    def _create_cameras_tab(self):
        """
        Crea la pestaña de configuración de cámaras.
        """
        # Frame para la pestaña de cámaras
        self.cameras_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cameras_frame, text="Cámaras")
        
        # Frame superior con botones
        buttons_frame = ttk.Frame(self.cameras_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Agregar Cámara", 
            command=self._add_camera_dialog
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            buttons_frame, 
            text="Editar Cámara", 
            command=self._edit_camera_dialog
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            buttons_frame, 
            text="Eliminar Cámara", 
            command=self._remove_camera
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Guardar Config", 
            command=self._save_config
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            buttons_frame, 
            text="Cargar Config", 
            command=self._load_config
        ).pack(side=tk.LEFT, padx=2)
        
        # Lista de cámaras
        cameras_list_frame = ttk.LabelFrame(self.cameras_frame, text="Cámaras Configuradas")
        cameras_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview para mostrar cámaras
        columns = ("name", "ip", "type", "status")
        self.cameras_tree = ttk.Treeview(cameras_list_frame, columns=columns, show="headings")
        
        # Configurar columnas
        self.cameras_tree.heading("name", text="Nombre")
        self.cameras_tree.heading("ip", text="IP")
        self.cameras_tree.heading("type", text="Marca/Protocolo")
        self.cameras_tree.heading("status", text="Estado")
        
        self.cameras_tree.column("name", width=150)
        self.cameras_tree.column("ip", width=120)
        self.cameras_tree.column("type", width=120)
        self.cameras_tree.column("status", width=100)
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(cameras_list_frame, orient=tk.VERTICAL, command=self.cameras_tree.yview)
        self.cameras_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview y scrollbar
        self.cameras_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click para editar
        self.cameras_tree.bind("<Double-1>", lambda e: self._edit_camera_dialog())
    
    def _create_layout_tab(self):
        """
        Crea la pestaña de configuración de layout.
        """
        # Frame para la pestaña de layout
        self.layout_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.layout_frame, text="Layout")
        
        # Opciones de layout
        layout_options_frame = ttk.LabelFrame(self.layout_frame, text="Diseño de Pantalla")
        layout_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.layout_var = tk.StringVar(value=self.current_layout)
        
        layouts = [
            ("1x1 - Una cámara", "single"),
            ("2x1 - Dos cámaras horizontales", "horizontal_2"),
            ("1x2 - Dos cámaras verticales", "vertical_2"),
            ("2x2 - Cuatro cámaras", "grid_2x2"),
            ("3x2 - Seis cámaras", "grid_3x2"),
            ("3x3 - Nueve cámaras", "grid_3x3"),
            ("4x3 - Doce cámaras", "grid_4x3"),
            ("Personalizado", "custom")
        ]
        
        for i, (text, value) in enumerate(layouts):
            ttk.Radiobutton(
                layout_options_frame,
                text=text,
                variable=self.layout_var,
                value=value,
                command=self._on_layout_change
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)
        
        # Opciones de visualización
        display_options_frame = ttk.LabelFrame(self.layout_frame, text="Opciones de Visualización")
        display_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Checkbox para mostrar información
        self.show_info_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_options_frame,
            text="Mostrar información de cámaras",
            variable=self.show_info_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Checkbox para mostrar FPS
        self.show_fps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_options_frame,
            text="Mostrar contador FPS",
            variable=self.show_fps_var
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Checkbox para auto-reconectar
        self.auto_reconnect_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            display_options_frame,
            text="Auto-reconectar cámaras desconectadas",
            variable=self.auto_reconnect_var
        ).pack(anchor=tk.W, padx=5, pady=2)
    
    def _create_config_tab(self):
        """
        Crea la pestaña de configuración avanzada.
        """
        # Frame para la pestaña de configuración
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuración")
        
        # Configuración de logging
        logging_frame = ttk.LabelFrame(self.config_frame, text="Logging")
        logging_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Nivel de logging
        ttk.Label(logging_frame, text="Nivel de logging:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        ttk.Combobox(
            logging_frame,
            textvariable=self.log_level_var,
            values=log_levels,
            state="readonly",
            width=10
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Configuración de conexión
        connection_frame = ttk.LabelFrame(self.config_frame, text="Conexión")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Timeout de conexión
        ttk.Label(connection_frame, text="Timeout de conexión (seg):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.connection_timeout_var = tk.IntVar(value=10)
        ttk.Spinbox(
            connection_frame,
            from_=1,
            to=60,
            textvariable=self.connection_timeout_var,
            width=10
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Reintentos de conexión
        ttk.Label(connection_frame, text="Reintentos de conexión:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.connection_retries_var = tk.IntVar(value=3)
        ttk.Spinbox(
            connection_frame,
            from_=0,
            to=10,
            textvariable=self.connection_retries_var,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Configuración de grabación
        recording_frame = ttk.LabelFrame(self.config_frame, text="Grabación")
        recording_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Directorio de grabación
        ttk.Label(recording_frame, text="Directorio de grabación:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.recording_dir_var = tk.StringVar(value="./recordings")
        ttk.Entry(
            recording_frame,
            textvariable=self.recording_dir_var,
            width=30
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Button(
            recording_frame,
            text="Explorar",
            command=self._browse_recording_dir
        ).grid(row=0, column=2, padx=5, pady=2)
        
        # Botones de configuración
        config_buttons_frame = ttk.Frame(self.config_frame)
        config_buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(
            config_buttons_frame,
            text="Aplicar Configuración",
            command=self._apply_config
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            config_buttons_frame,
            text="Restaurar Predeterminados",
            command=self._restore_defaults
        ).pack(side=tk.LEFT, padx=5)
    
    def _add_camera_dialog(self):
        """
        Abre el diálogo para agregar una nueva cámara.
        """
        self._camera_dialog()
    
    def _edit_camera_dialog(self):
        """
        Abre el diálogo para editar una cámara existente.
        """
        selection = self.cameras_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una cámara para editar")
            return
        
        # Obtener índice de la cámara seleccionada
        item = self.cameras_tree.item(selection[0])
        camera_name = item['values'][0]
        
        # Buscar la cámara en la configuración
        camera_config = None
        camera_index = -1
        for i, cam in enumerate(self.cameras_config):
            if cam.get('name') == camera_name:
                camera_config = cam
                camera_index = i
                break
        
        if camera_config:
            self._camera_dialog(camera_config, camera_index)
        else:
            messagebox.showerror("Error", "No se encontró la configuración de la cámara")
    
    def _camera_dialog(self, camera_config: Optional[Dict[str, Any]] = None, camera_index: int = -1):
        """
        Abre un diálogo para configurar una cámara.
        
        Args:
            camera_config: Configuración existente de la cámara (None para nueva)
            camera_index: Índice de la cámara en la lista (-1 para nueva)
        """
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.parent)
        dialog.title("Configurar Cámara" if camera_config else "Agregar Cámara")
        dialog.geometry("400x500")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal
        
        # Importar el gestor de marcas al inicio del diálogo
        from src.utils.brand_manager import get_brand_manager
        brand_manager = get_brand_manager()
        
        # Variables para el formulario
        name_var = tk.StringVar(value=camera_config.get('name', '') if camera_config else '')
        ip_var = tk.StringVar(value=camera_config.get('ip', '') if camera_config else '')
        brand_var = tk.StringVar(value=camera_config.get('brand', brand_manager.get_default_config().get('default_brand', 'dahua')) if camera_config else brand_manager.get_default_config().get('default_brand', 'dahua'))
        model_var = tk.StringVar(value=camera_config.get('model', '') if camera_config else '')
        type_var = tk.StringVar(value=camera_config.get('type', brand_manager.get_default_config().get('default_protocol', 'rtsp')) if camera_config else brand_manager.get_default_config().get('default_protocol', 'rtsp'))
        username_var = tk.StringVar(value=camera_config.get('username', 'admin') if camera_config else 'admin')
        password_var = tk.StringVar(value=camera_config.get('password', '') if camera_config else '')
        rtsp_port_var = tk.IntVar(value=camera_config.get('rtsp_port', 554) if camera_config else 554)
        http_port_var = tk.IntVar(value=camera_config.get('http_port', 80) if camera_config else 80)
        onvif_port_var = tk.IntVar(value=camera_config.get('onvif_port', 80) if camera_config else 80)
        channel_var = tk.IntVar(value=camera_config.get('channel', 1) if camera_config else 1)
        subtype_var = tk.IntVar(value=camera_config.get('subtype', 0) if camera_config else 0)
        
        row = 0
        
        # Nombre
        ttk.Label(dialog, text="Nombre:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # IP
        ttk.Label(dialog, text="IP:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=ip_var, width=30).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Marca
        ttk.Label(dialog, text="Marca:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        supported_brands = brand_manager.get_supported_brands()
        brand_combo = ttk.Combobox(
            dialog, 
            textvariable=brand_var, 
            values=supported_brands, 
            state="readonly",
            width=27
        )
        brand_combo.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Modelo
        ttk.Label(dialog, text="Modelo:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        model_combo = ttk.Combobox(
            dialog, 
            textvariable=model_var, 
            values=[], 
            state="readonly",
            width=27
        )
        model_combo.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Tipo de conexión
        ttk.Label(dialog, text="Protocolo:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        type_combo = ttk.Combobox(
            dialog, 
            textvariable=type_var, 
            values=[], 
            state="readonly",
            width=27
        )
        type_combo.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Función para actualizar opciones basadas en la marca
        def on_brand_change(*args):
            selected_brand = brand_var.get()
            
            # Obtener información de la marca seleccionada
            brand_info = brand_manager.get_brand_info(selected_brand)
            if not brand_info:
                return
            
            # Actualizar modelos disponibles
            models = brand_manager.get_brand_models(selected_brand)
            model_names = [model["name"] for model in models]
            model_combo['values'] = model_names
            
            # Actualizar protocolos soportados
            protocols = brand_manager.get_supported_protocols(selected_brand)
            type_combo['values'] = protocols
            
            # Establecer valores por defecto
            if model_names:
                model_var.set(model_names[0])
            if protocols:
                type_var.set(protocols[0])  # Primer protocolo disponible
            
            # Configurar puertos por defecto
            default_ports = brand_manager.get_default_ports(selected_brand)
            onvif_port_var.set(default_ports.get("onvif", 80))
            rtsp_port_var.set(default_ports.get("rtsp", 554))
            http_port_var.set(default_ports.get("http", 80))
        
        # Vincular cambio de marca
        brand_var.trace('w', on_brand_change)
        
        # Inicializar valores por defecto
        on_brand_change()
        
        # Usuario
        ttk.Label(dialog, text="Usuario:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=username_var, width=30).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Contraseña
        ttk.Label(dialog, text="Contraseña:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=password_var, show="*", width=30).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Separador
        ttk.Separator(dialog, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)
        row += 1
        
        # Puertos
        ttk.Label(dialog, text="Puerto RTSP:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Spinbox(dialog, from_=1, to=65535, textvariable=rtsp_port_var, width=28).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Puerto HTTP:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Spinbox(dialog, from_=1, to=65535, textvariable=http_port_var, width=28).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        ttk.Label(dialog, text="Puerto ONVIF:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Spinbox(dialog, from_=1, to=65535, textvariable=onvif_port_var, width=28).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Canal
        ttk.Label(dialog, text="Canal:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Spinbox(dialog, from_=1, to=16, textvariable=channel_var, width=28).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Subtipo
        ttk.Label(dialog, text="Subtipo:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Spinbox(dialog, from_=0, to=2, textvariable=subtype_var, width=28).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Botones
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def save_camera():
            # Validar campos
            if not name_var.get().strip():
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            if not ip_var.get().strip():
                messagebox.showerror("Error", "La IP es obligatoria")
                return
            
            # Crear configuración de cámara
            new_camera_config = {
                'name': name_var.get().strip(),
                'ip': ip_var.get().strip(),
                'brand': brand_var.get(),
                'model': model_var.get(),
                'type': type_var.get(),
                'username': username_var.get().strip(),
                'password': password_var.get(),
                'rtsp_port': rtsp_port_var.get(),
                'http_port': http_port_var.get(),
                'onvif_port': onvif_port_var.get(),
                'channel': channel_var.get(),
                'subtype': subtype_var.get()
            }
            
            # Agregar o actualizar cámara
            if camera_index >= 0:
                # Actualizar cámara existente
                self.cameras_config[camera_index] = new_camera_config
            else:
                # Agregar nueva cámara
                self.cameras_config.append(new_camera_config)
            
            # Actualizar la lista visual
            self._update_cameras_list()
            
            # Notificar cambios
            if self.on_cameras_change:
                self.on_cameras_change(self.cameras_config)
            
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="Guardar", command=save_camera).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def _remove_camera(self):
        """
        Elimina la cámara seleccionada.
        """
        selection = self.cameras_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una cámara para eliminar")
            return
        
        # Confirmar eliminación
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar esta cámara?"):
            # Obtener el nombre de la cámara
            item = self.cameras_tree.item(selection[0])
            camera_name = item['values'][0]
            
            # Eliminar de la configuración
            self.cameras_config = [cam for cam in self.cameras_config if cam.get('name') != camera_name]
            
            # Actualizar la lista visual
            self._update_cameras_list()
            
            # Notificar cambios
            if self.on_cameras_change:
                self.on_cameras_change(self.cameras_config)
    
    def _update_cameras_list(self):
        """
        Actualiza la lista visual de cámaras.
        """
        # Limpiar lista actual
        for item in self.cameras_tree.get_children():
            self.cameras_tree.delete(item)
        
        # Agregar cámaras
        for camera in self.cameras_config:
            brand = camera.get('brand', 'N/A')
            protocol = camera.get('type', 'N/A')
            brand_protocol = f"{brand.upper()}/{protocol.upper()}" if brand != 'N/A' else protocol
            
            self.cameras_tree.insert("", "end", values=(
                camera.get('name', 'Sin nombre'),
                camera.get('ip', 'N/A'),
                brand_protocol,
                'Desconectado'
            ))
    
    def _on_layout_change(self):
        """
        Maneja el cambio de layout.
        """
        self.current_layout = self.layout_var.get()
        self.logger.info(f"Layout cambiado a: {self.current_layout}")
        
        # Notificar cambio de layout si hay callback
        # TODO: Implementar callback para cambio de layout
    
    def _save_config(self):
        """
        Guarda la configuración actual en un archivo.
        """
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Guardar configuración"
        )
        
        if filename:
            try:
                config = {
                    'cameras': self.cameras_config,
                    'layout': self.current_layout,
                    'options': {
                        'show_info': self.show_info_var.get(),
                        'show_fps': self.show_fps_var.get(),
                        'auto_reconnect': self.auto_reconnect_var.get(),
                        'log_level': self.log_level_var.get(),
                        'connection_timeout': self.connection_timeout_var.get(),
                        'connection_retries': self.connection_retries_var.get(),
                        'recording_dir': self.recording_dir_var.get()
                    }
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Éxito", f"Configuración guardada en:\n{filename}")
                self.logger.info(f"Configuración guardada: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar configuración:\n{str(e)}")
                self.logger.error(f"Error al guardar configuración: {str(e)}")
    
    def _load_config(self):
        """
        Carga la configuración desde un archivo.
        """
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Cargar configuración"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Cargar cámaras
                self.cameras_config = config.get('cameras', [])
                self._update_cameras_list()
                
                # Cargar layout
                self.current_layout = config.get('layout', 'grid_2x2')
                self.layout_var.set(self.current_layout)
                
                # Cargar opciones
                options = config.get('options', {})
                self.show_info_var.set(options.get('show_info', True))
                self.show_fps_var.set(options.get('show_fps', True))
                self.auto_reconnect_var.set(options.get('auto_reconnect', False))
                self.log_level_var.set(options.get('log_level', 'INFO'))
                self.connection_timeout_var.set(options.get('connection_timeout', 10))
                self.connection_retries_var.set(options.get('connection_retries', 3))
                self.recording_dir_var.set(options.get('recording_dir', './recordings'))
                
                # Notificar cambios
                if self.on_cameras_change:
                    self.on_cameras_change(self.cameras_config)
                
                messagebox.showinfo("Éxito", f"Configuración cargada desde:\n{filename}")
                self.logger.info(f"Configuración cargada: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar configuración:\n{str(e)}")
                self.logger.error(f"Error al cargar configuración: {str(e)}")
    
    def _load_default_config(self):
        """
        Carga la configuración por defecto con todas las cámaras disponibles desde .env.
        """
        try:
            # Importar el gestor de configuración
            from src.utils.config import ConfigurationManager
            
            config = ConfigurationManager()
            available_cameras = config.get_available_cameras()
            
            # Configurar cada cámara disponible
            self.cameras_config = []
            
            for cam_info in available_cameras:
                if cam_info['brand'] == 'dahua':
                    camera_config = {
                        'name': f'Dahua {cam_info["model"]} ({cam_info["ip"]})',
                        'ip': cam_info['ip'],
                        'brand': 'dahua',
                        'model': cam_info['model'],
                        'type': 'rtsp',  # Protocolo por defecto
                        'username': cam_info['user'],
                        'password': config.camera_password,
                        'rtsp_port': config.rtsp_port,
                        'http_port': config.http_port,
                        'onvif_port': config.onvif_port,
                        'channel': config.rtsp_channel,
                        'subtype': config.rtsp_subtype
                    }
                elif cam_info['brand'] == 'tplink':
                    camera_config = {
                        'name': f'TP-Link {cam_info["model"]} ({cam_info["ip"]})',
                        'ip': cam_info['ip'],
                        'brand': 'tplink',
                        'model': cam_info['model'],
                        'type': 'rtsp',
                        'username': cam_info['user'],
                        'password': config.tplink_password,
                        'rtsp_port': 554,
                        'http_port': 80,
                        'onvif_port': 2020,
                        'channel': 1,
                        'subtype': 0
                    }
                
                self.cameras_config.append(camera_config)
            
            # Si no hay cámaras configuradas, usar configuración básica
            if not self.cameras_config:
                self.logger.warning("No se encontraron cámaras configuradas en .env")
                # Configuración mínima de ejemplo
                self.cameras_config = [
                    {
                        'name': 'Cámara de Ejemplo',
                        'ip': '192.168.1.100',
                        'brand': 'dahua',
                        'model': 'Hero-K51H',
                        'type': 'rtsp',
                        'username': 'admin',
                        'password': '',
                        'rtsp_port': 554,
                        'http_port': 80,
                        'onvif_port': 80,
                        'channel': 1,
                        'subtype': 0
                    }
                ]
            else:
                self.logger.info(f"Configuración por defecto cargada con {len(self.cameras_config)} cámaras")
            
        except Exception as e:
            self.logger.warning(f"No se pudo cargar configuración desde .env: {e}")
            # Configuración mínima de respaldo
            self.cameras_config = [
                {
                    'name': 'Cámara de Ejemplo',
                    'ip': '192.168.1.100',
                    'brand': 'dahua',
                    'model': 'Hero-K51H',
                    'type': 'rtsp',
                    'username': 'admin',
                    'password': '',
                    'rtsp_port': 554,
                    'http_port': 80,
                    'onvif_port': 80,
                    'channel': 1,
                    'subtype': 0
                }
            ]
        
        self._update_cameras_list()
        
        # Notificar cambios
        if self.on_cameras_change:
            self.on_cameras_change(self.cameras_config)
    
    def _browse_recording_dir(self):
        """
        Abre el explorador para seleccionar directorio de grabación.
        """
        directory = filedialog.askdirectory(
            title="Seleccionar directorio de grabación",
            initialdir=self.recording_dir_var.get()
        )
        
        if directory:
            self.recording_dir_var.set(directory)
    
    def _apply_config(self):
        """
        Aplica la configuración actual.
        """
        # Configurar logging
        log_level = getattr(logging, self.log_level_var.get())
        logging.getLogger().setLevel(log_level)
        
        # Crear directorio de grabación si no existe
        recording_dir = Path(self.recording_dir_var.get())
        recording_dir.mkdir(parents=True, exist_ok=True)
        
        messagebox.showinfo("Éxito", "Configuración aplicada correctamente")
        self.logger.info("Configuración aplicada")
    
    def _restore_defaults(self):
        """
        Restaura la configuración predeterminada.
        """
        if messagebox.askyesno("Confirmar", "¿Restaurar configuración predeterminada?"):
            # Restaurar valores por defecto
            self.show_info_var.set(True)
            self.show_fps_var.set(True)
            self.auto_reconnect_var.set(False)
            self.log_level_var.set("INFO")
            self.connection_timeout_var.set(10)
            self.connection_retries_var.set(3)
            self.recording_dir_var.set("./recordings")
            self.layout_var.set("grid_2x2")
            
            messagebox.showinfo("Éxito", "Configuración restaurada")
            self.logger.info("Configuración restaurada a valores predeterminados")
    
    def get_cameras_config(self) -> List[Dict[str, Any]]:
        """
        Obtiene la configuración actual de cámaras.
        
        Returns:
            Lista de configuraciones de cámaras
        """
        return self.cameras_config
    
    def get_current_layout(self) -> str:
        """
        Obtiene el layout actual.
        
        Returns:
            Nombre del layout actual
        """
        return self.current_layout 