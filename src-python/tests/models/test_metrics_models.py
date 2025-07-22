"""
Tests para los modelos de métricas del sistema de publicación.

Verifica la correcta funcionalidad de los modelos de métricas,
historial, paths, estadísticas y analytics.
"""

import pytest
from datetime import datetime, timedelta
from models.publishing.metrics_models import (
    StreamStatus,
    TerminationReason,
    PublishMetrics,
    PublishingHistorySession,
    MediaMTXPath,
    CameraActivity,
    PublishingStatistics,
    GeographicDistribution,
    ViewerAnalytics,
    calculate_metrics_summary,
    aggregate_camera_activities,
)


class TestPublishMetrics:
    """Tests para PublishMetrics."""
    
    def test_create_metrics_basic(self):
        """Prueba creación básica de métricas."""
        metrics = PublishMetrics(
            camera_id="cam_001",
            timestamp=datetime.utcnow(),
            fps=25.0,
            bitrate_kbps=2048.0,
            viewers=5,
            frames_sent=1500,
            bytes_sent=2097152
        )
        
        assert metrics.camera_id == "cam_001"
        assert metrics.fps == 25.0
        assert metrics.bitrate_kbps == 2048.0
        assert metrics.viewers == 5
        assert metrics.quality_score is not None
        assert metrics.status is not None
    
    def test_quality_score_calculation(self):
        """Prueba cálculo automático de quality score."""
        # Métricas óptimas
        metrics_good = PublishMetrics(
            camera_id="cam_001",
            timestamp=datetime.utcnow(),
            fps=30.0,
            bitrate_kbps=3000.0,
            viewers=10
        )
        assert metrics_good.quality_score >= 80
        assert metrics_good.status == StreamStatus.OPTIMAL
        
        # Métricas degradadas
        metrics_degraded = PublishMetrics(
            camera_id="cam_002",
            timestamp=datetime.utcnow(),
            fps=18.0,
            bitrate_kbps=800.0,
            viewers=2
        )
        assert 50 <= metrics_degraded.quality_score < 80
        assert metrics_degraded.status == StreamStatus.DEGRADED
        
        # Métricas pobres
        metrics_poor = PublishMetrics(
            camera_id="cam_003",
            timestamp=datetime.utcnow(),
            fps=10.0,
            bitrate_kbps=300.0,
            viewers=0
        )
        assert metrics_poor.quality_score < 50
        assert metrics_poor.status == StreamStatus.POOR
    
    def test_metrics_with_dropped_frames(self):
        """Prueba métricas con frames perdidos."""
        metrics = PublishMetrics(
            camera_id="cam_001",
            timestamp=datetime.utcnow(),
            fps=25.0,
            bitrate_kbps=2048.0,
            frames_sent=10000,
            dropped_frames=100  # 1% de pérdida
        )
        
        # 1% de pérdida debería penalizar ligeramente
        assert metrics.quality_score < 95
    
    def test_metrics_to_dict(self):
        """Prueba serialización a diccionario."""
        timestamp = datetime.utcnow()
        metrics = PublishMetrics(
            camera_id="cam_001",
            timestamp=timestamp,
            fps=25.0,
            bitrate_kbps=2048.0,
            viewers=5
        )
        
        data = metrics.to_dict()
        assert data["camera_id"] == "cam_001"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["fps"] == 25.0
        assert data["bitrate_kbps"] == 2048.0
        assert data["viewers"] == 5
        assert "quality_score" in data
        assert "status" in data


class TestPublishingHistorySession:
    """Tests para PublishingHistorySession."""
    
    def test_create_session(self):
        """Prueba creación de sesión histórica."""
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()
        
        session = PublishingHistorySession(
            session_id="sess_123",
            camera_id="cam_001",
            camera_name="Cámara Principal",
            server_id=1,
            server_name="MediaMTX Principal",
            publish_path="cam_001",
            start_time=start_time,
            end_time=end_time,
            total_frames=180000,
            total_bytes=1073741824,  # 1 GB
            average_fps=25.0,
            average_bitrate_kbps=2048.0,
            peak_viewers=15,
            average_viewers=8.5
        )
        
        assert session.session_id == "sess_123"
        assert session.duration_seconds == 7200  # 2 horas
        assert session.duration_formatted == "2h 0m 0s"
        assert session.data_transferred_gb == 1.0
    
    def test_session_duration_formatting(self):
        """Prueba formateo de duración."""
        # Solo segundos
        session1 = PublishingHistorySession(
            session_id="s1",
            camera_id="c1",
            server_id=1,
            publish_path="p1",
            start_time=datetime.utcnow(),
            duration_seconds=45
        )
        assert session1.duration_formatted == "45s"
        
        # Minutos y segundos
        session2 = PublishingHistorySession(
            session_id="s2",
            camera_id="c2",
            server_id=1,
            publish_path="p2",
            start_time=datetime.utcnow(),
            duration_seconds=125
        )
        assert session2.duration_formatted == "2m 5s"
        
        # Horas, minutos y segundos
        session3 = PublishingHistorySession(
            session_id="s3",
            camera_id="c3",
            server_id=1,
            publish_path="p3",
            start_time=datetime.utcnow(),
            duration_seconds=7265
        )
        assert session3.duration_formatted == "2h 1m 5s"
    
    def test_session_with_error(self):
        """Prueba sesión con terminación por error."""
        session = PublishingHistorySession(
            session_id="sess_error",
            camera_id="cam_001",
            server_id=1,
            publish_path="cam_001",
            start_time=datetime.utcnow() - timedelta(minutes=30),
            end_time=datetime.utcnow(),
            status="error",
            termination_reason=TerminationReason.CONNECTION_LOST,
            error_message="Connection timeout",
            error_count=5
        )
        
        assert session.status == "error"
        assert session.termination_reason == TerminationReason.CONNECTION_LOST
        assert session.error_message == "Connection timeout"
        assert session.error_count == 5


class TestMediaMTXPath:
    """Tests para MediaMTXPath."""
    
    def test_create_path(self):
        """Prueba creación de path MediaMTX."""
        path = MediaMTXPath(
            path_id=1,
            server_id=1,
            server_name="MediaMTX Principal",
            path_name="cam_001",
            source_type="rtsp",
            source_url="rtsp://192.168.1.100:554/stream1",
            is_active=True,
            is_running=True,
            connected_readers=5
        )
        
        assert path.path_id == 1
        assert path.path_name == "cam_001"
        assert path.is_configured is True
        assert path.viewer_count == 5
    
    def test_path_configuration_validation(self):
        """Prueba validación de configuración de path."""
        # Path RTSP sin URL - no configurado
        path1 = MediaMTXPath(
            path_id=1,
            server_id=1,
            path_name="test1",
            source_type="rtsp"
        )
        assert path1.is_configured is False
        
        # Path RTSP con URL - configurado
        path2 = MediaMTXPath(
            path_id=2,
            server_id=1,
            path_name="test2",
            source_type="rtsp",
            source_url="rtsp://example.com/stream"
        )
        assert path2.is_configured is True
        
        # Path WebRTC - siempre configurado
        path3 = MediaMTXPath(
            path_id=3,
            server_id=1,
            path_name="test3",
            source_type="webrtc"
        )
        assert path3.is_configured is True


class TestCameraActivity:
    """Tests para CameraActivity."""
    
    def test_create_activity(self):
        """Prueba creación de actividad de cámara."""
        activity = CameraActivity(
            camera_id="cam_001",
            camera_name="Cámara Principal",
            total_sessions=50,
            total_duration_hours=120.5,
            total_data_gb=250.0,
            average_viewers=12.5,
            peak_viewers=30,
            average_quality_score=85.0,
            error_rate=2.5,
            uptime_percentage=97.5,
            last_active=datetime.utcnow() - timedelta(hours=2)
        )
        
        assert activity.camera_id == "cam_001"
        assert activity.total_sessions == 50
        assert activity.is_recently_active is True
    
    def test_recently_active_check(self):
        """Prueba verificación de actividad reciente."""
        # Activa hace 2 horas - reciente
        activity1 = CameraActivity(
            camera_id="cam_001",
            camera_name="Cámara 1",
            last_active=datetime.utcnow() - timedelta(hours=2)
        )
        assert activity1.is_recently_active is True
        
        # Activa hace 2 días - no reciente
        activity2 = CameraActivity(
            camera_id="cam_002",
            camera_name="Cámara 2",
            last_active=datetime.utcnow() - timedelta(days=2)
        )
        assert activity2.is_recently_active is False
        
        # Sin actividad registrada
        activity3 = CameraActivity(
            camera_id="cam_003",
            camera_name="Cámara 3"
        )
        assert activity3.is_recently_active is False


class TestPublishingStatistics:
    """Tests para PublishingStatistics."""
    
    def test_create_statistics(self):
        """Prueba creación de estadísticas."""
        stats = PublishingStatistics(
            time_range="Últimas 24 horas",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            total_sessions=100,
            total_duration_hours=200.0,
            total_data_gb=500.0,
            unique_cameras=10,
            average_viewers=15.0,
            peak_viewers=50,
            error_rate=5.0,
            uptime_percentage=95.0
        )
        
        assert stats.total_sessions == 100
        assert stats.success_rate == 95.0  # 100 - 5.0 error_rate
        assert stats.total_bandwidth_gbps > 0
    
    def test_bandwidth_calculation(self):
        """Prueba cálculo de ancho de banda."""
        stats = PublishingStatistics(
            time_range="Test",
            start_date=datetime.utcnow() - timedelta(hours=1),
            end_date=datetime.utcnow(),
            total_duration_hours=1.0,
            total_data_gb=3.6  # 3.6 GB en 1 hora = 0.008 Gbps
        )
        
        # 3.6 GB * 8 bits/byte / 3600 segundos = 0.008 Gbps
        assert abs(stats.total_bandwidth_gbps - 0.008) < 0.001


class TestViewerAnalytics:
    """Tests para ViewerAnalytics."""
    
    def test_create_analytics(self):
        """Prueba creación de analytics de viewers."""
        analytics = ViewerAnalytics(
            time_range="Últimas 24 horas",
            total_unique_viewers=1000,
            total_viewing_hours=2500.0,
            average_session_duration_minutes=30.0,
            peak_concurrent_viewers=150,
            peak_time=datetime.utcnow()
        )
        
        assert analytics.total_unique_viewers == 1000
        assert analytics.total_viewing_hours == 2500.0
    
    def test_geographic_distribution(self):
        """Prueba distribución geográfica."""
        geo1 = GeographicDistribution(
            country_code="MX",
            country_name="México",
            state_code="CDMX",
            state_name="Ciudad de México",
            city_name="Ciudad de México",
            viewer_count=500,
            percentage=50.0
        )
        
        geo2 = GeographicDistribution(
            country_code="MX",
            country_name="México",
            state_code="PUE",
            state_name="Puebla",
            city_name="Puebla",
            viewer_count=300,
            percentage=30.0
        )
        
        analytics = ViewerAnalytics(
            time_range="Test",
            geographic_distribution=[geo1, geo2]
        )
        
        top_locations = analytics.get_top_locations(limit=1)
        assert len(top_locations) == 1
        assert top_locations[0].viewer_count == 500


class TestHelperFunctions:
    """Tests para funciones auxiliares."""
    
    def test_calculate_metrics_summary(self):
        """Prueba cálculo de resumen de métricas."""
        metrics_list = [
            PublishMetrics(
                camera_id="cam_001",
                timestamp=datetime.utcnow(),
                fps=25.0,
                bitrate_kbps=2000.0,
                viewers=5
            ),
            PublishMetrics(
                camera_id="cam_001",
                timestamp=datetime.utcnow(),
                fps=30.0,
                bitrate_kbps=2500.0,
                viewers=8
            ),
            PublishMetrics(
                camera_id="cam_001",
                timestamp=datetime.utcnow(),
                fps=20.0,
                bitrate_kbps=1800.0,
                viewers=3
            )
        ]
        
        summary = calculate_metrics_summary(metrics_list)
        
        assert summary["count"] == 3
        assert summary["avg_fps"] == 25.0  # (25 + 30 + 20) / 3
        assert summary["min_fps"] == 20.0
        assert summary["max_fps"] == 30.0
        assert summary["avg_bitrate_kbps"] == 2100.0  # (2000 + 2500 + 1800) / 3
        assert summary["peak_viewers"] == 8
    
    def test_calculate_metrics_summary_empty(self):
        """Prueba resumen con lista vacía."""
        summary = calculate_metrics_summary([])
        
        assert summary["count"] == 0
        assert summary["avg_fps"] == 0.0
        assert summary["avg_viewers"] == 0.0
    
    def test_aggregate_camera_activities(self):
        """Prueba agregación de actividades por cámara."""
        sessions = [
            PublishingHistorySession(
                session_id="s1",
                camera_id="cam_001",
                camera_name="Cámara 1",
                server_id=1,
                publish_path="cam_001",
                start_time=datetime.utcnow() - timedelta(hours=2),
                duration_seconds=3600,
                total_bytes=1073741824,  # 1 GB
                average_viewers=10.0,
                peak_viewers=15,
                quality_score=85.0
            ),
            PublishingHistorySession(
                session_id="s2",
                camera_id="cam_001",
                camera_name="Cámara 1",
                server_id=1,
                publish_path="cam_001",
                start_time=datetime.utcnow() - timedelta(hours=1),
                duration_seconds=1800,
                total_bytes=536870912,  # 0.5 GB
                average_viewers=8.0,
                peak_viewers=12,
                quality_score=90.0,
                error_count=1,
                termination_reason=TerminationReason.ERROR
            ),
            PublishingHistorySession(
                session_id="s3",
                camera_id="cam_002",
                camera_name="Cámara 2",
                server_id=1,
                publish_path="cam_002",
                start_time=datetime.utcnow() - timedelta(hours=3),
                duration_seconds=7200,
                total_bytes=2147483648,  # 2 GB
                average_viewers=20.0,
                peak_viewers=30,
                quality_score=95.0
            )
        ]
        
        activities = aggregate_camera_activities(sessions)
        
        assert len(activities) == 2
        
        # Cámara 1 debe tener 2 sesiones
        cam1_activity = next(a for a in activities if a.camera_id == "cam_001")
        assert cam1_activity.total_sessions == 2
        assert cam1_activity.total_duration_hours == 1.5  # 1 + 0.5 horas
        assert cam1_activity.total_data_gb == 1.5  # 1 + 0.5 GB
        assert cam1_activity.peak_viewers == 15
        assert cam1_activity.error_rate == 50.0  # 1 de 2 sesiones con error
        
        # Cámara 2 debe tener 1 sesión
        cam2_activity = next(a for a in activities if a.camera_id == "cam_002")
        assert cam2_activity.total_sessions == 1
        assert cam2_activity.total_duration_hours == 2.0
        assert cam2_activity.total_data_gb == 2.0
        assert cam2_activity.peak_viewers == 30
        assert cam2_activity.error_rate == 0.0