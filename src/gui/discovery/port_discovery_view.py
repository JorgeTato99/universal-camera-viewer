"""
Vista refactorizada para descubrimiento de puertos.
Implementa arquitectura modular con componentes especializados.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional

# Importar componentes modulares
from .components.scan_config_panel import ScanConfigPanel
from .components.scan_progress_panel import ScanProgressPanel
from .components.scan_results_panel import ScanResultsPanel

# Importar clases de escaneo
from .scanning import PortScanner, PortResult, ScanResult

# cspell:disable
class PortDiscoveryView:
    """
    Vista de descubrimiento de puertos.
    """
    
    def __init__(self, parent_container: tk.Widget):
        """
        Inicializa la vista refactorizada.
        
        Args:
            parent_container: Contenedor padre donde se embebida la vista
        """
        self.parent_container = parent_container
        
        # Estado del escaneo
        self.scanner = PortScanner(timeout=3)
        self.current_scan_thread: Optional[threading.Thread] = None
        self.scan_results: Optional[ScanResult] = None
        
        # Componentes de UI
        self.config_panel: Optional[ScanConfigPanel] = None
        self.progress_panel: Optional[ScanProgressPanel] = None
        self.results_panel: Optional[ScanResultsPanel] = None
        
        # Crear la vista
        self._create_view()
        self._setup_callbacks()
    
    def _create_view(self):
        """Crea la vista principal usando componentes modulares."""
        # Frame principal de la vista
        self.main_frame = tk.Frame(self.parent_container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear componentes especializados
        self.config_panel = ScanConfigPanel(self.main_frame)
        self.progress_panel = ScanProgressPanel(self.main_frame)
        self.results_panel = ScanResultsPanel(self.main_frame)
    
    def _setup_callbacks(self):
        """Configura los callbacks entre componentes."""
        # Configurar callbacks entre componentes
        self.config_panel.set_mode_change_callback(self._on_mode_change)
        self.config_panel.set_config_change_callback(self._on_config_change)
        
        # Configurar callbacks de botones de control
        self.config_panel.set_scan_callbacks(
            start_callback=self._start_scan,
            stop_callback=self._stop_scan,
            clear_callback=self._clear_results
        )
    
    def _on_mode_change(self, mode: str):
        """
        Maneja el cambio de modo de escaneo.
        
        Args:
            mode: Nuevo modo de escaneo
        """
        # Actualizar panel de resultados para el nuevo modo
        if self.results_panel:
            self.results_panel.set_scan_mode(mode)
    
    def _on_config_change(self, config: dict):
        """
        Maneja cambios en la configuración.
        
        Args:
            config: Nueva configuración
        """
        # Aquí se puede agregar lógica adicional si es necesario
        # Por ejemplo, validaciones en tiempo real
        pass
    
    def _start_scan(self):
        """Inicia el escaneo de puertos."""
        # Validar configuración
        is_valid, error_msg = self.config_panel.validate_config()
        if not is_valid:
            messagebox.showerror("Error de Configuración", error_msg)
            return
        
        # Obtener configuración
        config = self.config_panel.get_config()
        
        # Configurar UI para escaneo
        self.config_panel.start_scan_mode(config["mode"])
        self.progress_panel.reset_progress()
        
        # Agregar mensaje inicial a la consola
        self.results_panel.add_to_console(f"Iniciando escaneo {config['mode']} en {config['ip']}", "INFO")
        self.results_panel.add_to_console(f"Configuración: Timeout={config['timeout']}s, Intensidad={config['intensity']}", "INFO")
        
        # Crear y configurar escáner
        username = config.get("username", "") if config["mode"] == "advanced" else ""
        password = config.get("password", "") if config["mode"] == "advanced" else ""
        
        self.scanner = PortScanner(username=username, password=password, timeout=int(config["timeout"]))
        
        # Configurar callbacks del escáner (solo los que existen)
        self.scanner.set_progress_callback(self._on_scan_progress)
        self.scanner.set_result_callback(self._on_scan_result)
        
        # Configurar intensidad si es modo avanzado
        if config["mode"] == "advanced":
            self.scanner.set_intensity_level(config["intensity"])
        
        # Iniciar escaneo en hilo separado
        scan_thread = threading.Thread(
            target=self._run_scan_thread,
            args=(config,),
            daemon=True
        )
        scan_thread.start()
    
    def _stop_scan(self):
        """Detiene el escaneo actual."""
        if self.scanner:
            self.scanner.stop_scan()
            self.results_panel.add_to_console("Escaneo detenido por el usuario", "WARNING")
        
        self.config_panel.stop_scan_mode()
        self.progress_panel.set_status("Escaneo detenido")
    
    def _clear_results(self):
        """Limpia todos los resultados."""
        self.results_panel.clear_results()
        self.progress_panel.reset_progress()
        self.results_panel.add_to_console("Resultados limpiados", "INFO")
    
    def _on_scan_progress(self, current: int, total: int, message: str = ""):
        """Callback para actualizar progreso del escaneo."""
        self.progress_panel.update_progress(current, total, message)
        if message:
            self.results_panel.add_to_console(message, "INFO")
    
    def _on_scan_result(self, result: PortResult):
        """Callback para procesar resultado de puerto."""
        self.results_panel.add_result_to_table(result)
        if result.is_open:
            self.results_panel.add_to_console(
                f"Puerto abierto encontrado: {result.port} ({result.service_name})", 
                "SUCCESS"
            )
    
    def _on_scan_complete(self, scan_result: ScanResult):
        """Callback para escaneo completado."""
        self.config_panel.stop_scan_mode()
        
        # Actualizar información del escaneo
        total_ports = len(scan_result.open_ports) + len(scan_result.closed_ports)
        open_count = len(scan_result.open_ports)
        
        summary = f"Escaneo completado: {open_count}/{total_ports} puertos abiertos"
        self.progress_panel.set_scan_completed(summary)
        
        # Información detallada para el panel de resultados
        scan_info = (
            f"IP: {scan_result.target_ip} | "
            f"Puertos abiertos: {open_count} | "
            f"Total escaneados: {total_ports} | "
            f"Tiempo: {scan_result.scan_duration:.2f}s"
        )
        self.results_panel.set_scan_info(scan_info)
        
        # Mensaje en consola
        self.results_panel.add_to_console(summary, "SUCCESS")
        self.results_panel.add_to_console(f"Tiempo total: {scan_result.scan_duration:.2f} segundos", "INFO")
    
    def _on_scan_error(self, error_message: str):
        """Callback para errores del escaneo."""
        self.config_panel.stop_scan_mode()
        self.progress_panel.set_scan_error(error_message)
        self.results_panel.add_to_console(f"Error en escaneo: {error_message}", "ERROR")
        messagebox.showerror("Error de Escaneo", error_message)
    
    def cleanup(self):
        """Limpia la vista y libera recursos."""
        try:
            if hasattr(self, 'scanner') and self.scanner:
                self.scanner.stop_scan()
        except:
            pass
    
    def _run_scan_thread(self, config: dict):
        """
        Ejecuta el escaneo en un hilo separado.
        
        Args:
            config: Configuración del escaneo
        """
        try:
            # Ejecutar escaneo usando el método real del scanner
            result = self.scanner.scan_host(config["ip"])
            
            # Procesar resultado en el hilo principal
            self.main_frame.after(0, self._on_scan_complete, result)
                
        except Exception as e:
            self.main_frame.after(0, self._on_scan_error, str(e)) 