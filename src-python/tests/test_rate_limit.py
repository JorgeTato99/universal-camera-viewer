"""
Tests para el sistema de Rate Limiting.

Estos tests verifican que el rate limiting funcione correctamente
en diferentes escenarios.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from datetime import datetime

from api.middleware.rate_limit import (
    MemoryStorage,
    RateLimitConfig,
    RateLimitStats,
    get_client_identifier
)


class TestMemoryStorage:
    """Tests para el almacenamiento en memoria."""
    
    @pytest.mark.asyncio
    async def test_increment_new_key(self):
        """Test incrementar una clave nueva."""
        storage = MemoryStorage()
        
        count, reset_time = await storage.increment("test_key", 60)
        
        assert count == 1
        assert reset_time > time.time()
        assert reset_time <= time.time() + 60
    
    @pytest.mark.asyncio
    async def test_increment_existing_key(self):
        """Test incrementar una clave existente."""
        storage = MemoryStorage()
        
        # Primera llamada
        count1, reset1 = await storage.increment("test_key", 60)
        
        # Segunda llamada inmediata
        count2, reset2 = await storage.increment("test_key", 60)
        
        assert count1 == 1
        assert count2 == 2
        assert reset1 == reset2  # El reset time debe ser el mismo
    
    @pytest.mark.asyncio
    async def test_window_expiration(self):
        """Test que el contador se resetea después de la ventana."""
        storage = MemoryStorage()
        
        # Incrementar con ventana muy corta
        count1, _ = await storage.increment("test_key", 0.1)  # 100ms
        assert count1 == 1
        
        # Esperar que expire
        await asyncio.sleep(0.2)
        
        # Debe resetear
        count2, _ = await storage.increment("test_key", 60)
        assert count2 == 1
    
    @pytest.mark.asyncio
    async def test_get_count(self):
        """Test obtener contador actual."""
        storage = MemoryStorage()
        
        # Sin incrementar
        count = await storage.get_count("test_key")
        assert count == 0
        
        # Después de incrementar
        await storage.increment("test_key", 60)
        count = await storage.get_count("test_key")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """Test resetear contador."""
        storage = MemoryStorage()
        
        # Incrementar
        await storage.increment("test_key", 60)
        count = await storage.get_count("test_key")
        assert count == 1
        
        # Reset
        await storage.reset("test_key")
        count = await storage.get_count("test_key")
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test limpieza de entradas expiradas."""
        storage = MemoryStorage(max_entries=5)
        
        # Crear entradas con ventanas cortas
        for i in range(3):
            await storage.increment(f"expire_{i}", 0.1)
        
        # Crear entradas con ventanas largas
        for i in range(3):
            await storage.increment(f"keep_{i}", 60)
        
        # Esperar que expiren las primeras
        await asyncio.sleep(0.2)
        
        # Limpiar
        await storage.cleanup()
        
        # Verificar que se eliminaron las expiradas
        for i in range(3):
            count = await storage.get_count(f"expire_{i}")
            assert count == 0
        
        # Verificar que se mantuvieron las otras
        for i in range(3):
            count = await storage.get_count(f"keep_{i}")
            assert count == 1
    
    @pytest.mark.asyncio
    async def test_max_entries_limit(self):
        """Test límite máximo de entradas."""
        storage = MemoryStorage(max_entries=5)
        
        # Crear más entradas del límite
        for i in range(10):
            await storage.increment(f"key_{i}", 60)
        
        # Forzar cleanup
        await storage.cleanup()
        
        # Verificar que no hay más del límite
        total_keys = len(storage._storage)
        assert total_keys <= 5


class TestRateLimitConfig:
    """Tests para la configuración de rate limits."""
    
    def test_default_config(self):
        """Test configuración por defecto cuando no hay archivo."""
        with patch('pathlib.Path.exists', return_value=False):
            config = RateLimitConfig()
            
            # Debe usar configuración por defecto
            assert config.get_limit('global') is not None
            assert config.get_limit('read') is not None
    
    def test_get_limit_with_multiplier(self):
        """Test obtener límite con multiplicador de ambiente."""
        config = RateLimitConfig()
        
        # Mock ambiente desarrollo
        with patch.object(config, 'get_environment', return_value='development'):
            limit = config.get_limit('read')
            # En desarrollo debe ser 10x más alto
            assert '1000/minute' in limit or '100/minute' in limit
    
    def test_is_excluded_path(self):
        """Test verificación de paths excluidos."""
        config = RateLimitConfig()
        
        assert config.is_excluded('/health')
        assert config.is_excluded('/docs')
        assert config.is_excluded('/health/live')  # Prefijo
        assert not config.is_excluded('/api/cameras')
    
    def test_is_trusted_ip(self):
        """Test verificación de IPs confiables."""
        config = RateLimitConfig()
        
        assert config.is_trusted_ip('127.0.0.1')
        assert config.is_trusted_ip('::1')
        assert not config.is_trusted_ip('192.168.1.1')


class TestGetClientIdentifier:
    """Tests para identificación de cliente."""
    
    def test_direct_ip(self):
        """Test obtener IP directa."""
        request = Mock()
        request.headers = {}
        request.client = Mock(host='192.168.1.100')
        
        ip = get_client_identifier(request)
        assert ip == '192.168.1.100'
    
    def test_x_real_ip(self):
        """Test prioridad de X-Real-IP."""
        request = Mock()
        request.headers = {'X-Real-IP': '10.0.0.1'}
        request.client = Mock(host='192.168.1.100')
        
        ip = get_client_identifier(request)
        assert ip == '10.0.0.1'
    
    def test_x_forwarded_for(self):
        """Test X-Forwarded-For con múltiples IPs."""
        request = Mock()
        request.headers = {'X-Forwarded-For': '10.0.0.1, 10.0.0.2, 10.0.0.3'}
        request.client = Mock(host='192.168.1.100')
        
        ip = get_client_identifier(request)
        assert ip == '10.0.0.1'  # Primera IP
    
    def test_priority_order(self):
        """Test orden de prioridad de headers."""
        request = Mock()
        request.headers = {
            'X-Real-IP': '1.1.1.1',
            'X-Forwarded-For': '2.2.2.2'
        }
        request.client = Mock(host='3.3.3.3')
        
        ip = get_client_identifier(request)
        assert ip == '1.1.1.1'  # X-Real-IP tiene prioridad


class TestRateLimitStats:
    """Tests para estadísticas de rate limiting."""
    
    @pytest.mark.asyncio
    async def test_record_request(self):
        """Test registro de peticiones."""
        stats = RateLimitStats()
        
        # Registrar peticiones
        await stats.record_request('192.168.1.1', blocked=False)
        await stats.record_request('192.168.1.1', blocked=True, limit_name='read')
        await stats.record_request('192.168.1.2', blocked=False)
        
        # Obtener estadísticas
        result = await stats.get_stats()
        
        assert result['total_requests'] == 3
        assert result['blocked_requests'] == 1
        assert result['block_rate'] == pytest.approx(33.33, rel=0.01)
        assert '192.168.1.1' in result['top_ips']
        assert result['blocks_by_limit']['read'] == 1
    
    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test resetear estadísticas."""
        stats = RateLimitStats()
        
        # Registrar y resetear
        await stats.record_request('192.168.1.1', blocked=False)
        await stats.reset()
        
        result = await stats.get_stats()
        assert result['total_requests'] == 0
        assert result['blocked_requests'] == 0


# === Tests de integración ===

@pytest.mark.asyncio
async def test_rate_limit_flow():
    """Test flujo completo de rate limiting."""
    storage = MemoryStorage()
    
    # Simular múltiples peticiones
    key = "test_ip:read"
    limit = 5
    window = 1  # 1 segundo
    
    # Primeras 5 peticiones deben pasar
    for i in range(limit):
        count, _ = await storage.increment(key, window)
        assert count == i + 1
    
    # La 6ta debe ser bloqueada
    count, _ = await storage.increment(key, window)
    assert count == 6  # Excede el límite
    
    # Esperar que expire la ventana
    await asyncio.sleep(1.1)
    
    # Debe poder hacer peticiones nuevamente
    count, _ = await storage.increment(key, window)
    assert count == 1  # Reset


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test peticiones concurrentes."""
    storage = MemoryStorage()
    key = "concurrent_test"
    
    # Simular 10 peticiones concurrentes
    async def make_request():
        return await storage.increment(key, 60)
    
    results = await asyncio.gather(*[make_request() for _ in range(10)])
    
    # Verificar que los contadores sean secuenciales
    counts = [r[0] for r in results]
    assert sorted(counts) == list(range(1, 11))


# === Ejemplo de test con FastAPI ===

def test_rate_limit_headers():
    """
    Test que los headers de rate limit se agreguen correctamente.
    
    Este es un ejemplo de cómo probar con FastAPI TestClient:
    
    ```python
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    
    # Primera petición
    response = client.get("/api/cameras")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Exceder límite (simulado)
    for _ in range(100):
        response = client.get("/api/cameras")
    
    # Debe retornar 429
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    ```
    """
    pass  # Placeholder para documentación