#!/usr/bin/env python3
"""
ConfigService - Servicio de gestión de configuración avanzada.

Proporciona funcionalidades completas de:
- Gestión de perfiles de configuración
- Credenciales seguras con encriptación
- Configuración dinámica
- Validación automática
- Configuración por marca de cámara
- Backup y restauración de configuración
- Variables de entorno
"""

import asyncio
import json
import logging
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Union
import base64
import hashlib

# Importaciones para encriptación
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    from ..utils.config import ConfigurationManager
except ImportError:
    # Fallback para ejecución directa
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.config import ConfigurationManager


class ConfigCategory(Enum):
    """Categorías de configuración."""
    CAMERA = "camera"
    NETWORK = "network"
    DISPLAY = "display"
    RECORDING = "recording"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ADVANCED = "advanced"


class ConfigType(Enum):
    """Tipos de configuración."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PASSWORD = "password"
    FILE_PATH = "file_path"
    IP_ADDRESS = "ip_address"


@dataclass
class ConfigItem:
    """Item de configuración individual."""
    key: str
    value: Any
    type: ConfigType
    category: ConfigCategory
    description: str = ""
    default_value: Any = None
    required: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    is_sensitive: bool = False
    last_modified: datetime = field(default_factory=datetime.now)
    modified_by: str = "system"


@dataclass
class ConfigProfile:
    """Perfil de configuración."""
    profile_id: str
    name: str
    description: str
    category: str
    items: Dict[str, ConfigItem] = field(default_factory=dict)
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class CameraProfile:
    """Perfil específico de cámara."""
    brand: str
    model: str
    ip: str
    credentials: Dict[str, str]
    protocols: List[str]
    ports: Dict[str, int]
    rtsp_urls: List[str]
    advanced_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigServiceConfig:
    """Configuración del ConfigService."""
    config_file: str = "config/app_config.json"
    profiles_file: str = "config/profiles.json"
    credentials_file: str = "config/credentials.enc"
    backup_directory: str = "config/backups"
    encryption_enabled: bool = True
    auto_backup: bool = True
    backup_interval_hours: int = 24
    validation_enabled: bool = True
    env_file_path: str = ".env"
    max_backup_files: int = 10
    config_version: str = "1.0"


class ConfigService:
    """
    Servicio de gestión de configuración avanzada.
    
    Características principales:
    - Gestión de perfiles de configuración
    - Encriptación de credenciales sensibles
    - Validación automática de configuración
    - Backup y restauración automática
    - Integración con variables de entorno
    - Configuración dinámica en tiempo real
    - API de observadores para cambios
    """
    
    def __init__(self, config: Optional[ConfigServiceConfig] = None):
        """
        Inicializa el ConfigService.
        
        Args:
            config: Configuración del servicio
        """
        self.config = config or ConfigServiceConfig()
        self.logger = logging.getLogger("ConfigService")
        
        # Estado del servicio
        self._initialized = False
        self._lock = threading.RLock()
        
        # Configuración actual
        self._config_items: Dict[str, ConfigItem] = {}
        self._profiles: Dict[str, ConfigProfile] = {}
        self._active_profile_id: Optional[str] = None
        
        # Encriptación
        self._cipher_suite = None
        self._encryption_key = None
        
        # Observadores de cambios
        self._change_observers: List[Callable[[str, Any, Any], None]] = []
        
        # Integración con ConfigurationManager existente
        self._legacy_config_manager: Optional[ConfigurationManager] = None
        
        # Estadísticas
        self._stats = {
            "config_loads": 0,
            "config_saves": 0,
            "profile_switches": 0,
            "validation_errors": 0,
            "backup_operations": 0
        }
        
    async def initialize(self) -> bool:
        """
        Inicializa el servicio de configuración.
        
        Returns:
            True si se inicializó correctamente
        """
        if self._initialized:
            return True
        
        try:
            self.logger.info("🚀 Inicializando ConfigService...")
            
            # Crear directorios necesarios
            self._create_directories()
            
            # Inicializar encriptación
            if self.config.encryption_enabled:
                await self._initialize_encryption()
            
            # Cargar configuración existente
            await self._load_configuration()
            
            # Cargar perfiles
            await self._load_profiles()
            
            # Integrar con ConfigurationManager existente
            await self._integrate_legacy_config()
            
            # Inicializar configuración por defecto
            await self._initialize_default_config()
            
            # Iniciar tareas de fondo
            if self.config.auto_backup:
                asyncio.create_task(self._backup_worker())
            
            self._initialized = True
            self.logger.info("✅ ConfigService inicializado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando ConfigService: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Crea los directorios necesarios."""
        directories = [
            Path(self.config.config_file).parent,
            Path(self.config.profiles_file).parent,
            Path(self.config.credentials_file).parent,
            Path(self.config.backup_directory)
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def _initialize_encryption(self) -> None:
        """Inicializa el sistema de encriptación."""
        if not CRYPTO_AVAILABLE:
            self.logger.warning("⚠️ Cryptography no disponible, credenciales se guardarán en texto plano")
            self.config.encryption_enabled = False
            return
        
        try:
            # Generar o cargar clave de encriptación
            key_file = Path("config/.encryption_key")
            
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self._encryption_key = f.read()
            else:
                # Generar nueva clave basada en datos del sistema
                password = self._generate_system_password()
                salt = os.urandom(16)
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000
                )
                self._encryption_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                
                # Guardar clave de forma segura
                with open(key_file, 'wb') as f:
                    f.write(self._encryption_key)
                
                # Hacer el archivo solo lectura para el propietario
                key_file.chmod(0o600)
            
            self._cipher_suite = Fernet(self._encryption_key)
            self.logger.info("🔒 Encriptación inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando encriptación: {e}")
            self.config.encryption_enabled = False
    
    def _generate_system_password(self) -> str:
        """Genera una contraseña basada en características del sistema."""
        import platform
        import getpass
        
        # Usar características del sistema para generar una clave única
        system_info = f"{platform.node()}{platform.system()}{getpass.getuser()}"
        return hashlib.sha256(system_info.encode()).hexdigest()[:32]
    
    async def _load_configuration(self) -> None:
        """Carga la configuración desde el archivo."""
        config_file = Path(self.config.config_file)
        
        if not config_file.exists():
            self.logger.info("📁 Archivo de configuración no existe, creando configuración por defecto")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Cargar items de configuración
            for item_data in config_data.get('config_items', []):
                config_item = ConfigItem(
                    key=item_data['key'],
                    value=item_data['value'],
                    type=ConfigType(item_data['type']),
                    category=ConfigCategory(item_data['category']),
                    description=item_data.get('description', ''),
                    default_value=item_data.get('default_value'),
                    required=item_data.get('required', False),
                    validation_rules=item_data.get('validation_rules', {}),
                    is_sensitive=item_data.get('is_sensitive', False),
                    last_modified=datetime.fromisoformat(item_data.get('last_modified', datetime.now().isoformat())),
                    modified_by=item_data.get('modified_by', 'system')
                )
                
                # Desencriptar valores sensibles
                if config_item.is_sensitive and self._cipher_suite:
                    try:
                        config_item.value = self._decrypt_value(config_item.value)
                    except Exception as e:
                        self.logger.warning(f"No se pudo desencriptar valor sensible para {config_item.key}: {e}")
                
                self._config_items[config_item.key] = config_item
            
            self._active_profile_id = config_data.get('active_profile_id')
            self._stats["config_loads"] += 1
            
            self.logger.info(f"📥 Configuración cargada: {len(self._config_items)} items")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
    
    async def _load_profiles(self) -> None:
        """Carga los perfiles de configuración."""
        profiles_file = Path(self.config.profiles_file)
        
        if not profiles_file.exists():
            self.logger.info("📁 Archivo de perfiles no existe, creando perfiles por defecto")
            await self._create_default_profiles()
            return
        
        try:
            with open(profiles_file, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            
            for profile_data in profiles_data.get('profiles', []):
                profile = ConfigProfile(
                    profile_id=profile_data['profile_id'],
                    name=profile_data['name'],
                    description=profile_data['description'],
                    category=profile_data['category'],
                    is_default=profile_data.get('is_default', False),
                    created_at=datetime.fromisoformat(profile_data.get('created_at', datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(profile_data.get('updated_at', datetime.now().isoformat())),
                    tags=profile_data.get('tags', [])
                )
                
                # Cargar items del perfil
                for item_data in profile_data.get('items', []):
                    config_item = ConfigItem(
                        key=item_data['key'],
                        value=item_data['value'],
                        type=ConfigType(item_data['type']),
                        category=ConfigCategory(item_data['category']),
                        description=item_data.get('description', ''),
                        default_value=item_data.get('default_value'),
                        required=item_data.get('required', False),
                        validation_rules=item_data.get('validation_rules', {}),
                        is_sensitive=item_data.get('is_sensitive', False),
                        last_modified=datetime.fromisoformat(item_data.get('last_modified', datetime.now().isoformat())),
                        modified_by=item_data.get('modified_by', 'system')
                    )
                    profile.items[config_item.key] = config_item
                
                self._profiles[profile.profile_id] = profile
            
            self.logger.info(f"📂 Perfiles cargados: {len(self._profiles)}")
            
        except Exception as e:
            self.logger.error(f"Error cargando perfiles: {e}")
    
    async def _integrate_legacy_config(self) -> None:
        """Integra con el ConfigurationManager existente."""
        try:
            self._legacy_config_manager = ConfigurationManager()
            
            # Migrar configuración existente si es necesario
            await self._migrate_legacy_config()
            
            self.logger.info("🔄 Integración con configuración legacy completada")
            
        except Exception as e:
            self.logger.error(f"Error integrando configuración legacy: {e}")
    
    async def _migrate_legacy_config(self) -> None:
        """Migra configuración legacy al nuevo sistema."""
        if not self._legacy_config_manager:
            return
        
        # Migrar configuración de cámaras
        try:
            # Verificar si existen atributos antes de acceder
            if hasattr(self._legacy_config_manager, 'get_camera_ip'):
                camera_ip = getattr(self._legacy_config_manager, 'get_camera_ip', lambda: None)()
                if camera_ip:
                    await self.set_config_value(
                        "dahua.ip", 
                        camera_ip,
                        ConfigType.IP_ADDRESS,
                        ConfigCategory.CAMERA,
                        "Dirección IP de la cámara Dahua"
                    )
            
            if hasattr(self._legacy_config_manager, 'get_camera_user'):
                camera_user = getattr(self._legacy_config_manager, 'get_camera_user', lambda: None)()
                if camera_user:
                    await self.set_config_value(
                        "dahua.username",
                        camera_user,
                        ConfigType.STRING,
                        ConfigCategory.CAMERA,
                        "Usuario de la cámara Dahua"
                    )
            
            if hasattr(self._legacy_config_manager, 'get_camera_password'):
                camera_password = getattr(self._legacy_config_manager, 'get_camera_password', lambda: None)()
                if camera_password:
                    await self.set_config_value(
                        "dahua.password",
                        camera_password,
                        ConfigType.PASSWORD,
                        ConfigCategory.CAMERA,
                        "Contraseña de la cámara Dahua",
                        is_sensitive=True
                    )
            
            # Similar para otras marcas...
            self.logger.info("✅ Migración de configuración legacy completada")
            
        except Exception as e:
            self.logger.error(f"Error migrando configuración legacy: {e}")
    
    async def _initialize_default_config(self) -> None:
        """Inicializa la configuración por defecto."""
        default_configs = [
            # Configuración de cámaras
            ("app.name", "Visor Universal de Cámaras Multi-Marca", ConfigType.STRING, ConfigCategory.ADVANCED),
            ("app.version", "2.0.0", ConfigType.STRING, ConfigCategory.ADVANCED),
            
            # Configuración de red
            ("network.timeout", 10, ConfigType.INTEGER, ConfigCategory.NETWORK, "Timeout de conexión en segundos"),
            ("network.retry_attempts", 3, ConfigType.INTEGER, ConfigCategory.NETWORK, "Intentos de reintento"),
            ("network.buffer_size", 1, ConfigType.INTEGER, ConfigCategory.NETWORK, "Tamaño del buffer de video"),
            
            # Configuración de display
            ("display.fps_limit", 30, ConfigType.INTEGER, ConfigCategory.DISPLAY, "Límite de FPS para visualización"),
            ("display.auto_resize", True, ConfigType.BOOLEAN, ConfigCategory.DISPLAY, "Redimensionar automáticamente"),
            ("display.quality", "high", ConfigType.STRING, ConfigCategory.DISPLAY, "Calidad de visualización"),
            
            # Configuración de grabación
            ("recording.enabled", False, ConfigType.BOOLEAN, ConfigCategory.RECORDING, "Habilitar grabación"),
            ("recording.format", "mp4", ConfigType.STRING, ConfigCategory.RECORDING, "Formato de grabación"),
            ("recording.quality", "720p", ConfigType.STRING, ConfigCategory.RECORDING, "Calidad de grabación"),
            
            # Configuración de seguridad
            ("security.encrypt_config", True, ConfigType.BOOLEAN, ConfigCategory.SECURITY, "Encriptar configuración sensible"),
            ("security.session_timeout", 30, ConfigType.INTEGER, ConfigCategory.SECURITY, "Timeout de sesión en minutos"),
            
            # Configuración de rendimiento
            ("performance.max_concurrent_connections", 10, ConfigType.INTEGER, ConfigCategory.PERFORMANCE, "Máximo conexiones concurrentes"),
            ("performance.cache_enabled", True, ConfigType.BOOLEAN, ConfigCategory.PERFORMANCE, "Habilitar cache"),
            ("performance.thread_pool_size", 5, ConfigType.INTEGER, ConfigCategory.PERFORMANCE, "Tamaño del pool de threads"),
        ]
        
        for config_tuple in default_configs:
            if len(config_tuple) == 4:
                key, value, config_type, category = config_tuple
                description = ""
            else:
                key, value, config_type, category, description = config_tuple
                
            if key not in self._config_items:
                await self.set_config_value(key, value, config_type, category, description)
    
    async def _create_default_profiles(self) -> None:
        """Crea perfiles de configuración por defecto."""
        # Perfil básico
        basic_profile = ConfigProfile(
            profile_id="basic",
            name="Configuración Básica",
            description="Configuración básica para uso general",
            category="basic",
            is_default=True
        )
        
        # Perfil avanzado
        advanced_profile = ConfigProfile(
            profile_id="advanced",
            name="Configuración Avanzada",
            description="Configuración avanzada con todas las características",
            category="advanced"
        )
        
        # Perfil de desarrollo
        dev_profile = ConfigProfile(
            profile_id="development",
            name="Desarrollo",
            description="Configuración para desarrollo y testing",
            category="development"
        )
        
        self._profiles["basic"] = basic_profile
        self._profiles["advanced"] = advanced_profile
        self._profiles["development"] = dev_profile
        
        self._active_profile_id = "basic"
        
        await self._save_profiles()
    
    # === API pública de configuración ===
    
    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        with self._lock:
            if key in self._config_items:
                return self._config_items[key].value
            return default
    
    async def set_config_value(
        self, 
        key: str, 
        value: Any, 
        config_type: ConfigType = ConfigType.STRING,
        category: ConfigCategory = ConfigCategory.ADVANCED,
        description: str = "",
        is_sensitive: bool = False,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
            config_type: Tipo de configuración
            category: Categoría de configuración
            description: Descripción del parámetro
            is_sensitive: Si el valor es sensible (se encriptará)
            validation_rules: Reglas de validación
            
        Returns:
            True si se estableció correctamente
        """
        try:
            # Validar valor si está habilitada la validación
            if self.config.validation_enabled:
                if not await self._validate_config_value(key, value, config_type, validation_rules or {}):
                    self._stats["validation_errors"] += 1
                    return False
            
            # Obtener valor anterior para notificación
            old_value = None
            if key in self._config_items:
                old_value = self._config_items[key].value
            
            # Encriptar valor si es sensible
            stored_value = value
            if is_sensitive and self._cipher_suite:
                stored_value = self._encrypt_value(value)
            
            # Crear o actualizar item de configuración
            config_item = ConfigItem(
                key=key,
                value=stored_value,
                type=config_type,
                category=category,
                description=description,
                default_value=value if old_value is None else self._config_items[key].default_value,
                is_sensitive=is_sensitive,
                validation_rules=validation_rules or {},
                last_modified=datetime.now(),
                modified_by="user"
            )
            
            with self._lock:
                self._config_items[key] = config_item
            
            # Notificar observadores
            await self._notify_observers(key, old_value, value)
            
            # Guardar configuración
            await self._save_configuration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error estableciendo configuración {key}: {e}")
            return False
    
    async def delete_config_value(self, key: str) -> bool:
        """
        Elimina un valor de configuración.
        
        Args:
            key: Clave de configuración
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            old_value = None
            
            with self._lock:
                if key in self._config_items:
                    old_value = self._config_items[key].value
                    del self._config_items[key]
                else:
                    return False
            
            # Notificar observadores
            await self._notify_observers(key, old_value, None)
            
            # Guardar configuración
            await self._save_configuration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error eliminando configuración {key}: {e}")
            return False
    
    # === Gestión de perfiles ===
    
    async def create_profile(self, profile_id: str, name: str, description: str, category: str = "custom") -> bool:
        """
        Crea un nuevo perfil de configuración.
        
        Args:
            profile_id: ID único del perfil
            name: Nombre del perfil
            description: Descripción del perfil
            category: Categoría del perfil
            
        Returns:
            True si se creó correctamente
        """
        try:
            if profile_id in self._profiles:
                self.logger.error(f"El perfil {profile_id} ya existe")
                return False
            
            profile = ConfigProfile(
                profile_id=profile_id,
                name=name,
                description=description,
                category=category
            )
            
            with self._lock:
                self._profiles[profile_id] = profile
            
            await self._save_profiles()
            
            self.logger.info(f"✅ Perfil creado: {profile_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando perfil {profile_id}: {e}")
            return False
    
    async def switch_profile(self, profile_id: str) -> bool:
        """
        Cambia al perfil especificado.
        
        Args:
            profile_id: ID del perfil
            
        Returns:
            True si se cambió correctamente
        """
        try:
            if profile_id not in self._profiles:
                self.logger.error(f"El perfil {profile_id} no existe")
                return False
            
            old_profile_id = self._active_profile_id
            
            with self._lock:
                self._active_profile_id = profile_id
                
                # Aplicar configuración del perfil
                profile = self._profiles[profile_id]
                for key, config_item in profile.items.items():
                    self._config_items[key] = config_item
            
            self._stats["profile_switches"] += 1
            
            # Notificar observadores del cambio de perfil
            await self._notify_observers("__profile__", old_profile_id, profile_id)
            
            await self._save_configuration()
            
            self.logger.info(f"🔄 Perfil cambiado a: {profile_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cambiando a perfil {profile_id}: {e}")
            return False
    
    def get_active_profile(self) -> Optional[ConfigProfile]:
        """
        Obtiene el perfil activo.
        
        Returns:
            Perfil activo o None
        """
        if self._active_profile_id and self._active_profile_id in self._profiles:
            return self._profiles[self._active_profile_id]
        return None
    
    def get_all_profiles(self) -> Dict[str, ConfigProfile]:
        """
        Obtiene todos los perfiles.
        
        Returns:
            Diccionario con todos los perfiles
        """
        return self._profiles.copy()
    
    # === Gestión de credenciales ===
    
    async def set_camera_credentials(self, brand: str, username: str, password: str) -> bool:
        """
        Establece credenciales para una marca de cámara.
        
        Args:
            brand: Marca de la cámara
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            True si se establecieron correctamente
        """
        try:
            await self.set_config_value(
                f"{brand}.username",
                username,
                ConfigType.STRING,
                ConfigCategory.CAMERA,
                f"Usuario para cámaras {brand}"
            )
            
            await self.set_config_value(
                f"{brand}.password",
                password,
                ConfigType.PASSWORD,
                ConfigCategory.CAMERA,
                f"Contraseña para cámaras {brand}",
                is_sensitive=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error estableciendo credenciales para {brand}: {e}")
            return False
    
    async def get_camera_credentials(self, brand: str) -> Dict[str, str]:
        """
        Obtiene credenciales para una marca de cámara.
        
        Args:
            brand: Marca de la cámara
            
        Returns:
            Diccionario con username y password
        """
        username = await self.get_config_value(f"{brand}.username", "admin")
        password = await self.get_config_value(f"{brand}.password", "")
        
        return {
            "username": username,
            "password": password
        }
    
    # === Exportación e importación ===
    
    async def export_config(self, filepath: str, include_sensitive: bool = False) -> bool:
        """
        Exporta la configuración a un archivo.
        
        Args:
            filepath: Ruta del archivo de exportación
            include_sensitive: Si incluir valores sensibles
            
        Returns:
            True si se exportó correctamente
        """
        try:
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "config_version": self.config.config_version,
                    "include_sensitive": include_sensitive
                },
                "active_profile_id": self._active_profile_id,
                "config_items": [],
                "profiles": []
            }
            
            # Exportar items de configuración
            for config_item in self._config_items.values():
                if config_item.is_sensitive and not include_sensitive:
                    continue
                
                item_data = asdict(config_item)
                item_data['type'] = config_item.type.value
                item_data['category'] = config_item.category.value
                item_data['last_modified'] = config_item.last_modified.isoformat()
                
                export_data["config_items"].append(item_data)
            
            # Exportar perfiles
            for profile in self._profiles.values():
                profile_data = asdict(profile)
                profile_data['created_at'] = profile.created_at.isoformat()
                profile_data['updated_at'] = profile.updated_at.isoformat()
                
                # Exportar items del perfil
                profile_items = []
                for config_item in profile.items.values():
                    if config_item.is_sensitive and not include_sensitive:
                        continue
                    
                    item_data = asdict(config_item)
                    item_data['type'] = config_item.type.value
                    item_data['category'] = config_item.category.value
                    item_data['last_modified'] = config_item.last_modified.isoformat()
                    
                    profile_items.append(item_data)
                
                profile_data['items'] = profile_items
                export_data["profiles"].append(profile_data)
            
            # Guardar archivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"📤 Configuración exportada: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando configuración: {e}")
            return False
    
    # === Métodos privados ===
    
    def _encrypt_value(self, value: str) -> str:
        """Encripta un valor sensible."""
        if not self._cipher_suite:
            return value
        
        try:
            encrypted_bytes = self._cipher_suite.encrypt(str(value).encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception:
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Desencripta un valor sensible."""
        if not self._cipher_suite:
            return encrypted_value
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            return encrypted_value
    
    async def _validate_config_value(self, key: str, value: Any, config_type: ConfigType, validation_rules: Dict[str, Any]) -> bool:
        """Valida un valor de configuración."""
        try:
            # Validación de tipo
            if config_type == ConfigType.INTEGER and not isinstance(value, int):
                self.logger.error(f"Valor para {key} debe ser entero")
                return False
            
            if config_type == ConfigType.FLOAT and not isinstance(value, (int, float)):
                self.logger.error(f"Valor para {key} debe ser número")
                return False
            
            if config_type == ConfigType.BOOLEAN and not isinstance(value, bool):
                self.logger.error(f"Valor para {key} debe ser booleano")
                return False
            
            if config_type == ConfigType.IP_ADDRESS:
                import ipaddress
                try:
                    # Convertir a string antes de validar
                    ipaddress.ip_address(str(value))
                except ValueError:
                    self.logger.error(f"Valor para {key} debe ser IP válida")
                    return False
            
            # Validaciones específicas según reglas
            if "min_value" in validation_rules and value < validation_rules["min_value"]:
                self.logger.error(f"Valor para {key} debe ser >= {validation_rules['min_value']}")
                return False
            
            if "max_value" in validation_rules and value > validation_rules["max_value"]:
                self.logger.error(f"Valor para {key} debe ser <= {validation_rules['max_value']}")
                return False
            
            if "allowed_values" in validation_rules and value not in validation_rules["allowed_values"]:
                self.logger.error(f"Valor para {key} debe ser uno de: {validation_rules['allowed_values']}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando {key}: {e}")
            return False
    
    async def _notify_observers(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notifica a los observadores de cambios."""
        for observer in self._change_observers:
            try:
                observer(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"Error notificando observador: {e}")
    
    async def _save_configuration(self) -> None:
        """Guarda la configuración al archivo."""
        try:
            config_data = {
                "config_version": self.config.config_version,
                "last_saved": datetime.now().isoformat(),
                "active_profile_id": self._active_profile_id,
                "config_items": []
            }
            
            for config_item in self._config_items.values():
                item_data = asdict(config_item)
                item_data['type'] = config_item.type.value
                item_data['category'] = config_item.category.value
                item_data['last_modified'] = config_item.last_modified.isoformat()
                
                config_data["config_items"].append(item_data)
            
            with open(self.config.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            self._stats["config_saves"] += 1
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
    
    async def _save_profiles(self) -> None:
        """Guarda los perfiles al archivo."""
        try:
            profiles_data = {
                "config_version": self.config.config_version,
                "last_saved": datetime.now().isoformat(),
                "profiles": []
            }
            
            for profile in self._profiles.values():
                profile_data = asdict(profile)
                profile_data['created_at'] = profile.created_at.isoformat()
                profile_data['updated_at'] = profile.updated_at.isoformat()
                
                # Serializar items del perfil
                profile_items = []
                for config_item in profile.items.values():
                    item_data = asdict(config_item)
                    item_data['type'] = config_item.type.value
                    item_data['category'] = config_item.category.value
                    item_data['last_modified'] = config_item.last_modified.isoformat()
                    
                    profile_items.append(item_data)
                
                profile_data['items'] = profile_items
                profiles_data["profiles"].append(profile_data)
            
            with open(self.config.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Error guardando perfiles: {e}")
    
    async def _backup_worker(self) -> None:
        """Worker para backup automático."""
        while self._initialized:
            try:
                await asyncio.sleep(self.config.backup_interval_hours * 3600)
                await self._create_backup()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en backup automático: {e}")
    
    async def _create_backup(self) -> bool:
        """Crea un backup de la configuración."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(self.config.backup_directory)
            backup_file = backup_dir / f"config_backup_{timestamp}.json"
            
            await self.export_config(str(backup_file), include_sensitive=False)
            
            # Limpiar backups antiguos
            backup_files = sorted(backup_dir.glob("config_backup_*.json"))
            if len(backup_files) > self.config.max_backup_files:
                for old_backup in backup_files[:-self.config.max_backup_files]:
                    old_backup.unlink()
            
            self._stats["backup_operations"] += 1
            self.logger.info(f"💾 Backup creado: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return False
    
    # === API de observadores ===
    
    def add_change_observer(self, observer: Callable[[str, Any, Any], None]) -> None:
        """
        Agrega un observador de cambios de configuración.
        
        Args:
            observer: Función que será llamada cuando cambie la configuración
        """
        self._change_observers.append(observer)
    
    def remove_change_observer(self, observer: Callable[[str, Any, Any], None]) -> None:
        """
        Remueve un observador de cambios.
        
        Args:
            observer: Función observadora a remover
        """
        if observer in self._change_observers:
            self._change_observers.remove(observer)
    
    # === Estadísticas ===
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del servicio."""
        return {
            **self._stats,
            "config_items_count": len(self._config_items),
            "profiles_count": len(self._profiles),
            "active_profile": self._active_profile_id,
            "encryption_enabled": self.config.encryption_enabled
        }


# Función global para obtener instancia del servicio
_config_service_instance: Optional[ConfigService] = None


def get_config_service(config: Optional[ConfigServiceConfig] = None) -> ConfigService:
    """
    Obtiene la instancia global del ConfigService.
    
    Args:
        config: Configuración opcional
        
    Returns:
        Instancia del ConfigService
    """
    global _config_service_instance
    
    if _config_service_instance is None:
        _config_service_instance = ConfigService(config)
    
    return _config_service_instance 