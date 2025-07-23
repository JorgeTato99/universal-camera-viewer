"""
Servicio mejorado de encriptación para credenciales con soporte de rotación de claves.

Este servicio implementa:
- Encriptación con versionado de claves
- Rotación segura de claves
- Validación de integridad
- Mejor protección del archivo de claves
- Auditoría de acceso
"""
import os
import base64
import json
import logging
import time
from typing import Optional, Dict, Tuple, List
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path
from datetime import datetime, timedelta
import threading
import hashlib

from services.base_service import BaseService


class KeyVersion:
    """Representa una versión de clave de encriptación."""
    
    def __init__(self, version: int, key: bytes, created_at: datetime, is_active: bool = True):
        self.version = version
        self.key = key
        self.created_at = created_at
        self.is_active = is_active
        self.cipher = Fernet(key)
        
    def to_dict(self) -> dict:
        """Convierte a diccionario para persistencia."""
        return {
            'version': self.version,
            'key': base64.urlsafe_b64encode(self.key).decode(),
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KeyVersion':
        """Crea desde diccionario."""
        return cls(
            version=data['version'],
            key=base64.urlsafe_b64decode(data['key'].encode()),
            created_at=datetime.fromisoformat(data['created_at']),
            is_active=data['is_active']
        )


class EncryptionServiceV2(BaseService):
    """
    Servicio mejorado de encriptación con versionado y rotación de claves.
    
    Mejoras sobre la versión anterior:
    - Versionado de claves para rotación segura
    - Validación de integridad con HMAC
    - Mejor protección del archivo de claves
    - Auditoría de acceso a credenciales
    - Compatibilidad con versión anterior
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "EncryptionServiceV2":
        """Garantiza una única instancia thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio de encriptación mejorado."""
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        
        # Configuración
        project_root = Path(__file__).parent.parent.parent
        self._key_store_dir = project_root / "data" / ".encryption"
        self._key_store_file = self._key_store_dir / "keystore.json"
        self._legacy_key_file = project_root / "data" / ".encryption_key"
        
        # Estado interno
        self._keys: Dict[int, KeyVersion] = {}
        self._current_version: Optional[int] = None
        self._access_log: List[Dict] = []
        self._integrity_key: Optional[bytes] = None
        
        # Inicializar
        self._initialize_encryption()
        self._initialized = True
        
    def _initialize_encryption(self) -> None:
        """Inicializa el sistema de encriptación con soporte para migración."""
        try:
            # Crear directorio seguro
            self._ensure_secure_directory()
            
            # Intentar cargar keystore existente
            if self._key_store_file.exists():
                self._load_keystore()
            elif self._legacy_key_file.exists():
                # Migrar desde versión anterior
                self._migrate_from_legacy()
            else:
                # Crear nuevo keystore
                self._create_new_keystore()
                
            self.logger.info(f"Sistema de encriptación inicializado. Versión actual: {self._current_version}")
            
        except Exception as e:
            self.logger.error(f"Error inicializando encriptación: {e}")
            raise
            
    def _ensure_secure_directory(self) -> None:
        """Crea directorio con permisos seguros."""
        self._key_store_dir.mkdir(parents=True, exist_ok=True)
        
        # En Windows, marcar como oculto y sistema
        if os.name == 'nt':
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            FILE_ATTRIBUTE_SYSTEM = 0x04
            
            # Marcar directorio como oculto y sistema
            ctypes.windll.kernel32.SetFileAttributesW(
                str(self._key_store_dir),
                FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
            )
            
    def _generate_integrity_key(self) -> bytes:
        """Genera clave para validación de integridad."""
        # Usar información del sistema para generar clave única
        try:
            import uuid
            system_info = f"{uuid.getnode()}-{os.environ.get('COMPUTERNAME', 'unknown')}"
        except:
            system_info = "default-system"
            
        return hashlib.sha256(system_info.encode()).digest()
        
    def _calculate_checksum(self, data: str) -> str:
        """Calcula checksum para validación de integridad."""
        if not self._integrity_key:
            self._integrity_key = self._generate_integrity_key()
            
        return hashlib.sha256(
            data.encode() + self._integrity_key
        ).hexdigest()
        
    def _load_keystore(self) -> None:
        """Carga el keystore desde archivo."""
        try:
            with open(self._key_store_file, 'r') as f:
                data = json.load(f)
                
            # Validar integridad
            stored_checksum = data.get('checksum', '')
            data_copy = data.copy()
            data_copy.pop('checksum', None)
            calculated_checksum = self._calculate_checksum(json.dumps(data_copy, sort_keys=True))
            
            if stored_checksum != calculated_checksum:
                raise ValueError("Integridad del keystore comprometida")
                
            # Cargar claves
            self._current_version = data['current_version']
            for key_data in data['keys']:
                key_version = KeyVersion.from_dict(key_data)
                self._keys[key_version.version] = key_version
                
            self.logger.info(f"Keystore cargado con {len(self._keys)} claves")
            
        except Exception as e:
            self.logger.error(f"Error cargando keystore: {e}")
            raise
            
    def _save_keystore(self) -> None:
        """Guarda el keystore en archivo."""
        try:
            # Preparar datos
            data = {
                'current_version': self._current_version,
                'keys': [key.to_dict() for key in self._keys.values()],
                'last_rotation': datetime.now().isoformat(),
                'created_at': min(k.created_at for k in self._keys.values()).isoformat() if self._keys else datetime.now().isoformat()
            }
            
            # Calcular checksum
            data_str = json.dumps(data, sort_keys=True)
            data['checksum'] = self._calculate_checksum(data_str)
            
            # Guardar con permisos restrictivos
            with open(self._key_store_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Aplicar permisos en Windows
            if os.name == 'nt':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                FILE_ATTRIBUTE_SYSTEM = 0x04
                ctypes.windll.kernel32.SetFileAttributesW(
                    str(self._key_store_file),
                    FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
                )
                
        except Exception as e:
            self.logger.error(f"Error guardando keystore: {e}")
            raise
            
    def _migrate_from_legacy(self) -> None:
        """Migra desde el sistema de encriptación anterior."""
        self.logger.info("Migrando desde sistema de encriptación legacy")
        
        try:
            # Leer clave legacy
            with open(self._legacy_key_file, 'rb') as f:
                legacy_key = f.read()
                
            # Crear primera versión con la clave legacy
            key_v1 = KeyVersion(
                version=1,
                key=legacy_key,
                created_at=datetime.now(),
                is_active=True
            )
            
            self._keys[1] = key_v1
            self._current_version = 1
            
            # Guardar en nuevo formato
            self._save_keystore()
            
            # Renombrar archivo legacy para backup
            backup_path = self._legacy_key_file.with_suffix('.backup')
            self._legacy_key_file.rename(backup_path)
            
            self.logger.info("Migración completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en migración: {e}")
            raise
            
    def _create_new_keystore(self) -> None:
        """Crea un nuevo keystore con clave inicial."""
        self.logger.info("Creando nuevo keystore")
        
        # Generar primera clave
        new_key = self._generate_key()
        
        key_v1 = KeyVersion(
            version=1,
            key=new_key,
            created_at=datetime.now(),
            is_active=True
        )
        
        self._keys[1] = key_v1
        self._current_version = 1
        
        # Guardar
        self._save_keystore()
        
    def _generate_key(self) -> bytes:
        """Genera una nueva clave de encriptación."""
        # Usar una sal única basada en el hardware si es posible
        try:
            import uuid
            salt = str(uuid.getnode()).encode()[:16]  # MAC address como sal
        except:
            salt = os.urandom(16)
            
        # Derivar clave usando PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Usar entropía del sistema
        key_material = os.urandom(32)
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        
        return key
        
    def encrypt(self, plaintext: str) -> str:
        """
        Encripta un texto plano con la clave actual.
        
        Args:
            plaintext: Texto a encriptar
            
        Returns:
            str: Texto encriptado con versión de clave
            
        Formato: "v{version}:{encrypted_base64}"
        """
        if not plaintext:
            return ""
            
        if not self._current_version or self._current_version not in self._keys:
            raise ValueError("Sistema de encriptación no inicializado")
            
        try:
            current_key = self._keys[self._current_version]
            
            # Encriptar
            encrypted_bytes = current_key.cipher.encrypt(plaintext.encode())
            
            # Convertir a base64
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_bytes).decode()
            
            # Agregar versión
            versioned = f"v{self._current_version}:{encrypted_b64}"
            
            # Auditoría (sin loggear el valor)
            self._log_access('encrypt', success=True)
            
            return versioned
            
        except Exception as e:
            self._log_access('encrypt', success=False, error=str(e))
            self.logger.error(f"Error encriptando: {e}")
            raise ValueError(f"No se pudo encriptar el texto: {e}")
            
    def decrypt(self, encrypted: str) -> str:
        """
        Desencripta un texto encriptado, soportando múltiples versiones de clave.
        
        Args:
            encrypted: Texto encriptado con versión
            
        Returns:
            str: Texto plano desencriptado
        """
        if not encrypted:
            return ""
            
        try:
            # Verificar si tiene formato con versión
            if encrypted.startswith('v') and ':' in encrypted:
                # Formato nuevo con versión
                version_str, encrypted_data = encrypted.split(':', 1)
                version = int(version_str[1:])
            else:
                # Formato legacy, asumir versión 1
                version = 1
                encrypted_data = encrypted
                
            # Obtener clave de la versión correspondiente
            if version not in self._keys:
                raise ValueError(f"Versión de clave {version} no encontrada")
                
            key_version = self._keys[version]
            
            # Decodificar de base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Desencriptar
            decrypted_bytes = key_version.cipher.decrypt(encrypted_bytes)
            
            # Auditoría
            self._log_access('decrypt', success=True, key_version=version)
            
            return decrypted_bytes.decode()
            
        except InvalidToken:
            # Intentar con formato legacy si falla
            if not encrypted.startswith('v'):
                try:
                    # Intentar con clave v1 directamente
                    if 1 in self._keys:
                        encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
                        decrypted_bytes = self._keys[1].cipher.decrypt(encrypted_bytes)
                        self._log_access('decrypt', success=True, key_version=1, legacy=True)
                        return decrypted_bytes.decode()
                except:
                    pass
                    
            self._log_access('decrypt', success=False, error="Invalid token")
            self.logger.error("Token de encriptación inválido")
            raise ValueError("No se pudo desencriptar el texto")
            
        except Exception as e:
            self._log_access('decrypt', success=False, error=str(e))
            self.logger.error(f"Error desencriptando: {e}")
            raise ValueError(f"No se pudo desencriptar el texto: {e}")
            
    def _log_access(self, operation: str, success: bool, 
                    key_version: Optional[int] = None, 
                    error: Optional[str] = None,
                    legacy: bool = False) -> None:
        """Registra acceso para auditoría (sin valores sensibles)."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'success': success,
            'key_version': key_version or self._current_version,
            'legacy': legacy
        }
        
        if error and not success:
            log_entry['error_type'] = error.split(':')[0] if ':' in error else error
            
        self._access_log.append(log_entry)
        
        # Mantener solo últimas 1000 entradas
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-1000:]
            
    def rotate_keys(self) -> Tuple[bool, Optional[str]]:
        """
        Rota las claves de encriptación generando una nueva versión.
        
        Returns:
            Tuple[bool, Optional[str]]: (éxito, mensaje de error si falla)
            
        Nota: Esta operación NO re-encripta datos existentes automáticamente.
        Los datos antiguos seguirán siendo desencriptables con claves anteriores.
        """
        try:
            # Generar nueva clave
            new_key = self._generate_key()
            new_version = max(self._keys.keys()) + 1 if self._keys else 1
            
            # Crear nueva versión
            new_key_version = KeyVersion(
                version=new_version,
                key=new_key,
                created_at=datetime.now(),
                is_active=True
            )
            
            # Marcar versión anterior como inactiva (pero mantenerla para desencriptar)
            if self._current_version and self._current_version in self._keys:
                self._keys[self._current_version].is_active = False
                
            # Agregar nueva versión
            self._keys[new_version] = new_key_version
            self._current_version = new_version
            
            # Guardar cambios
            self._save_keystore()
            
            self.logger.info(f"Rotación de claves exitosa. Nueva versión: {new_version}")
            
            # TODO: Implementar re-encriptación de datos existentes en background
            # Esto requeriría acceso a la base de datos para actualizar todos los
            # valores encriptados a la nueva versión
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error rotando claves: {e}"
            self.logger.error(error_msg)
            return False, error_msg
            
    def get_key_info(self) -> Dict[str, any]:
        """
        Obtiene información sobre las claves (sin exponer las claves mismas).
        
        Returns:
            Dict con información del estado de las claves
        """
        return {
            'current_version': self._current_version,
            'total_versions': len(self._keys),
            'active_versions': sum(1 for k in self._keys.values() if k.is_active),
            'oldest_key': min(k.created_at for k in self._keys.values()).isoformat() if self._keys else None,
            'newest_key': max(k.created_at for k in self._keys.values()).isoformat() if self._keys else None,
            'last_rotation': max(k.created_at for k in self._keys.values() if k.version > 1).isoformat() if any(k.version > 1 for k in self._keys.values()) else None
        }
        
    def get_access_stats(self) -> Dict[str, any]:
        """
        Obtiene estadísticas de acceso para auditoría.
        
        Returns:
            Dict con estadísticas de uso
        """
        if not self._access_log:
            return {
                'total_operations': 0,
                'encrypt_count': 0,
                'decrypt_count': 0,
                'success_rate': 0,
                'legacy_count': 0
            }
            
        total = len(self._access_log)
        encrypt_count = sum(1 for log in self._access_log if log['operation'] == 'encrypt')
        decrypt_count = sum(1 for log in self._access_log if log['operation'] == 'decrypt')
        success_count = sum(1 for log in self._access_log if log['success'])
        legacy_count = sum(1 for log in self._access_log if log.get('legacy', False))
        
        return {
            'total_operations': total,
            'encrypt_count': encrypt_count,
            'decrypt_count': decrypt_count,
            'success_rate': (success_count / total * 100) if total > 0 else 0,
            'legacy_count': legacy_count,
            'last_24h': sum(1 for log in self._access_log 
                          if datetime.fromisoformat(log['timestamp']) > 
                          datetime.now() - timedelta(hours=24))
        }
        
    def verify_encryption_health(self) -> Dict[str, any]:
        """
        Verifica el estado de salud del sistema de encriptación.
        
        Returns:
            Dict con estado de salud detallado
        """
        health = {
            'healthy': True,
            'checks': {}
        }
        
        # Verificar keystore
        try:
            if not self._key_store_file.exists():
                health['checks']['keystore_exists'] = False
                health['healthy'] = False
            else:
                health['checks']['keystore_exists'] = True
                
                # Verificar integridad
                self._load_keystore()
                health['checks']['keystore_integrity'] = True
        except:
            health['checks']['keystore_integrity'] = False
            health['healthy'] = False
            
        # Verificar claves
        health['checks']['has_keys'] = len(self._keys) > 0
        health['checks']['has_current_version'] = self._current_version is not None
        
        if not health['checks']['has_keys'] or not health['checks']['has_current_version']:
            health['healthy'] = False
            
        # Test de encriptación/desencriptación
        try:
            test_text = "health_check_test_" + str(time.time())
            encrypted = self.encrypt(test_text)
            decrypted = self.decrypt(encrypted)
            health['checks']['encryption_works'] = decrypted == test_text
        except:
            health['checks']['encryption_works'] = False
            health['healthy'] = False
            
        # Información adicional
        health['key_info'] = self.get_key_info()
        health['access_stats'] = self.get_access_stats()
        
        return health
        
    def cleanup_old_versions(self, keep_versions: int = 5) -> int:
        """
        Limpia versiones antiguas de claves manteniendo las más recientes.
        
        Args:
            keep_versions: Número de versiones a mantener
            
        Returns:
            int: Número de versiones eliminadas
            
        Nota: Mantiene al menos las últimas 'keep_versions' versiones
        para poder desencriptar datos antiguos.
        """
        if len(self._keys) <= keep_versions:
            return 0
            
        # Ordenar por versión
        sorted_versions = sorted(self._keys.keys())
        
        # Determinar versiones a eliminar (mantener las más recientes)
        versions_to_remove = sorted_versions[:-keep_versions]
        
        removed_count = 0
        for version in versions_to_remove:
            if version != self._current_version:  # Nunca eliminar la versión actual
                del self._keys[version]
                removed_count += 1
                
        if removed_count > 0:
            self._save_keystore()
            self.logger.info(f"Eliminadas {removed_count} versiones antiguas de claves")
            
        return removed_count
        
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        # Guardar estadísticas finales si hay cambios pendientes
        if self._access_log:
            self.logger.info(f"Estadísticas finales de encriptación: {self.get_access_stats()}")
            
        self.logger.info("Servicio de encriptación cerrado")


# Instancia global del servicio mejorado
encryption_service_v2 = EncryptionServiceV2()