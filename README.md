# 🎥 Universal Camera Viewer

[![Version](https://img.shields.io/badge/version-0.8.5-blue)](https://github.com/JorgeTato99/universal-camera-viewer)
[![Status](https://img.shields.io/badge/status-FUNCIONAL-brightgreen)](CURRENT_STATUS.md)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-61dafb)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-WebSocket-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)

Sistema profesional de videovigilancia IP con streaming en tiempo real. ¡Ciclo completo funcional implementado!

## 🎉 Nuevo en v0.8.5: Streaming en Tiempo Real

- ✅ **Streaming RTSP funcional** con cámaras Dahua
- ✅ **WebSocket estable** con heartbeat automático
- ✅ **Métricas en vivo**: FPS, latencia y tiempo de conexión
- ✅ **Interfaz pulida** con área de video limpia
- ✅ **Manejo robusto de errores** con reintentos automáticos

## ✨ Características Principales

### 🎥 Streaming de Video
- **Tiempo real**: Transmisión fluida vía WebSocket con base64 encoding
- **Multi-protocolo**: ONVIF, RTSP, HTTP/CGI
- **Alto rendimiento**: 13-15 FPS @ 2880x1620, < 300MB RAM
- **Reconexión automática**: Sistema inteligente de recuperación

### 📷 Compatibilidad de Cámaras
- **Dahua**: Probado con modelos Hero-K51H (RTSP puerto 554)
- **TP-Link**: Soporte ONVIF (puerto 2020)
- **Steren**: Compatible con ONVIF (puerto 8000)
- **Genéricas**: Auto-detección con 16+ patrones RTSP

### 🖥️ Interfaz Moderna
- **React + Material-UI**: Diseño responsivo y elegante
- **Tema claro/oscuro**: Persistente en localStorage
- **Grid de cámaras**: Vista optimizada para múltiples streams
- **Controles intuitivos**: Conexión con un click

## 🚀 Inicio Rápido

### Requisitos Previos

```bash
# Python 3.8+
python --version

# Node.js 18+ y Yarn
node --version
npm install -g yarn  # IMPORTANTE: Usar yarn, no npm

# Para build nativo (opcional)
# Rust con MSVC en Windows
# https://www.rust-lang.org/tools/install
```

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/JorgeTato99/universal-camera-viewer.git
cd universal-camera-viewer

# Frontend React
yarn install         # IMPORTANTE: Usar yarn, NO npm

# Backend FastAPI
pip install -r requirements.txt
```

### Ejecución

```bash
# Terminal 1 - Backend FastAPI
python run_api.py
# API en http://localhost:8000
# Docs en http://localhost:8000/docs

# Terminal 2 - Frontend React
yarn dev
# UI en http://localhost:5173

# Opcional: App nativa con Tauri
yarn tauri-dev      # Desarrollo con hot reload
yarn tauri-build    # Genera instalador .exe/.msi
```

## 📁 Estructura del Proyecto

```
├── src/              # Frontend React/TypeScript
│   ├── features/     # Componentes por funcionalidad
│   │   ├── cameras/  # Gestión de cámaras
│   │   └── streaming/# Reproductor de video
│   └── services/     # Comunicación WebSocket
├── src-python/       # Backend FastAPI + Python
│   ├── websocket/    # Handlers de streaming
│   ├── presenters/   # Lógica MVP
│   └── services/     # RTSP, ONVIF, Video
├── src-tauri/        # Wrapper nativo (opcional)
└── docs/             # Documentación detallada
```

## 🔧 Configuración

### Configuración Básica

Las cámaras se pueden configurar directamente desde la interfaz o mediante archivo `.env`:

```env
# Ejemplo para Dahua
DAHUA_IP=192.168.1.172
DAHUA_USER=admin
DAHUA_PASSWORD=tu_password
DAHUA_RTSP_PORT=554

# URLs RTSP por marca
# Dahua: rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0
# TP-Link: rtsp://user:pass@ip:554/stream1
# Hikvision: rtsp://user:pass@ip:554/Streaming/Channels/101
```

### Puertos Comunes

| Marca | RTSP | ONVIF | HTTP |
|-------|------|-------|------|
| Dahua | 554  | 80    | 80   |
| TP-Link | 554 | 2020  | 80   |
| Steren | 5543 | 8000  | 80   |

## 📚 Documentación

- [Estado actual del proyecto](CURRENT_STATUS.md) - ⭐ Ver detalles del streaming funcional
- [Características detalladas](docs/FEATURES.md)
- [Arquitectura técnica](docs/ARCHITECTURE.md)
- [Compatibilidad de cámaras](docs/CAMERA_COMPATIBILITY.md)
- [Configuración Windows](docs/WINDOWS_SETUP.md)
- [Protocolo WebSocket](CURRENT_STATUS.md#-protocolo-websocket)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Distribuido bajo licencia MIT. Ver `LICENSE` para más información.

## 🎯 Próximos Pasos

- [ ] Soporte para múltiples cámaras simultáneas
- [ ] Grabación de video local
- [ ] Detección de movimiento
- [ ] Control PTZ para cámaras móviles
- [ ] Integración con servicios cloud

## 📈 Rendimiento

- **FPS**: 13-15 (limitado por cámara fuente)
- **Latencia**: < 200ms end-to-end
- **CPU**: ~10-15% con streaming activo
- **RAM**: < 300MB por stream
- **Red**: 2-4 Mbps por cámara HD

## 👥 Autor

**Jorge Tato** - [@JorgeTato99](https://github.com/JorgeTato99)

---

> ⚠️ **Notas importantes**:
> - En Windows, usar siempre `yarn` en lugar de `npm` debido a un bug con dependencias nativas
> - El streaming requiere que el backend FastAPI esté ejecutándose en `http://localhost:8000`
> - Para cámaras Dahua, usar la ruta RTSP específica: `/cam/realmonitor?channel=1&subtype=0`