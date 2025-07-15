#!/usr/bin/env python3
"""
Script para verificar qué proceso está usando la base de datos.
"""
import psutil
import sys
from pathlib import Path

def find_processes_using_file(filepath):
    """Encuentra procesos que están usando un archivo específico."""
    filepath = Path(filepath).resolve()
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            # Obtener archivos abiertos por el proceso
            if proc.info['open_files']:
                for file in proc.info['open_files']:
                    if Path(file.path).resolve() == filepath:
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'path': file.path
                        })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return processes

def main():
    db_path = "data/camera_data.db"
    
    print(f"Buscando procesos que usan: {db_path}")
    processes = find_processes_using_file(db_path)
    
    if processes:
        print(f"\n⚠️  Encontrados {len(processes)} procesos usando la base de datos:")
        for proc in processes:
            print(f"  - PID: {proc['pid']}, Nombre: {proc['name']}")
        
        print("\nPara cerrar estos procesos:")
        print("1. En Windows: taskkill /F /PID <numero_pid>")
        print("2. O cierra las aplicaciones manualmente")
    else:
        print("✅ No se encontraron procesos usando la base de datos")
        print("   Puede que el archivo esté bloqueado por el sistema")
        print("   Intente reiniciar el equipo si el problema persiste")

if __name__ == "__main__":
    # Instalar psutil si no está disponible
    try:
        import psutil
    except ImportError:
        print("Instalando psutil...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    main()