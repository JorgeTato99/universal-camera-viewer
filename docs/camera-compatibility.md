# 📷 Compatibilidad de Cámaras

> Guía completa de marcas soportadas, configuración y solución de problemas

## 📊 Marcas Soportadas y Testeadas

| Marca | Modelo | Protocolo | Puerto | Estado | Notas |
|-------|--------|-----------|--------|--------|-------|
| **Dahua** | Hero-K51H | RTSP/ONVIF | 554/80 | ✅ Funcional | Probado en producción |
| **TP-Link** | Tapo C520WS | ONVIF | 2020 | ✅ Funcional | Requiere ONVIF habilitado |
| **Steren** | CCTV-235 | ONVIF | 8000 | ✅ Funcional | RTSP en puerto 5543 |
| **Hikvision** | DS-2CD2043G2-I | RTSP/ONVIF | 554/80 | ⚠️ No probado | Teóricamente compatible |
| **Xiaomi** | Mi Home Security 360 | RTSP | 554 | ⚠️ No probado | Requiere hack RTSP |
| **Reolink** | RLC-810A | RTSP/ONVIF | 554/80 | ⚠️ No probado | Compatible en teoría |

## 🔧 Configuración por Marca

### Dahua

```yaml
Marca: Dahua
Puerto ONVIF: 80
Puerto RTSP: 554
URL RTSP: rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0
Credenciales por defecto: admin/admin (cambiar en primer uso)
```

**Configuración recomendada:**

1. Habilitar ONVIF en configuración web
2. Usar subtype=0 para stream principal
3. Verificar que el usuario tenga permisos ONVIF

### TP-Link Tapo

```yaml
Marca: TP-Link
Puerto ONVIF: 2020
Puerto RTSP: 554
URL RTSP: rtsp://user:pass@ip:554/stream1
Requiere: Crear cuenta local en la app Tapo
```

**Pasos de configuración:**

1. Instalar app Tapo en móvil
2. Configurar cámara con la app
3. Crear usuario local en Configuración > Avanzado
4. Habilitar ONVIF si está disponible

### Steren

```yaml
Marca: Steren
Puerto ONVIF: 8000
Puerto RTSP: 5543
URL RTSP: rtsp://user:pass@ip:5543/stream
Interfaz web: http://ip:80
```

**Notas importantes:**

- Puerto RTSP no estándar (5543)
- ONVIF en puerto 8000
- Algunos modelos requieren Internet Explorer para configuración inicial

### Hikvision

```yaml
Marca: Hikvision
Puerto ONVIF: 80
Puerto RTSP: 554
URL RTSP: rtsp://user:pass@ip:554/Streaming/Channels/101
Stream secundario: /Streaming/Channels/102
```

## 🔍 Credenciales

### Seguridad de Credenciales

Las credenciales se almacenan encriptadas en la base de datos usando AES-256:

```bash
# Ver credenciales actuales (encriptadas)
sqlite3 data/camera_data.db "SELECT username, password_encrypted FROM camera_credentials;"

# Actualizar credenciales mediante seed
python src-python/seed_database.py --clear
```

### Credenciales por Defecto Comunes

| Marca | Usuario | Contraseña | Notas |
|-------|---------|------------|-------|
| Dahua | admin | admin | Cambiar en primer acceso |
| TP-Link | admin | admin | Requiere cuenta Tapo |
| Hikvision | admin | 12345 | Fuerza cambio inicial |
| Steren | admin | admin | Algunos sin contraseña |

⚠️ **IMPORTANTE**: Siempre cambiar las credenciales por defecto

## 🚨 Solución de Problemas

### Error: "Sender not Authorized"

**Causa**: Credenciales incorrectas o permisos ONVIF insuficientes

**Solución**:

```bash
# Actualizar password en base de datos
python src-python/seed_database.py --clear
# Editar el archivo antes de ejecutar con password correcto
```

### Error: "Connection Timeout"

**Causas posibles**:

1. Puerto incorrecto
2. Cámara en diferente VLAN
3. Firewall bloqueando conexión

**Diagnóstico**:

```bash
# Verificar conectividad
ping 192.168.1.172

# Verificar puerto RTSP
nmap -p 554 192.168.1.172

# Test directo RTSP
ffplay rtsp://user:pass@192.168.1.172:554/
```

### Error: "Stream not found"

**Causa**: URL RTSP incorrecta

**Solución**: Probar diferentes paths:

```bash
# Dahua
/cam/realmonitor?channel=1&subtype=0
/cam/realmonitor?channel=1&subtype=1

# Hikvision
/Streaming/Channels/101
/h264/ch1/main/av_stream

# Generic
/stream
/video
/live
```

### Cámara no aparece en scan

**Verificar**:

1. Cámara y PC en misma red
2. ONVIF habilitado en cámara
3. Puerto ONVIF correcto según marca
4. Sin aislamiento de clientes en router WiFi

## 📡 Detección Automática

El sistema incluye auto-detección de cámaras:

```python
# Scanner automático
python src-python/examples/network_analyzer.py

# Salida esperada:
Escaneando red: 192.168.1.0/24
Probando puertos ONVIF: [80, 8080, 2020, 8000]
Cámaras encontradas:
- 192.168.1.172: Dahua (ONVIF puerto 80)
```

## 🔗 URLs RTSP por Marca

### Patrones Comunes

```bash
# Formato general
rtsp://[usuario]:[contraseña]@[ip]:[puerto]/[ruta]

# Ejemplos reales
rtsp://admin:pass123@192.168.1.172:554/cam/realmonitor?channel=1&subtype=0
rtsp://admin:admin@192.168.1.100:554/stream1
rtsp://admin:12345@192.168.1.50:554/Streaming/Channels/101
```

### Herramientas de Testing

```bash
# VLC
vlc rtsp://user:pass@ip:554/path

# FFmpeg
ffmpeg -i rtsp://user:pass@ip:554/path -f null -

# OpenCV Python
import cv2
cap = cv2.VideoCapture("rtsp://user:pass@ip:554/path")
```

## 📚 Referencias

- [ONVIF Specifications](https://www.onvif.org/specifications/)
- [RTSP RFC 2326](https://tools.ietf.org/html/rfc2326)
- [Foros IPCamTalk](https://ipcamtalk.com/) - Comunidad activa

---

**Última actualización**: v0.9.5 - Julio 2025
