"""
Definiciones de índices para optimización de consultas.

Este módulo contiene todos los índices de la base de datos
organizados por tabla/funcionalidad.
"""


def get_camera_indexes():
    """Índices para tablas principales de cámaras."""
    return [
        # Índices para cameras
        "CREATE INDEX idx_cameras_ip ON cameras(ip_address)",
        "CREATE INDEX idx_cameras_brand ON cameras(brand)",
        "CREATE INDEX idx_cameras_active ON cameras(is_active)",
        "CREATE INDEX idx_cameras_code ON cameras(code)",
        "CREATE INDEX idx_cameras_location ON cameras(location)",
        
        # Índices para credentials
        "CREATE INDEX idx_credentials_camera ON camera_credentials(camera_id)",
        "CREATE INDEX idx_credentials_default ON camera_credentials(camera_id, is_default)",
        
        # Índices para protocols
        "CREATE INDEX idx_protocols_camera ON camera_protocols(camera_id)",
        "CREATE INDEX idx_protocols_type ON camera_protocols(protocol_type)",
        "CREATE INDEX idx_protocols_primary ON camera_protocols(camera_id, is_primary)",
        
        # Índices para endpoints
        "CREATE INDEX idx_endpoints_camera ON camera_endpoints(camera_id)",
        "CREATE INDEX idx_endpoints_type ON camera_endpoints(endpoint_type)",
        "CREATE INDEX idx_endpoints_verified ON camera_endpoints(is_verified)",
        "CREATE INDEX idx_endpoints_active ON camera_endpoints(camera_id, is_active)",
    ]


def get_operation_indexes():
    """Índices para tablas de operación."""
    return [
        # Índices para statistics
        "CREATE INDEX idx_stats_camera ON camera_statistics(camera_id)",
        "CREATE INDEX idx_stats_last_connection ON camera_statistics(last_connection_at)",
        
        # Índices para logs
        "CREATE INDEX idx_logs_camera ON connection_logs(camera_id)",
        "CREATE INDEX idx_logs_session ON connection_logs(session_id)",
        "CREATE INDEX idx_logs_time ON connection_logs(started_at)",
        "CREATE INDEX idx_logs_status ON connection_logs(status)",
        
        # Índices para events
        "CREATE INDEX idx_events_camera ON camera_events(camera_id)",
        "CREATE INDEX idx_events_type ON camera_events(event_type)",
        "CREATE INDEX idx_events_time ON camera_events(occurred_at)",
        "CREATE INDEX idx_events_severity ON camera_events(event_severity)",
    ]


def get_scanning_indexes():
    """Índices para tablas de escaneo."""
    return [
        # Índices para scans
        "CREATE INDEX idx_scans_time ON network_scans(start_time)",
        "CREATE INDEX idx_scans_status ON network_scans(status)",
        
        # Índices para scan results
        "CREATE INDEX idx_scan_results_scan ON scan_results(scan_id)",
        "CREATE INDEX idx_scan_results_ip ON scan_results(ip_address)",
        "CREATE INDEX idx_scan_results_camera ON scan_results(is_camera)",
    ]


def get_storage_indexes():
    """Índices para tablas de almacenamiento."""
    return [
        # Índices para snapshots
        "CREATE INDEX idx_snapshots_camera ON snapshots(camera_id)",
        "CREATE INDEX idx_snapshots_time ON snapshots(capture_time)",
        
        # Índices para recordings
        "CREATE INDEX idx_recordings_camera ON recordings(camera_id)",
        "CREATE INDEX idx_recordings_time ON recordings(start_time)",
    ]


def get_mediamtx_indexes():
    """Índices para tablas de MediaMTX."""
    return [
        # Índices para MediaMTX servers
        "CREATE INDEX idx_mediamtx_servers_active ON mediamtx_servers(is_active)",
        "CREATE INDEX idx_mediamtx_servers_default ON mediamtx_servers(is_default)",
        
        # Índices para camera publications
        "CREATE INDEX idx_camera_publications_camera ON camera_publications(camera_id)",
        "CREATE INDEX idx_camera_publications_server ON camera_publications(server_id)",
        "CREATE INDEX idx_camera_publications_session ON camera_publications(session_id)",
        "CREATE INDEX idx_camera_publications_status ON camera_publications(status)",
        "CREATE INDEX idx_camera_publications_active ON camera_publications(is_active)",
        
        # Índices para publication history
        "CREATE INDEX idx_publication_history_camera ON publication_history(camera_id)",
        "CREATE INDEX idx_publication_history_server ON publication_history(server_id)",
        "CREATE INDEX idx_publication_history_session ON publication_history(session_id)",
        "CREATE INDEX idx_publication_history_time ON publication_history(start_time)",
        
        # Índices para publication metrics
        "CREATE INDEX idx_publication_metrics_publication ON publication_metrics(publication_id)",
        "CREATE INDEX idx_publication_metrics_time ON publication_metrics(metric_time)",
        
        # Índices para publication viewers
        "CREATE INDEX idx_publication_viewers_publication ON publication_viewers(publication_id)",
        "CREATE INDEX idx_publication_viewers_time ON publication_viewers(start_time)",
        
        # Índices para MediaMTX paths
        "CREATE INDEX idx_mediamtx_paths_server ON mediamtx_paths(server_id)",
        "CREATE INDEX idx_mediamtx_paths_name ON mediamtx_paths(path_name)",
    ]


def get_all_indexes():
    """Retorna todos los índices de la base de datos."""
    indexes = []
    indexes.extend(get_camera_indexes())
    indexes.extend(get_operation_indexes())
    indexes.extend(get_scanning_indexes())
    indexes.extend(get_storage_indexes())
    indexes.extend(get_mediamtx_indexes())
    return indexes


def get_index_count():
    """Retorna el número total de índices."""
    return len(get_all_indexes())