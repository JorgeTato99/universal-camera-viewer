# 📚 Documentación - Universal Camera Viewer

> **Sistema Profesional de Videovigilancia IP v0.9.5**  
> Stack: FastAPI + React + WebSocket | Base de Datos: SQLite 3FN

## 🗂️ Índice de Documentación

### 📋 Guías de Inicio Rápido

1. **[🚀 Instalación y Setup](installation.md)**  
   *Requisitos, dependencias y configuración inicial*

2. **[🪟 Configuración Windows](windows-setup.md)**  
   *Guía específica para desarrollo en Windows*

3. **[💻 Guía de Desarrollo](development.md)**  
   *Comandos, workflow y mejores prácticas*

### 🏗️ Arquitectura y Diseño

4. **[🏛️ Arquitectura del Sistema](architecture.md)**  
   *FastAPI + React, WebSocket streaming, patrón MVP*

5. **[🗄️ Esquema de Base de Datos](database-schema.md)**  
   *Diseño 3FN, 16 tablas normalizadas, encriptación*

6. **[🎨 Diseño de Interfaz](ui-design.md)**  
   *Material-UI, componentes React, sistema de diseño*

### 📷 Cámaras y Protocolos

7. **[📷 Compatibilidad de Cámaras](camera-compatibility.md)**  
   *Marcas soportadas, configuración específica*

8. **[🔌 Protocolos de Comunicación](camera-protocols.md)**  
   *ONVIF, RTSP, HTTP/CGI - Detalles técnicos*

### 🚀 API y Deployment

9. **[📡 API REST y WebSocket](api-services.md)**  
   *Endpoints, autenticación, streaming*

10. **[✨ Características del Sistema](features.md)**  
    *Funcionalidades completas y roadmap*

11. **[📦 Deployment y Distribución](deployment.md)**  
    *Docker, instaladores, configuración producción*

---

## 📊 Estado de la Documentación

| Documento | Estado | Última Actualización | Descripción |
|-----------|--------|---------------------|-------------|
| installation.md | ✅ | v0.9.5 | Instalación con Yarn y FastAPI |
| windows-setup.md | ✅ | v0.9.5 | Desarrollo en Windows |
| development.md | ✅ | v0.9.5 | Comandos y workflow actual |
| architecture.md | ✅ | v0.9.5 | Arquitectura FastAPI + WebSocket |
| database-schema.md | ✅ | v0.9.5 | Esquema 3FN completo |
| ui-design.md | ✅ | v0.9.0 | React + Material-UI |
| camera-compatibility.md | ✅ | v0.9.0 | Cámaras testeadas |
| camera-protocols.md | ✅ | v0.9.0 | Protocolos implementados |
| api-services.md | ✅ | v0.9.3 | API v2 documentada |
| features.md | ✅ | v0.9.3 | Características actuales |
| deployment.md | ✅ | v0.9.5 | Deploy con Docker |

---

## 🎯 Quick Links

### 🚀 Inicio Rápido

```bash
# Backend
python run_api.py

# Frontend (nueva terminal)
yarn dev
```

- **[📋 Guía Completa](installation.md)** - Instalación paso a paso
- **[🐛 Problemas Windows](windows-setup.md#problemas-comunes)** - Yarn vs NPM
- **[🔧 Base de Datos](database-schema.md#gestión-de-base-de-datos)** - Comandos de BD

### 📚 Documentación Clave

- **[🏗️ Arquitectura WebSocket](architecture.md#websocket-streaming)** - Streaming en tiempo real
- **[🗄️ Estructura 3FN](database-schema.md#tablas-principales)** - 16 tablas normalizadas
- **[📷 Configurar Cámaras](camera-compatibility.md#configuración-por-marca)** - Dahua, TP-Link, etc.

---

## 🆘 Ayuda Rápida

### Errores Comunes

#### **Error: Cannot find module (Windows)**

```bash
# Solución: Usar Yarn en lugar de NPM
yarn install
```

[Más detalles →](windows-setup.md#problemas-comunes)

#### **Error: ONVIF Authentication Failed**

```bash
# Recrear BD con credenciales correctas
python src-python/seed_database.py --clear
```

[Configuración de cámaras →](camera-compatibility.md#credenciales)

#### **Error: Multiple encryption keys**

```bash
# La clave debe estar en:
data/.encryption_key
```

[Seguridad →](database-schema.md#ubicación-y-seguridad)

---

## 🎯 Estado del Proyecto

### ✅ Funcional en v0.9.5

- **Streaming WebSocket** en tiempo real con cámaras Dahua
- **Base de datos 3FN** con encriptación AES-256
- **Frontend React** con Material-UI
- **API REST + WebSocket** con FastAPI
- **Métricas en vivo**: FPS, latencia, uptime

### 🔄 En Desarrollo

- Soporte multi-cámara simultáneo
- Grabación local de video
- Detección de movimiento
- Control PTZ

---

**📅 Última actualización:** 16 Julio 2025  
**🏷️ Versión actual:** 0.9.5  
**📍 Estado**: Sistema en producción con streaming funcional
