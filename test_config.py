#!/usr/bin/env python3
"""
Script de prueba para verificar la carga de configuración.
"""

import logging
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_config():
    """Prueba la carga de configuración."""
    print("🔧 Probando carga de configuración...")
    
    from src.utils.config import get_config
    
    config = get_config()
    
    print("\n📋 Variables de entorno cargadas:")
    print(f"  Dahua IP: {getattr(config, 'camera_ip', 'None')}")
    print(f"  TP-Link IP: {getattr(config, 'tplink_ip', 'None')}")
    print(f"  Steren IP: {getattr(config, 'steren_ip', 'None')}")
    print(f"  Generic IP: {getattr(config, 'generic_ip', 'None')}")
    
    print(f"\n👤 Usuarios:")
    print(f"  Dahua User: {getattr(config, 'camera_user', 'None')}")
    print(f"  TP-Link User: {getattr(config, 'tplink_user', 'None')}")
    print(f"  Steren User: {getattr(config, 'steren_user', 'None')}")
    print(f"  Generic User: {getattr(config, 'generic_user', 'None')}")
    
    print(f"\n🔐 Contraseñas (ocultas):")
    print(f"  Dahua Password: {'***' if getattr(config, 'camera_password', '') else 'None'}")
    print(f"  TP-Link Password: {'***' if getattr(config, 'tplink_password', '') else 'None'}")
    print(f"  Steren Password: {'***' if getattr(config, 'steren_password', '') else 'None'}")
    print(f"  Generic Password: {'***' if getattr(config, 'generic_password', '') else 'None'}")
    
    print(f"\n📷 Cámaras disponibles:")
    cameras = config.get_available_cameras()
    for i, cam in enumerate(cameras, 1):
        print(f"  {i}. {cam['brand'].upper()}: {cam['name']} ({cam['ip']})")
    
    print(f"\n✅ Total de cámaras encontradas: {len(cameras)}")

if __name__ == "__main__":
    test_config() 