# Respuesta a Implementación de Métricas de Latencia - Backend

## ✅ Estado: IMPLEMENTADO - 17 de Enero 2025

## 📋 Resumen de Implementación

Se ha implementado el campo de latencia solicitado por el equipo de frontend en las métricas del stream. La implementación incluye tanto latencia simulada (inmediata) como soporte para latencia real (futura).

## 🎯 Cambios Realizados

### 1. Latencia Simulada (COMPLETADO)

**Archivo modificado**: `src-python/websocket/stream_handler.py`

#### Método `calculate_metrics()` actualizado:
```python
def calculate_metrics(self) -> Dict[str, Any]:
    # ... código existente ...
    
    # Latencia simulada basada en calidad (valores realistas para cámaras IP)
    latency_map = {
        "low": 150,     # 150ms para baja calidad
        "medium": 100,  # 100ms para calidad media  
        "high": 200     # 200ms para alta calidad
    }
    base_latency = latency_map.get(self.quality, 100)
    
    # Variabilidad de ±20ms para simular condiciones reales
    latency = base_latency + random.randint(-20, 20)
    latency = max(latency, 10)  # Mínimo 10ms
    
    return {
        "fps": round(actual_fps, 1),
        "target_fps": self.fps,
        "quality": self.quality,
        "format": self.format,
        "frames_sent": self.frame_count,
        "uptime_seconds": round(elapsed, 1),
        "latency": latency,  # NUEVO CAMPO
        # Métricas adicionales
        "avg_fps": round(self.metrics.get_average_fps(), 1),
        "avg_latency": round(self.metrics.get_average_latency(), 1),
        "health_score": round(self.metrics.get_health_score(), 1)
    }
```

### 2. Integración con StreamMetrics (COMPLETADO)

Se integró el modelo `StreamMetrics` existente que mantiene un historial de 30 valores de latencia:

```python
# Constructor actualizado
def __init__(self, camera_id: str, websocket: WebSocket, client_id: str):
    # ... código existente ...
    
    # Modelo de métricas avanzadas
    self.metrics = StreamMetrics(stream_id=f"{camera_id}_{client_id}")
```

### 3. Soporte para Latencia Real (COMPLETADO)

**Método `send_frame()` actualizado** para aceptar timestamp de captura:

```python
async def send_frame(self, frame_data: str, capture_timestamp: Optional[float] = None) -> None:
    """
    Args:
        frame_data: Frame en base64
        capture_timestamp: Timestamp de captura en milisegundos (opcional)
    """
    # Calcular latencia real si tenemos timestamp
    real_latency = None
    if capture_timestamp:
        current_time_ms = time.time() * 1000
        real_latency = round(current_time_ms - capture_timestamp)
        self.metrics.update_latency(real_latency)
    
    metrics = self.calculate_metrics()
    
    # Usar latencia real si está disponible
    if real_latency is not None:
        metrics["latency"] = real_latency
        metrics["latency_type"] = "real"
    else:
        metrics["latency_type"] = "simulated"
```

## 📊 Formato de Respuesta Actualizado

El frontend ahora recibirá:

```json
{
  "type": "frame",
  "camera_id": "5c69e02a-bd5e-4559-85c9-90664032f860",
  "data": "...",
  "timestamp": "2025-07-17T18:00:00.000Z",
  "frame_number": 100,
  "metrics": {
    "fps": 9.5,
    "target_fps": 15,
    "quality": "medium",
    "format": "jpeg",
    "frames_sent": 100,
    "uptime_seconds": 300.5,
    "latency": 95,              // NUEVO: Latencia actual en ms
    "latency_type": "simulated", // NUEVO: Tipo de latencia
    "avg_fps": 14.2,            // NUEVO: FPS promedio
    "avg_latency": 102.3,       // NUEVO: Latencia promedio
    "health_score": 85.5        // NUEVO: Score de salud (0-100)
  }
}
```

## 🔄 Diferencias con la Propuesta Original

### Mejoras implementadas:
1. **Valores más realistas**: 100-200ms en lugar de 30-80ms
2. **Variabilidad dinámica**: ±20ms para simular jitter de red
3. **Métricas adicionales**: Promedios y health score
4. **Indicador de tipo**: `latency_type` para diferenciar real vs simulada

### Rationale de los cambios:
- **100-200ms**: Más realista para cámaras IP en redes locales
- **Variabilidad**: Simula condiciones reales de red (jitter)
- **Health Score**: Métrica compuesta útil para dashboards

## 🚀 Uso para el Frontend

### Mostrar latencia actual:
```typescript
const Latency = ({ metrics }) => {
  const { latency, latency_type } = metrics;
  const isHigh = latency > 200;
  
  return (
    <div className={`latency ${isHigh ? 'warning' : 'normal'}`}>
      <span>{latency}ms</span>
      {latency_type === 'simulated' && <sup>*</sup>}
    </div>
  );
};
```

### Indicador de salud del stream:
```typescript
const StreamHealth = ({ metrics }) => {
  const { health_score } = metrics;
  const status = health_score > 80 ? 'good' : 
                 health_score > 60 ? 'fair' : 'poor';
  
  return (
    <HealthBar 
      value={health_score} 
      status={status}
      label={`Stream Health: ${health_score}%`}
    />
  );
};
```

## 📈 Próximos Pasos (Opcional)

Para implementar latencia real en el futuro:

1. **En el servicio que captura frames**:
```python
frame_data = {
    "data": base64_frame,
    "capture_timestamp": time.time() * 1000
}
```

2. **Al enviar el frame**:
```python
await stream_handler.send_frame(
    frame_data["data"], 
    capture_timestamp=frame_data["capture_timestamp"]
)
```

## ✅ Verificación

Para verificar que funciona:

1. Conectar a un stream
2. Observar el campo `latency` en las métricas
3. La latencia debería variar entre 80-220ms según la calidad
4. El campo `latency_type` indicará "simulated" por ahora

## 📝 Notas Adicionales

- La latencia simulada es suficiente para desarrollo/testing del frontend
- La infraestructura para latencia real está lista cuando se necesite
- El modelo `StreamMetrics` mantiene historial de 30 valores
- El `health_score` considera FPS, latencia, errores y frames perdidos

## 🤝 Confirmación

La implementación está completa y lista para uso. El frontend puede empezar a usar el campo `latency` inmediatamente. Los valores simulados son realistas y varían dinámicamente para proporcionar una experiencia similar a la producción.