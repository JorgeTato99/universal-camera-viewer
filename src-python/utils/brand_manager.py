"""
Brand Manager - MVP Architecture
================================

Gestor de marcas de cámaras adaptado para arquitectura MVP.
Carga especificaciones de marcas desde archivo JSON y proporciona
una API limpia para consultar información de marcas y modelos.

Mejoras sobre la versión anterior:
- Thread-safe singleton pattern
- Caching inteligente
- Mejor manejo de errores
- API más robusta
- Validación mejorada
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Información de modelo de cámara."""
    id: str
    name: str
    display_name: str
    supported_protocols: List[str]
    default_credentials: Dict[str, str]
    stream_config: Dict[str, int]
    description: Optional[str] = None
    onvif_profiles: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None


@dataclass
class BrandInfo:
    """Información de marca de cámara."""
    id: str
    name: str
    default_ports: Dict[str, int]
    rtsp_urls: List[str]
    protocols: List[str]
    models: List[ModelInfo]


class BrandManager:
    """
    Gestor de marcas de cámaras - MVP Architecture.
    
    Carga configuraciones desde JSON y permite agregar nuevas marcas
    sin modificar código. Implementa patrón Singleton thread-safe.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls, config_file: Optional[str] = None):
        """Implementación thread-safe del patrón Singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de marcas.
        
        Args:
            config_file: Ruta al archivo de configuración JSON
        """
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        
        # Configurar archivo de configuración
        if config_file is None:
            config_file = str(Path(__file__).parent / "camera_brands.json")
        self.config_file = Path(config_file)
        
        # Cache de configuración
        self._brands_cache: Dict[str, BrandInfo] = {}
        self._config_cache: Dict[str, Any] = {}
        
        # Cargar configuración
        self._load_configuration()
        
        # Marcar como inicializado
        BrandManager._initialized = True
        self.logger.info("BrandManager inicializado correctamente")
    
    def _load_configuration(self) -> None:
        """Carga la configuración de marcas desde el archivo JSON."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                raw_config = json.load(f)
            
            self._config_cache = raw_config
            self._build_brands_cache(raw_config)
            
            brands_count = len(self._brands_cache)
            self.logger.info(f"Configuración de marcas cargada: {brands_count} marcas")
            
        except FileNotFoundError:
            self.logger.error(f"Archivo de configuración no encontrado: {self.config_file}")
            self._load_default_configuration()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error al decodificar JSON: {e}")
            self._load_default_configuration()
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self._load_default_configuration()
    
    def _build_brands_cache(self, config: Dict[str, Any]) -> None:
        """
        Construye el cache de marcas desde la configuración cruda.
        
        Args:
            config: Configuración cruda desde JSON
        """
        brands = config.get("brands", {})
        
        for brand_id, brand_data in brands.items():
            try:
                # Parsear modelos
                models = []
                for model_data in brand_data.get("models", []):
                    model = ModelInfo(
                        id=model_data["id"],
                        name=model_data["name"],
                        display_name=model_data["display_name"],
                        supported_protocols=model_data["supported_protocols"],
                        default_credentials=model_data["default_credentials"],
                        stream_config=model_data["stream_config"],
                        description=model_data.get("description"),
                        onvif_profiles=model_data.get("onvif_profiles"),
                        device_info=model_data.get("device_info")
                    )
                    models.append(model)
                
                # Crear información de marca
                brand_info = BrandInfo(
                    id=brand_id,
                    name=brand_data["name"],
                    default_ports=brand_data["default_ports"],
                    rtsp_urls=brand_data["rtsp_urls"],
                    protocols=brand_data["protocols"],
                    models=models
                )
                
                self._brands_cache[brand_id] = brand_info
                
            except KeyError as e:
                self.logger.error(f"Campo requerido faltante en marca {brand_id}: {e}")
            except Exception as e:
                self.logger.error(f"Error procesando marca {brand_id}: {e}")
    
    def _load_default_configuration(self) -> None:
        """Carga configuración por defecto en caso de error."""
        self.logger.warning("Cargando configuración de marcas por defecto")
        
        # Configuración mínima por defecto
        default_config = {
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
        
        self._config_cache = default_config
        self._build_brands_cache(default_config)
    
    # === API Pública ===
    
    def get_supported_brands(self) -> List[str]:
        """
        Obtiene lista de marcas soportadas.
        
        Returns:
            Lista de IDs de marcas soportadas
        """
        return list(self._brands_cache.keys())
    
    def get_brand_info(self, brand_id: str) -> Optional[BrandInfo]:
        """
        Obtiene información de una marca específica.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Información de la marca o None si no existe
        """
        return self._brands_cache.get(brand_id)
    
    def get_brand_display_name(self, brand_id: str) -> str:
        """
        Obtiene el nombre de visualización de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Nombre de visualización o el ID si no existe
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.name if brand_info else brand_id.title()
    
    def get_brand_models(self, brand_id: str) -> List[ModelInfo]:
        """
        Obtiene lista de modelos de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Lista de modelos de la marca
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.models if brand_info else []
    
    def get_model_info(self, brand_id: str, model_id: str) -> Optional[ModelInfo]:
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
            if model.id == model_id:
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
            return model_info.supported_protocols if model_info else []
        else:
            brand_info = self.get_brand_info(brand_id)
            return brand_info.protocols if brand_info else []
    
    def get_default_ports(self, brand_id: str) -> Dict[str, int]:
        """
        Obtiene puertos por defecto de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Diccionario con puertos por defecto
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.default_ports if brand_info else {}
    
    def get_rtsp_urls(self, brand_id: str) -> List[str]:
        """
        Obtiene URLs RTSP de una marca.
        
        Args:
            brand_id: ID de la marca
            
        Returns:
            Lista de patrones de URL RTSP
        """
        brand_info = self.get_brand_info(brand_id)
        return brand_info.rtsp_urls if brand_info else []
    
    def build_rtsp_url(self, brand_id: str, username: str, password: str, 
                      ip: str, port: Optional[int] = None, channel: int = 1, 
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
        try:
            # Obtener puerto por defecto si no se especifica
            if port is None:
                default_ports = self.get_default_ports(brand_id)
                port = default_ports.get("rtsp", 554)
            
            # Asegurar que port no sea None
            final_port = port if port is not None else 554
            
            # Obtener patrón de URL
            rtsp_urls = self.get_rtsp_urls(brand_id)
            if not rtsp_urls or url_index >= len(rtsp_urls):
                # Fallback URL genérica
                url_pattern = "/stream1"
            else:
                url_pattern = rtsp_urls[url_index]
            
            # Formatear el patrón
            formatted_path = url_pattern.format(
                channel=channel,
                subtype=subtype
            )
            
            # Construir URL completa
            auth_part = f"{username}:{password}@" if username and password else ""
            rtsp_url = f"rtsp://{auth_part}{ip}:{final_port}{formatted_path}"
            
            return rtsp_url
            
        except Exception as e:
            self.logger.error(f"Error construyendo URL RTSP para {brand_id}: {e}")
            # URL de fallback genérica
            auth_part = f"{username}:{password}@" if username and password else ""
            fallback_port = port if port is not None else 554
            return f"rtsp://{auth_part}{ip}:{fallback_port}/stream1"
    
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
        return model_info.default_credentials if model_info else {"username": "admin", "password": ""}
    
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
        return model_info.stream_config if model_info else {"channel": 1, "subtype": 0}
    
    def get_display_name(self, brand_id: str, model_id: Optional[str] = None) -> str:
        """
        Obtiene nombre de visualización para marca/modelo.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo (opcional)
            
        Returns:
            Nombre de visualización completo
        """
        if model_id:
            model_info = self.get_model_info(brand_id, model_id)
            return model_info.display_name if model_info else f"{brand_id.title()} {model_id}"
        else:
            return self.get_brand_display_name(brand_id)
    
    def validate_brand_model(self, brand_id: str, model_id: str) -> bool:
        """
        Valida que una combinación marca/modelo sea válida.
        
        Args:
            brand_id: ID de la marca
            model_id: ID del modelo
            
        Returns:
            True si la combinación es válida
        """
        return self.get_model_info(brand_id, model_id) is not None
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración por defecto del sistema.
        
        Returns:
            Configuración por defecto
        """
        return self._config_cache.get("default_config", {})
    
    def reload_configuration(self) -> bool:
        """
        Recarga la configuración desde el archivo.
        
        Returns:
            True si la recarga fue exitosa
        """
        try:
            self.logger.info("Recargando configuración de marcas...")
            
            # Limpiar cache
            self._brands_cache.clear()
            self._config_cache.clear()
            
            # Recargar
            self._load_configuration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recargando configuración de marcas: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de las marcas configuradas.
        
        Returns:
            Resumen de configuración
        """
        summary = {
            'total_brands': len(self._brands_cache),
            'brands': [],
            'total_models': 0
        }
        
        for brand_id, brand_info in self._brands_cache.items():
            brand_summary = {
                'id': brand_id,
                'name': brand_info.name,
                'models_count': len(brand_info.models),
                'protocols': brand_info.protocols
            }
            summary['brands'].append(brand_summary)
            summary['total_models'] += len(brand_info.models)
        
        return summary


# Función de conveniencia para obtener la instancia singleton
def get_brand_manager() -> BrandManager:
    """
    Obtiene la instancia singleton del BrandManager.
    
    Returns:
        Instancia del BrandManager
    """
    return BrandManager() 