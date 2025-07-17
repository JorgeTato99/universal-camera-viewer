# Implementación de Métricas de Latencia - Backend

## Problema Identificado

El frontend espera recibir métricas de latencia (en milisegundos) para mostrar en la interfaz de usuario, pero el backend no está enviando este campo en las métricas del stream.

## Ubicación del Problema

**Archivo**: `src-python/websocket/stream_handler.py`  
**Método**: `calculate_metrics()` (líneas 415-435)

## Solución Requerida

### 1. Modificar el método `calculate_metrics()` para incluir latencia

```python
def calculate_metrics(self) -> Dict[str, Any]:
    """
    Calcular métricas del stream.
    
    Returns:
        Diccionario con métricas
    """
    if not self.start_time:
        return {}
    
    elapsed = (datetime.utcnow() - self.start_time).total_seconds()
    actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
    
    # Calcular latencia simulada o real
    # Opción 1: Latencia simulada basada en calidad
    latency_map = {
        "low": 30,      # 30ms para baja calidad
        "medium": 50,   # 50ms para calidad media
        "high": 80      # 80ms para alta calidad
    }
    latency = latency_map.get(self.quality, 50)
    
    # Opción 2: Si tienen acceso a métricas reales de la cámara
    # latency = self.get_real_latency()  # Implementar según su sistema
    
    return {
        "fps": round(actual_fps, 1),
        "target_fps": self.fps,
        "quality": self.quality,
        "format": self.format,
        "frames_sent": self.frame_count,
        "uptime_seconds": round(elapsed, 1),
        "latency": latency  # NUEVO CAMPO
    }
```

### 2. Para una implementación más avanzada con latencia real

Si desean calcular la latencia real (tiempo entre captura del frame y recepción en el cliente), necesitarán:

1. **Agregar timestamp al frame cuando se captura**:
```python
# En el servicio que captura frames de la cámara
frame_data = {
    "data": base64_frame,
    "capture_timestamp": time.time() * 1000  # En milisegundos
}
```

2. **Calcular latencia al enviar**:
```python
# En stream_handler.py
async def send_frame(self, frame_data: str, capture_timestamp: float = None) -> None:
    """
    Enviar frame al cliente.
    
    Args:
        frame_data: Frame en base64
        capture_timestamp: Timestamp de captura en ms
    """
    # Calcular latencia si tenemos timestamp de captura
    latency = 0
    if capture_timestamp:
        current_time = time.time() * 1000  # En milisegundos
        latency = round(current_time - capture_timestamp)
    
    metrics = self.calculate_metrics()
    metrics["latency"] = latency  # Sobrescribir con latencia real
    
    message = {
        "type": "frame",
        "camera_id": self.camera_id,
        "data": frame_data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "frame_number": self.frame_count,
        "metrics": metrics
    }
    
    await self.connection.send_json(message)
```

### 3. Integración con el modelo StreamMetrics existente

Ya tienen un modelo `StreamMetrics` en `src-python/models/streaming/stream_metrics.py` que soporta latencia. Pueden integrarlo:

```python
# En stream_handler.py
from models.streaming.stream_metrics import StreamMetrics

class StreamHandler:
    def __init__(self, camera_id: str, websocket: WebSocket, client_id: str):
        # ... código existente ...
        self.metrics = StreamMetrics(stream_id=f"{camera_id}_{client_id}")
    
    async def send_frame(self, frame_data: str) -> None:
        # Actualizar métricas
        self.metrics.increment_frame_count()
        
        # Si tienen latencia real, actualizarla
        # self.metrics.update_latency(calculated_latency)
        
        metrics_dict = {
            "fps": self.metrics.get_current_fps(),
            "target_fps": self.fps,
            "quality": self.quality,
            "format": self.format,
            "frames_sent": self.metrics.total_frames,
            "latency": self.metrics.get_current_latency()  # Usar latencia del modelo
        }
        
        # ... resto del código ...
```

## Verificación

Después de implementar los cambios, las métricas enviadas al frontend deberían incluir:

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
    "latency": 45  // NUEVO CAMPO EN MILISEGUNDOS
  }
}
```

## Notas Adicionales

- La latencia puede ser simulada inicialmente (como en la Opción 1) para verificar que el frontend funciona correctamente
- Para una implementación real, necesitarán medir el tiempo desde la captura del frame hasta su envío
- Consideren usar el modelo `StreamMetrics` existente para mantener un historial de latencias y calcular promedios