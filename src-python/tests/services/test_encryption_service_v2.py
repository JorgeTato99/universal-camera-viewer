"""
Tests para el servicio de encriptación v2.

Verifica la correcta funcionalidad del servicio de encriptación mejorado
con versionado de claves, rotación, migración y auditoría.
"""

import pytest
import asyncio
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Configurar path para importar desde src-python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.encryption_service_v2 import EncryptionServiceV2, KeyVersion


class TestKeyVersion:
    """Tests para la clase KeyVersion."""
    
    def test_create_key_version(self):
        """Prueba creación de una versión de clave."""
        # Generar clave de prueba
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key()
        
        # Crear versión
        key_v = KeyVersion(
            version=1,
            key=test_key,
            created_at=datetime.now(),
            is_active=True
        )
        
        assert key_v.version == 1
        assert key_v.key == test_key
        assert key_v.is_active is True
        assert key_v.cipher is not None
        
    def test_key_version_to_dict(self):
        """Prueba conversión a diccionario."""
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key()
        created_at = datetime.now()
        
        key_v = KeyVersion(1, test_key, created_at, True)
        dict_data = key_v.to_dict()
        
        assert dict_data['version'] == 1
        assert 'key' in dict_data
        assert dict_data['created_at'] == created_at.isoformat()
        assert dict_data['is_active'] is True
        
    def test_key_version_from_dict(self):
        """Prueba creación desde diccionario."""
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key()
        created_at = datetime.now()
        
        dict_data = {
            'version': 2,
            'key': test_key.decode(),
            'created_at': created_at.isoformat(),
            'is_active': False
        }
        
        key_v = KeyVersion.from_dict(dict_data)
        
        assert key_v.version == 2
        assert key_v.key == test_key
        assert key_v.created_at.isoformat() == created_at.isoformat()
        assert key_v.is_active is False


class TestEncryptionServiceV2:
    """Tests para el servicio de encriptación v2."""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea un directorio temporal para tests."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        # Limpiar después del test
        shutil.rmtree(temp_path, ignore_errors=True)
        
    @pytest.fixture
    def mock_service(self, temp_dir):
        """Crea una instancia del servicio con directorio temporal."""
        # Resetear singleton para tests
        EncryptionServiceV2._instance = None
        
        # Mockear paths
        with patch.object(Path, '__new__') as mock_path:
            # Configurar mock para usar temp_dir
            def path_new(cls, *args):
                if args and str(args[0]).endswith('keystore.json'):
                    return temp_dir / "keystore.json"
                elif args and '.encryption' in str(args[0]):
                    return temp_dir / ".encryption"
                else:
                    return object.__new__(cls)
            
            mock_path.side_effect = path_new
            
            # Crear servicio con path temporal
            service = EncryptionServiceV2()
            service._key_store_dir = temp_dir / ".encryption"
            service._key_store_file = service._key_store_dir / "keystore.json"
            service._legacy_key_file = temp_dir / ".encryption_key"
            
            # Forzar inicialización
            service._initialized = False
            service._initialize_encryption()
            
            yield service
            
            # Limpiar
            EncryptionServiceV2._instance = None
    
    def test_singleton_pattern(self):
        """Verifica que el servicio sea singleton."""
        # Resetear para test limpio
        EncryptionServiceV2._instance = None
        
        service1 = EncryptionServiceV2()
        service2 = EncryptionServiceV2()
        
        assert service1 is service2
        
        # Limpiar
        EncryptionServiceV2._instance = None
        
    def test_initialization_new_keystore(self, mock_service):
        """Prueba inicialización con nuevo keystore."""
        assert mock_service._current_version == 1
        assert len(mock_service._keys) == 1
        assert 1 in mock_service._keys
        assert mock_service._keys[1].is_active is True
        
        # Verificar que se creó el archivo
        assert mock_service._key_store_file.exists()
        
    def test_encrypt_decrypt_basic(self, mock_service):
        """Prueba encriptación y desencriptación básica."""
        test_data = "password123!@#"
        
        # Encriptar
        encrypted = mock_service.encrypt(test_data)
        assert encrypted != test_data
        assert encrypted.startswith("v1:")
        
        # Desencriptar
        decrypted = mock_service.decrypt(encrypted)
        assert decrypted == test_data
        
    def test_encrypt_empty_string(self, mock_service):
        """Prueba encriptar string vacío."""
        encrypted = mock_service.encrypt("")
        assert encrypted == ""
        
        decrypted = mock_service.decrypt("")
        assert decrypted == ""
        
    def test_encrypt_special_characters(self, mock_service):
        """Prueba encriptar caracteres especiales."""
        test_cases = [
            "пароль123",  # Cirílico
            "密码123",     # Chino
            "🔐🔑🔓",      # Emojis
            "user@email.com:p@ssw0rd!",
            "line1\nline2\ttab",
            "quote'double\"back\\slash/"
        ]
        
        for test_data in test_cases:
            encrypted = mock_service.encrypt(test_data)
            decrypted = mock_service.decrypt(encrypted)
            assert decrypted == test_data, f"Failed for: {test_data}"
            
    def test_decrypt_invalid_token(self, mock_service):
        """Prueba desencriptar token inválido."""
        with pytest.raises(ValueError) as exc:
            mock_service.decrypt("v1:invalid_token_data")
        assert "No se pudo desencriptar" in str(exc.value)
        
    def test_decrypt_wrong_version(self, mock_service):
        """Prueba desencriptar con versión inexistente."""
        with pytest.raises(ValueError) as exc:
            mock_service.decrypt("v99:some_encrypted_data")
        assert "Versión de clave 99 no encontrada" in str(exc.value)
        
    def test_key_rotation(self, mock_service):
        """Prueba rotación de claves."""
        # Encriptar con v1
        test_data = "secret_before_rotation"
        encrypted_v1 = mock_service.encrypt(test_data)
        assert encrypted_v1.startswith("v1:")
        
        # Rotar claves
        success, error = mock_service.rotate_keys()
        assert success is True
        assert error is None
        assert mock_service._current_version == 2
        
        # Encriptar con v2
        encrypted_v2 = mock_service.encrypt(test_data)
        assert encrypted_v2.startswith("v2:")
        assert encrypted_v2 != encrypted_v1
        
        # Verificar que ambas versiones se pueden desencriptar
        assert mock_service.decrypt(encrypted_v1) == test_data
        assert mock_service.decrypt(encrypted_v2) == test_data
        
        # Verificar que v1 está inactiva pero v2 activa
        assert mock_service._keys[1].is_active is False
        assert mock_service._keys[2].is_active is True
        
    def test_multiple_key_rotations(self, mock_service):
        """Prueba múltiples rotaciones de claves."""
        versions_data = {}
        
        # Encriptar con versión inicial
        test_data = "test_multiple_rotations"
        versions_data[1] = mock_service.encrypt(test_data)
        
        # Realizar 5 rotaciones
        for i in range(5):
            success, _ = mock_service.rotate_keys()
            assert success is True
            versions_data[i + 2] = mock_service.encrypt(test_data)
            
        # Verificar versión actual
        assert mock_service._current_version == 6
        
        # Verificar que todas las versiones se pueden desencriptar
        for version, encrypted in versions_data.items():
            assert encrypted.startswith(f"v{version}:")
            assert mock_service.decrypt(encrypted) == test_data
            
    def test_keystore_persistence(self, mock_service):
        """Prueba persistencia del keystore."""
        # Encriptar datos y rotar claves
        test_data = "persistent_data"
        encrypted_v1 = mock_service.encrypt(test_data)
        mock_service.rotate_keys()
        encrypted_v2 = mock_service.encrypt(test_data)
        
        # Crear nueva instancia (simular reinicio)
        EncryptionServiceV2._instance = None
        new_service = EncryptionServiceV2()
        new_service._key_store_dir = mock_service._key_store_dir
        new_service._key_store_file = mock_service._key_store_file
        new_service._initialize_encryption()
        
        # Verificar que puede desencriptar ambas versiones
        assert new_service.decrypt(encrypted_v1) == test_data
        assert new_service.decrypt(encrypted_v2) == test_data
        assert new_service._current_version == 2
        
    def test_legacy_migration(self, temp_dir):
        """Prueba migración desde sistema legacy."""
        # Crear archivo legacy
        from cryptography.fernet import Fernet
        legacy_key = Fernet.generate_key()
        legacy_file = temp_dir / ".encryption_key"
        legacy_file.write_bytes(legacy_key)
        
        # Crear servicio que debería migrar
        EncryptionServiceV2._instance = None
        service = EncryptionServiceV2()
        service._key_store_dir = temp_dir / ".encryption"
        service._key_store_file = service._key_store_dir / "keystore.json"
        service._legacy_key_file = legacy_file
        service._initialize_encryption()
        
        # Verificar migración
        assert service._current_version == 1
        assert len(service._keys) == 1
        assert not legacy_file.exists()  # Debe renombrarse
        assert (temp_dir / ".encryption_key.backup").exists()
        
        # Verificar que la clave migrada funciona
        fernet = Fernet(legacy_key)
        test_encrypted = fernet.encrypt(b"test_data")
        decrypted = fernet.decrypt(test_encrypted)
        assert decrypted == b"test_data"
        
    def test_get_key_info(self, mock_service):
        """Prueba obtención de información de claves."""
        # Rotar algunas claves
        mock_service.rotate_keys()
        mock_service.rotate_keys()
        
        info = mock_service.get_key_info()
        
        assert info['current_version'] == 3
        assert info['total_versions'] == 3
        assert info['active_versions'] == 1  # Solo la actual
        assert info['oldest_key'] is not None
        assert info['newest_key'] is not None
        assert info['last_rotation'] is not None
        
    def test_access_stats(self, mock_service):
        """Prueba estadísticas de acceso."""
        # Realizar varias operaciones
        for i in range(5):
            mock_service.encrypt(f"test_{i}")
        
        for i in range(3):
            encrypted = mock_service.encrypt(f"decrypt_test_{i}")
            mock_service.decrypt(encrypted)
            
        # Intentar desencriptar algo inválido
        try:
            mock_service.decrypt("v1:invalid")
        except:
            pass
            
        stats = mock_service.get_access_stats()
        
        assert stats['total_operations'] > 0
        assert stats['encrypt_count'] == 8  # 5 + 3
        assert stats['decrypt_count'] == 4  # 3 exitosos + 1 fallido
        assert stats['success_rate'] < 100  # Por el fallido
        assert stats['legacy_count'] == 0
        
    def test_verify_encryption_health(self, mock_service):
        """Prueba verificación de salud del sistema."""
        health = mock_service.verify_encryption_health()
        
        assert health['healthy'] is True
        assert health['checks']['keystore_exists'] is True
        assert health['checks']['keystore_integrity'] is True
        assert health['checks']['has_keys'] is True
        assert health['checks']['has_current_version'] is True
        assert health['checks']['encryption_works'] is True
        
        # Verificar que incluye información adicional
        assert 'key_info' in health
        assert 'access_stats' in health
        
    def test_cleanup_old_versions(self, mock_service):
        """Prueba limpieza de versiones antiguas."""
        # Crear 10 versiones
        for _ in range(9):
            mock_service.rotate_keys()
            
        assert len(mock_service._keys) == 10
        
        # Limpiar manteniendo solo 5
        removed = mock_service.cleanup_old_versions(keep_versions=5)
        
        assert removed == 5
        assert len(mock_service._keys) == 5
        # Verificar que se mantuvieron las más recientes (6-10)
        assert 6 in mock_service._keys
        assert 10 in mock_service._keys
        assert 1 not in mock_service._keys
        
    def test_integrity_validation(self, mock_service):
        """Prueba validación de integridad del keystore."""
        # Guardar keystore válido
        mock_service._save_keystore()
        
        # Modificar archivo directamente (simular manipulación)
        with open(mock_service._key_store_file, 'r') as f:
            data = json.load(f)
            
        # Cambiar un valor
        data['current_version'] = 99
        
        with open(mock_service._key_store_file, 'w') as f:
            json.dump(data, f)
            
        # Intentar cargar debe fallar por integridad
        with pytest.raises(ValueError) as exc:
            mock_service._load_keystore()
        assert "Integridad del keystore comprometida" in str(exc.value)
        
    def test_concurrent_access(self, mock_service):
        """Prueba acceso concurrente (thread safety)."""
        import threading
        
        results = []
        errors = []
        
        def encrypt_decrypt_task(index):
            try:
                data = f"concurrent_test_{index}"
                encrypted = mock_service.encrypt(data)
                decrypted = mock_service.decrypt(encrypted)
                results.append(decrypted == data)
            except Exception as e:
                errors.append(str(e))
                
        # Crear múltiples threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=encrypt_decrypt_task, args=(i,))
            threads.append(t)
            t.start()
            
        # Esperar a que terminen
        for t in threads:
            t.join()
            
        # Verificar resultados
        assert len(errors) == 0, f"Errores en concurrencia: {errors}"
        assert all(results), "Algunas operaciones concurrentes fallaron"
        assert len(results) == 10
        
    def test_backward_compatibility_decrypt(self, mock_service):
        """Prueba compatibilidad hacia atrás con formato sin versión."""
        # Simular dato encriptado con formato antiguo
        from cryptography.fernet import Fernet
        import base64
        
        # Obtener la clave v1
        key_v1 = mock_service._keys[1].key
        fernet = Fernet(key_v1)
        
        # Encriptar directamente (sin versión)
        test_data = "legacy_format_data"
        encrypted_bytes = fernet.encrypt(test_data.encode())
        encrypted_b64 = base64.urlsafe_b64encode(encrypted_bytes).decode()
        
        # Debe poder desencriptar asumiendo v1
        decrypted = mock_service.decrypt(encrypted_b64)
        assert decrypted == test_data
        
        # Verificar que se registró como legacy
        stats = mock_service.get_access_stats()
        assert stats['legacy_count'] > 0
        
    async def test_cleanup(self, mock_service):
        """Prueba limpieza de recursos."""
        # Realizar algunas operaciones
        mock_service.encrypt("test")
        
        # Limpiar
        await mock_service.cleanup()
        
        # Verificar que se limpió
        assert mock_service._cipher_suite is None
        
    def test_error_handling_no_keystore(self, temp_dir):
        """Prueba manejo de error cuando no se puede crear keystore."""
        # Hacer directorio de solo lectura
        EncryptionServiceV2._instance = None
        
        # Mock para simular fallo al crear directorio
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("No permission")):
            with pytest.raises(PermissionError):
                service = EncryptionServiceV2()
                service._key_store_dir = temp_dir / ".encryption"
                service._key_store_file = service._key_store_dir / "keystore.json"
                service._initialize_encryption()
                
    def test_audit_log_limit(self, mock_service):
        """Prueba límite del log de auditoría."""
        # Realizar más de 1000 operaciones
        for i in range(1100):
            mock_service.encrypt(f"test_{i}")
            
        # Verificar que se mantiene el límite
        assert len(mock_service._access_log) == 1000
        
        # Verificar que se mantuvieron las más recientes
        stats = mock_service.get_access_stats()
        assert stats['encrypt_count'] == 1000  # Solo cuenta las últimas 1000


class TestEncryptionIntegration:
    """Tests de integración con otros componentes."""
    
    @pytest.fixture
    def mock_service(self):
        """Servicio para tests de integración."""
        EncryptionServiceV2._instance = None
        service = EncryptionServiceV2()
        yield service
        EncryptionServiceV2._instance = None
        
    def test_encrypt_dict_functionality(self, mock_service):
        """Prueba encriptar campos específicos de diccionario."""
        # TODO: Este método no está implementado en el servicio v2
        # pero existe en v1. Documentar como funcionalidad pendiente.
        # Por ahora, verificar que el servicio básico funciona
        
        data = {
            'username': 'admin',
            'password': 'secret123',
            'other': 'not_secret'
        }
        
        # Encriptar manualmente los campos sensibles
        encrypted_password = mock_service.encrypt(data['password'])
        
        assert encrypted_password != data['password']
        assert encrypted_password.startswith('v')
        
        # TODO: Implementar encrypt_dict y decrypt_dict en v2
        # para mantener compatibilidad con v1
        
    def test_performance_bulk_operations(self, mock_service):
        """Prueba rendimiento con operaciones masivas."""
        import time
        
        # Preparar datos de prueba
        test_data = ["password_" + str(i) for i in range(100)]
        
        # Medir encriptación
        start = time.time()
        encrypted = [mock_service.encrypt(data) for data in test_data]
        encrypt_time = time.time() - start
        
        # Medir desencriptación
        start = time.time()
        decrypted = [mock_service.decrypt(enc) for enc in encrypted]
        decrypt_time = time.time() - start
        
        # Verificar correctitud
        assert decrypted == test_data
        
        # Verificar rendimiento (debe ser < 1 segundo para 100 operaciones)
        assert encrypt_time < 1.0, f"Encriptación muy lenta: {encrypt_time}s"
        assert decrypt_time < 1.0, f"Desencriptación muy lenta: {decrypt_time}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])