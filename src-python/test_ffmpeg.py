#!/usr/bin/env python3
"""
Script para verificar que FFmpeg está correctamente instalado y funcionando.
"""

import asyncio
import sys
import shutil
from pathlib import Path

# Agregar src-python al path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Configurar event loop para Windows
if sys.platform == 'win32':
    from utils.async_helpers import setup_windows_event_loop
    setup_windows_event_loop()

from utils.async_helpers import run_command_with_timeout


async def test_ffmpeg():
    """Prueba la instalación de FFmpeg."""
    print("=== Verificando FFmpeg ===\n")
    
    # Buscar FFmpeg en PATH
    ffmpeg_path = shutil.which('ffmpeg')
    
    if not ffmpeg_path:
        print("❌ FFmpeg NO encontrado en PATH")
        print("\nPara instalar FFmpeg:")
        print("1. Descarga desde: https://ffmpeg.org/download.html")
        print("2. Extrae los archivos")
        print("3. Agrega la carpeta 'bin' al PATH del sistema")
        return False
    
    print(f"✅ FFmpeg encontrado en: {ffmpeg_path}")
    
    # Verificar versión
    print("\n=== Verificando versión ===")
    
    try:
        return_code, stdout, stderr = await run_command_with_timeout(
            ['ffmpeg', '-version'],
            timeout=5.0
        )
        
        if return_code == 0:
            # Extraer versión
            lines = stdout.split('\n') if stdout else []
            if lines:
                version_line = lines[0]
                print(f"✅ {version_line}")
            else:
                print("✅ FFmpeg funciona correctamente")
            
            # Mostrar codecs disponibles (primeras líneas)
            print("\n=== Codecs principales ===")
            if len(lines) > 1:
                for line in lines[1:6]:
                    if line.strip():
                        print(f"  {line.strip()}")
            
            return True
        else:
            print(f"❌ Error ejecutando FFmpeg (código: {return_code})")
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando FFmpeg: {str(e)}")
        return False


async def test_ffmpeg_formats():
    """Prueba los formatos soportados por FFmpeg."""
    print("\n\n=== Verificando formatos RTSP ===")
    
    try:
        # Verificar soporte RTSP
        return_code, stdout, stderr = await run_command_with_timeout(
            ['ffmpeg', '-formats'],
            timeout=5.0
        )
        
        if return_code == 0 and stdout:
            # Buscar RTSP en la salida
            lines = stdout.split('\n')
            rtsp_found = False
            
            for line in lines:
                if 'rtsp' in line.lower():
                    print(f"✅ Soporte RTSP encontrado: {line.strip()}")
                    rtsp_found = True
                    break
            
            if not rtsp_found:
                print("⚠️ No se encontró soporte RTSP explícito (podría estar incluido)")
            
            # Verificar protocolos
            print("\n=== Verificando protocolos ===")
            return_code, stdout, stderr = await run_command_with_timeout(
                ['ffmpeg', '-protocols'],
                timeout=5.0
            )
            
            if return_code == 0 and stdout:
                if 'rtsp' in stdout.lower():
                    print("✅ Protocolo RTSP soportado")
                if 'rtmp' in stdout.lower():
                    print("✅ Protocolo RTMP soportado")
                if 'http' in stdout.lower():
                    print("✅ Protocolo HTTP soportado")
            
    except Exception as e:
        print(f"❌ Error verificando formatos: {str(e)}")


def main():
    """Función principal."""
    print("Test de FFmpeg para Universal Camera Viewer")
    print("=" * 50)
    print(f"Python: {sys.version}")
    print(f"Sistema: {sys.platform}")
    print("=" * 50)
    print()
    
    # Ejecutar pruebas
    loop = asyncio.get_event_loop()
    
    # Prueba básica
    ffmpeg_ok = loop.run_until_complete(test_ffmpeg())
    
    if ffmpeg_ok:
        # Prueba de formatos
        loop.run_until_complete(test_ffmpeg_formats())
        
        print("\n" + "=" * 50)
        print("✅ FFmpeg está correctamente instalado y configurado")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ FFmpeg no está correctamente instalado")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()