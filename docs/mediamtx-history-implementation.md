# Implementación del Sistema de Historial MediaMTX - Fase 2.2

## Resumen Ejecutivo

Se ha completado la implementación del sistema de historial de publicaciones para MediaMTX, incluyendo:

1. **Métodos de consulta** con filtros avanzados y paginación
2. **Gestión automática** de transición de publicaciones activas a historial
3. **Limpieza inteligente** con modo dry-run
4. **Optimizaciones de BD** mediante índices especializados

## Arquitectura Implementada

### 1. Flujo de Datos

```
camera_publications (activa) → publication_history (al detener)
         ↓                              ↓
publication_metrics              métricas agregadas
         ↓                              ↓
publication_viewers              estadísticas finales
```

### 2. Componentes Principales

#### MediaMTXDatabaseService

**Métodos implementados:**

- `get_publication_history(request: GetHistoryRequest)`: Consulta con filtros
- `get_session_detail(session_id: str)`: Detalle completo de sesión
- `cleanup_old_history(...)`: Limpieza segura con preview
- `move_publication_to_history(...)`: Transición automática

#### Integración con RTSPPublisherService

Al detener una publicación:

1. Determina razón de terminación (USER_STOPPED, ERROR)
2. Calcula métricas agregadas finales
3. Mueve datos a `publication_history`
4. Limpia registros temporales

### 3. Optimizaciones de Base de Datos

#### Índices Creados

```sql
-- Filtros comunes
idx_publication_history_filters(camera_id, start_time DESC, termination_reason)

-- Búsquedas temporales
idx_publication_history_time_range(start_time DESC, end_time)

-- Análisis de duración
idx_publication_history_duration(duration_seconds, start_time DESC)

-- Sesiones con errores
idx_publication_history_errors(error_count, termination_reason)
WHERE error_count > 0
```

#### Vista Materializada

```sql
CREATE VIEW v_publication_stats AS
-- Estadísticas pre-calculadas por cámara y día
```

## Características Destacadas

### 1. Filtros Avanzados

- Por cámara, servidor, estado
- Rango de fechas flexible
- Duración mínima
- Razón de terminación
- Ordenamiento configurable

### 2. Limpieza Inteligente

```python
cleanup_old_history(
    older_than_days=90,
    keep_errors=True,      # Mantiene sesiones problemáticas
    dry_run=True          # Preview por defecto
)
```

**Protecciones:**

- Mantiene sesiones con errores
- Preserva sesiones largas (>24h)
- Transaccional con rollback
- Reporte detallado antes de eliminar

### 3. Detalle de Sesión Completo

Incluye:

- Información básica + metadata
- Métricas agregadas (FPS, bitrate, frames)
- Timeline de errores
- Estadísticas de viewers por protocolo
- Comando FFmpeg utilizado

## Decisiones de Diseño

### 1. Session ID con UUID

- Generado con `uuid.uuid4()` para unicidad global
- Permite rastreo entre tablas relacionadas
- Facilita debugging y auditoría

### 2. Metadata JSON

Almacena información adicional flexible:

- `process_pid`: PID del proceso FFmpeg
- `ffmpeg_command`: Comando completo para debug
- `final_error_count`: Contador final de errores

### 3. Dry-Run por Defecto

- Previene eliminaciones accidentales
- Permite preview de cambios
- Reporte detallado sin modificar datos

## Consideraciones de Rendimiento

### 1. Paginación Obligatoria

- Límite máximo: 200 registros por página
- Offset calculado para grandes datasets
- Count query separada para total

### 2. Agregaciones Eficientes

- Uso de índices para GROUP BY
- Límites en queries pesadas (TOP 10)
- Cálculos incrementales donde sea posible

### 3. Limpieza en Lotes

- Transacciones para consistencia
- Eliminación en cascada optimizada
- Estimación de espacio antes de ejecutar

## Mantenimiento Recomendado

### 1. Limpieza Periódica

```bash
# Ejecutar mensualmente
# Preview
DELETE /api/publishing/history?older_than_days=90&dry_run=true

# Ejecutar si OK
DELETE /api/publishing/history?older_than_days=90&dry_run=false
```

### 2. Monitoreo de Índices

```sql
-- Verificar uso de índices
EXPLAIN QUERY PLAN
SELECT * FROM publication_history
WHERE camera_id = ? AND start_time > ?;
```

### 3. Vacuum Periódico

```sql
-- Después de limpiezas masivas
VACUUM publication_history;
ANALYZE publication_history;
```

## Próximos Pasos

### Mejoras Futuras

1. **Tabla de eventos** para timeline detallado
2. **Métricas en tiempo real** via WebSocket
3. **Exportación** a formatos CSV/Excel
4. **Gráficos de tendencias** históricos

### Integración Pendiente

1. Dashboard de estadísticas en frontend
2. Alertas por patrones anómalos
3. API de análisis predictivo

## Notas de Implementación

### TODOs Documentados

```python
# TODO: Implementar tabla de eventos/errores
# En get_session_detail(), línea 844

# TODO: Calcular uptime_percent basado en duración esperada
# En get_session_detail(), línea 838
```

### Limitaciones Actuales

1. Timeline de errores es básico (solo último error)
2. No hay exportación directa a archivos
3. Análisis geográfico de viewers no implementado

## Testing Recomendado

### 1. Test de Filtros

```python
# Verificar todos los filtros
request = GetHistoryRequest(
    camera_id="cam_001",
    start_date=datetime.now() - timedelta(days=7),
    min_duration_seconds=300,
    termination_reason=TerminationReason.ERROR
)
```

### 2. Test de Limpieza

```python
# Siempre con dry_run primero
result = await cleanup_old_history(
    older_than_days=30,
    keep_errors=True,
    dry_run=True
)
assert result['dry_run'] == True
```

### 3. Test de Transición

```python
# Verificar move_to_history
await stop_publishing(camera_id)
# Verificar que aparece en historial
history = await get_publication_history(...)
assert camera_id in [h['camera_id'] for h in history['items']]
```
