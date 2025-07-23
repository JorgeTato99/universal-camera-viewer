# Integración con ELK Stack

Este documento describe cómo configurar y usar la integración de logs con ELK Stack (Elasticsearch, Logstash, Kibana) en Universal Camera Viewer.

## Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Configuración](#configuración)
4. [Uso](#uso)
5. [Formato de Logs](#formato-de-logs)
6. [Despliegue con Docker](#despliegue-con-docker)
7. [Dashboards de Kibana](#dashboards-de-kibana)
8. [Troubleshooting](#troubleshooting)

## Descripción General

La integración con ELK Stack permite:

- **Agregación centralizada** de todos los logs del sistema
- **Búsqueda y análisis** avanzado de logs
- **Visualización en tiempo real** de métricas y eventos
- **Alertas automáticas** basadas en patrones
- **Trazabilidad completa** con correlation IDs
- **Cumplimiento** con requisitos de auditoría

### Características Implementadas

✅ **Formateadores JSON estructurados** compatibles con ELK  
✅ **Handler basado en archivos** para Filebeat (producción)  
✅ **Handler directo a Elasticsearch** (desarrollo/testing)  
✅ **Contexto enriquecido** con metadata de cámaras  
✅ **Sanitización automática** de información sensible  
✅ **Separación por categorías** (app, audit, errors, metrics, streaming)  
✅ **Elastic Common Schema (ECS)** para estandarización  

## Arquitectura

### Flujo de Logs en Producción (Recomendado)

```text
┌─────────────────┐     ┌──────────┐     ┌─────────────┐     ┌────────┐
│   Aplicación    │────▶│  Archivos │────▶│  Filebeat   │────▶│Logstash│
│  (JSON Logs)    │     │   JSON    │     │ (Shipper)   │     │        │
└─────────────────┘     └──────────┘     └─────────────┘     └───┬────┘
                                                                   │
                                                                   ▼
                                                           ┌──────────────┐
                                 ┌────────┐               │Elasticsearch │
                                 │ Kibana │◀──────────────│   (Storage)  │
                                 └────────┘               └──────────────┘
```

### Flujo de Logs en Desarrollo

```text
┌─────────────────┐                        ┌──────────────┐
│   Aplicación    │───────────────────────▶│Elasticsearch │
│ (Direct Handler)│                        │   (Local)    │
└─────────────────┘                        └──────────────┘
```

## Configuración

### Variables de Entorno

```bash
# Habilitar integración con ELK
ELK_ENABLED=true

# Tipo de handler (file o elasticsearch)
ELK_HANDLER_TYPE=file  # Recomendado para producción

# Configuración para handler de archivos
ELK_BUFFER_SIZE=1000
ELK_FLUSH_INTERVAL=5.0

# Configuración para handler directo (desarrollo)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SSL=false
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme

# Habilitar logs JSON en consola
USE_JSON_LOGS=true

# Ambiente (afecta nivel de sanitización)
ENVIRONMENT=production
```

### Archivo .env Ejemplo

```bash
# Logging Configuration
ELK_ENABLED=true
ELK_HANDLER_TYPE=file
USE_JSON_LOGS=true
ENVIRONMENT=production

# ELK Buffer Settings
ELK_BUFFER_SIZE=2000
ELK_FLUSH_INTERVAL=10.0

# Elasticsearch (solo para desarrollo)
# ELASTICSEARCH_HOST=elastic.local
# ELASTICSEARCH_PORT=9200
# ELASTICSEARCH_SSL=true
# ELASTICSEARCH_USER=elastic
# ELASTICSEARCH_PASSWORD=secure_password
```

## Uso

### Activación Básica

1. **Configurar variables de entorno**:

   ```bash
   export ELK_ENABLED=true
   export USE_JSON_LOGS=true
   ```

2. **Iniciar la aplicación**:

   ```bash
   python src-python/api/main.py
   ```

3. **Verificar archivos de log JSON**:

   ```bash
   ls -la logs/elk/
   # ucv-app.json
   # ucv-audit.json
   # ucv-errors.json
   # ucv-metrics.json
   # ucv-streaming.json
   ```

### Uso del Logger Mejorado

```python
from utils.logging_integration import get_enhanced_logger

# Crear logger con capacidades de contexto
logger = get_enhanced_logger(__name__)

# Log simple con contexto automático
logger.info("Operación completada")

# Log con contexto de cámara
from utils.log_context import LogContext

with LogContext(camera={
    'id': 'cam_123',
    'ip': '192.168.1.100',
    'brand': 'Dahua'
}):
    logger.info("Conectando a cámara")
    # Todos los logs dentro del contexto incluirán la info de la cámara

# Eventos específicos de cámara
logger.camera_event(
    camera_id="cam_123",
    event="motion_detected",
    details={"zone": "entrance", "confidence": 0.95}
)

# Métricas de streaming
logger.stream_metric(
    stream_id="stream_456",
    metric_name="fps",
    value=29.5,
    tags={"quality": "HD", "codec": "H264"}
)
```

### Decoradores para Operaciones

```python
from utils.logging_integration import camera_operation, stream_operation

class CameraService:
    @camera_operation(
        camera_id="cam_123",
        camera_ip="192.168.1.100",
        brand="Dahua"
    )
    async def connect_camera(self, camera_id: str):
        # El contexto de cámara se agrega automáticamente
        # También genera correlation_id y mide tiempo de ejecución
        await self._establish_connection()
        
    @stream_operation(
        stream_id="stream_456",
        protocol="RTSP",
        camera_id="cam_123"
    )
    async def start_streaming(self, stream_id: str):
        # Contexto de streaming + correlation ID + timing
        await self._initialize_stream()
```

## Formato de Logs

### Estructura JSON Estándar

```json
{
  "@timestamp": "2024-01-23T10:30:45.123Z",
  "level": "INFO",
  "logger_name": "services.camera_service",
  "message": "Cámara conectada exitosamente",
  "module": "camera_service",
  "function": "connect_camera",
  "line_number": 125,
  "app": {
    "name": "Universal Camera Viewer",
    "version": "0.9.0",
    "environment": "production"
  },
  "host": {
    "name": "prod-server-01"
  },
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "camera": {
    "id": "cam_123",
    "ip": "192.168.1.100",
    "brand": "Dahua"
  },
  "extra": {
    "execution_time_ms": 250.5,
    "event_type": "camera_connection"
  }
}
```

### Elastic Common Schema (ECS)

Los logs también pueden usar ECS para mejor compatibilidad:

```json
{
  "@timestamp": "2024-01-23T10:30:45.123Z",
  "log": {
    "level": "info",
    "logger": "services.camera_service",
    "origin": {
      "file": {
        "name": "camera_service.py",
        "line": 125
      },
      "function": "connect_camera"
    }
  },
  "message": "Cámara conectada exitosamente",
  "service": {
    "name": "Universal Camera Viewer",
    "version": "0.9.0",
    "environment": "production"
  },
  "event": {
    "created": "2024-01-23T10:30:45.123Z",
    "kind": "event",
    "category": ["process"],
    "type": ["info"]
  },
  "camera": {
    "id": "cam_123",
    "ip": "192.168.1.xxx",
    "brand": "Dahua"
  }
}
```

## Despliegue con Docker

### docker-compose.yml para ELK Stack

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: ucv-elasticsearch
    environment:
      - node.name=elasticsearch
      - cluster.name=ucv-cluster
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - 9200:9200
    networks:
      - ucv-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: ucv-logstash
    volumes:
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    ports:
      - 5044:5044
      - 9600:9600
    environment:
      LS_JAVA_OPTS: "-Xmx256m -Xms256m"
    networks:
      - ucv-network
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: ucv-kibana
    ports:
      - 5601:5601
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
    networks:
      - ucv-network
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: ucv-filebeat
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/logs:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: filebeat -e -strict.perms=false
    networks:
      - ucv-network
    depends_on:
      - logstash

volumes:
  elasticsearch-data:
    driver: local

networks:
  ucv-network:
    driver: bridge
```

### Configuración de Filebeat

`filebeat/filebeat.yml`:

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /logs/elk/ucv-app.json
  fields:
    log_type: app
  json.keys_under_root: true
  json.add_error_key: true

- type: log
  enabled: true
  paths:
    - /logs/elk/ucv-audit.json
  fields:
    log_type: audit
  json.keys_under_root: true
  json.add_error_key: true

- type: log
  enabled: true
  paths:
    - /logs/elk/ucv-errors.json
  fields:
    log_type: error
  json.keys_under_root: true
  json.add_error_key: true

- type: log
  enabled: true
  paths:
    - /logs/elk/ucv-streaming.json
  fields:
    log_type: streaming
  json.keys_under_root: true
  json.add_error_key: true

output.logstash:
  hosts: ["logstash:5044"]

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

### Pipeline de Logstash

`logstash/pipeline/ucv-pipeline.conf`:

```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  # Parsear timestamp ISO8601
  date {
    match => [ "@timestamp", "ISO8601" ]
    target => "@timestamp"
  }

  # Agregar campos según tipo de log
  if [fields][log_type] == "streaming" {
    mutate {
      add_field => { "[@metadata][target_index]" => "ucv-streaming-%{+YYYY.MM.dd}" }
    }
  } else if [fields][log_type] == "audit" {
    mutate {
      add_field => { "[@metadata][target_index]" => "ucv-audit-%{+YYYY.MM.dd}" }
    }
  } else if [fields][log_type] == "error" {
    mutate {
      add_field => { "[@metadata][target_index]" => "ucv-errors-%{+YYYY.MM.dd}" }
    }
  } else {
    mutate {
      add_field => { "[@metadata][target_index]" => "ucv-app-%{+YYYY.MM.dd}" }
    }
  }

  # Enriquecer con GeoIP si hay IPs
  if [camera][ip] {
    geoip {
      source => "[camera][ip]"
      target => "[camera][geo]"
      tag_on_failure => ["_geoip_lookup_failure"]
    }
  }

  # Eliminar campos innecesarios
  mutate {
    remove_field => [ "[fields]", "[host][name]" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][target_index]}"
    template_name => "ucv"
    template => "/usr/share/logstash/templates/ucv-template.json"
    template_overwrite => true
  }
}
```

## Dashboards de Kibana

### Dashboard Principal - Camera Operations

Visualizaciones recomendadas:

1. **Métricas en Tiempo Real**
   - Total de cámaras activas
   - FPS promedio por cámara
   - Latencia de conexión
   - Errores por minuto

2. **Distribución de Eventos**
   - Gráfico de torta por tipo de evento
   - Timeline de eventos de cámara
   - Heatmap de actividad por hora

3. **Análisis de Errores**
   - Top 10 errores más comunes
   - Tendencia de errores por servicio
   - Correlation IDs de errores

4. **Auditoría**
   - Accesos por usuario
   - Operaciones sensibles
   - Timeline de eventos de seguridad

### Consultas Útiles de Kibana

```json
// Buscar todos los errores de una cámara específica
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "ERROR" } },
        { "term": { "camera.id": "cam_123" } }
      ]
    }
  }
}

// Encontrar operaciones lentas (>1000ms)
{
  "query": {
    "range": {
      "extra.execution_time_ms": {
        "gt": 1000
      }
    }
  }
}

// Rastrear por correlation ID
{
  "query": {
    "term": {
      "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  }
}
```

## Troubleshooting

### Los logs no aparecen en Elasticsearch

1. **Verificar que ELK esté habilitado**:

   ```bash
   echo $ELK_ENABLED  # Debe ser "true"
   ```

2. **Verificar archivos JSON**:

   ```bash
   tail -f logs/elk/ucv-app.json
   # Debe mostrar JSON válido
   ```

3. **Verificar Filebeat**:

   ```bash
   docker logs ucv-filebeat
   # Buscar errores de conexión
   ```

4. **Verificar índices en Elasticsearch**:

   ```bash
   curl http://localhost:9200/_cat/indices?v
   ```

### Logs sin contexto

1. **Usar el logger mejorado**:

   ```python
   # ❌ Logger estándar
   import logging
   logger = logging.getLogger(__name__)
   
   # ✅ Logger mejorado
   from utils.logging_integration import get_enhanced_logger
   logger = get_enhanced_logger(__name__)
   ```

2. **Establecer contexto correctamente**:

   ```python
   from utils.log_context import LogContext
   
   with LogContext(camera={'id': 'cam_123'}):
       # Logs aquí incluirán el contexto
       logger.info("Operación con contexto")
   ```

### Rendimiento degradado

1. **Ajustar buffer size**:

   ```bash
   export ELK_BUFFER_SIZE=5000  # Aumentar buffer
   export ELK_FLUSH_INTERVAL=30.0  # Flush menos frecuente
   ```

2. **Usar handler de archivos en producción**:

   ```bash
   export ELK_HANDLER_TYPE=file  # No "elasticsearch"
   ```

3. **Rotar logs antiguos**:

   ```python
   from services.logging_service import logging_service
   logging_service.cleanup_old_logs(days=7)
   ```

### Información sensible en logs

La sanitización está activada por defecto, pero verificar:

1. **Ambiente configurado correctamente**:

   ```bash
   export ENVIRONMENT=production  # Activa sanitización completa
   ```

2. **Revisar patrones de sanitización**:

   ```python
   # utils/sanitizers.py contiene los patrones
   # Agregar nuevos si es necesario
   ```

## Próximos Pasos

### TODO: Funcionalidades Pendientes

1. **Integración con OpenTelemetry** para trazas distribuidas
2. **Alertas automáticas** basadas en Watcher de Elasticsearch
3. **Machine Learning** para detección de anomalías
4. **Dashboards pre-configurados** exportables
5. **Métricas de negocio** específicas del dominio

### Mejoras Planificadas

- Compresión de logs antes del envío
- Encriptación de logs en tránsito
- Backup automático de configuración de Kibana
- Templates de índices optimizados
- Políticas de retención automática
