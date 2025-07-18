#!/usr/bin/env python3
"""
Script para crear la base de datos desde cero.

Este script elimina la base de datos existente y crea una nueva
con la estructura 3FN siguiendo las mejores prácticas.
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class DatabaseCreator:
    """Crea la base de datos con estructura 3FN optimizada."""
    
    def __init__(self, db_path: str = "data/camera_data.db"):
        """
        Inicializa el creador de base de datos.
        
        Args:
            db_path: Ruta donde crear la base de datos
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def drop_existing_database(self) -> None:
        """Elimina la base de datos existente si existe."""
        if self.db_path.exists():
            logger.warning(f"Eliminando base de datos existente: {self.db_path}")
            try:
                self.db_path.unlink()
                logger.info("Base de datos eliminada")
            except PermissionError:
                # Intentar cerrar cualquier conexión existente
                import gc
                gc.collect()  # Forzar recolección de basura
                
                # Intentar renombrar en lugar de eliminar
                backup_name = f"{self.db_path}.old_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    self.db_path.rename(backup_name)
                    logger.warning(f"No se pudo eliminar, se renombró a: {backup_name}")
                except Exception as e:
                    logger.error(f"No se pudo eliminar ni renombrar la base de datos: {e}")
                    logger.error("Por favor cierre todos los procesos que usen la base de datos:")
                    logger.error("1. Detenga el servidor FastAPI (Ctrl+C)")
                    logger.error("2. Cierre SQLite Browser o herramientas similares")
                    logger.error("3. Verifique que no haya scripts Python ejecutándose")
                    raise RuntimeError(f"Base de datos en uso: {self.db_path}")
        
    def create_database(self) -> bool:
        """
        Crea la base de datos con todas las tablas.
        
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            # Eliminar DB existente
            self.drop_existing_database()
            
            # Crear nueva conexión
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Habilitar claves foráneas
            cursor.execute("PRAGMA foreign_keys = ON")
            
            logger.info("Creando nueva base de datos...")
            
            # ================== TABLAS PRINCIPALES ==================
            
            # Tabla de cámaras - Información básica e inmutable
            cursor.execute("""
                CREATE TABLE cameras (
                    camera_id TEXT PRIMARY KEY,  -- UUID v4
                    code TEXT UNIQUE,             -- Código legible único (ej: Dahua_IPC-HDW1200SP_192_168_1_100)
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    mac_address TEXT,
                    firmware_version TEXT,
                    hardware_version TEXT,
                    serial_number TEXT UNIQUE,    -- Serial del fabricante si está disponible
                    location TEXT,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,              -- Usuario que creó el registro
                    updated_by TEXT,              -- Usuario que actualizó
                    CHECK (camera_id LIKE '________-____-____-____-____________'),  -- Validar formato UUID
                    CHECK (length(display_name) > 0)
                )
            """)
            
            # Tabla de credenciales - Separada por seguridad y múltiples por cámara
            cursor.execute("""
                CREATE TABLE camera_credentials (
                    credential_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    credential_name TEXT NOT NULL,  -- Nombre descriptivo (ej: "Admin", "Viewer")
                    username TEXT NOT NULL,
                    password_encrypted TEXT NOT NULL,
                    auth_type TEXT DEFAULT 'basic' CHECK (auth_type IN ('basic', 'digest', 'bearer', 'api_key')),
                    api_key TEXT,                   -- Para autenticación por API key
                    certificate_path TEXT,          -- Para autenticación por certificado
                    is_active BOOLEAN DEFAULT 1,
                    is_default BOOLEAN DEFAULT 0,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    UNIQUE(camera_id, credential_name),
                    CHECK (length(username) > 0 OR api_key IS NOT NULL)
                )
            """)
            
            # Tabla de protocolos - Configuración por protocolo
            cursor.execute("""
                CREATE TABLE camera_protocols (
                    protocol_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    protocol_type TEXT NOT NULL CHECK (protocol_type IN ('ONVIF', 'RTSP', 'HTTP', 'HTTPS', 'WEBSOCKET')),
                    port INTEGER NOT NULL CHECK (port > 0 AND port <= 65535),
                    is_enabled BOOLEAN DEFAULT 1,
                    is_primary BOOLEAN DEFAULT 0,
                    version TEXT,                   -- Versión del protocolo (ej: "2.0" para ONVIF)
                    path TEXT,                      -- Path base para el protocolo
                    configuration JSON,             -- Configuración específica del protocolo
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    UNIQUE(camera_id, protocol_type, port)
                )
            """)
            
            # Tabla de endpoints/URLs descubiertas
            # APIs PARCIALMENTE IMPLEMENTADAS - Falta:
            # - POST /cameras/{id}/endpoints - Crear endpoint manual
            # - PUT /cameras/{id}/endpoints/{id} - Actualizar endpoint
            # - DELETE /cameras/{id}/endpoints/{id} - Eliminar endpoint
            # - POST /cameras/{id}/endpoints/{id}/verify - Verificar endpoint
            cursor.execute("""
                CREATE TABLE camera_endpoints (
                    endpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    endpoint_type TEXT NOT NULL,    -- rtsp_main, rtsp_sub, snapshot, onvif_device, etc.
                    endpoint_name TEXT NOT NULL,    -- Nombre descriptivo
                    url TEXT NOT NULL,
                    protocol_id INTEGER,            -- Referencia al protocolo usado
                    credential_id INTEGER,          -- Credencial requerida para este endpoint
                    is_verified BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    last_verified TIMESTAMP,
                    response_time_ms INTEGER,
                    priority INTEGER DEFAULT 0,     -- Para ordenar endpoints preferidos
                    metadata JSON,                  -- Información adicional del endpoint
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    FOREIGN KEY (protocol_id) REFERENCES camera_protocols (protocol_id) ON DELETE SET NULL,
                    FOREIGN KEY (credential_id) REFERENCES camera_credentials (credential_id) ON DELETE SET NULL,
                    UNIQUE(camera_id, endpoint_type, url)
                )
            """)
            
            # Tabla de capacidades - Features soportadas
            # APIs FALTANTES:
            # - GET /cameras/{id}/capabilities - Listar capacidades
            # - POST /cameras/{id}/capabilities/detect - Auto-detectar capacidades
            # - PUT /cameras/{id}/capabilities/{type} - Actualizar capacidad
            # - GET /capabilities/types - Listar tipos de capacidades
            cursor.execute("""
                CREATE TABLE camera_capabilities (
                    capability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    capability_type TEXT NOT NULL,
                    capability_name TEXT NOT NULL,
                    is_supported BOOLEAN DEFAULT 1,
                    configuration JSON,
                    verified_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    UNIQUE(camera_id, capability_type)
                )
            """)
            
            # Tabla de perfiles de streaming
            cursor.execute("""
                CREATE TABLE stream_profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    profile_name TEXT NOT NULL,
                    profile_token TEXT,             -- Token ONVIF si aplica
                    stream_type TEXT DEFAULT 'main' CHECK (stream_type IN ('main', 'sub', 'third')),
                    encoding TEXT CHECK (encoding IN ('H264', 'H265', 'MJPEG', 'MPEG4')),
                    resolution TEXT,                -- "1920x1080", "1280x720", etc.
                    framerate INTEGER CHECK (framerate > 0 AND framerate <= 120),
                    bitrate INTEGER CHECK (bitrate > 0),
                    quality TEXT CHECK (quality IN ('highest', 'high', 'medium', 'low', 'lowest')),
                    gop_interval INTEGER,           -- Group of Pictures interval
                    is_default BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    endpoint_id INTEGER,            -- Endpoint asociado a este perfil
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    FOREIGN KEY (endpoint_id) REFERENCES camera_endpoints (endpoint_id) ON DELETE SET NULL,
                    UNIQUE(camera_id, profile_name)
                )
            """)
            
            # ================== TABLAS DE OPERACIÓN ==================
            
            # Tabla de estadísticas - Métricas agregadas
            # APIs FALTANTES:
            # - GET /cameras/{id}/statistics - Estadísticas de cámara
            # - GET /statistics/summary - Resumen global
            # - POST /statistics/reset - Reiniciar estadísticas
            # - GET /statistics/export - Exportar estadísticas
            cursor.execute("""
                CREATE TABLE camera_statistics (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL UNIQUE,
                    total_connections INTEGER DEFAULT 0 CHECK (total_connections >= 0),
                    successful_connections INTEGER DEFAULT 0 CHECK (successful_connections >= 0),
                    failed_connections INTEGER DEFAULT 0 CHECK (failed_connections >= 0),
                    total_uptime_seconds INTEGER DEFAULT 0 CHECK (total_uptime_seconds >= 0),
                    total_data_mb REAL DEFAULT 0 CHECK (total_data_mb >= 0),
                    average_fps REAL CHECK (average_fps >= 0),
                    average_latency_ms INTEGER CHECK (average_latency_ms >= 0),
                    max_concurrent_streams INTEGER DEFAULT 0,
                    last_connection_at TIMESTAMP,
                    last_disconnection_at TIMESTAMP,
                    last_error_at TIMESTAMP,
                    last_error_code TEXT,
                    last_error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
                )
            """)
            
            # Tabla de logs de conexión - Historial detallado
            # APIs PARCIALMENTE IMPLEMENTADAS - Falta:
            # - GET /connections/logs - Listar todos los logs con filtros
            # - GET /connections/logs/stats - Estadísticas agregadas
            # - DELETE /connections/logs - Limpiar logs antiguos
            # - GET /connections/logs/export - Exportar logs
            cursor.execute("""
                CREATE TABLE connection_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,       -- UUID de la sesión
                    connection_type TEXT,
                    protocol_used TEXT,
                    endpoint_id INTEGER,
                    credential_id INTEGER,
                    status TEXT CHECK (status IN ('connecting', 'connected', 'disconnected', 'failed', 'timeout')),
                    error_code TEXT,
                    error_message TEXT,
                    client_ip TEXT,                 -- IP del cliente que se conectó
                    duration_seconds INTEGER,
                    bytes_sent INTEGER,
                    bytes_received INTEGER,
                    average_fps REAL,
                    started_at TIMESTAMP NOT NULL,
                    ended_at TIMESTAMP,
                    metadata JSON,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    FOREIGN KEY (endpoint_id) REFERENCES camera_endpoints (endpoint_id) ON DELETE SET NULL,
                    FOREIGN KEY (credential_id) REFERENCES camera_credentials (credential_id) ON DELETE SET NULL
                )
            """)
            
            # Tabla de eventos - Registro de eventos importantes
            # APIs PARCIALMENTE IMPLEMENTADAS (solo WebSocket) - Falta:
            # - GET /events - Listar eventos históricos
            # - GET /events/{id} - Obtener detalle de evento
            # - PUT /events/{id}/acknowledge - Reconocer evento
            # - DELETE /events - Limpiar eventos antiguos
            # - GET /events/stats - Estadísticas de eventos
            cursor.execute("""
                CREATE TABLE camera_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,       -- motion, connection_lost, tampering, etc.
                    event_severity TEXT CHECK (event_severity IN ('info', 'warning', 'error', 'critical')),
                    event_data JSON,
                    is_acknowledged BOOLEAN DEFAULT 0,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
                )
            """)
            
            # ================== TABLAS DE ESCANEO ==================
            
            # Tabla de escaneos de red
            cursor.execute("""
                CREATE TABLE network_scans (
                    scan_id TEXT PRIMARY KEY,       -- UUID
                    scan_type TEXT NOT NULL CHECK (scan_type IN ('quick', 'deep', 'custom', 'single')),
                    scan_name TEXT,
                    target_network TEXT NOT NULL,   -- CIDR o IP individual
                    port_list TEXT,                 -- Puertos escaneados
                    protocol_list TEXT,             -- Protocolos buscados
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    total_hosts_scanned INTEGER DEFAULT 0,
                    hosts_alive INTEGER DEFAULT 0,
                    cameras_found INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                    error_message TEXT,
                    created_by TEXT,
                    configuration JSON,             -- Configuración del escaneo
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de resultados de escaneo
            cursor.execute("""
                CREATE TABLE scan_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    mac_address TEXT,
                    hostname TEXT,
                    is_alive BOOLEAN DEFAULT 1,
                    is_camera BOOLEAN DEFAULT 0,
                    confidence_score REAL DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100),
                    detected_brand TEXT,
                    detected_model TEXT,
                    detected_services JSON,         -- Lista de servicios detectados
                    open_ports JSON,                -- Lista de puertos abiertos
                    response_time_ms INTEGER,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_id) REFERENCES network_scans (scan_id) ON DELETE CASCADE,
                    UNIQUE(scan_id, ip_address)
                )
            """)
            
            # ================== TABLAS DE ALMACENAMIENTO ==================
            
            # Tabla de snapshots
            # APIs FALTANTES:
            # - GET /snapshots - Listar snapshots
            # - POST /cameras/{id}/snapshots - Capturar snapshot
            # - GET /snapshots/{id} - Obtener snapshot
            # - DELETE /snapshots/{id} - Eliminar snapshot
            # - GET /snapshots/{id}/download - Descargar snapshot
            # - POST /snapshots/cleanup - Limpiar snapshots antiguos
            cursor.execute("""
                CREATE TABLE snapshots (
                    snapshot_id TEXT PRIMARY KEY,   -- UUID
                    camera_id TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    thumbnail_path TEXT,
                    capture_time TIMESTAMP NOT NULL,
                    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0),
                    width INTEGER CHECK (width > 0),
                    height INTEGER CHECK (height > 0),
                    format TEXT CHECK (format IN ('JPEG', 'PNG', 'WEBP')),
                    quality INTEGER CHECK (quality > 0 AND quality <= 100),
                    trigger_type TEXT,              -- manual, motion, scheduled, etc.
                    is_archived BOOLEAN DEFAULT 0,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
                )
            """)
            
            # Tabla de grabaciones
            # APIs FALTANTES:
            # - GET /recordings - Listar grabaciones
            # - POST /cameras/{id}/recordings/start - Iniciar grabación
            # - POST /cameras/{id}/recordings/stop - Detener grabación
            # - GET /recordings/{id} - Obtener info de grabación
            # - DELETE /recordings/{id} - Eliminar grabación
            # - GET /recordings/{id}/download - Descargar grabación
            # - GET /recordings/{id}/stream - Stream de grabación
            cursor.execute("""
                CREATE TABLE recordings (
                    recording_id TEXT PRIMARY KEY,  -- UUID
                    camera_id TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
                    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0),
                    format TEXT CHECK (format IN ('MP4', 'AVI', 'MKV', 'MOV')),
                    codec TEXT,
                    resolution TEXT,
                    framerate INTEGER,
                    bitrate INTEGER,
                    has_audio BOOLEAN DEFAULT 0,
                    trigger_type TEXT,
                    is_archived BOOLEAN DEFAULT 0,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    CHECK (end_time > start_time)
                )
            """)
            
            # ================== TABLAS DE CONFIGURACIÓN ==================
            
            # Tabla de configuración global
            cursor.execute("""
                CREATE TABLE system_config (
                    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'float', 'boolean', 'json')),
                    is_encrypted BOOLEAN DEFAULT 0,
                    is_user_configurable BOOLEAN DEFAULT 1,
                    default_value TEXT,
                    description TEXT,
                    validation_rules JSON,          -- Reglas de validación
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    UNIQUE(category, setting_key)
                )
            """)
            
            # Tabla de plantillas de configuración
            # APIs FALTANTES:
            # - GET /templates - Listar plantillas
            # - POST /templates - Crear plantilla
            # - GET /templates/{id} - Obtener plantilla
            # - PUT /templates/{id} - Actualizar plantilla
            # - DELETE /templates/{id} - Eliminar plantilla
            # - POST /templates/{id}/apply - Aplicar plantilla a cámara
            cursor.execute("""
                CREATE TABLE config_templates (
                    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL UNIQUE,
                    template_type TEXT NOT NULL,    -- camera_brand, protocol, etc.
                    brand TEXT,
                    model_pattern TEXT,             -- Patrón regex para matching de modelos
                    configuration JSON NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT
                )
            """)
            
            # ================== ÍNDICES PARA OPTIMIZACIÓN ==================
            
            logger.info("Creando índices...")
            
            # Índices para cameras
            cursor.execute("CREATE INDEX idx_cameras_ip ON cameras(ip_address)")
            cursor.execute("CREATE INDEX idx_cameras_brand ON cameras(brand)")
            cursor.execute("CREATE INDEX idx_cameras_active ON cameras(is_active)")
            cursor.execute("CREATE INDEX idx_cameras_code ON cameras(code)")
            cursor.execute("CREATE INDEX idx_cameras_location ON cameras(location)")
            
            # Índices para credentials
            cursor.execute("CREATE INDEX idx_credentials_camera ON camera_credentials(camera_id)")
            cursor.execute("CREATE INDEX idx_credentials_default ON camera_credentials(camera_id, is_default)")
            
            # Índices para protocols
            cursor.execute("CREATE INDEX idx_protocols_camera ON camera_protocols(camera_id)")
            cursor.execute("CREATE INDEX idx_protocols_type ON camera_protocols(protocol_type)")
            cursor.execute("CREATE INDEX idx_protocols_primary ON camera_protocols(camera_id, is_primary)")
            
            # Índices para endpoints
            cursor.execute("CREATE INDEX idx_endpoints_camera ON camera_endpoints(camera_id)")
            cursor.execute("CREATE INDEX idx_endpoints_type ON camera_endpoints(endpoint_type)")
            cursor.execute("CREATE INDEX idx_endpoints_verified ON camera_endpoints(is_verified)")
            cursor.execute("CREATE INDEX idx_endpoints_active ON camera_endpoints(camera_id, is_active)")
            
            # Índices para statistics
            cursor.execute("CREATE INDEX idx_stats_camera ON camera_statistics(camera_id)")
            cursor.execute("CREATE INDEX idx_stats_last_connection ON camera_statistics(last_connection_at)")
            
            # Índices para logs
            cursor.execute("CREATE INDEX idx_logs_camera ON connection_logs(camera_id)")
            cursor.execute("CREATE INDEX idx_logs_session ON connection_logs(session_id)")
            cursor.execute("CREATE INDEX idx_logs_time ON connection_logs(started_at)")
            cursor.execute("CREATE INDEX idx_logs_status ON connection_logs(status)")
            
            # Índices para events
            cursor.execute("CREATE INDEX idx_events_camera ON camera_events(camera_id)")
            cursor.execute("CREATE INDEX idx_events_type ON camera_events(event_type)")
            cursor.execute("CREATE INDEX idx_events_time ON camera_events(occurred_at)")
            cursor.execute("CREATE INDEX idx_events_severity ON camera_events(event_severity)")
            
            # Índices para scans
            cursor.execute("CREATE INDEX idx_scans_time ON network_scans(start_time)")
            cursor.execute("CREATE INDEX idx_scans_status ON network_scans(status)")
            cursor.execute("CREATE INDEX idx_scan_results_scan ON scan_results(scan_id)")
            cursor.execute("CREATE INDEX idx_scan_results_ip ON scan_results(ip_address)")
            cursor.execute("CREATE INDEX idx_scan_results_camera ON scan_results(is_camera)")
            
            # Índices para snapshots
            cursor.execute("CREATE INDEX idx_snapshots_camera ON snapshots(camera_id)")
            cursor.execute("CREATE INDEX idx_snapshots_time ON snapshots(capture_time)")
            
            # Índices para recordings
            cursor.execute("CREATE INDEX idx_recordings_camera ON recordings(camera_id)")
            cursor.execute("CREATE INDEX idx_recordings_time ON recordings(start_time)")
            
            # ================== TRIGGERS PARA INTEGRIDAD ==================
            
            logger.info("Creando triggers...")
            
            # Trigger para actualizar updated_at automáticamente
            tables_with_updated_at = [
                'cameras', 'camera_credentials', 'camera_protocols', 
                'camera_endpoints', 'stream_profiles', 'camera_statistics',
                'system_config', 'config_templates'
            ]
            
            for table in tables_with_updated_at:
                cursor.execute(f"""
                    CREATE TRIGGER update_{table}_timestamp 
                    AFTER UPDATE ON {table}
                    BEGIN
                        UPDATE {table} 
                        SET updated_at = CURRENT_TIMESTAMP 
                        WHERE rowid = NEW.rowid;
                    END
                """)
            
            # Trigger para validar que solo hay un protocolo primario por cámara
            cursor.execute("""
                CREATE TRIGGER enforce_single_primary_protocol
                BEFORE INSERT ON camera_protocols
                WHEN NEW.is_primary = 1
                BEGIN
                    UPDATE camera_protocols 
                    SET is_primary = 0 
                    WHERE camera_id = NEW.camera_id AND is_primary = 1;
                END
            """)
            
            # Trigger para crear estadísticas cuando se crea una cámara
            cursor.execute("""
                CREATE TRIGGER create_camera_statistics
                AFTER INSERT ON cameras
                BEGIN
                    INSERT INTO camera_statistics (camera_id)
                    VALUES (NEW.camera_id);
                END
            """)
            
            # Trigger para validar que solo hay una credencial por defecto por cámara
            cursor.execute("""
                CREATE TRIGGER enforce_single_default_credential
                BEFORE INSERT ON camera_credentials
                WHEN NEW.is_default = 1
                BEGIN
                    UPDATE camera_credentials 
                    SET is_default = 0 
                    WHERE camera_id = NEW.camera_id AND is_default = 1;
                END
            """)
            
            # ================== VISTAS ÚTILES ==================
            
            logger.info("Creando vistas...")
            
            # Vista de cámaras con información completa
            cursor.execute("""
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
            """)
            
            # Vista de endpoints verificados
            cursor.execute("""
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
            """)
            
            # ================== DATOS INICIALES ==================
            
            logger.info("Insertando datos iniciales...")
            
            # Configuraciones por defecto del sistema
            default_configs = [
                ('general', 'app_name', 'Universal Camera Viewer', 'string', 0, 'Nombre de la aplicación'),
                ('general', 'version', '0.9.1', 'string', 0, 'Versión de la aplicación'),
                ('general', 'theme', 'light', 'string', 1, 'Tema de la interfaz'),
                ('network', 'default_timeout', '10', 'integer', 1, 'Timeout por defecto en segundos'),
                ('network', 'max_retries', '3', 'integer', 1, 'Máximo de reintentos de conexión'),
                ('streaming', 'default_fps', '15', 'integer', 1, 'FPS por defecto para streaming'),
                ('streaming', 'buffer_size', '1048576', 'integer', 1, 'Tamaño del buffer en bytes'),
                ('storage', 'snapshot_retention_days', '30', 'integer', 1, 'Días de retención de snapshots'),
                ('storage', 'max_snapshot_size_mb', '10', 'integer', 1, 'Tamaño máximo de snapshot en MB'),
                ('security', 'encryption_algorithm', 'AES256', 'string', 0, 'Algoritmo de encriptación'),
                ('security', 'session_timeout_minutes', '30', 'integer', 1, 'Timeout de sesión en minutos')
            ]
            
            cursor.executemany("""
                INSERT INTO system_config (category, setting_key, setting_value, setting_type, is_user_configurable, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, default_configs)
            
            # Plantillas de configuración por marca
            templates = [
                ('Dahua Default', 'camera_brand', 'dahua', None, {
                    'protocols': [
                        {'type': 'ONVIF', 'port': 80},
                        {'type': 'RTSP', 'port': 554}
                    ],
                    'endpoints': {
                        'rtsp_main': 'rtsp://{ip}:{port}/cam/realmonitor?channel=1&subtype=0',
                        'rtsp_sub': 'rtsp://{ip}:{port}/cam/realmonitor?channel=1&subtype=1',
                        'snapshot': 'http://{ip}/cgi-bin/snapshot.cgi'
                    }
                }),
                ('Hikvision Default', 'camera_brand', 'hikvision', None, {
                    'protocols': [
                        {'type': 'ONVIF', 'port': 80},
                        {'type': 'RTSP', 'port': 554}
                    ],
                    'endpoints': {
                        'rtsp_main': 'rtsp://{ip}:{port}/Streaming/Channels/101',
                        'rtsp_sub': 'rtsp://{ip}:{port}/Streaming/Channels/102',
                        'snapshot': 'http://{ip}/ISAPI/Streaming/channels/101/picture'
                    }
                }),
                ('TP-Link Default', 'camera_brand', 'tplink', None, {
                    'protocols': [
                        {'type': 'ONVIF', 'port': 2020},
                        {'type': 'RTSP', 'port': 554}
                    ],
                    'endpoints': {
                        'rtsp_main': 'rtsp://{ip}:{port}/stream1',
                        'rtsp_sub': 'rtsp://{ip}:{port}/stream2',
                        'snapshot': 'http://{ip}/cgi-bin/snapshot.cgi'
                    }
                })
            ]
            
            for name, ttype, brand, pattern, config in templates:
                cursor.execute("""
                    INSERT INTO config_templates (template_name, template_type, brand, model_pattern, configuration)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, ttype, brand, pattern, json.dumps(config)))
            
            # Confirmar cambios
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Base de datos creada exitosamente en: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando base de datos: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_database(self) -> bool:
        """
        Verifica que la base de datos se creó correctamente.
        
        Returns:
            bool: True si la verificación es exitosa
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Verificar que existen las tablas principales
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = [
                'cameras', 'camera_credentials', 'camera_protocols',
                'camera_endpoints', 'camera_capabilities', 'stream_profiles',
                'camera_statistics', 'connection_logs', 'camera_events',
                'network_scans', 'scan_results', 'snapshots', 'recordings',
                'system_config', 'config_templates'
            ]
            
            missing = set(required_tables) - set(tables)
            if missing:
                logger.error(f"Tablas faltantes: {missing}")
                return False
            
            logger.info(f"✅ Verificación exitosa: {len(tables)} tablas encontradas")
            
            # Verificar integridad de claves foráneas
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            if fk_errors:
                logger.error(f"Errores de claves foráneas: {fk_errors}")
                return False
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error verificando base de datos: {e}")
            return False


def main():
    """Función principal para ejecutar el script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crear base de datos para Universal Camera Viewer')
    parser.add_argument('--path', default='data/camera_data.db', help='Ruta de la base de datos')
    parser.add_argument('--force', action='store_true', help='Forzar recreación sin confirmar')
    
    args = parser.parse_args()
    
    creator = DatabaseCreator(args.path)
    
    # Verificar si existe y pedir confirmación
    if Path(args.path).exists() and not args.force:
        response = input(f"⚠️  La base de datos {args.path} existe. ¿Eliminar y recrear? (s/n): ")
        if response.lower() != 's':
            print("Operación cancelada")
            return
    
    # Crear base de datos
    if creator.create_database():
        # Verificar creación
        if creator.verify_database():
            print("✅ Base de datos creada y verificada exitosamente")
        else:
            print("❌ La base de datos se creó pero falló la verificación")
            sys.exit(1)
    else:
        print("❌ Error al crear la base de datos")
        sys.exit(1)


if __name__ == "__main__":
    main()