"""
Configuración central de la aplicación.

Gestiona variables de entorno y configuraciones por defecto.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings:
    """Configuración de la aplicación."""
    
    # Configuración general
    APP_NAME: str = "Universal Camera Viewer"
    APP_VERSION: str = "0.9.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Configuración de API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Configuración de WebSocket
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_MAX_CONNECTIONS: int = int(os.getenv("WS_MAX_CONNECTIONS", "100"))
    
    # Configuración de streaming
    DEFAULT_FPS: int = int(os.getenv("DEFAULT_FPS", "30"))
    DEFAULT_QUALITY: str = os.getenv("DEFAULT_QUALITY", "medium")
    STREAM_BUFFER_SIZE: int = int(os.getenv("STREAM_BUFFER_SIZE", "5"))
    
    # Configuración de cámaras específicas
    # Dahua
    DAHUA_USERNAME: Optional[str] = os.getenv("DAHUA_USERNAME")
    DAHUA_PASSWORD: Optional[str] = os.getenv("DAHUA_PASSWORD")
    DAHUA_IP: Optional[str] = os.getenv("DAHUA_IP", "192.168.1.172")
    DAHUA_RTSP_PORT: int = int(os.getenv("DAHUA_RTSP_PORT", "554"))
    
    # Timeouts y reintentos
    CONNECTION_TIMEOUT: int = int(os.getenv("CONNECTION_TIMEOUT", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    
    # Rutas RTSP por marca
    RTSP_PATHS = {
        'dahua': os.getenv("DAHUA_RTSP_PATH", "/cam/realmonitor?channel=1&subtype=0"),
        'tp-link': os.getenv("TPLINK_RTSP_PATH", "/stream1"),
        'steren': os.getenv("STEREN_RTSP_PATH", "/Streaming/Channels/101"),
        'hikvision': os.getenv("HIKVISION_RTSP_PATH", "/Streaming/Channels/101"),
        'generic': os.getenv("GENERIC_RTSP_PATH", "/stream1")
    }
    
    # Configuración de base de datos
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/camera_data.db")
    
    # Configuración de caché
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutos
    
    # Feature flags
    ENABLE_MOCK_STREAMS: bool = os.getenv("ENABLE_MOCK_STREAMS", "True").lower() == "true"
    CHECK_CONNECTIVITY: bool = os.getenv("CHECK_CONNECTIVITY", "True").lower() == "true"
    
    def get_camera_config(self, brand: str = "dahua") -> dict:
        """
        Obtiene configuración para una marca de cámara.
        
        Args:
            brand: Marca de la cámara
            
        Returns:
            Diccionario con configuración
        """
        brand = brand.lower()
        
        if brand == "dahua":
            return {
                'username': self.DAHUA_USERNAME,
                'password': self.DAHUA_PASSWORD,
                'ip': self.DAHUA_IP,
                'rtsp_port': self.DAHUA_RTSP_PORT,
                'rtsp_path': self.RTSP_PATHS.get('dahua', '/stream1')
            }
        
        # Agregar más marcas según sea necesario
        return {}


# Instancia global de configuración
settings = Settings()