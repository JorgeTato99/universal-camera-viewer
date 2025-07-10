#!/usr/bin/env python3
"""
Script temporal para resetear el tema a claro por defecto
"""

import os
import json
from pathlib import Path

def reset_theme_to_light():
    """Resetea el tema a claro eliminando la configuración persistente."""
    
    config_file = Path("config/theme_config.json")
    
    print("🎨 Reseteando tema a claro por defecto...")
    
    try:
        if config_file.exists():
            print(f"🗑️ Eliminando archivo de configuración: {config_file}")
            os.remove(config_file)
        
        # Crear nuevo archivo con tema claro
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'theme': 'light',
            'primary_color': '#1976D2'  # ft.Colors.BLUE_700
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Tema reseteado a claro por defecto")
        print("🚀 Ahora puedes ejecutar: python src/main.py")
        
    except Exception as e:
        print(f"❌ Error reseteando tema: {e}")

if __name__ == "__main__":
    reset_theme_to_light() 