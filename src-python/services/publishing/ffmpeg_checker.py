"""
Verificador de FFmpeg con compatibilidad para Python 3.13 en Windows.

Este módulo proporciona una verificación robusta de FFmpeg que funciona
en todas las versiones de Python y sistemas operativos.
"""

import shutil
import subprocess
import re
from typing import Optional, Tuple
from services.logging_service import get_secure_logger


logger = get_secure_logger("services.publishing.ffmpeg_checker")


def check_ffmpeg_sync() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica si FFmpeg está disponible de forma síncrona.
    
    Esta función evita problemas con asyncio en Python 3.13+ en Windows.
    
    Returns:
        Tupla con (disponible, path, version)
    """
    try:
        # Buscar FFmpeg en PATH
        ffmpeg_path = shutil.which('ffmpeg')
        
        if not ffmpeg_path:
            logger.warning("FFmpeg no encontrado en PATH")
            return False, None, None
        
        logger.debug(f"FFmpeg encontrado en: {ffmpeg_path}")
        
        # Verificar que funciona ejecutando -version
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parsear versión
                version_match = re.search(r'ffmpeg version ([^\s]+)', output)
                version = version_match.group(1) if version_match else "unknown"
                
                logger.info(f"FFmpeg {version} disponible en {ffmpeg_path}")
                
                # Verificar si es una versión muy antigua
                major_version_match = re.search(r'^(\d+)', version)
                if major_version_match:
                    major_version = int(major_version_match.group(1))
                    if major_version < 4:
                        logger.warning(
                            f"FFmpeg versión {version} es antigua. "
                            "Se recomienda versión 4.0 o superior."
                        )
                
                return True, ffmpeg_path, version
                
            else:
                logger.error(f"FFmpeg retornó código de error: {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr}")
                return False, ffmpeg_path, None
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout ejecutando 'ffmpeg -version'")
            return False, ffmpeg_path, None
            
        except Exception as e:
            logger.error(f"Error ejecutando FFmpeg: {str(e)}")
            return False, ffmpeg_path, None
            
    except Exception as e:
        logger.error(f"Error inesperado verificando FFmpeg: {str(e)}")
        return False, None, None


def get_ffmpeg_info() -> dict:
    """
    Obtiene información detallada de FFmpeg.
    
    Returns:
        Dict con información de FFmpeg
    """
    info = {
        'available': False,
        'path': None,
        'version': None,
        'codecs': [],
        'formats': [],
        'protocols': []
    }
    
    available, path, version = check_ffmpeg_sync()
    
    info['available'] = available
    info['path'] = path
    info['version'] = version
    
    if not available or not path:
        return info
    
    # Obtener codecs (simplificado)
    try:
        result = subprocess.run(
            [path, '-codecs'],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        if result.returncode == 0:
            # Buscar codecs relevantes
            lines = result.stdout.split('\n')
            for line in lines:
                if 'h264' in line.lower():
                    info['codecs'].append('h264')
                    break
                    
    except:
        pass
    
    # Obtener protocolos
    try:
        result = subprocess.run(
            [path, '-protocols'],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        if result.returncode == 0:
            output = result.stdout.lower()
            if 'rtsp' in output:
                info['protocols'].append('rtsp')
            if 'rtmp' in output:
                info['protocols'].append('rtmp')
            if 'http' in output:
                info['protocols'].append('http')
                
    except:
        pass
    
    return info