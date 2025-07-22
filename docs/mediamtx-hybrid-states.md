# 📋 Documentación: Estados Híbridos MediaMTX

## 🎯 Resumen

El sistema MediaMTX utiliza una arquitectura de **estados híbridos** donde el backend y frontend manejan diferentes conjuntos de estados para optimizar tanto el rendimiento del sistema como la experiencia del usuario.

## 🔄 Estados por Capa

### Backend (5 estados)

El backend maneja únicamente los estados esenciales del sistema:

```python
class PublishStatus(Enum):
    IDLE = "idle"              # Sin actividad
    STARTING = "starting"      # Iniciando publicación
    PUBLISHING = "publishing"  # Publicando activamente
    ERROR = "error"           # Error en la publicación
    STOPPED = "stopped"       # Detenido (para historial)
```

### Frontend (7 estados)

El frontend extiende los estados para mejorar la UX:

```typescript
enum PublishingStatus {
  IDLE = 'IDLE',
  STARTING = 'STARTING',
  PUBLISHING = 'PUBLISHING',
  STOPPING = 'STOPPING',        // Solo frontend - transitorio
  STOPPED = 'STOPPED',
  ERROR = 'ERROR',
  RECONNECTING = 'RECONNECTING' // Solo frontend - transitorio
}
```

## 🎭 Estados Transitorios (Solo Frontend)

### STOPPING

- **Cuándo se usa**: Cuando el usuario hace clic en "Detener publicación"
- **Duración**: Desde el clic hasta recibir confirmación del backend
- **Propósito**: Dar feedback inmediato al usuario
- **Transición**: PUBLISHING → STOPPING → IDLE/STOPPED

```typescript
// En publishingStore.ts
stopPublishing: async (cameraId) => {
  // 1. Cambiar a STOPPING localmente
  publication.status = PublishingStatus.STOPPING;
  
  // 2. Llamar al backend
  await api.stopPublishing(cameraId);
  
  // 3. Backend responde con IDLE o STOPPED
  publication.status = response.status;
}
```

### RECONNECTING

- **Cuándo se usa**: Cuando el backend indica error con metadata de reconexión
- **Duración**: Durante los intentos de reconexión
- **Propósito**: Distinguir entre error permanente y reconexión temporal
- **Transición**: ERROR (con metadata) → RECONNECTING → PUBLISHING/ERROR

```typescript
// Mapeo en fetchPublishingStatus
const context = {
  isReconnecting: pub.metrics?.is_reconnecting || false
};

if (pub.status === 'error' && context.isReconnecting) {
  return PublishingStatus.RECONNECTING;
}
```

## 🔄 Flujo de Estados

### Publicación Exitosa
```
[No existe] → STARTING → PUBLISHING → STOPPING* → STOPPED/IDLE
                                        (*solo frontend)
```

### Publicación con Error y Reconexión
```
PUBLISHING → ERROR → RECONNECTING* → PUBLISHING
                      (*solo frontend si hay metadata)
```

## 💾 Manejo en Backend

El backend indica reconexión mediante **metadata** en lugar de un estado explícito:

```python
# En rtsp_publisher_service.py
if process.error_count <= self._config.max_reconnects:
    process.status = PublishStatus.ERROR
    process.metrics['is_reconnecting'] = True
    process.metrics['reconnect_attempt'] = process.error_count
    process.metrics['max_reconnects'] = self._config.max_reconnects
```

## 🖥️ Mapeo Frontend-Backend

El frontend utiliza la función `mapBackendToFrontendPublishingStatus` para convertir estados:

```typescript
// src/utils/statusLabels.ts
export function mapBackendToFrontendPublishingStatus(
  backendStatus: string,
  context?: {
    isReconnecting?: boolean;
    isStopping?: boolean;
  }
): string {
  // ERROR con reconexión → RECONNECTING
  if (backendStatus === 'error' && context?.isReconnecting) {
    return 'RECONNECTING';
  }
  
  // Estados transitorios locales
  if (context?.isStopping) {
    return 'STOPPING';
  }
  
  // Mapeo directo
  return backendStatus.toUpperCase();
}
```

## 🏷️ Etiquetas en Español

Todas las etiquetas de estado se centralizan en `src/utils/statusLabels.ts`:

```typescript
export const PublishingStatusLabels = {
  IDLE: 'Inactivo',
  STARTING: 'Iniciando',
  PUBLISHING: 'Publicando',
  STOPPING: 'Deteniendo',      // Solo frontend
  STOPPED: 'Detenido',
  ERROR: 'Error',
  RECONNECTING: 'Reconectando' // Solo frontend
}
```

## ✅ Beneficios del Enfoque Híbrido

1. **Backend Simple**: Solo maneja estados reales del sistema
2. **UX Mejorada**: Estados transitorios dan mejor feedback
3. **Sin Overhead**: No hay comunicación innecesaria backend↔frontend
4. **Flexibilidad**: Frontend puede agregar estados sin modificar backend
5. **Escalabilidad**: Fácil agregar nuevos estados transitorios

## ⚠️ Consideraciones Importantes

1. **Sincronización**: Los estados transitorios deben resolverse rápidamente
2. **Timeout**: Implementar timeouts para estados transitorios
3. **Consistencia**: El estado final siempre viene del backend
4. **Testing**: Probar transiciones de estados, especialmente las locales

## 📝 Ejemplo de Uso

```typescript
// Componente usando estados con etiquetas
import { getPublishingStatusLabel } from '@/utils/statusLabels';

function PublishingStatus({ status }) {
  const label = getPublishingStatusLabel(status);
  const isTransient = ['STOPPING', 'RECONNECTING'].includes(status);
  
  return (
    <Chip 
      label={label}
      color={getStatusColor(status)}
      variant={isTransient ? 'outlined' : 'filled'}
    />
  );
}
```

## 🔮 Extensibilidad Futura

Este sistema permite agregar fácilmente:

1. Nuevos estados transitorios (ej: `PAUSING`, `RESUMING`)
2. Internacionalización completa con i18n
3. Estados específicos por tipo de cámara
4. Animaciones basadas en transiciones de estado

---

**Última actualización**: 2025-07-22