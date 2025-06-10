"""
Clase base abstracta para todas las conexiones de cámara.
Implementa el patrón Template Method y define la interfaz común.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseConnection(ABC):
    """
    Clase abstracta base para todas las conexiones de cámara IP.
    Define la interfaz común y comportamientos compartidos.
    
    Implementa el principio de responsabilidad única (SRP) y
    el principio abierto/cerrado (OCP) de SOLID.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa la conexión base (compatible con múltiples APIs).
        
        Args:
            Múltiples formatos soportados para compatibilidad
        """
        self.is_connected = False
        self.connection_handle: Optional[Any] = None
        
        # Configurar logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Soporte para API antigua (camera_ip, credentials)
        if len(args) == 2 and isinstance(args[1], dict):
            self.camera_ip = args[0]
            self.credentials = args[1]
        # Soporte para nueva API (config_manager)
        elif len(args) == 1:
            self.config_manager = args[0]
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establece la conexión con la cámara.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
            
        Raises:
            ConnectionError: Si no se puede establecer la conexión
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Cierra la conexión con la cámara.
        
        Returns:
            True si se desconectó correctamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    def is_alive(self) -> bool:
        """
        Verifica si la conexión está activa.
        
        Returns:
            True si la conexión está activa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[Any]:
        """
        Obtiene un frame/imagen de la cámara.
        
        Returns:
            Frame de video o imagen, None si no se puede obtener
        """
        pass
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el estado de la conexión.
        
        Returns:
            Diccionario con información de la conexión
        """
        # Compatibilidad con ambas APIs
        if hasattr(self, 'camera_ip'):
            camera_ip = self.camera_ip
            username = self.credentials.get("username", "") if hasattr(self, 'credentials') else ""
        else:
            camera_ip = getattr(self, 'config_manager', None)
            username = ""
            
        return {
            "camera_ip": camera_ip,
            "is_connected": self.is_connected,
            "connection_type": self.__class__.__name__,
            "username": username
        }
    
    def validate_credentials(self) -> bool:
        """
        Valida que las credenciales estén completas.
        
        Returns:
            True si las credenciales son válidas, False en caso contrario
        """
        if hasattr(self, 'credentials'):
            required_fields = ["username", "password"]
            return all(field in self.credentials and self.credentials[field] 
                      for field in required_fields)
        return True  # Las conexiones nuevas manejan la validación internamente
    
    def __enter__(self):
        """
        Soporte para context manager - establece conexión.
        """
        camera_ip = getattr(self, 'camera_ip', 'unknown')
        if not self.connect():
            raise ConnectionError(f"No se pudo conectar a la cámara {camera_ip}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Soporte para context manager - cierra conexión.
        """
        self.disconnect()
    
    def __str__(self) -> str:
        """
        Representación en string de la conexión.
        """
        camera_ip = getattr(self, 'camera_ip', 'unknown')
        status = "conectado" if self.is_connected else "desconectado"
        return f"{self.__class__.__name__}({camera_ip}) - {status}"


class ConnectionFactory:
    """
    Factory para crear diferentes tipos de conexiones.
    Implementa el patrón Factory Method.
    """
    
    @staticmethod
    def create_connection(connection_type: str, config_manager, 
                         camera_brand: str = "dahua") -> BaseConnection:
        """
        Crea una instancia de conexión del tipo especificado.
        
        Args:
            connection_type: Tipo de conexión ('rtsp', 'onvif', 'amcrest', 'tplink', 'steren')
            config_manager: Instancia del gestor de configuración
            camera_brand: Marca de la cámara ('dahua', 'tplink', 'steren')
            
        Returns:
            Instancia de la conexión solicitada
            
        Raises:
            ValueError: Si el tipo de conexión no es soportado
        """
        # Importar conexiones específicas
        from .rtsp_connection import RTSPConnection
        from .amcrest_connection import AmcrestConnection
        from .onvif_connection import ONVIFConnection
        from .tplink_connection import TPLinkConnection
        from .steren_connection import SterenConnection
        
        # Mapeo de conexiones por marca
        connection_map = {
            "dahua": {
                "rtsp": RTSPConnection,
                "amcrest": AmcrestConnection,
                "onvif": ONVIFConnection,
            },
            "tplink": {
                "rtsp": TPLinkConnection,
                "tplink": TPLinkConnection,  # Alias por compatibilidad
                "onvif": ONVIFConnection,   # TP-Link también soporta ONVIF
            },
            "steren": {
                "rtsp": SterenConnection,
                "onvif": SterenConnection,  # Steren usa ONVIF + RTSP integrado
                "steren": SterenConnection,  # Alias por compatibilidad
            }
        }
        
        if camera_brand not in connection_map:
            raise ValueError(f"Marca de cámara no soportada: {camera_brand}")
        
        brand_connections = connection_map[camera_brand]
        
        if connection_type not in brand_connections:
            available = list(brand_connections.keys())
            raise ValueError(f"Tipo de conexión '{connection_type}' no soportado para {camera_brand}. "
                           f"Disponibles: {available}")
        
        connection_class = brand_connections[connection_type]
        return connection_class(config_manager)
    
    @staticmethod
    def get_supported_connections(camera_brand: str = None) -> Dict[str, list]:
        """
        Obtiene las conexiones soportadas por marca.
        
        Args:
            camera_brand: Marca específica o None para todas
            
        Returns:
            Diccionario con conexiones soportadas por marca
        """
        supported = {
            "dahua": ["rtsp", "amcrest", "onvif"],
            "tplink": ["rtsp", "tplink", "onvif"],
            "steren": ["rtsp", "onvif", "steren"]
        }
        
        if camera_brand:
            return {camera_brand: supported.get(camera_brand, [])}
        
        return supported 