"""
Implementación de conexión HTTP/CGI para cámaras Dahua usando requests directamente.
Proporciona funcionalidades de snapshot, stream MJPEG y controles PTZ.
"""

import io
import time
from typing import Optional, Dict, Any, Union
import numpy as np
from PIL import Image
import requests
from requests.auth import HTTPDigestAuth
from .base_connection import BaseConnection


class AmcrestConnection(BaseConnection):
    """
    Implementación concreta de conexión HTTP/CGI usando requests directamente.
    Hereda de BaseConnection e implementa funcionalidades web específicas de Dahua.
    """
    
    def __init__(self, config_manager):
        """
        Inicializa la conexión HTTP con configuración.
        
        Args:
            config_manager: Instancia del gestor de configuración
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("AmcrestConnection")
        
        # Configuración específica HTTP
        self.camera_ip = getattr(config_manager, 'camera_ip', '192.168.1.172')
        self.username = getattr(config_manager, 'camera_user', 'admin')
        self.password = getattr(config_manager, 'camera_password', '')
        self.port = getattr(config_manager, 'http_port', 80)
        self.timeout = getattr(config_manager, 'timeout', 10)
        self.base_url = f"http://{self.camera_ip}:{self.port}"
        self.auth = HTTPDigestAuth(self.username, self.password)
        
    def connect(self) -> bool:
        """
        Establece la conexión HTTP con la cámara usando requests.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
            
        Raises:
            ConnectionError: Si no se puede establecer la conexión
        """
        try:
            if not self.username or not self.password:
                self.logger.error("Credenciales inválidas para conexión HTTP")
                return False
            
            self.logger.info(f"Intentando conectar HTTP a {self.camera_ip}:{self.port}")
            
            # Crear sesión HTTP con autenticación Digest
            self.connection_handle = requests.Session()
            self.connection_handle.auth = self.auth
            self.connection_handle.timeout = self.timeout
            
            # Verificar conexión obteniendo información del dispositivo
            device_info = self._test_connection()
            if device_info:
                self.is_connected = True
                self.logger.info(f"Conexión HTTP establecida exitosamente a {self.camera_ip}")
                self.logger.info(f"Dispositivo: {device_info.get('deviceType', 'Unknown')}")
                return True
            else:
                self.logger.error("No se pudo verificar la conexión con la cámara")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al conectar HTTP: {str(e)}")
            self._cleanup_connection()
            return False
    
    def disconnect(self) -> bool:
        """
        Cierra la conexión HTTP.
        
        Returns:
            True si se desconectó correctamente, False en caso contrario
        """
        try:
            # Cerrar sesión HTTP
            if self.connection_handle:
                self.connection_handle.close()
            self.connection_handle = None
            self.is_connected = False
            self.logger.info(f"Conexión HTTP cerrada para {self.camera_ip}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al desconectar HTTP: {str(e)}")
            return False
    
    def is_alive(self) -> bool:
        """
        Verifica si la conexión HTTP está activa.
        
        Returns:
            True si la conexión está activa, False en caso contrario
        """
        if not self.is_connected or self.connection_handle is None:
            return False
        
        try:
            # Hacer una petición ligera para verificar conectividad
            response = self.connection_handle.get(
                f"{self.base_url}/cgi-bin/magicBox.cgi?action=getMachineName",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Conexión HTTP no está activa: {str(e)}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Obtiene un snapshot (frame estático) de la cámara vía HTTP.
        
        Returns:
            Array numpy con el frame BGR, None si no se puede obtener
        """
        if not self.is_alive():
            self.logger.warning("Intentando obtener frame sin conexión activa")
            return None
        
        try:
            self.logger.debug("Capturando snapshot vía HTTP")
            
            # Obtener snapshot usando CGI directo
            snapshot_url = f"{self.base_url}/cgi-bin/snapshot.cgi?channel=0"
            response = self.connection_handle.get(snapshot_url, timeout=self.timeout)
            
            if response.status_code == 200 and response.content:
                # Convertir datos binarios a imagen PIL
                image = Image.open(io.BytesIO(response.content))
                
                # Convertir PIL a array numpy (RGB -> BGR para OpenCV)
                frame_rgb = np.array(image)
                if len(frame_rgb.shape) == 3:
                    frame_bgr = frame_rgb[:, :, ::-1]  # RGB to BGR
                    self.logger.debug(f"Snapshot capturado - Shape: {frame_bgr.shape}")
                    return frame_bgr
                else:
                    self.logger.warning("Formato de imagen no soportado")
                    return None
            else:
                self.logger.warning(f"Error HTTP {response.status_code} al obtener snapshot")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al obtener snapshot HTTP: {str(e)}")
            return None
    
    def save_snapshot(self, filename: str, channel: int = 0) -> bool:
        """
        Captura y guarda un snapshot directamente desde la cámara.
        
        Args:
            filename: Nombre del archivo donde guardar la imagen
            channel: Canal de la cámara (por defecto 0)
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not self.is_alive():
            self.logger.error("No hay conexión activa para snapshot")
            return False
        
        try:
            self.logger.info(f"Guardando snapshot en {filename}")
            
            # Obtener snapshot usando CGI directo
            snapshot_url = f"{self.base_url}/cgi-bin/snapshot.cgi?channel={channel}"
            response = self.connection_handle.get(snapshot_url, timeout=self.timeout)
            
            if response.status_code == 200 and response.content:
                # Guardar imagen directamente
                with open(filename, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Snapshot guardado exitosamente como {filename}")
                return True
            else:
                self.logger.error(f"Error HTTP {response.status_code} al obtener snapshot")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al guardar snapshot: {str(e)}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa del dispositivo.
        
        Returns:
            Diccionario con información del dispositivo
        """
        if not self.is_alive():
            return {}
        
        try:
            device_info = {}
            
            # Obtener información usando diferentes endpoints CGI
            info_endpoints = {
                "machine_name": "/cgi-bin/magicBox.cgi?action=getMachineName",
                "device_type": "/cgi-bin/magicBox.cgi?action=getDeviceType", 
                "serial_number": "/cgi-bin/magicBox.cgi?action=getSerialNo",
                "software_version": "/cgi-bin/magicBox.cgi?action=getSoftwareVersion",
                "hardware_version": "/cgi-bin/magicBox.cgi?action=getHardwareVersion",
                "system_info": "/cgi-bin/magicBox.cgi?action=getSystemInfo"
            }
            
            for key, endpoint in info_endpoints.items():
                try:
                    response = self.connection_handle.get(
                        f"{self.base_url}{endpoint}", 
                        timeout=5
                    )
                    if response.status_code == 200:
                        # Parsear respuesta CGI (formato: key=value)
                        content = response.text.strip()
                        if '=' in content:
                            device_info[key] = content.split('=', 1)[1]
                        else:
                            device_info[key] = content
                    else:
                        device_info[key] = "N/A"
                except Exception:
                    device_info[key] = "Error"
            
            self.logger.debug("Información del dispositivo obtenida exitosamente")
            return device_info
            
        except Exception as e:
            self.logger.error(f"Error al obtener información del dispositivo: {str(e)}")
            return {}
    
    def ptz_control(self, action: str, speed: int = 3) -> bool:
        """
        Controla movimientos PTZ de la cámara.
        
        Args:
            action: Acción PTZ ('up', 'down', 'left', 'right', 'zoom_in', 'zoom_out', 'stop')
            speed: Velocidad del movimiento (1-8, por defecto 3)
            
        Returns:
            True si el comando fue enviado exitosamente, False en caso contrario
        """
        if not self.is_alive():
            self.logger.error("No hay conexión activa para control PTZ")
            return False
        
        try:
            self.logger.info(f"Ejecutando comando PTZ: {action} con velocidad {speed}")
            
            # Mapear acciones a comandos CGI
            ptz_commands = {
                'up': f"/cgi-bin/ptz.cgi?action=start&code=Up&channel=0&arg1=0&arg2={speed}&arg3=0",
                'down': f"/cgi-bin/ptz.cgi?action=start&code=Down&channel=0&arg1=0&arg2={speed}&arg3=0",
                'left': f"/cgi-bin/ptz.cgi?action=start&code=Left&channel=0&arg1=0&arg2={speed}&arg3=0",
                'right': f"/cgi-bin/ptz.cgi?action=start&code=Right&channel=0&arg1=0&arg2={speed}&arg3=0",
                'zoom_in': f"/cgi-bin/ptz.cgi?action=start&code=ZoomTele&channel=0&arg1=0&arg2={speed}&arg3=0",
                'zoom_out': f"/cgi-bin/ptz.cgi?action=start&code=ZoomWide&channel=0&arg1=0&arg2={speed}&arg3=0",
                'stop': f"/cgi-bin/ptz.cgi?action=stop&code=Up&channel=0&arg1=0&arg2={speed}&arg3=0"
            }
            
            if action.lower() in ptz_commands:
                ptz_url = f"{self.base_url}{ptz_commands[action.lower()]}"
                response = self.connection_handle.get(ptz_url, timeout=self.timeout)
                
                if response.status_code == 200:
                    self.logger.info(f"Comando PTZ {action} ejecutado exitosamente")
                    return True
                else:
                    self.logger.warning(f"Comando PTZ {action} falló - HTTP {response.status_code}")
                    return False
            else:
                self.logger.error(f"Acción PTZ no soportada: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en control PTZ: {str(e)}")
            return False
    
    def set_preset(self, preset_id: int, name: str = "") -> bool:
        """
        Establece un preset PTZ en la posición actual.
        
        Args:
            preset_id: ID del preset (1-255)
            name: Nombre opcional del preset
            
        Returns:
            True si se estableció exitosamente, False en caso contrario
        """
        if not self.is_alive():
            self.logger.error("No hay conexión activa para establecer preset")
            return False
        
        try:
            self.logger.info(f"Estableciendo preset {preset_id}: {name}")
            
            preset_url = f"{self.base_url}/cgi-bin/ptz.cgi?action=start&code=SetPreset&channel=0&arg1={preset_id}&arg2=0&arg3=0"
            response = self.connection_handle.get(preset_url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.info(f"Preset {preset_id} establecido exitosamente")
                return True
            else:
                self.logger.error(f"Error al establecer preset {preset_id} - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al establecer preset: {str(e)}")
            return False
    
    def goto_preset(self, preset_id: int) -> bool:
        """
        Mueve la cámara a un preset establecido.
        
        Args:
            preset_id: ID del preset a ir (1-255)
            
        Returns:
            True si se movió exitosamente, False en caso contrario
        """
        if not self.is_alive():
            self.logger.error("No hay conexión activa para ir a preset")
            return False
        
        try:
            self.logger.info(f"Moviendo a preset {preset_id}")
            
            preset_url = f"{self.base_url}/cgi-bin/ptz.cgi?action=start&code=GotoPreset&channel=0&arg1={preset_id}&arg2=0&arg3=0"
            response = self.connection_handle.get(preset_url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.info(f"Movimiento a preset {preset_id} exitoso")
                return True
            else:
                self.logger.error(f"Error al ir a preset {preset_id} - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al ir a preset: {str(e)}")
            return False
    
    def get_mjpeg_stream_url(self, channel: int = 0, subtype: int = 0) -> str:
        """
        Construye la URL para stream MJPEG.
        
        Args:
            channel: Canal de la cámara
            subtype: Subtipo de stream
            
        Returns:
            URL del stream MJPEG
        """
        username = self.credentials.get("username", "")
        password = self.credentials.get("password", "")
        
        mjpeg_url = (f"http://{username}:{password}@{self.camera_ip}:{self.port}/"
                    f"cgi-bin/mjpg/video.cgi?channel={channel}&subtype={subtype}")
        
        self.logger.debug(f"URL MJPEG generada para canal {channel}")
        return mjpeg_url
    
    def _test_connection(self) -> Optional[Dict[str, Any]]:
        """
        Prueba la conexión obteniendo información básica del dispositivo.
        Método privado para validación interna.
        
        Returns:
            Diccionario con información básica o None si falla
        """
        try:
            # Intentar obtener información básica del dispositivo
            machine_name_response = self.connection_handle.get(
                f"{self.base_url}/cgi-bin/magicBox.cgi?action=getMachineName",
                timeout=5
            )
            
            device_type_response = self.connection_handle.get(
                f"{self.base_url}/cgi-bin/magicBox.cgi?action=getDeviceType",
                timeout=5
            )
            
            if machine_name_response.status_code == 200:
                machine_name = machine_name_response.text.strip()
                if '=' in machine_name:
                    machine_name = machine_name.split('=', 1)[1]
                
                device_type = "Unknown"
                if device_type_response.status_code == 200:
                    device_type = device_type_response.text.strip()
                    if '=' in device_type:
                        device_type = device_type.split('=', 1)[1]
                
                return {
                    "deviceType": device_type,
                    "machineName": machine_name
                }
            else:
                return None
            
        except Exception as e:
            self.logger.error(f"Error en prueba de conexión: {str(e)}")
            return None
    
    def _cleanup_connection(self) -> None:
        """
        Limpia recursos de conexión en caso de error.
        Método privado para manejo interno de errores.
        """
        self.connection_handle = None
        self.is_connected = False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Extiende la información base con detalles específicos de Amcrest.
        
        Returns:
            Diccionario con información completa de la conexión Amcrest
        """
        base_info = super().get_connection_info()
        amcrest_info = {
            "port": self.port,
            "timeout": self.timeout,
            "base_url": self.base_url,
            "mjpeg_url": self.get_mjpeg_stream_url() if self.is_alive() else "",
            "device_info": self.get_device_info() if self.is_alive() else {}
        }
        
        return {**base_info, **amcrest_info} 