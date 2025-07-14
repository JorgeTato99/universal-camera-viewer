# 📊 Estado Actual del Proyecto - v0.8.0 (Enero 2025)

> **Documento técnico consolidado** - Estado actual de la migración a Tauri, arquitectura, componentes implementados y roadmap.

![Estado](https://img.shields.io/badge/Estado-Migración%20Tauri%20Iniciada-orange)
![Backend](https://img.shields.io/badge/Backend%20Python-95%25%20Completo-brightgreen)
![Frontend](https://img.shields.io/badge/Frontend%20React-En%20Desarrollo-yellow)
![Versión](https://img.shields.io/badge/Versión-0.8.0-blue)

---

## 🎯 **Resumen Ejecutivo**

### **🚀 Migración Mayor: Flet → Tauri (v0.8.0)**

**Cambio Fundamental**: Transición de Flet a **Tauri** para aplicación nativa con mejor rendimiento

- 🔄 **Frontend**: De Flet (Python) → React + TypeScript + Material-UI
- ✅ **Backend**: Python MVP mantenido → Comunicación vía Tauri IPC
- 📁 **Estructura**: Reorganizada con `src-python/` y `src/`
- 🧰 **Tooling**: Yarn obligatorio (bug npm), Rust MSVC requerido

### **📊 Estado de Componentes**

| Componente | Estado | Completitud | Detalles |
|------------|--------|-------------|----------|
| **Backend Python** | ✅ Funcional | 95% | Falta 20% presenters |
| **Arquitectura MVP** | ✅ Implementada | 95% | Services completos |
| **Video Streaming** | ✅ Backend listo | 100% | VideoStreamService implementado |
| **Frontend React** | 🚧 En desarrollo | 5% | Estructura inicial |
| **Comunicación IPC** | 📝 Diseñada | 0% | Scripts creados, no integrados |
| **UI Components** | 🔄 Migrando | 0% | De Flet a React |

---

## 📁 **Estructura del Proyecto (v0.8.0)**

```
universal-camera-viewer/
├── src/                    # Frontend React/TypeScript (NEW)
│   ├── App.tsx            # Componente principal React
│   ├── main.tsx           # Punto de entrada React
│   └── [components...]    # Por implementar
│
├── src-python/            # Backend Python (MOVED from src/)
│   ├── main.py           # Legacy Flet (referencia)
│   ├── models/           # ✅ Modelos completos + StreamModel
│   ├── views/            # Legacy Flet UI (referencia solamente)
│   ├── presenters/       # 🚧 20% completo
│   ├── services/         # ✅ Completo + VideoStreamService
│   │   └── video/        # ✅ Streaming implementado
│   ├── protocol_handlers/# ✅ ONVIF, RTSP funcionales
│   └── utils/            # ✅ Utilidades + FrameConverter
│
├── src-tauri/            # Aplicación Rust/Tauri
│   ├── tauri.conf.json   # Configurado puerto 5173
│   └── Cargo.toml        # Dependencias Rust
│
├── scripts/              # Comunicación Python-Tauri
│   ├── python_sidecar.py # IPC via stdin/stdout
│   └── start_python_backend.py # Backend HTTP alternativo
│
└── docs/                 # Documentación actualizada
    └── WINDOWS_SETUP.md  # Guía específica Windows
```

---

## 🏗️ **Arquitectura Actual**

### **Frontend (React + Tauri) - EN DESARROLLO**

- **Framework**: React 19 + TypeScript
- **UI Library**: Material-UI v7
- **State Management**: Zustand (planeado)
- **Build Tool**: Vite (puerto 5173)
- **Native Wrapper**: Tauri v2

### **Backend (Python MVP) - 95% COMPLETO**

- **Arquitectura**: Model-View-Presenter (MVP)
- **Async**: asyncio para todas las operaciones I/O
- **Protocolos**: ONVIF, RTSP, HTTP/CGI funcionales
- **Video**: OpenCV + conversión base64
- **Patrones Implementados**:
  - ✅ Singleton: `VideoStreamService`
  - ✅ Factory: `StreamManagerFactory`
  - ✅ Strategy: `FrameConverter`
  - ✅ Template Method: `StreamManager`
  - 🚧 Observer: Presenters (20% completo)

### **Comunicación Frontend-Backend**

- **Diseño**: Tauri Command API + Python Sidecar
- **Protocolo**: JSON via stdin/stdout
- **Video**: Frames como base64 strings
- **Estado**: Scripts creados, integración pendiente

---

## 🔧 **Componentes Implementados vs Faltantes**

### ✅ **Implementado (Backend)**

#### 1. **Conexiones a Cámaras**

- `ConnectionService` - Gestión de conexiones
- `ProtocolService` - ONVIF, RTSP, HTTP/CGI
- Handlers específicos por marca funcionando

#### 2. **Streaming de Video**

```python
# Nuevos componentes v0.8.0:
src-python/
├── services/video/
│   ├── video_stream_service.py    # ✅ Singleton service
│   └── stream_managers/
│       ├── base_stream_manager.py  # ✅ Template method
│       ├── rtsp_stream_manager.py  # ✅ RTSP implementation
│       └── onvif_stream_manager.py # ✅ ONVIF implementation
├── utils/video/
│   └── frame_converter.py          # ✅ OpenCV → base64
└── models/streaming/
    ├── stream_model.py             # ✅ Estado del stream
    └── frame_model.py              # ✅ Datos del frame
```

#### 3. **Presenters Adaptados**

- `VideoStreamPresenter` - Emite eventos Tauri
- `CameraPresenter` - Integra streaming (parcial)

### ❌ **Faltante (Frontend + Integración)**

#### 1. **UI React Components**

```typescript
// Por implementar:
src/
├── components/
│   ├── Camera/
│   │   ├── CameraView.tsx        // Widget de video
│   │   ├── CameraGrid.tsx        // Grid de cámaras
│   │   └── VideoPlayer.tsx       // Display de frames
│   ├── Controls/
│   │   └── ConnectionPanel.tsx   // Panel de control
│   └── Layout/
│       └── MainLayout.tsx        // Layout principal
```

#### 2. **Integración Tauri**

- Configurar sidecar Python en `tauri.conf.json`
- Implementar comandos Tauri en Rust
- Conectar eventos bidireccionales
- Sistema de actualización de frames

#### 3. **Presenters Faltantes (80%)**

```python
# Por completar en src-python/presenters/:
├── base/
│   ├── base_presenter.py      # Clase base
│   └── presenter_interface.py # Protocolo
├── main_presenter.py          # Coordinador principal
├── scan_presenter.py          # Discovery/escaneo
└── settings_presenter.py      # Configuración
```

---

## 🚀 **Comandos de Desarrollo**

### **Requisitos Previos (Windows)**

```bash
# 1. Rust con MSVC (NO GNU)
# Descargar: https://www.rust-lang.org/tools/install
# Seleccionar: stable-x86_64-pc-windows-msvc

# 2. Yarn (obligatorio por bug npm)
npm install -g yarn

# 3. Python 3.8+
python --version
```

### **Instalación**

```bash
# Frontend - USAR YARN
yarn install         # NO usar npm install

# Backend Python
cd src-python
pip install -r ../requirements.txt
```

### **Ejecución**

```bash
# Desarrollo completo
yarn tauri-dev      # Frontend + Rust + Python sidecar

# Solo frontend
yarn dev            # http://localhost:5173

# Solo backend Python (legacy Flet)
python run_python.py

# Build producción
yarn tauri-build    # Genera .exe/.msi
```

---

## 📊 **Métricas y Performance**

### **Backend Performance** (Sin cambios)

- **FPS**: 13-20+ según marca de cámara
- **RAM**: < 200MB para 4 cámaras
- **CPU**: < 15% streaming activo
- **Latencia**: 89-210ms según protocolo

### **Marcas Probadas**

| Marca | Modelo | Protocolo | Estado |
|-------|--------|-----------|--------|
| Dahua | Hero-K51H | ONVIF/RTSP | ✅ Funcional |
| TP-Link | Tapo C520WS | ONVIF | ✅ Funcional |
| Steren | CCTV-235 | ONVIF | ✅ Funcional |
| Generic | 8MP WiFi | RTSP | ✅ Funcional |

---

## 🎯 **Roadmap de Desarrollo**

### **Fase 1: Completar Migración Base** (En progreso)

- [x] Reorganizar estructura del proyecto
- [x] Implementar servicios de streaming
- [x] Adaptar presenters para Tauri
- [ ] Configurar Python sidecar
- [ ] Crear componentes React básicos
- [ ] Implementar comunicación IPC

### **Fase 2: UI Funcional**

- [ ] Migrar diseño Material de Flet a React
- [ ] Implementar grid de cámaras
- [ ] Sistema de visualización de video
- [ ] Panel de control y configuración

### **Fase 3: Features Avanzadas**

- [ ] Completar presenters (80% restante)
- [ ] Analytics con DuckDB
- [ ] Sistema de grabación
- [ ] Detección de movimiento

### **Fase 4: Producción**

- [ ] Suite de testing completa
- [ ] Optimización de performance
- [ ] Empaquetado multiplataforma
- [ ] Sistema de actualizaciones

---

## ⚠️ **Consideraciones Importantes**

### **Bug de NPM en Windows**

```bash
# NPM NO instala estas dependencias:
@tauri-apps/cli-win32-x64-msvc
@rollup/rollup-win32-x64-msvc

# SOLUCIÓN: Usar Yarn siempre
yarn install  # ✅ Correcto
npm install   # ❌ Fallará
```

### **Paths Actualizados**

```python
# Viejo (pre v0.8.0)
from src.models.camera_model import CameraModel  # ❌

# Nuevo (v0.8.0+)
from models.camera_model import CameraModel      # ✅
# O con path completo:
sys.path.append('src-python')
```

### **Estado de Componentes Legacy**

- `src-python/views/` - Solo referencia, no usar
- `src-python/main.py` - Flet app, solo para testing
- Toda la lógica de negocio es reutilizable

---

## 📝 **Para el Siguiente Desarrollador**

### **Prioridades Inmediatas**

1. **Configurar Python sidecar** en Tauri
2. **Crear VideoPlayer.tsx** que reciba frames base64
3. **Implementar comando Tauri** para start_stream
4. **Conectar** VideoStreamPresenter con frontend

### **Archivos Clave para Revisar**

```
src-python/services/video/video_stream_service.py  # Lógica streaming
src-python/presenters/streaming/                   # Presenters adaptados
scripts/python_sidecar.py                         # Comunicación IPC
src-tauri/tauri.conf.json                        # Configuración
```

### **Decisiones Técnicas Tomadas**

1. **Yarn sobre NPM**: Bug crítico en Windows
2. **Base64 para frames**: Simplicidad sobre WebRTC
3. **Sidecar sobre API HTTP**: Menor latencia
4. **MVP mantenido**: Backend Python sin cambios mayores

---

> **Estado: Migración a Tauri iniciada - Backend listo, Frontend pendiente**  
> **Versión: 0.8.0 - Breaking changes en estructura**  
> **Última actualización: Enero 2025**
