"""
Gestor de procesos FFmpeg y parser de salida.

Encapsula la lógica específica de FFmpeg para mantener
el servicio principal limpio y enfocado.
"""

import asyncio
import re
import shutil
import sys
from typing import Dict, Optional, Any
from services.logging_service import get_secure_logger
from utils.async_helpers import create_subprocess_safely
from services.publishing.ffmpeg_checker import check_ffmpeg_sync

class FFmpegManager:
    """
    Gestiona interacciones con FFmpeg.
    
    Responsabilidades:
    - Verificar disponibilidad de FFmpeg
    - Parsear salida de FFmpeg (stdout/stderr)
    - Extraer métricas de streaming en tiempo real
    - Identificar y categorizar errores
    
    Esta clase encapsula toda la lógica específica de FFmpeg
    para mantener el servicio principal limpio y reutilizable.
    
    Attributes:
        logger: Logger para mensajes de depuración
        _ffmpeg_path: Ruta completa al ejecutable de FFmpeg
        _error_count: Contador de errores para estadísticas
    """
    
    def __init__(self):
        """Inicializa el manager."""
        self.logger = get_secure_logger("services.publishing.ffmpeg_manager")
        self._ffmpeg_path: Optional[str] = None
        self._error_count: Dict[str, int] = {}  # Contador de errores por tipo
        
    async def check_ffmpeg_available(self) -> bool:
        """
        Verifica que FFmpeg esté instalado y accesible.
        
        Usa verificación síncrona para evitar problemas con asyncio
        en Python 3.13+ en Windows.
        
        Returns:
            True si FFmpeg está disponible y funcional
            
        Side Effects:
            Establece self._ffmpeg_path con la ruta encontrada
        """
        self.logger.debug("Verificando disponibilidad de FFmpeg")
        
        try:
            # Usar verificación síncrona para evitar problemas con Python 3.13
            available, ffmpeg_path, version = check_ffmpeg_sync()
            
            if not available:
                self.logger.error(
                    "FFmpeg no está disponible. "
                    "Instala FFmpeg desde https://ffmpeg.org/download.html"
                )
                return False
            
            self._ffmpeg_path = ffmpeg_path
            self.logger.info(f"FFmpeg {version} disponible en {self._ffmpeg_path}")
            
            return True
                
        except Exception as e:
            self.logger.exception("Error inesperado verificando FFmpeg")
            return False
            
    def parse_metrics(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parsea línea de salida de FFmpeg para extraer métricas.
        
        Extrae información de rendimiento de las líneas de estadísticas
        que FFmpeg emite durante el procesamiento.
        
        Args:
            line: Línea de salida de FFmpeg
            
        Returns:
            Dict con métricas o None si no es una línea de estadísticas
            
        Example:
            Input: "frame=  120 fps= 30 q=-1.0 size=    1024kB time=00:00:04.00 bitrate=2097.2kbits/s speed=1.00x"
            Output: {
                'frames': 120,
                'fps': 30.0,
                'bitrate_kbps': 2097.2,
                'speed': 1.0,
                'time_seconds': 4,
                'size_kb': 1024
            }
        """
        # Verificar si es una línea de stats (contiene frame= o time=)
        if 'frame=' not in line and 'time=' not in line:
            return None
            
        metrics = {}
        
        try:
            # Frame count
            frame_match = re.search(r'frame=\s*(\d+)', line)
            if frame_match:
                metrics['frames'] = int(frame_match.group(1))
                
            # FPS (puede ser decimal o 'N/A')
            fps_match = re.search(r'fps=\s*([\d.]+|N/A)', line)
            if fps_match and fps_match.group(1) != 'N/A':
                try:
                    metrics['fps'] = float(fps_match.group(1))
                except ValueError:
                    pass
                    
            # Bitrate
            bitrate_match = re.search(r'bitrate=\s*([\d.]+)kbits/s', line)
            if bitrate_match:
                metrics['bitrate_kbps'] = float(bitrate_match.group(1))
                
            # Speed (factor de velocidad de procesamiento)
            speed_match = re.search(r'speed=\s*([\d.]+)x', line)
            if speed_match:
                speed = float(speed_match.group(1))
                metrics['speed'] = speed
                
                # Advertir si la velocidad es menor a 1.0x (no tiempo real)
                if speed < 0.95:  # Dar un pequeño margen
                    self.logger.warning(
                        f"Velocidad de procesamiento baja: {speed}x. "
                        "El stream puede tener problemas de rendimiento"
                    )
                    
            # Tamaño
            size_match = re.search(r'size=\s*(\d+)kB', line)
            if size_match:
                metrics['size_kb'] = int(size_match.group(1))
                
            # Tiempo transcurrido
            time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})(?:\.(\d{2}))?', line)
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = int(time_match.group(3))
                centiseconds = int(time_match.group(4) or 0)
                
                total_seconds = hours * 3600 + minutes * 60 + seconds + (centiseconds / 100)
                metrics['time_seconds'] = total_seconds
                
            # Calidad (q value)
            q_match = re.search(r'q=([\d.-]+)', line)
            if q_match:
                q_value = q_match.group(1)
                if q_value != '-1.0':  # -1.0 significa que no aplica
                    try:
                        metrics['quality'] = float(q_value)
                    except ValueError:
                        pass
                        
        except Exception as e:
            self.logger.debug(f"Error parseando métricas de línea: {e}")
            
        return metrics if metrics else None
        
    def parse_error(self, line: str) -> Optional[str]:
        """
        Extrae mensaje de error de la salida de FFmpeg.
        
        Identifica y categoriza errores comunes de FFmpeg para
        proporcionar mensajes más claros al usuario.
        
        Args:
            line: Línea de salida de FFmpeg (stderr)
            
        Returns:
            Mensaje de error formateado o None si no es un error
        """
        if not line or not line.strip():
            return None
            
        line_lower = line.lower()
        
        # Patrones de error con mensajes amigables
        error_mappings = [
            # Errores de conexión
            (r'Connection refused', 'Conexión rechazada por el servidor'),
            (r'Connection timed out', 'Timeout de conexión - verifica que la cámara esté accesible'),
            (r'No route to host', 'No se puede alcanzar el host - verifica la red'),
            (r'Network is unreachable', 'Red inalcanzable - verifica conectividad'),
            
            # Errores de autenticación
            (r'401 Unauthorized', 'Autenticación fallida - verifica usuario y contraseña'),
            (r'403 Forbidden', 'Acceso denegado - sin permisos suficientes'),
            
            # Errores de recurso
            (r'404 Not Found', 'Stream no encontrado - verifica la URL'),
            (r'Stream not found', 'Stream no encontrado en la URL especificada'),
            
            # Errores de protocolo
            (r'Invalid data found', 'Datos inválidos - el stream puede estar corrupto'),
            (r'Protocol not found', 'Protocolo no soportado - verifica el formato de URL'),
            (r'Unsupported codec', 'Códec no soportado - formato de video incompatible'),
            
            # Errores HTTP
            (r'Server returned (4\d\d)', 'Error HTTP \\1 del servidor'),
            (r'Server returned (5\d\d)', 'Error del servidor \\1 - servidor no disponible'),
            
            # Errores RTSP específicos
            (r'method DESCRIBE failed', 'Fallo RTSP DESCRIBE - URL puede ser incorrecta'),
            (r'method SETUP failed', 'Fallo RTSP SETUP - problema con la sesión'),
            (r'method PLAY failed', 'Fallo RTSP PLAY - no se puede iniciar stream'),
            
            # Errores de recursos
            (r'Cannot allocate memory', 'Sin memoria suficiente'),
            (r'Too many open files', 'Demasiados archivos abiertos - límite del sistema alcanzado'),
        ]
        
        # Buscar patrones conocidos
        for pattern, friendly_msg in error_mappings:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Reemplazar grupos capturados si los hay
                if match.groups():
                    return re.sub(pattern, friendly_msg, match.group(0), flags=re.IGNORECASE)
                return friendly_msg
                
        # Detectar errores genéricos
        if 'error' in line_lower:
            # Limpiar mensaje de error
            error_msg = line.strip()
            
            # Remover prefijos comunes de FFmpeg
            prefixes_to_remove = [
                r'^\[.+?\]\s*',  # [rtsp @ 0x...]
                r'^.+?:\s*Error\s*',  # path/file: Error
            ]
            
            for prefix in prefixes_to_remove:
                error_msg = re.sub(prefix, '', error_msg, flags=re.IGNORECASE)
                
            return error_msg
            
        # Detectar warnings que pueden ser críticos
        critical_warnings = [
            'unable to open',
            'failed to',
            'could not',
            'permission denied',
            'access denied'
        ]
        
        for warning in critical_warnings:
            if warning in line_lower:
                return line.strip()
                
        return None