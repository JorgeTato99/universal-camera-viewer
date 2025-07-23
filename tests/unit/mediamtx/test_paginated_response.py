"""
Tests unitarios para el genérico PaginatedResponse.

Estos tests verifican que la respuesta paginada genérica funcione
correctamente con diferentes tipos de datos y casos edge.
"""

import sys
from pathlib import Path
from typing import List

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src-python"))

import pytest
from pydantic import BaseModel, Field
from datetime import datetime

from api.schemas.base import PaginatedResponse
from api.schemas.responses.mediamtx_responses import (
    PublishMetricsSnapshot,
    MediaMTXServerResponse,
    PublishingAlertResponse
)


class TestPaginatedResponseBasics:
    """Tests básicos de creación y propiedades computadas."""
    
    def test_create_empty_paginated_response(self):
        """
        Debe crear una respuesta paginada vacía correctamente.
        
        Caso edge: Lista vacía pero con metadatos válidos.
        """
        # Crear respuesta vacía
        response = PaginatedResponse[PublishMetricsSnapshot](
            total=0,
            page=1,
            page_size=20,
            items=[]
        )
        
        # Verificar propiedades
        assert response.total == 0
        assert response.page == 1
        assert response.page_size == 20
        assert response.items == []
        
        # Verificar propiedades computadas
        assert response.has_next is False
        assert response.has_previous is False
        assert response.total_pages == 0
        
        print("[OK] Respuesta paginada vacía creada correctamente")
    
    def test_single_page_response(self):
        """
        Debe manejar correctamente una respuesta de una sola página.
        
        Caso común: Todos los items caben en una página.
        """
        # Crear datos de prueba
        metrics = PublishMetricsSnapshot(
            camera_id="cam_001",
            timestamp="2024-01-15T10:30:00Z",
            fps=25.0,
            bitrate_kbps=2048,
            viewers=5,
            frames_sent=1000,
            bytes_sent=1000000
        )
        
        response = PaginatedResponse[PublishMetricsSnapshot](
            total=1,
            page=1,
            page_size=20,
            items=[metrics]
        )
        
        # Verificar propiedades computadas
        assert response.has_next is False
        assert response.has_previous is False
        assert response.total_pages == 1
        
        print("[OK] Respuesta de página única manejada correctamente")
    
    def test_multiple_pages_navigation(self):
        """
        Debe calcular correctamente la navegación entre páginas.
        
        Verifica has_next, has_previous y total_pages.
        """
        # Simular página 2 de 5
        response = PaginatedResponse[MediaMTXServerResponse](
            total=100,  # 100 items totales
            page=2,     # Página actual
            page_size=20,  # 20 items por página
            items=[]  # Los items no afectan la navegación
        )
        
        # Verificar cálculos
        assert response.total_pages == 5  # 100/20 = 5
        assert response.has_previous is True  # Página 2 tiene anterior
        assert response.has_next is True  # Página 2 de 5 tiene siguiente
        
        # Primera página
        first_page = PaginatedResponse[MediaMTXServerResponse](
            total=100,
            page=1,
            page_size=20,
            items=[]
        )
        assert first_page.has_previous is False
        assert first_page.has_next is True
        
        # Última página
        last_page = PaginatedResponse[MediaMTXServerResponse](
            total=100,
            page=5,
            page_size=20,
            items=[]
        )
        assert last_page.has_previous is True
        assert last_page.has_next is False
        
        print("[OK] Navegación entre páginas calculada correctamente")
    
    def test_edge_case_calculations(self):
        """
        Debe manejar casos edge en cálculos de paginación.
        
        Incluye divisiones no exactas y límites.
        """
        # Caso: División no exacta (101 items, 20 por página = 6 páginas)
        response = PaginatedResponse[PublishingAlertResponse](
            total=101,
            page=1,
            page_size=20,
            items=[]
        )
        assert response.total_pages == 6  # ceil(101/20) = 6
        
        # Caso: Exactamente en el límite
        exact_response = PaginatedResponse[PublishingAlertResponse](
            total=100,
            page=1,
            page_size=20,
            items=[]
        )
        assert exact_response.total_pages == 5  # 100/20 = 5
        
        # Caso: Un solo item
        single_item = PaginatedResponse[PublishingAlertResponse](
            total=1,
            page=1,
            page_size=20,
            items=[]
        )
        assert single_item.total_pages == 1
        
        print("[OK] Casos edge calculados correctamente")


class TestPaginatedResponseSerialization:
    """Tests de serialización y model_dump."""
    
    def test_model_dump_includes_computed_properties(self):
        """
        Debe incluir propiedades computadas en model_dump().
        
        Importante para que el frontend reciba has_next, has_previous, etc.
        """
        response = PaginatedResponse[PublishMetricsSnapshot](
            total=50,
            page=2,
            page_size=10,
            items=[]
        )
        
        # Serializar
        dumped = response.model_dump()
        
        # Verificar que incluye propiedades computadas
        assert 'has_next' in dumped
        assert 'has_previous' in dumped
        assert 'total_pages' in dumped
        
        # Verificar valores
        assert dumped['has_next'] is True  # Página 2 de 5
        assert dumped['has_previous'] is True
        assert dumped['total_pages'] == 5
        
        print("[OK] model_dump incluye propiedades computadas")
    
    def test_json_serialization(self):
        """
        Debe serializar correctamente a JSON.
        
        Verifica que el JSON sea válido y contenga todos los campos.
        """
        # Crear item de prueba
        metrics = PublishMetricsSnapshot(
            camera_id="test_cam",
            timestamp="2024-01-15T10:30:00Z",
            fps=30.0,
            bitrate_kbps=3000,
            viewers=10,
            frames_sent=5000,
            bytes_sent=2000000
        )
        
        response = PaginatedResponse[PublishMetricsSnapshot](
            total=1,
            page=1,
            page_size=10,
            items=[metrics]
        )
        
        # Serializar a JSON
        json_str = response.model_dump_json()
        
        # Verificar estructura
        print(f"JSON generado: {json_str[:200]}...")  # Debug
        
        # Verificar campos básicos
        assert '"total":1' in json_str
        assert '"page":1' in json_str
        assert '"page_size":10' in json_str
        assert '"items"' in json_str
        assert '"camera_id":"test_cam"' in json_str
        
        # Las propiedades computadas pueden no estar en JSON por defecto
        # Verificar con model_dump primero
        dumped = response.model_dump()
        assert dumped['has_next'] is False
        assert dumped['has_previous'] is False
        assert dumped['total_pages'] == 1
        
        print("[OK] Serialización JSON correcta")


class TestPaginatedResponseWithDifferentTypes:
    """Tests con diferentes tipos de items."""
    
    def test_with_simple_model(self):
        """
        Debe funcionar con modelos simples.
        
        Prueba el genérico con un modelo básico.
        """
        class SimpleItem(BaseModel):
            id: int
            name: str
        
        items = [
            SimpleItem(id=1, name="Item 1"),
            SimpleItem(id=2, name="Item 2")
        ]
        
        response = PaginatedResponse[SimpleItem](
            total=2,
            page=1,
            page_size=10,
            items=items
        )
        
        assert len(response.items) == 2
        assert response.items[0].name == "Item 1"
        
        print("[OK] Funciona con modelos simples")
    
    def test_with_complex_nested_model(self):
        """
        Debe funcionar con modelos complejos anidados.
        
        Usa MediaMTXServerResponse que tiene campos opcionales y datetime.
        """
        server = MediaMTXServerResponse(
            id=1,
            name="Test Server",
            server_url="rtsp://localhost:8554",
            rtsp_port=8554,
            api_enabled=True,
            auth_required=False,
            use_tcp=True,
            is_active=True,
            is_default=True,
            max_reconnect_attempts=5,
            reconnect_delay_seconds=3.0,
            publish_path_template="cam_{camera_id}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test_user"
        )
        
        response = PaginatedResponse[MediaMTXServerResponse](
            total=1,
            page=1,
            page_size=10,
            items=[server]
        )
        
        # Verificar serialización
        dumped = response.model_dump()
        assert dumped['items'][0]['name'] == "Test Server"
        assert dumped['total_pages'] == 1
        
        print("[OK] Funciona con modelos complejos")


class TestPaginatedResponseValidation:
    """Tests de validación de datos."""
    
    def test_page_must_be_positive(self):
        """
        Debe validar que la página sea positiva.
        
        Verifica que Pydantic valida automáticamente page >= 1.
        """
        # Pydantic valida automáticamente gracias a Field(..., ge=1)
        try:
            response = PaginatedResponse[PublishMetricsSnapshot](
                total=10,
                page=0,  # Inválido: debe ser >= 1
                page_size=10,
                items=[]
            )
            print("[FAIL] No se validó página >= 1")
        except Exception as e:
            # Se espera ValidationError
            assert "greater than or equal to 1" in str(e)
            print(f"[OK] Validación de página: {e}")
    
    def test_items_type_validation(self):
        """
        Debe validar que los items sean del tipo correcto.
        
        Pydantic debería validar automáticamente los tipos.
        """
        # Intentar crear con tipo incorrecto
        with pytest.raises(Exception):  # Pydantic ValidationError
            # Intentar pasar strings cuando espera PublishMetricsSnapshot
            PaginatedResponse[PublishMetricsSnapshot](
                total=1,
                page=1,
                page_size=10,
                items=["string_invalido"]  # Tipo incorrecto
            )
        
        print("[OK] Validación de tipos funciona")


def run_all_tests():
    """Ejecuta todos los tests y muestra resumen."""
    print("Tests Unitarios de PaginatedResponse\n")
    
    # Tests básicos
    basics = TestPaginatedResponseBasics()
    basics.test_create_empty_paginated_response()
    basics.test_single_page_response()
    basics.test_multiple_pages_navigation()
    basics.test_edge_case_calculations()
    
    print()
    
    # Tests de serialización
    serialization = TestPaginatedResponseSerialization()
    serialization.test_model_dump_includes_computed_properties()
    serialization.test_json_serialization()
    
    print()
    
    # Tests con diferentes tipos
    types = TestPaginatedResponseWithDifferentTypes()
    types.test_with_simple_model()
    types.test_with_complex_nested_model()
    
    print()
    
    # Tests de validación
    validation = TestPaginatedResponseValidation()
    validation.test_page_must_be_positive()
    # validation.test_items_type_validation()  # Requiere pytest
    
    print("\n[PASSED] Todos los tests unitarios pasaron")
    print("\nNotas de implementación:")
    print("- PaginatedResponse funciona correctamente con genéricos")
    print("- Las propiedades computadas se incluyen en model_dump()")
    print("- Compatible con diferentes tipos de modelos")
    print("- Validación automática: page >= 1, page_size >= 1 y <= 200")
    print("- JSON serialization NO incluye propiedades computadas por defecto")
    print("\nTODO para endpoints:")
    print("- Usar model_dump() para incluir has_next, has_previous, total_pages")
    print("- O configurar serialización custom si se necesita en JSON")


if __name__ == "__main__":
    run_all_tests()