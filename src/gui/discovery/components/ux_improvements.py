"""
Mejoras adicionales de UX para el módulo Port Discovery.
Incluye funcionalidades avanzadas y optimizaciones de experiencia de usuario.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional
import json
import os
from datetime import datetime

class UXImprovements:
    """
    Clase que contiene mejoras adicionales de UX para implementar.
    """
    
    @staticmethod
    def create_scan_presets_widget(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un widget de presets de escaneo para configuraciones rápidas.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con el widget de presets
        """
        presets_frame = ttk.LabelFrame(parent_frame, text="⚡ Presets de Escaneo", padding=5)
        
        # Presets predefinidos
        presets = {
            "🚀 Rápido": {"timeout": 1.0, "intensity": "basic", "description": "Escaneo rápido básico"},
            "⚖️ Balanceado": {"timeout": 3.0, "intensity": "medium", "description": "Balance entre velocidad y precisión"},
            "🔍 Completo": {"timeout": 5.0, "intensity": "high", "description": "Escaneo exhaustivo y preciso"},
            "🎯 Personalizado": {"timeout": 3.0, "intensity": "basic", "description": "Configuración personalizada"}
        }
        
        # Crear botones de preset
        buttons_frame = ttk.Frame(presets_frame)
        buttons_frame.pack(fill=tk.X)
        
        for preset_name, config in presets.items():
            btn = ttk.Button(
                buttons_frame,
                text=preset_name,
                width=12,
                command=lambda cfg=config: UXImprovements._apply_preset(cfg)
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            # Tooltip con descripción
            UXImprovements._add_tooltip(btn, config["description"])
        
        return presets_frame
    
    @staticmethod
    def create_scan_history_widget(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un widget de historial de escaneos.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con el historial de escaneos
        """
        history_frame = ttk.LabelFrame(parent_frame, text="📊 Historial de Escaneos", padding=5)
        
        # Lista de historial
        history_tree = ttk.Treeview(
            history_frame,
            columns=("IP", "Fecha", "Abiertos", "Total", "Tiempo"),
            show="headings",
            height=4
        )
        
        # Configurar columnas
        history_tree.heading("IP", text="IP")
        history_tree.heading("Fecha", text="Fecha")
        history_tree.heading("Abiertos", text="Abiertos")
        history_tree.heading("Total", text="Total")
        history_tree.heading("Tiempo", text="Tiempo")
        
        history_tree.column("IP", width=120)
        history_tree.column("Fecha", width=100)
        history_tree.column("Abiertos", width=60)
        history_tree.column("Total", width=60)
        history_tree.column("Tiempo", width=80)
        
        history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Botones de control
        controls_frame = ttk.Frame(history_frame)
        controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(controls_frame, text="🔄 Repetir", width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="📋 Comparar", width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="🗑️ Limpiar", width=10).pack(side=tk.LEFT, padx=2)
        
        return history_frame
    
    @staticmethod
    def create_network_discovery_widget(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un widget de descubrimiento automático de red.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con herramientas de descubrimiento
        """
        discovery_frame = ttk.LabelFrame(parent_frame, text="🌐 Descubrimiento de Red", padding=5)
        
        # Información de red actual
        info_frame = ttk.Frame(discovery_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(info_frame, text="Red actual:", font=("Arial", 8)).pack(side=tk.LEFT)
        network_label = ttk.Label(info_frame, text="192.168.1.0/24", font=("Arial", 8, "bold"))
        network_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Botones de descubrimiento
        buttons_frame = ttk.Frame(discovery_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="🔍 Escanear Red", width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="📡 Ping Sweep", width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="🎯 Auto-detectar", width=15).pack(side=tk.LEFT, padx=2)
        
        return discovery_frame
    
    @staticmethod
    def create_performance_monitor(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un monitor de rendimiento en tiempo real.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con métricas de rendimiento
        """
        perf_frame = ttk.LabelFrame(parent_frame, text="⚡ Monitor de Rendimiento", padding=5)
        
        # Métricas en tiempo real
        metrics_frame = ttk.Frame(perf_frame)
        metrics_frame.pack(fill=tk.X)
        
        # CPU Usage
        cpu_frame = ttk.Frame(metrics_frame)
        cpu_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(cpu_frame, text="CPU:", font=("Arial", 8)).pack()
        cpu_progress = ttk.Progressbar(cpu_frame, length=60, mode='determinate')
        cpu_progress.pack()
        
        # Memory Usage
        mem_frame = ttk.Frame(metrics_frame)
        mem_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(mem_frame, text="RAM:", font=("Arial", 8)).pack()
        mem_progress = ttk.Progressbar(mem_frame, length=60, mode='determinate')
        mem_progress.pack()
        
        # Network Usage
        net_frame = ttk.Frame(metrics_frame)
        net_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(net_frame, text="Red:", font=("Arial", 8)).pack()
        net_progress = ttk.Progressbar(net_frame, length=60, mode='determinate')
        net_progress.pack()
        
        return perf_frame
    
    @staticmethod
    def create_smart_suggestions(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un panel de sugerencias inteligentes.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con sugerencias
        """
        suggestions_frame = ttk.LabelFrame(parent_frame, text="💡 Sugerencias Inteligentes", padding=5)
        
        # Lista de sugerencias
        suggestions_list = tk.Listbox(suggestions_frame, height=3, font=("Arial", 8))
        suggestions_list.pack(fill=tk.BOTH, expand=True)
        
        # Sugerencias de ejemplo
        sample_suggestions = [
            "💡 Considera usar timeout de 2s para redes locales",
            "🚀 El puerto 8080 está abierto, prueba HTTP-Alt",
            "🔒 Se detectó SSH (22), verifica credenciales"
        ]
        
        for suggestion in sample_suggestions:
            suggestions_list.insert(tk.END, suggestion)
        
        return suggestions_frame
    
    @staticmethod
    def create_keyboard_shortcuts_help(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un panel de ayuda con shortcuts de teclado.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con shortcuts
        """
        help_frame = ttk.LabelFrame(parent_frame, text="⌨️ Shortcuts de Teclado", padding=5)
        
        shortcuts = [
            ("F5", "Iniciar escaneo"),
            ("Esc", "Detener escaneo"),
            ("Ctrl+L", "Limpiar resultados"),
            ("Ctrl+1", "Modo simple"),
            ("Ctrl+2", "Modo avanzado"),
            ("Tab", "Autocompletar IP"),
            ("Ctrl+E", "Exportar resultados"),
            ("F1", "Ayuda completa")
        ]
        
        for i, (key, description) in enumerate(shortcuts):
            row_frame = ttk.Frame(help_frame)
            row_frame.pack(fill=tk.X, pady=1)
            
            ttk.Label(row_frame, text=key, font=("Consolas", 8, "bold"), width=8).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=description, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        
        return help_frame
    
    @staticmethod
    def create_theme_selector(parent_frame: tk.Widget) -> ttk.Frame:
        """
        Crea un selector de temas visuales.
        
        Args:
            parent_frame: Frame padre
            
        Returns:
            Frame con selector de temas
        """
        theme_frame = ttk.LabelFrame(parent_frame, text="🎨 Tema Visual", padding=5)
        
        themes = ["🌞 Claro", "🌙 Oscuro", "🌈 Colorido", "💼 Profesional"]
        
        theme_var = tk.StringVar(value="🌞 Claro")
        
        for theme in themes:
            ttk.Radiobutton(
                theme_frame,
                text=theme,
                variable=theme_var,
                value=theme
            ).pack(anchor=tk.W, pady=1)
        
        return theme_frame
    
    @staticmethod
    def _apply_preset(config: Dict):
        """Aplica una configuración preset."""
        # Esta función sería implementada para aplicar la configuración
        print(f"Aplicando preset: {config}")
    
    @staticmethod
    def _add_tooltip(widget, text):
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
                padx=5,
                pady=3
            )
            label.pack()
            
            tooltip.after(3000, tooltip.destroy)
        
        widget.bind('<Enter>', show_tooltip)

class ScanProfileManager:
    """
    Gestor de perfiles de escaneo para guardar y cargar configuraciones.
    """
    
    def __init__(self, profiles_file: str = "scan_profiles.json"):
        self.profiles_file = profiles_file
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict:
        """Carga perfiles desde archivo."""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando perfiles: {e}")
        
        return self._get_default_profiles()
    
    def _get_default_profiles(self) -> Dict:
        """Obtiene perfiles por defecto."""
        return {
            "Rápido": {
                "timeout": 1.0,
                "intensity": "basic",
                "description": "Escaneo rápido para pruebas",
                "created": datetime.now().isoformat()
            },
            "Estándar": {
                "timeout": 3.0,
                "intensity": "medium",
                "description": "Configuración balanceada",
                "created": datetime.now().isoformat()
            },
            "Exhaustivo": {
                "timeout": 5.0,
                "intensity": "maximum",
                "description": "Escaneo completo y detallado",
                "created": datetime.now().isoformat()
            }
        }
    
    def save_profile(self, name: str, config: Dict):
        """Guarda un perfil de configuración."""
        self.profiles[name] = {
            **config,
            "created": datetime.now().isoformat()
        }
        self._save_profiles()
    
    def delete_profile(self, name: str):
        """Elimina un perfil."""
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
    
    def get_profile(self, name: str) -> Optional[Dict]:
        """Obtiene un perfil específico."""
        return self.profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """Lista todos los perfiles disponibles."""
        return list(self.profiles.keys())
    
    def _save_profiles(self):
        """Guarda perfiles a archivo."""
        try:
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando perfiles: {e}")

class AccessibilityFeatures:
    """
    Características de accesibilidad para mejorar la usabilidad.
    """
    
    @staticmethod
    def enable_high_contrast_mode(root: tk.Tk):
        """Habilita modo de alto contraste."""
        style = ttk.Style()
        style.configure("HighContrast.TLabel", background="black", foreground="white")
        style.configure("HighContrast.TButton", background="yellow", foreground="black")
    
    @staticmethod
    def enable_large_fonts(root: tk.Tk):
        """Habilita fuentes grandes para mejor legibilidad."""
        root.option_add("*Font", "Arial 12")
    
    @staticmethod
    def add_screen_reader_support(widget, description: str):
        """Agrega soporte para lectores de pantalla."""
        # Implementación básica - en un entorno real se usaría una librería específica
        widget.configure(name=description)
    
    @staticmethod
    def enable_keyboard_navigation(root: tk.Tk):
        """Mejora la navegación por teclado."""
        # Configurar orden de tabulación
        def focus_next_widget(event):
            event.widget.tk_focusNext().focus()
            return "break"
        
        def focus_prev_widget(event):
            event.widget.tk_focusPrev().focus()
            return "break"
        
        root.bind_class("Entry", "<Tab>", focus_next_widget)
        root.bind_class("Entry", "<Shift-Tab>", focus_prev_widget)

# Ejemplo de uso de las mejoras
def demo_ux_improvements():
    """Demostración de las mejoras de UX."""
    root = tk.Tk()
    root.title("Demo - Mejoras de UX")
    root.geometry("800x600")
    
    # Crear notebook para organizar las mejoras
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Pestaña 1: Presets y configuración
    config_frame = ttk.Frame(notebook)
    notebook.add(config_frame, text="Configuración")
    
    UXImprovements.create_scan_presets_widget(config_frame).pack(fill=tk.X, pady=5)
    UXImprovements.create_network_discovery_widget(config_frame).pack(fill=tk.X, pady=5)
    
    # Pestaña 2: Historial y monitoreo
    monitor_frame = ttk.Frame(notebook)
    notebook.add(monitor_frame, text="Monitoreo")
    
    UXImprovements.create_scan_history_widget(monitor_frame).pack(fill=tk.BOTH, expand=True, pady=5)
    UXImprovements.create_performance_monitor(monitor_frame).pack(fill=tk.X, pady=5)
    
    # Pestaña 3: Ayuda y personalización
    help_frame = ttk.Frame(notebook)
    notebook.add(help_frame, text="Ayuda")
    
    help_container = ttk.Frame(help_frame)
    help_container.pack(fill=tk.BOTH, expand=True)
    
    left_frame = ttk.Frame(help_container)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    right_frame = ttk.Frame(help_container)
    right_frame.pack(side=tk.RIGHT, fill=tk.Y)
    
    UXImprovements.create_keyboard_shortcuts_help(left_frame).pack(fill=tk.BOTH, expand=True)
    UXImprovements.create_smart_suggestions(left_frame).pack(fill=tk.BOTH, expand=True, pady=(5, 0))
    
    UXImprovements.create_theme_selector(right_frame).pack(fill=tk.X)
    
    root.mainloop()

if __name__ == "__main__":
    demo_ux_improvements() 