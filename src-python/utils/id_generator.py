"""
Generador de IDs únicos para entidades del sistema.

Proporciona diferentes estrategias de generación de IDs según
el tipo de entidad y requisitos de unicidad.
"""
import uuid
import time
import secrets
from typing import Optional
from enum import Enum


class IDType(Enum):
    """Tipos de ID soportados."""
    UUID = "uuid"
    ULID = "ulid"
    CUSTOM = "custom"


class IDGenerator:
    """Generador de IDs únicos para diferentes entidades."""
    
    @staticmethod
    def generate_camera_id() -> str:
        """
        Genera un ID único para una cámara.
        
        Usa UUID v4 por defecto para garantizar unicidad global.
        
        Returns:
            str: ID único en formato UUID
            
        Example:
            >>> camera_id = IDGenerator.generate_camera_id()
            >>> print(camera_id)
            "550e8400-e29b-41d4-a716-446655440000"
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_scan_id() -> str:
        """
        Genera un ID único para un escaneo de red.
        
        Returns:
            str: ID único en formato UUID
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_snapshot_id() -> str:
        """
        Genera un ID único para un snapshot.
        
        Returns:
            str: ID único en formato UUID
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_custom_id(prefix: str, include_timestamp: bool = True) -> str:
        """
        Genera un ID personalizado con prefijo opcional.
        
        Args:
            prefix: Prefijo para el ID (ej: "CAM", "SCAN")
            include_timestamp: Si incluir timestamp en el ID
            
        Returns:
            str: ID personalizado
            
        Example:
            >>> custom_id = IDGenerator.generate_custom_id("CAM")
            >>> print(custom_id)
            "CAM-1674567890-a2f4b8c1"
        """
        parts = [prefix]
        
        if include_timestamp:
            parts.append(str(int(time.time())))
        
        # Agregar parte aleatoria para unicidad
        parts.append(secrets.token_hex(4))
        
        return "-".join(parts)
    
    @staticmethod
    def generate_readable_id(entity_type: str, brand: Optional[str] = None) -> str:
        """
        Genera un ID legible por humanos.
        
        Args:
            entity_type: Tipo de entidad ("camera", "scan", etc)
            brand: Marca opcional para incluir en el ID
            
        Returns:
            str: ID legible pero único
            
        Example:
            >>> readable_id = IDGenerator.generate_readable_id("camera", "dahua")
            >>> print(readable_id)
            "camera-dahua-2024-a2f4"
        """
        parts = [entity_type.lower()]
        
        if brand:
            parts.append(brand.lower())
        
        # Agregar año actual
        parts.append(str(time.localtime().tm_year))
        
        # Agregar parte aleatoria corta
        parts.append(secrets.token_hex(2))
        
        return "-".join(parts)
    
    @staticmethod
    def validate_uuid(id_string: str) -> bool:
        """
        Valida si un string es un UUID válido.
        
        Args:
            id_string: String a validar
            
        Returns:
            bool: True si es un UUID válido
        """
        try:
            uuid.UUID(id_string)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def migrate_legacy_id(legacy_id: str) -> str:
        """
        Migra un ID legacy al nuevo formato UUID.
        
        Mantiene un mapeo determinístico para IDs antiguos,
        útil durante migraciones.
        
        Args:
            legacy_id: ID en formato antiguo
            
        Returns:
            str: Nuevo ID en formato UUID
        """
        # Usar UUID v5 (determinístico) basado en namespace
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return str(uuid.uuid5(namespace, legacy_id))


# Funciones de conveniencia
def generate_camera_id() -> str:
    """Genera un ID único para una cámara."""
    return IDGenerator.generate_camera_id()


def generate_scan_id() -> str:
    """Genera un ID único para un escaneo."""
    return IDGenerator.generate_scan_id()


def generate_snapshot_id() -> str:
    """Genera un ID único para un snapshot."""
    return IDGenerator.generate_snapshot_id()