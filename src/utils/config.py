"""
Gestor de configuración para el módulo Dahua Visor.
Maneja la lectura y validación de variables de entorno.
"""

import os
from typing import Optional
from dotenv import load_dotenv


class ConfigurationManager:
    """
    Gestor centralizado de configuración del sistema.
    Implementa el patrón Singleton para mantener una única instancia.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """
        Implementa el patrón Singleton para la configuración.
        """
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa el gestor de configuración cargando las variables de entorno.
        """
        if not self._initialized:
            load_dotenv()
            self._load_camera_config()
            self._load_tplink_config()
            self._load_connection_config()
            self._load_logging_config()
            ConfigurationManager._initialized = True
    
    def _load_camera_config(self) -> None:
        """
        Carga la configuración específica de la cámara Dahua.
        """
        self.camera_ip = os.getenv("CAMERA_IP", "192.168.1.100")
        self.camera_user = os.getenv("CAMERA_USER", "admin")
        self.camera_password = os.getenv("CAMERA_PASSWORD", "")
        
        # No requerir contraseña obligatoriamente para permitir múltiples marcas
        if not self.camera_password:
            self.camera_password = ""
    
    def _load_tplink_config(self) -> None:
        """
        Carga la configuración específica de la cámara TP-Link.
        """
        self.tplink_ip = os.getenv("TP_LINK_IP", "192.168.1.77")
        self.tplink_user = os.getenv("TP_LINK_USER", "admin")
        self.tplink_password = os.getenv("TP_LINK_PASSWORD", "")
    
    def _load_connection_config(self) -> None:
        """
        Carga la configuración de puertos y conexiones.
        """
        self.rtsp_port = int(os.getenv("RTSP_PORT", "554"))
        self.http_port = int(os.getenv("HTTP_PORT", "80"))
        self.onvif_port = int(os.getenv("ONVIF_PORT", "80"))
        self.sdk_port = int(os.getenv("SDK_PORT", "37777"))
        
        self.rtsp_channel = int(os.getenv("RTSP_CHANNEL", "1"))
        self.rtsp_subtype = int(os.getenv("RTSP_SUBTYPE", "0"))
        
        self.onvif_wsdl_path = os.getenv("ONVIF_WSDL_PATH", "./sdk/wsdl")
    
    def _load_logging_config(self) -> None:
        """
        Carga la configuración de logging del sistema.
        """
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "dahua-visor.log")
    
    def get_rtsp_url(self, camera_brand: str = "dahua") -> str:
        """
        Construye la URL RTSP completa para la conexión según la marca.
        
        Args:
            camera_brand: Marca de la cámara ("dahua" o "tplink")
            
        Returns:
            URL RTSP formateada con credenciales y parámetros
        """
        if camera_brand.lower() == "tplink":
            return (f"rtsp://{self.tplink_user}:{self.tplink_password}@"
                    f"{self.tplink_ip}:{self.rtsp_port}/stream1")
        else:  # dahua por defecto
            return (f"rtsp://{self.camera_user}:{self.camera_password}@"
                    f"{self.camera_ip}:{self.rtsp_port}/cam/realmonitor?"
                    f"channel={self.rtsp_channel}&subtype={self.rtsp_subtype}")
    
    def get_camera_credentials(self, camera_brand: str = "dahua") -> dict:
        """
        Obtiene las credenciales de la cámara según la marca.
        
        Args:
            camera_brand: Marca de la cámara ("dahua" o "tplink")
            
        Returns:
            Diccionario con usuario y contraseña
        """
        if camera_brand.lower() == "tplink":
            return {
                "username": self.tplink_user,
                "password": self.tplink_password,
                "ip": self.tplink_ip
            }
        else:  # dahua por defecto
            return {
                "username": self.camera_user,
                "password": self.camera_password,
                "ip": self.camera_ip
            }
    
    def get_available_cameras(self) -> list:
        """
        Obtiene la lista de cámaras configuradas disponibles.
        
        Returns:
            Lista de diccionarios con información de cámaras disponibles
        """
        cameras = []
        
        # Verificar Dahua
        if self.camera_password and self.camera_ip:
            cameras.append({
                "brand": "dahua",
                "model": "Hero-K51H",
                "name": "Dahua Hero-K51H",
                "ip": self.camera_ip,
                "user": self.camera_user,
                "protocols": ["rtsp", "amcrest", "onvif"]
            })
        
        # Verificar TP-Link
        if self.tplink_password and self.tplink_ip:
            cameras.append({
                "brand": "tplink",
                "model": "Tapo C520WS",
                "name": "TP-Link Tapo C520WS",
                "ip": self.tplink_ip,
                "user": self.tplink_user,
                "protocols": ["rtsp"]
            })
        
        return cameras
    
    def validate_configuration(self) -> bool:
        """
        Valida que la configuración esté completa y sea válida.
        
        Returns:
            True si la configuración es válida, False en caso contrario
        """
        required_fields = [
            self.camera_ip,
            self.camera_user,
            self.camera_password
        ]
        
        return all(field for field in required_fields)


def get_config() -> ConfigurationManager:
    """
    Función helper para obtener la instancia de configuración.
    
    Returns:
        Instancia única del gestor de configuración
    """
    return ConfigurationManager() 