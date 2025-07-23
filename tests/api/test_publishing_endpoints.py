"""
Tests de integración para endpoints de publicación MediaMTX.

Estos tests verifican que los endpoints de la API funcionan correctamente
con respuestas mockeadas. No requieren un servidor MediaMTX real.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime
from unittest.mock import patch, AsyncMock

from models.publishing.publisher_models import PublishStatus


class TestPublishingStatusEndpoints:
    """Tests para endpoints de estado de publicación."""
    
    @pytest.mark.asyncio
    async def test_get_publish_status_success(
        self, 
        async_client: AsyncClient,
        mock_publish_status
    ):
        """
        GET /api/publishing/status/{camera_id} debe devolver el estado actual.
        """
        # Arrange
        camera_id = "cam_001"
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.get_publish_status.return_value = mock_publish_status
            
            # Act
            response = await async_client.get(f"/api/publishing/status/{camera_id}")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verificar estructura de respuesta
            assert data["camera_id"] == camera_id
            assert data["status"] == "PUBLISHING"  # Ahora en mayúsculas
            assert data["publish_path"] == "cam_001"
            assert data["uptime_seconds"] == 3600.0
            assert data["error_count"] == 0
            assert data["last_error"] is None
            
            # Verificar métricas
            assert "metrics" in data
            metrics = data["metrics"]
            assert metrics["fps"] == 25.0
            assert metrics["bitrate_kbps"] == 2048.0
            assert metrics["viewers"] == 3
    
    @pytest.mark.asyncio
    async def test_get_publish_status_not_found(
        self,
        async_client: AsyncClient
    ):
        """
        GET /api/publishing/status/{camera_id} debe devolver 404 si no existe.
        """
        # Arrange
        camera_id = "cam_invalid"
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.get_publish_status.return_value = None
            
            # Act
            response = await async_client.get(f"/api/publishing/status/{camera_id}")
            
            # Assert
            assert response.status_code == 404
            assert "Publicación no encontrada" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_list_active_publications(
        self,
        async_client: AsyncClient
    ):
        """
        GET /api/publishing/status/list debe devolver lista de publicaciones activas.
        """
        # Arrange
        mock_publications = [
            {
                "camera_id": "cam_001",
                "status": PublishStatus.PUBLISHING.value,
                "publish_path": "cam_001",
                "uptime_seconds": 3600,
                "error_count": 0,
                "last_error": None,
                "metrics": None
            },
            {
                "camera_id": "cam_002",
                "status": PublishStatus.STARTING.value,
                "publish_path": "cam_002",
                "uptime_seconds": 0,
                "error_count": 0,
                "last_error": None,
                "metrics": None
            }
        ]
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.get_all_publish_status.return_value = mock_publications
            
            # Act
            response = await async_client.get("/api/publishing/status/list")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 2
            assert data["active"] == 2
            assert len(data["items"]) == 2
            
            # Verificar que los estados usan mayúsculas
            assert data["items"][0]["status"] == "PUBLISHING"
            assert data["items"][1]["status"] == "STARTING"


class TestPublishingControlEndpoints:
    """Tests para endpoints de control de publicación."""
    
    @pytest.mark.asyncio
    async def test_start_publishing_success(
        self,
        async_client: AsyncClient
    ):
        """
        POST /api/publishing/start debe iniciar publicación correctamente.
        """
        # Arrange
        request_data = {
            "camera_id": "cam_001",
            "force_restart": False
        }
        
        mock_result = {
            "success": True,
            "camera_id": "cam_001",
            "publish_path": "cam_001",
            "error": None,
            "error_type": None,
            "process_id": 12345
        }
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.start_publishing = AsyncMock(return_value=mock_result)
            
            # Act
            response = await async_client.post(
                "/api/publishing/start",
                json=request_data
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["camera_id"] == "cam_001"
            assert data["publish_path"] == "cam_001"
            assert data["error"] is None
            
            # Verificar que se llamó con los parámetros correctos
            mock_presenter.start_publishing.assert_called_once_with(
                "cam_001",
                force_restart=False
            )
    
    @pytest.mark.asyncio
    async def test_start_publishing_already_running(
        self,
        async_client: AsyncClient
    ):
        """
        POST /api/publishing/start debe manejar cuando ya está publicando.
        """
        # Arrange
        request_data = {
            "camera_id": "cam_001",
            "force_restart": False
        }
        
        mock_result = {
            "success": False,
            "camera_id": "cam_001",
            "publish_path": None,
            "error": "Ya existe una publicación activa",
            "error_type": "already_publishing",
            "process_id": None
        }
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.start_publishing = AsyncMock(return_value=mock_result)
            
            # Act
            response = await async_client.post(
                "/api/publishing/start",
                json=request_data
            )
            
            # Assert
            assert response.status_code == 200  # No es error HTTP
            data = response.json()
            
            assert data["success"] is False
            assert data["error"] == "Ya existe una publicación activa"
            assert data["error_type"] == "already_publishing"
    
    @pytest.mark.asyncio
    async def test_stop_publishing_success(
        self,
        async_client: AsyncClient
    ):
        """
        POST /api/publishing/stop debe detener publicación correctamente.
        """
        # Arrange
        request_data = {
            "camera_id": "cam_001"
        }
        
        mock_result = {
            "success": True,
            "camera_id": "cam_001",
            "message": "Publicación detenida exitosamente"
        }
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.stop_publishing = AsyncMock(return_value=mock_result)
            
            # Act
            response = await async_client.post(
                "/api/publishing/stop",
                json=request_data
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["camera_id"] == "cam_001"
            assert "exitosamente" in data["message"]


class TestPublishingHealthEndpoints:
    """Tests para endpoints de salud del sistema."""
    
    @pytest.mark.asyncio
    async def test_get_system_health(
        self,
        async_client: AsyncClient,
        mock_mediamtx_server
    ):
        """
        GET /api/publishing/health debe devolver estado de salud del sistema.
        
        Verifica que el mapeo de overall_status funciona correctamente.
        """
        # Arrange - Simular respuesta del servicio de BD
        mock_servers = [mock_mediamtx_server]
        
        with patch('api.routers.publishing.mediamtx_db_service') as mock_db:
            mock_db.get_all_servers = AsyncMock(return_value=mock_servers)
            mock_db.check_server_health = AsyncMock(return_value={
                "server_id": 1,
                "server_name": "Test MediaMTX Server",
                "health_status": "healthy",
                "last_check_time": datetime.utcnow(),
                "rtsp_server_ok": True,
                "api_server_ok": True,
                "paths_ok": True,
                "active_connections": 5,
                "cpu_usage_percent": 25.5,
                "memory_usage_mb": 512.0,
                "uptime_seconds": 86400,
                "error_count": 0,
                "last_error": None,
                "warnings": []
            })
            mock_db.get_publishing_stats = AsyncMock(return_value={
                "active_publications": 5,
                "total_publications": 5
            })
            
            # Act
            response = await async_client.get("/api/publishing/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verificar estructura principal
            assert data["overall_status"] in ["healthy", "warning", "error"]
            assert data["total_servers"] == 1
            assert data["healthy_servers"] == 1
            assert data["active_publications"] == 5
            assert data["total_viewers"] >= 0
            
            # Verificar detalles del servidor
            assert len(data["servers"]) == 1
            server = data["servers"][0]
            assert server["server_id"] == 1
            assert server["health_status"] == "healthy"
            
            # Verificar arrays de alertas y recomendaciones
            assert isinstance(data["active_alerts"], list)
            assert isinstance(data["recommendations"], list)
    
    @pytest.mark.asyncio 
    async def test_get_system_health_degraded(
        self,
        async_client: AsyncClient
    ):
        """
        GET /api/publishing/health debe mapear 'degraded' a 'warning'.
        """
        # Arrange - Simular sistema degradado
        mock_servers = [
            {"id": 1, "name": "Server 1", "is_active": True},
            {"id": 2, "name": "Server 2", "is_active": True}
        ]
        
        with patch('api.routers.publishing.mediamtx_db_service') as mock_db:
            mock_db.get_all_servers = AsyncMock(return_value=mock_servers)
            
            # Un servidor saludable, otro no
            mock_db.check_server_health = AsyncMock(side_effect=[
                {
                    "server_id": 1,
                    "health_status": "healthy",
                    "server_name": "Server 1",
                    "last_check_time": datetime.utcnow(),
                    "rtsp_server_ok": True,
                    "active_connections": 5,
                    "error_count": 0,
                    "warnings": []
                },
                {
                    "server_id": 2,
                    "health_status": "unhealthy",
                    "server_name": "Server 2", 
                    "last_check_time": datetime.utcnow(),
                    "rtsp_server_ok": False,
                    "active_connections": 0,
                    "error_count": 5,
                    "warnings": ["Server not responding"]
                }
            ])
            
            mock_db.get_publishing_stats = AsyncMock(return_value={
                "active_publications": 3,
                "total_publications": 3
            })
            
            # Act
            response = await async_client.get("/api/publishing/health")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verificar que 'degraded' se mapea a 'warning'
            assert data["overall_status"] == "warning"  # No 'degraded'
            assert data["healthy_servers"] == 1
            assert data["total_servers"] == 2
            
            # Debe haber recomendaciones
            assert len(data["recommendations"]) > 0


class TestPublishingMetricsEndpoints:
    """Tests para endpoints de métricas."""
    
    @pytest.mark.asyncio
    async def test_get_current_metrics(
        self,
        async_client: AsyncClient,
        mock_publish_metrics
    ):
        """
        GET /api/publishing/metrics/current/{camera_id} debe devolver métricas actuales.
        """
        # Arrange
        camera_id = "cam_001"
        
        with patch('api.routers.publishing_metrics.metrics_service') as mock_service:
            mock_service.get_latest_metrics = AsyncMock(return_value=mock_publish_metrics)
            
            # Act
            response = await async_client.get(
                f"/api/publishing/metrics/current/{camera_id}"
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verificar estructura de métricas
            assert data["camera_id"] == camera_id
            assert data["fps"] == 30.0
            assert data["bitrate_kbps"] == 3000.0
            assert data["viewers"] == 5
            assert data["frames_sent"] == 150000
            assert data["bytes_sent"] == 1073741824
            assert data["quality_score"] == 95.0
            assert data["status"] == "optimal"
    
    @pytest.mark.asyncio
    async def test_get_metrics_history(
        self,
        async_client: AsyncClient
    ):
        """
        GET /api/publishing/metrics/{camera_id}/history debe devolver historial paginado.
        """
        # Arrange
        camera_id = "cam_001"
        mock_history = {
            "camera_id": camera_id,
            "total": 100,
            "page": 1,
            "page_size": 20,
            "items": [mock_publish_metrics for _ in range(20)],
            "time_range": {
                "start": "2024-01-15T00:00:00Z",
                "end": "2024-01-15T23:59:59Z"
            }
        }
        
        with patch('api.routers.publishing_metrics.metrics_service') as mock_service:
            mock_service.get_metrics_history = AsyncMock(return_value=mock_history)
            
            # Act
            response = await async_client.get(
                f"/api/publishing/metrics/{camera_id}/history",
                params={"page": 1, "page_size": 20}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verificar paginación
            assert data["total"] == 100
            assert data["page"] == 1
            assert data["page_size"] == 20
            assert len(data["items"]) == 20
            assert "time_range" in data
            
            # Verificar propiedades computadas
            assert data["has_next"] is True
            assert data["has_previous"] is False
            assert data["total_pages"] == 5


class TestPublishingAlertsEndpoints:
    """Tests para endpoints de alertas."""
    
    @pytest.mark.asyncio
    async def test_dismiss_alert_success(
        self,
        async_client: AsyncClient
    ):
        """
        POST /api/publishing/alerts/{alert_id}/dismiss debe descartar alerta.
        
        TODO: Este endpoint usa almacenamiento en memoria temporal.
        Cuando se implemente persistencia en BD, actualizar este test.
        """
        # Arrange
        alert_id = "alert_12345"
        request_data = {
            "note": "Falsa alarma, ignorar"
        }
        
        # Act
        response = await async_client.post(
            f"/api/publishing/alerts/{alert_id}/dismiss",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["alert_id"] == alert_id
        assert "descartada exitosamente" in data["message"]
        assert data["note"] == "Falsa alarma, ignorar"
        
        # Verificar que incluye nota sobre temporalidad
        assert "temporal" in data["note"] or "reiniciar" in data["note"]
    
    @pytest.mark.asyncio
    async def test_dismiss_alert_already_dismissed(
        self,
        async_client: AsyncClient
    ):
        """
        POST /api/publishing/alerts/{alert_id}/dismiss debe manejar alertas ya descartadas.
        """
        # Arrange
        alert_id = "alert_12345"
        
        # Descartar primero
        await async_client.post(
            f"/api/publishing/alerts/{alert_id}/dismiss",
            json={}
        )
        
        # Act - Intentar descartar de nuevo
        response = await async_client.post(
            f"/api/publishing/alerts/{alert_id}/dismiss",
            json={}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "ya estaba descartada" in data["message"]


# TODO: Agregar más tests cuando se implementen los siguientes endpoints:
# - Tests de configuración de servidores MediaMTX
# - Tests de gestión de paths
# - Tests de exportación de métricas
# - Tests de analytics de viewers
# - Tests de historial de publicaciones