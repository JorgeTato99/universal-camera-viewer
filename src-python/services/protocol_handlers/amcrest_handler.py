"""
AmcrestHandler - Manejador de protocolo HTTP/CGI para cámaras Amcrest/Dahua.

Migra funcionalidad de AmcrestConnection (src_old) hacia la nueva arquitectura MVP
implementando HTTP/CGI, PTZ, snapshots y streaming MJPEG.
"""

import asyncio
import io
import logging
import time
from typing import Optional, Dict, Any, List
import numpy as np
from PIL import Image
import requests
from requests.auth import HTTPDigestAuth

from .base_handler import BaseHandler
from ..protocol_service import ConnectionState, ProtocolCapabilities, StreamingConfig
from ...models import ConnectionConfig


class AmcrestHandler(BaseHandler):
    """
    Manejador de protocolo HTTP/CGI para cámaras Amcrest/Dahua.
    
    Implementa funcionalidades completas de:
    - Snapshots vía HTTP/CGI
    - Streaming MJPEG 
    - Control PTZ completo (movimiento, presets)
    - Información de dispositivo
    - Compatibilidad con API antigua y nueva
    """
    
    # Comandos PTZ estándar Dahua/Amcrest
    PTZ_COMMANDS = {
        'up': "/cgi-bin/ptz.cgi?action=start&code=Up&channel=0&arg1=0&arg2={speed}&arg3=0",
        'down': "/cgi-bin/ptz.cgi?action=start&code=Down&channel=0&arg1=0&arg2={speed}&arg3=0",
        'left': "/cgi-bin/ptz.cgi?action=start&code=Left&channel=0&arg1=0&arg2={speed}&arg3=0",
        'right': "/cgi-bin/ptz.cgi?action=start&code=Right&channel=0&arg1=0&arg2={speed}&arg3=0",
        'zoom_in': "/cgi-bin/ptz.cgi?action=start&code=ZoomTele&channel=0&arg1=0&arg2={speed}&arg3=0",
        'zoom_out': "/cgi-bin/ptz.cgi?action=start&code=ZoomWide&channel=0&arg1=0&arg2={speed}&arg3=0",
        'stop': "/cgi-bin/ptz.cgi?action=stop&code=Up&channel=0&arg1=0&arg2={speed}&arg3=0"
    }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el handler Amcrest con compatibilidad dual.
        
        Formatos soportados:
        - Nuevo: AmcrestHandler(config: ConnectionConfig, streaming_config: StreamingConfig)
        - Antiguo: AmcrestHandler(camera_ip: str, credentials: dict)
        - Legacy: AmcrestHandler(config_manager)
        """
        super().__init__(*args, **kwargs)
        
        # Configuración específica HTTP/CGI
        self._setup_http_config()
        
        # Estado HTTP
        self.session: Optional[requests.Session] = None
        self.base_url: str = ""
        self.auth: Optional[HTTPDigestAuth] = None
        
        # Cache para optimización
        self._device_info_cache: Optional[Dict[str, Any]] = None
        self._mjpeg_url_cache: Optional[str] = None
    
    def _setup_http_config(self):
        """Configura parámetros específicos HTTP/CGI."""
        # Detectar configuración según API utilizada
        if hasattr(self, 'config') and self.config:
            # Nueva API
            self.ip = self.config.ip
            self.username = self.config.username
            self.password = self.config.password
            self.http_port = getattr(self.config, 'http_port', 80)
            self.timeout = getattr(self.config, 'timeout', 10)
        else:
            # API antigua/legacy - ya configurado en BaseHandler
            self.ip = self.camera_ip
            self.http_port = getattr(self, 'http_port', 80)
            self.timeout = getattr(self, 'timeout', 10)
        
        # Configurar URLs y autenticación
        self.base_url = f"http://{self.ip}:{self.http_port}"
        self.auth = HTTPDigestAuth(self.username, self.password)
    
    async def connect(self) -> bool:
        """
        Establece conexión HTTP/CGI con la cámara.
        
        Returns:
            True si la conexión fue exitosa
        """
        self._set_state(ConnectionState.CONNECTING)
        
        try:
            if not self.username or not self.password:
                self.logger.error("Credenciales inválidas para conexión HTTP")
                self._set_state(ConnectionState.ERROR)
                return False
            
            self.logger.info(f"Iniciando conexión HTTP a {self.ip}:{self.http_port}")
            
            # Crear sesión HTTP con autenticación Digest
            self.session = requests.Session()
            self.session.auth = self.auth
            # Configurar timeout por defecto a nivel de requests
            
            # Verificar conexión obteniendo información del dispositivo
            device_info = await self._test_connection()
            if device_info:
                self._device_info_cache = device_info
                self._set_state(ConnectionState.CONNECTED)
                self.logger.info(f"Conexión HTTP establecida: {device_info.get('deviceType', 'Unknown')}")
                return True
            else:
                self.logger.error("No se pudo verificar la conexión HTTP")
                self._set_state(ConnectionState.ERROR)
                return False
                
        except Exception as e:
            self.logger.error(f"Error de conexión HTTP: {str(e)}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    async def _test_connection(self) -> Optional[Dict[str, Any]]:
        """
        Prueba la conexión HTTP obteniendo información básica del dispositivo.
        
        Returns:
            Diccionario con información básica o None si falla
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Obtener información básica del dispositivo
            machine_name_response = await loop.run_in_executor(
                None,
                lambda: self.session.get(  # type: ignore
                    f"{self.base_url}/cgi-bin/magicBox.cgi?action=getMachineName",
                    timeout=5
                )
            )
            
            device_type_response = await loop.run_in_executor(
                None,
                lambda: self.session.get(  # type: ignore
                    f"{self.base_url}/cgi-bin/magicBox.cgi?action=getDeviceType",
                    timeout=5
                )
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
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error en prueba de conexión HTTP: {str(e)}")
            return None
    
    async def disconnect(self) -> bool:
        """
        Cierra la conexión HTTP.
        
        Returns:
            True si se desconectó correctamente
        """
        try:
            # Detener streaming si está activo
            if self.is_streaming:
                await self.stop_streaming()
            
            # Cerrar sesión HTTP
            if self.session:
                self.session.close()
                self.session = None
            
            # Limpiar cache
            self._device_info_cache = None
            self._mjpeg_url_cache = None
            
            self._set_state(ConnectionState.DISCONNECTED)
            self.logger.info("Conexión HTTP cerrada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cerrando conexión HTTP: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión HTTP sin establecerla permanentemente.
        
        Returns:
            True si la conexión es posible
        """
        try:
            # Crear sesión temporal
            temp_session = requests.Session()
            temp_session.auth = self.auth
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: temp_session.get(
                    f"{self.base_url}/cgi-bin/magicBox.cgi?action=getMachineName",
                    timeout=5
                )
            )
            
            temp_session.close()
            return response.status_code == 200
            
        except Exception as e:
            self.logger.debug(f"Test de conexión HTTP falló: {str(e)}")
            return False
    
    async def capture_snapshot(self) -> Optional[bytes]:
        """
        Captura un snapshot de la cámara vía HTTP/CGI.
        
        Returns:
            Datos de la imagen en bytes o None si falla
        """
        if not self.is_connected or not self.session:
            self.logger.error("Conexión HTTP no establecida")
            return None
        
        try:
            self.logger.debug("Capturando snapshot vía HTTP/CGI")
            
            # Obtener snapshot usando CGI directo
            snapshot_url = f"{self.base_url}/cgi-bin/snapshot.cgi?channel=0"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(snapshot_url, timeout=self.timeout)  # type: ignore
            )
            
            if response.status_code == 200 and response.content:
                self.logger.debug(f"Snapshot capturado - Tamaño: {len(response.content)} bytes")
                return response.content
            else:
                self.logger.warning(f"Error HTTP {response.status_code} al obtener snapshot")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturando snapshot HTTP: {str(e)}")
            return None
    
    async def start_streaming(self) -> bool:
        """
        Inicia el streaming MJPEG.
        
        Returns:
            True si el streaming se inició exitosamente
        """
        if self.is_streaming:
            return True
        
        if not self.is_connected:
            self.logger.error("Conexión HTTP no establecida para streaming")
            return False
        
        try:
            # El streaming MJPEG es principalmente bajo demanda
            # Solo marcamos como streaming disponible
            self._streaming_active = True
            self._set_state(ConnectionState.STREAMING)
            self.logger.info("Streaming MJPEG disponible")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando streaming MJPEG: {str(e)}")
            return False
    
    async def stop_streaming(self) -> bool:
        """
        Detiene el streaming MJPEG.
        
        Returns:
            True si el streaming se detuvo exitosamente
        """
        try:
            self._streaming_active = False
            self._set_state(ConnectionState.CONNECTED)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo streaming MJPEG: {str(e)}")
            return False
    
    def get_capabilities(self) -> ProtocolCapabilities:
        """Obtiene capacidades HTTP/CGI Amcrest."""
        return ProtocolCapabilities(
            supports_streaming=True,  # MJPEG streaming
            supports_snapshots=True,
            supports_ptz=True,  # PTZ completo
            supports_audio=False,
            max_resolution="1920x1080",
            supported_codecs=["MJPEG"]
        )
    
    # ==========================================
    # MÉTODOS ESPECÍFICOS AMCREST (Funcionalidad Principal)
    # ==========================================
    
    async def get_device_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información completa del dispositivo vía HTTP/CGI.
        
        Returns:
            Diccionario con información del dispositivo
        """
        # Usar cache si está disponible
        if self._device_info_cache:
            return self._device_info_cache.copy()
        
        if not self.is_connected or not self.session:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Obtener información extendida del dispositivo
            responses = await asyncio.gather(
                loop.run_in_executor(None, self._get_machine_name),
                loop.run_in_executor(None, self._get_device_type),
                loop.run_in_executor(None, self._get_software_version),
                return_exceptions=True
            )
            
            device_info = {}
            
            # Procesar respuestas
            if len(responses) >= 1 and not isinstance(responses[0], Exception):
                device_info['machineName'] = responses[0]
            
            if len(responses) >= 2 and not isinstance(responses[1], Exception):
                device_info['deviceType'] = responses[1]
            
            if len(responses) >= 3 and not isinstance(responses[2], Exception):
                device_info['softwareVersion'] = responses[2]
            
            # Cache para futuras consultas
            if device_info:
                self._device_info_cache = device_info
            
            return device_info if device_info else None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información del dispositivo: {str(e)}")
            return None
    
    def _get_machine_name(self) -> Optional[str]:
        """Obtiene el nombre de la máquina (método síncrono)."""
        try:
            if self.session:
                response = self.session.get(  # type: ignore
                    f"{self.base_url}/cgi-bin/magicBox.cgi?action=getMachineName",
                    timeout=5
                )
                if response.status_code == 200:
                    result = response.text.strip()
                    return result.split('=', 1)[1] if '=' in result else result
        except Exception:
            pass
        return None
    
    def _get_device_type(self) -> Optional[str]:
        """Obtiene el tipo de dispositivo (método síncrono)."""
        try:
            if self.session:
                response = self.session.get(  # type: ignore
                    f"{self.base_url}/cgi-bin/magicBox.cgi?action=getDeviceType",
                    timeout=5
                )
                if response.status_code == 200:
                    result = response.text.strip()
                    return result.split('=', 1)[1] if '=' in result else result
        except Exception:
            pass
        return None
    
    def _get_software_version(self) -> Optional[str]:
        """Obtiene la versión de software (método síncrono)."""
        try:
            if self.session:
                response = self.session.get(  # type: ignore
                    f"{self.base_url}/cgi-bin/magicBox.cgi?action=getSoftwareVersion",
                    timeout=5
                )
                if response.status_code == 200:
                    result = response.text.strip()
                    return result.split('=', 1)[1] if '=' in result else result
        except Exception:
            pass
        return None
    
    # ==========================================
    # CONTROL PTZ (Funcionalidad Avanzada)
    # ==========================================
    
    async def ptz_control(self, action: str, speed: int = 3) -> bool:
        """
        Controla movimientos PTZ de la cámara.
        
        Args:
            action: Acción PTZ ('up', 'down', 'left', 'right', 'zoom_in', 'zoom_out', 'stop')
            speed: Velocidad del movimiento (1-8, por defecto 3)
            
        Returns:
            True si el comando fue enviado exitosamente
        """
        if not self.is_connected or not self.session:
            self.logger.error("No hay conexión HTTP activa para control PTZ")
            return False
        
        try:
            self.logger.info(f"Ejecutando comando PTZ: {action} con velocidad {speed}")
            
            if action.lower() in self.PTZ_COMMANDS:
                ptz_url = f"{self.base_url}{self.PTZ_COMMANDS[action.lower()].format(speed=speed)}"
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.session.get(ptz_url, timeout=self.timeout)  # type: ignore
                )
                
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
    
    async def set_preset(self, preset_id: int, name: str = "") -> bool:
        """
        Establece un preset PTZ en la posición actual.
        
        Args:
            preset_id: ID del preset (1-255)
            name: Nombre opcional del preset
            
        Returns:
            True si se estableció exitosamente
        """
        if not self.is_connected or not self.session:
            self.logger.error("No hay conexión HTTP activa para establecer preset")
            return False
        
        try:
            self.logger.info(f"Estableciendo preset {preset_id}: {name}")
            
            preset_url = f"{self.base_url}/cgi-bin/ptz.cgi?action=start&code=SetPreset&channel=0&arg1={preset_id}&arg2=0&arg3=0"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(preset_url, timeout=self.timeout)  # type: ignore
            )
            
            if response.status_code == 200:
                self.logger.info(f"Preset {preset_id} establecido exitosamente")
                return True
            else:
                self.logger.error(f"Error al establecer preset {preset_id} - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al establecer preset: {str(e)}")
            return False
    
    async def goto_preset(self, preset_id: int) -> bool:
        """
        Mueve la cámara a un preset establecido.
        
        Args:
            preset_id: ID del preset a ir (1-255)
            
        Returns:
            True si se movió exitosamente
        """
        if not self.is_connected or not self.session:
            self.logger.error("No hay conexión HTTP activa para ir a preset")
            return False
        
        try:
            self.logger.info(f"Moviendo a preset {preset_id}")
            
            preset_url = f"{self.base_url}/cgi-bin/ptz.cgi?action=start&code=GotoPreset&channel=0&arg1={preset_id}&arg2=0&arg3=0"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(preset_url, timeout=self.timeout)  # type: ignore
            )
            
            if response.status_code == 200:
                self.logger.info(f"Movimiento a preset {preset_id} exitoso")
                return True
            else:
                self.logger.error(f"Error al ir a preset {preset_id} - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al ir a preset: {str(e)}")
            return False
    
    # ==========================================
    # STREAMING MJPEG (Funcionalidad de Video)
    # ==========================================
    
    def get_mjpeg_stream_url(self, channel: int = 0, subtype: int = 0) -> str:
        """
        Construye la URL para stream MJPEG.
        
        Args:
            channel: Canal de la cámara
            subtype: Subtipo de stream
            
        Returns:
            URL del stream MJPEG
        """
        if self._mjpeg_url_cache:
            return self._mjpeg_url_cache
        
        mjpeg_url = (f"http://{self.username}:{self.password}@{self.ip}:{self.http_port}/"
                    f"cgi-bin/mjpg/video.cgi?channel={channel}&subtype={subtype}")
        
        # Cache para futuras consultas
        self._mjpeg_url_cache = mjpeg_url
        self.logger.debug(f"URL MJPEG generada para canal {channel}")
        return mjpeg_url
    
    async def get_mjpeg_frame(self, channel: int = 0, subtype: int = 0) -> Optional[bytes]:
        """
        Obtiene un frame del stream MJPEG.
        
        Args:
            channel: Canal de la cámara
            subtype: Subtipo de stream
            
        Returns:
            Frame MJPEG en bytes o None si falla
        """
        if not self.is_connected or not self.session:
            return None
        
        try:
            mjpeg_url = f"{self.base_url}/cgi-bin/mjpg/video.cgi?channel={channel}&subtype={subtype}"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(mjpeg_url, timeout=self.timeout, stream=True)  # type: ignore
            )
            
            if response.status_code == 200:
                # Leer primer frame del stream MJPEG
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        # Buscar inicio de frame JPEG
                        if b'\xff\xd8' in chunk:  # JPEG header
                            response.close()
                            return chunk
            
            response.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo frame MJPEG: {str(e)}")
            return None
    
    # ==========================================
    # MÉTODOS DE COMPATIBILIDAD (API Antigua)
    # ==========================================
    
    def save_snapshot(self, filename: str, channel: int = 0) -> bool:
        """
        Versión síncrona de captura de snapshot para compatibilidad.
        
        Args:
            filename: Nombre del archivo donde guardar la imagen
            channel: Canal de la cámara
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Ejecutar captura async de forma síncrona
            loop = asyncio.get_event_loop()
            snapshot_data = loop.run_until_complete(self.capture_snapshot())
            
            if snapshot_data:
                with open(filename, 'wb') as f:
                    f.write(snapshot_data)
                self.logger.info(f"Snapshot guardado exitosamente como {filename}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error guardando snapshot: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Extiende la información base con detalles específicos de Amcrest.
        
        Returns:
            Diccionario con información completa de la conexión Amcrest
        """
        base_info = super().get_connection_info()
        amcrest_info = {
            "http_port": self.http_port,
            "timeout": self.timeout,
            "base_url": self.base_url,
            "mjpeg_url": self.get_mjpeg_stream_url() if self.is_connected else "",
            "device_info": self._device_info_cache or {},
            "supports_ptz": True
        }
        
        return {**base_info, **amcrest_info} 