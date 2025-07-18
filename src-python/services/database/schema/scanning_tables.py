"""
Tablas de escaneo de red.

Contiene las definiciones para funcionalidad de descubrimiento:
- network_scans: Registro de escaneos
- scan_results: Resultados de cada escaneo
"""

# Tabla de escaneos de red
NETWORK_SCANS_TABLE = """
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
"""

# Tabla de resultados de escaneo
SCAN_RESULTS_TABLE = """
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
"""


def get_scanning_tables():
    """Retorna lista de tuplas (nombre_tabla, sql_create)."""
    return [
        ('network_scans', NETWORK_SCANS_TABLE),
        ('scan_results', SCAN_RESULTS_TABLE)
    ]


def get_table_names():
    """Retorna solo los nombres de las tablas de escaneo."""
    return [name for name, _ in get_scanning_tables()]