#!/usr/bin/env python3
"""
Visor Universal de Cámaras - Aplicación Principal
Sistema profesional de videovigilancia multi-marca con mejoras UX avanzadas.

Características principales:
- ✅ Interfaz moderna con iconos y tooltips
- ✅ Panel de control completo con pestañas
- ✅ Soporte multi-marca (Dahua, TP-Link, Steren, Generic)
- ✅ Configuración desde archivo .env
- ✅ Shortcuts de teclado completos
- ✅ Métricas en tiempo real (FPS, latencia, uptime)
- ✅ Sistema de layouts adaptativos
- ✅ Feedback visual mejorado
- ✅ Logging detallado para diagnóstico
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional

# Agregar el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Configura el sistema de logging mejorado."""
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'universal_visor.log', encoding='utf-8')
        ]
    )
    
    # Configurar logger específico para la aplicación
    logger = logging.getLogger("UniversalVisor")
    logger.info("=== Sistema de logging inicializado ===")
    return logger

class UniversalVisorApp:
    """
    Aplicación principal del Visor Universal de Cámaras.
    Integra todas las mejoras UX y funcionalidades avanzadas.
    """
    
    def __init__(self):
        """Inicializa la aplicación principal."""
        self.logger = setup_logging()
        self.logger.info("🚀 Iniciando Visor Universal de Cámaras v0.2.0")
        
        # Crear ventana principal
        self._create_main_window()
        
        # Configurar estilos
        self._setup_styles()
        
        # Crear interfaz principal
        self._create_main_interface()
        
        # Configurar eventos
        self._setup_events()
        
        self.logger.info("✅ Aplicación principal inicializada correctamente")
    
    def _create_main_window(self):
        """Crea y configura la ventana principal."""
        self.root = tk.Tk()
        self.root.title("🎥 Visor Universal de Cámaras - Módulo Principal")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 700)
        
        # Configurar icono de la ventana (si existe)
        try:
            # Intentar cargar icono
            icon_path = Path("assets/icon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Continuar sin icono si no se puede cargar
        
        # Centrar ventana
        self._center_window()
        
        # Configurar colores
        self.root.configure(bg='#f8f9fa')
        
        self.logger.info("🖼️ Ventana principal creada y configurada")
    
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_styles(self):
        """Configura los estilos visuales de la aplicación."""
        self.style = ttk.Style()
        
        # Intentar usar tema moderno
        try:
            available_themes = self.style.theme_names()
            if 'clam' in available_themes:
                self.style.theme_use('clam')
            elif 'alt' in available_themes:
                self.style.theme_use('alt')
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo configurar tema: {e}")
        
        # Configurar estilos personalizados
        self.style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        self.style.configure('Subtitle.TLabel', font=('Arial', 10), foreground='#34495e')
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#27ae60')
        self.style.configure('Status.TLabel', font=('Arial', 9), foreground='#7f8c8d')
        self.style.configure('Accent.TButton', font=('Arial', 9, 'bold'))
        
        self.logger.info("🎨 Estilos visuales configurados")
    
    def _create_main_interface(self):
        """Crea la interfaz principal de la aplicación."""
        # Header principal
        self._create_header()
        
        # Contenedor principal
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Crear el visor mejorado
        self._create_enhanced_viewer()
        
        # Footer con información
        self._create_footer()
    
    def _create_header(self):
        """Crea el header principal con información de la aplicación."""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Título principal
        title_label = ttk.Label(
            header_frame,
            text="🎥 Visor Universal de Cámaras",
            style='Title.TLabel'
        )
        title_label.pack(side=tk.LEFT)
        
        # Información de versión
        version_label = ttk.Label(
            header_frame,
            text="v0.2.0 - Sistema Profesional Multi-marca",
            style='Subtitle.TLabel'
        )
        version_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de acción rápida
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            actions_frame,
            text="ℹ️ Acerca de",
            command=self._show_about,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            actions_frame,
            text="📋 Logs",
            command=self._show_logs,
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        # Separador
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, pady=2)
    
    def _create_enhanced_viewer(self):
        """Crea el visor mejorado con todas las funcionalidades UX."""
        try:
            # Importar el visor mejorado
            from src.viewer.real_time_viewer import RealTimeViewer
            
            # Crear el visor con todas las mejoras UX
            self.viewer = RealTimeViewer(parent_container=self.main_container)
            
            # El visor se empaqueta automáticamente en su constructor
            self.logger.info("✅ Visor mejorado creado e integrado")
            
        except Exception as e:
            self.logger.error(f"❌ Error creando visor mejorado: {e}")
            self._show_error_fallback(str(e))
    
    def _show_error_fallback(self, error_msg: str):
        """Muestra una interfaz de fallback en caso de error."""
        error_frame = ttk.Frame(self.main_container)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Mensaje de error
        error_label = ttk.Label(
            error_frame,
            text="❌ Error al cargar el visor principal",
            style='Title.TLabel',
            foreground='#e74c3c'
        )
        error_label.pack(pady=10)
        
        # Detalles del error
        details_label = ttk.Label(
            error_frame,
            text=f"Detalles: {error_msg}",
            style='Subtitle.TLabel'
        )
        details_label.pack(pady=5)
        
        # Botón para reintentar
        retry_btn = ttk.Button(
            error_frame,
            text="🔄 Reintentar",
            command=self._retry_viewer_creation,
            style='Accent.TButton'
        )
        retry_btn.pack(pady=10)
    
    def _retry_viewer_creation(self):
        """Reintenta crear el visor."""
        # Limpiar contenedor
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Reintentar creación
        self._create_enhanced_viewer()
    
    def _create_footer(self):
        """Crea el footer con información de estado."""
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Separador
        separator = ttk.Separator(footer_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 5))
        
        # Información de estado
        status_frame = ttk.Frame(footer_frame)
        status_frame.pack(fill=tk.X)
        
        # Estado de la aplicación
        self.status_label = ttk.Label(
            status_frame,
            text="🟢 Sistema inicializado correctamente",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Información del sistema
        system_info = f"Python {sys.version_info.major}.{sys.version_info.minor} | Tkinter {tk.TkVersion}"
        system_label = ttk.Label(
            status_frame,
            text=system_info,
            style='Status.TLabel'
        )
        system_label.pack(side=tk.RIGHT)
    
    def _setup_events(self):
        """Configura los eventos de la aplicación."""
        # Evento de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Shortcuts globales
        self.root.bind('<F1>', lambda e: self._show_help())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<Control-l>', lambda e: self._show_logs())
        
        self.logger.info("⌨️ Eventos y shortcuts configurados")
    
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = """🎥 Visor Universal de Cámaras v0.2.0

Sistema profesional de videovigilancia multi-marca con mejoras UX avanzadas.

✨ Características principales:
• Interfaz moderna con iconos y tooltips
• Panel de control completo con pestañas
• Soporte multi-marca (Dahua, TP-Link, Steren, Generic)
• Configuración desde archivo .env
• Shortcuts de teclado completos
• Métricas en tiempo real (FPS, latencia, uptime)
• Sistema de layouts adaptativos
• Feedback visual mejorado
• Logging detallado para diagnóstico

🏗️ Arquitectura:
• Principios SOLID y Clean Code
• Patrón MVC con separación de responsabilidades
• Sistema modular y extensible
• Manejo robusto de errores

👨‍💻 Desarrollado con Python + Tkinter
📅 Versión: 0.2.0 - Junio 2025"""
        
        messagebox.showinfo("Acerca de - Visor Universal", about_text)
    
    def _show_logs(self):
        """Abre una ventana para mostrar los logs."""
        try:
            log_window = tk.Toplevel(self.root)
            log_window.title("📋 Logs del Sistema")
            log_window.geometry("800x600")
            
            # Crear área de texto con scroll
            text_frame = ttk.Frame(log_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 9))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Cargar logs
            try:
                log_file = Path("logs/universal_visor.log")
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        text_widget.insert(tk.END, f.read())
                else:
                    text_widget.insert(tk.END, "No se encontraron logs.")
            except Exception as e:
                text_widget.insert(tk.END, f"Error cargando logs: {e}")
            
            # Ir al final del texto
            text_widget.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron mostrar los logs:\n{e}")
    
    def _show_help(self):
        """Muestra la ayuda de la aplicación."""
        help_text = """🆘 Ayuda - Visor Universal de Cámaras

⌨️ Shortcuts de Teclado:
• F1: Mostrar esta ayuda
• F5: Conectar todas las cámaras
• F6: Desconectar todas las cámaras
• F8: Capturar todas las cámaras
• F9: Refrescar vista
• Ctrl+S: Guardar configuración
• Ctrl+O: Cargar configuración
• Ctrl+L: Mostrar logs
• Ctrl+Q: Salir de la aplicación

🎯 Uso Básico:
1. Las cámaras se cargan automáticamente desde el archivo .env
2. Usa los botones de la barra superior para acciones globales
3. Cada cámara tiene sus propios controles individuales
4. El panel inferior permite configurar cámaras y layouts

📋 Panel de Control:
• Pestaña Cámaras: Agregar, editar, eliminar cámaras
• Pestaña Layout: Configurar disposición en pantalla
• Pestaña Configuración: Ajustes generales del sistema

🔧 Solución de Problemas:
• Revisa los logs (Ctrl+L) para diagnóstico
• Verifica la conectividad de red a las cámaras
• Confirma credenciales en el archivo .env
• Usa "Probar Conexión" en el panel de control"""
        
        messagebox.showinfo("Ayuda - Visor Universal", help_text)
    
    def _on_closing(self):
        """Maneja el cierre de la aplicación."""
        try:
            self.logger.info("🔄 Cerrando aplicación...")
            
            # Cerrar el visor si existe
            if hasattr(self, 'viewer') and self.viewer:
                self.viewer.cleanup()
            
            # Cerrar ventana principal
            self.root.quit()
            self.root.destroy()
            
            self.logger.info("✅ Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error cerrando aplicación: {e}")
        finally:
            sys.exit(0)
    
    def run(self):
        """Ejecuta la aplicación principal."""
        try:
            self.logger.info("🚀 Iniciando bucle principal de la aplicación...")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("⚠️ Aplicación interrumpida por usuario")
            self._on_closing()
        except Exception as e:
            self.logger.error(f"❌ Error en bucle principal: {e}")
            messagebox.showerror("Error Crítico", f"Error inesperado:\n{e}")
            self._on_closing()

def main():
    """Función principal de entrada."""
    try:
        # Verificar dependencias básicas
        required_modules = ['tkinter', 'PIL', 'cv2', 'dotenv']
        missing_modules = []
        
        for module in required_modules:
            try:
                if module == 'PIL':
                    import PIL
                elif module == 'cv2':
                    import cv2
                elif module == 'dotenv':
                    import dotenv
                else:
                    __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"❌ Módulos faltantes: {', '.join(missing_modules)}")
            print("📦 Instala las dependencias con: pip install -r requirements.txt")
            sys.exit(1)
        
        # Crear y ejecutar aplicación
        app = UniversalVisorApp()
        app.run()
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("📦 Asegúrate de que todas las dependencias estén instaladas")
        print("💡 Ejecuta: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        logging.exception("Error crítico en aplicación principal")
        sys.exit(1)

if __name__ == "__main__":
    main() 