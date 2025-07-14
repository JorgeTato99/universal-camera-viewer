# 🏗️ Arquitectura Técnica

## Arquitectura MVP (Model-View-Presenter)

El proyecto implementa una arquitectura MVP estricta con las siguientes capas:

### Model Layer (100% Completo)
```
src-python/models/
├── camera_model.py      # Entidad de cámara
├── connection_model.py  # Estado de conexión
├── scan_model.py        # Resultados de escaneo
└── streaming/
    ├── stream_model.py  # Estado del stream
    └── frame_model.py   # Datos del frame
```

### View Layer (✅ React Funcional)
- **Legacy**: `src-python/views/` - Flet UI (referencia)
- **Actual**: `src/` - React + TypeScript + Material-UI
  - VideoPlayer con streaming WebSocket funcional
  - CameraCard con métricas en tiempo real
  - Grid responsivo de cámaras

### Presenter Layer (✅ Streaming Funcional)
```
src-python/presenters/
├── camera_presenter.py     # Gestión de cámaras
├── streaming/
│   └── video_stream_presenter.py  # ✅ Streaming WebSocket funcional
└── [pendientes...]         # 70% por implementar
```

**WebSocket Streaming Implementado**:
- StreamHandler para conexiones WebSocket
- Integración con VideoStreamPresenter
- Transmisión de frames base64 JPEG
- Heartbeat y reconexiones automáticas

### Service Layer (✅ 100% Completo)
```
src-python/services/
├── connection_service.py   # Gestión de conexiones
├── protocol_service.py     # Protocolos ONVIF/RTSP
├── scan_service.py         # Descubrimiento de red
├── config_service.py       # Configuración
└── video/
    ├── video_stream_service.py  # Singleton para streaming
    ├── rtsp_stream_manager.py   # ✅ RTSP con OpenCV funcional
    └── stream_manager.py        # Gestión de streams
```

## Patrones de Diseño Implementados

### Singleton Pattern
```python
class VideoStreamService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Factory Pattern
```python
class StreamManagerFactory:
    @staticmethod
    def create_manager(protocol: StreamProtocol) -> StreamManager:
        if protocol == StreamProtocol.RTSP:
            return RTSPStreamManager()
        elif protocol == StreamProtocol.ONVIF:
            return ONVIFStreamManager()
```

### Strategy Pattern
```python
class FrameConverter:
    def __init__(self, strategy: ConversionStrategy):
        self._strategy = strategy
    
    def convert(self, frame: np.ndarray) -> str:
        return self._strategy.convert(frame)
```

### Template Method Pattern
```python
class StreamManager(ABC):
    def start_stream(self):
        self._initialize()      # Hook
        self._connect()         # Abstract
        self._configure()       # Hook
        self._begin_capture()   # Template
```

## Comunicación Frontend-Backend

### Arquitectura WebSocket (FastAPI) ✅ FUNCIONAL
```
┌─────────────────┐     WebSocket      ┌────────────────┐
│  React Frontend │ ←───────────────→  │ FastAPI Backend │
│   VideoPlayer   │     ws://8000      │  StreamHandler  │
└─────────────────┘                    └────────────────┘
        ↓                                       ↓
   Base64 JPEG                             OpenCV RTSP
   @ 13-15 FPS                            Capture Thread
```

### Flujo de Streaming en Tiempo Real
1. **Conexión**: React establece WebSocket con `/ws/stream/{camera_id}`
2. **Autenticación**: Backend valida cámara y credenciales
3. **RTSP Stream**: OpenCV captura frames de la cámara
4. **Encoding**: Frames BGR → JPEG → Base64
5. **Transmisión**: WebSocket envía frames a 13-15 FPS
6. **Renderizado**: React muestra frames en `<img>` tag

### Protocolo WebSocket Implementado
```typescript
// Frontend → Backend
{
  "action": "start_stream",
  "params": {
    "quality": "medium",
    "fps": 30,
    "format": "jpeg"
  }
}

// Backend → Frontend (cada frame)
{
  "type": "frame",
  "camera_id": "cam_192.168.1.172",
  "data": "base64_jpeg_string",
  "timestamp": "2025-01-14T18:00:00.123Z",
  "frame_number": 1234,
  "metrics": {
    "fps": 15,
    "frameCount": 1234
  }
}

// Heartbeat (cada 30s)
Frontend: { "type": "ping" }
Backend: { "type": "pong" }
```

### Arquitectura Tauri (Opcional)
```
React Frontend <-> Tauri Core <-> Python Sidecar
     JSON            IPC           stdin/stdout
```

## Protocolos de Cámara

### ONVIF Implementation
```python
# Descubrimiento WS-Discovery
# Autenticación WS-UsernameToken
# Servicios: Media, Device, PTZ
# Perfiles dinámicos por cámara
```

### RTSP Implementation
```python
# URLs patterns (16+ soportados)
# Autenticación Basic/Digest
# Decodificación con OpenCV
# Reconnect automático
```

### Configuración por Marca
```python
BRAND_CONFIGS = {
    'dahua': {
        'onvif_port': 80,
        'rtsp_port': 554,
        'auth': 'digest'
    },
    'tplink': {
        'onvif_port': 2020,
        'rtsp_port': 554,
        'auth': 'basic'
    },
    'steren': {
        'onvif_port': 8000,
        'rtsp_port': 5543,
        'dual_stream': True
    }
}
```

## Performance y Optimización

### Gestión de Memoria
- Pool de conexiones reutilizables
- Liberación automática de recursos OpenCV
- Garbage collection optimizado
- Límites de buffer configurables

### Threading y Async
- AsyncIO para todas las operaciones I/O
- ThreadPoolExecutor para decodificación
- Queues para comunicación inter-thread
- Backpressure handling

### Métricas de Performance
```python
# Target metrics
FPS: 15-30 (configurable)
Latencia: < 200ms
CPU: < 5% por cámara
RAM: < 50MB por stream
```

## Seguridad

### Gestión de Credenciales
- No hardcoded credentials
- Encriptación en .env (planeado)
- Sesiones con timeout
- Rate limiting en APIs

### Validación de Entrada
- IP address validation
- Port range checking
- Command injection prevention
- Path traversal protection

## Testing Strategy

### Unit Tests
- Models: 100% coverage target
- Services: 90% coverage target
- Presenters: 85% coverage target
- Utils: 95% coverage target

### Integration Tests
- Protocol handlers
- Database operations
- IPC communication
- End-to-end flows

### Performance Tests
- Load testing (4+ cámaras)
- Memory leak detection
- Network stress testing
- UI responsiveness

---

### 📚 Navegación

[← Anterior: Guía de Desarrollo](development.md) | [📑 Índice](README.md) | [Siguiente: Características Detalladas →](FEATURES.md)