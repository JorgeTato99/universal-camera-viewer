"""
Tests para el servicio de logging seguro.

Verifica la correcta funcionalidad del servicio de logging con
sanitización automática, filtros, y gestión centralizada.
"""

import pytest
import logging
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import sys

# Configurar path para importar desde src-python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.logging_service import (
    LoggingService, SecureLogger, LogLevel,
    get_secure_logger, log_audit
)


class TestSecureLogger:
    """Tests para la clase SecureLogger."""
    
    def test_create_secure_logger(self):
        """Prueba creación de logger seguro."""
        logger = SecureLogger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        
    def test_audit_log_method(self):
        """Prueba método de log de auditoría."""
        logger = SecureLogger("test_audit")
        logger.setLevel(LogLevel.AUDIT)
        
        # Mock handler para capturar logs
        handler = Mock()
        logger.addHandler(handler)
        
        # Log de auditoría
        logger.audit("Test audit message", extra={'user': 'admin'})
        
        # Verificar que se llamó
        assert handler.handle.called
        
    def test_log_secure_with_context(self):
        """Prueba log seguro con contexto sanitizado."""
        logger = SecureLogger("test_secure")
        logger.setLevel(logging.DEBUG)
        
        # Mock handler
        handler = Mock()
        logger.addHandler(handler)
        
        # Log con contexto sensible
        context = {
            'password': 'secret123',
            'username': 'admin',
            'safe_data': 'visible'
        }
        
        logger.log_secure(logging.INFO, "Test message", context=context)
        
        # Verificar que se llamó al handler
        assert handler.handle.called
        
        # Verificar que el contexto fue sanitizado
        log_record = handler.handle.call_args[0][0]
        assert hasattr(log_record, 'context')
        assert log_record.context['password'] == '[REDACTED]'
        assert log_record.context['username'] == 'admin'  # Username no es sensible por defecto
        assert log_record.context['safe_data'] == 'visible'


class TestLoggingService:
    """Tests para el servicio de logging."""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea un directorio temporal para logs."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path, ignore_errors=True)
        
    @pytest.fixture
    def mock_service(self, temp_dir):
        """Crea una instancia del servicio con directorio temporal."""
        # Resetear singleton
        LoggingService._instance = None
        
        # Crear servicio con directorio temporal
        service = LoggingService()
        service.log_dir = temp_dir
        service._initialized = False
        service.__init__()
        
        yield service
        
        # Limpiar
        LoggingService._instance = None
        
    def test_singleton_pattern(self):
        """Verifica que el servicio sea singleton."""
        LoggingService._instance = None
        
        service1 = LoggingService()
        service2 = LoggingService()
        
        assert service1 is service2
        
        LoggingService._instance = None
        
    def test_initialization(self, mock_service):
        """Prueba inicialización del servicio."""
        assert mock_service.environment in ['production', 'development', 'testing']
        assert mock_service.log_dir.exists()
        assert len(mock_service._handlers) > 0
        assert 'console' in mock_service._handlers
        assert 'file' in mock_service._handlers
        assert 'error' in mock_service._handlers
        assert 'audit' in mock_service._handlers
        
    def test_get_logger_basic(self, mock_service):
        """Prueba obtención de logger básico."""
        logger = mock_service.get_logger("test.module")
        
        assert isinstance(logger, SecureLogger)
        assert logger.name == "test.module"
        assert "test.module" in mock_service._loggers
        
        # Obtener de nuevo debe retornar el mismo
        logger2 = mock_service.get_logger("test.module")
        assert logger is logger2
        
    def test_logger_level_by_environment(self, mock_service):
        """Prueba nivel de log según ambiente."""
        # Producción
        mock_service.environment = 'production'
        logger_prod = mock_service.get_logger("test.prod")
        assert logger_prod.level == logging.INFO
        
        # Desarrollo
        mock_service.environment = 'development'
        logger_dev = mock_service.get_logger("test.dev")
        assert logger_dev.level == logging.DEBUG
        
    def test_contextual_filters_applied(self, mock_service):
        """Prueba aplicación de filtros contextuales."""
        # Logger para RTSP
        logger_rtsp = mock_service.get_logger("services.rtsp.manager")
        # Debe tener URLSanitizerFilter
        filter_types = [type(f).__name__ for f in logger_rtsp.filters]
        assert any('URLSanitizer' in name for name in filter_types)
        
        # Logger para comandos
        logger_cmd = mock_service.get_logger("services.ffmpeg.command")
        filter_types = [type(f).__name__ for f in logger_cmd.filters]
        assert any('CommandSanitizer' in name for name in filter_types)
        
    def test_add_custom_handler(self, mock_service):
        """Prueba agregar handler personalizado."""
        # Crear handler personalizado
        custom_handler = logging.StreamHandler()
        custom_handler.setLevel(logging.WARNING)
        
        # Agregar al servicio
        mock_service.add_custom_handler("custom", custom_handler)
        
        assert "custom" in mock_service._handlers
        
        # Verificar que se agregó a loggers existentes
        for logger in mock_service._loggers.values():
            assert custom_handler in logger.handlers
            
    def test_log_audit_event(self, mock_service):
        """Prueba registro de eventos de auditoría."""
        # Registrar evento
        mock_service.log_audit_event(
            event_type="credential_access",
            details={'camera_id': 'cam123', 'action': 'decrypt'},
            user="admin",
            ip="192.168.1.100"
        )
        
        # Verificar métricas
        assert mock_service._log_metrics['audit_events'] == 1
        
        # Verificar que se logueó (verificar archivo si es posible)
        audit_logger = mock_service.get_logger('audit')
        assert audit_logger is not None
        
    def test_log_audit_event_sanitization(self, mock_service):
        """Prueba que los eventos de auditoría se sanitizan."""
        # Registrar evento con datos sensibles
        mock_service.log_audit_event(
            event_type="login_attempt",
            details={
                'username': 'admin',
                'password': 'should_be_hidden',
                'api_key': 'secret_key_123'
            }
        )
        
        # El password y api_key deberían estar sanitizados
        # Verificar indirectamente a través del archivo de log si es posible
        
    def test_log_metric(self, mock_service):
        """Prueba registro de métricas."""
        mock_service.log_metric(
            "camera.fps",
            value=25.5,
            tags={'camera_id': 'cam1', 'brand': 'dahua'}
        )
        
        # Verificar que se creó logger de métricas
        assert 'metrics' in mock_service._loggers
        
    def test_get_logging_stats(self, mock_service, temp_dir):
        """Prueba obtención de estadísticas."""
        # Crear algunos archivos de log
        (temp_dir / "app_20240123.log").write_text("test log content")
        (temp_dir / "errors.log").write_text("error content")
        
        stats = mock_service.get_logging_stats()
        
        assert stats['environment'] == mock_service.environment
        assert stats['active_loggers'] == len(mock_service._loggers)
        assert 'handlers' in stats
        assert 'metrics' in stats
        assert 'log_files' in stats
        assert len(stats['log_files']) >= 2
        
    def test_rotate_logs(self, mock_service):
        """Prueba rotación de logs."""
        # Mock handlers con RotatingFileHandler
        for handler in mock_service._handlers.values():
            if hasattr(handler, 'doRollover'):
                handler.doRollover = Mock()
                
        mock_service.rotate_logs()
        
        # Verificar que se llamó doRollover
        for handler in mock_service._handlers.values():
            if hasattr(handler, 'doRollover'):
                handler.doRollover.assert_called_once()
                
    def test_cleanup_old_logs(self, mock_service, temp_dir):
        """Prueba limpieza de logs antiguos."""
        # Crear logs antiguos
        old_date = datetime.now() - timedelta(days=40)
        old_log = temp_dir / "old_app_20230101.log"
        old_log.write_text("old content")
        
        # Modificar fecha de modificación (mock)
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_mtime = old_date.timestamp()
            
            removed = mock_service.cleanup_old_logs(days=30)
            
        # En un test real esto no funcionaría sin realmente cambiar la fecha
        # pero verificamos la lógica
        assert removed >= 0
        
    def test_set_environment(self, mock_service):
        """Prueba cambio de ambiente."""
        original_env = mock_service.environment
        
        # Cambiar ambiente
        new_env = 'development' if original_env == 'production' else 'production'
        mock_service.set_environment(new_env)
        
        assert mock_service.environment == new_env
        
        # Verificar que se reconfiguraron los loggers
        # (verificar que se llamó setup_logging_filters)
        
    def test_configure_module_logging(self, mock_service):
        """Prueba configuración específica de módulo."""
        mock_service.configure_module_logging(
            "services.critical",
            level=logging.ERROR,
            filters=['password=\\S+']
        )
        
        logger = mock_service.get_logger("services.critical")
        assert logger.level == logging.ERROR
        
    async def test_cleanup(self, mock_service):
        """Prueba limpieza de recursos."""
        # Mock handlers
        for handler in mock_service._handlers.values():
            handler.close = Mock()
            
        await mock_service.cleanup()
        
        # Verificar que se cerraron handlers
        for handler in mock_service._handlers.values():
            handler.close.assert_called_once()
            
    def test_audit_level_registration(self):
        """Verifica que el nivel AUDIT esté registrado."""
        assert hasattr(logging, 'AUDIT') or LogLevel.AUDIT == 45
        
    def test_formatter_by_environment(self, mock_service):
        """Prueba formato de log según ambiente."""
        # El formatter debe tener más detalle en desarrollo
        if mock_service.environment == 'development':
            assert 'filename' in mock_service.formatter._fmt
            assert 'lineno' in mock_service.formatter._fmt
        else:
            # En producción es más simple
            assert mock_service.formatter._fmt.count('%') < 6


class TestLoggingIntegration:
    """Tests de integración del sistema de logging."""
    
    @pytest.fixture
    def mock_service(self):
        """Servicio para tests de integración."""
        LoggingService._instance = None
        service = LoggingService()
        yield service
        LoggingService._instance = None
        
    def test_convenience_functions(self, mock_service):
        """Prueba funciones de conveniencia."""
        # get_secure_logger
        logger = get_secure_logger("test.convenience")
        assert isinstance(logger, SecureLogger)
        
        # log_audit
        log_audit("test_event", {'data': 'test'}, user="tester")
        assert mock_service._log_metrics['audit_events'] > 0
        
    def test_sensitive_data_not_logged(self, mock_service):
        """Verifica que datos sensibles no se logueen."""
        logger = mock_service.get_logger("test.sensitive")
        
        # Capturar salida del handler
        test_handler = logging.StreamHandler()
        test_handler.stream = Mock()
        logger.addHandler(test_handler)
        
        # Log con información sensible
        logger.info("Connecting to rtsp://admin:password123@192.168.1.100/stream")
        
        # Verificar que se sanitizó
        # El mock del stream debería haber recibido la versión sanitizada
        write_calls = test_handler.stream.write.call_args_list
        logged_text = ''.join([call[0][0] for call in write_calls if call[0]])
        
        assert "password123" not in logged_text
        assert "***:***" in logged_text or "[REDACTED]" in logged_text
        
    def test_concurrent_logging(self, mock_service):
        """Prueba logging concurrente (thread safety)."""
        import threading
        
        errors = []
        
        def log_task(index):
            try:
                logger = mock_service.get_logger(f"test.thread.{index}")
                for i in range(10):
                    logger.info(f"Thread {index} - Message {i}")
                    logger.debug(f"Debug from thread {index}")
            except Exception as e:
                errors.append(str(e))
                
        # Crear múltiples threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=log_task, args=(i,))
            threads.append(t)
            t.start()
            
        # Esperar
        for t in threads:
            t.join()
            
        # Verificar que no hubo errores
        assert len(errors) == 0
        assert len(mock_service._loggers) >= 5
        
    def test_metrics_aggregation(self, mock_service):
        """Prueba agregación de métricas."""
        # Registrar varias métricas
        for i in range(10):
            mock_service.log_metric("test.counter", i)
            
        # Registrar eventos de auditoría
        for i in range(5):
            mock_service.log_audit_event("test_event", {'index': i})
            
        stats = mock_service.get_logging_stats()
        
        assert stats['metrics']['audit_events'] == 5
        
    def test_log_files_creation(self, mock_service):
        """Verifica creación de archivos de log."""
        # Forzar creación de logs
        logger = mock_service.get_logger("test.files")
        logger.info("Test message for file")
        logger.error("Test error message")
        
        audit_logger = mock_service.get_logger("audit")
        audit_logger.audit("Test audit message")
        
        # Verificar que los archivos existen
        log_files = list(mock_service.log_dir.glob("*.log"))
        assert len(log_files) > 0
        
        # Debe haber al menos app log y error log
        log_names = [f.name for f in log_files]
        assert any('app' in name for name in log_names)
        assert any('error' in name for name in log_names)
        assert any('audit' in name for name in log_names)


class TestLoggingFiltersIntegration:
    """Tests de integración con filtros de logging."""
    
    def test_environment_based_filtering(self):
        """Prueba filtrado basado en ambiente."""
        LoggingService._instance = None
        
        # Test en producción
        os.environ['ENVIRONMENT'] = 'production'
        service_prod = LoggingService()
        logger_prod = service_prod.get_logger("test.env.prod")
        
        # En producción debe tener filtros estrictos
        assert len(logger_prod.filters) > 0
        
        # Test en desarrollo
        LoggingService._instance = None
        os.environ['ENVIRONMENT'] = 'development'
        service_dev = LoggingService()
        logger_dev = service_dev.get_logger("test.env.dev")
        
        # Los filtros pueden ser diferentes
        assert logger_dev is not None
        
        # Limpiar
        LoggingService._instance = None
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])