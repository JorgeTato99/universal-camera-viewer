# 🎥 Universal Camera Viewer

[![Version](https://img.shields.io/badge/version-0.8.0-blue)](https://github.com/JorgeTato99/universal-camera-viewer)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-61dafb)](https://react.dev/)
[![Tauri](https://img.shields.io/badge/tauri-2.0-ffc131)](https://tauri.app/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)

Sistema profesional de videovigilancia para cámaras IP multi-marca con interfaz nativa moderna.

## ✨ Características

- 📷 **Multi-marca**: Dahua, TP-Link, Steren, cámaras genéricas
- 🔌 **Multi-protocolo**: ONVIF, RTSP, HTTP/CGI
- 🎯 **Auto-detección**: Descubrimiento automático de cámaras en red
- 🖥️ **Interfaz nativa**: Aplicación desktop con Tauri + React
- 📊 **Alto rendimiento**: 13-20+ FPS, < 200MB RAM, < 15% CPU

## 🚀 Inicio Rápido

### Requisitos Previos

```bash
# Windows: Rust con MSVC (NO GNU)
# https://www.rust-lang.org/tools/install

# Yarn (requerido por bug de npm)
npm install -g yarn

# Python 3.8+
python --version
```

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/JorgeTato99/universal-camera-viewer.git
cd universal-camera-viewer

# Frontend
yarn install         # IMPORTANTE: Usar yarn, NO npm

# Backend Python
pip install -r requirements.txt
```

### Ejecución

```bash
# Desarrollo completo
yarn tauri-dev      # App completa con hot reload

# Solo frontend
yarn dev            # http://localhost:5173

# Build producción
yarn tauri-build    # Genera instalador nativo
```

## 📁 Estructura del Proyecto

```
├── src/              # Frontend React/TypeScript
├── src-python/       # Backend Python (MVP)
├── src-tauri/        # Core Rust/Tauri
├── scripts/          # Utilidades y comunicación IPC
└── docs/             # Documentación detallada
```

## 🔧 Configuración

Crear archivo `.env` con las credenciales de tus cámaras:

```env
# Ejemplo para Dahua
DAHUA_IP=192.168.1.172
DAHUA_USER=admin
DAHUA_PASSWORD=tu_password

# Ver más ejemplos en .env.example
```

## 📚 Documentación

- [Características detalladas](docs/FEATURES.md)
- [Arquitectura técnica](docs/ARCHITECTURE.md)
- [Compatibilidad de cámaras](docs/CAMERA_COMPATIBILITY.md)
- [Configuración Windows](docs/WINDOWS_SETUP.md)
- [Estado del proyecto](CURRENT_STATUS.md)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Distribuido bajo licencia MIT. Ver `LICENSE` para más información.

## 👥 Autor

**Jorge Tato** - [@JorgeTato99](https://github.com/JorgeTato99)

---

⚠️ **Nota importante**: En Windows, usar siempre `yarn` en lugar de `npm` debido a un bug con dependencias nativas.