# Guía de Tests - Universal Camera Viewer

## Estructura de Tests

```
tests/
├── api/                      # Tests de endpoints HTTP
│   └── test_publishing_endpoints.py
├── integration/              # Tests de flujos completos
│   └── mediamtx/
│       └── test_publication_flow.py
├── unit/                     # Tests unitarios
│   └── mediamtx/
│       ├── test_mediamtx_path_alias.py
│       ├── test_paginated_response.py
│       └── test_type_consistency.py
├── validators/               # Herramientas de validación
│   ├── type_validator.py
│   └── typescript_parser.py
└── conftest.py              # Configuración de pytest
```

## Ejecutar Tests

### Todos los tests
```bash
pytest
```

### Tests específicos por categoría
```bash
# Solo tests unitarios
pytest tests/unit/

# Solo tests de API
pytest tests/api/

# Solo tests de integración
pytest tests/integration/

# Solo tests de MediaMTX
pytest tests/ -k mediamtx
```

### Tests con cobertura
```bash
pytest --cov=src-python --cov-report=html
```

### Tests en modo verbose
```bash
pytest -v
```

### Tests con output capturado
```bash
pytest -s  # Muestra prints y logs
```

## Tests de Consistencia de Tipos

Para verificar que los tipos del backend coinciden con el frontend:

```bash
python tests/unit/mediamtx/test_type_consistency.py
```

## Fixtures Disponibles

### En conftest.py

- `async_client`: Cliente HTTP para tests de API
- `mock_mediamtx_server`: Configuración mock de servidor MediaMTX
- `mock_publish_status`: Estado de publicación mock
- `mock_publish_metrics`: Métricas de publicación mock
- `mock_publishing_presenter`: Mock del presenter
- `mock_mediamtx_db_service`: Mock del servicio de BD

### Ejemplo de uso

```python
@pytest.mark.asyncio
async def test_example(async_client, mock_publish_status):
    response = await async_client.get("/api/publishing/status/cam_001")
    assert response.status_code == 200
```

## Pendientes (TODOs)

### Tests Faltantes
1. **Tests de configuración de servidores MediaMTX**
2. **Tests de gestión de paths**
3. **Tests de exportación de métricas**
4. **Tests de analytics de viewers**
5. **Tests con servidor MediaMTX real** (actualmente todos usan mocks)

### Funcionalidades con Datos Mock
1. **Viewer analytics**: Datos geográficos son mock (México: CDMX, Puebla, Veracruz)
2. **Total viewers**: Calculado como publicaciones × 3 (mock)
3. **Alertas descartadas**: Almacenamiento en memoria (temporal)

### Mejoras Planificadas
1. **Base de datos de prueba**: Actualmente se usan mocks, implementar BD SQLite en memoria
2. **Tests E2E**: Con servidor MediaMTX real usando Docker
3. **CI/CD**: Configurar GitHub Actions para ejecutar tests automáticamente
4. **Performance tests**: Agregar tests de carga y estrés

## Notas Importantes

### Migración de Base de Datos
Antes de ejecutar la aplicación con los cambios de PublishStatus, ejecutar:
```sql
-- Archivo: src-python/services/database/migrations/002_update_publish_status_to_uppercase.sql
```

### Inconsistencias Resueltas
1. **PublishingStatus**: Ahora usa MAYÚSCULAS consistentemente
2. **MediaMTXPath.id**: Usa alias para compatibilidad
3. **overall_status**: Mapea automáticamente degraded→warning, critical→error

## Configuración de VS Code

Para ejecutar tests desde VS Code, agregar a `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.cwd": "${workspaceFolder}"
}
```