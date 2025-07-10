"""
Gestor de marcas de cámaras para configuración agnóstica.
Carga especificaciones de marcas desde archivo JSON.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class BrandManager:
    """
    Gestor de marcas de cámaras que carga configuraciones desde JSON.
    Permite agregar nuevas marcas sin modificar código.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de marcas.
        
        Args:
            config_file: Ruta al archivo de configuración JSON
        """
        self.logger = logging.getLogger("BrandManager")
        
        if config_file is None:
            config_file = Path(__file__).parent / "camera_brands.json"
        
        self.config_file = Path(config_file)
        self.brands_config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración de marcas desde el archivo JSON.
        
        Returns:
            Diccionario con configuración de marcas
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"Configuración de marcas cargada: {len(config.get('brands', {}))} marcas")
            return config
            
        except FileNotFoundError:
            self.logger.error(f"Archivo de configuración no encontrado: {self.config_file}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error al decodificar JSON: {e}")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración por defecto en caso de error.
        
        Returns:
            Configuración mínima por defecto
        """
        return {
            "brands": {
                "dahua": {
                    "name": "Dahua",
                    "default_ports": {"rtsp": 554, "http": 80, "onvif": 80},
                    "rtsp_urls": ["/cam/realmonitor?channel={channel}&subtype={subtype}"],
                    "protocols": ["rtsp", "onvif"],
                    "models": [
                        {
                            "id": "generic",
                            "name": "Generic Model",
                            "display_name": "Dahua Generic",
                            "supported_protocols": ["rtsp", "onvif"],
                            "default_credentials": {"username": "admin", "password": ""},
                            "stream_config": {"channel": 1, "subtype": 0}
                        }
                    ]
                }
            },
            "default_config": {
                "connection_timeout": 10,
                "connection_retries": 3,
                "default_brand": "dahua",
                "default_protocol": "rtsp"
            }
        }
    
    def get_supported_brands(self) -> List[str]:
        """
        Obtiene lista de marcas soportadas.
        
        Returns:
            Lista de IDs de marcas soportadas
        """
        return list(self.brands_config.get("brands", {}).keys())
    
    def get_brand_info(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una marca específica.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Información de la marca o None si no existe
        """
        return self.brands_config.get("brands", {}).get(brand_id)
    
    def get_brand_models(self, brand_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene lista de modelos de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Lista de modelos de la marca
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.get("models", []) if brand_info else []
    
    def get_model_info(self, brand_id: str, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un modelo específico.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo
            
        Returns:
            Información del modelo o None si no existe
        """
        models = self.get_brand_models(brand_id)
        for model in models:
            if model.get("id") == model_id:
                return model
        return None
    
    def get_supported_protocols(self, brand_id: str, model_id: Optional[str] = None) -> List[str]:
        """
        Obtiene protocolos soportados por una marca/modelo.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo (opcional)
            
        Returns:
            Lista de protocolos soportados
        """
        if model_id:
            model_info = self.get_model_info(brand_id, model_id)
            return model_info.get("supported_protocols", []) if model_info else []
        else:
            brand_info = self.get_brand_info(brand_id)
            return brand_info.get("protocols", []) if brand_info else []
    
    def get_default_ports(self, brand_id: str) -> Dict[str, int]:
        """
        Obtiene puertos por defecto de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Diccionario con puertos por defecto
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.get("default_ports", {}) if brand_info else {}
    
    def get_rtsp_urls(self, brand_id: str) -> List[str]:
        """
        Obtiene URLs RTSP de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Lista de patrones de URL RTSP
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.get("rtsp_urls", []) if brand_info else []
    
    def build_rtsp_url(self, brand_id: str, username: str, password: str, 
                      ip: str, port: int = None, channel: int = 1, 
                      subtype: int = 0, url_index: int = 0) -> str:
        """
        Construye URL RTSP completa para una marca específica.
        
        Args:
            brand_id: ID de la marca
            username: Usuario
            password: Contraseña
            ip: IP de la cámara
            port: Puerto RTSP (opcional, usa default)
            channel: Canal de stream
            subtype: Subtipo de stream
            url_index: Índice de URL a usar (0 = primera)
            
        Returns:
            URL RTSP completa
        """
        rtsp_urls = self.get_rtsp_urls(brand_id)
        if not rtsp_urls:
            return f"rtsp://{username}:{password}@{ip}:554/"
        
        # Usar índice específico o el primero disponible
        url_pattern = rtsp_urls[min(url_index, len(rtsp_urls) - 1)]
        
        # Obtener puerto por defecto si no se especifica
        if port is None:
            ports = self.get_default_ports(brand_id)
            port = ports.get("rtsp", 554)
        
        # Formatear URL con parámetros
        url_path = url_pattern.format(channel=channel, subtype=subtype)
        
        return f"rtsp://{username}:{password}@{ip}:{port}{url_path}"
    
    def get_default_credentials(self, brand_id: str, model_id: str) -> Dict[str, str]:
        """
        Obtiene credenciales por defecto de un modelo.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo
            
        Returns:
            Diccionario con credenciales por defecto
        """
        model_info = self.get_model_info(brand_id, model_id)
        return model_info.get("default_credentials", {"username": "admin", "password": ""}) if model_info else {"username": "admin", "password": ""}
    
    def get_stream_config(self, brand_id: str, model_id: str) -> Dict[str, int]:
        """
        Obtiene configuración de stream de un modelo.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo
            
        Returns:
            Diccionario con configuración de stream
        """
        model_info = self.get_model_info(brand_id, model_id)
        return model_info.get("stream_config", {"channel": 1, "subtype": 0}) if model_info else {"channel": 1, "subtype": 0}
    
    def get_display_name(self, brand_id: str, model_id: str = None) -> str:
        """
        Obtiene nombre para mostrar de una marca/modelo.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo (opcional)
            
        Returns:
            Nombre para mostrar
        """
        if model_id:
            model_info = self.get_model_info(brand_id, model_id)
            return model_info.get("display_name", f"{brand_id} {model_id}") if model_info else f"{brand_id} {model_id}"
        else:
            brand_info = self.get_brand_info(brand_id)
            return brand_info.get("name", brand_id.title()) if brand_info else brand_id.title()
    
    def validate_brand_model(self, brand_id: str, model_id: str) -> bool:
        """
        Valida si una combinación marca/modelo existe.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo
            
        Returns:
            True si la combinación existe
        """
        return self.get_model_info(brand_id, model_id) is not None
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración por defecto global.
        
        Returns:
            Configuración por defecto
        """
        return self.brands_config.get("default_config", {})


# Instancia global del gestor de marcas
_brand_manager = None

def get_brand_manager() -> BrandManager:
    """
    Obtiene la instancia global del gestor de marcas.
    
    Returns:
        Instancia del BrandManager
    """
    global _brand_manager
    if _brand_manager is None:
        _brand_manager = BrandManager()
    return _brand_manager 