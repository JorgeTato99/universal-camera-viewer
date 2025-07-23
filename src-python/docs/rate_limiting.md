# Rate Limiting - Universal Camera Viewer

## Resumen

El sistema de rate limiting protege la API contra abuso y ataques DoS mediante límites configurables por tipo de operación. Utiliza SlowAPI con almacenamiento en memoria y está preparado para migración a Redis.

## Características

- ✅ Límites configurables por YAML externo
- ✅ Multiplicadores por ambiente (desarrollo/producción)
- ✅ Headers estándar RFC 6585
- ✅ Logging detallado de violaciones
- ✅ IPs confiables con bypass
- ✅ Paths excluidos (health, docs)
- ✅ Preparado para Redis (documentado)
- ✅ Métricas y estadísticas

## Configuración

### Archivo de Configuración

`src-python/config/rate_limit_settings.yaml`

```yaml
development:
  enabled: true
  multiplier: 10  # Límites 10x más altos
  storage: "memory"

production:
  enabled: true
  multiplier: 1
  storage: "memory"  # TODO: Cambiar a "redis"

limits:
  global:
    rate: "1000/hour"
    burst: 50
  read:
    rate: "100/minute"
    burst: 10
  write:
    rate: "10/minute"
    burst: 2
  camera_connect:
    rate: "5/minute"
    burst: 1
  network_scan:
    rate: "1/minute"
    burst: 1
```

### Límites Predefinidos

| Límite | Producción | Desarrollo | Uso |
|--------|------------|------------|-----|
| global | 1000/hora | 10000/hora | Todas las peticiones |
| read | 100/minuto | 1000/minuto | GET endpoints |
| write | 10/minuto | 100/minuto | POST, PUT, DELETE |
| camera_connect | 5/minuto | 50/minuto | Conexión a cámaras |
| network_scan | 1/minuto | 10/minuto | Escaneo de red |
| stream_start | 10/minuto | 100/minuto | Iniciar streaming |
| websocket_connect | 20/hora | 200/hora | Nuevas conexiones WS |

## Uso en Endpoints

### Operaciones de Lectura

```python
from api.dependencies.rate_limit import read_limit

@router.get("/cameras")
@read_limit()  # 100/minute (1000 en dev)
async def list_cameras():
    pass
```

### Operaciones de Escritura

```python
from api.dependencies.rate_limit import write_limit

@router.post("/cameras")
@write_limit()  # 10/minute (100 en dev)
async def create_camera():
    pass
```

### Operaciones Críticas

```python
from api.dependencies.rate_limit import critical_operation_limit

@router.post("/scan")
@critical_operation_limit()  # 1/minute
async def scan_network():
    pass
```

### Límites Personalizados

```python
from api.dependencies.rate_limit import rate_limit

@router.post("/custom")
@rate_limit("custom_operation", "5/hour")
async def custom_operation():
    pass
```

### WebSocket

```python
from api.dependencies.rate_limit import websocket_rate_limit

@router.websocket("/stream")
@websocket_rate_limit("websocket_connect")
async def stream(websocket):
    pass
```

## Headers de Respuesta

### Petición Normal

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706021400
X-RateLimit-Window: 60
```

### Límite Excedido (429)

```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706021400

{
  "success": false,
  "error": "Límite de peticiones excedido",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "detail": {
    "limit": 100,
    "remaining": 0,
    "reset_at": "2024-01-23T12:30:00Z",
    "retry_after": 45
  }
}
```

## Migración a Redis

### 1. Instalar Dependencias

```bash
pip install redis aioredis
```

### 2. Actualizar Configuración

```yaml
production:
  storage: "redis"
  redis:
    url: "redis://localhost:6379"
    key_prefix: "ucv_rate_limit"
```

### 3. Implementar RedisStorage

```python
# En api/middleware/rate_limit.py
class RedisStorage(RateLimitStorage):
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
    
    async def increment(self, key: str, window: int):
        # Implementación con Redis
        pass
```

## Monitoreo

### Logs Detallados

```
WARNING - Rate limit exceeded: IP=192.168.1.100, Path=/api/scan, Method=POST, Limit=network_scan (1/minute), Count=2/1
```

### Estadísticas Agregadas

```
INFO - Rate limit stats: Total=1523, Blocked=23 (1.5%), Top IPs=[('192.168.1.100', 523), ('10.0.0.50', 234)]
```

### Métricas Disponibles

- Total de peticiones
- Peticiones bloqueadas
- Tasa de bloqueo
- Top IPs por peticiones
- Top IPs bloqueadas
- Bloqueos por tipo de límite

## Testing

### Test Unitario

```python
import pytest
from api.middleware.rate_limit import MemoryStorage

@pytest.mark.asyncio
async def test_rate_limit():
    storage = MemoryStorage()
    
    # Primera petición
    count, _ = await storage.increment("test", 60)
    assert count == 1
    
    # Segunda petición
    count, _ = await storage.increment("test", 60)
    assert count == 2
```

### Test de Integración

```python
from fastapi.testclient import TestClient

def test_rate_limit_endpoint(client: TestClient):
    # Hacer múltiples peticiones
    for i in range(10):
        response = client.get("/api/cameras")
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
```

## Troubleshooting

### Problema: Rate limiting no funciona

1. Verificar que el middleware esté registrado:
   ```python
   setup_rate_limiting(app)
   ```

2. Verificar configuración:
   ```bash
   cat src-python/config/rate_limit_settings.yaml
   ```

3. Revisar logs para errores

### Problema: IPs incorrectas

1. Verificar headers de proxy:
   - X-Real-IP
   - X-Forwarded-For

2. Configurar proxy correctamente

### Problema: Límites muy restrictivos

1. Ajustar multiplicador de desarrollo
2. Crear límites personalizados
3. Agregar IPs a lista de confiables

## Mejores Prácticas

1. **No deshabilitar en producción**: Siempre mantener rate limiting activo
2. **Monitorear métricas**: Revisar logs para ajustar límites
3. **Documentar límites**: Informar a usuarios de la API
4. **Planear para escala**: Migrar a Redis antes de múltiples workers
5. **Límites graduales**: Empezar permisivo y ajustar según uso

## Referencias

- [RFC 6585](https://tools.ietf.org/html/rfc6585) - Additional HTTP Status Codes
- [SlowAPI Documentation](https://github.com/laurentS/slowapi)
- [Redis Rate Limiting Patterns](https://redis.io/docs/reference/patterns/rate-limiting/)