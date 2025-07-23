"""
Tests para verificar la solución de alias en MediaMTXPath.

Este test verifica que la inconsistencia entre 'id' (frontend) y 'path_id' (backend)
se resuelve correctamente usando alias en Pydantic.
"""

import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src-python"))

from api.schemas.responses.mediamtx_responses import MediaMTXPath, PathSourceType
from datetime import datetime


def test_mediamtx_path_serialization():
    """
    Verifica que MediaMTXPath serializa 'path_id' como 'id'.
    
    El frontend espera 'id' pero la base de datos usa 'path_id'.
    Este test confirma que el alias funciona correctamente.
    """
    # Crear instancia con path_id
    path = MediaMTXPath(
        path_id=123,
        server_id=1,
        server_name="MediaMTX Principal",
        path_name="cam_001",
        source_type=PathSourceType.RTSP,
        source_url="rtsp://192.168.1.100:554/stream",
        is_active=True,
        is_running=True,
        connected_publishers=1,
        connected_readers=5,
        record_enabled=False,
        authentication_required=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Serializar con alias
    serialized = path.model_dump(by_alias=True)
    
    # Verificar que se serializa como 'id'
    assert 'id' in serialized, "El campo 'id' debe estar presente en la serialización"
    assert 'path_id' not in serialized, "El campo 'path_id' NO debe estar en la serialización con alias"
    assert serialized['id'] == 123, "El valor de 'id' debe ser correcto"
    
    print("[OK] Serialización con alias funciona correctamente")
    print(f"   - Campo 'id' presente: {serialized['id']}")
    print(f"   - Campo 'path_id' ausente: {'path_id' not in serialized}")


def test_mediamtx_path_deserialization():
    """
    Verifica que MediaMTXPath puede deserializar tanto 'id' como 'path_id'.
    
    Esto es importante para compatibilidad durante la transición.
    """
    # Datos con 'id' (como vendría del frontend)
    data_with_id = {
        "id": 456,
        "server_id": 1,
        "server_name": "MediaMTX Test",
        "path_name": "cam_002", 
        "source_type": "rtsp",
        "is_active": True,
        "is_running": False,
        "connected_publishers": 0,
        "connected_readers": 0,
        "record_enabled": False,
        "authentication_required": False,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    
    # Deserializar desde 'id'
    path_from_id = MediaMTXPath(**data_with_id)
    assert path_from_id.path_id == 456, "Debe poder deserializar desde 'id'"
    
    # Datos con 'path_id' (como vendría de la base de datos)
    data_with_path_id = data_with_id.copy()
    data_with_path_id['path_id'] = data_with_path_id.pop('id')
    
    # Deserializar desde 'path_id'
    path_from_path_id = MediaMTXPath(**data_with_path_id)
    assert path_from_path_id.path_id == 456, "Debe poder deserializar desde 'path_id'"
    
    print("[OK] Deserialización funciona con ambos nombres")
    print(f"   - Desde 'id': {path_from_id.path_id}")
    print(f"   - Desde 'path_id': {path_from_path_id.path_id}")


def test_json_serialization():
    """
    Verifica la serialización a JSON para respuestas de API.
    
    Este es el formato que recibirá el frontend.
    """
    path = MediaMTXPath(
        path_id=789,
        server_id=2,
        path_name="test_path",
        source_type=PathSourceType.RTMP,
        is_active=True,
        is_running=True,
        connected_publishers=2,
        connected_readers=10,
        record_enabled=True,
        record_path="/recordings",
        authentication_required=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Serializar a JSON (simula respuesta de API)
    json_str = path.model_dump_json(by_alias=True)
    
    # Verificar que contiene 'id' en el JSON
    assert '"id":789' in json_str, "El JSON debe contener 'id' con el valor correcto"
    assert '"path_id"' not in json_str, "El JSON NO debe contener 'path_id'"
    
    print("[OK] Serialización JSON correcta")
    print(f"   - JSON contiene 'id': {'\"id\":789' in json_str}")
    print(f"   - JSON NO contiene 'path_id': {'\"path_id\"' not in json_str}")


def test_backwards_compatibility():
    """
    Verifica que el cambio es retrocompatible.
    
    NOTA: Este test documenta el comportamiento actual.
    TODO: Cuando el frontend se actualice para usar 'path_id',
    este test deberá actualizarse o eliminarse.
    """
    # Simular respuesta actual del backend (sin alias)
    backend_response = {
        "path_id": 999,
        "server_id": 1,
        "path_name": "legacy_path",
        "source_type": "rtsp",
        "is_active": True,
        "is_running": True,
        "connected_publishers": 0,
        "connected_readers": 0,
        "record_enabled": False,
        "authentication_required": False,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    
    # Crear modelo
    path = MediaMTXPath(**backend_response)
    
    # Serializar SIN alias (comportamiento anterior)
    without_alias = path.model_dump(by_alias=False)
    assert 'path_id' in without_alias
    assert 'id' not in without_alias
    
    # Serializar CON alias (nuevo comportamiento)
    with_alias = path.model_dump(by_alias=True)
    assert 'id' in with_alias
    assert 'path_id' not in with_alias
    
    print("[OK] Compatibilidad hacia atrás mantenida")
    print(f"   - Sin alias: usa 'path_id'")
    print(f"   - Con alias: usa 'id'")
    print("\nNOTA: Los endpoints deben usar by_alias=True para el frontend")


if __name__ == "__main__":
    print("Test de Solución para MediaMTXPath id vs path_id\n")
    
    # Ejecutar tests
    test_mediamtx_path_serialization()
    print()
    test_mediamtx_path_deserialization()
    print()
    test_json_serialization()
    print()
    test_backwards_compatibility()
    
    print("\n[PASSED] Todos los tests pasaron")
    print("\nResumen de la solución:")
    print("  1. Backend mantiene 'path_id' (consistente con BD)")
    print("  2. Se agregó alias='id' para serialización al frontend")
    print("  3. populate_by_name=True permite recibir ambos nombres")
    print("  4. Los endpoints deben usar by_alias=True al serializar")
    print("\nTODO: Actualizar frontend para usar 'path_id' en el futuro")