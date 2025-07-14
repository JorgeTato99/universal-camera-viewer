# 📷 Compatibilidad de Cámaras

## Marcas Soportadas y Testadas

### ✅ Dahua
- **Modelo Probado**: Hero-K51H
- **Configuración**:
  - ONVIF: Puerto 80
  - RTSP: Puerto 554 (requiere DMSS workflow)
  - Resolución: 4K (2880x1620)
  - FPS: 13-15
- **Notas**: Excelente compatibilidad ONVIF, HTTP/CGI no soportado en este modelo

### ✅ TP-Link
- **Modelo Probado**: Tapo C520WS
- **Configuración**:
  - ONVIF: Puerto 2020
  - RTSP: Puerto 554 (directo)
  - Multi-perfil soportado
  - FPS: Variable según perfil
- **Notas**: Discovery intermitente (~4% fail rate), retry automático implementado

### ✅ Steren
- **Modelo Probado**: CCTV-235
- **Configuración**:
  - ONVIF: Puerto 8000
  - RTSP: Puerto 5543
  - Dual-stream: 4MP + 360p
  - FPS: 20+
- **Notas**: Excelente rendimiento con dual-stream

### ✅ China Genérica
- **Modelo Probado**: 8MP WiFi
- **Configuración**:
  - Detección automática de protocolo
  - 16+ patrones RTSP probados
  - Resolución: 5.9MP (2304x2592)
  - FPS: 12
- **Notas**: 30% requieren patrones no estándar, auto-detección funcional

## Métricas de Rendimiento

| Marca | Protocolo | FPS | Resolución | Latencia | CPU | RAM |
|-------|-----------|-----|------------|----------|-----|-----|
| Dahua | ONVIF | 13.86 | 4K | 89ms | 8.2% | 45MB |
| Dahua | RTSP | 15.32 | 4K | 125ms | 9.1% | 48MB |
| TP-Link | ONVIF | Variable | Multi | 178ms | 6.5% | 38MB |
| Steren | ONVIF | 20.3 | 4MP/360p | 95ms | 7.8% | 42MB |
| Generic | Auto | 12.0 | 5.9MP | 210ms | 10.1% | 52MB |

## Configuración por Marca

### Dahua
```python
{
    'onvif_port': 80,
    'rtsp_port': 554,
    'stream_path': '/cam/realmonitor?channel=1&subtype=0',
    'snapshot_endpoint': '/cgi-bin/snapshot.cgi',
    'auth_method': 'digest'
}
```

### TP-Link
```python
{
    'onvif_port': 2020,
    'rtsp_port': 554,
    'stream_paths': ['/stream1', '/stream2'],
    'auth_method': 'basic'
}
```

### Steren
```python
{
    'onvif_port': 8000,
    'rtsp_port': 5543,
    'dual_stream': True,
    'profiles': ['PROFILE_395207', 'PROFILE_395208']
}
```

### Genérica
```python
{
    'auto_detect': True,
    'common_ports': [80, 554, 2020, 8000, 8080],
    'rtsp_patterns': [
        '/stream1', '/stream2', '/live/stream1',
        '/h264', '/video', '/main', '/sub',
        '/user={user}&password={pass}&channel=1&stream=0'
    ]
}
```

## URLs RTSP Descubiertas

```bash
# Dahua Hero-K51H
rtsp://admin:password@192.168.1.172:554/cam/realmonitor?channel=1&subtype=0

# TP-Link Tapo C520WS
rtsp://admin:password@192.168.1.77:554/stream1

# Steren CCTV-235
rtsp://admin:password@192.168.1.178:5543/live/channel0

# China Genérica 8MP
rtsp://192.168.1.180:554/user=EightMPWiFiSCmr&password=password&channel=1&stream=0
```

## Solución de Problemas

### Dahua
- **Problema**: RTSP no funciona directamente
- **Solución**: Activar primero en app DMSS, luego conectar

### TP-Link
- **Problema**: Discovery falla ocasionalmente
- **Solución**: Sistema de retry automático (hasta 3 intentos)

### Steren
- **Problema**: Puerto ONVIF no estándar (8000)
- **Solución**: Auto-detección de puertos implementada

### Genérica
- **Problema**: URL RTSP no estándar
- **Solución**: 16+ patrones de prueba automática

## Agregar Nueva Cámara

1. **Probar ONVIF Discovery**:
   ```python
   python examples/protocols/onvif_discovery.py
   ```

2. **Identificar Puertos**:
   ```python
   python examples/network/port_scanner.py --ip 192.168.1.X
   ```

3. **Validar Conexión**:
   ```python
   python examples/protocols/connection_test.py
   ```

4. **Agregar Configuración**:
   - Editar `camera_brands.json`
   - Agregar perfil de marca
   - Documentar en este archivo