"""
Tests de integración para flujos completos de publicación.

Estos tests verifican el flujo completo desde inicio hasta detención
de una publicación, incluyendo estados intermedios y métricas.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

from models.publishing.publisher_models import PublishStatus


class TestPublicationLifecycle:
    """Tests del ciclo de vida completo de una publicación."""
    
    @pytest.mark.asyncio
    async def test_complete_publication_flow(
        self,
        async_client: AsyncClient,
        mock_mediamtx_server
    ):
        """
        Test del flujo completo: iniciar -> publicar -> obtener métricas -> detener.
        
        Este test simula el ciclo de vida completo de una publicación,
        verificando que los estados cambian correctamente.
        """
        camera_id = "cam_001"
        
        # Mock del presenter que simula cambios de estado
        mock_states = {
            "initial": {
                "camera_id": camera_id,
                "status": PublishStatus.IDLE.value,
                "publish_path": None,
                "uptime_seconds": 0,
                "error_count": 0,
                "last_error": None,
                "metrics": None
            },
            "starting": {
                "camera_id": camera_id,
                "status": PublishStatus.STARTING.value,
                "publish_path": "cam_001",
                "uptime_seconds": 0,
                "error_count": 0,
                "last_error": None,
                "metrics": None
            },
            "publishing": {
                "camera_id": camera_id,
                "status": PublishStatus.PUBLISHING.value,
                "publish_path": "cam_001",
                "uptime_seconds": 10,
                "error_count": 0,
                "last_error": None,
                "metrics": {
                    "fps": 25.0,
                    "bitrate_kbps": 2048.0,
                    "viewers": 2,
                    "frames_sent": 250,
                    "bytes_sent": 2621440,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            "stopped": {
                "camera_id": camera_id,
                "status": PublishStatus.STOPPED.value,
                "publish_path": None,
                "uptime_seconds": 0,
                "error_count": 0,
                "last_error": None,
                "metrics": None
            }
        }
        
        current_state = "initial"
        
        def get_current_status(cam_id):
            """Simula el estado actual basado en la variable."""
            return mock_states[current_state]
        
        async def simulate_start_publishing(cam_id, force_restart=False):
            """Simula el inicio de publicación."""
            nonlocal current_state
            if current_state == "initial":
                current_state = "starting"
                # Simular transición a publishing después de un delay
                await asyncio.sleep(0.1)
                current_state = "publishing"
                return {
                    "success": True,
                    "camera_id": cam_id,
                    "publish_path": "cam_001",
                    "error": None,
                    "process_id": 12345
                }
            return {
                "success": False,
                "error": "Ya está publicando"
            }
        
        async def simulate_stop_publishing(cam_id):
            """Simula la detención de publicación."""
            nonlocal current_state
            if current_state == "publishing":
                current_state = "stopped"
                return {
                    "success": True,
                    "camera_id": cam_id,
                    "message": "Publicación detenida"
                }
            return {
                "success": False,
                "error": "No hay publicación activa"
            }
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.get_publish_status.side_effect = get_current_status
            mock_presenter.start_publishing = AsyncMock(side_effect=simulate_start_publishing)
            mock_presenter.stop_publishing = AsyncMock(side_effect=simulate_stop_publishing)
            
            # Step 1: Verificar estado inicial
            response = await async_client.get(f"/api/publishing/status/{camera_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "IDLE"
            assert data["metrics"] is None
            
            # Step 2: Iniciar publicación
            response = await async_client.post(
                "/api/publishing/start",
                json={"camera_id": camera_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["publish_path"] == "cam_001"
            
            # Step 3: Verificar estado PUBLISHING
            await asyncio.sleep(0.2)  # Esperar transición
            response = await async_client.get(f"/api/publishing/status/{camera_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "PUBLISHING"
            assert data["metrics"] is not None
            assert data["metrics"]["fps"] == 25.0
            
            # Step 4: Obtener métricas actuales
            with patch('api.routers.publishing_metrics.metrics_service') as mock_metrics:
                mock_metrics.get_latest_metrics = AsyncMock(return_value={
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "fps": 25.0,
                    "bitrate_kbps": 2048.0,
                    "viewers": 2,
                    "frames_sent": 250,
                    "bytes_sent": 2621440,
                    "quality_score": 92.0,
                    "status": "optimal"
                })
                
                response = await async_client.get(
                    f"/api/publishing/metrics/current/{camera_id}"
                )
                assert response.status_code == 200
                metrics = response.json()
                assert metrics["quality_score"] == 92.0
                assert metrics["status"] == "optimal"
            
            # Step 5: Detener publicación
            response = await async_client.post(
                "/api/publishing/stop",
                json={"camera_id": camera_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Step 6: Verificar estado final
            response = await async_client.get(f"/api/publishing/status/{camera_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "STOPPED"
            assert data["metrics"] is None
    
    @pytest.mark.asyncio
    async def test_publication_error_handling(
        self,
        async_client: AsyncClient
    ):
        """
        Test del manejo de errores durante la publicación.
        
        Verifica que los errores se reportan correctamente y el sistema
        puede recuperarse.
        """
        camera_id = "cam_002"
        
        # Simular un error durante la publicación
        error_state = {
            "camera_id": camera_id,
            "status": PublishStatus.ERROR.value,
            "publish_path": "cam_002",
            "uptime_seconds": 5,
            "error_count": 3,
            "last_error": "Connection to camera lost",
            "metrics": None
        }
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            # Simular fallo al iniciar
            mock_presenter.start_publishing = AsyncMock(return_value={
                "success": False,
                "camera_id": camera_id,
                "error": "Failed to connect to camera",
                "error_type": "connection_failed"
            })
            
            # Intentar iniciar publicación
            response = await async_client.post(
                "/api/publishing/start",
                json={"camera_id": camera_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Failed to connect" in data["error"]
            
            # Verificar estado de error
            mock_presenter.get_publish_status.return_value = error_state
            response = await async_client.get(f"/api/publishing/status/{camera_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ERROR"
            assert data["error_count"] == 3
            assert "Connection to camera lost" in data["last_error"]
    
    @pytest.mark.asyncio
    async def test_concurrent_publication_requests(
        self,
        async_client: AsyncClient
    ):
        """
        Test de manejo de solicitudes concurrentes.
        
        Verifica que el sistema maneja correctamente intentos
        simultáneos de iniciar/detener publicaciones.
        """
        camera_id = "cam_003"
        
        # Estado compartido para simular condiciones de carrera
        is_publishing = False
        lock = asyncio.Lock()
        
        async def controlled_start(cam_id, force_restart=False):
            """Simula inicio con control de concurrencia."""
            async with lock:
                nonlocal is_publishing
                if is_publishing and not force_restart:
                    return {
                        "success": False,
                        "error": "Ya existe una publicación activa"
                    }
                is_publishing = True
                return {
                    "success": True,
                    "camera_id": cam_id,
                    "publish_path": f"cam_{cam_id}"
                }
        
        with patch('api.routers.publishing.publishing_presenter') as mock_presenter:
            mock_presenter.start_publishing = AsyncMock(side_effect=controlled_start)
            
            # Lanzar múltiples solicitudes concurrentes
            tasks = []
            for i in range(5):
                task = async_client.post(
                    "/api/publishing/start",
                    json={"camera_id": camera_id}
                )
                tasks.append(task)
            
            # Ejecutar todas las solicitudes
            responses = await asyncio.gather(*tasks)
            
            # Solo una debe tener éxito
            successful = [r for r in responses if r.json()["success"]]
            failed = [r for r in responses if not r.json()["success"]]
            
            assert len(successful) == 1
            assert len(failed) == 4
            
            # Verificar mensajes de error
            for response in failed:
                data = response.json()
                assert "Ya existe una publicación activa" in data["error"]


class TestMetricsCollection:
    """Tests de recolección y análisis de métricas."""
    
    @pytest.mark.asyncio
    async def test_metrics_quality_degradation(
        self,
        async_client: AsyncClient
    ):
        """
        Test de detección de degradación en calidad de stream.
        
        Verifica que el sistema detecta cuando las métricas
        indican problemas de calidad.
        """
        camera_id = "cam_004"
        
        # Simular métricas degradándose con el tiempo
        metrics_timeline = [
            {
                "timestamp": "2024-01-15T10:00:00Z",
                "fps": 30.0,
                "bitrate_kbps": 3000.0,
                "quality_score": 95.0,
                "status": "optimal"
            },
            {
                "timestamp": "2024-01-15T10:01:00Z", 
                "fps": 25.0,
                "bitrate_kbps": 2500.0,
                "quality_score": 85.0,
                "status": "optimal"
            },
            {
                "timestamp": "2024-01-15T10:02:00Z",
                "fps": 20.0,
                "bitrate_kbps": 1800.0,
                "quality_score": 70.0,
                "status": "degraded"
            },
            {
                "timestamp": "2024-01-15T10:03:00Z",
                "fps": 15.0,
                "bitrate_kbps": 1000.0,
                "quality_score": 45.0,
                "status": "poor"
            }
        ]
        
        with patch('api.routers.publishing_metrics.metrics_service') as mock_service:
            # Simular historial de métricas
            mock_service.get_metrics_history = AsyncMock(return_value={
                "camera_id": camera_id,
                "total": len(metrics_timeline),
                "page": 1,
                "page_size": 10,
                "items": [
                    {
                        "camera_id": camera_id,
                        **metric,
                        "viewers": 5,
                        "frames_sent": 1000 * (i + 1),
                        "bytes_sent": 1048576 * (i + 1)
                    }
                    for i, metric in enumerate(metrics_timeline)
                ],
                "time_range": {
                    "start": metrics_timeline[0]["timestamp"],
                    "end": metrics_timeline[-1]["timestamp"]
                }
            })
            
            # Obtener historial
            response = await async_client.get(
                f"/api/publishing/metrics/{camera_id}/history",
                params={"page": 1, "page_size": 10}
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verificar degradación progresiva
            items = data["items"]
            assert items[0]["status"] == "optimal"
            assert items[-1]["status"] == "poor"
            
            # Verificar que quality_score disminuye
            quality_scores = [item["quality_score"] for item in items]
            assert quality_scores == sorted(quality_scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_metrics_alert_generation(
        self,
        async_client: AsyncClient
    ):
        """
        Test de generación de alertas basadas en métricas.
        
        TODO: Cuando se implemente el sistema de alertas automáticas
        basadas en métricas, actualizar este test.
        """
        # Por ahora verificamos que el health endpoint incluye alertas
        with patch('api.routers.publishing.mediamtx_db_service') as mock_db:
            mock_db.get_all_servers = AsyncMock(return_value=[
                {"id": 1, "name": "Server 1", "is_active": True}
            ])
            mock_db.check_server_health = AsyncMock(return_value={
                "server_id": 1,
                "server_name": "Server 1",
                "health_status": "healthy",
                "last_check_time": datetime.utcnow(),
                "rtsp_server_ok": True,
                "active_connections": 50,  # Alto número de conexiones
                "cpu_usage_percent": 85.0,  # Alto uso de CPU
                "memory_usage_mb": 1900.0,  # Alto uso de memoria
                "error_count": 0,
                "warnings": ["High CPU usage", "High memory usage"]
            })
            mock_db.get_publishing_stats = AsyncMock(return_value={
                "active_publications": 45,
                "total_publications": 45
            })
            
            response = await async_client.get("/api/publishing/health")
            assert response.status_code == 200
            data = response.json()
            
            # Debe haber alertas por alto uso de recursos
            assert len(data["active_alerts"]) > 0
            
            # Verificar que hay una alerta de performance
            perf_alerts = [
                a for a in data["active_alerts"] 
                if a["alert_type"] == "performance"
            ]
            assert len(perf_alerts) > 0


# TODO: Agregar más tests de integración cuando se implementen:
# - Test de failover entre servidores MediaMTX
# - Test de recuperación automática después de errores
# - Test de límites de publicaciones simultáneas
# - Test de integración con sistema de permisos/autenticación