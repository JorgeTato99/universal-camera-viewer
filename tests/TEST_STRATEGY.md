# 🧪 Estrategia de Testing - Universal Camera Viewer

## 📋 Visión General

Este documento define la estrategia de testing para el proyecto Universal Camera Viewer, estableciendo principios, estructura y mejores prácticas para asegurar la calidad del código.

## 🎯 Principios Fundamentales

### 1. **Usar SOLO servicios del backend**

- Los tests deben consumir las APIs y servicios existentes
- NO acceder directamente a modelos o implementar lógica manualmente
- Si un test necesita reimplementar algo, el servicio está incompleto

### 2. **Ser agnósticos de marca**

- NO crear tests específicos por marca (test_tplink.py, test_dahua.py)
- Los tests deben funcionar con cualquier cámara compatible
- Usar datos genéricos o mockear cuando sea necesario

### 3. **Separación de responsabilidades**

- Tests unitarios: Prueban componentes aislados
- Tests de integración: Prueban interacciones entre servicios
- Tests E2E: Prueban flujos completos de usuario

### 4. **Independencia del hardware**

- Los tests no deben depender de cámaras físicas para ejecutarse
- Usar mocks para simular respuestas de hardware
- Tests con hardware real son opcionales y separados

## 📁 Estructura Propuesta

```
tests/
├── unit/                         # Tests unitarios
│   ├── test_models.py           # Validaciones de modelos de datos
│   ├── test_utils.py            # Funciones de utilidad
│   └── test_validators.py       # Lógica de validación
│
├── integration/                  # Tests de integración
│   ├── test_scan_service.py     # Servicio de escaneo
│   ├── test_protocol_service.py # Servicio de protocolos
│   ├── test_connection_service.py # Servicio de conexiones
│   ├── test_camera_manager.py   # Gestión de cámaras
│   └── test_stream_service.py   # Servicio de streaming
│
├── api/                         # Tests de endpoints FastAPI
│   ├── test_scanner_endpoints.py # /api/scanner/*
│   ├── test_camera_endpoints.py  # /api/cameras/*
│   ├── test_stream_endpoints.py  # /api/stream/*
│   └── test_websocket.py        # WebSocket endpoints
│
├── e2e/                         # Tests end-to-end
│   ├── test_camera_discovery.py # Flujo: descubrir → conectar
│   ├── test_streaming_flow.py   # Flujo: conectar → stream → ver
│   └── test_multi_camera.py     # Flujo: múltiples cámaras
│
├── fixtures/                    # Datos de prueba
│   ├── camera_data.json        # Configuraciones de cámara mock
│   ├── scan_results.json       # Resultados de escaneo mock
│   └── stream_responses.py     # Respuestas RTSP/ONVIF mock
│
├── utils/                       # Utilidades de testing
│   ├── mock_camera.py          # Cámara virtual para tests
│   ├── test_helpers.py         # Funciones auxiliares
│   └── async_helpers.py        # Helpers para tests async
│
└── hardware/                    # Tests con hardware real (opcional)
    ├── README.md               # Cómo ejecutar con cámaras reales
    ├── test_real_camera.py     # Test interactivo con cámara real
    └── performance_test.py     # Tests de rendimiento
```

## 🔧 Tecnologías y Herramientas

### Framework Principal

- **pytest**: Framework de testing principal
- **pytest-asyncio**: Para tests asíncronos
- **pytest-cov**: Cobertura de código
- **pytest-mock**: Mocking avanzado

### Herramientas Adicionales

- **faker**: Generación de datos de prueba
- **httpx**: Cliente HTTP para tests de API
- **respx**: Mocking de requests HTTP

## 📝 Convenciones de Nomenclatura

### Archivos

- `test_*.py`: Archivos de test
- `*_test.py`: También válido
- `conftest.py`: Configuración y fixtures compartidas

### Funciones

```python
# Tests unitarios
def test_should_validate_ip_address():
    """Debería validar direcciones IP correctamente."""
    pass

# Tests de integración  
async def test_scan_service_discovers_cameras():
    """ScanService debería descubrir cámaras en la red."""
    pass

# Tests E2E
async def test_user_can_view_camera_stream():
    """Usuario puede ver el stream de una cámara."""
    pass
```

## 🎭 Estrategia de Mocking

### Niveles de Mock

1. **Nivel de Red**: Mock de respuestas HTTP/RTSP
2. **Nivel de Servicio**: Mock de servicios externos
3. **Nivel de Hardware**: Simulación de cámaras

### Ejemplo de Mock

```python
@pytest.fixture
def mock_camera():
    """Cámara mock para tests."""
    return {
        "ip": "192.168.1.100",
        "ports": [554, 80, 2020],
        "protocols": ["RTSP", "ONVIF"],
        "brand": "Generic",
        "model": "Test Camera"
    }
```

## 📊 Métricas de Calidad

### Cobertura Objetivo

- **Modelos**: 100% de cobertura
- **Servicios**: 90% de cobertura
- **API Endpoints**: 95% de cobertura
- **Presenters**: 85% de cobertura
- **Total**: >85% de cobertura

### Tiempo de Ejecución

- Tests unitarios: <1 segundo cada uno
- Tests de integración: <5 segundos cada uno
- Tests E2E: <30 segundos cada uno
- Suite completa: <5 minutos

## 🚀 Comandos de Ejecución

```bash
# Ejecutar todos los tests
pytest

# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/

# Con cobertura
pytest --cov=src-python --cov-report=html

# Tests en paralelo
pytest -n auto

# Tests con output detallado
pytest -v -s

# Tests con hardware real
pytest tests/hardware/ --hardware
```

## 🔄 Integración Continua

### Pipeline de CI

1. **Linting**: flake8, black, isort
2. **Type Checking**: mypy
3. **Unit Tests**: Rápidos, sin dependencias
4. **Integration Tests**: Con servicios mockeados
5. **Coverage Report**: Mínimo 85%

### Pre-commit Hooks

```yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
```

## 📅 Roadmap de Implementación

### Fase 1: Estructura Básica (Actual)

- Tests directos para validar funcionalidad
- Foco en servicios principales
- Sin estructura formal

### Fase 2: Organización (Próximo)

- Separar tests por categorías
- Agregar fixtures compartidas
- Implementar mocks básicos

### Fase 3: Cobertura Completa (Futuro)

- Tests para todos los componentes
- Mocks sofisticados
- Tests de rendimiento

### Fase 4: Automatización Total

- CI/CD completo
- Tests de regresión automáticos
- Monitoreo de calidad

## ⚠️ Antipatrones a Evitar

1. **NO reimplementar lógica de negocio en tests**
2. **NO hacer tests dependientes entre sí**
3. **NO usar datos hardcodeados de producción**
4. **NO hacer tests que requieran configuración manual**
5. **NO crear tests específicos por marca de cámara**

## 📚 Referencias

- [pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Async Testing Guide](https://pytest-asyncio.readthedocs.io/)

---

> **Nota**: Este documento está en evolución constante. A medida que el proyecto crece, la estrategia de testing se irá refinando y expandiendo.
