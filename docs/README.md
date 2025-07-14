# 📚 Documentación - Universal Camera Viewer

> **Visor Universal de Cámaras Multi-Marca v0.8.0**  
> Stack: Tauri + React + Python | Arquitectura: MVP Pattern

## 🗂️ Índice de Documentación

### Orden de Lectura Recomendado

1. **[🚀 Instalación y Setup](installation.md)**  
   *Configuración inicial, dependencias y primer arranque*

2. **[🪟 Configuración Windows](WINDOWS_SETUP.md)**  
   *Guía específica para Windows, Rust MSVC y solución bug NPM*

3. **[💻 Guía de Desarrollo](development.md)**  
   *Workflow de desarrollo, comandos y mejores prácticas*

4. **[🏛️ Arquitectura Técnica](ARCHITECTURE.md)**  
   *Arquitectura MVP, patrones de diseño y comunicación Tauri*

5. **[✨ Características Detalladas](FEATURES.md)**  
   *Funcionalidades completas, UI/UX y herramientas*

6. **[🎨 Diseño de Interfaz](ui-design.md)**  
   *Material Design 3, componentes y sistema de diseño*

7. **[📷 Compatibilidad de Cámaras](CAMERA_COMPATIBILITY.md)**  
   *Marcas soportadas, configuración y troubleshooting*

8. **[🔌 Protocolos de Cámara](camera-protocols.md)**  
   *ONVIF, RTSP, HTTP/CGI - Implementación técnica*

9. **[📡 API y Servicios](api-services.md)**  
   *Documentación de servicios internos y APIs*

10. **[📦 Deployment y Distribución](deployment.md)**  
    *Build, empaquetado y distribución multiplataforma*

---

## 📊 Estado de la Documentación

| Documento | Actualizado | Versión | Estado |
|-----------|-------------|---------|--------|
| installation.md | ⚠️ | 0.7.0 | Necesita actualización Tauri |
| WINDOWS_SETUP.md | ✅ | 0.8.0 | Actualizado |
| development.md | ⚠️ | 0.7.0 | Necesita comandos Yarn |
| ARCHITECTURE.md | ✅ | 0.8.0 | Actualizado |
| FEATURES.md | ✅ | 0.8.0 | Actualizado |
| ui-design.md | ⚠️ | 0.7.0 | Referencias Flet, migrar React |
| CAMERA_COMPATIBILITY.md | ✅ | 0.8.0 | Actualizado |
| camera-protocols.md | ✅ | 0.7.0 | Válido, sin cambios |
| api-services.md | ✅ | 0.7.0 | Válido, sin cambios |
| deployment.md | ❌ | 0.7.0 | Necesita reescribir para Tauri |

---

## 🎯 Quick Links

### Para Empezar

- **[⚡ Inicio Rápido](installation.md#quick-start)** - Ejecutar en 5 minutos
- **[🐛 Solución Bug NPM](WINDOWS_SETUP.md#bug-crítico-de-npm-en-windows)** - Usar Yarn obligatorio
- **[🔧 Comandos Básicos](development.md#comandos-principales)** - yarn tauri-dev

### Arquitectura

- **[🏗️ Patrón MVP](ARCHITECTURE.md#arquitectura-mvp-model-view-presenter)** - Entender la estructura
- **[🔄 Comunicación IPC](ARCHITECTURE.md#comunicación-frontend-backend-tauri)** - React ↔ Python
- **[📐 Patrones de Diseño](ARCHITECTURE.md#patrones-de-diseño-implementados)** - Singleton, Factory, etc.

### Cámaras

- **[📷 Marcas Soportadas](CAMERA_COMPATIBILITY.md#marcas-soportadas-y-testadas)** - Dahua, TP-Link, Steren
- **[🔧 Configuración Rápida](CAMERA_COMPATIBILITY.md#configuración-por-marca)** - Por marca
- **[🚨 Troubleshooting](CAMERA_COMPATIBILITY.md#solución-de-problemas)** - Problemas comunes

---

## 🆘 Ayuda Rápida

### Errores Comunes

#### **Error: Cannot find module '@tauri-apps/cli-win32-x64-msvc'**

- Ver: [Bug NPM Windows](WINDOWS_SETUP.md#el-problema)
- Solución: Usar `yarn install` en lugar de `npm install`

#### **Error: Microsoft Visual C++ 14.0 or greater is required**

- Ver: [Requisitos Rust](WINDOWS_SETUP.md#1-rust--msvc-toolchain)
- Solución: Instalar Visual Studio Build Tools

#### **Cámara no conecta**

- Ver: [Troubleshooting Cámaras](CAMERA_COMPATIBILITY.md#solución-de-problemas)
- Verificar: Puerto correcto según marca

---

## 📝 Notas de Migración v0.8.0

### Cambios Principales

- 🔄 **Frontend**: Flet → React + TypeScript
- 📁 **Estructura**: Python movido a `src-python/`
- 🚀 **Framework**: Tauri para aplicación nativa
- 📦 **Dependencias**: Yarn obligatorio (bug npm)

### Documentos por Actualizar

1. `installation.md` - Agregar pasos Tauri/Yarn
2. `development.md` - Cambiar npm → yarn
3. `ui-design.md` - Migrar ejemplos a React
4. `deployment.md` - Reescribir para Tauri

---

**📅 Última actualización:** Enero 2025  
**🏷️ Versión documentada:** 0.8.0  
**📍 Estado**: Migración a Tauri en progreso
