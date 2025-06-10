"""
Conexión para cámaras Steren CCTV-235 usando protocolos ONVIF y RTSP.
Implementa la conexión específica para cámaras Steren con soporte dual-stream.
"""

import cv2
import logging
from typing import Optional, Dict, Any, List, Tuple
from .base_connection import BaseConnection

# Importaciones opcionales para ONVIF
try:
    from onvif import ONVIFCamera
    from onvif.exceptions import ONVIFError
    ONVIF_AVAILABLE = True
except ImportError:
    ONVIF_AVAILABLE = False


class SterenConnection(BaseConnection):
    """
    Conexión específica para cámaras Steren CCTV-235.
    Soporta protocolo ONVIF para control y RTSP para streaming de video.
    Implementa dual-stream: canal principal (4MP) y sub-canal (360p).
    """
    
    def __init__(self, config_manager):
        """
        Inicializa la conexión Steren.
        
        Args:
            config_manager: Instancia del gestor de configuración
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("SterenConnection")
        
        # Configuración específica Steren
        self.camera_ip = getattr(config_manager, 'steren_ip', '192.168.1.178')
        self.username = getattr(config_manager, 'steren_user', 'admin')
        self.password = getattr(config_manager, 'steren_password', '')
        self.onvif_port = getattr(config_manager, 'steren_onvif_port', 8000)
        self.rtsp_port = getattr(config_manager, 'steren_rtsp_port', 5543)
        
        # URLs específicas para Steren CCTV-235 (basado en nuestras pruebas)
        self.stream_urls = {
            'main': f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/live/channel0",
            'sub': f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/live/channel1"
        }
        
        # URLs de snapshot ONVIF (basado en nuestras pruebas)
        self.snapshot_urls = {
            'main': f"http://{self.camera_ip}:{self.onvif_port}/snapshot/PROFILE_395207",
            'sub': f"http://{self.camera_ip}:{self.onvif_port}/snapshot/PROFILE_395208"
        }
        
        self.current_stream_type = 'main'
        self.stream_qualities = {
            'main': 'Ultra HD (2560x1440) - HEVC',
            'sub': 'Standard (640x360) - H264'
        }
        
        # Configuración de tokens ONVIF (descubiertos en nuestras pruebas)
        self.onvif_tokens = {
            'main': 'PROFILE_395207',
            'sub': 'PROFILE_395208'
        }
        
        # Características específicas de Steren
        self.device_info = {
            'manufacturer': 'Happytimesoft',
            'model': 'IPCamera',
            'brand': 'Steren',
            'model_number': 'CCTV-235'
        }
        
        # Estado de conexiones
        self.rtsp_connection = None
        self.onvif_camera = None
        self.onvif_media_service = None
        
    def connect(self) -> bool:
        """
        Establece la conexión con la cámara Steren.
        Intenta primero ONVIF para control completo, luego RTSP para streaming.
        
        Returns:
            True si al menos una conexión fue exitosa
        """
        success = False
        
        # Intentar conexión ONVIF primero
        if self._establish_onvif_connection():
            self.logger.info("✅ Conexión ONVIF Steren establecida")
            success = True
        
        # Intentar conexión RTSP para streaming
        if self._establish_rtsp_connection():
            self.logger.info("✅ Conexión RTSP Steren establecida")
            success = True
        
        if success:
            self.is_connected = True
            self._log_connection_summary()
        
        return success
    
    def disconnect(self) -> bool:
        """
        Cierra todas las conexiones con la cámara Steren.
        
        Returns:
            True si se desconectó correctamente
        """
        try:
            self._close_rtsp_connection()
            self._close_onvif_connection()
            self.is_connected = False
            self.logger.info("🔌 Conexión Steren cerrada completamente")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error desconectando Steren: {e}")
            return False
    
    def is_alive(self) -> bool:
        """
        Verifica si al menos una conexión está activa.
        
        Returns:
            True si alguna conexión está activa
        """
        if not self.is_connected:
            return False
        
        # Verificar RTSP
        rtsp_alive = False
        if self.rtsp_connection:
            try:
                ret, _ = self.rtsp_connection.read()
                rtsp_alive = ret
            except:
                pass
        
        # Verificar ONVIF
        onvif_alive = False
        if self.onvif_camera:
            try:
                # Hacer una consulta simple para verificar ONVIF
                device_service = self.onvif_camera.create_devicemgmt_service()
                device_service.GetDeviceInformation()
                onvif_alive = True
            except:
                pass
        
        return rtsp_alive or onvif_alive
    
    def get_frame(self) -> Optional[cv2.Mat]:
        """
        Obtiene un frame del stream RTSP actual.
        
        Returns:
            Frame de video en formato OpenCV o None si hay error
        """
        if not self.rtsp_connection:
            return None
        
        try:
            ret, frame = self.rtsp_connection.read()
            
            if ret and frame is not None:
                return frame
            else:
                self.logger.warning("⚠️ Frame vacío recibido de Steren")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo frame Steren: {e}")
            return None
    
    def _establish_onvif_connection(self) -> bool:
        """
        Establece la conexión ONVIF con la cámara Steren.
        
        Returns:
            True si la conexión ONVIF fue exitosa
        """
        if not ONVIF_AVAILABLE:
            self.logger.warning("⚠️ ONVIF no disponible - funcionalidad limitada")
            return False
        
        try:
            self.logger.info(f"Conectando ONVIF Steren en {self.camera_ip}:{self.onvif_port}...")
            
            # Crear conexión ONVIF
            self.onvif_camera = ONVIFCamera(
                self.camera_ip, 
                self.onvif_port, 
                self.username, 
                self.password
            )
            
            # Verificar conexión obteniendo info del dispositivo
            device_service = self.onvif_camera.create_devicemgmt_service()
            device_info = device_service.GetDeviceInformation()
            
            # Crear servicio de media
            self.onvif_media_service = self.onvif_camera.create_media_service()
            
            self.logger.info(f"✅ ONVIF Steren conectado:")
            self.logger.info(f"   Fabricante: {device_info.Manufacturer}")
            self.logger.info(f"   Modelo: {device_info.Model}")
            self.logger.info(f"   Firmware: {device_info.FirmwareVersion}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error conexión ONVIF Steren: {e}")
            self.onvif_camera = None
            self.onvif_media_service = None
            return False
    
    def _establish_rtsp_connection(self) -> bool:
        """
        Establece la conexión RTSP con la cámara Steren.
        
        Returns:
            True si la conexión RTSP fue exitosa
        """
        try:
            # Intentar conectar con stream principal primero, luego sub
            for stream_type, url in self.stream_urls.items():
                self.logger.info(f"Intentando RTSP Steren stream '{stream_type}'...")
                
                cap = cv2.VideoCapture(url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    # Probar leer un frame
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        self.rtsp_connection = cap
                        self.current_stream_type = stream_type
                        
                        # Obtener información del stream
                        height, width = frame.shape[:2]
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        self.logger.info(f"✅ RTSP Steren conectado:")
                        self.logger.info(f"   Stream: {self.stream_qualities[stream_type]}")
                        self.logger.info(f"   Resolución: {width}x{height}")
                        self.logger.info(f"   FPS: {fps}")
                        
                        return True
                    else:
                        cap.release()
                else:
                    cap.release()
            
            self.logger.error("❌ No se pudo establecer conexión RTSP Steren")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error estableciendo conexión RTSP Steren: {e}")
            return False
    
    def _close_rtsp_connection(self) -> None:
        """Cierra la conexión RTSP activa."""
        if self.rtsp_connection:
            self.rtsp_connection.release()
            self.rtsp_connection = None
    
    def _close_onvif_connection(self) -> None:
        """Cierra la conexión ONVIF activa."""
        self.onvif_camera = None
        self.onvif_media_service = None
    
    def _log_connection_summary(self) -> None:
        """Registra un resumen del estado de las conexiones."""
        onvif_status = "✅" if self.onvif_camera else "❌"
        rtsp_status = "✅" if self.rtsp_connection else "❌"
        
        self.logger.info(f"📊 Estado conexiones Steren:")
        self.logger.info(f"   ONVIF: {onvif_status}")
        self.logger.info(f"   RTSP: {rtsp_status}")
        self.logger.info(f"   Stream activo: {self.stream_qualities[self.current_stream_type]}")
    
    def capture_snapshot(self, filename: str) -> bool:
        """
        Captura un snapshot usando el método más apropiado disponible.
        Prioriza ONVIF sobre captura de frame RTSP.
        
        Args:
            filename: Nombre del archivo donde guardar el snapshot
            
        Returns:
            True si el snapshot fue guardado exitosamente
        """
        # Intentar captura vía ONVIF primero (mejor calidad)
        if self.onvif_media_service:
            try:
                snapshot_uri = self.onvif_media_service.GetSnapshotUri({
                    'ProfileToken': self.onvif_tokens[self.current_stream_type]
                })
                
                # Descargar imagen vía HTTP
                import requests
                response = requests.get(
                    snapshot_uri.Uri,
                    auth=(self.username, self.password),
                    timeout=10
                )
                
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    self.logger.info(f"📸 Snapshot ONVIF Steren guardado: {filename}")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Falló snapshot ONVIF, intentando RTSP: {e}")
        
        # Fallback: captura de frame RTSP
        frame = self.get_frame()
        if frame is not None:
            try:
                success = cv2.imwrite(filename, frame)
                if success:
                    self.logger.info(f"📸 Snapshot RTSP Steren guardado: {filename}")
                    return True
                    
            except Exception as e:
                self.logger.error(f"❌ Error guardando snapshot RTSP: {e}")
        
        self.logger.error(f"❌ No se pudo capturar snapshot Steren: {filename}")
        return False
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada del stream actual.
        
        Returns:
            Diccionario con información del stream
        """
        info = {
            'brand': 'Steren',
            'model': 'CCTV-235',
            'current_stream': self.current_stream_type,
            'quality': self.stream_qualities[self.current_stream_type],
            'rtsp_url': self.stream_urls[self.current_stream_type],
            'snapshot_url': self.snapshot_urls[self.current_stream_type],
            'onvif_token': self.onvif_tokens[self.current_stream_type],
            'connections': {
                'onvif': self.onvif_camera is not None,
                'rtsp': self.rtsp_connection is not None
            }
        }
        
        # Agregar información técnica si tenemos conexión RTSP
        if self.rtsp_connection:
            try:
                width = int(self.rtsp_connection.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.rtsp_connection.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = self.rtsp_connection.get(cv2.CAP_PROP_FPS)
                
                info.update({
                    'resolution': f"{width}x{height}",
                    'width': width,
                    'height': height,
                    'fps': fps
                })
            except:
                pass
        
        return info
    
    def switch_stream_quality(self, quality: str) -> bool:
        """
        Cambia entre stream principal y secundario.
        
        Args:
            quality: 'main' para stream principal, 'sub' para secundario
            
        Returns:
            True si el cambio fue exitoso
        """
        if quality not in ['main', 'sub']:
            self.logger.error(f"❌ Calidad no válida: {quality}. Use 'main' o 'sub'")
            return False
        
        if quality == self.current_stream_type:
            self.logger.info(f"ℹ️ Ya está usando stream '{quality}'")
            return True
        
        # Cerrar conexión actual
        self._close_rtsp_connection()
        
        # Conectar con nueva calidad
        self.current_stream_type = quality
        
        if self._establish_rtsp_connection():
            self.logger.info(f"✅ Cambiado a stream Steren '{quality}'")
            return True
        else:
            self.logger.error(f"❌ Error cambiando a stream '{quality}'")
            return False
    
    def get_available_streams(self) -> List[Dict[str, str]]:
        """
        Obtiene lista de streams disponibles.
        
        Returns:
            Lista de diccionarios con información de streams
        """
        streams = []
        for stream_type, description in self.stream_qualities.items():
            streams.append({
                'type': stream_type,
                'description': description,
                'url': self.stream_urls[stream_type],
                'token': self.onvif_tokens[stream_type]
            })
        
        return streams
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión con la cámara Steren.
        
        Returns:
            Tupla (éxito, mensaje_descripción)
        """
        try:
            # Probar ONVIF
            onvif_ok = self._establish_onvif_connection()
            if onvif_ok:
                self._close_onvif_connection()
            
            # Probar RTSP
            rtsp_ok = self._establish_rtsp_connection()
            if rtsp_ok:
                self._close_rtsp_connection()
            
            if onvif_ok and rtsp_ok:
                return True, "✅ Conexión Steren completa (ONVIF + RTSP)"
            elif rtsp_ok:
                return True, "⚠️ Conexión Steren parcial (solo RTSP)"
            elif onvif_ok:
                return True, "⚠️ Conexión Steren parcial (solo ONVIF)"
            else:
                return False, "❌ No se pudo conectar a Steren"
                
        except Exception as e:
            return False, f"❌ Error probando conexión Steren: {str(e)}"
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Obtiene información del dispositivo Steren.
        
        Returns:
            Diccionario con información del dispositivo
        """
        info = self.device_info.copy()
        info.update({
            'ip': self.camera_ip,
            'onvif_port': self.onvif_port,
            'rtsp_port': self.rtsp_port,
            'username': self.username,
            'connected': self.is_connected,
            'available_streams': len(self.stream_urls),
            'current_stream': self.current_stream_type
        })
        
        # Agregar información ONVIF si está disponible
        if self.onvif_camera:
            try:
                device_service = self.onvif_camera.create_devicemgmt_service()
                device_info = device_service.GetDeviceInformation()
                
                info.update({
                    'firmware': device_info.FirmwareVersion,
                    'serial': device_info.SerialNumber,
                    'hardware_id': getattr(device_info, 'HardwareId', 'N/A')
                })
            except:
                pass
        
        return info
    
    def ptz_move(self, direction: str, speed: float = 0.5) -> bool:
        """
        Controla movimiento PTZ (si está disponible vía ONVIF).
        
        Args:
            direction: Dirección del movimiento ('up', 'down', 'left', 'right', 'stop')
            speed: Velocidad del movimiento (0.0 a 1.0)
            
        Returns:
            True si el comando fue enviado exitosamente
        """
        if not self.onvif_camera:
            self.logger.warning("⚠️ PTZ requiere conexión ONVIF")
            return False
        
        try:
            ptz_service = self.onvif_camera.create_ptz_service()
            
            # Mapeo de direcciones
            direction_map = {
                'up': (0, speed, 0),
                'down': (0, -speed, 0),
                'left': (-speed, 0, 0),
                'right': (speed, 0, 0),
                'stop': (0, 0, 0)
            }
            
            if direction not in direction_map:
                self.logger.error(f"❌ Dirección PTZ no válida: {direction}")
                return False
            
            x, y, z = direction_map[direction]
            
            # Enviar comando PTZ
            ptz_service.ContinuousMove({
                'ProfileToken': self.onvif_tokens[self.current_stream_type],
                'Velocity': {
                    'PanTilt': {'x': x, 'y': y},
                    'Zoom': {'x': z}
                }
            })
            
            self.logger.info(f"✅ Comando PTZ Steren enviado: {direction}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error PTZ Steren: {e}")
            return False