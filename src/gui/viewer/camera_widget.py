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
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.connections.base_connection import BaseConnection, ConnectionFactory
from src.connections.rtsp_connection import RTSPConnection
from src.connections.amcrest_connection import AmcrestConnection
from src.connections.onvif_connection import ONVIFConnection


class CameraWidget:
    """
    Widget para mostrar el stream de una cámara individual.
    Maneja la conexión, visualización y controles básicos.
    """
    
    def __init__(self, parent_frame: tk.Widget, camera_config: Dict[str, Any]):
        """
        Inicializa el widget de cámara.
        
        Args:
            parent_frame: Frame padre donde se insertará el widget
            camera_config: Configuración de la cámara (IP, credenciales, etc.)
        """
        self.parent_frame = parent_frame
        self.camera_config = camera_config
        self.connection: Optional[BaseConnection] = None
        self.is_streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        self.current_frame = None
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Configurar logging
        self.logger = logging.getLogger(f"CameraWidget_{camera_config.get('name', 'Unknown')}")
        
        # Crear interfaz
        self._create_ui()
        
        # Estado inicial
        self._update_status("Desconectado", "red")
    
    def _create_ui(self):
        """
        Crea la interfaz gráfica del widget de cámara.
        """
        # Frame principal del widget
        self.main_frame = ttk.LabelFrame(
            self.parent_frame, 
            text=f"Cámara: {self.camera_config.get('name', 'Sin nombre')}"
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame superior con información y controles
        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Información de la cámara
        info_left = ttk.Frame(self.info_frame)
        info_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.ip_label = ttk.Label(info_left, text=f"IP: {self.camera_config.get('ip', 'N/A')}")
        self.ip_label.pack(anchor=tk.W)
        
        self.status_label = ttk.Label(info_left, text="Estado: Desconectado")
        self.status_label.pack(anchor=tk.W)
        
        self.fps_label = ttk.Label(info_left, text="FPS: 0")
        self.fps_label.pack(anchor=tk.W)
        
        # Controles
        controls_frame = ttk.Frame(self.info_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        self.connect_btn = ttk.Button(
            controls_frame, 
            text="Conectar", 
            command=self._toggle_connection
        )
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        self.snapshot_btn = ttk.Button(
            controls_frame, 
            text="Snapshot", 
            command=self._take_snapshot,
            state=tk.DISABLED
        )
        self.snapshot_btn.pack(side=tk.LEFT, padx=2)
        
        self.record_btn = ttk.Button(
            controls_frame, 
            text="Grabar", 
            command=self._toggle_recording,
            state=tk.DISABLED
        )
        self.record_btn.pack(side=tk.LEFT, padx=2)
        
        # Frame para el video
        self.video_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=2)
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas para mostrar el video
        self.video_canvas = tk.Canvas(
            self.video_frame, 
            width=640, 
            height=480, 
            bg='black'
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Texto inicial en el canvas
        self.video_canvas.create_text(
            320, 240, 
            text="Stream no iniciado\nPresiona 'Conectar' para comenzar", 
            fill="white", 
            font=("Arial", 12),
            justify=tk.CENTER
        )
    
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
            self._update_status("Conectando...", "orange")
            
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
            
            # Configurar parámetros específicos según el tipo (si es necesario)
            # Las nuevas conexiones usan el config_manager automáticamente
            
            # Intentar conectar
            if self.connection.connect():
                self.is_streaming = True
                self._update_status("Conectado", "green")
                self.connect_btn.config(text="Desconectar")
                self.snapshot_btn.config(state=tk.NORMAL)
                self.record_btn.config(state=tk.NORMAL)
                
                # Iniciar thread de streaming
                self.stream_thread = threading.Thread(target=self._stream_worker, daemon=True)
                self.stream_thread.start()
                
                self.logger.info("Conexión establecida exitosamente")
            else:
                self._update_status("Error de conexión", "red")
                messagebox.showerror("Error", "No se pudo conectar a la cámara")
                
        except Exception as e:
            self.logger.error(f"Error al conectar: {str(e)}")
            self._update_status("Error", "red")
            messagebox.showerror("Error", f"Error al conectar:\n{str(e)}")
    
    def _disconnect(self):
        """
        Desconecta la cámara y detiene el streaming.
        """
        try:
            self.logger.info("Desconectando cámara")
            self.is_streaming = False
            
            # Esperar a que termine el thread
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=2)
            
            # Desconectar la conexión
            if self.connection:
                self.connection.disconnect()
                self.connection = None
            
            # Actualizar UI
            self._update_status("Desconectado", "red")
            self.connect_btn.config(text="Conectar")
            self.snapshot_btn.config(state=tk.DISABLED)
            self.record_btn.config(state=tk.DISABLED)
            
            # Limpiar canvas
            self._clear_video_canvas()
            
            self.logger.info("Desconexión completada")
            
        except Exception as e:
            self.logger.error(f"Error al desconectar: {str(e)}")
    
    def _stream_worker(self):
        """
        Worker thread que maneja el streaming de video.
        """
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        while self.is_streaming and self.connection:
            try:
                # Obtener frame
                frame = self.connection.get_frame()
                
                if frame is not None:
                    self.current_frame = frame
                    
                    # Actualizar FPS
                    self._update_fps()
                    
                    # Mostrar frame en la UI (thread-safe)
                    self.video_canvas.after(0, self._display_frame, frame)
                    
                else:
                    self.logger.warning("No se pudo obtener frame")
                    time.sleep(0.1)  # Evitar loop muy rápido
                    
            except Exception as e:
                self.logger.error(f"Error en streaming: {str(e)}")
                time.sleep(0.1)
        
        self.logger.info("Worker thread de streaming terminado")
    
    def _display_frame(self, frame):
        """
        Muestra un frame en el canvas de video.
        
        Args:
            frame: Frame de OpenCV (BGR)
        """
        try:
            # Convertir BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Redimensionar para ajustar al canvas
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calcular dimensiones manteniendo aspect ratio
                h, w = frame_rgb.shape[:2]
                aspect_ratio = w / h
                
                if canvas_width / canvas_height > aspect_ratio:
                    # Ajustar por altura
                    new_height = canvas_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    # Ajustar por ancho
                    new_width = canvas_width
                    new_height = int(new_width / aspect_ratio)
                
                # Redimensionar
                frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
                
                # Convertir a PIL Image y luego a PhotoImage
                pil_image = Image.fromarray(frame_resized)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Limpiar canvas y mostrar nueva imagen
                self.video_canvas.delete("all")
                self.video_canvas.create_image(
                    canvas_width // 2, 
                    canvas_height // 2, 
                    image=photo
                )
                
                # Mantener referencia para evitar garbage collection
                self.video_canvas.image = photo
                
        except Exception as e:
            self.logger.error(f"Error al mostrar frame: {str(e)}")
    
    def _update_fps(self):
        """
        Actualiza el contador de FPS.
        """
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
            
            # Actualizar label de FPS
            self.fps_label.after(0, lambda: self.fps_label.config(text=f"FPS: {self.current_fps}"))
    
    def _update_status(self, status: str, color: str):
        """
        Actualiza el estado mostrado en la UI.
        
        Args:
            status: Texto del estado
            color: Color del texto (red, green, orange, etc.)
        """
        self.status_label.config(text=f"Estado: {status}", foreground=color)
    
    def _clear_video_canvas(self):
        """
        Limpia el canvas de video y muestra mensaje por defecto.
        """
        self.video_canvas.delete("all")
        self.video_canvas.create_text(
            320, 240, 
            text="Stream no iniciado\nPresiona 'Conectar' para comenzar", 
            fill="white", 
            font=("Arial", 12),
            justify=tk.CENTER
        )
    
    def _take_snapshot(self):
        """
        Toma un snapshot de la cámara.
        """
        if not self.connection or not self.is_streaming:
            messagebox.showwarning("Advertencia", "No hay conexión activa")
            return
        
        try:
            timestamp = int(time.time())
            camera_name = self.camera_config.get('name', 'camera').replace(' ', '_')
            filename = f"snapshot_{camera_name}_{timestamp}.jpg"
            
            if self.connection.save_snapshot(filename):
                messagebox.showinfo("Éxito", f"Snapshot guardado como:\n{filename}")
                self.logger.info(f"Snapshot guardado: {filename}")
            else:
                messagebox.showerror("Error", "No se pudo guardar el snapshot")
                
        except Exception as e:
            self.logger.error(f"Error al tomar snapshot: {str(e)}")
            messagebox.showerror("Error", f"Error al tomar snapshot:\n{str(e)}")
    
    def _toggle_recording(self):
        """
        Alterna la grabación de video (placeholder por ahora).
        """
        # TODO: Implementar grabación de video
        messagebox.showinfo("Función", "Grabación de video - Próximamente")
    
    def cleanup(self):
        """
        Limpia recursos al cerrar el widget.
        """
        if self.is_streaming:
            self._disconnect() 