"""
Configuración compartida para tests de pytest.

Este archivo proporciona fixtures y configuraciones comunes para todos los tests.
"""
import pytest
from httpx import AsyncClient
from typing import AsyncGenerator, Dict, Any
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Agregar src-python al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

# Importar la aplicación FastAPI
from api.main import app

# Importar modelos necesarios
from models.publishing.publisher_models import PublishStatus
from api.schemas.responses.mediamtx_responses import MediaMTXServerResponse


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP asíncrono para tests de API.
    
    Proporciona un cliente configurado para realizar peticiones a la API
    sin necesidad de levantar un servidor real.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_mediamtx_server() -> Dict[str, Any]:
    """
    Mock de configuración de servidor MediaMTX.
    
    Proporciona datos de prueba para un servidor MediaMTX ficticio.
    """
    return {
        "id": 1,
        "name": "Test MediaMTX Server",
        "server_url": "rtsp://localhost:8554",
        "rtsp_port": 8554,
        "api_url": "http://localhost:9997",
        "api_port": 9997,
        "api_enabled": True,
        "username": "admin",
        "auth_required": True,
        "use_tcp": True,
        "is_active": True,
        "is_default": True,
        "max_reconnect_attempts": 10,
        "reconnect_delay_seconds": 5.0,
        "publish_path_template": "cam_{camera_id}",
        "health_status": "healthy",
        "last_health_check": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "test_user"
    }


@pytest.fixture
def mock_publish_status() -> Dict[str, Any]:
    """
    Mock de estado de publicación.
    
    Proporciona datos de prueba para el estado de una publicación.
    """
    return {
        "camera_id": "cam_001",
        "status": PublishStatus.PUBLISHING.value,  # "PUBLISHING"
        "publish_path": "cam_001",
        "uptime_seconds": 3600.0,
        "error_count": 0,
        "last_error": None,
        "metrics": {
            "fps": 25.0,
            "bitrate_kbps": 2048.0,
            "viewers": 3,
            "frames_sent": 90000,
            "bytes_sent": 31457280,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@pytest.fixture
def mock_publish_metrics() -> Dict[str, Any]:
    """
    Mock de métricas de publicación.
    
    Proporciona datos de prueba para métricas de streaming.
    """
    return {
        "camera_id": "cam_001",
        "timestamp": datetime.utcnow().isoformat(),
        "fps": 30.0,
        "bitrate_kbps": 3000.0,
        "viewers": 5,
        "frames_sent": 150000,
        "bytes_sent": 1073741824,  # 1GB
        "quality_score": 95.0,
        "status": "optimal"
    }


@pytest.fixture
def mock_publishing_presenter():
    """
    Mock del PublishingPresenter para tests.
    
    Proporciona un mock del presenter con métodos comunes configurados.
    """
    presenter = AsyncMock()
    
    # Configurar respuestas por defecto
    presenter.start_publishing.return_value = {
        "success": True,
        "publish_path": "cam_001"
    }
    presenter.stop_publishing.return_value = {
        "success": True
    }
    presenter.get_publish_status.return_value = {
        "status": PublishStatus.PUBLISHING.value,
        "metrics": {
            "fps": 25.0,
            "bitrate_kbps": 2048.0,
            "viewers": 3
        }
    }
    
    return presenter


@pytest.fixture
def mock_mediamtx_db_service():
    """
    Mock del MediaMTXDatabaseService para tests.
    
    Proporciona un mock del servicio de base de datos con métodos configurados.
    """
    service = AsyncMock()
    
    # Configurar respuestas por defecto
    service.get_active_server.return_value = MediaMTXServerResponse(
        id=1,
        name="Test Server",
        server_url="rtsp://localhost:8554",
        api_url="http://localhost:9997",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    service.get_publication_history.return_value = {
        "total": 10,
        "items": []
    }
    
    return service


@pytest.fixture
def mock_mediamtx_api_response():
    """
    Mock de respuesta de la API de MediaMTX.
    
    Simula respuestas típicas de la API REST de MediaMTX.
    """
    return {
        "paths": {
            "cam_001": {
                "source": {
                    "type": "rtsp",
                    "url": "rtsp://192.168.1.100:554/stream"
                },
                "readers": [
                    {
                        "type": "rtsp",
                        "id": "reader1"
                    }
                ]
            }
        }
    }


# Configuración de logging para tests
@pytest.fixture(autouse=True)
def configure_test_logging(caplog):
    """
    Configura el logging para capturar logs durante los tests.
    
    Permite verificar que se generen los logs esperados.
    """
    caplog.set_level("INFO")
    

# Fixtures para manejo de base de datos de prueba
@pytest.fixture
async def test_db():
    """
    Base de datos en memoria para tests.
    
    TODO: Implementar cuando se agreguen tests que requieran BD real.
    Por ahora los tests usan mocks.
    """
    # Placeholder para futura implementación
    yield None


# Marker para tests que requieren servicios externos
pytest.mark.requires_mediamtx = pytest.mark.skipif(
    "not config.getoption('--mediamtx')",
    reason="Requiere servidor MediaMTX real (usar --mediamtx para ejecutar)"
)