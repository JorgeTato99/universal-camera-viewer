"""
Definiciones de vistas SQL para consultas optimizadas.

Este módulo contiene todas las vistas de la base de datos
que facilitan consultas complejas y reportes.
"""


def get_camera_views():
    """Vistas relacionadas con cámaras."""
    return [
        # Vista de cámaras con información completa
        """
        CREATE VIEW camera_overview AS
        SELECT 
            c.camera_id,
            c.code,
            c.brand,
            c.model,
            c.display_name,
            c.ip_address,
            c.location,
            c.is_active,
            COUNT(DISTINCT ce.endpoint_id) as endpoint_count,
            COUNT(DISTINCT cc.credential_id) as credential_count,
            COUNT(DISTINCT cp.protocol_id) as protocol_count,
            cs.last_connection_at,
            cs.successful_connections,
            cs.failed_connections
        FROM cameras c
        LEFT JOIN camera_endpoints ce ON c.camera_id = ce.camera_id
        LEFT JOIN camera_credentials cc ON c.camera_id = cc.camera_id
        LEFT JOIN camera_protocols cp ON c.camera_id = cp.camera_id
        LEFT JOIN camera_statistics cs ON c.camera_id = cs.camera_id
        GROUP BY c.camera_id
        """,
        
        # Vista de endpoints verificados
        """
        CREATE VIEW verified_endpoints AS
        SELECT 
            e.*,
            c.brand,
            c.model,
            c.display_name,
            p.protocol_type,
            p.port
        FROM camera_endpoints e
        JOIN cameras c ON e.camera_id = c.camera_id
        LEFT JOIN camera_protocols p ON e.protocol_id = p.protocol_id
        WHERE e.is_verified = 1 AND e.is_active = 1
        """,
    ]


def get_mediamtx_views():
    """Vistas relacionadas con MediaMTX."""
    return [
        # Vista de publicaciones activas con información completa
        """
        CREATE VIEW active_publications AS
        SELECT 
            cp.publication_id,
            cp.camera_id,
            c.display_name as camera_name,
            c.ip_address as camera_ip,
            cp.server_id,
            ms.server_name,
            ms.rtsp_url,
            cp.publish_path,
            cp.status,
            cp.start_time,
            cp.error_count,
            cp.last_error
        FROM camera_publications cp
        JOIN cameras c ON cp.camera_id = c.camera_id
        JOIN mediamtx_servers ms ON cp.server_id = ms.server_id
        WHERE cp.is_active = 1
        """,
        
        # Vista de estadísticas de publicación
        """
        CREATE VIEW publication_statistics AS
        SELECT 
            ph.camera_id,
            c.display_name as camera_name,
            COUNT(*) as total_sessions,
            SUM(ph.duration_seconds) as total_duration_seconds,
            AVG(ph.duration_seconds) as avg_duration_seconds,
            AVG(ph.average_fps) as avg_fps,
            AVG(ph.average_bitrate_kbps) as avg_bitrate_kbps,
            SUM(ph.total_frames) as total_frames_published,
            SUM(ph.total_data_mb) as total_data_mb,
            SUM(ph.error_count) as total_errors,
            MAX(ph.max_viewers) as max_concurrent_viewers,
            SUM(ph.total_viewer_time_seconds) as total_viewer_time
        FROM publication_history ph
        JOIN cameras c ON ph.camera_id = c.camera_id
        GROUP BY ph.camera_id
        """,
    ]


def get_operational_views():
    """Vistas para operaciones y monitoreo."""
    return [
        # Vista de conexiones recientes
        """
        CREATE VIEW recent_connections AS
        SELECT 
            cl.log_id,
            cl.camera_id,
            c.display_name as camera_name,
            cl.session_id,
            cl.status,
            cl.started_at,
            cl.ended_at,
            cl.duration_seconds,
            cl.error_message
        FROM connection_logs cl
        JOIN cameras c ON cl.camera_id = c.camera_id
        WHERE cl.started_at > datetime('now', '-7 days')
        ORDER BY cl.started_at DESC
        """,
        
        # Vista de eventos críticos
        """
        CREATE VIEW critical_events AS
        SELECT 
            ce.event_id,
            ce.camera_id,
            c.display_name as camera_name,
            ce.event_type,
            ce.event_severity,
            ce.event_data,
            ce.occurred_at,
            ce.is_acknowledged,
            ce.acknowledged_by
        FROM camera_events ce
        JOIN cameras c ON ce.camera_id = c.camera_id
        WHERE ce.event_severity IN ('error', 'critical')
          AND ce.occurred_at > datetime('now', '-30 days')
        ORDER BY ce.occurred_at DESC
        """,
    ]


def get_summary_views():
    """Vistas de resumen y estadísticas."""
    return [
        # Vista de resumen del sistema
        """
        CREATE VIEW system_summary AS
        SELECT 
            (SELECT COUNT(*) FROM cameras WHERE is_active = 1) as active_cameras,
            (SELECT COUNT(*) FROM cameras WHERE is_active = 0) as inactive_cameras,
            (SELECT COUNT(*) FROM camera_publications WHERE is_active = 1) as active_publications,
            (SELECT COUNT(*) FROM network_scans WHERE status = 'running') as running_scans,
            (SELECT COUNT(*) FROM snapshots WHERE capture_time > datetime('now', '-1 day')) as recent_snapshots,
            (SELECT COUNT(*) FROM recordings WHERE start_time > datetime('now', '-1 day')) as recent_recordings,
            (SELECT COUNT(*) FROM camera_events WHERE occurred_at > datetime('now', '-1 hour') AND event_severity IN ('error', 'critical')) as recent_critical_events
        """,
        
        # Vista de uso de almacenamiento
        """
        CREATE VIEW storage_usage AS
        SELECT 
            'snapshots' as storage_type,
            COUNT(*) as file_count,
            SUM(file_size_bytes) / 1048576.0 as total_size_mb,
            AVG(file_size_bytes) / 1048576.0 as avg_size_mb,
            MAX(capture_time) as last_created
        FROM snapshots
        UNION ALL
        SELECT 
            'recordings' as storage_type,
            COUNT(*) as file_count,
            SUM(file_size_bytes) / 1048576.0 as total_size_mb,
            AVG(file_size_bytes) / 1048576.0 as avg_size_mb,
            MAX(start_time) as last_created
        FROM recordings
        """,
    ]


def get_all_views():
    """Retorna todas las vistas de la base de datos."""
    views = []
    views.extend(get_camera_views())
    views.extend(get_mediamtx_views())
    views.extend(get_operational_views())
    views.extend(get_summary_views())
    return views


def get_view_count():
    """Retorna el número total de vistas."""
    return len(get_all_views())


def get_view_names():
    """Retorna los nombres de todas las vistas."""
    names = []
    for view_sql in get_all_views():
        # Extraer nombre de la vista del SQL
        if "CREATE VIEW" in view_sql:
            parts = view_sql.split()
            idx = parts.index("VIEW") + 1
            if idx < len(parts):
                view_name = parts[idx].strip()
                names.append(view_name)
    return names