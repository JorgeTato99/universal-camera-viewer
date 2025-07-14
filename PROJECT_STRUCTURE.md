# Estructura del Proyecto - Universal Camera Viewer

## 📁 Organización de Directorios

```
universal-camera-viewer/
├── src/                    # Frontend React/TypeScript (Tauri)
│   ├── App.tsx            # Componente principal React
│   ├── main.tsx           # Punto de entrada React
│   ├── App.css            # Estilos de la aplicación
│   └── index.css          # Estilos globales
│
├── src-python/            # Backend Python (MVP Architecture)
│   ├── main.py           # Punto de entrada Python (legacy Flet)
│   ├── models/           # Capa de modelos MVP
│   ├── views/            # Capa de vistas (legacy Flet, referencia)
│   ├── presenters/       # Capa de presentadores MVP
│   ├── services/         # Servicios de negocio
│   ├── protocol_handlers/# Manejadores de protocolos (ONVIF, RTSP)
│   └── utils/            # Utilidades y helpers
│
├── src-tauri/            # Configuración y código Rust de Tauri
│   ├── tauri.conf.json   # Configuración de Tauri
│   ├── Cargo.toml        # Dependencias Rust
│   └── src/              # Código Rust
│
├── scripts/              # Scripts auxiliares
│   ├── python_sidecar.py # Sidecar Python para Tauri
│   └── start_python_backend.py # Backend HTTP alternativo
│
├── examples/             # Ejemplos y demos
├── tests/               # Pruebas unitarias e integración
├── docs/                # Documentación del proyecto
└── .cursor/rules/       # Reglas de desarrollo Cursor
```

## 🏗️ Arquitectura

### Frontend (React + Tauri)
- **Framework**: React 19 con TypeScript
- **UI Library**: Material-UI v7
- **State Management**: Zustand
- **Routing**: React Router DOM v7
- **Build Tool**: Vite

### Backend (Python MVP)
- **Arquitectura**: Model-View-Presenter (MVP)
- **Async**: asyncio para operaciones I/O
- **Protocolos**: ONVIF, RTSP, HTTP/CGI
- **Video**: OpenCV para procesamiento
- **Patrones de Diseño**:
  - Singleton: VideoStreamService
  - Factory: StreamManagerFactory
  - Strategy: FrameConverter
  - Observer: Presenters

### Comunicación Frontend-Backend
- **IPC**: Tauri Command API
- **Sidecar**: Proceso Python comunicándose via JSON
- **Eventos**: Sistema de eventos bidireccional
- **Streaming**: Base64 encoding de frames

## 🚀 Comandos de Desarrollo

### Requisitos Previos (Windows)
```bash
# Instalar Rust con MSVC toolchain
# Descargar desde: https://www.rust-lang.org/tools/install
# Seleccionar: stable-x86_64-pc-windows-msvc

# Instalar Yarn (requerido por bug de npm con opcionales nativos)
npm install -g yarn
```

### Frontend (React/Tauri)
```bash
# Instalar dependencias con Yarn
yarn install         # Instala correctamente @tauri-apps/cli-win32-x64-msvc

# Desarrollo con hot reload
yarn dev             # Vite en puerto 5173

# Desarrollo Tauri (frontend + backend Rust)
yarn tauri-dev       # Frontend + Rust, puerto unificado 5173

# Build de producción
yarn tauri-build
```

### Backend (Python)
```bash
# Ejecutar backend Python standalone
python run_python.py

# Ejecutar sidecar para Tauri
python scripts/python_sidecar.py

# Ejecutar con Make
make run
```

### Desarrollo Completo
```bash
# Instalar dependencias
yarn install         # Frontend (respeta opcionales nativos)
make install-dev     # Backend Python

# Ejecutar aplicación completa
yarn tauri-dev       # Inicia Tauri + React + Python sidecar
```

### ⚠️ Nota sobre NPM vs Yarn
NPM tiene un bug que no instala dependencias opcionales nativas en Windows:
- `@tauri-apps/cli-win32-x64-msvc`
- `@rollup/rollup-win32-x64-msvc`

Por esto usamos **Yarn** que sí las instala correctamente.

## 📝 Migración en Progreso

### Estado Actual
- ✅ Backend Python 95% completo (falta 20% de presenters)
- ✅ Arquitectura MVP implementada
- ✅ Servicios de streaming implementados
- 🚧 Migración de Flet a Tauri en progreso
- 🚧 Frontend React en desarrollo inicial

### Próximos Pasos
1. Completar implementación de presentadores
2. Configurar sidecar Python en Tauri
3. Implementar UI React siguiendo diseño Material 3
4. Integrar comunicación IPC frontend-backend
5. Migrar funcionalidades de Flet a React

## 🔧 Configuración de Desarrollo

### VS Code / Cursor
1. Abrir carpeta raíz del proyecto
2. Las reglas de desarrollo en `.cursor/rules/` se aplican automáticamente
3. Configuración Python: apunta a `src-python/`
4. Configuración TypeScript: apunta a `src/`

### Variables de Entorno
```bash
# Backend Python
PYTHONPATH=./src-python

# Tauri (si es necesario)
TAURI_SKIP_DEVSERVER_CHECK=true
```

## 📚 Documentación Adicional
- [README.md](README.md) - Información general del proyecto
- [CLAUDE.md](CLAUDE.md) - Guía para Claude Code
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios
- [.cursor/rules/](/.cursor/rules/) - Reglas de arquitectura y estilo