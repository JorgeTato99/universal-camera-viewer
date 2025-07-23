# 🎥 Universal Camera Gateway

[![Version](https://img.shields.io/badge/version-0.9.10-blue)](https://github.com/JorgeTato99/universal-camera-viewer)
[![Status](https://img.shields.io/badge/status-PRODUCCIÓN-brightgreen)](CURRENT_STATUS.md)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-61dafb)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-WebSocket-009688)](https://fastapi.tiangolo.com/)
[![MediaMTX](https://img.shields.io/badge/MediaMTX-Compatible-orange)](https://github.com/bluenviron/mediamtx)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)

## Gateway inteligente para descubrimiento y publicación de cámaras IP hacia servidores MediaMTX centralizados

> Universal Camera Gateway actúa como puente entre cámaras IP locales y servidores de streaming centralizados, automatizando el descubrimiento, conexión y relay de streams RTSP.

## 🎯 ¿Qué es Universal Camera Gateway?

Universal Camera Gateway (UCG) es una herramienta profesional diseñada para resolver el problema de integrar múltiples cámaras IP de diferentes marcas en un sistema centralizado de video. Funciona como:

1. **Explorador de Red**: Descubre automáticamente cámaras IP en la red local
2. **Gateway de Protocolos**: Conecta con cámaras usando ONVIF, RTSP, HTTP/CGI
3. **Relay de Streaming**: Publica streams hacia servidores MediaMTX (local o cloud)
4. **Panel de Control**: Interfaz web para gestión y monitoreo en tiempo real

### 🏗️ Arquitectura del Sistema

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Cámaras IP     │     │ Universal Camera │     │   MediaMTX      │
│  (Red Local)    │────▶│     Gateway      │────▶│ (Local/Cloud)   │
│                 │RTSP │                  │RTSP │                 │
│ • Dahua         │     │ • Descubrimiento │     │ • Distribución  │
│ • TP-Link       │     │ • Autenticación  │     │ • Grabación     │
│ • Hikvision     │     │ • Relay FFmpeg   │     │ • Transcodifica │
│ • Steren        │     │ • Monitoreo      │     │ • Multi-cliente │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## ✨ Características Principales

### 🔍 Descubrimiento Inteligente

- **Auto-detección** de cámaras en la red local
- **Identificación** automática de marca y modelo
- **Prueba** de múltiples protocolos y puertos
- **Validación** de credenciales y conectividad

### 🌐 Gateway de Publicación

- **Relay RTSP → MediaMTX** sin transcodificación (`-c copy`)
- **Gestión** de múltiples configuraciones MediaMTX
- **Reconexión** automática con backoff exponencial
- **Métricas** en tiempo real de cada publicación

### 🎥 Streaming Local

- **Visualización** directa desde la interfaz web
- **Transmisión** vía WebSocket con baja latencia
- **Soporte** multi-cámara simultáneo
- **Métricas** FPS, latencia, tiempo en línea

### 🖥️ Interfaz de Gestión

- **Dashboard** React con Material-UI
- **Control** individual por cámara
- **Estado** en tiempo real de conexiones
- **Configuración** persistente en base de datos

## 🚀 Inicio Rápido

### Requisitos del Sistema

```bash
# Core
- Python 3.8+
- Node.js 18+
- Yarn (npm tiene bugs con dependencias nativas)

# Para publicación a MediaMTX
- FFmpeg (https://ffmpeg.org/download.html)
- MediaMTX Server (local o remoto)
```

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/JorgeTato99/universal-camera-viewer.git
cd universal-camera-viewer

# Frontend
yarn install         # IMPORTANTE: Usar yarn, NO npm

# Backend
pip install -r requirements.txt

# FFmpeg (para publicación MediaMTX)
# Windows: Descargar y agregar al PATH
# Linux: sudo apt install ffmpeg
# macOS: brew install ffmpeg
```

### Configuración de Base de Datos

```bash
# OPCIÓN 1: Recrear TODO desde cero (DB + Seeds) - Recomendado para desarrollo
python src-python/migrate_database.py --force --no-backup

# OPCIÓN 2: Crear base de datos vacía
python src-python/services/create_database.py --force

# OPCIÓN 3: Solo insertar/actualizar seeds
python src-python/seed_database.py              # Agrega datos si no existen
python src-python/seed_database.py --clear --force  # Limpia todo y reinserta

# Verificar datos existentes
python src-python/seed_database.py --verify-only
```

**Nota**: En desarrollo se puede recrear la DB sin problemas. Las contraseñas se encriptan automáticamente con el sistema v2.

### Ejecución

```bash
# Terminal 1 - Backend FastAPI
python run_api.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs

# Terminal 2 - Frontend React
yarn dev
# UI: http://localhost:5173

# Terminal 3 - MediaMTX (opcional)
# Descargar de: https://github.com/bluenviron/mediamtx
./mediamtx
# RTSP: rtsp://localhost:8554
# API: http://localhost:9997
```

## 📡 Flujo de Trabajo

### 1. Descubrimiento de Cámaras

```python
# El sistema escanea la red local buscando cámaras
# Prueba puertos comunes: 80, 554, 2020, 8000
# Identifica protocolos: ONVIF, RTSP, HTTP
```

### 2. Conexión y Validación

```python
# Valida credenciales con cada cámara
# Descubre endpoints RTSP disponibles
# Almacena configuración en base de datos
```

### 3. Publicación a MediaMTX

```python
# Inicia proceso FFmpeg por cámara:
ffmpeg -i rtsp://camera_local -c copy -f rtsp rtsp://mediamtx_server/camera_id

# Sin transcodificación para máximo rendimiento
# Reconexión automática si falla
```

### 4. Monitoreo

```python
# Dashboard web muestra estado en tiempo real
# WebSocket emite eventos de cambios
# Métricas de FPS, bitrate, latencia
```

## 🔧 API REST

### Endpoints de Cámaras

```bash
# Gestión de cámaras
GET    /api/v2/cameras              # Listar todas
POST   /api/v2/cameras              # Agregar nueva
GET    /api/v2/cameras/{id}         # Detalles
PUT    /api/v2/cameras/{id}         # Actualizar
DELETE /api/v2/cameras/{id}         # Eliminar

# Control de conexión
POST   /api/v2/cameras/{id}/connect
POST   /api/v2/cameras/{id}/disconnect
GET    /api/v2/cameras/{id}/stream-url

# Descubrimiento
POST   /api/v2/cameras/scan-network
POST   /api/v2/cameras/{id}/discover-endpoints
```

### Endpoints de Publicación MediaMTX

```bash
# Control de publicación
POST   /api/publishing/start        # Iniciar relay
POST   /api/publishing/stop         # Detener relay
GET    /api/publishing/status       # Estado global
GET    /api/publishing/status/{id}  # Estado específico

# Configuración MediaMTX
GET    /api/publishing/config       # Listar configs
POST   /api/publishing/config       # Crear config
PUT    /api/publishing/config/{name}
DELETE /api/publishing/config/{name}
POST   /api/publishing/config/{name}/activate
```

## 📊 WebSocket para Eventos

### Streaming de Video

```javascript
// Conectar para recibir frames de video
const ws = new WebSocket('ws://localhost:8000/ws/stream/camera_id');

// Recibir frames
ws.onmessage = (event) => {
  const { type, data, metrics } = JSON.parse(event.data);
  if (type === 'frame') {
    // data contiene imagen JPEG en base64
    img.src = `data:image/jpeg;base64,${data}`;
  }
};
```

### Eventos de Publicación

```javascript
// Suscribirse a eventos MediaMTX
const ws = new WebSocket('ws://localhost:8000/ws/publishing');

ws.send(JSON.stringify({
  type: 'subscribe_camera',
  camera_id: 'cam-001'
}));

// Recibir actualizaciones
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // publishing_started, metrics_update, publishing_error
};
```

## 📁 Estructura del Proyecto

```bash
universal-camera-gateway/
├── src/                    # Frontend React
│   ├── features/          # Componentes por función
│   │   ├── cameras/       # Gestión de cámaras
│   │   └── streaming/     # Player de video
│   └── services/          # Comunicación API/WS
├── src-python/            # Backend FastAPI
│   ├── models/            # Modelos de dominio
│   ├── presenters/        # Lógica MVP
│   ├── services/          # Servicios core
│   │   ├── protocols/     # ONVIF, RTSP, HTTP
│   │   ├── publishing/    # MediaMTX relay
│   │   └── database/      # Persistencia
│   └── websocket/         # Handlers WS
├── src-tauri/             # App nativa (opcional)
└── docs/                  # Documentación
```

## 🎯 Casos de Uso

### 1. Hogar Inteligente

- Descubrir cámaras IP de diferentes marcas
- Centralizar streams en servidor local
- Acceder desde cualquier dispositivo

### 2. Pequeña Empresa

- Gateway en cada sucursal
- Publicar a MediaMTX en la nube
- Monitoreo centralizado

### 3. Instaladores de CCTV

- Herramienta de diagnóstico y configuración
- Validar conectividad antes de instalar NVR
- Documentar configuraciones

## 📈 Rendimiento

### Gateway Local

- **Cámaras simultáneas**: 10-20 (depende del hardware)
- **CPU por cámara**: ~2-5% (relay sin transcodificación)
- **RAM por cámara**: ~50MB
- **Latencia adicional**: < 50ms

### Streaming Directo

- **FPS**: Nativo de la cámara (típico 15-30)
- **Resolución**: Hasta 4K (depende de red)
- **Latencia WebSocket**: < 200ms
- **Clientes simultáneos**: 5-10 por cámara

## 🔒 Seguridad

- **Credenciales encriptadas** en base de datos
- **Sin exposición** de cámaras a internet
- **Autenticación** para API (próximamente)
- **HTTPS** para producción (configurar proxy)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/NewFeature`)
3. Commit cambios (`git commit -m 'Add NewFeature'`)
4. Push al branch (`git push origin feature/NewFeature`)
5. Abrir Pull Request

## 📚 Documentación Adicional

- [Estado actual detallado](CURRENT_STATUS.md)
- [Integración MediaMTX](src-python/docs/mediamtx-integration.md)
- [Arquitectura técnica](docs/ARCHITECTURE.md)
- [Protocolos de cámaras](docs/camera-protocols.md)
- [Esquema de base de datos](docs/DATABASE_SCHEMA_3FN.md)

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles

## 👥 Autor

**Jorge Tato** - [@JorgeTato99](https://github.com/JorgeTato99)

---

> **Universal Camera Gateway** - Transformando cámaras IP aisladas en un sistema de videovigilancia unificado
