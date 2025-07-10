"""
Panel de progreso para el escaneo de puertos.
Muestra barra de progreso y estado actual con UX mejorada.
"""

import tkinter as tk
from tkinter import ttk
import time
from typing import Optional

# cspell:disable
class ScanProgressPanel:
    """
    Panel que muestra el progreso del escaneo de puertos con UX mejorada.
    
    Incluye barra de progreso, estado, estimación de tiempo y velocidad.
    """
    
    def __init__(self, parent_container: tk.Widget):
        """
        Inicializa el panel de progreso.
        
        Args:
            parent_container: Contenedor padre donde se colocará el panel
        """
        self.parent_container = parent_container
        
        # Variables de estado
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Listo para escanear")
        
        # Variables para UX mejorada
        self.speed_var = tk.StringVar(value="0 puertos/s")
        self.eta_var = tk.StringVar(value="--:--")
        self.current_port_var = tk.StringVar(value="")
        
        # Estado del escaneo y métricas
        self.scan_in_progress = False
        self.scan_start_time: Optional[float] = None
        self.last_update_time: Optional[float] = None
        self.ports_scanned = 0
        self.total_ports = 0
        
        # Animación
        self.animation_active = False
        self.animation_step = 0
        
        self._create_panel()
    
    def _create_panel(self):
        """Crea el panel de progreso con diseño mejorado."""
        # Frame de progreso con mejor diseño
        progress_frame = ttk.LabelFrame(self.parent_container, text="Progreso del Escaneo", padding=8)
        progress_frame.pack(fill=tk.X, padx=8, pady=3)
        
        # Fila 1: Estado principal y puerto actual
        status_row = ttk.Frame(progress_frame)
        status_row.pack(fill=tk.X, pady=(0, 5))
        
        # Estado principal
        self.status_label = ttk.Label(
            status_row, 
            textvariable=self.status_var,
            font=("Arial", 9, "bold")
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Puerto actual (lado derecho)
        self.current_port_label = ttk.Label(
            status_row,
            textvariable=self.current_port_var,
            font=("Arial", 8),
            foreground="#666666"
        )
        self.current_port_label.pack(side=tk.RIGHT)
        
        # Fila 2: Barra de progreso mejorada
        progress_row = ttk.Frame(progress_frame)
        progress_row.pack(fill=tk.X, pady=2)
        
        # Barra de progreso con estilo
        self.progress_bar = ttk.Progressbar(
            progress_row, 
            variable=self.progress_var, 
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Fila 3: Métricas de rendimiento
        metrics_row = ttk.Frame(progress_frame)
        metrics_row.pack(fill=tk.X, pady=(5, 0))
        
        # Velocidad
        speed_frame = ttk.Frame(metrics_row)
        speed_frame.pack(side=tk.LEFT)
        
        ttk.Label(speed_frame, text="⚡ Velocidad:", font=("Arial", 8)).pack(side=tk.LEFT)
        ttk.Label(speed_frame, textvariable=self.speed_var, font=("Arial", 8, "bold"), foreground="#1976d2").pack(side=tk.LEFT, padx=(3, 0))
        
        # Separador
        ttk.Separator(metrics_row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # Tiempo estimado
        eta_frame = ttk.Frame(metrics_row)
        eta_frame.pack(side=tk.LEFT)
        
        ttk.Label(eta_frame, text="⏱️ Tiempo restante:", font=("Arial", 8)).pack(side=tk.LEFT)
        ttk.Label(eta_frame, textvariable=self.eta_var, font=("Arial", 8, "bold"), foreground="#ff9800").pack(side=tk.LEFT, padx=(3, 0))
        
        # Indicador de actividad (lado derecho)
        self.activity_frame = ttk.Frame(metrics_row)
        self.activity_frame.pack(side=tk.RIGHT)
        
        self.activity_label = ttk.Label(
            self.activity_frame,
            text="⚪",
            font=("Arial", 12)
        )
        self.activity_label.pack()
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """
        Actualiza la barra de progreso con métricas mejoradas.
        
        Args:
            current: Progreso actual
            total: Total de elementos
            message: Mensaje de estado opcional
        """
        self.ports_scanned = current
        self.total_ports = total
        
        # Inicializar tiempo de inicio si es necesario
        if self.scan_start_time is None:
            self.scan_start_time = time.time()
        
        # Actualizar progreso
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        
        # Actualizar estado
        if message:
            status_text = f"{message}"
            self.current_port_var.set(f"({current}/{total})")
        else:
            status_text = f"Escaneando puertos..."
            self.current_port_var.set(f"Progreso: {current}/{total}")
        
        self.status_var.set(status_text)
        
        # Calcular y actualizar métricas
        self._update_metrics()
        
        # Iniciar animación si no está activa
        if not self.animation_active and current > 0:
            self._start_activity_animation()
    
    def _update_metrics(self):
        """Actualiza las métricas de velocidad y tiempo estimado."""
        if self.scan_start_time is None or self.ports_scanned == 0:
            return
        
        current_time = time.time()
        elapsed_time = current_time - self.scan_start_time
        
        # Calcular velocidad (puertos por segundo)
        if elapsed_time > 0:
            speed = self.ports_scanned / elapsed_time
            self.speed_var.set(f"{speed:.1f} puertos/s")
            
            # Calcular tiempo estimado restante
            if speed > 0 and self.total_ports > self.ports_scanned:
                remaining_ports = self.total_ports - self.ports_scanned
                eta_seconds = remaining_ports / speed
                
                if eta_seconds < 60:
                    eta_text = f"{eta_seconds:.0f}s"
                elif eta_seconds < 3600:
                    minutes = int(eta_seconds // 60)
                    seconds = int(eta_seconds % 60)
                    eta_text = f"{minutes}:{seconds:02d}"
                else:
                    hours = int(eta_seconds // 3600)
                    minutes = int((eta_seconds % 3600) // 60)
                    eta_text = f"{hours}h {minutes}m"
                
                self.eta_var.set(eta_text)
            else:
                self.eta_var.set("Calculando...")
        
        self.last_update_time = current_time
    
    def _start_activity_animation(self):
        """Inicia la animación del indicador de actividad."""
        if not self.animation_active:
            self.animation_active = True
            self._animate_activity()
    
    def _animate_activity(self):
        """Anima el indicador de actividad."""
        if not self.animation_active:
            return
        
        # Símbolos de animación
        symbols = ["⚪", "🔵", "🟢", "🟡", "🟠", "🔴"]
        
        # Actualizar símbolo
        symbol = symbols[self.animation_step % len(symbols)]
        self.activity_label.config(text=symbol)
        
        self.animation_step += 1
        
        # Programar siguiente frame
        if self.animation_active:
            self.parent_container.after(200, self._animate_activity)
    
    def _stop_activity_animation(self):
        """Detiene la animación del indicador de actividad."""
        self.animation_active = False
        self.activity_label.config(text="⚪")
    
    def set_status(self, status: str):
        """
        Establece el mensaje de estado con mejor formato.
        
        Args:
            status: Mensaje de estado
        """
        self.status_var.set(status)
        
        # Limpiar puerto actual si no hay escaneo activo
        if "detenido" in status.lower() or "completado" in status.lower():
            self.current_port_var.set("")
    
    def set_progress(self, progress: float):
        """
        Establece el progreso directamente.
        
        Args:
            progress: Progreso (0-100)
        """
        self.progress_var.set(progress)
    
    def reset_progress(self):
        """Reinicia la barra de progreso y métricas."""
        self.progress_var.set(0)
        self.status_var.set("Listo para escanear")
        self.current_port_var.set("")
        self.speed_var.set("0 puertos/s")
        self.eta_var.set("--:--")
        
        # Resetear métricas
        self.scan_start_time = None
        self.last_update_time = None
        self.ports_scanned = 0
        self.total_ports = 0
        
        # Detener animación
        self._stop_activity_animation()
    
    def set_scan_completed(self, summary: str):
        """
        Configura la UI para escaneo completado con métricas finales.
        
        Args:
            summary: Resumen del escaneo completado
        """
        self.progress_var.set(100)
        self.status_var.set("✅ " + summary)
        
        # Mostrar métricas finales
        if self.scan_start_time:
            total_time = time.time() - self.scan_start_time
            if total_time < 60:
                time_text = f"{total_time:.1f}s"
            else:
                minutes = int(total_time // 60)
                seconds = int(total_time % 60)
                time_text = f"{minutes}:{seconds:02d}"
            
            self.current_port_var.set(f"Completado en {time_text}")
            
            # Velocidad promedio final
            if total_time > 0 and self.total_ports > 0:
                avg_speed = self.total_ports / total_time
                self.speed_var.set(f"{avg_speed:.1f} puertos/s (promedio)")
        
        self.eta_var.set("Finalizado")
        
        # Detener animación y mostrar éxito
        self._stop_activity_animation()
        self.activity_label.config(text="✅")
    
    def set_scan_error(self, error_message: str):
        """
        Configura la UI para error en escaneo con indicador visual.
        
        Args:
            error_message: Mensaje de error
        """
        self.status_var.set(f"❌ Error: {error_message}")
        self.current_port_var.set("Escaneo interrumpido")
        self.eta_var.set("Error")
        
        # Detener animación y mostrar error
        self._stop_activity_animation()
        self.activity_label.config(text="❌")
    
    def set_scan_starting(self, target_ip: str, total_ports: int):
        """
        Configura la UI para inicio de escaneo.
        
        Args:
            target_ip: IP objetivo del escaneo
            total_ports: Número total de puertos a escanear
        """
        self.total_ports = total_ports
        self.scan_start_time = time.time()
        
        self.status_var.set(f"🔍 Iniciando escaneo en {target_ip}")
        self.current_port_var.set(f"0/{total_ports} puertos")
        self.speed_var.set("Iniciando...")
        self.eta_var.set("Calculando...")
        
        # Iniciar animación
        self._start_activity_animation()
    
    def set_scan_paused(self):
        """Configura la UI para escaneo pausado."""
        self.status_var.set("⏸️ Escaneo pausado")
        self.eta_var.set("Pausado")
        self._stop_activity_animation()
        self.activity_label.config(text="⏸️")
    
    def resume_scan(self):
        """Reanuda el escaneo desde pausa."""
        self.status_var.set("🔍 Reanudando escaneo...")
        self._start_activity_animation()
    
    def get_scan_metrics(self) -> dict:
        """
        Obtiene las métricas actuales del escaneo.
        
        Returns:
            Diccionario con métricas del escaneo
        """
        elapsed_time = 0
        if self.scan_start_time:
            elapsed_time = time.time() - self.scan_start_time
        
        return {
            "ports_scanned": self.ports_scanned,
            "total_ports": self.total_ports,
            "elapsed_time": elapsed_time,
            "progress_percentage": self.progress_var.get(),
            "current_speed": self.speed_var.get(),
            "estimated_time_remaining": self.eta_var.get()
        } 