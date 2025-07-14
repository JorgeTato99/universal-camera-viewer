# 📡 API y Servicios

## 📋 Servicios Internos

El sistema implementa **5 servicios principales** que forman la capa de negocio:

| Servicio | Responsabilidad | Estado | Archivos |
|----------|-----------------|--------|----------|
| **ProtocolService** | Gestión de protocolos de cámara | ✅ 100% | `protocol_service.py` |
| **ScanService** | Escaneo de red y descubrimiento | ✅ 100% | `scan_service.py` |
| **ConnectionService** | Gestión de conexiones activas | ✅ 100% | `connection_service.py` |
| **ConfigService** | Configuración y settings | ✅ 100% | `config_service.py` |
| **DataService** | Persistencia y base de datos | ✅ 100% | `data_service.py` |

## 🔧 Protocol Service

### **Clase Principal**

```python
# src/services/protocol_service.py
class ProtocolService:
    """Gestión unificada de protocolos de cámara"""
    
    def __init__(self):
        self.onvif_handler = ONVIFHandler()
        self.rtsp_handler = RTSPHandler() 
        self.http_cgi_handler = HTTPCGIHandler()
        
    async def detect_camera_protocol(self, ip: str, brand: str) -> dict:
        """Auto-detecta el mejor protocolo para una cámara"""
        
    async def connect_camera(self, ip: str, protocol: str, credentials: dict) -> bool:
        """Establece conexión usando el protocolo especificado"""
        
    async def get_stream_url(self, ip: str, protocol: str) -> str:
        """Obtiene URL del stream de video"""
        
    async def capture_snapshot(self, ip: str, protocol: str) -> bytes:
        """Captura imagen estática"""
```

### **Métodos de API**

#### **detect_camera_protocol(ip, brand)**

```python
# Entrada
{
    "ip": "192.168.1.100",
    "brand": "dahua"
}

# Salida
{
    "primary_protocol": "onvif",
    "secondary_protocol": "http_cgi",
    "available_ports": [80, 554, 8080],
    "supported_formats": ["h264", "mjpeg"],
    "confidence_score": 0.95
}
```

#### **connect_camera(ip, protocol, credentials)**

```python
# Entrada
{
    "ip": "192.168.1.100",
    "protocol": "onvif",
    "credentials": {
        "username": "admin",
        "password": "password123"
    }
}

# Salida
{
    "success": true,
    "stream_url": "rtsp://192.168.1.100:554/stream1",
    "device_info": {
        "model": "IPC-HFW2831S-S-S2",
        "firmware": "V2.800.0000000.0.R",
        "resolution": "1920x1080"
    }
}
```

## 🌐 Scan Service

### **Clase Principal**

```python
# src/services/scan_service.py
class ScanService:
    """Escaneo de red y descubrimiento de cámaras"""
    
    def __init__(self):
        self.scan_results = []
        self.active_scans = {}
        
    async def scan_network_range(self, network: str, scan_type: str = "fast") -> list:
        """Escanea un rango de red buscando cámaras"""
        
    async def scan_single_ip(self, ip: str) -> dict:
        """Escanea una IP específica"""
        
    async def get_scan_progress(self, scan_id: str) -> dict:
        """Obtiene progreso de escaneo activo"""
        
    def get_discovered_cameras(self) -> list:
        """Retorna lista de cámaras descubiertas"""
```

### **Métodos de API**

#### **scan_network_range(network, scan_type)**

```python
# Entrada
{
    "network": "192.168.1.0/24",
    "scan_type": "comprehensive"  # fast, normal, comprehensive
}

# Salida
{
    "scan_id": "scan_20241210_143022",
    "total_ips": 254,
    "estimated_time": "120s",
    "scan_status": "in_progress"
}
```

#### **get_discovered_cameras()**

```python
# Salida
[
    {
        "ip": "192.168.1.100",
        "brand": "dahua",
        "model": "IPC-HFW2831S",
        "protocols": ["onvif", "http_cgi"],
        "ports_open": [80, 554],
        "response_time": 45,
        "confidence": 0.92
    },
    {
        "ip": "192.168.1.101", 
        "brand": "tplink",
        "model": "VIGI C300",
        "protocols": ["onvif", "rtsp"],
        "ports_open": [554, 8080],
        "response_time": 67,
        "confidence": 0.88
    }
]
```

## 🔗 Connection Service

### **Clase Principal**

```python
# src/services/connection_service.py
class ConnectionService:
    """Gestión de conexiones activas a cámaras"""
    
    def __init__(self):
        self.active_connections = {}
        self.connection_pool = {}
        self.max_connections = 10
        
    async def establish_connection(self, camera_config: dict) -> str:
        """Establece nueva conexión a cámara"""
        
    async def close_connection(self, connection_id: str) -> bool:
        """Cierra conexión específica"""
        
    async def get_stream_frame(self, connection_id: str) -> bytes:
        """Obtiene frame actual del stream"""
        
    def get_connection_status(self, connection_id: str) -> dict:
        """Estado de conexión específica"""
        
    def get_all_connections(self) -> list:
        """Lista todas las conexiones activas"""
```

### **Métodos de API**

#### **establish_connection(camera_config)**

```python
# Entrada
{
    "ip": "192.168.1.100",
    "brand": "dahua",
    "protocol": "onvif",
    "credentials": {
        "username": "admin",
        "password": "password123"
    },
    "stream_quality": "high"  # low, medium, high
}

# Salida
{
    "connection_id": "conn_dahua_192_168_1_100",
    "status": "connected",
    "stream_url": "rtsp://192.168.1.100:554/stream1",
    "fps": 25,
    "resolution": "1920x1080",
    "bandwidth_kbps": 2048
}
```

#### **get_all_connections()**

```python
# Salida
[
    {
        "connection_id": "conn_dahua_192_168_1_100",
        "ip": "192.168.1.100", 
        "brand": "dahua",
        "status": "connected",
        "uptime_seconds": 3600,
        "frames_received": 90000,
        "last_frame_time": "2024-12-10T14:30:22Z"
    },
    {
        "connection_id": "conn_tplink_192_168_1_101",
        "ip": "192.168.1.101",
        "brand": "tplink", 
        "status": "reconnecting",
        "uptime_seconds": 1800,
        "frames_received": 45000,
        "last_frame_time": "2024-12-10T14:29:58Z"
    }
]
```

## ⚙️ Config Service

### **Clase Principal**

```python
# src/services/config_service.py
class ConfigService:
    """Gestión de configuración y settings"""
    
    def __init__(self):
        self.config_file = "config/app_config.json"
        self.profiles_file = "config/profiles.json"
        self.current_config = {}
        
    def load_config(self) -> dict:
        """Carga configuración desde archivo"""
        
    def save_config(self, config: dict) -> bool:
        """Guarda configuración a archivo"""
        
    def get_camera_profile(self, brand: str) -> dict:
        """Obtiene perfil de configuración por marca"""
        
    def create_backup(self) -> str:
        """Crea backup de configuración actual"""
        
    def restore_backup(self, backup_id: str) -> bool:
        """Restaura configuración desde backup"""
```

### **Configuración por Defecto**

```json
// config/app_config.json
{
    "app": {
        "version": "0.7.0",
        "debug_mode": false,
        "auto_scan_on_start": true,
        "max_concurrent_cameras": 8,
        "default_scan_range": "192.168.1.0/24"
    },
    "ui": {
        "theme": "auto",
        "language": "es",
        "window_size": [1200, 800],
        "enable_animations": true,
        "show_performance_stats": false
    },
    "camera": {
        "connection_timeout": 10,
        "retry_attempts": 3,
        "default_stream_quality": "medium",
        "enable_motion_detection": false,
        "snapshot_format": "jpg"
    },
    "network": {
        "scan_timeout": 5,
        "ping_timeout": 2,
        "max_scan_threads": 50,
        "discovery_protocols": ["onvif", "rtsp", "http_cgi"]
    }
}
```

## 💾 Data Service

### **Clase Principal**

```python
# src/services/data_service.py
class DataService:
    """Persistencia y gestión de datos"""
    
    def __init__(self):
        self.db_path = "data/camera_data.db"
        self.analytics_db = "data/analytics.db"
        
    async def save_discovered_camera(self, camera_data: dict) -> bool:
        """Guarda cámara descubierta en BD"""
        
    async def get_saved_cameras(self) -> list:
        """Obtiene cámaras guardadas"""
        
    async def log_connection_attempt(self, ip: str, success: bool, protocol: str) -> bool:
        """Log de intento de conexión para analytics"""
        
    async def get_connection_history(self, ip: str) -> list:
        """Historial de conexiones de una cámara"""
        
    async def export_data(self, format: str = "json") -> str:
        """Exporta datos a archivo"""
```

### **Schema de Base de Datos**

```sql
-- data/camera_data.db
CREATE TABLE cameras (
    id INTEGER PRIMARY KEY,
    ip TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    model TEXT,
    protocols TEXT,  -- JSON array
    last_seen TIMESTAMP,
    connection_quality REAL,
    notes TEXT
);

CREATE TABLE connections (
    id INTEGER PRIMARY KEY,
    camera_ip TEXT,
    protocol TEXT,
    success BOOLEAN,
    timestamp TIMESTAMP,
    error_message TEXT,
    response_time_ms INTEGER
);

CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY,
    scan_id TEXT,
    network_range TEXT,
    total_found INTEGER,
    scan_duration_seconds INTEGER,
    timestamp TIMESTAMP
);
```

## 📊 Analytics y Métricas

### **Sistema de Métricas**

```python
# src/utils/analytics.py
class AnalyticsService:
    """Análisis y métricas del sistema"""
    
    def __init__(self):
        self.duckdb_conn = duckdb.connect('data/analytics.db')
        
    def log_camera_discovery(self, ip: str, brand: str, protocols: list):
        """Log de descubrimiento de cámara"""
        
    def generate_usage_report(self, days: int = 30) -> dict:
        """Genera reporte de uso"""
        
    def get_protocol_success_rates(self) -> dict:
        """Tasa de éxito por protocolo"""
        
    def get_brand_statistics(self) -> dict:
        """Estadísticas por marca de cámara"""
```

### **Métricas Disponibles**

```python
# Ejemplo de métricas
{
    "discovery_stats": {
        "total_cameras_found": 156,
        "unique_brands": 4,
        "avg_discovery_time": 8.5,
        "success_rate": 0.94
    },
    "protocol_stats": {
        "onvif": {"attempts": 120, "success": 115, "rate": 0.96},
        "rtsp": {"attempts": 89, "success": 82, "rate": 0.92},
        "http_cgi": {"attempts": 45, "success": 41, "rate": 0.91}
    },
    "brand_stats": {
        "dahua": {"count": 45, "avg_response": 67},
        "tplink": {"count": 38, "avg_response": 89},
        "steren": {"count": 32, "avg_response": 112},
        "generic": {"count": 41, "avg_response": 95}
    }
}
```

## 🔌 Eventos y Callbacks

### **Sistema de Eventos**

```python
# src/utils/events.py
class EventManager:
    """Gestión de eventos del sistema"""
    
    def __init__(self):
        self.listeners = {}
        
    def subscribe(self, event_type: str, callback: callable):
        """Suscribirse a evento"""
        
    def emit(self, event_type: str, data: dict):
        """Emitir evento"""
        
    def unsubscribe(self, event_type: str, callback: callable):
        """Desuscribirse de evento"""
```

### **Eventos Disponibles**

```python
# Eventos del sistema
EVENTS = {
    'camera_discovered': 'Nueva cámara encontrada',
    'camera_connected': 'Cámara conectada exitosamente', 
    'camera_disconnected': 'Cámara desconectada',
    'scan_started': 'Escaneo de red iniciado',
    'scan_completed': 'Escaneo de red completado',
    'connection_failed': 'Falló conexión a cámara',
    'stream_started': 'Stream de video iniciado',
    'stream_stopped': 'Stream de video detenido'
}
```

## 🎯 Próximos Pasos

1. **[📦 Instalación](installation.md)** - Setup inicial del proyecto
2. **[💻 Desarrollo](development.md)** - Configurar entorno de desarrollo
3. **[🌐 Protocolos](camera-protocols.md)** - Entender protocolos de cámara

---

**📡 Servicios:** 5 servicios principales con APIs bien definidas  
**💾 Persistencia:** SQLite + DuckDB para datos y analytics  
**📊 Métricas:** Sistema completo de analytics y reporting

---

### 📚 Navegación

[← Anterior: Protocolos de Cámara](camera-protocols.md) | [📑 Índice](README.md) | [Siguiente: Deployment y Distribución →](deployment.md)
