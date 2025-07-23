"""
Ejemplo de uso del validador TypeScript.

Este archivo demuestra cómo usar el validador para verificar
compatibilidad entre respuestas del backend y tipos del frontend.

NOTA: Este es un ejemplo/prototipo. Los tests reales estarán en
los archivos de test correspondientes.
"""

import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from type_validator import TypeValidator, ValidationError


def example_validation():
    """Ejemplo de validación de tipos."""
    
    # Crear validador con el archivo de tipos del frontend
    validator = TypeValidator("src/features/publishing/types.ts")
    
    # Ejemplo 1: Validar PublishConfiguration
    print("=== Ejemplo 1: PublishConfiguration ===")
    
    # Respuesta simulada del backend
    backend_response = {
        "id": 1,  # ✅ Correcto: number
        "name": "MediaMTX Principal",
        "mediamtx_url": "rtsp://localhost:8554",
        "api_url": "http://localhost:9997",
        "api_enabled": True,
        "username": "admin",
        "auth_enabled": True,
        "use_tcp": True,
        "is_active": True,
        "max_reconnects": 10,
        "reconnect_delay": 5,
        "publish_path_template": "cam_{camera_id}",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    
    try:
        validator.validate_response(backend_response, "PublishConfiguration")
        print("✅ PublishConfiguration válida")
    except ValidationError as e:
        print(f"❌ Error de validación: {e}")
    
    # Ejemplo 2: Detectar inconsistencia en MediaMTXPath
    print("\n=== Ejemplo 2: MediaMTXPath con inconsistencia ===")
    
    # Backend envía 'path_id' pero frontend espera 'id'
    backend_path_response = {
        "path_id": 1,  # ❌ Backend usa path_id
        "server_id": 1,
        "path_name": "cam_001",
        "source_type": "rtsp",
        "source_url": "rtsp://192.168.1.100:554/stream",
        "record_enabled": False,
        "authentication_required": False,
        "is_active": True,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    
    try:
        validator.validate_response(backend_path_response, "MediaMTXPath")
        print("✅ MediaMTXPath válida")
    except ValidationError as e:
        print(f"❌ Error de validación: {e}")
    
    # Verificar compatibilidad de campos
    problems = validator.check_field_compatibility(
        backend_path_response,
        "MediaMTXPath",
        field_mappings={"id": "path_id"}  # Mapeo conocido
    )
    
    if problems:
        print("\n⚠️  Problemas de compatibilidad detectados:")
        for problem in problems:
            print(f"  - {problem}")
    
    # Ejemplo 3: Validar enum PublishingStatus
    print("\n=== Ejemplo 3: PublishingStatus ===")
    
    valid_status = "PUBLISHING"
    invalid_status = "RUNNING"  # Valor antiguo, ya no válido
    
    try:
        validator.validate_response(valid_status, "PublishingStatus")
        print(f"✅ Estado '{valid_status}' es válido")
    except ValidationError as e:
        print(f"❌ Error: {e}")
    
    try:
        validator.validate_response(invalid_status, "PublishingStatus")
    except ValidationError as e:
        print(f"❌ Estado '{invalid_status}' no es válido: {e}")
    
    # Ejemplo 4: Generar datos mock
    print("\n=== Ejemplo 4: Generar datos mock ===")
    
    mock_metrics = validator.generate_mock_data("PublishMetrics")
    print(f"Mock PublishMetrics: {mock_metrics}")
    
    # Validar que el mock cumple con la interface
    try:
        validator.validate_response(mock_metrics, "PublishMetrics")
        print("✅ Mock data es válido")
    except ValidationError as e:
        print(f"❌ Mock data inválido: {e}")


def example_fix_inconsistency():
    """Ejemplo de cómo corregir la inconsistencia id vs path_id."""
    
    print("\n=== Solución para inconsistencia id vs path_id ===")
    
    # Opción 1: Transformar respuesta del backend
    def transform_backend_response(response):
        """Transforma path_id a id para compatibilidad."""
        if "path_id" in response:
            response["id"] = response.pop("path_id")
        return response
    
    backend_response = {
        "path_id": 1,
        "server_id": 1,
        "path_name": "cam_001",
        # ... otros campos
    }
    
    # Transformar antes de validar
    transformed = transform_backend_response(backend_response.copy())
    print(f"Respuesta transformada: 'path_id' -> 'id'")
    print(f"  Antes: path_id = {backend_response.get('path_id')}")
    print(f"  Después: id = {transformed.get('id')}")
    
    # Opción 2: Usar Pydantic con alias (recomendado)
    print("\n📝 Solución recomendada: Usar alias en Pydantic")
    print("""
    class MediaMTXPath(BaseModel):
        path_id: int = Field(..., alias="id")  # Backend usa path_id, serializa como id
        server_id: int
        # ... otros campos
        
        class Config:
            populate_by_name = True  # Acepta ambos nombres al deserializar
    """)


if __name__ == "__main__":
    print("🧪 Prototipo de Validador TypeScript\n")
    
    # Verificar que el archivo de tipos existe
    ts_file = Path("src/features/publishing/types.ts")
    if not ts_file.exists():
        print(f"⚠️  Archivo de tipos no encontrado: {ts_file}")
        print("   Asegúrate de ejecutar desde la raíz del proyecto")
        exit(1)
    
    # Ejecutar ejemplos
    example_validation()
    example_fix_inconsistency()
    
    print("\n✅ Prototipo completado")
    print("\n📌 Próximos pasos:")
    print("  1. Integrar validador en tests unitarios")
    print("  2. Crear fixtures con datos validados")
    print("  3. Implementar tests de cada endpoint")
    print("  4. Resolver inconsistencias encontradas")