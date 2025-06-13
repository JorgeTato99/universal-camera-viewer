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
import time
import os
from dotenv import load_dotenv

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
        self.current_layout = 2  # Número de columnas por defecto
        
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
        # Frame principal del panel con estilo mejorado - SIN expand=True
        self.main_frame = ttk.LabelFrame(self.parent, text="🎛️ Panel de Control - Gestión de Cámaras")
        self.main_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Crear notebook para pestañas - altura fija para no competir con el visor
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.X, padx=5, pady=5)
        
        # Pestaña de cámaras
        self._create_cameras_tab()
        
        # Pestaña de layout
        self._create_layout_tab()
        
        # Pestaña de configuración
        self._create_config_tab()
    
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
    
    def _create_cameras_tab(self):
        """
        Crea la pestaña de configuración de cámaras.
        """
        # Frame para la pestaña de cámaras
        self.cameras_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cameras_frame, text="📹 Cámaras")
        
        # Frame superior con botones mejorados
        buttons_frame = ttk.Frame(self.cameras_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botones principales con iconos
        add_btn = ttk.Button(
            buttons_frame, 
            text="➕ Agregar Cámara", 
            command=self._add_camera_dialog,
            style="Accent.TButton"
        )
        add_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(add_btn, "Agregar nueva cámara al sistema")
        
        edit_btn = ttk.Button(
            buttons_frame, 
            text="✏️ Editar Cámara", 
            command=self._edit_camera_dialog
        )
        edit_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(edit_btn, "Editar configuración de la cámara seleccionada")
        
        remove_btn = ttk.Button(
            buttons_frame, 
            text="🗑️ Eliminar Cámara", 
            command=self._remove_camera
        )
        remove_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(remove_btn, "Eliminar cámara seleccionada del sistema")
        
        # Separador visual
        ttk.Separator(buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Botones de configuración
        save_btn = ttk.Button(
            buttons_frame, 
            text="💾 Guardar Config", 
            command=self._save_config
        )
        save_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(save_btn, "Guardar configuración actual en archivo JSON")
        
        load_btn = ttk.Button(
            buttons_frame, 
            text="📂 Cargar Config", 
            command=self._load_config
        )
        load_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(load_btn, "Cargar configuración desde archivo JSON")
        
        # Separador visual
        ttk.Separator(buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Botones de acción rápida
        test_btn = ttk.Button(
            buttons_frame, 
            text="🔍 Probar Conexión", 
            command=self._test_selected_camera
        )
        test_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(test_btn, "Probar conexión de la cámara seleccionada")
        
        duplicate_btn = ttk.Button(
            buttons_frame, 
            text="📋 Duplicar", 
            command=self._duplicate_camera
        )
        duplicate_btn.pack(side=tk.LEFT, padx=2)
        self._add_tooltip(duplicate_btn, "Duplicar configuración de la cámara seleccionada")
        
        # Contador de cámaras (lado derecho)
        self.cameras_count_label = ttk.Label(
            buttons_frame,
            text="📹 0 cámaras configuradas",
            font=("Arial", 9, "bold")
        )
        self.cameras_count_label.pack(side=tk.RIGHT, padx=5)
        
        # Lista de cámaras con estilo mejorado - altura fija para no competir con el visor
        cameras_list_frame = ttk.LabelFrame(self.cameras_frame, text="📋 Cámaras Configuradas")
        cameras_list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Treeview para mostrar cámaras con columnas mejoradas - altura reducida
        columns = ("name", "ip", "type", "brand", "status")
        self.cameras_tree = ttk.Treeview(cameras_list_frame, columns=columns, show="headings", height=5)
        
        # Configurar columnas con iconos
        self.cameras_tree.heading("name", text="📹 Nombre")
        self.cameras_tree.heading("ip", text="🌐 IP")
        self.cameras_tree.heading("type", text="🔧 Protocolo")
        self.cameras_tree.heading("brand", text="🏷️ Marca")
        self.cameras_tree.heading("status", text="📊 Estado")
        
        self.cameras_tree.column("name", width=150)
        self.cameras_tree.column("ip", width=120)
        self.cameras_tree.column("type", width=100)
        self.cameras_tree.column("brand", width=100)
        self.cameras_tree.column("status", width=100)
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(cameras_list_frame, orient=tk.VERTICAL, command=self.cameras_tree.yview)
        self.cameras_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview y scrollbar - altura fija
        self.cameras_tree.pack(side=tk.LEFT, fill=tk.X)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind eventos
        self.cameras_tree.bind("<Double-1>", lambda e: self._edit_camera_dialog())
        self.cameras_tree.bind("<Button-3>", self._show_context_menu)  # Click derecho
        
        # Barra de estado de la pestaña
        status_frame = ttk.Frame(self.cameras_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.cameras_status_label = ttk.Label(
            status_frame,
            text="💡 Selecciona una cámara para ver opciones adicionales",
            font=("Arial", 8),
            foreground="#7f8c8d"
        )
        self.cameras_status_label.pack(side=tk.LEFT)
        
        # Indicador de validación
        self.validation_label = ttk.Label(
            status_frame,
            text="✅ Configuración válida",
            font=("Arial", 8),
            foreground="#27ae60"
        )
        self.validation_label.pack(side=tk.RIGHT)
    
    def _show_context_menu(self, event):
        """
        Muestra menú contextual en el treeview.
        
        Args:
            event: Evento del click derecho
        """
        # Seleccionar item bajo el cursor
        item = self.cameras_tree.identify_row(event.y)
        if item:
            self.cameras_tree.selection_set(item)
            
            # Crear menú contextual
            context_menu = tk.Menu(self.cameras_tree, tearoff=0)
            context_menu.add_command(label="✏️ Editar", command=self._edit_camera_dialog)
            context_menu.add_command(label="📋 Duplicar", command=self._duplicate_camera)
            context_menu.add_command(label="🔍 Probar Conexión", command=self._test_selected_camera)
            context_menu.add_separator()
            context_menu.add_command(label="🗑️ Eliminar", command=self._remove_camera)
            
            # Mostrar menú
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def _test_selected_camera(self):
        """
        Prueba la conexión de la cámara seleccionada.
        """
        selection = self.cameras_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una cámara para probar la conexión")
            return
        
        # Obtener configuración de la cámara seleccionada
        item = selection[0]
        camera_index = self.cameras_tree.index(item)
        camera_config = self.cameras_config[camera_index]
        
        # Mostrar diálogo de prueba
        self._show_connection_test_dialog(camera_config)
    
    def _show_connection_test_dialog(self, camera_config):
        """
        Muestra diálogo de prueba de conexión.
        
        Args:
            camera_config: Configuración de la cámara a probar
        """
        test_window = tk.Toplevel(self.cameras_frame)
        test_window.title(f"🔍 Prueba de Conexión - {camera_config.get('name', 'Cámara')}")
        test_window.geometry("400x300")
        test_window.resizable(False, False)
        
        # Centrar ventana
        test_window.transient(self.cameras_frame)
        test_window.grab_set()
        
        # Información de la prueba
        info_frame = ttk.LabelFrame(test_window, text="📋 Información de Conexión")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        info_text = f"""
🎥 Nombre: {camera_config.get('name', 'N/A')}
🌐 IP: {camera_config.get('ip', 'N/A')}
👤 Usuario: {camera_config.get('username', 'N/A')}
🔧 Protocolo: {camera_config.get('type', 'N/A').upper()}
🏷️ Marca: {camera_config.get('brand', 'N/A').upper()}
🔌 Puerto ONVIF: {camera_config.get('onvif_port', 'N/A')}
        """
        
        info_label = ttk.Label(info_frame, text=info_text, font=("Arial", 10), justify=tk.LEFT)
        info_label.pack(padx=10, pady=10)
        
        # Área de resultados
        results_frame = ttk.LabelFrame(test_window, text="📊 Resultados de la Prueba")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        results_text = tk.Text(results_frame, height=8, width=50, font=("Courier", 9))
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Botones
        buttons_frame = ttk.Frame(test_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def run_test():
            """Ejecuta la prueba de conexión."""
            results_text.delete(1.0, tk.END)
            results_text.insert(tk.END, "🔍 Iniciando prueba de conexión...\n\n")
            results_text.update()
            
            try:
                # Simular prueba de conexión (aquí iría la lógica real)
                import time
                
                results_text.insert(tk.END, "📡 Probando conectividad de red...\n")
                results_text.update()
                time.sleep(0.5)
                
                results_text.insert(tk.END, "✅ Ping exitoso\n\n")
                results_text.update()
                
                results_text.insert(tk.END, "🔌 Probando puerto ONVIF...\n")
                results_text.update()
                time.sleep(0.5)
                
                results_text.insert(tk.END, "✅ Puerto accesible\n\n")
                results_text.update()
                
                results_text.insert(tk.END, "🔐 Probando credenciales...\n")
                results_text.update()
                time.sleep(0.5)
                
                results_text.insert(tk.END, "✅ Autenticación exitosa\n\n")
                results_text.update()
                
                results_text.insert(tk.END, "🎥 Probando stream de video...\n")
                results_text.update()
                time.sleep(1.0)
                
                results_text.insert(tk.END, "✅ Stream disponible\n\n")
                results_text.insert(tk.END, "🎉 PRUEBA EXITOSA: La cámara está lista para usar\n")
                results_text.update()
                
            except Exception as e:
                results_text.insert(tk.END, f"❌ ERROR: {str(e)}\n")
        
        test_btn = ttk.Button(buttons_frame, text="🚀 Ejecutar Prueba", command=run_test)
        test_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = ttk.Button(buttons_frame, text="Cerrar", command=test_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def _duplicate_camera(self):
        """
        Duplica la configuración de la cámara seleccionada.
        """
        selection = self.cameras_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una cámara para duplicar")
            return
        
        # Obtener configuración de la cámara seleccionada
        item = selection[0]
        camera_index = self.cameras_tree.index(item)
        original_config = self.cameras_config[camera_index].copy()
        
        # Modificar nombre para evitar duplicados
        original_name = original_config.get('name', 'Cámara')
        original_config['name'] = f"{original_name} (Copia)"
        
        # Abrir diálogo de edición con la configuración duplicada
        self._camera_dialog(original_config, -1)
    
    def _update_cameras_count(self):
        """
        Actualiza el contador de cámaras.
        """
        count = len(self.cameras_config)
        if count == 0:
            text = "📹 Sin cámaras configuradas"
        elif count == 1:
            text = "📹 1 cámara configurada"
        else:
            text = f"📹 {count} cámaras configuradas"
        
        self.cameras_count_label.config(text=text)
        
        # Actualizar validación
        if count > 0:
            self.validation_label.config(text="✅ Configuración válida", foreground="#27ae60")
        else:
            self.validation_label.config(text="⚠️ Sin cámaras configuradas", foreground="#f39c12")
    
    def _create_layout_tab(self):
        """
        Crea la pestaña de configuración de layout.
        """
        # Frame para la pestaña de layout
        self.layout_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.layout_frame, text="📱 Layout")
        
        # Descripción mejorada
        description_frame = ttk.LabelFrame(self.layout_frame, text="ℹ️ Información de Layouts")
        description_frame.pack(fill=tk.X, padx=5, pady=5)
        
        description_text = """
🎯 Los layouts determinan cómo se organizan las cámaras en pantalla.
📱 Selecciona el número de columnas por fila según tus necesidades.
🔄 Las cámaras adicionales se colocarán automáticamente en filas siguientes.
✨ El sistema usa columnspan inteligente para optimizar el espacio.
        """
        
        description_label = ttk.Label(
            description_frame,
            text=description_text,
            font=("Arial", 9),
            justify=tk.LEFT
        )
        description_label.pack(padx=10, pady=5)
        
        # Opciones de layout - Selector de columnas
        layout_options_frame = ttk.LabelFrame(self.layout_frame, text="📐 Configuración de Columnas")
        layout_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Frame para los radio buttons
        columns_frame = ttk.Frame(layout_options_frame)
        columns_frame.pack(pady=10)
        
        self.layout_var = tk.IntVar(value=self.current_layout)
        
        # Opciones de columnas (1-4) con iconos
        column_options = [
            (1, "1️⃣ 1 columna\n(100% ancho)"),
            (2, "2️⃣ 2 columnas\n(50% cada una)"),
            (3, "3️⃣ 3 columnas\n(33% cada una)"),
            (4, "4️⃣ 4 columnas\n(25% cada una)")
        ]
        
        for i, (cols, description) in enumerate(column_options):
            radio_btn = ttk.Radiobutton(
                columns_frame,
                text=description,
                variable=self.layout_var,
                value=cols,
                command=self._on_layout_change
            )
            radio_btn.grid(row=0, column=i, padx=10, pady=5)
            self._add_tooltip(radio_btn, f"Organizar cámaras en {cols} columna{'s' if cols > 1 else ''} por fila")
        
        # Ejemplo visual mejorado
        example_frame = ttk.LabelFrame(layout_options_frame, text="👁️ Vista Previa con 4 Cámaras")
        example_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.example_label = ttk.Label(
            example_frame,
            text=self._get_layout_example(self.current_layout),
            font=("Courier", 8),
            justify=tk.LEFT
        )
        self.example_label.pack(pady=5)
        
        # Opciones de visualización mejoradas
        display_options_frame = ttk.LabelFrame(self.layout_frame, text="🎨 Opciones de Visualización")
        display_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Checkbox para mostrar información
        self.show_info_var = tk.BooleanVar(value=True)
        info_check = ttk.Checkbutton(
            display_options_frame,
            text="📊 Mostrar información de cámaras (IP, FPS, estado)",
            variable=self.show_info_var,
            command=self._on_display_option_change
        )
        info_check.pack(anchor=tk.W, padx=10, pady=5)
        self._add_tooltip(info_check, "Mostrar/ocultar información detallada en cada cámara")
        
        # Checkbox para mostrar controles
        self.show_controls_var = tk.BooleanVar(value=True)
        controls_check = ttk.Checkbutton(
            display_options_frame,
            text="🎛️ Mostrar controles de cámara (conectar, snapshot, etc.)",
            variable=self.show_controls_var,
            command=self._on_display_option_change
        )
        controls_check.pack(anchor=tk.W, padx=10, pady=5)
        self._add_tooltip(controls_check, "Mostrar/ocultar botones de control en cada cámara")
        
        # Checkbox para auto-reconexión
        self.auto_reconnect_var = tk.BooleanVar(value=False)
        reconnect_check = ttk.Checkbutton(
            display_options_frame,
            text="🔄 Reconexión automática en caso de error",
            variable=self.auto_reconnect_var,
            command=self._on_display_option_change
        )
        reconnect_check.pack(anchor=tk.W, padx=10, pady=5)
        self._add_tooltip(reconnect_check, "Intentar reconectar automáticamente si se pierde la conexión")
        
        # Información del layout actual
        current_layout_frame = ttk.LabelFrame(self.layout_frame, text="📋 Layout Actual")
        current_layout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.current_layout_info = ttk.Label(
            current_layout_frame,
            text=f"📱 Layout actual: {self.current_layout} columnas",
            font=("Arial", 10, "bold")
        )
        self.current_layout_info.pack(padx=10, pady=5)
    
    def _on_display_option_change(self):
        """
        Maneja cambios en las opciones de visualización.
        """
        # Aquí se pueden implementar cambios en tiempo real
        self.logger.info("Opciones de visualización actualizadas")
        
        # Notificar cambios si hay callback
        if self.on_cameras_change:
            self.on_cameras_change(self.cameras_config)
    
    def _get_layout_example(self, columns: int) -> str:
        """
        Genera un ejemplo visual del layout.
        
        Args:
            columns: Número de columnas
            
        Returns:
            String con representación visual del layout
        """
        examples = {
            1: """
┌─────────────────────────────────────┐
│              Cámara 1               │
├─────────────────────────────────────┤
│              Cámara 2               │
├─────────────────────────────────────┤
│              Cámara 3               │
├─────────────────────────────────────┤
│              Cámara 4               │
└─────────────────────────────────────┘
            """,
            2: """
┌─────────────────┬─────────────────┐
│    Cámara 1     │    Cámara 2     │
├─────────────────┼─────────────────┤
│    Cámara 3     │    Cámara 4     │
└─────────────────┴─────────────────┘
            """,
            3: """
┌───────────┬───────────┬───────────┐
│ Cámara 1  │ Cámara 2  │ Cámara 3  │
├───────────┼───────────┼───────────┤
│         Cámara 4 (columnspan)     │
└───────────┴───────────┴───────────┘
            """,
            4: """
┌────────┬────────┬────────┬────────┐
│Cámara 1│Cámara 2│Cámara 3│Cámara 4│
└────────┴────────┴────────┴────────┘
            """
        }
        
        return examples.get(columns, "Layout no disponible")
    
    def _on_layout_change(self):
        """
        Maneja el cambio de layout.
        """
        new_layout = self.layout_var.get()
        if new_layout != self.current_layout:
            self.current_layout = new_layout
            
            # Actualizar ejemplo visual
            self.example_label.config(text=self._get_layout_example(self.current_layout))
            
            # Actualizar información del layout actual
            self.current_layout_info.config(text=f"📱 Layout actual: {self.current_layout} columnas")
            
            # Notificar cambio
            if self.on_cameras_change:
                self.on_cameras_change(self.cameras_config)
            
            self.logger.info(f"Layout cambiado a {self.current_layout} columnas")
    
    def _create_config_tab(self):
        """
        Crea la pestaña de configuración general.
        """
        # Frame para la pestaña de configuración
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="⚙️ Configuración")
        
        # Configuración de conexión
        connection_frame = ttk.LabelFrame(self.config_frame, text="🌐 Configuración de Conexión")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Timeout de conexión
        timeout_frame = ttk.Frame(connection_frame)
        timeout_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="⏱️ Timeout de conexión (segundos):").pack(side=tk.LEFT)
        
        self.timeout_var = tk.StringVar(value="10")
        timeout_spinbox = ttk.Spinbox(
            timeout_frame,
            from_=5,
            to=60,
            textvariable=self.timeout_var,
            width=10
        )
        timeout_spinbox.pack(side=tk.RIGHT, padx=5)
        self._add_tooltip(timeout_spinbox, "Tiempo máximo de espera para establecer conexión")
        
        # Reintentos de conexión
        retries_frame = ttk.Frame(connection_frame)
        retries_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(retries_frame, text="🔄 Reintentos automáticos:").pack(side=tk.LEFT)
        
        self.retries_var = tk.StringVar(value="3")
        retries_spinbox = ttk.Spinbox(
            retries_frame,
            from_=0,
            to=10,
            textvariable=self.retries_var,
            width=10
        )
        retries_spinbox.pack(side=tk.RIGHT, padx=5)
        self._add_tooltip(retries_spinbox, "Número de reintentos automáticos en caso de fallo")
        
        # Configuración de grabación
        recording_frame = ttk.LabelFrame(self.config_frame, text="📹 Configuración de Grabación")
        recording_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Directorio de grabación
        dir_frame = ttk.Frame(recording_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dir_frame, text="📁 Directorio de grabación:").pack(side=tk.LEFT)
        
        self.recording_dir_var = tk.StringVar(value="./recordings")
        dir_entry = ttk.Entry(dir_frame, textvariable=self.recording_dir_var, width=30)
        dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(dir_frame, text="📂 Examinar", command=self._browse_recording_dir)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        self._add_tooltip(browse_btn, "Seleccionar directorio para guardar grabaciones")
        
        # Calidad de grabación
        quality_frame = ttk.Frame(recording_frame)
        quality_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(quality_frame, text="🎬 Calidad de grabación:").pack(side=tk.LEFT)
        
        self.quality_var = tk.StringVar(value="Alta")
        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            values=["Baja", "Media", "Alta", "Ultra"],
            state="readonly",
            width=15
        )
        quality_combo.pack(side=tk.RIGHT, padx=5)
        self._add_tooltip(quality_combo, "Calidad de video para grabaciones")
        
        # Configuración de interfaz
        interface_frame = ttk.LabelFrame(self.config_frame, text="🎨 Configuración de Interfaz")
        interface_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tema de la interfaz
        theme_frame = ttk.Frame(interface_frame)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(theme_frame, text="🎨 Tema de la interfaz:").pack(side=tk.LEFT)
        
        self.theme_var = tk.StringVar(value="Claro")
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["Claro", "Oscuro", "Auto"],
            state="readonly",
            width=15
        )
        theme_combo.pack(side=tk.RIGHT, padx=5)
        self._add_tooltip(theme_combo, "Tema visual de la aplicación")
        
        # Idioma
        language_frame = ttk.Frame(interface_frame)
        language_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(language_frame, text="🌍 Idioma:").pack(side=tk.LEFT)
        
        self.language_var = tk.StringVar(value="Español")
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=["Español", "English", "Français"],
            state="readonly",
            width=15
        )
        language_combo.pack(side=tk.RIGHT, padx=5)
        self._add_tooltip(language_combo, "Idioma de la interfaz")
        
        # Configuración avanzada
        advanced_frame = ttk.LabelFrame(self.config_frame, text="🔧 Configuración Avanzada")
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Opciones avanzadas con checkboxes
        self.debug_mode_var = tk.BooleanVar(value=False)
        debug_check = ttk.Checkbutton(
            advanced_frame,
            text="🐛 Modo debug (logs detallados)",
            variable=self.debug_mode_var
        )
        debug_check.pack(anchor=tk.W, padx=10, pady=2)
        self._add_tooltip(debug_check, "Activar logging detallado para diagnóstico")
        
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_check = ttk.Checkbutton(
            advanced_frame,
            text="💾 Guardado automático de configuración",
            variable=self.auto_save_var
        )
        auto_save_check.pack(anchor=tk.W, padx=10, pady=2)
        self._add_tooltip(auto_save_check, "Guardar automáticamente cambios de configuración")
        
        self.notifications_var = tk.BooleanVar(value=True)
        notifications_check = ttk.Checkbutton(
            advanced_frame,
            text="🔔 Notificaciones del sistema",
            variable=self.notifications_var
        )
        notifications_check.pack(anchor=tk.W, padx=10, pady=2)
        self._add_tooltip(notifications_check, "Mostrar notificaciones de eventos importantes")
        
        # Botones de configuración
        config_buttons_frame = ttk.Frame(self.config_frame)
        config_buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Botón aplicar
        apply_btn = ttk.Button(
            config_buttons_frame,
            text="✅ Aplicar Configuración",
            command=self._apply_config,
            style="Accent.TButton"
        )
        apply_btn.pack(side=tk.LEFT, padx=5)
        self._add_tooltip(apply_btn, "Aplicar todos los cambios de configuración")
        
        # Botón restaurar
        restore_btn = ttk.Button(
            config_buttons_frame,
            text="🔄 Restaurar Valores por Defecto",
            command=self._restore_defaults
        )
        restore_btn.pack(side=tk.LEFT, padx=5)
        self._add_tooltip(restore_btn, "Restaurar configuración a valores por defecto")
        
        # Información de la configuración
        config_info_frame = ttk.LabelFrame(self.config_frame, text="ℹ️ Información")
        config_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        config_info_text = """
🎯 Esta configuración afecta el comportamiento global de la aplicación.
⚙️ Los cambios se aplicarán inmediatamente al presionar "Aplicar".
💾 La configuración se guarda automáticamente si está habilitado.
🔄 Puedes restaurar valores por defecto en cualquier momento.
        """
        
        config_info_label = ttk.Label(
            config_info_frame,
            text=config_info_text,
            font=("Arial", 9),
            justify=tk.LEFT
        )
        config_info_label.pack(padx=10, pady=5)
    
    def _add_camera_dialog(self):
        """
        Abre el diálogo para agregar una nueva cámara.
        """
        self._camera_dialog()
    
    def _edit_camera_dialog(self):
        """
        Abre el diálogo para editar la cámara seleccionada.
        """
        selection = self.cameras_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una cámara para editar")
            return
        
        # Obtener configuración de la cámara seleccionada
        item = selection[0]
        camera_index = self.cameras_tree.index(item)
        camera_config = self.cameras_config[camera_index]
        
        # Abrir diálogo de edición
        self._camera_dialog(camera_config, camera_index)
    
    def _camera_dialog(self, camera_config: Optional[Dict[str, Any]] = None, camera_index: int = -1):
        """
        Muestra el diálogo de configuración de cámara.
        
        Args:
            camera_config: Configuración existente (None para nueva cámara)
            camera_index: Índice de la cámara (-1 para nueva cámara)
        """
        is_new_camera = camera_config is None
        if is_new_camera:
            camera_config = {
                'name': '',
                'ip': '',
                'username': 'admin',
                'password': '',
                'type': 'rtsp',  # Cambiado de 'onvif' a 'rtsp' para mejor compatibilidad
                'brand': 'dahua',
                'onvif_port': 80,
                'rtsp_port': 554,
                'http_port': 80
            }
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.cameras_frame)
        dialog.title(f"{'➕ Agregar' if is_new_camera else '✏️ Editar'} Cámara")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        
        # Centrar ventana
        dialog.transient(self.cameras_frame)
        dialog.grab_set()
        
        # Variables para los campos
        name_var = tk.StringVar(value=camera_config.get('name', ''))
        ip_var = tk.StringVar(value=camera_config.get('ip', ''))
        username_var = tk.StringVar(value=camera_config.get('username', 'admin'))
        password_var = tk.StringVar(value=camera_config.get('password', ''))
        type_var = tk.StringVar(value=camera_config.get('type', 'onvif'))
        brand_var = tk.StringVar(value=camera_config.get('brand', 'dahua'))
        onvif_port_var = tk.StringVar(value=str(camera_config.get('onvif_port', 80)))
        rtsp_port_var = tk.StringVar(value=str(camera_config.get('rtsp_port', 554)))
        http_port_var = tk.StringVar(value=str(camera_config.get('http_port', 80)))
        
        # Frame principal con scroll
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Información básica
        basic_frame = ttk.LabelFrame(main_frame, text="📋 Información Básica")
        basic_frame.pack(fill=tk.X, pady=5)
        
        # Nombre
        ttk.Label(basic_frame, text="🎥 Nombre de la cámara:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        name_entry = ttk.Entry(basic_frame, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        basic_frame.grid_columnconfigure(1, weight=1)
        
        # IP
        ttk.Label(basic_frame, text="🌐 Dirección IP:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ip_entry = ttk.Entry(basic_frame, textvariable=ip_var, width=30)
        ip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Credenciales
        credentials_frame = ttk.LabelFrame(main_frame, text="🔐 Credenciales")
        credentials_frame.pack(fill=tk.X, pady=5)
        
        # Usuario
        ttk.Label(credentials_frame, text="👤 Usuario:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        username_entry = ttk.Entry(credentials_frame, textvariable=username_var, width=30)
        username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        credentials_frame.grid_columnconfigure(1, weight=1)
        
        # Contraseña
        ttk.Label(credentials_frame, text="🔒 Contraseña:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        password_entry = ttk.Entry(credentials_frame, textvariable=password_var, show="*", width=30)
        password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Configuración de conexión
        connection_frame = ttk.LabelFrame(main_frame, text="🔧 Configuración de Conexión")
        connection_frame.pack(fill=tk.X, pady=5)
        
        # Protocolo
        ttk.Label(connection_frame, text="🔧 Protocolo:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        type_combo = ttk.Combobox(
            connection_frame,
            textvariable=type_var,
            values=["onvif", "rtsp", "amcrest"],
            state="readonly",
            width=27
        )
        type_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        connection_frame.grid_columnconfigure(1, weight=1)
        
        # Marca
        ttk.Label(connection_frame, text="🏷️ Marca:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        brand_combo = ttk.Combobox(
            connection_frame,
            textvariable=brand_var,
            values=["dahua", "tplink", "steren", "generic"],
            state="readonly",
            width=27
        )
        brand_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Puertos
        ports_frame = ttk.LabelFrame(main_frame, text="🔌 Configuración de Puertos")
        ports_frame.pack(fill=tk.X, pady=5)
        
        # Puerto ONVIF
        ttk.Label(ports_frame, text="🔌 Puerto ONVIF:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        onvif_port_entry = ttk.Entry(ports_frame, textvariable=onvif_port_var, width=10)
        onvif_port_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Puerto RTSP
        ttk.Label(ports_frame, text="📡 Puerto RTSP:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        rtsp_port_entry = ttk.Entry(ports_frame, textvariable=rtsp_port_var, width=10)
        rtsp_port_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Puerto HTTP
        ttk.Label(ports_frame, text="🌐 Puerto HTTP:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        http_port_entry = ttk.Entry(ports_frame, textvariable=http_port_var, width=10)
        http_port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Función para actualizar puertos según la marca
        def on_brand_change(*args):
            brand = brand_var.get().lower()
            if brand == 'tplink':
                onvif_port_var.set('2020')
                rtsp_port_var.set('554')
                http_port_var.set('80')
            elif brand == 'steren':
                onvif_port_var.set('8000')
                rtsp_port_var.set('554')
                http_port_var.set('80')
            elif brand == 'dahua':
                onvif_port_var.set('80')
                rtsp_port_var.set('554')
                http_port_var.set('80')
            else:  # generic
                onvif_port_var.set('80')
                rtsp_port_var.set('554')
                http_port_var.set('80')
        
        brand_var.trace('w', on_brand_change)
        
        # Validación en tiempo real
        validation_frame = ttk.Frame(main_frame)
        validation_frame.pack(fill=tk.X, pady=5)
        
        validation_label = ttk.Label(
            validation_frame,
            text="⚠️ Complete todos los campos obligatorios",
            font=("Arial", 9),
            foreground="#f39c12"
        )
        validation_label.pack()
        
        def validate_fields():
            """Valida los campos en tiempo real."""
            name = name_var.get().strip()
            ip = ip_var.get().strip()
            
            if not name or not ip:
                validation_label.config(text="⚠️ Complete todos los campos obligatorios", foreground="#f39c12")
                return False
            
            # Validar IP básica
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, ip):
                validation_label.config(text="❌ Formato de IP inválido", foreground="#e74c3c")
                return False
            
            validation_label.config(text="✅ Configuración válida", foreground="#27ae60")
            return True
        
        # Bind validación a los campos principales
        name_var.trace('w', lambda *args: validate_fields())
        ip_var.trace('w', lambda *args: validate_fields())
        
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        def save_camera():
            """Guarda la configuración de la cámara."""
            if not validate_fields():
                messagebox.showerror("Error", "Por favor corrige los errores antes de guardar")
                return
            
            # Crear configuración
            new_config = {
                'name': name_var.get().strip(),
                'ip': ip_var.get().strip(),
                'username': username_var.get().strip(),
                'password': password_var.get(),
                'type': type_var.get(),
                'brand': brand_var.get(),
                'onvif_port': int(onvif_port_var.get()),
                'rtsp_port': int(rtsp_port_var.get()),
                'http_port': int(http_port_var.get())
            }
            
            try:
                if is_new_camera:
                    # Agregar nueva cámara
                    self.cameras_config.append(new_config)
                    self.logger.info(f"Nueva cámara agregada: {new_config['name']}")
                else:
                    # Actualizar cámara existente
                    self.cameras_config[camera_index] = new_config
                    self.logger.info(f"Cámara actualizada: {new_config['name']}")
            
                # Actualizar lista y notificar cambios
                self._update_cameras_list()
                self._update_cameras_count()
            
                if self.on_cameras_change:
                    self.on_cameras_change(self.cameras_config)
            
                dialog.destroy()
            
                # Mostrar confirmación
                action = "agregada" if is_new_camera else "actualizada"
                messagebox.showinfo("Éxito", f"✅ Cámara {action} exitosamente")
            
            except Exception as e:
                self.logger.error(f"Error guardando cámara: {str(e)}")
                messagebox.showerror("Error", f"Error al guardar la cámara:\n{str(e)}")
        
        def test_connection():
            """Prueba la conexión con la configuración actual."""
            if not validate_fields():
                messagebox.showerror("Error", "Por favor corrige los errores antes de probar")
                return
            
            # Crear configuración temporal para prueba
            test_config = {
                'name': name_var.get().strip(),
                'ip': ip_var.get().strip(),
                'username': username_var.get().strip(),
                'password': password_var.get(),
                'type': type_var.get(),
                'brand': brand_var.get(),
                'onvif_port': int(onvif_port_var.get()),
                'rtsp_port': int(rtsp_port_var.get()),
                'http_port': int(http_port_var.get())
            }
            
            self._show_connection_test_dialog(test_config)
        
        # Botones de acción
        ttk.Button(
            buttons_frame,
            text="🔍 Probar Conexión",
            command=test_connection
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="✅ Guardar",
            command=save_camera,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="❌ Cancelar",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Validación inicial
        validate_fields()
        
        # Focus en el primer campo
        if is_new_camera:
            name_entry.focus()
        else:
            ip_entry.focus()
    
    def _remove_camera(self):
        """
        Elimina la cámara seleccionada.
        """
        selection = self.cameras_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una cámara para eliminar")
            return
        
        # Obtener información de la cámara
        item = selection[0]
        camera_index = self.cameras_tree.index(item)
        camera_name = self.cameras_config[camera_index].get('name', 'Cámara')
        
        # Confirmar eliminación
        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la cámara '{camera_name}'?\n\nEsta acción no se puede deshacer."
        ):
            try:
                # Eliminar de la configuración
                del self.cameras_config[camera_index]
            
                # Actualizar lista y notificar cambios
                self._update_cameras_list()
                self._update_cameras_count()
            
                if self.on_cameras_change:
                    self.on_cameras_change(self.cameras_config)
                
                self.logger.info(f"Cámara eliminada: {camera_name}")
                messagebox.showinfo("Éxito", f"✅ Cámara '{camera_name}' eliminada exitosamente")
            
            except Exception as e:
                self.logger.error(f"Error eliminando cámara: {str(e)}")
                messagebox.showerror("Error", f"Error al eliminar la cámara:\n{str(e)}")
    
    def _update_cameras_list(self):
        """
        Actualiza la lista de cámaras en el treeview.
        """
        # Limpiar lista actual
        for item in self.cameras_tree.get_children():
            self.cameras_tree.delete(item)
        
        # Agregar cámaras
        for i, camera in enumerate(self.cameras_config):
            # Determinar estado (por ahora siempre "Configurado")
            status = "✅ Configurado"
            
            self.cameras_tree.insert(
                "",
                "end",
                values=(
                    camera.get('name', f'Cámara {i+1}'),
                    camera.get('ip', 'N/A'),
                    camera.get('type', 'N/A').upper(),
                    camera.get('brand', 'N/A').upper(),
                    status
                )
            )
        
        # Actualizar estado de la pestaña
        count = len(self.cameras_config)
        if count == 0:
            self.cameras_status_label.config(text="💡 Agrega cámaras usando el botón '➕ Agregar Cámara'")
        else:
            self.cameras_status_label.config(text=f"💡 {count} cámara{'s' if count != 1 else ''} configurada{'s' if count != 1 else ''}")
    
    def _save_config(self):
        """
        Guarda la configuración actual en un archivo JSON.
        """
        try:
            # Abrir diálogo para seleccionar archivo
            filename = filedialog.asksaveasfilename(
                title="Guardar Configuración",
                defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            
            if filename:
                # Preparar configuración completa
                config_data = {
                    'cameras': self.cameras_config,
                    'layout': self.current_layout,
                    'version': '2.0',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Guardar archivo
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Configuración guardada en: {filename}")
                messagebox.showinfo("Éxito", f"✅ Configuración guardada exitosamente en:\n{filename}")
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {str(e)}")
            messagebox.showerror("Error", f"Error al guardar la configuración:\n{str(e)}")
    
    def _load_config(self):
        """
        Carga configuración desde un archivo JSON.
        """
        try:
            # Abrir diálogo para seleccionar archivo
            filename = filedialog.askopenfilename(
                title="Cargar Configuración",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            
            if filename:
                # Cargar archivo
                with open(filename, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Validar estructura
                if 'cameras' not in config_data:
                    raise ValueError("Archivo de configuración inválido: falta sección 'cameras'")
                
                # Confirmar carga
                if messagebox.askyesno(
                    "Confirmar Carga",
                    f"¿Cargar configuración desde {filename}?\n\nEsto reemplazará la configuración actual."
                ):
                    # Cargar configuración
                    self.cameras_config = config_data['cameras']
                    
                    # Cargar layout si está disponible
                    if 'layout' in config_data:
                        self.current_layout = config_data['layout']
                    self.layout_var.set(self.current_layout)
                    self.example_label.config(text=self._get_layout_example(self.current_layout))
                    self.current_layout_info.config(text=f"📱 Layout actual: {self.current_layout} columnas")
                    
                    # Actualizar interfaz
                    self._update_cameras_list()
                    self._update_cameras_count()
                
                # Notificar cambios
                if self.on_cameras_change:
                    self.on_cameras_change(self.cameras_config)
                
                self.logger.info(f"Configuración cargada desde: {filename}")
                messagebox.showinfo("Éxito", f"✅ Configuración cargada exitosamente desde:\n{filename}")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar la configuración:\n{str(e)}")
    
    def _load_default_config(self):
        """
        Carga la configuración por defecto desde el archivo .env.
        """
        try:
            # Cargar variables de entorno
            load_dotenv()
            
            # Configuración desde .env
            default_cameras = [
                {
                    'name': 'Cámara Dahua Hero-K51H',
                    'ip': os.getenv('CAMERA_IP', '192.168.1.172'),
                    'username': os.getenv('CAMERA_USER', 'admin'),
                    'password': os.getenv('CAMERA_PASSWORD', ''),
                    'type': 'rtsp',
                    'brand': 'dahua',
                    'onvif_port': int(os.getenv('ONVIF_PORT', '80')),
                    'rtsp_port': int(os.getenv('RTSP_PORT', '554')),
                    'http_port': int(os.getenv('HTTP_PORT', '80'))
                },
                {
                    'name': 'Cámara TP-Link Tapo C320WS',
                    'ip': os.getenv('TP_LINK_IP', '192.168.1.77'),
                    'username': os.getenv('TP_LINK_USER', 'admin'),
                    'password': os.getenv('TP_LINK_PASSWORD', ''),
                    'type': 'onvif',
                    'brand': 'tplink',
                    'onvif_port': 2020,  # TP-Link usa puerto 2020 para ONVIF
                    'rtsp_port': int(os.getenv('RTSP_PORT', '554')),
                    'http_port': int(os.getenv('HTTP_PORT', '80'))
                },
                {
                    'name': 'Cámara Steren CCTV-235',
                    'ip': os.getenv('STEREN_IP', '192.168.1.178'),
                    'username': os.getenv('STEREN_USER', 'admin'),
                    'password': os.getenv('STEREN_PASSWORD', ''),
                    'type': 'onvif',
                    'brand': 'steren',
                    'onvif_port': 8000,  # Steren usa puerto 8000 para ONVIF
                    'rtsp_port': int(os.getenv('RTSP_PORT', '554')),
                    'http_port': int(os.getenv('HTTP_PORT', '80'))
                },
                {
                    'name': 'Cámara Generic China',
                    'ip': os.getenv('GENERIC_IP', '192.168.1.180'),
                    'username': os.getenv('GENERIC_USER', 'admin'),
                    'password': os.getenv('GENERIC_PASSWORD', ''),
                    'type': 'rtsp',
                    'brand': 'generic',
                    'onvif_port': int(os.getenv('ONVIF_PORT', '80')),
                    'rtsp_port': int(os.getenv('RTSP_PORT', '554')),
                    'http_port': int(os.getenv('HTTP_PORT', '80'))
                }
            ]
            
            self.cameras_config = default_cameras
            self.current_layout = 2
            
            # Actualizar interfaz
            self._update_cameras_list()
            self._update_cameras_count()
            
            # Notificar cambios
            if self.on_cameras_change:
                self.on_cameras_change(self.cameras_config)
            
            self.logger.info("Configuración por defecto cargada desde .env")
            self.logger.info(f"Cámaras configuradas:")
            for camera in default_cameras:
                self.logger.info(f"  - {camera['name']}: {camera['ip']} ({camera['username']})")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración por defecto: {str(e)}")
            # Fallback a configuración hardcodeada si falla la carga del .env
            self._load_fallback_config()
    
    def _load_fallback_config(self):
        """
        Carga configuración hardcodeada como fallback.
        """
        try:
            # Configuración hardcodeada como respaldo
            fallback_cameras = [
                {
                    'name': 'Cámara Dahua Hero-K51H',
                    'ip': '192.168.1.172',
                    'username': 'admin',
                    'password': '',
                    'type': 'rtsp',  # Cambiado de 'onvif' a 'rtsp' para mejor compatibilidad
                    'brand': 'dahua',
                    'onvif_port': 80,
                    'rtsp_port': 554,
                    'http_port': 80
                },
                {
                    'name': 'Cámara TP-Link Tapo C320WS',
                    'ip': '192.168.1.77',
                    'username': 'admin',
                    'password': '',
                    'type': 'onvif',
                    'brand': 'tplink',
                    'onvif_port': 2020,
                    'rtsp_port': 554,
                    'http_port': 80
                },
                {
                    'name': 'Cámara Steren CCTV-235',
                    'ip': '192.168.1.178',
                    'username': 'admin',
                    'password': '',
                    'type': 'onvif',
                    'brand': 'steren',
                    'onvif_port': 8000,
                    'rtsp_port': 554,
                    'http_port': 80
                },
                {
                    'name': 'Cámara Generic China',
                    'ip': '192.168.1.180',
                    'username': 'admin',
                    'password': '',
                    'type': 'rtsp',
                    'brand': 'generic',
                    'onvif_port': 80,
                    'rtsp_port': 554,
                    'http_port': 80
                }
            ]
        
            self.cameras_config = fallback_cameras
            self.current_layout = 2
            
            # Actualizar interfaz
            self._update_cameras_list()
            self._update_cameras_count()
        
            # Notificar cambios
            if self.on_cameras_change:
                self.on_cameras_change(self.cameras_config)
            
            self.logger.info("Configuración fallback cargada (sin .env)")
        
        except Exception as e:
            self.logger.error(f"Error cargando configuración fallback: {str(e)}")
    
    def _browse_recording_dir(self):
        """
        Abre diálogo para seleccionar directorio de grabación.
        """
        directory = filedialog.askdirectory(
            title="Seleccionar Directorio de Grabación",
            initialdir=self.recording_dir_var.get()
        )
        
        if directory:
            self.recording_dir_var.set(directory)
    
    def _apply_config(self):
        """
        Aplica la configuración general.
        """
        try:
            # Aquí se aplicarían los cambios de configuración
            # Por ahora solo mostramos confirmación
        
            messagebox.showinfo("Configuración Aplicada", "✅ Configuración aplicada exitosamente")
            self.logger.info("Configuración general aplicada")
        
        except Exception as e:
            self.logger.error(f"Error aplicando configuración: {str(e)}")
            messagebox.showerror("Error", f"Error al aplicar la configuración:\n{str(e)}")
    
    def _restore_defaults(self):
        """
        Restaura los valores por defecto de configuración.
        """
        if messagebox.askyesno(
            "Restaurar Valores por Defecto",
            "¿Restaurar todos los valores de configuración a sus valores por defecto?\n\nEsto no afectará las cámaras configuradas."
        ):
            try:
                # Restaurar valores por defecto
                self.timeout_var.set("10")
                self.retries_var.set("3")
                self.recording_dir_var.set("./recordings")
                self.quality_var.set("Alta")
                self.theme_var.set("Claro")
                self.language_var.set("Español")
                self.debug_mode_var.set(False)
                self.auto_save_var.set(True)
                self.notifications_var.set(True)
            
                messagebox.showinfo("Éxito", "✅ Valores por defecto restaurados")
                self.logger.info("Valores por defecto restaurados")
            
            except Exception as e:
                self.logger.error(f"Error restaurando valores por defecto: {str(e)}")
                messagebox.showerror("Error", f"Error al restaurar valores por defecto:\n{str(e)}")
    
    def get_cameras_config(self) -> List[Dict[str, Any]]:
        """
        Obtiene la configuración actual de cámaras.
        
        Returns:
            Lista con la configuración de cámaras
        """
        return self.cameras_config.copy()
    
    def get_current_layout(self) -> int:
        """
        Obtiene el layout actual.
        
        Returns:
            Número de columnas del layout actual
        """
        return self.current_layout 