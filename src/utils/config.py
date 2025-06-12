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
            import logging
            logger = logging.getLogger("ConfigurationManager")
            logger.info("🔧 Inicializando ConfigurationManager...")
            
            load_dotenv()
            self._load_camera_config()
            self._load_tplink_config()
            self._load_steren_config()
            self._load_generic_config()
            self._load_connection_config()
            self._load_logging_config()
            
            logger.info("✅ ConfigurationManager inicializado")
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
    
    def _load_steren_config(self) -> None:
        """
        Carga la configuración específica de la cámara Steren (condicional).
        Solo se carga si las variables de entorno están definidas.
        """
        import logging
        logger = logging.getLogger("ConfigurationManager")
        
        steren_ip = os.getenv("STEREN_IP")
        if steren_ip:
            self.steren_ip = steren_ip
            self.steren_user = os.getenv("STEREN_USER", "admin")
            self.steren_password = os.getenv("STEREN_PASSWORD", "")
            self.steren_onvif_port = int(os.getenv("STEREN_ONVIF_PORT", "8000"))
            self.steren_rtsp_port = int(os.getenv("STEREN_RTSP_PORT", "5543"))
            logger.info(f"✅ Steren configurada desde .env: {self.steren_ip} (user: {self.steren_user})")
        else:
            # No configurar si no están las variables
            self.steren_ip = None
            self.steren_user = None
            self.steren_password = None
            self.steren_onvif_port = None
            self.steren_rtsp_port = None
            logger.debug("❌ Steren NO configurada - STEREN_IP no encontrada en .env")
    
    def _load_generic_config(self) -> None:
        """
        Carga la configuración específica de la cámara genérica (condicional).
        Solo se carga si las variables de entorno están definidas.
        """
        import logging
        logger = logging.getLogger("ConfigurationManager")
        
        generic_ip = os.getenv("GENERIC_IP")
        if generic_ip:
            self.generic_ip = generic_ip
            self.generic_user = os.getenv("GENERIC_USER", "admin")
            self.generic_password = os.getenv("GENERIC_PASSWORD", "")
            logger.info(f"✅ Generic configurada desde .env: {self.generic_ip} (user: {self.generic_user})")
        else:
            # No configurar si no están las variables
            self.generic_ip = None
            self.generic_user = None
            self.generic_password = None
            logger.debug("❌ Generic NO configurada - GENERIC_IP no encontrada en .env")
    
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
            camera_brand: Marca de la cámara ("dahua", "tplink", "steren", "generic")
            
        Returns:
            Diccionario con usuario y contraseña
        """
        if camera_brand.lower() == "tplink":
            return {
                "username": self.tplink_user,
                "password": self.tplink_password,
                "ip": self.tplink_ip
            }
        elif camera_brand.lower() == "steren":
            return {
                "username": self.steren_user if hasattr(self, 'steren_user') and self.steren_user else "admin",
                "password": self.steren_password if hasattr(self, 'steren_password') and self.steren_password else "",
                "ip": self.steren_ip if hasattr(self, 'steren_ip') and self.steren_ip else None
            }
        elif camera_brand.lower() == "generic":
            return {
                "username": self.generic_user if hasattr(self, 'generic_user') and self.generic_user else "admin",
                "password": self.generic_password if hasattr(self, 'generic_password') and self.generic_password else "",
                "ip": self.generic_ip if hasattr(self, 'generic_ip') and self.generic_ip else None
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
        import logging
        logger = logging.getLogger("ConfigurationManager")
        
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
            logger.debug(f"✅ Dahua configurada: {self.camera_ip}")
        
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
            logger.debug(f"✅ TP-Link configurada: {self.tplink_ip}")
        
        # Verificar Steren (condicional) - Solo requiere IP y usuario
        if hasattr(self, 'steren_ip') and self.steren_ip and hasattr(self, 'steren_user') and self.steren_user:
            cameras.append({
                "brand": "steren",
                "model": "CCTV-235",
                "name": "Steren CCTV-235",
                "ip": self.steren_ip,
                "user": self.steren_user,
                "protocols": ["rtsp", "onvif", "steren"]
            })
            logger.debug(f"✅ Steren configurada: {self.steren_ip}")
        else:
            logger.debug(f"❌ Steren NO configurada - IP: {getattr(self, 'steren_ip', 'None')}, User: {getattr(self, 'steren_user', 'None')}")
        
        # Verificar Generic (condicional) - Solo requiere IP y usuario
        if hasattr(self, 'generic_ip') and self.generic_ip and hasattr(self, 'generic_user') and self.generic_user:
            cameras.append({
                "brand": "generic",
                "model": "generic-rtsp",
                "name": "Cámara China Genérica",
                "ip": self.generic_ip,
                "user": self.generic_user,
                "protocols": ["rtsp", "generic", "custom"]
            })
            logger.debug(f"✅ Generic configurada: {self.generic_ip}")
        else:
            logger.debug(f"❌ Generic NO configurada - IP: {getattr(self, 'generic_ip', 'None')}, User: {getattr(self, 'generic_user', 'None')}")
        
        logger.info(f"📋 Cámaras disponibles encontradas: {len(cameras)}")
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
    
    def is_camera_configured(self, camera_brand: str) -> bool:
        """
        Verifica si una cámara específica está configurada en las variables de entorno.
        
        Args:
            camera_brand: Marca de la cámara a verificar
            
        Returns:
            True si la cámara está configurada, False en caso contrario
        """
        if camera_brand.lower() == "dahua":
            return bool(self.camera_ip and self.camera_user)
        elif camera_brand.lower() == "tplink":
            return bool(self.tplink_ip and self.tplink_user)
        elif camera_brand.lower() == "steren":
            return bool(hasattr(self, 'steren_ip') and self.steren_ip and 
                       hasattr(self, 'steren_user') and self.steren_user)
        elif camera_brand.lower() == "generic":
            return bool(hasattr(self, 'generic_ip') and self.generic_ip and 
                       hasattr(self, 'generic_user') and self.generic_user)
        
        return False
    
    def get_configured_camera_ips(self) -> dict:
        """
        Obtiene un diccionario con las IPs de todas las cámaras configuradas.
        
        Returns:
            Diccionario {marca: ip} de cámaras configuradas
        """
        configured_ips = {}
        
        if self.camera_ip:
            configured_ips['dahua'] = self.camera_ip
        if self.tplink_ip:
            configured_ips['tplink'] = self.tplink_ip
        if hasattr(self, 'steren_ip') and self.steren_ip:
            configured_ips['steren'] = self.steren_ip
        if hasattr(self, 'generic_ip') and self.generic_ip:
            configured_ips['generic'] = self.generic_ip
        
        return configured_ips


def get_config() -> ConfigurationManager:
    """
    Función helper para obtener la instancia de configuración.
    
    Returns:
        Instancia única del gestor de configuración
    """
    return ConfigurationManager() 