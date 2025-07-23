"""
Tests para las funciones de sanitización.

Verifica que todas las funciones de sanitización protegen correctamente
la información sensible en diferentes contextos.
"""

import pytest
from pathlib import Path
import sys

# Configurar path para importar desde src-python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.sanitizers import (
    sanitize_url,
    sanitize_url_regex,
    sanitize_command,
    sanitize_ip,
    sanitize_headers,
    sanitize_config,
    sanitize_error_message,
    sanitize_log_message,
    create_safe_log_context
)


class TestSanitizeUrl:
    """Tests para sanitización de URLs."""
    
    def test_sanitize_url_with_credentials(self):
        """Prueba sanitización de URL con credenciales."""
        # RTSP
        url = "rtsp://admin:password123@192.168.1.100:554/stream"
        sanitized = sanitize_url(url)
        assert sanitized == "rtsp://***:***@192.168.1.100:554/stream"
        assert "password123" not in sanitized
        assert "admin" not in sanitized
        
        # HTTP
        url = "http://user:secret@api.example.com/path"
        sanitized = sanitize_url(url)
        assert sanitized == "http://***:***@api.example.com/path"
        
        # HTTPS
        url = "https://apikey:secretkey@secure.api.com:8443/v1/endpoint"
        sanitized = sanitize_url(url)
        assert sanitized == "https://***:***@secure.api.com:8443/v1/endpoint"
        
    def test_sanitize_url_without_credentials(self):
        """Prueba sanitización de URL sin credenciales."""
        url = "rtsp://192.168.1.100:554/stream"
        sanitized = sanitize_url(url)
        assert sanitized == url  # No debe cambiar
        
        url = "http://example.com/api/endpoint"
        sanitized = sanitize_url(url)
        assert sanitized == url
        
    def test_sanitize_url_with_show_user(self):
        """Prueba sanitización mostrando parcialmente el usuario."""
        url = "rtsp://administrator:pass123@camera.local/stream"
        sanitized = sanitize_url(url, show_user=True)
        assert sanitized == "rtsp://ad***:***@camera.local/stream"
        
        # Usuario corto
        url = "rtsp://a:pass@camera.local/stream"
        sanitized = sanitize_url(url, show_user=True)
        assert sanitized == "rtsp://*:***@camera.local/stream"
        
    def test_sanitize_url_with_custom_mask(self):
        """Prueba sanitización con carácter de máscara personalizado."""
        url = "rtsp://user:pass@host/path"
        sanitized = sanitize_url(url, mask_char='X')
        assert sanitized == "rtsp://XXX:XXX@host/path"
        
    def test_sanitize_url_with_query_params(self):
        """Prueba sanitización con parámetros de consulta."""
        url = "http://user:pass@api.com/endpoint?param1=value1&param2=value2"
        sanitized = sanitize_url(url)
        assert sanitized == "http://***:***@api.com/endpoint?param1=value1&param2=value2"
        assert "?param1=value1" in sanitized  # Los parámetros se mantienen
        
    def test_sanitize_url_edge_cases(self):
        """Prueba casos extremos de URLs."""
        # URL vacía
        assert sanitize_url("") == ""
        assert sanitize_url(None) == None
        
        # URL malformada
        url = "not-a-valid-url"
        assert sanitize_url(url) == url
        
        # Solo usuario sin password
        url = "ftp://user@ftp.example.com"
        sanitized = sanitize_url(url)
        assert "user" not in sanitized or "***" in sanitized
        
    def test_sanitize_url_regex_fallback(self):
        """Prueba función regex de respaldo."""
        # URLs que deberían usar el fallback
        url = "rtsp://admin:pass@host"
        sanitized = sanitize_url_regex(url)
        assert sanitized == "rtsp://***:***@host"
        
        # Múltiples protocolos
        urls = [
            ("ftp://user:pass@ftp.com", "ftp://***:***@ftp.com"),
            ("sftp://admin:secret@sftp.com", "sftp://***:***@sftp.com"),
            ("ssh://root:toor@server", "ssh://***:***@server"),
        ]
        
        for original, expected in urls:
            assert sanitize_url_regex(original) == expected


class TestSanitizeCommand:
    """Tests para sanitización de comandos."""
    
    def test_sanitize_ffmpeg_command(self):
        """Prueba sanitización de comando FFmpeg."""
        cmd = 'ffmpeg -i rtsp://admin:pass123@192.168.1.1/stream -f rtsp rtsp://output:secret@server/live'
        sanitized = sanitize_command(cmd)
        
        assert "pass123" not in sanitized
        assert "secret" not in sanitized
        assert "***:***" in sanitized
        assert "ffmpeg" in sanitized  # El comando debe mantenerse
        
    def test_sanitize_command_with_headers(self):
        """Prueba sanitización de headers en comandos."""
        cmd = 'curl -H "Authorization: Bearer secret_token_123" https://api.com'
        sanitized = sanitize_command(cmd)
        
        assert "secret_token_123" not in sanitized
        assert "[REDACTED]" in sanitized
        assert "curl" in sanitized
        
    def test_sanitize_command_password_args(self):
        """Prueba sanitización de argumentos de password."""
        commands = [
            'mysql -u root -pMyPassword123 database',
            'psql --password=SecretDB123 -U postgres',
            'redis-cli -a RedisPass123',
            'mongosh --password SuperSecret',
        ]
        
        for cmd in commands:
            sanitized = sanitize_command(cmd)
            assert "Password123" not in sanitized
            assert "SecretDB123" not in sanitized
            assert "RedisPass123" not in sanitized
            assert "SuperSecret" not in sanitized
            assert "[REDACTED]" in sanitized
            
    def test_sanitize_command_custom_patterns(self):
        """Prueba sanitización con patrones personalizados."""
        cmd = "custom-tool --api-key=12345 --secret-value=abcdef"
        patterns = [r'--secret-value=\S+']
        
        sanitized = sanitize_command(cmd, patterns)
        assert "abcdef" not in sanitized
        assert "[REDACTED]" in sanitized
        # api-key también debe ser sanitizado por los patrones por defecto
        assert "12345" not in sanitized
        
    def test_sanitize_command_edge_cases(self):
        """Prueba casos extremos de comandos."""
        assert sanitize_command("") == ""
        assert sanitize_command(None) == None
        
        # Comando sin información sensible
        cmd = "ls -la /home/user"
        assert sanitize_command(cmd) == cmd


class TestSanitizeIp:
    """Tests para sanitización de IPs."""
    
    def test_sanitize_ip_partial(self):
        """Prueba sanitización parcial de IP."""
        assert sanitize_ip("192.168.1.100") == "192.168.1.xxx"
        assert sanitize_ip("10.0.0.1") == "10.0.0.xxx"
        assert sanitize_ip("172.16.254.1") == "172.16.254.xxx"
        
    def test_sanitize_ip_full(self):
        """Prueba sanitización completa de IP."""
        assert sanitize_ip("192.168.1.100", level='full') == "xxx.xxx.xxx.xxx"
        assert sanitize_ip("8.8.8.8", level='full') == "xxx.xxx.xxx.xxx"
        
    def test_sanitize_ip_none(self):
        """Prueba sin sanitización."""
        assert sanitize_ip("192.168.1.100", level='none') == "192.168.1.100"
        
    def test_sanitize_ip_invalid(self):
        """Prueba con IPs inválidas."""
        assert sanitize_ip("not.an.ip.address") == "not.an.ip.address"
        assert sanitize_ip("192.168.1") == "192.168.1"  # Incompleta
        assert sanitize_ip("") == ""
        assert sanitize_ip(None) == None


class TestSanitizeHeaders:
    """Tests para sanitización de headers HTTP."""
    
    def test_sanitize_sensitive_headers(self):
        """Prueba sanitización de headers sensibles."""
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
            'X-API-Key': 'secret_api_key_123',
            'Cookie': 'session=abc123; user=admin',
            'Content-Type': 'application/json',
            'User-Agent': 'MyApp/1.0'
        }
        
        sanitized = sanitize_headers(headers)
        
        assert sanitized['Authorization'] == 'Bearer [REDACTED]'
        assert sanitized['X-API-Key'] == '[REDACTED]'
        assert sanitized['Cookie'] == '[REDACTED]'
        assert sanitized['Content-Type'] == 'application/json'  # No sensible
        assert sanitized['User-Agent'] == 'MyApp/1.0'  # No sensible
        
    def test_sanitize_headers_case_insensitive(self):
        """Prueba que la sanitización sea insensible a mayúsculas."""
        headers = {
            'authorization': 'Basic dXNlcjpwYXNz',
            'AUTHORIZATION': 'Bearer token',
            'X-Api-Key': 'key123',
            'x-auth-token': 'token456'
        }
        
        sanitized = sanitize_headers(headers)
        
        assert '[REDACTED]' in sanitized.get('authorization', '')
        assert '[REDACTED]' in sanitized.get('AUTHORIZATION', '')
        assert sanitized.get('X-Api-Key') == '[REDACTED]'
        assert sanitized.get('x-auth-token') == '[REDACTED]'
        
    def test_sanitize_headers_empty(self):
        """Prueba con headers vacíos."""
        assert sanitize_headers({}) == {}
        assert sanitize_headers(None) == None


class TestSanitizeConfig:
    """Tests para sanitización de configuraciones."""
    
    def test_sanitize_config_basic(self):
        """Prueba sanitización básica de configuración."""
        config = {
            'host': '192.168.1.100',
            'port': 8080,
            'username': 'admin',
            'password': 'secret123',
            'api_key': 'key_abc123',
            'debug': True
        }
        
        sanitized = sanitize_config(config)
        
        assert sanitized['host'] == '192.168.1.100'
        assert sanitized['port'] == 8080
        assert sanitized['username'] == 'admin'  # Por defecto no es sensible
        assert sanitized['password'] == '[REDACTED]'
        assert sanitized['api_key'] == '[REDACTED]'
        assert sanitized['debug'] is True
        
    def test_sanitize_config_nested(self):
        """Prueba sanitización de configuración anidada."""
        config = {
            'database': {
                'host': 'localhost',
                'password': 'db_secret',
                'credentials': {
                    'access_key': 'aws_key',
                    'secret_key': 'aws_secret'
                }
            },
            'cache': {
                'redis_url': 'redis://user:pass@localhost:6379'
            }
        }
        
        sanitized = sanitize_config(config)
        
        assert sanitized['database']['password'] == '[REDACTED]'
        assert sanitized['database']['credentials']['access_key'] == '[REDACTED]'
        assert sanitized['database']['credentials']['secret_key'] == '[REDACTED]'
        assert 'redis://***:***@localhost:6379' in sanitized['cache']['redis_url']
        
    def test_sanitize_config_lists(self):
        """Prueba sanitización de listas en configuración."""
        config = {
            'allowed_hosts': ['192.168.1.1', '192.168.1.2'],
            'api_keys': ['key1', 'key2', 'key3'],
            'passwords': ['pass1', 'pass2']
        }
        
        sanitized = sanitize_config(config)
        
        assert sanitized['allowed_hosts'] == ['192.168.1.1', '192.168.1.2']
        assert all(key == '[REDACTED]' for key in sanitized['api_keys'])
        assert all(pwd == '[REDACTED]' for pwd in sanitized['passwords'])
        
    def test_sanitize_config_custom_keys(self):
        """Prueba sanitización con llaves personalizadas."""
        config = {
            'my_secret_field': 'sensitive_data',
            'normal_field': 'visible_data'
        }
        
        sanitized = sanitize_config(config, sensitive_keys=['my_secret_field'])
        
        assert sanitized['my_secret_field'] == '[REDACTED]'
        assert sanitized['normal_field'] == 'visible_data'
        
    def test_sanitize_config_different_types(self):
        """Prueba sanitización de diferentes tipos de datos."""
        config = {
            'password_string': 'secret',
            'password_int': 12345,
            'password_float': 123.45,
            'password_bool': True,
            'password_dict': {'inner': 'secret'},
            'password_list': ['s1', 's2']
        }
        
        sanitized = sanitize_config(config)
        
        assert sanitized['password_string'] == '[REDACTED]'
        assert sanitized['password_int'] == 0
        assert sanitized['password_float'] == 0
        assert sanitized['password_bool'] is False
        assert sanitized['password_dict'] == {'inner': '[REDACTED]'}
        assert all(item == '[REDACTED]' for item in sanitized['password_list'])


class TestSanitizeErrorMessage:
    """Tests para sanitización de mensajes de error."""
    
    def test_sanitize_error_with_urls(self):
        """Prueba sanitización de URLs en errores."""
        error = "Failed to connect to rtsp://admin:pass123@192.168.1.100/stream: timeout"
        sanitized = sanitize_error_message(error)
        
        assert "pass123" not in sanitized
        assert "admin" not in sanitized
        assert "***:***" in sanitized
        
    def test_sanitize_error_with_paths(self):
        """Prueba sanitización de rutas de archivo."""
        # Windows
        error = r"File not found: C:\Users\JohnDoe\Documents\config.ini"
        sanitized = sanitize_error_message(error)
        assert r"C:\Users\[USER]\" in sanitized
        assert "JohnDoe" not in sanitized
        
        # Linux
        error = "Permission denied: /home/johndoe/.ssh/id_rsa"
        sanitized = sanitize_error_message(error)
        assert "/home/[USER]/" in sanitized
        assert "johndoe" not in sanitized
        
    def test_sanitize_error_with_ips(self):
        """Prueba sanitización de IPs internas."""
        error = "Cannot reach 192.168.1.100 or 10.0.0.50"
        sanitized = sanitize_error_message(error)
        
        assert "[INTERNAL_IP]" in sanitized
        assert "192.168.1.100" not in sanitized
        assert "10.0.0.50" not in sanitized
        
    def test_sanitize_error_with_emails(self):
        """Prueba sanitización de emails."""
        error = "Invalid login for user@example.com"
        sanitized = sanitize_error_message(error)
        
        assert "[EMAIL]" in sanitized
        assert "user@example.com" not in sanitized
        
    def test_sanitize_error_with_hashes(self):
        """Prueba sanitización de hashes y claves."""
        error = "Invalid API key: a1b2c3d4e5f6789012345678901234567890abcd"
        sanitized = sanitize_error_message(error)
        
        assert "[HASH]" in sanitized or "[KEY]" in sanitized
        assert "a1b2c3d4e5f6" not in sanitized


class TestSanitizeLogMessage:
    """Tests para sanitización general de mensajes de log."""
    
    def test_sanitize_log_with_context(self):
        """Prueba sanitización con contexto específico."""
        # Contexto de comando
        msg = "Executing: ffmpeg -i rtsp://user:pass@cam/stream"
        sanitized = sanitize_log_message(msg, context='command')
        assert "pass" not in sanitized
        
        # Contexto de URL
        msg = "Connecting to rtsp://admin:secret@192.168.1.1"
        sanitized = sanitize_log_message(msg, context='url')
        assert "secret" not in sanitized
        
        # Contexto de error
        msg = "Error: Failed to authenticate user@company.com"
        sanitized = sanitize_log_message(msg, context='error')
        assert "[EMAIL]" in sanitized
        
    def test_sanitize_log_general(self):
        """Prueba sanitización general sin contexto."""
        msg = "Processing request from 192.168.1.50 to rtsp://user:pwd@server/cam"
        sanitized = sanitize_log_message(msg)
        
        assert "pwd" not in sanitized
        assert "192.168.1.xxx" in sanitized  # IP privada sanitizada
        assert "***:***" in sanitized
        
    def test_sanitize_log_edge_cases(self):
        """Prueba casos extremos."""
        assert sanitize_log_message("") == ""
        assert sanitize_log_message(None) == None
        
        # Mensaje sin información sensible
        msg = "Application started successfully on port 8080"
        assert sanitize_log_message(msg) == msg


class TestCreateSafeLogContext:
    """Tests para creación de contexto seguro."""
    
    def test_create_safe_context(self):
        """Prueba creación de contexto seguro para logging."""
        context = {
            'user': 'admin',
            'password': 'secret123',
            'action': 'login',
            'ip': '192.168.1.100',
            'metadata': {
                'api_key': 'key123',
                'session': 'abc123'
            }
        }
        
        safe = create_safe_log_context(context)
        
        assert safe['user'] == 'admin'
        assert safe['password'] == '[REDACTED]'
        assert safe['action'] == 'login'
        assert safe['ip'] == '192.168.1.100'
        assert safe['metadata']['api_key'] == '[REDACTED]'
        assert safe['metadata']['session'] == 'abc123'  # Session no es sensible por defecto


class TestSanitizersIntegration:
    """Tests de integración de sanitizadores."""
    
    def test_complex_sanitization_scenario(self):
        """Prueba escenario complejo con múltiples tipos de datos sensibles."""
        # Simular un log complejo con múltiples elementos sensibles
        log_data = {
            'message': 'Failed to execute command',
            'command': 'ffmpeg -i rtsp://admin:cam123@192.168.1.100:554/stream -c copy output.mp4',
            'error': 'Connection timeout to rtsp://admin:cam123@192.168.1.100:554/stream',
            'user_info': {
                'email': 'admin@example.com',
                'ip': '10.0.0.50'
            },
            'config': {
                'database_password': 'db_secret_123',
                'api_keys': ['key1', 'key2'],
                'webhook_url': 'https://user:token@webhook.site/endpoint'
            }
        }
        
        # Sanitizar todo
        safe_log = create_safe_log_context(log_data)
        
        # Verificar que todo está sanitizado apropiadamente
        assert 'cam123' not in str(safe_log)
        assert 'db_secret_123' not in str(safe_log)
        assert '[REDACTED]' in str(safe_log)
        assert '***:***' in safe_log['command']
        
        # El email podría mantenerse o sanitizarse según la configuración
        # pero las passwords definitivamente deben estar ocultas
        assert safe_log['config']['database_password'] == '[REDACTED]'
        
    def test_performance_bulk_sanitization(self):
        """Prueba rendimiento con muchas operaciones."""
        import time
        
        # Preparar datos de prueba
        urls = [f"rtsp://user{i}:pass{i}@camera{i}.local/stream" for i in range(100)]
        
        # Medir tiempo
        start = time.time()
        sanitized = [sanitize_url(url) for url in urls]
        elapsed = time.time() - start
        
        # Verificar que todas se sanitizaron
        assert all('pass' not in s for s in sanitized)
        assert all('***:***' in s for s in sanitized)
        
        # Debe ser rápido (< 100ms para 100 URLs)
        assert elapsed < 0.1, f"Sanitización muy lenta: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])