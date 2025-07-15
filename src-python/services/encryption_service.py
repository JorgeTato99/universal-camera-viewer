"""
Servicio de encriptación para credenciales.

Gestiona la encriptación y desencriptación segura de credenciales de cámaras.
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path

from services.base_service import BaseService


class EncryptionService(BaseService):
    """Servicio singleton para encriptación de credenciales."""
    
    _instance = None
    
    def __new__(cls) -> "EncryptionService":
        """Garantiza una única instancia del servicio."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio de encriptación."""
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self._cipher_suite: Optional[Fernet] = None
        self._key_file = Path("data/.encryption_key")
        self._initialize_encryption()
        self._initialized = True
        
    def _initialize_encryption(self) -> None:
        """Inicializa el sistema de encriptación."""
        try:
            # Intentar cargar clave existente
            encryption_key = self._load_or_create_key()
            self._cipher_suite = Fernet(encryption_key)
            self.logger.info("Sistema de encriptación inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error inicializando encriptación: {e}")
            raise
            
    def _load_or_create_key(self) -> bytes:
        """
        Carga la clave de encriptación existente o crea una nueva.
        
        Returns:
            bytes: Clave de encriptación
        """
        # Crear directorio si no existe
        self._key_file.parent.mkdir(exist_ok=True)
        
        if self._key_file.exists():
            # Cargar clave existente
            try:
                with open(self._key_file, 'rb') as f:
                    key = f.read()
                self.logger.debug("Clave de encriptación cargada desde archivo")
                return key
            except Exception as e:
                self.logger.error(f"Error cargando clave de encriptación: {e}")
                raise
        else:
            # Generar nueva clave
            key = self._generate_key()
            
            # Guardar clave de forma segura
            try:
                # Establecer permisos restrictivos en Windows
                with open(self._key_file, 'wb') as f:
                    f.write(key)
                
                # En Windows, intentar ocultar el archivo
                if os.name == 'nt':
                    import ctypes
                    FILE_ATTRIBUTE_HIDDEN = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(
                        str(self._key_file), FILE_ATTRIBUTE_HIDDEN
                    )
                    
                self.logger.info("Nueva clave de encriptación generada y guardada")
                return key
            except Exception as e:
                self.logger.error(f"Error guardando clave de encriptación: {e}")
                raise
                
    def _generate_key(self) -> bytes:
        """
        Genera una nueva clave de encriptación.
        
        Returns:
            bytes: Nueva clave de encriptación
        """
        # Usar una sal única basada en el hardware si es posible
        try:
            # Intentar obtener ID único del sistema
            import uuid
            salt = str(uuid.getnode()).encode()[:16]  # MAC address como sal
        except:
            # Fallback a sal aleatoria
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
        Encripta un texto plano.
        
        Args:
            plaintext: Texto a encriptar
            
        Returns:
            str: Texto encriptado en base64
            
        Raises:
            ValueError: Si no se puede encriptar
        """
        if not plaintext:
            return ""
            
        if not self._cipher_suite:
            raise ValueError("Sistema de encriptación no inicializado")
            
        try:
            # Encriptar
            encrypted_bytes = self._cipher_suite.encrypt(plaintext.encode())
            
            # Convertir a base64 para almacenamiento
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode()
            
            return encrypted_str
        except Exception as e:
            self.logger.error(f"Error encriptando texto: {e}")
            raise ValueError(f"No se pudo encriptar el texto: {e}")
            
    def decrypt(self, encrypted: str) -> str:
        """
        Desencripta un texto encriptado.
        
        Args:
            encrypted: Texto encriptado en base64
            
        Returns:
            str: Texto plano desencriptado
            
        Raises:
            ValueError: Si no se puede desencriptar
        """
        if not encrypted:
            return ""
            
        if not self._cipher_suite:
            raise ValueError("Sistema de encriptación no inicializado")
            
        try:
            # Decodificar de base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
            
            # Desencriptar
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"Error desencriptando texto: {e}")
            raise ValueError(f"No se pudo desencriptar el texto: {e}")
            
    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Encripta campos específicos de un diccionario.
        
        Args:
            data: Diccionario con datos
            fields: Lista de campos a encriptar
            
        Returns:
            dict: Diccionario con campos encriptados
        """
        encrypted_data = data.copy()
        
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
                except Exception as e:
                    self.logger.error(f"Error encriptando campo {field}: {e}")
                    
        return encrypted_data
        
    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Desencripta campos específicos de un diccionario.
        
        Args:
            data: Diccionario con datos encriptados
            fields: Lista de campos a desencriptar
            
        Returns:
            dict: Diccionario con campos desencriptados
        """
        decrypted_data = data.copy()
        
        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except Exception as e:
                    self.logger.error(f"Error desencriptando campo {field}: {e}")
                    # Mantener valor original si falla
                    
        return decrypted_data
        
    def rotate_key(self) -> bool:
        """
        Rota la clave de encriptación (para seguridad periódica).
        
        Returns:
            bool: True si la rotación fue exitosa
        """
        try:
            # TODO: Implementar rotación de claves
            # 1. Generar nueva clave
            # 2. Re-encriptar todos los datos con nueva clave
            # 3. Guardar nueva clave
            # 4. Eliminar clave antigua
            
            self.logger.warning("Rotación de claves no implementada aún")
            return False
            
        except Exception as e:
            self.logger.error(f"Error rotando clave: {e}")
            return False
            
    def verify_encryption_health(self) -> bool:
        """
        Verifica que el sistema de encriptación esté funcionando.
        
        Returns:
            bool: True si el sistema está saludable
        """
        try:
            # Prueba de encriptación/desencriptación
            test_text = "test_encryption_health_check"
            encrypted = self.encrypt(test_text)
            decrypted = self.decrypt(encrypted)
            
            return decrypted == test_text
            
        except Exception as e:
            self.logger.error(f"Sistema de encriptación no saludable: {e}")
            return False
            
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self._cipher_suite = None
        self.logger.info("Servicio de encriptación cerrado")


# Instancia global del servicio
encryption_service = EncryptionService()