"""
Configuration Manager - MVP Architecture
========================================

Gestor centralizado de configuración del sistema adaptado para arquitectura MVP.
Implementa el patrón Singleton y proporciona acceso thread-safe a la configuración.

Mejoras sobre la versión anterior:
- Thread-safe configuration access
- Mejor validación de configuración
- Soporte para múltiples fuentes de configuración
- Caching inteligente
- Configuración por entornos
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import threading


@dataclass
class CameraConfig:
    """Configuración de cámara individual."""
    ip: str
    username: str
    password: str
    brand: str
    model: str
    rtsp_port: int = 554
    onvif_port: int = 80
    http_port: int = 80
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'ip': self.ip,
            'username': self.username,
            'password': self.password,
            'brand': self.brand,
            'model': self.model,
            'rtsp_port': self.rtsp_port,
            'onvif_port': self.onvif_port,
            'http_port': self.http_port,
            'enabled': self.enabled
        }


class ConfigurationManager:
    """
    Gestor centralizado de configuración del sistema - MVP Architecture.
    Implementa el patrón Singleton thread-safe para mantener una única instancia.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        """Implementación thread-safe del patrón Singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el gestor de configuración."""
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        
        # Variables de configuración
        self._config_cache: Dict[str, Any] = {}
        self._cameras_config: List[CameraConfig] = []
        
        # Cargar configuración
        self._load_all_configuration()
        
        # Marcar como inicializado
        ConfigurationManager._initialized = True
        self.logger.info("ConfigurationManager inicializado correctamente")
    
    def _load_all_configuration(self) -> None:
        """Carga toda la configuración del sistema."""
        try:
            # Cargar configuración desde variables de entorno
            self._load_camera_configs()
            self._load_connection_config()
            self._load_logging_config()
            self._load_application_config()
            
            self.logger.info("Configuración cargada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self._load_default_configuration()
    
    def _load_camera_configs(self) -> None:
        """Carga configuraciones de cámaras desde variables de entorno."""
        
        # Configuración Dahua (Hero-K51H)
        if os.getenv('DAHUA_IP'):
            dahua_config = CameraConfig(
                ip=os.getenv('DAHUA_IP', '192.168.1.172'),
                username=os.getenv('DAHUA_USER', 'admin'),
                password=os.getenv('DAHUA_PASSWORD', ''),
                brand='dahua',
                model='Hero-K51H',
                rtsp_port=int(os.getenv('DAHUA_RTSP_PORT', '554')),
                onvif_port=int(os.getenv('DAHUA_ONVIF_PORT', '80')),
                http_port=int(os.getenv('DAHUA_HTTP_PORT', '80'))
            )
            self._cameras_config.append(dahua_config)
            self.logger.info(f"Configuración Dahua cargada: {dahua_config.ip}")
        
        # Configuración TP-Link (Tapo C520WS)
        if os.getenv('TPLINK_IP'):
            tplink_config = CameraConfig(
                ip=os.getenv('TPLINK_IP', '192.168.1.77'),
                username=os.getenv('TPLINK_USER', 'admin'),
                password=os.getenv('TPLINK_PASSWORD', ''),
                brand='tplink',
                model='Tapo-C520WS',
                rtsp_port=int(os.getenv('TPLINK_RTSP_PORT', '554')),
                onvif_port=int(os.getenv('TPLINK_ONVIF_PORT', '2020')),
                http_port=int(os.getenv('TPLINK_HTTP_PORT', '80'))
            )
            self._cameras_config.append(tplink_config)
            self.logger.info(f"Configuración TP-Link cargada: {tplink_config.ip}")
        
        # Configuración Steren (CCTV-235)
        if os.getenv('STEREN_IP'):
            steren_config = CameraConfig(
                ip=os.getenv('STEREN_IP', '192.168.1.178'),
                username=os.getenv('STEREN_USER', 'admin'),
                password=os.getenv('STEREN_PASSWORD', ''),
                brand='steren',
                model='CCTV-235',
                rtsp_port=int(os.getenv('STEREN_RTSP_PORT', '5543')),
                onvif_port=int(os.getenv('STEREN_ONVIF_PORT', '8000')),
                http_port=int(os.getenv('STEREN_HTTP_PORT', '80'))
            )
            self._cameras_config.append(steren_config)
            self.logger.info(f"Configuración Steren cargada: {steren_config.ip}")
        
        # Configuración Generic (Cámaras chinas)
        if os.getenv('GENERIC_IP'):
            generic_config = CameraConfig(
                ip=os.getenv('GENERIC_IP', '192.168.1.100'),
                username=os.getenv('GENERIC_USER', 'admin'),
                password=os.getenv('GENERIC_PASSWORD', ''),
                brand='generic',
                model='8MP-WiFi',
                rtsp_port=int(os.getenv('GENERIC_RTSP_PORT', '554')),
                onvif_port=int(os.getenv('GENERIC_ONVIF_PORT', '80')),
                http_port=int(os.getenv('GENERIC_HTTP_PORT', '80'))
            )
            self._cameras_config.append(generic_config)
            self.logger.info(f"Configuración Generic cargada: {generic_config.ip}")
        
        # Cache de configuraciones de cámara
        self._config_cache['cameras'] = [cam.to_dict() for cam in self._cameras_config]
    
    def _load_connection_config(self) -> None:
        """Carga configuración de conexiones."""
        self._config_cache['connection'] = {
            'timeout': int(os.getenv('CONNECTION_TIMEOUT', '10')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'retry_delay': float(os.getenv('RETRY_DELAY', '1.0')),
            'buffer_size': int(os.getenv('BUFFER_SIZE', '1')),
        }
    
    def _load_logging_config(self) -> None:
        """Carga configuración de logging."""
        self._config_cache['logging'] = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file_enabled': os.getenv('LOG_FILE_ENABLED', 'true').lower() == 'true',
            'file_path': os.getenv('LOG_FILE_PATH', 'camera_viewer.log'),
            'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', '10485760')),  # 10MB
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
        }
    
    def _load_application_config(self) -> None:
        """Carga configuración de la aplicación."""
        self._config_cache['application'] = {
            'window_width': int(os.getenv('WINDOW_WIDTH', '1200')),
            'window_height': int(os.getenv('WINDOW_HEIGHT', '800')),
            'theme': os.getenv('APP_THEME', 'light'),
            'auto_connect': os.getenv('AUTO_CONNECT', 'false').lower() == 'true',
            'save_snapshots_path': os.getenv('SNAPSHOTS_PATH', './snapshots'),
            'auto_discovery': os.getenv('AUTO_DISCOVERY', 'true').lower() == 'true'
        }
    
    def _load_default_configuration(self) -> None:
        """Carga configuración por defecto en caso de error."""
        self.logger.warning("Cargando configuración por defecto")
        
        # Configuración por defecto
        self._config_cache = {
            'cameras': [],
            'connection': {
                'timeout': 10,
                'max_retries': 3,
                'retry_delay': 1.0,
                'buffer_size': 1
            },
            'logging': {
                'level': 'INFO',
                'file_enabled': True,
                'file_path': 'camera_viewer.log',
                'max_file_size': 10485760,
                'backup_count': 5
            },
            'application': {
                'window_width': 1200,
                'window_height': 800,
                'theme': 'light',
                'auto_connect': False,
                'save_snapshots_path': './snapshots',
                'auto_discovery': True
            }
        }
    
    # === API Pública ===
    
    def get_cameras_config(self) -> List[Dict[str, Any]]:
        """
        Obtiene la configuración de todas las cámaras.
        
        Returns:
            Lista de configuraciones de cámaras
        """
        return self._config_cache.get('cameras', [])
    
    def get_camera_config(self, brand: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de una cámara específica por marca.
        
        Args:
            brand: Marca de la cámara
            
        Returns:
            Configuración de la cámara o None si no existe
        """
        cameras = self.get_cameras_config()
        for camera in cameras:
            if camera.get('brand') == brand:
                return camera
        return None
    
    def get_connection_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de conexiones."""
        return self._config_cache.get('connection', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de logging."""
        return self._config_cache.get('logging', {})
    
    def get_application_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de la aplicación."""
        return self._config_cache.get('application', {})
    
    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor específico de configuración.
        
        Args:
            section: Sección de configuración
            key: Clave del valor
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        section_config = self._config_cache.get(section, {})
        return section_config.get(key, default)
    
    def is_camera_configured(self, brand: str) -> bool:
        """
        Verifica si una cámara está configurada.
        
        Args:
            brand: Marca de la cámara
            
        Returns:
            True si la cámara está configurada
        """
        return self.get_camera_config(brand) is not None
    
    def get_configured_camera_ips(self) -> Dict[str, str]:
        """
        Obtiene las IPs de las cámaras configuradas.
        
        Returns:
            Diccionario marca -> IP
        """
        ips = {}
        cameras = self.get_cameras_config()
        for camera in cameras:
            if camera.get('enabled', True):
                ips[camera['brand']] = camera['ip']
        return ips
    
    def validate_configuration(self) -> bool:
        """
        Valida que la configuración sea correcta.
        
        Returns:
            True si la configuración es válida
        """
        try:
            # Validar que al menos una cámara esté configurada
            cameras = self.get_cameras_config()
            if not cameras:
                self.logger.warning("No hay cámaras configuradas")
                return False
            
            # Validar configuraciones de cámara
            for camera in cameras:
                required_fields = ['ip', 'username', 'brand']
                for field in required_fields:
                    if not camera.get(field):
                        self.logger.error(f"Campo requerido '{field}' faltante en configuración de cámara")
                        return False
            
            self.logger.info("Configuración validada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando configuración: {e}")
            return False
    
    def reload_configuration(self) -> bool:
        """
        Recarga la configuración desde las fuentes.
        
        Returns:
            True si la recarga fue exitosa
        """
        try:
            self.logger.info("Recargando configuración...")
            
            # Limpiar cache
            self._config_cache.clear()
            self._cameras_config.clear()
            
            # Recargar todo
            self._load_all_configuration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recargando configuración: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de la configuración actual.
        
        Returns:
            Resumen de configuración
        """
        return {
            'cameras_count': len(self.get_cameras_config()),
            'cameras_brands': [cam['brand'] for cam in self.get_cameras_config()],
            'connection_timeout': self.get_config_value('connection', 'timeout'),
            'logging_level': self.get_config_value('logging', 'level'),
            'auto_connect': self.get_config_value('application', 'auto_connect'),
            'window_size': f"{self.get_config_value('application', 'window_width')}x{self.get_config_value('application', 'window_height')}"
        }


# Función de conveniencia para obtener la instancia singleton
def get_config() -> ConfigurationManager:
    """
    Obtiene la instancia singleton del ConfigurationManager.
    
    Returns:
        Instancia del ConfigurationManager
    """
    return ConfigurationManager() 