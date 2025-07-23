# 🧪 Validador de Tipos TypeScript

## 📋 Descripción

Este módulo proporciona herramientas para validar que las respuestas del backend (Python) cumplan con las interfaces TypeScript definidas en el frontend, asegurando consistencia entre ambos sistemas.

## 🎯 Características

- **Parser TypeScript**: Extrae interfaces y enums de archivos `.ts`
- **Validación de Tipos**: Verifica que las respuestas cumplan con las interfaces
- **Detección de Inconsistencias**: Identifica diferencias en nombres de campos
- **Generación de Mocks**: Crea datos de prueba que cumplen con las interfaces

## 📁 Estructura

```
validators/
├── __init__.py              # Exports públicos
├── typescript_parser.py     # Parser de archivos TypeScript
├── type_validator.py        # Validador de respuestas
├── example_usage.py         # Ejemplos de uso
└── README.md               # Esta documentación
```

## 🚀 Uso Básico

```python
from tests.validators import TypeValidator

# Crear validador con archivo de tipos
validator = TypeValidator("src/features/publishing/types.ts")

# Validar respuesta del backend
response = {"id": 1, "name": "Test", ...}
validator.validate_response(response, "PublishConfiguration")

# Detectar inconsistencias
problems = validator.check_field_compatibility(
    backend_response,
    "MediaMTXPath",
    field_mappings={"id": "path_id"}
)
```

## 🔍 Inconsistencias Detectadas

### 1. MediaMTXPath: `id` vs `path_id`

- **Frontend espera**: `id: number`
- **Backend envía**: `path_id: int`

**Solución recomendada**: Usar alias en Pydantic

```python
class MediaMTXPath(BaseModel):
    path_id: int = Field(..., alias="id")
    
    class Config:
        populate_by_name = True
```

## ⚠️ Limitaciones Actuales

1. **Parser Simplificado**:
   - Solo parsea interfaces y enums básicos
   - No maneja herencia de interfaces
   - No procesa genéricos complejos
   - Asume formato de código consistente

2. **Validación**:
   - No valida todas las características de TypeScript
   - Union types tienen soporte limitado
   - No valida constrains de tipos (min, max, etc.)

## 🔧 TODOs para Producción

1. **Mejorar Parser**:
   - [ ] Usar librería TypeScript AST (ts-morph)
   - [ ] Soportar herencia de interfaces
   - [ ] Manejar genéricos complejos
   - [ ] Parsear tipos además de interfaces

2. **Mejorar Validación**:
   - [ ] Generar JSON Schema completo
   - [ ] Validar con jsonschema library
   - [ ] Soportar validaciones custom
   - [ ] Mejor manejo de referencias circulares

3. **Integración**:
   - [ ] Plugin pytest para validación automática
   - [ ] Generación automática de fixtures
   - [ ] CI/CD para detectar incompatibilidades
   - [ ] Reportes detallados de diferencias

## 📊 Ejemplo de Ejecución

```bash
# Desde la raíz del proyecto
python tests/validators/example_usage.py

# Output esperado:
🧪 Prototipo de Validador TypeScript

=== Ejemplo 1: PublishConfiguration ===
✅ PublishConfiguration válida

=== Ejemplo 2: MediaMTXPath con inconsistencia ===
❌ Error de validación: Validation error at 'MediaMTXPath.id': Campo requerido 'id' faltante

⚠️  Problemas de compatibilidad detectados:
  - Campo requerido 'id' no encontrado en respuesta del backend (buscando como 'path_id')
  - Campo 'path_id' del backend no existe en interface del frontend
```

## 🤝 Integración con Tests

El validador está diseñado para integrarse en los tests de la siguiente manera:

```python
import pytest
from tests.validators import TypeValidator

@pytest.fixture(scope="module")
def type_validator():
    """Fixture para validador de tipos."""
    return TypeValidator("src/features/publishing/types.ts")

def test_api_response_types(test_client, type_validator):
    """Verifica que las respuestas de API cumplan con tipos del frontend."""
    response = test_client.get("/api/publishing/config")
    
    # Validar estructura
    type_validator.validate_response(
        response.json(),
        "PublishConfiguration"
    )
```

## 📝 Notas de Implementación

- El parser es un **prototipo funcional** que demuestra el concepto
- Para producción, considerar herramientas más robustas
- La validación se enfoca en detectar problemas comunes
- Los errores incluyen contexto detallado para debugging