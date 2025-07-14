# 💻 Guía de Desarrollo

## 🚀 Setup Inicial

```bash
# Configuración completa de desarrollo
make fresh-start

# O paso a paso:
make install-dev
make install-pre-commit
make check-all
```

## 🔄 Workflow de Desarrollo

### 1. **Preparar Feature Branch**

```bash
git checkout -b feature/nueva-funcionalidad
```

### 2. **Desarrollo Local**

```bash
# Ejecutar en modo desarrollo
make dev

# O con debug
make run-debug
```

### 3. **Verificación de Calidad**

```bash
# Formatear código
make format

# Verificar calidad completa
make check-all

# Tests
make test-cov
```

### 4. **Pre-commit**

```bash
# Automático con hooks instalados
git commit -m "feat: nueva funcionalidad"

# Manual
make pre-commit
```

## 🛠️ Comandos Make Esenciales

### **Desarrollo Diario**

```bash
make dev           # Setup + ejecutar
make run           # Ejecutar aplicación
make run-debug     # Ejecutar con debug
make format        # Formatear código
make lint          # Verificar linting
make test          # Ejecutar tests
```

### **Calidad de Código**

```bash
make check-all     # Todas las verificaciones
make type-check    # Verificar tipos
make security      # Análisis de seguridad
make pre-commit    # Hooks completos
```

### **Mantenimiento**

```bash
make clean         # Limpiar temporales
make clean-all     # Limpieza profunda
make db-backup     # Respaldar BD
make config-backup # Respaldar config
```

## 🏗️ Estructura de Desarrollo

```bash
src/
├── models/           # 🗃️ Capa de datos
│   ├── camera_model.py
│   ├── connection_model.py
│   └── scan_model.py
├── views/            # 🎨 Interfaz Flet
│   ├── main_view.py
│   └── camera_view.py
├── presenters/       # 🔗 Lógica MVP (EN DESARROLLO)
│   ├── main_presenter.py
│   ├── camera_presenter.py
│   └── scan_presenter.py
├── services/         # ⚙️ Servicios de negocio
│   ├── protocol_service.py
│   ├── scan_service.py
│   └── connection_service.py
└── utils/            # 🛠️ Utilidades
    ├── config.py
    └── brand_manager.py
```

## 🎯 Tareas Prioritarias

### **Próximo Sprint (MVP Completion)**

1. **🔗 Completar Presenter Layer (80% restante)**

   ```python
   # Implementar en presenters/
   - camera_presenter.py  # Gestión de cámaras
   - scan_presenter.py    # Escaneo de red
   - config_presenter.py  # Configuración
   ```

2. **📊 Integración DuckDB Analytics**

   ```python
   # Agregar en services/
   - analytics_service.py
   - data_service.py (mejorar)
   ```

3. **🧪 Test Suite Completo**

   ```python
   # Crear en tests/
   - test_presenters/
   - test_integration/
   ```

## 🔧 Herramientas de Desarrollo

### **IDE Setup Recomendado**

**VS Code Extensions:**

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker"
  ]
}
```

**PyCharm Settings:**

- Black formatter configurado
- isort integration
- MyPy type checking habilitado

### **Pre-commit Hooks**

```yaml
# Instalados automáticamente:
- black (formateo)
- isort (imports)
- flake8 (linting)
- mypy (tipos)
- bandit (seguridad)
```

## 🐛 Debugging

### **Debug de UI (Flet)**

```python
# En src/main.py
if __name__ == "__main__":
    flet.app(
        target=main,
        view=flet.AppView.WEB_BROWSER,  # Para debug web
        port=8080
    )
```

### **Debug de Cámaras**

```bash
# Scripts de diagnóstico
python examples/diagnostics/camera_detector.py
python examples/diagnostics/network_analyzer.py

# Tests específicos por marca
python examples/testing/tplink_complete_test.py
python examples/testing/steren_complete_test.py
```

### **Performance Profiling**

```bash
# Análisis de rendimiento
make performance

# Memory profiling
python -m memory_profiler src/main.py
```

## 📊 Métricas de Desarrollo

### **Code Quality Gates**

- **Coverage:** >80% para servicios core
- **Linting:** 0 errores en flake8
- **Type Hints:** >70% coverage con mypy
- **Security:** Sin vulnerabilidades altas en bandit

### **Performance Targets**

- **Startup:** <3 segundos
- **Scan Network:** <10 segundos para /24
- **Camera Connection:** <5 segundos
- **Memory Usage:** <200MB en operación normal

## 🚨 Problemas Comunes

### **Error: Import not found**

```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# O usar relative imports
from ..services import protocol_service
```

### **Error: Flet no conecta**

```bash
# Verificar puerto disponible
netstat -an | grep 8080

# Limpiar caché
make clean
```

### **Error: Tests fallan**

```bash
# Ejecutar con verbose
pytest tests/ -v -s

# Test específico
pytest tests/test_services/test_protocol_service.py -v
```

## 🎨 Contribución UI

### **Material Design 3 Guidelines**

- Usar `ColorScheme.from_seed()`
- Componentes elevados con sombras
- Typography scale consistente
- Estados interactivos (hover, pressed)

### **Responsive Design**

```python
# Breakpoints
MOBILE = 600
TABLET = 900
DESKTOP = 1200
```

## 📝 Documentación de Código

### **Docstrings Style (Google)**

```python
def connect_camera(ip: str, protocol: str) -> bool:
    """Conecta a una cámara usando el protocolo especificado.
    
    Args:
        ip: Dirección IP de la cámara
        protocol: Protocolo a usar (onvif, rtsp, http)
        
    Returns:
        True si la conexión fue exitosa, False en caso contrario
        
    Raises:
        ConnectionError: Si no se puede establecer conexión
    """
```

## 🎯 Próximos Pasos

1. **[🏛️ Entender Arquitectura MVP](architecture.md)**
2. **[📡 Conocer Services API](api-services.md)**
3. **[📱 Build y Deploy](deployment.md)**

---

**💡 Tips:**

- Usa `make help` para ver todos los comandos
- Configura tu IDE con las extensiones recomendadas
- Ejecuta `make check-all` antes de cada commit

---

### 📚 Navegación

[← Anterior: Configuración para Windows](WINDOWS_SETUP.md) | [📑 Índice](README.md) | [Siguiente: Arquitectura Técnica →](ARCHITECTURE.md)
