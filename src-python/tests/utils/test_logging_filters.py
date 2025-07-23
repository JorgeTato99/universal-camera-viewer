"""
Tests para los filtros de logging.

Verifica que los filtros de logging detecten y saniticen correctamente
información sensible antes de que sea escrita a los logs.
"""

import pytest
import logging
import re
from unittest.mock import Mock, MagicMock
from pathlib import Path
import sys

# Configurar path para importar desde src-python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging_filters import (
    SensitiveDataFilter,
    URLSanitizerFilter,
    CommandSanitizerFilter,
    ContextualFilter,
    EnvironmentBasedFilter,
    setup_logging_filters
)


class TestSensitiveDataFilter:
    """Tests para el filtro de datos sensibles."""
    
    @pytest.fixture
    def filter_prod(self):
        """Filtro configurado para producción."""
        return SensitiveDataFilter(environment='production')
        
    @pytest.fixture
    def filter_dev(self):
        """Filtro configurado para desarrollo."""
        return SensitiveDataFilter(environment='development')
        
    def test_filter_urls_in_message(self, filter_prod):
        """Prueba filtrado de URLs con credenciales."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Connecting to rtsp://admin:password123@192.168.1.100/stream",
            args=(),
            exc_info=None
        )
        
        # Aplicar filtro
        result = filter_prod.filter(record)
        
        assert result is True  # Siempre retorna True
        assert "password123" not in record.msg
        assert "admin" not in record.msg
        assert "***:***" in record.msg
        
    def test_filter_multiple_patterns(self, filter_prod):
        """Prueba filtrado de múltiples patrones sensibles."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Using API_KEY=secret123 and password:mypass to connect",
            args=(),
            exc_info=None
        )
        
        filter_prod.filter(record)
        
        assert "secret123" not in record.msg
        assert "mypass" not in record.msg
        assert "[REDACTED]" in record.msg
        
    def test_filter_args_dict(self, filter_prod):
        """Prueba filtrado de argumentos tipo diccionario."""
        args_dict = {
            'username': 'admin',
            'password': 'secret123',
            'host': 'localhost'
        }
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Login attempt with: %(username)s",
            args=args_dict,
            exc_info=None
        )
        
        filter_prod.filter(record)
        
        assert record.args['password'] == '[REDACTED]'
        assert record.args['username'] == 'admin'  # No es sensible por defecto
        assert record.args['host'] == 'localhost'
        
    def test_filter_args_tuple(self, filter_prod):
        """Prueba filtrado de argumentos tipo tupla."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Connecting to %s with password %s",
            args=("rtsp://user:pass@host", "another_pass"),
            exc_info=None
        )
        
        filter_prod.filter(record)
        
        assert isinstance(record.args, tuple)
        assert "pass" not in record.args[0]
        assert "***:***" in record.args[0]
        
    def test_filter_exception_info(self, filter_prod):
        """Prueba filtrado de información de excepción."""
        try:
            raise ValueError("Error connecting to rtsp://admin:secret@camera/stream")
        except ValueError as e:
            exc_info = sys.exc_info()
            
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Connection failed",
            args=(),
            exc_info=exc_info
        )
        
        filter_prod.filter(record)
        
        # La excepción debe ser sanitizada
        exception = record.exc_info[1]
        assert "secret" not in str(exception.args[0])
        
    def test_development_sanitization(self, filter_dev):
        """Prueba sanitización menos agresiva en desarrollo."""
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Debug: password=secret123 token=abc api-key=xyz",
            args=(),
            exc_info=None
        )
        
        filter_dev.filter(record)
        
        # En desarrollo debe ocultar passwords pero puede mostrar más info
        assert "secret123" not in record.msg
        assert "password=[REDACTED]" in record.msg
        
    def test_custom_patterns(self):
        """Prueba filtro con patrones personalizados."""
        custom_patterns = [r'CUSTOM_SECRET=\S+']
        filter_custom = SensitiveDataFilter(additional_patterns=custom_patterns)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Config: CUSTOM_SECRET=my_secret_value",
            args=(),
            exc_info=None
        )
        
        filter_custom.filter(record)
        
        assert "my_secret_value" not in record.msg
        assert "[REDACTED]" in record.msg
        
    def test_hash_detection(self, filter_prod):
        """Prueba detección de hashes largos."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API key: a1b2c3d4e5f6789012345678901234567890abcd",
            args=(),
            exc_info=None
        )
        
        filter_prod.filter(record)
        
        assert "a1b2c3d4e5f6789012345678901234567890abcd" not in record.msg
        assert "[REDACTED]" in record.msg


class TestURLSanitizerFilter:
    """Tests para el filtro de URLs."""
    
    @pytest.fixture
    def filter_default(self):
        """Filtro con configuración por defecto."""
        return URLSanitizerFilter()
        
    @pytest.fixture
    def filter_show_user(self):
        """Filtro mostrando parcialmente el usuario."""
        return URLSanitizerFilter(show_user=True)
        
    def test_filter_single_url(self, filter_default):
        """Prueba filtrado de una URL."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Connecting to rtsp://admin:pass@camera.local:554/stream",
            args=(),
            exc_info=None
        )
        
        filter_default.filter(record)
        
        assert "pass" not in record.msg
        assert "admin" not in record.msg
        assert "***:***" in record.msg
        assert "camera.local:554/stream" in record.msg
        
    def test_filter_multiple_urls(self, filter_default):
        """Prueba filtrado de múltiples URLs."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Primary: http://user1:pass1@api.com, Backup: https://user2:pass2@backup.com",
            args=(),
            exc_info=None
        )
        
        filter_default.filter(record)
        
        assert "pass1" not in record.msg
        assert "pass2" not in record.msg
        assert "user1" not in record.msg
        assert "user2" not in record.msg
        assert record.msg.count("***:***") == 2
        
    def test_filter_show_user_option(self, filter_show_user):
        """Prueba opción de mostrar usuario parcialmente."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Auth failed for rtsp://administrator:wrongpass@192.168.1.100",
            args=(),
            exc_info=None
        )
        
        filter_show_user.filter(record)
        
        assert "wrongpass" not in record.msg
        assert "administrator" not in record.msg
        assert "ad***:***" in record.msg
        
    def test_filter_no_urls(self, filter_default):
        """Prueba con mensaje sin URLs."""
        original_msg = "This is a normal log message without URLs"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=original_msg,
            args=(),
            exc_info=None
        )
        
        filter_default.filter(record)
        
        assert record.msg == original_msg  # No debe cambiar


class TestCommandSanitizerFilter:
    """Tests para el filtro de comandos."""
    
    @pytest.fixture
    def filter(self):
        """Filtro de comandos."""
        return CommandSanitizerFilter()
        
    def test_filter_ffmpeg_command(self, filter):
        """Prueba filtrado de comando FFmpeg."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Executing: ffmpeg -i rtsp://user:pass@cam/stream -c copy output.mp4",
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        assert "pass" not in record.msg
        assert "rtsp://***:***@cam/stream" in record.msg
        assert "ffmpeg" in record.msg
        assert "output.mp4" in record.msg
        
    def test_filter_curl_command(self, filter):
        """Prueba filtrado de comando curl."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg='Running: curl -H "Authorization: Bearer secret_token" https://api.com',
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        assert "secret_token" not in record.msg
        assert "[REDACTED]" in record.msg
        assert "curl" in record.msg
        
    def test_filter_database_commands(self, filter):
        """Prueba filtrado de comandos de base de datos."""
        commands = [
            "mysql -u root -pmypassword database_name",
            "psql postgresql://user:pass@localhost/db",
            "redis-cli -a redis_password",
        ]
        
        for cmd in commands:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Executing: {cmd}",
                args=(),
                exc_info=None
            )
            
            filter.filter(record)
            
            assert "mypassword" not in record.msg
            assert "pass" not in record.msg
            assert "redis_password" not in record.msg
            
    def test_no_command_detection(self, filter):
        """Prueba cuando no hay comando para filtrar."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Processing completed successfully",
            args=(),
            exc_info=None
        )
        
        original_msg = record.msg
        filter.filter(record)
        
        assert record.msg == original_msg  # No debe cambiar


class TestContextualFilter:
    """Tests para el filtro contextual."""
    
    def test_filter_by_logger_name(self):
        """Prueba filtrado basado en nombre del logger."""
        context_rules = {
            'services.rtsp': 'url',
            'services.ffmpeg': 'command',
            'api.auth': 'config'
        }
        
        filter = ContextualFilter(context_rules)
        
        # Test URL context
        record_url = logging.LogRecord(
            name="services.rtsp.manager",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Connecting to rtsp://user:pass@camera",
            args=(),
            exc_info=None
        )
        
        filter.filter(record_url)
        assert "pass" not in record_url.msg
        
        # Test command context
        record_cmd = logging.LogRecord(
            name="services.ffmpeg.processor",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Running: ffmpeg -i input.mp4 -password secret output.mp4",
            args=(),
            exc_info=None
        )
        
        filter.filter(record_cmd)
        assert "secret" not in record_cmd.msg
        
    def test_no_matching_context(self):
        """Prueba cuando no hay contexto coincidente."""
        filter = ContextualFilter({'specific.module': 'url'})
        
        record = logging.LogRecord(
            name="other.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Some message with password=123",
            args=(),
            exc_info=None
        )
        
        original_msg = record.msg
        filter.filter(record)
        
        assert record.msg == original_msg  # No debe cambiar


class TestEnvironmentBasedFilter:
    """Tests para el filtro basado en ambiente."""
    
    def test_production_filtering(self):
        """Prueba filtrado en producción."""
        filter = EnvironmentBasedFilter('production')
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Password=secret123 connecting to rtsp://user:pass@cam",
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        # En producción debe ser estricto
        assert "secret123" not in record.msg
        assert "pass" not in record.msg
        
    def test_development_filtering(self):
        """Prueba filtrado en desarrollo."""
        filter = EnvironmentBasedFilter('development')
        
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Debug info: rtsp://admin:debugpass@camera user=testuser",
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        # En desarrollo puede ser menos estricto pero aún debe ocultar passwords
        assert "debugpass" not in record.msg
        
    def test_minimal_filtering(self):
        """Prueba filtrado mínimo en testing."""
        filter = EnvironmentBasedFilter('testing')
        
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Test data: password=test123 other=data",
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        # En testing solo oculta passwords obvios
        assert "test123" not in record.msg or "password=[REDACTED]" in record.msg
        
    def test_unknown_environment(self):
        """Prueba con ambiente desconocido (debe usar full)."""
        filter = EnvironmentBasedFilter('unknown_env')
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Sensitive: api_key=12345",
            args=(),
            exc_info=None
        )
        
        filter.filter(record)
        
        # Debe aplicar sanitización completa por defecto
        assert "12345" not in record.msg


class TestSetupLoggingFilters:
    """Tests para la función de configuración de filtros."""
    
    def test_setup_production_filters(self):
        """Prueba configuración de filtros para producción."""
        logger = logging.getLogger("test.setup.prod")
        
        setup_logging_filters(logger, environment='production')
        
        # Debe tener múltiples filtros
        assert len(logger.filters) >= 3
        
        # Verificar tipos de filtros
        filter_types = [type(f).__name__ for f in logger.filters]
        assert 'SensitiveDataFilter' in filter_types
        assert 'URLSanitizerFilter' in filter_types
        assert 'CommandSanitizerFilter' in filter_types
        
    def test_setup_development_filters(self):
        """Prueba configuración de filtros para desarrollo."""
        logger = logging.getLogger("test.setup.dev")
        
        setup_logging_filters(logger, environment='development')
        
        # Debe tener al menos el filtro de ambiente
        assert len(logger.filters) >= 1
        
        filter_types = [type(f).__name__ for f in logger.filters]
        assert 'EnvironmentBasedFilter' in filter_types
        
    def test_setup_with_additional_patterns(self):
        """Prueba configuración con patrones adicionales."""
        logger = logging.getLogger("test.setup.custom")
        
        custom_patterns = [r'CUSTOM_TOKEN=\S+']
        setup_logging_filters(
            logger, 
            environment='production',
            additional_patterns=custom_patterns
        )
        
        # Verificar que se aplicaron los filtros
        assert len(logger.filters) > 0
        
    def test_clear_existing_filters(self):
        """Prueba que se limpien filtros existentes."""
        logger = logging.getLogger("test.setup.clear")
        
        # Agregar filtro dummy
        dummy_filter = logging.Filter()
        logger.addFilter(dummy_filter)
        
        assert len(logger.filters) == 1
        
        # Setup debe limpiar filtros existentes
        setup_logging_filters(logger)
        
        # El filtro dummy no debe estar
        assert dummy_filter not in logger.filters
        
    def test_filters_on_handlers(self):
        """Prueba que los filtros se apliquen también a handlers."""
        logger = logging.getLogger("test.setup.handlers")
        
        # Agregar handler
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        
        setup_logging_filters(logger, environment='production')
        
        # El handler también debe tener filtros
        assert len(handler.filters) > 0


class TestFiltersIntegration:
    """Tests de integración de filtros."""
    
    def test_multiple_filters_chain(self):
        """Prueba cadena de múltiples filtros."""
        logger = logging.getLogger("test.integration")
        
        # Agregar múltiples filtros
        logger.addFilter(SensitiveDataFilter())
        logger.addFilter(URLSanitizerFilter())
        logger.addFilter(CommandSanitizerFilter())
        
        # Crear record con múltiples tipos de datos sensibles
        record = logging.LogRecord(
            name="test.integration",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Executing: ffmpeg -i rtsp://user:pass@cam/stream with API_KEY=secret",
            args=(),
            exc_info=None
        )
        
        # Aplicar todos los filtros
        for filter in logger.filters:
            filter.filter(record)
            
        # Todo debe estar sanitizado
        assert "pass" not in record.msg
        assert "secret" not in record.msg
        assert "[REDACTED]" in record.msg
        assert "***:***" in record.msg
        
    def test_filter_performance(self):
        """Prueba rendimiento de filtros."""
        import time
        
        filter = SensitiveDataFilter()
        
        # Crear muchos records
        records = []
        for i in range(100):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Message {i}: password=pass{i} url=http://user{i}:pwd{i}@host",
                args=(),
                exc_info=None
            )
            records.append(record)
            
        # Medir tiempo de filtrado
        start = time.time()
        for record in records:
            filter.filter(record)
        elapsed = time.time() - start
        
        # Verificar que todos se filtraron
        for i, record in enumerate(records):
            assert f"pass{i}" not in record.msg
            assert f"pwd{i}" not in record.msg
            
        # Debe ser rápido (< 100ms para 100 records)
        assert elapsed < 0.1, f"Filtrado muy lento: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])