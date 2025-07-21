# 📺 Guía Frontend - APIs MediaMTX

## 🎯 Resumen Ejecutivo

Se han implementado APIs completas para la integración con MediaMTX, el servidor RTSP que centraliza el streaming. Esta guía ayudará a los desarrolladores frontend a crear las vistas necesarias para consumir estas APIs.

---

## 🗂️ Estructura de Menú Propuesta

```
📡 Publicación MediaMTX
├── 📊 Dashboard
├── 🎥 Publicaciones Activas
├── 📈 Métricas y Estadísticas
├── 📜 Historial de Sesiones
├── 👥 Audiencia y Viewers
├── 🛤️ Configuración de Paths
└── 🏥 Salud del Sistema
```

---

## 🚀 APIs Principales y Casos de Uso

### 1. Dashboard Principal

**Vista sugerida**: Panel con widgets de resumen

#### Endpoints clave:
```typescript
// Estado general del sistema
GET /api/publishing/health

// Publicaciones activas
GET /api/publishing/status

// Estadísticas agregadas
GET /api/publishing/statistics/summary
```

**Archivo de referencia**: `src-python/api/routers/publishing.py`

#### Ejemplo de respuesta (health):
```json
{
  "overall_status": "healthy",
  "total_servers": 2,
  "healthy_servers": 2,
  "active_publications": 15,
  "total_viewers": 47,
  "active_alerts": []
}
```

---

### 2. Control de Publicaciones

**Vista sugerida**: Tabla con acciones de control

#### Endpoints principales:
```typescript
// Iniciar publicación
POST /api/publishing/start
{
  "camera_id": "cam-001",
  "force_restart": false
}

// Detener publicación
POST /api/publishing/stop
{
  "camera_id": "cam-001"
}

// Estado de una cámara específica
GET /api/publishing/status/{camera_id}
```

**Archivo de referencia**: `src-python/api/routers/publishing.py`

#### Componentes sugeridos:
- Tabla de cámaras con estado actual
- Botones Start/Stop con confirmación
- Indicador de estado en tiempo real
- Modal para ver detalles de error

---

### 3. Métricas y Estadísticas

**Vista sugerida**: Dashboard con gráficos

#### Endpoints relevantes:
```typescript
// Métricas actuales de una cámara
GET /api/publishing/metrics/{camera_id}

// Historial de métricas con paginación
GET /api/publishing/metrics/{camera_id}/history?page=1&page_size=100&time_range=last_24_hours

// Dashboard de estadísticas
GET /api/publishing/statistics/summary?time_range=last_7_days

// Exportar métricas
POST /api/publishing/metrics/{camera_id}/export
{
  "format": "excel",
  "time_range": "last_30_days",
  "include_events": true
}
```

**Archivo de referencia**: `src-python/routers/publishing_metrics.py`

#### Visualizaciones recomendadas:
- Gráfico de línea temporal (bitrate, FPS)
- Gauge para métricas en tiempo real
- Heatmap de actividad por hora
- Botón de exportación con formatos

---

### 4. Historial de Publicaciones

**Vista sugerida**: Tabla con filtros avanzados

#### Endpoints principales:
```typescript
// Listado con filtros
GET /api/publishing/history?
  camera_id=cam-001&
  start_date=2025-01-01&
  page=1&
  page_size=50&
  order_by=start_time&
  order_desc=true

// Detalle de sesión
GET /api/publishing/history/{session_id}

// Historial por cámara
GET /api/publishing/history/camera/{camera_id}?days=7

// Limpieza de historial antiguo
DELETE /api/publishing/history
{
  "older_than_days": 90,
  "keep_errors": true,
  "dry_run": true  // Primero simular
}
```

**Archivo de referencia**: `src-python/routers/publishing_history.py`

#### Características de la vista:
- Filtros por fecha, cámara, estado
- Timeline visual de sesiones
- Modal con detalles completos
- Herramienta de limpieza con preview

---

### 5. Gestión de Audiencia

**Vista sugerida**: Dashboard analítico

#### Endpoints clave:
```typescript
// Viewers activos
GET /api/publishing/viewers?active_only=true&page=1

// Análisis de audiencia
GET /api/publishing/viewers/analytics?
  time_range=last_7_days&
  group_by=day&
  include_geographic=true

// Viewers por publicación
GET /api/publishing/viewers/{publication_id}

// Estadísticas por protocolo
GET /api/publishing/stats/protocols
```

**Archivo de referencia**: `src-python/routers/publishing_viewers.py`

#### Visualizaciones sugeridas:
- Mapa de calor geográfico
- Gráfico de barras por protocolo
- Timeline de viewers concurrentes
- Top cámaras por audiencia

---

### 6. Configuración de Paths MediaMTX

**Vista sugerida**: CRUD con formulario avanzado

#### Endpoints principales:
```typescript
// Listar paths
GET /api/publishing/paths?server_id=1&active_only=true

// Crear path
POST /api/publishing/paths
{
  "server_id": 1,
  "path_name": "entrance_cam",
  "source_type": "rtsp",
  "source_url": "rtsp://192.168.1.100:554/stream",
  "record_enabled": true,
  "authentication_required": false
}

// Actualizar path
PUT /api/publishing/paths/{path_id}

// Probar conectividad
POST /api/publishing/paths/{path_id}/test
{
  "timeout_seconds": 10,
  "test_write": true
}

// Plantillas disponibles
GET /api/publishing/paths/templates
```

**Archivo de referencia**: `src-python/routers/mediamtx_paths.py`

#### Componentes del formulario:
- Selector de tipo de fuente
- Configuración de grabación
- Gestión de permisos/IPs
- Test de conectividad integrado
- Plantillas predefinidas

---

### 7. Monitoreo de Salud

**Vista sugerida**: Panel de estado con alertas

#### Endpoints relevantes:
```typescript
// Alertas activas
GET /api/publishing/alerts?severity=error

// Estado de servidor específico
GET /api/publishing/servers/{server_id}/status

// Health check manual
POST /api/publishing/servers/{server_id}/health-check
{
  "check_rtsp": true,
  "check_api": true,
  "timeout_seconds": 10
}
```

**Archivo de referencia**: `src-python/api/routers/publishing.py`

#### Elementos de la vista:
- Semáforo de estado por servidor
- Lista de alertas con prioridad
- Botón de health check manual
- Historial de incidentes

---

## 💡 Mejores Prácticas de Implementación

### 1. Manejo de Estados
```typescript
// Estados posibles de publicación
enum PublishStatus {
  IDLE = "idle",
  STARTING = "starting", 
  RUNNING = "running",
  ERROR = "error",
  STOPPING = "stopping"
}
```

### 2. Polling para Actualizaciones
```typescript
// Para vistas en tiempo real
useInterval(() => {
  fetchPublishingStatus();
  fetchActiveViewers();
}, 5000); // Cada 5 segundos
```

### 3. Manejo de Errores
```typescript
// Todas las APIs devuelven formato consistente
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  error_code?: string;
}
```

### 4. Paginación
```typescript
// Parámetros estándar
interface PaginationParams {
  page: number;      // Desde 1
  page_size: number; // Max 200
}

// Respuesta paginada
interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}
```

---

## 🎨 Diseño UX Recomendado

### Colores de Estado
- 🟢 **Verde**: Publicando correctamente
- 🟡 **Amarillo**: Iniciando/Deteniendo
- 🔴 **Rojo**: Error o desconectado
- ⚫ **Gris**: Inactivo

### Acciones Rápidas
- **Play/Stop**: Control directo desde tabla
- **Ver Métricas**: Click en cámara activa
- **Exportar**: Botón contextual en gráficos
- **Refresh**: Actualización manual disponible

### Notificaciones
- Toast para acciones exitosas
- Modal para errores con detalles
- Badge para alertas no leídas
- Sonido opcional para alertas críticas

---

## 📁 Estructura de Archivos Backend

Para referencia completa del código:

```
src-python/
├── api/
│   ├── routers/
│   │   ├── publishing.py          # Control básico + health
│   │   └── publishing_config.py   # Configuración servidores
│   └── schemas/
│       ├── requests/
│       │   └── mediamtx_requests.py
│       └── responses/
│           └── mediamtx_responses.py
├── routers/
│   ├── publishing_metrics.py     # Métricas y estadísticas
│   ├── publishing_history.py     # Historial de sesiones
│   ├── publishing_viewers.py     # Gestión de audiencia
│   └── mediamtx_paths.py        # Configuración de paths
└── services/
    └── database/
        └── mediamtx_db_service.py # Lógica de BD
```

---

## 🚦 Flujo de Trabajo Típico

1. **Configurar Servidor MediaMTX** (una vez)
   - POST `/api/publishing/config`

2. **Crear Path para Cámara**
   - POST `/api/publishing/paths`
   - POST `/api/publishing/paths/{id}/test`

3. **Iniciar Publicación**
   - POST `/api/publishing/start`
   - GET `/api/publishing/status/{camera_id}`

4. **Monitorear**
   - GET `/api/publishing/metrics/{camera_id}`
   - GET `/api/publishing/viewers`

5. **Revisar Historial**
   - GET `/api/publishing/history`
   - GET `/api/publishing/statistics/summary`

---

## 🔗 Enlaces Útiles

- **Documentación Swagger**: http://localhost:8000/docs
- **Esquemas TypeScript**: Generar desde OpenAPI
- **WebSocket Events**: Ver `websocket/handlers/publishing_handler.py`

---

## 📞 Soporte

Para dudas sobre las APIs:
1. Revisar los archivos mencionados
2. Consultar logs del backend
3. Usar Swagger UI para pruebas
4. Verificar schemas de request/response