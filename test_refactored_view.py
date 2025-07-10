"""
Script de prueba para la vista de descubrimiento refactorizada.
"""

import tkinter as tk
from src.gui.discovery.port_discovery_view_refactored import PortDiscoveryViewRefactored

def main():
    """Función principal de prueba."""
    # Crear ventana principal
    root = tk.Tk()
    root.title("Prueba Vista Refactorizada")
    root.geometry("1200x800")
    
    try:
        # Crear vista refactorizada
        view = PortDiscoveryViewRefactored(root)
        
        # Configurar cierre limpio
        def on_closing():
            view.cleanup()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Iniciar loop principal
        root.mainloop()
        
    except Exception as e:
        print(f"Error en prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 