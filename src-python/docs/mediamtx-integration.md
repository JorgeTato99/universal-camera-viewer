# Plan de Integración con MediaMTX

## Objetivo

Universal Camera Viewer es una herramienta de exploración y gateway de emisión. La meta principal es emitir streams de cámaras IP descubiertas hacia un servidor MediaMTX central.

## Arquitectura: RTSP Relay con FFmpeg

- **Sin transcodificación**: `-c copy` preserva el stream original
- **Aislamiento**: Un proceso FFmpeg por cámara  
- **Recuperación**: Reinicio automático con backoff exponencial

## Estado de Implementación

### ✅ Completado

1. **Modelos de dominio** (`models/publishing/`)
   - PublisherProcess, PublishStatus, PublishErrorType
   - Validación y métricas integradas

2. **FFmpeg Manager** (`services/publishing/ffmpeg_manager.py`)
   - Verificación de disponibilidad con detección de versión
   - Parser de métricas mejorado (FPS, bitrate, speed)
   - Detección inteligente de errores con mensajes amigables

3. **RTSPPublisherService** (`services/publishing/rtsp_publisher_service.py`)
   - Gestión completa del ciclo de vida de procesos
   - Logging detallado por niveles (DEBUG, INFO, WARNING, ERROR)
   - Manejo robusto de excepciones con tipos específicos
   - Reconexión automática con límite configurable

4. **MediaMTXClient** (`services/publishing/mediamtx_client.py`)
   - Cliente HTTP asíncrono con reintentos
   - Health checks y verificación de paths
   - Manejo de sesiones con cleanup automático
   - Timeout configurable y validación de entradas

5. **PublishingPresenter** (`presenters/publishing_presenter.py`)
   - Coordinación MVP completa
   - Validación de business logic
   - Emisión de eventos para WebSocket
   - Manejo de errores con tipos específicos

6. **API REST** (`api/routers/publishing.py`)
   - Endpoints documentados con OpenAPI
   - Códigos HTTP apropiados (201, 404, 409, 500)
   - Logging detallado de operaciones
   - Respuestas estructuradas con detalles de error

### ✅ Mejoras Implementadas

- **Arquitectura SOLID**: Separación clara de responsabilidades
- **Clean Code**: Métodos pequeños, nombres descriptivos, DRY
- **Logging Mejorado**: Niveles apropiados (DEBUG para detalles, INFO para operaciones, WARNING para problemas, ERROR para fallos)
- **Excepciones Tipadas**: PublishErrorType con categorías específicas
- **Documentación Completa**: Docstrings detallados con Args, Returns, Raises

### ✅ Implementaciones Adicionales Completadas

7. **WebSocket Handler** (`websocket/handlers/publishing_handler.py`)
   - Handler completo para eventos en tiempo real
   - Suscripciones por cámara para broadcasts dirigidos
   - Loop de actualización de métricas cada 2 segundos
   - Comandos: subscribe_camera, start_publishing, stop_publishing, get_status
   - Integración con PublishingPresenter para emisión de eventos

8. **Configuración desde Base de Datos** (`services/database/publishing_db_service.py`)
   - Servicio completo de persistencia con SQLite
   - Tablas: publishing_configurations, publishing_states, publishing_history, publishing_metrics
   - CRUD de configuraciones MediaMTX
   - Seguimiento de estados activos y métricas
   - Historial completo de sesiones de publicación

9. **API de Configuración** (`api/routers/publishing_config.py`)
   - Endpoints REST para gestión de configuraciones
   - CRUD completo: crear, leer, actualizar, eliminar
   - Activación de configuraciones con `/activate`
   - Validación de configuraciones en uso antes de eliminar

### ⏳ Pendiente

1. **UI React**
   - Componentes para control de publicación
   - Visualización de métricas en tiempo real
   - Integración con WebSocket para eventos

2. **Tests**
   - Unit tests para servicios
   - Integration tests con MediaMTX mock
   - Tests de rendimiento con múltiples cámaras

## Uso de la API

```bash
# Iniciar publicación
POST /api/publishing/start
{
  "camera_id": "cam-001",
  "force_restart": false
}

# Respuesta exitosa (201 Created)
{
  "camera_id": "cam-001",
  "status": "publishing",
  "publish_path": "camera_cam-001",
  "uptime_seconds": 0,
  "error_count": 0,
  "metrics": {}
}

# Detener publicación
POST /api/publishing/stop
{
  "camera_id": "cam-001"
}

# Ver estado de todas las publicaciones
GET /api/publishing/status

# Ver estado específico
GET /api/publishing/status/cam-001
```

## Configuración Recomendada

```python
config = PublishConfiguration(
    mediamtx_url="rtsp://localhost:8554",
    max_reconnects=3,
    reconnect_delay=5.0,
    use_tcp=True,
    api_enabled=True,
    api_url="http://localhost:9997"
)
```

## Notas de Implementación

- Los procesos FFmpeg usan `-c copy` para máxima eficiencia
- Cada cámara tiene su propio proceso aislado
- Los errores se categorizan para mejor debugging
- Las métricas se actualizan en tiempo real desde FFmpeg
- La reconexión usa backoff exponencial hasta max_reconnects

