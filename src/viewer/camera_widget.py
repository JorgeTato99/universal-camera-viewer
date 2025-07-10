"""
Widget individual para mostrar el stream de una cámara en tiempo real.
Incluye controles básicos y información de estado.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import logging
from typing import Optional, Dict, Any, Callable
import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.connections.base_connection import BaseConnection, ConnectionFactory
from src.connections.rtsp_connection import RTSPConnection
from src.connections.amcrest_connection import AmcrestConnection
from src.connections.onvif_connection import ONVIFConnection

# cspell:disable
class CameraWidget:
    """
    Widget para mostrar el stream de una cámara individual.
    Maneja la conexión, visualización y controles básicos.
    """
    
    def __init__(self, parent: tk.Widget, camera_config: Dict[str, Any], on_status_change: Optional[Callable] = None):
        """
        Inicializa el widget de cámara.
        
        Args:
            parent: Widget padre donde se insertará el widget
            camera_config: Configuración de la cámara (IP, credenciales, etc.)
            on_status_change: Callback cuando cambia el estado de la cámara
        """
        self.parent = parent
        self.camera_config = camera_config
        self.on_status_change = on_status_change
        self.connection: Optional[BaseConnection] = None
        self.is_streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        self.current_frame = None
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        self.connection_start_time = None
        self.bytes_received = 0
        self.last_frame_time = time.time()
        
        # Configurar logging
        self.logger = logging.getLogger(f"CameraWidget_{camera_config.get('name', 'Unknown')}")
        
        # Crear interfaz
        self._create_ui()
        
        # Estado inicial
        self._update_status("Desconectado", "🔴")
        self._clear_video_canvas("initial")
    
    def _create_ui(self):
        """
        Crea la interfaz gráfica del widget de cámara.
        """
        # Frame principal del widget con estilo mejorado
        camera_name = self.camera_config.get('name', 'Sin nombre')
        camera_brand = self.camera_config.get('brand', 'generic').upper()
        
        self.main_frame = ttk.LabelFrame(
            self.parent, 
            text=f"📹 {camera_name} ({camera_brand})"
        )
        self.main_frame.grid(sticky="nsew")
        
        # Configurar expansión del frame principal
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Frame superior con información y controles
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        # Panel de información (lado izquierdo)
        info_left = ttk.Frame(self.info_frame)
        info_left.grid(row=0, column=0, sticky="w")
        
        # Información básica con iconos
        self.ip_label = ttk.Label(
            info_left, 
            text=f"🌐 {self.camera_config.get('ip', 'N/A')}",
            font=("Arial", 9)
        )
        self.ip_label.grid(row=0, column=0, sticky="w", padx=2)
        
        self.status_label = ttk.Label(
            info_left, 
            text="🔴 Desconectado",
            font=("Arial", 9, "bold")
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=10)
        
        # Métricas en tiempo real
        metrics_frame = ttk.Frame(info_left)
        metrics_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        
        self.fps_label = ttk.Label(
            metrics_frame, 
            text="📊 0.0 FPS",
            font=("Arial", 8)
        )
        self.fps_label.grid(row=0, column=0, sticky="w", padx=2)
        
        self.latency_label = ttk.Label(
            metrics_frame, 
            text="⏱️ 0ms",
            font=("Arial", 8)
        )
        self.latency_label.grid(row=0, column=1, sticky="w", padx=5)
        
        self.uptime_label = ttk.Label(
            metrics_frame, 
            text="🕐 00:00:00",
            font=("Arial", 8)
        )
        self.uptime_label.grid(row=0, column=2, sticky="w", padx=5)
        
        self.quality_label = ttk.Label(
            metrics_frame, 
            text="📺 N/A",
            font=("Arial", 8)
        )
        self.quality_label.grid(row=0, column=3, sticky="w", padx=5)
        
        # Panel de controles (lado derecho)
        controls_frame = ttk.Frame(self.info_frame)
        controls_frame.grid(row=0, column=1, sticky="e", padx=5)
        
        # Botones con iconos y estilos
        self.connect_btn = ttk.Button(
            controls_frame, 
            text="🔗 Conectar", 
            command=self._toggle_connection,
            width=12
        )
        self.connect_btn.grid(row=0, column=0, padx=2)
        self._add_tooltip(self.connect_btn, "Conectar/desconectar cámara")
        
        self.snapshot_btn = ttk.Button(
            controls_frame, 
            text="📸 Capturar", 
            command=self._take_snapshot,
            state=tk.DISABLED,
            width=12
        )
        self.snapshot_btn.grid(row=0, column=1, padx=2)
        self._add_tooltip(self.snapshot_btn, "Capturar snapshot HD")
        
        self.settings_btn = ttk.Button(
            controls_frame, 
            text="⚙️ Config", 
            command=self._show_settings,
            width=10
        )
        self.settings_btn.grid(row=0, column=2, padx=2)
        self._add_tooltip(self.settings_btn, "Configuración de cámara")
        
        # Botones adicionales en segunda fila
        controls_frame2 = ttk.Frame(self.info_frame)
        controls_frame2.grid(row=1, column=1, sticky="e", padx=5, pady=2)
        
        self.refresh_btn = ttk.Button(
            controls_frame2, 
            text="🔄 Refrescar", 
            command=self._refresh_connection,
            width=12
        )
        self.refresh_btn.grid(row=0, column=0, padx=2)
        self._add_tooltip(self.refresh_btn, "Refrescar conexión")
        
        self.info_btn = ttk.Button(
            controls_frame2, 
            text="ℹ️ Info", 
            command=self._show_camera_info,
            width=10
        )
        self.info_btn.grid(row=0, column=1, padx=2)
        self._add_tooltip(self.info_btn, "Información detallada")
        
        # Separador visual
        ttk.Separator(self.main_frame, orient=tk.HORIZONTAL).grid(
            row=1, column=0, sticky="ew", padx=5, pady=2
        )
        
        # Frame para el video con borde mejorado
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas para mostrar el video con mejor estilo
        self.video_canvas = tk.Canvas(
            self.video_frame, 
            width=320, 
            height=240, 
            bg='#2c3e50',
            highlightthickness=2,
            highlightbackground="#34495e",
            relief=tk.FLAT
        )
        self.video_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Bind eventos del canvas
        self.video_canvas.bind("<Button-1>", self._on_canvas_click)
        self.video_canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        
        # Barra de estado inferior
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        # Indicador de estado de conexión
        self.connection_indicator = ttk.Label(
            self.status_frame,
            text="⚪",
            font=("Arial", 12)
        )
        self.connection_indicator.grid(row=0, column=0, padx=2)
        
        # URL de conexión (censurada)
        self.url_label = ttk.Label(
            self.status_frame, 
            text="🔗 No conectado",
            font=("Courier", 8),
            foreground="#7f8c8d"
        )
        self.url_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Indicador de calidad de señal
        self.signal_indicator = ttk.Label(
            self.status_frame,
            text="📶",
            font=("Arial", 10)
        )
        self.signal_indicator.grid(row=0, column=2, padx=2)
    
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
    
    def _on_canvas_click(self, event):
        """Maneja click simple en el canvas."""
        if self.is_streaming:
            self._take_snapshot()
    
    def _on_canvas_double_click(self, event):
        """Maneja doble click en el canvas."""
        self._show_fullscreen()
    
    def _show_fullscreen(self):
        """Muestra el video en pantalla completa (placeholder)."""
        messagebox.showinfo("Pantalla Completa", "Función de pantalla completa próximamente disponible")
    
    def _show_settings(self):
        """Muestra diálogo de configuración de la cámara."""
        settings_window = tk.Toplevel(self.main_frame)
        settings_window.title(f"⚙️ Configuración - {self.camera_config.get('name', 'Cámara')}")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Centrar ventana
        settings_window.transient(self.main_frame)
        settings_window.grab_set()
        
        # Información de configuración
        info_frame = ttk.LabelFrame(settings_window, text="📋 Información de Configuración")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        config_text = f"""
🎥 Nombre: {self.camera_config.get('name', 'N/A')}
🌐 IP: {self.camera_config.get('ip', 'N/A')}
👤 Usuario: {self.camera_config.get('username', 'N/A')}
🔧 Protocolo: {self.camera_config.get('type', 'N/A').upper()}
🏷️ Marca: {self.camera_config.get('brand', 'N/A').upper()}
🔌 Puerto ONVIF: {self.camera_config.get('onvif_port', 'N/A')}
📡 Puerto RTSP: {self.camera_config.get('rtsp_port', 'N/A')}
        """
        
        config_label = ttk.Label(info_frame, text=config_text, font=("Arial", 10), justify=tk.LEFT)
        config_label.pack(padx=10, pady=10)
        
        # Botón cerrar
        close_button = ttk.Button(settings_window, text="Cerrar", command=settings_window.destroy)
        close_button.pack(pady=10)
    
    def _show_camera_info(self):
        """Muestra información detallada de la cámara."""
        info_window = tk.Toplevel(self.main_frame)
        info_window.title(f"ℹ️ Información - {self.camera_config.get('name', 'Cámara')}")
        info_window.geometry("500x400")
        info_window.resizable(True, True)
        
        # Centrar ventana
        info_window.transient(self.main_frame)
        info_window.grab_set()
        
        # Notebook para organizar información
        info_notebook = ttk.Notebook(info_window)
        info_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de estado
        status_frame = ttk.Frame(info_notebook)
        info_notebook.add(status_frame, text="📊 Estado")
        
        status_info = f"""
ESTADO DE CONEXIÓN:
🔗 Estado: {'Conectado' if self.is_streaming else 'Desconectado'}
📊 FPS Actual: {self.current_fps:.1f}
⏱️ Tiempo Conectado: {self._get_uptime()}
📺 Resolución: {self._get_resolution()}
🔄 Frames Procesados: {self.fps_counter}

MÉTRICAS DE RED:
🌐 Latencia: {self._get_latency()}ms
📡 Calidad Señal: {self._get_signal_quality()}
💾 Datos Recibidos: {self._format_bytes(self.bytes_received)}
        """
        
        status_label = ttk.Label(status_frame, text=status_info, font=("Courier", 10), justify=tk.LEFT)
        status_label.pack(padx=10, pady=10)
        
        # Pestaña de configuración
        config_frame = ttk.Frame(info_notebook)
        info_notebook.add(config_frame, text="⚙️ Configuración")
        
        config_info = f"""
CONFIGURACIÓN DE CÁMARA:
📹 Nombre: {self.camera_config.get('name', 'N/A')}
🌐 Dirección IP: {self.camera_config.get('ip', 'N/A')}
👤 Usuario: {self.camera_config.get('username', 'N/A')}
🔒 Contraseña: {'***' if self.camera_config.get('password') else 'No configurada'}
🔧 Protocolo: {self.camera_config.get('type', 'N/A').upper()}
🏷️ Marca: {self.camera_config.get('brand', 'N/A').upper()}
🔌 Puerto ONVIF: {self.camera_config.get('onvif_port', 'N/A')}
📡 Puerto RTSP: {self.camera_config.get('rtsp_port', 'N/A')}

URL DE CONEXIÓN:
{self._get_connection_url()}
        """
        
        config_label = ttk.Label(config_frame, text=config_info, font=("Courier", 9), justify=tk.LEFT)
        config_label.pack(padx=10, pady=10)
        
        # Botón cerrar
        close_button = ttk.Button(info_window, text="Cerrar", command=info_window.destroy)
        close_button.pack(pady=10)
    
    def _refresh_connection(self):
        """Refresca la conexión de la cámara."""
        if self.is_streaming:
            self._disconnect()
            # Pequeña pausa antes de reconectar
            self.main_frame.after(1000, self._connect)
        else:
            self._connect()
    
    def _get_uptime(self) -> str:
        """Obtiene el tiempo de conexión formateado."""
        if not self.connection_start_time:
            return "00:00:00"
        
        uptime_seconds = int(time.time() - self.connection_start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _get_resolution(self) -> str:
        """Obtiene la resolución actual del video."""
        if self.current_frame is not None:
            height, width = self.current_frame.shape[:2]
            return f"{width}x{height}"
        return "N/A"
    
    def _get_latency(self) -> int:
        """Calcula la latencia aproximada."""
        if self.is_streaming and self.last_frame_time:
            return int((time.time() - self.last_frame_time) * 1000)
        return 0
    
    def _get_signal_quality(self) -> str:
        """Determina la calidad de la señal basada en FPS."""
        if self.current_fps >= 15:
            return "Excelente"
        elif self.current_fps >= 10:
            return "Buena"
        elif self.current_fps >= 5:
            return "Regular"
        elif self.current_fps > 0:
            return "Pobre"
        else:
            return "Sin señal"
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Formatea bytes en unidades legibles."""
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.1f} KB"
        elif bytes_count < 1024 * 1024 * 1024:
            return f"{bytes_count / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_count / (1024 * 1024 * 1024):.1f} GB"
    
    def _toggle_connection(self):
        """
        Alterna entre conectar y desconectar la cámara.
        """
        if self.is_streaming:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """
        Establece conexión con la cámara y comienza el streaming.
        """
        try:
            self.logger.info("Iniciando conexión con la cámara")
            self._update_status("Conectando...", "🟡")
            self._notify_status_change("connecting")
            
            # Crear conexión usando ConnectionFactory
            connection_type = self.camera_config.get('type', 'onvif')  # ONVIF por defecto
            camera_brand = self.camera_config.get('brand', 'dahua')  # Dahua por defecto
            
            # Crear ConfigurationManager dinámico
            from src.utils.config import ConfigurationManager
            
            # Crear config manager temporal con datos de la cámara
            temp_config = ConfigurationManager()
            
            # Configurar según la marca
            if camera_brand.lower() == 'tplink':
                temp_config.tplink_ip = self.camera_config['ip']
                temp_config.tplink_user = self.camera_config.get('username', 'admin')
                temp_config.tplink_password = self.camera_config.get('password', '')
                temp_config.onvif_port = self.camera_config.get('onvif_port', 2020)
            else:  # Dahua por defecto
                temp_config.camera_ip = self.camera_config['ip']
                temp_config.camera_user = self.camera_config.get('username', 'admin')
                temp_config.camera_password = self.camera_config.get('password', '')
                temp_config.onvif_port = self.camera_config.get('onvif_port', 80)
            
            # Usar ConnectionFactory para crear la conexión
            self.connection = ConnectionFactory.create_connection(
                connection_type=connection_type,
                config_manager=temp_config,
                camera_brand=camera_brand
            )
            
            # Intentar conectar
            if self.connection.connect():
                self.is_streaming = True
                self.connection_start_time = time.time()
                self._update_status("Conectado", "🟢")
                self._update_connection_url()
                self._notify_status_change("connected")
                
                # Actualizar controles
                self.connect_btn.config(text="🔌 Desconectar")
                self.snapshot_btn.config(state=tk.NORMAL)
                
                # Iniciar thread de streaming
                self.stream_thread = threading.Thread(target=self._stream_worker, daemon=True)
                self.stream_thread.start()
                
                self.logger.info("Conexión establecida exitosamente")
            else:
                self._update_status("Error de conexión", "🔴")
                self._update_connection_url()
                self._clear_video_canvas("error")
                self._notify_status_change("error")
                messagebox.showerror("Error", "No se pudo conectar a la cámara")
                
        except Exception as e:
            self.logger.error(f"Error al conectar: {str(e)}")
            self._update_status("Error", "🔴")
            self._clear_video_canvas("error")
            self._notify_status_change("error")
            messagebox.showerror("Error de Conexión", f"Error al conectar:\n{str(e)}")
    
    def _notify_status_change(self, status: str):
        """
        Notifica cambio de estado al callback padre.
        
        Args:
            status: Nuevo estado de la cámara
        """
        if self.on_status_change:
            try:
                camera_name = self.camera_config.get('name', 'Cámara')
                self.on_status_change(camera_name, status)
            except Exception as e:
                self.logger.error(f"Error notificando cambio de estado: {e}")
    
    def is_connected(self) -> bool:
        """
        Verifica si la cámara está conectada.
        
        Returns:
            True si está conectada, False en caso contrario
        """
        return self.is_streaming and self.connection is not None
    
    def get_fps(self) -> float:
        """
        Obtiene el FPS actual de la cámara.
        
        Returns:
            FPS actual
        """
        return self.current_fps
    
    def _stream_worker(self):
        """
        Worker thread para el streaming de video.
        """
        self.logger.info("Iniciando worker de streaming")
        
        while self.is_streaming and self.connection:
            try:
                # Obtener frame
                frame = self.connection.get_frame()
                
                if frame is not None:
                    self.current_frame = frame
                    self.last_frame_time = time.time()
                    
                    # Actualizar contador de bytes (estimado)
                    self.bytes_received += frame.nbytes if hasattr(frame, 'nbytes') else len(frame.tobytes())
                    
                    # Mostrar frame en el canvas
                    self._display_frame(frame)
                    
                    # Actualizar FPS
                    self._update_fps()
                    
                    # Actualizar métricas cada 30 frames
                    if self.fps_counter % 30 == 0:
                        self._update_metrics_display()
                else:
                    # Si no hay frame, pequeña pausa para evitar uso excesivo de CPU
                    time.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(f"Error en streaming: {str(e)}")
                if self.is_streaming:  # Solo mostrar error si aún deberíamos estar streaming
                    self._update_status("Error de stream", "🔴")
                    self._clear_video_canvas("stream_error")
                break
        
        self.logger.info("Worker de streaming finalizado")
    
    def _display_frame(self, frame):
        """
        Muestra un frame en el canvas de video.
        
        Args:
            frame: Frame de OpenCV a mostrar
        """
        try:
            # Obtener dimensiones del canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            # Si el canvas aún no tiene dimensiones, usar valores por defecto
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 320
                canvas_height = 240
            
            # Redimensionar frame manteniendo aspecto
            frame_height, frame_width = frame.shape[:2]
            
            # Calcular escala manteniendo aspecto
            scale_w = canvas_width / frame_width
            scale_h = canvas_height / frame_height
            scale = min(scale_w, scale_h)
            
            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)
            
            # Redimensionar frame
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # Convertir de BGR a RGB
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            
            # Convertir a PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convertir a PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Calcular posición centrada
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            # Mostrar en canvas (usar after para thread safety)
            self.video_canvas.after(0, lambda: self._update_canvas_image(photo, x, y))
            
        except Exception as e:
            self.logger.error(f"Error mostrando frame: {str(e)}")
    
    def _update_canvas_image(self, photo, x, y):
        """
        Actualiza la imagen en el canvas (thread-safe).
        
        Args:
            photo: PhotoImage a mostrar
            x, y: Posición donde mostrar la imagen
        """
        try:
            # Limpiar canvas
            self.video_canvas.delete("all")
            
            # Mostrar nueva imagen
            self.video_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            
            # Mantener referencia para evitar garbage collection
            self.video_canvas.image = photo
            
        except Exception as e:
            self.logger.error(f"Error actualizando canvas: {str(e)}")
    
    def _update_fps(self):
        """
        Actualiza el contador de FPS.
        """
        self.fps_counter += 1
        
        # Calcular FPS cada segundo
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
            
            # Actualizar label de FPS
            self.fps_label.after(0, lambda: self.fps_label.config(text=f"📊 {self.current_fps:.1f} FPS"))
    
    def _update_metrics_display(self):
        """
        Actualiza la visualización de métricas en tiempo real.
        """
        try:
            # Actualizar latencia
            latency = self._get_latency()
            self.latency_label.after(0, lambda: self.latency_label.config(text=f"⏱️ {latency}ms"))
            
            # Actualizar tiempo de conexión
            uptime = self._get_uptime()
            self.uptime_label.after(0, lambda: self.uptime_label.config(text=f"🕐 {uptime}"))
            
            # Actualizar calidad
            quality = self._get_signal_quality()
            self.quality_label.after(0, lambda: self.quality_label.config(text=f"📺 {quality}"))
            
            # Actualizar indicadores de estado
            self._update_status_indicators()
            
        except Exception as e:
            self.logger.error(f"Error actualizando métricas: {e}")
    
    def _update_status_indicators(self):
        """
        Actualiza los indicadores visuales de estado.
        """
        try:
            # Indicador de conexión
            if self.is_streaming:
                if self.current_fps > 10:
                    indicator = "🟢"  # Verde - excelente
                elif self.current_fps > 5:
                    indicator = "🟡"  # Amarillo - regular
                else:
                    indicator = "🔴"  # Rojo - pobre
            else:
                indicator = "⚪"  # Blanco - desconectado
            
            self.connection_indicator.after(0, lambda: self.connection_indicator.config(text=indicator))
            
            # Indicador de calidad de señal
            quality = self._get_signal_quality()
            if quality == "Excelente":
                signal = "📶"
            elif quality == "Buena":
                signal = "📶"
            elif quality == "Regular":
                signal = "📶"
            elif quality == "Pobre":
                signal = "📶"
            else:
                signal = "📵"
            
            self.signal_indicator.after(0, lambda: self.signal_indicator.config(text=signal))
            
        except Exception as e:
            self.logger.error(f"Error actualizando indicadores: {e}")
    
    def _update_status(self, status: str, icon: str):
        """
        Actualiza el estado mostrado en la interfaz.
        
        Args:
            status: Texto del estado
            icon: Icono del estado
        """
        self.status_label.config(text=f"{icon} {status}")
    
    def _censor_credentials(self, username: str, password: str) -> tuple:
        """
        Censura las credenciales para mostrar en la UI.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Tupla con (username_censurado, password_censurado)
        """
        # Censurar username (mostrar solo primeros 2 caracteres)
        if len(username) <= 2:
            censored_username = username
        else:
            censored_username = username[:2] + "*" * (len(username) - 2)
        
        # Censurar password completamente
        censored_password = "*" * len(password) if password else ""
        
        return censored_username, censored_password
    
    def _get_connection_url(self) -> str:
        """
        Obtiene la URL de conexión actual (censurada).
        
        Returns:
            URL de conexión censurada
        """
        if not self.connection or not self.is_streaming:
            return "No conectado"
        
        try:
            # Obtener información básica
            ip = self.camera_config.get('ip', 'N/A')
            username = self.camera_config.get('username', 'admin')
            password = self.camera_config.get('password', '')
            connection_type = self.camera_config.get('type', 'onvif')
            
            # Censurar credenciales
            censored_username, censored_password = self._censor_credentials(username, password)
            
            # Construir URL según el tipo de conexión
            if connection_type.lower() == 'rtsp':
                rtsp_port = self.camera_config.get('rtsp_port', 554)
                if hasattr(self.connection, 'stream_url') and self.connection.stream_url:
                    # Usar URL real pero censurar credenciales
                    url = self.connection.stream_url
                    # Reemplazar credenciales reales con censuradas
                    if username in url and password in url:
                        url = url.replace(f"{username}:{password}", f"{censored_username}:{censored_password}")
                    return url
                else:
                    return f"rtsp://{censored_username}:{censored_password}@{ip}:{rtsp_port}/stream"
            
            elif connection_type.lower() == 'onvif':
                onvif_port = self.camera_config.get('onvif_port', 80)
                if hasattr(self.connection, 'stream_url') and self.connection.stream_url:
                    # ONVIF devuelve URL RTSP, censurar credenciales
                    url = self.connection.stream_url
                    if username in url and password in url:
                        url = url.replace(f"{username}:{password}", f"{censored_username}:{censored_password}")
                    return f"ONVIF:{onvif_port} -> {url}"
                else:
                    return f"ONVIF://{ip}:{onvif_port} (configurando...)"
            
            elif connection_type.lower() == 'amcrest':
                http_port = self.camera_config.get('http_port', 80)
                return f"HTTP://{censored_username}:{censored_password}@{ip}:{http_port}/cgi-bin/"
            
            else:
                return f"{connection_type.upper()}://{ip} (configurando...)"
                
        except Exception as e:
            self.logger.error(f"Error obteniendo URL de conexión: {str(e)}")
            return "Error obteniendo URL"
    
    def _update_connection_url(self):
        """
        Actualiza la URL de conexión mostrada en la interfaz.
        """
        url = self._get_connection_url()
        self.url_label.config(text=f"🔗 {url}")
    
    def _clear_video_canvas(self, state: str = "initial"):
        """
        Limpia el canvas de video y muestra un mensaje según el estado.
        
        Args:
            state: Estado actual (initial, error, disconnected, stream_error)
        """
        try:
            # Limpiar canvas
            self.video_canvas.delete("all")
            
            # Configurar mensaje y color según el estado
            if state == "initial":
                message = "🎥 Visor Universal de Cámaras\n\n📹 Presiona 'Conectar' para iniciar\n\n💡 Click: Capturar\n💡 Doble-click: Pantalla completa"
                color = "#ecf0f1"
                bg_color = "#2c3e50"
            elif state == "error":
                message = "❌ Error de Conexión\n\n🔧 Verifica:\n• Dirección IP\n• Credenciales\n• Red\n\n🔄 Presiona 'Refrescar' para reintentar"
                color = "#e74c3c"
                bg_color = "#2c3e50"
            elif state == "disconnected":
                message = "🔌 Desconectado\n\n✅ Desconexión exitosa\n\n🔗 Presiona 'Conectar' para reconectar"
                color = "#f39c12"
                bg_color = "#2c3e50"
            elif state == "stream_error":
                message = "📡 Error de Stream\n\n⚠️ Problema en la transmisión\n\n🔄 Reconectando automáticamente..."
                color = "#e67e22"
                bg_color = "#2c3e50"
            else:
                message = "📹 Cámara Lista\n\nEsperando conexión..."
                color = "#95a5a6"
                bg_color = "#2c3e50"
            
            # Cambiar color de fondo del canvas
            self.video_canvas.config(bg=bg_color)
            
            # Obtener dimensiones del canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 320
                canvas_height = 240
            
            # Crear texto centrado
            self.video_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text=message,
                fill=color,
                font=("Arial", 11, "bold"),
                justify=tk.CENTER
            )
            
            # Agregar marca de agua en la esquina
            brand_text = f"{self.camera_config.get('brand', 'GENERIC').upper()}"
            self.video_canvas.create_text(
                canvas_width - 10,
                canvas_height - 10,
                text=brand_text,
                fill="#7f8c8d",
                font=("Arial", 8),
                anchor=tk.SE
            )
            
        except Exception as e:
            self.logger.error(f"Error limpiando canvas: {str(e)}")
    
    def _take_snapshot(self):
        """
        Captura un snapshot de la cámara.
        """
        if not self.is_streaming or not self.connection:
            messagebox.showwarning("Advertencia", "La cámara debe estar conectada para capturar snapshots")
            return
        
        try:
            # Usar el frame actual si está disponible
            if self.current_frame is not None:
                # Generar nombre de archivo con timestamp
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                camera_name = self.camera_config.get('name', 'camera').replace(' ', '_')
                filename = f"snapshot_{camera_name}_{timestamp}.jpg"
                
                # Guardar imagen
                cv2.imwrite(filename, self.current_frame)
                
                # Mostrar confirmación
                messagebox.showinfo(
                    "📸 Snapshot Capturado", 
                    f"✅ Snapshot guardado exitosamente:\n\n📁 {filename}\n\n📺 Resolución: {self._get_resolution()}"
                )
                
                self.logger.info(f"Snapshot capturado: {filename}")
            else:
                # Intentar capturar directamente de la conexión
                if hasattr(self.connection, 'capture_snapshot'):
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    camera_name = self.camera_config.get('name', 'camera').replace(' ', '_')
                    filename = f"snapshot_{camera_name}_{timestamp}.jpg"
                    
                    if self.connection.capture_snapshot(filename):
                        messagebox.showinfo("📸 Snapshot Capturado", f"✅ Snapshot guardado: {filename}")
                        self.logger.info(f"Snapshot capturado via conexión: {filename}")
                    else:
                        messagebox.showerror("Error", "❌ No se pudo capturar el snapshot")
                else:
                    messagebox.showerror("Error", "❌ No hay frame disponible para capturar")
                    
        except Exception as e:
            self.logger.error(f"Error capturando snapshot: {str(e)}")
            messagebox.showerror("Error", f"❌ Error al capturar snapshot:\n{str(e)}")
    
    def connect(self):
        """Método público para conectar la cámara."""
        if not self.is_streaming:
            self._connect()
    
    def disconnect(self):
        """Método público para desconectar la cámara."""
        if self.is_streaming:
            self._disconnect()
    
    def refresh(self):
        """Método público para refrescar la conexión."""
        self._refresh_connection()
    
    def capture_snapshot(self):
        """Método público para capturar snapshot."""
        self._take_snapshot()
    
    def cleanup(self):
        """
        Limpia recursos del widget.
        """
        try:
            self.logger.info("Limpiando recursos del widget de cámara")
            
            # Detener streaming
            if self.is_streaming:
                self._disconnect()
            
            # Limpiar canvas
            if hasattr(self, 'video_canvas'):
                self.video_canvas.delete("all")
            
            # Limpiar frame principal
            if hasattr(self, 'main_frame'):
                self.main_frame.destroy()
            
            self.logger.info("Recursos del widget limpiados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error limpiando recursos del widget: {str(e)}")
    
    def grid(self, **kwargs):
        """Método para posicionar el widget usando grid."""
        if hasattr(self, 'main_frame'):
            self.main_frame.grid(**kwargs)
    
    def pack(self, **kwargs):
        """Método para posicionar el widget usando pack."""
        if hasattr(self, 'main_frame'):
            self.main_frame.pack(**kwargs)
    
    def _disconnect(self):
        """
        Desconecta la cámara y detiene el streaming.
        """
        try:
            self.logger.info("Desconectando cámara")
            self.is_streaming = False
            self.connection_start_time = None
            
            # Esperar a que termine el thread
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=2)
            
            # Desconectar la conexión
            if self.connection:
                self.connection.disconnect()
                self.connection = None
            
            # Actualizar UI
            self._update_status("Desconectado", "🔴")
            self._update_connection_url()
            self._notify_status_change("disconnected")
            
            # Actualizar controles
            self.connect_btn.config(text="🔗 Conectar")
            self.snapshot_btn.config(state=tk.DISABLED)
            
            # Limpiar canvas con mensaje de desconexión manual
            self.video_canvas.after(100, lambda: self._clear_video_canvas("disconnected"))
            
            # Resetear métricas
            self.current_fps = 0
            self.fps_counter = 0
            self.bytes_received = 0
            self._update_metrics_display()
            
            self.logger.info("Desconexión completada")
            
        except Exception as e:
            self.logger.error(f"Error al desconectar: {str(e)}")
    
    def _stream_worker(self):
        """
        Worker thread para el streaming de video.
        """
        self.logger.info("Iniciando worker de streaming")
        
        while self.is_streaming and self.connection:
            try:
                # Obtener frame
                frame = self.connection.get_frame()
                
                if frame is not None:
                    self.current_frame = frame
                    self.last_frame_time = time.time()
                    
                    # Actualizar contador de bytes (estimado)
                    self.bytes_received += frame.nbytes if hasattr(frame, 'nbytes') else len(frame.tobytes())
                    
                    # Mostrar frame en el canvas
                    self._display_frame(frame)
                    
                    # Actualizar FPS
                    self._update_fps()
                    
                    # Actualizar métricas cada 30 frames
                    if self.fps_counter % 30 == 0:
                        self._update_metrics_display()
                else:
                    # Si no hay frame, pequeña pausa para evitar uso excesivo de CPU
                    time.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(f"Error en streaming: {str(e)}")
                if self.is_streaming:  # Solo mostrar error si aún deberíamos estar streaming
                    self._update_status("Error de stream", "🔴")
                    self._clear_video_canvas("stream_error")
                break
        
        self.logger.info("Worker de streaming finalizado")
    
    def _display_frame(self, frame):
        """
        Muestra un frame en el canvas de video.
        
        Args:
            frame: Frame de OpenCV a mostrar
        """
        try:
            # Obtener dimensiones del canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            # Si el canvas aún no tiene dimensiones, usar valores por defecto
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 320
                canvas_height = 240
            
            # Redimensionar frame manteniendo aspecto
            frame_height, frame_width = frame.shape[:2]
            
            # Calcular escala manteniendo aspecto
            scale_w = canvas_width / frame_width
            scale_h = canvas_height / frame_height
            scale = min(scale_w, scale_h)
            
            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)
            
            # Redimensionar frame
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # Convertir de BGR a RGB
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            
            # Convertir a PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convertir a PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Calcular posición centrada
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            # Mostrar en canvas (usar after para thread safety)
            self.video_canvas.after(0, lambda: self._update_canvas_image(photo, x, y))
            
        except Exception as e:
            self.logger.error(f"Error mostrando frame: {str(e)}")
    
    def _update_canvas_image(self, photo, x, y):
        """
        Actualiza la imagen en el canvas (thread-safe).
        
        Args:
            photo: PhotoImage a mostrar
            x, y: Posición donde mostrar la imagen
        """
        try:
            # Limpiar canvas
            self.video_canvas.delete("all")
            
            # Mostrar nueva imagen
            self.video_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            
            # Mantener referencia para evitar garbage collection
            self.video_canvas.image = photo
            
        except Exception as e:
            self.logger.error(f"Error actualizando canvas: {str(e)}")
    
    def _update_fps(self):
        """
        Actualiza el contador de FPS.
        """
        self.fps_counter += 1
        
        # Calcular FPS cada segundo
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
            
            # Actualizar label de FPS
            self.fps_label.after(0, lambda: self.fps_label.config(text=f"📊 {self.current_fps:.1f} FPS"))
    
    def _update_metrics_display(self):
        """
        Actualiza la visualización de métricas en tiempo real.
        """
        try:
            # Actualizar latencia
            latency = self._get_latency()
            self.latency_label.after(0, lambda: self.latency_label.config(text=f"⏱️ {latency}ms"))
            
            # Actualizar tiempo de conexión
            uptime = self._get_uptime()
            self.uptime_label.after(0, lambda: self.uptime_label.config(text=f"🕐 {uptime}"))
            
            # Actualizar calidad
            quality = self._get_signal_quality()
            self.quality_label.after(0, lambda: self.quality_label.config(text=f"📺 {quality}"))
            
            # Actualizar indicadores de estado
            self._update_status_indicators()
            
        except Exception as e:
            self.logger.error(f"Error actualizando métricas: {e}")
    
    def _update_status_indicators(self):
        """
        Actualiza los indicadores visuales de estado.
        """
        try:
            # Indicador de conexión
            if self.is_streaming:
                if self.current_fps > 10:
                    indicator = "🟢"  # Verde - excelente
                elif self.current_fps > 5:
                    indicator = "🟡"  # Amarillo - regular
                else:
                    indicator = "🔴"  # Rojo - pobre
            else:
                indicator = "⚪"  # Blanco - desconectado
            
            self.connection_indicator.after(0, lambda: self.connection_indicator.config(text=indicator))
            
            # Indicador de calidad de señal
            quality = self._get_signal_quality()
            if quality == "Excelente":
                signal = "📶"
            elif quality == "Buena":
                signal = "📶"
            elif quality == "Regular":
                signal = "📶"
            elif quality == "Pobre":
                signal = "📶"
            else:
                signal = "📵"
            
            self.signal_indicator.after(0, lambda: self.signal_indicator.config(text=signal))
            
        except Exception as e:
            self.logger.error(f"Error actualizando indicadores: {e}")
    
    def _update_status(self, status: str, icon: str):
        """
        Actualiza el estado mostrado en la interfaz.
        
        Args:
            status: Texto del estado
            icon: Icono del estado
        """
        self.status_label.config(text=f"{icon} {status}")
    
    def _censor_credentials(self, username: str, password: str) -> tuple:
        """
        Censura las credenciales para mostrar en la UI.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Tupla con (username_censurado, password_censurado)
        """
        # Censurar username (mostrar solo primeros 2 caracteres)
        if len(username) <= 2:
            censored_username = username
        else:
            censored_username = username[:2] + "*" * (len(username) - 2)
        
        # Censurar password completamente
        censored_password = "*" * len(password) if password else ""
        
        return censored_username, censored_password
    
    def _get_connection_url(self) -> str:
        """
        Obtiene la URL de conexión actual (censurada).
        
        Returns:
            URL de conexión censurada
        """
        if not self.connection or not self.is_streaming:
            return "No conectado"
        
        try:
            # Obtener información básica
            ip = self.camera_config.get('ip', 'N/A')
            username = self.camera_config.get('username', 'admin')
            password = self.camera_config.get('password', '')
            connection_type = self.camera_config.get('type', 'onvif')
            
            # Censurar credenciales
            censored_username, censored_password = self._censor_credentials(username, password)
            
            # Construir URL según el tipo de conexión
            if connection_type.lower() == 'rtsp':
                rtsp_port = self.camera_config.get('rtsp_port', 554)
                if hasattr(self.connection, 'stream_url') and self.connection.stream_url:
                    # Usar URL real pero censurar credenciales
                    url = self.connection.stream_url
                    # Reemplazar credenciales reales con censuradas
                    if username in url and password in url:
                        url = url.replace(f"{username}:{password}", f"{censored_username}:{censored_password}")
                    return url
                else:
                    return f"rtsp://{censored_username}:{censored_password}@{ip}:{rtsp_port}/stream"
            
            elif connection_type.lower() == 'onvif':
                onvif_port = self.camera_config.get('onvif_port', 80)
                if hasattr(self.connection, 'stream_url') and self.connection.stream_url:
                    # ONVIF devuelve URL RTSP, censurar credenciales
                    url = self.connection.stream_url
                    if username in url and password in url:
                        url = url.replace(f"{username}:{password}", f"{censored_username}:{censored_password}")
                    return f"ONVIF:{onvif_port} -> {url}"
                else:
                    return f"ONVIF://{ip}:{onvif_port} (configurando...)"
            
            elif connection_type.lower() == 'amcrest':
                http_port = self.camera_config.get('http_port', 80)
                return f"HTTP://{censored_username}:{censored_password}@{ip}:{http_port}/cgi-bin/"
            
            else:
                return f"{connection_type.upper()}://{ip} (configurando...)"
                
        except Exception as e:
            self.logger.error(f"Error obteniendo URL de conexión: {str(e)}")
            return "Error obteniendo URL"
    
    def _update_connection_url(self):
        """
        Actualiza la URL de conexión mostrada en la interfaz.
        """
        url = self._get_connection_url()
        self.url_label.config(text=f"🔗 {url}")
    
    def _clear_video_canvas(self, state: str = "initial"):
        """
        Limpia el canvas de video y muestra un mensaje según el estado.
        
        Args:
            state: Estado actual (initial, error, disconnected, stream_error)
        """
        try:
            # Limpiar canvas
            self.video_canvas.delete("all")
            
            # Configurar mensaje y color según el estado
            if state == "initial":
                message = "🎥 Visor Universal de Cámaras\n\n📹 Presiona 'Conectar' para iniciar\n\n💡 Click: Capturar\n💡 Doble-click: Pantalla completa"
                color = "#ecf0f1"
                bg_color = "#2c3e50"
            elif state == "error":
                message = "❌ Error de Conexión\n\n🔧 Verifica:\n• Dirección IP\n• Credenciales\n• Red\n\n🔄 Presiona 'Refrescar' para reintentar"
                color = "#e74c3c"
                bg_color = "#2c3e50"
            elif state == "disconnected":
                message = "🔌 Desconectado\n\n✅ Desconexión exitosa\n\n🔗 Presiona 'Conectar' para reconectar"
                color = "#f39c12"
                bg_color = "#2c3e50"
            elif state == "stream_error":
                message = "📡 Error de Stream\n\n⚠️ Problema en la transmisión\n\n🔄 Reconectando automáticamente..."
                color = "#e67e22"
                bg_color = "#2c3e50"
            else:
                message = "📹 Cámara Lista\n\nEsperando conexión..."
                color = "#95a5a6"
                bg_color = "#2c3e50"
            
            # Cambiar color de fondo del canvas
            self.video_canvas.config(bg=bg_color)
            
            # Obtener dimensiones del canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 320
                canvas_height = 240
            
            # Crear texto centrado
            self.video_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text=message,
                fill=color,
                font=("Arial", 11, "bold"),
                justify=tk.CENTER
            )
            
            # Agregar marca de agua en la esquina
            brand_text = f"{self.camera_config.get('brand', 'GENERIC').upper()}"
            self.video_canvas.create_text(
                canvas_width - 10,
                canvas_height - 10,
                text=brand_text,
                fill="#7f8c8d",
                font=("Arial", 8),
                anchor=tk.SE
            )
            
        except Exception as e:
            self.logger.error(f"Error limpiando canvas: {str(e)}")
    
    def _take_snapshot(self):
        """
        Captura un snapshot de la cámara.
        """
        if not self.is_streaming or not self.connection:
            messagebox.showwarning("Advertencia", "La cámara debe estar conectada para capturar snapshots")
            return
        
        try:
            # Usar el frame actual si está disponible
            if self.current_frame is not None:
                # Generar nombre de archivo con timestamp
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                camera_name = self.camera_config.get('name', 'camera').replace(' ', '_')
                filename = f"snapshot_{camera_name}_{timestamp}.jpg"
                
                # Guardar imagen
                cv2.imwrite(filename, self.current_frame)
                
                # Mostrar confirmación
                messagebox.showinfo(
                    "📸 Snapshot Capturado", 
                    f"✅ Snapshot guardado exitosamente:\n\n📁 {filename}\n\n📺 Resolución: {self._get_resolution()}"
                )
                
                self.logger.info(f"Snapshot capturado: {filename}")
            else:
                # Intentar capturar directamente de la conexión
                if hasattr(self.connection, 'capture_snapshot'):
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    camera_name = self.camera_config.get('name', 'camera').replace(' ', '_')
                    filename = f"snapshot_{camera_name}_{timestamp}.jpg"
                    
                    if self.connection.capture_snapshot(filename):
                        messagebox.showinfo("📸 Snapshot Capturado", f"✅ Snapshot guardado: {filename}")
                        self.logger.info(f"Snapshot capturado via conexión: {filename}")
                    else:
                        messagebox.showerror("Error", "❌ No se pudo capturar el snapshot")
                else:
                    messagebox.showerror("Error", "❌ No hay frame disponible para capturar")
                    
        except Exception as e:
            self.logger.error(f"Error capturando snapshot: {str(e)}")
            messagebox.showerror("Error", f"❌ Error al capturar snapshot:\n{str(e)}")
    
    def connect(self):
        """Método público para conectar la cámara."""
        if not self.is_streaming:
            self._connect()
    
    def disconnect(self):
        """Método público para desconectar la cámara."""
        if self.is_streaming:
            self._disconnect()
    
    def refresh(self):
        """Método público para refrescar la conexión."""
        self._refresh_connection()
    
    def capture_snapshot(self):
        """Método público para capturar snapshot."""
        self._take_snapshot()
    
    def cleanup(self):
        """
        Limpia recursos del widget.
        """
        try:
            self.logger.info("Limpiando recursos del widget de cámara")
            
            # Detener streaming
            if self.is_streaming:
                self._disconnect()
            
            # Limpiar canvas
            if hasattr(self, 'video_canvas'):
                self.video_canvas.delete("all")
            
            # Limpiar frame principal
            if hasattr(self, 'main_frame'):
                self.main_frame.destroy()
            
            self.logger.info("Recursos del widget limpiados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error limpiando recursos del widget: {str(e)}")
    
    def grid(self, **kwargs):
        """Método para posicionar el widget usando grid."""
        if hasattr(self, 'main_frame'):
            self.main_frame.grid(**kwargs)
    
    def pack(self, **kwargs):
        """Método para posicionar el widget usando pack."""
        if hasattr(self, 'main_frame'):
            self.main_frame.pack(**kwargs) 