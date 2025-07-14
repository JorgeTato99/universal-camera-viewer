# Changelog

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionado Semántico](https://semver.org/spec/v2.0.0.html).

---

## [0.8.2] - 2025-07-14

### ✨ Added - Frontend React Implementation

- **Frontend React completo** con estructura profesional:
  - **Design System** con tokens, temas light/dark, colores para estados de cámaras
  - **Material-UI v5** personalizado con tema extendido
  - **Zustand stores** para gestión de estado (cameras, streaming, scanner, notifications)
  - **TauriService** completo con todos los comandos IPC
  - **Páginas principales** implementadas (Cameras, Streaming, Scanner, Settings, Analytics)
  - **Layout responsivo** con Sidebar, TopBar y MainLayout
  - **TypeScript estricto** con tipos completos para toda la aplicación

- **Arquitectura frontend organizada**:
  - `/design-system` - Tokens de diseño y configuración de tema
  - `/stores` - Estado global con Zustand
  - `/services` - Servicios Tauri y API
  - `/features` - Módulos de funcionalidad por página
  - `/components` - Componentes reutilizables UI

### 📚 Documentation - Complete Update

- **Todos los docs actualizados a v0.8.0**:
  - `installation.md` - Instrucciones con Yarn y requisitos Tauri
  - `development.md` - Flujo de trabajo React/TypeScript
  - `ui-design.md` - Migrado completamente a React + Material-UI
  - `deployment.md` - Build process con Tauri y Python sidecar
  
- **Navegación mejorada** entre documentos con links
- **WINDOWS_SETUP.md** añadido a navegación principal
- **Estado de documentación** actualizado al 100%

### 🔄 Changed - Project Organization

- **Consolidación de documentos**:
  - `CURRENT_STATUS.md` unificado (elimina PROJECT_STRUCTURE.md y MISSING_COMPONENTS_ANALYSIS.md)
  - Incluye roadmap, arquitectura, y estado actual en un solo lugar
  
- **README.md simplificado**:
  - Reducido de ~500 a ~110 líneas
  - Información detallada movida a `/docs`
  - Enlaces claros a documentación específica

### 🛠️ Fixed - Build Configuration

- **Tauri capabilities** configurado correctamente
- **Cargo.toml** con metadata del proyecto
- **GitHub Actions** actualizado para CI/CD con Yarn
- **PowerShell commands** en documentación para Windows

---

## [0.8.1] - 2025-07-14

### ✨ Added - Video Streaming Architecture

- **Sistema completo de streaming de video**:
  - `StreamModel` y `FrameModel` para gestión de estado
  - `VideoStreamService` (Singleton) para gestión centralizada
  - `StreamManager` con Template Method y Factory patterns
  - `RTSPStreamManager` y `ONVIFStreamManager` implementaciones específicas
  - `FrameConverter` con Strategy pattern (JPEG/PNG/WebP)
  - `VideoStreamPresenter` adaptado para eventos Tauri

- **Integración con arquitectura existente**:
  - `CameraPresenter` actualizado con métodos de streaming
  - Emisión de eventos Tauri para frames de video
  - Gestión de recursos y cleanup automático
  - Manejo de errores y reconexión

### 🔄 Changed - Documentation Structure

- **Documentación reorganizada en `/docs`**:
  - `FEATURES.md` - Características detalladas
  - `ARCHITECTURE.md` - Detalles técnicos MVP
  - `CAMERA_COMPATIBILITY.md` - Guía de marcas y protocolos
  - `README.md` en docs con índice numerado

- **Nuevos archivos de estado**:
  - `CURRENT_STATUS.md` - Estado consolidado del proyecto
  - `UI_UX_DESIGN_GUIDE.md` - Guía de diseño para React

### 🛠️ Fixed - Project Structure

- **Separación clara Python/React**:
  - `src/` ahora solo contiene código React/TypeScript
  - `src-python/` contiene todo el backend Python
  - Evita mezcla de tecnologías en mismo directorio

- **Importaciones Python** actualizadas para nueva estructura
- **Scripts** ajustados para nueva organización

---

## [0.8.0] - 2025-07-14

### 🚀 Major Change - Migración de Flet a Tauri

Esta versión marca el inicio de la migración de Flet a Tauri para lograr una aplicación nativa con mejor rendimiento.

### ✨ Added - Nueva Arquitectura

- **Tauri Framework** integrado con React + TypeScript para el frontend
- **Estructura de proyecto reorganizada**:
  - `src/` - Frontend React/TypeScript
  - `src-python/` - Backend Python (movido desde `src/`)
  - `src-tauri/` - Aplicación Rust/Tauri
  - `scripts/` - Scripts auxiliares para comunicación Python-Tauri
- **VideoStreamService** (Singleton) para gestión centralizada de streams
- **StreamManager** con patrón Factory y Template Method
- **FrameConverter** con patrón Strategy para conversión de frames a base64
- **Python Sidecar** script para comunicación IPC con Tauri
- **Yarn** como gestor de paquetes (requerido por bug de npm en Windows)

### 🔄 Changed - Infraestructura

- **Frontend migrado** de Flet a React + Material-UI v7
- **Comunicación** cambiada a Tauri IPC en lugar de Flet events
- **VideoStreamPresenter** adaptado para emitir eventos Tauri
- **CameraPresenter** actualizado para integrar streaming de video
- **Puerto unificado** Vite configurado en 5173 (alineado con Tauri)
- **Makefile** actualizado con comandos para Yarn y Tauri
- **Documentación** actualizada para reflejar nueva estructura

### 🛠️ Fixed - Windows Development

- **Bug de npm** que no instala dependencias opcionales nativas:
  - `@tauri-apps/cli-win32-x64-msvc`
  - `@rollup/rollup-win32-x64-msvc`
- **Solución**: Migración obligatoria a Yarn que sí respeta opcionales
- **Rust toolchain** documentado: debe ser `stable-x86_64-pc-windows-msvc`

### 📚 Documentation

- **CLAUDE.md** actualizado con nueva estructura y comandos
- **PROJECT_STRUCTURE.md** creado con detalles de organización
- **WINDOWS_SETUP.md** creado con guía específica para Windows
- **README.md** actualizado con comandos de Yarn y requisitos

### ⚠️ Breaking Changes

- Comandos cambiados de `npm` a `yarn` (obligatorio)
- Python ahora en `src-python/` en lugar de `src/`
- Flet UI ya no es la interfaz principal (referencia solamente)

### 🔮 Next Steps

- Completar implementación de presentadores (80% restante)
- Implementar UI React siguiendo diseño Material de Flet
- Configurar sidecar Python en Tauri
- Implementar streaming de video en frontend React

---

## [0.7.4] - 2025-07-11

### ✨ Added - Timeout Management

- **Timeout agresivo** en conexiones ONVIF para evitar bloqueos
- **Timeouts escalonados** en operaciones de protocolo (3-5 segundos)
- **Manejo de TimeoutError** específico en ONVIFProtocolHandler
- **Cleanup automático** de conexiones residuales en ProtocolService

### 🔄 Changed - Error Handling

- **Método cleanup()** del ProtocolService para cierre ordenado de conexiones
- **Bloques finally** en test_error_handling para limpieza garantizada
- **Timeout configuration** en test_connection y connect methods
- **Resource management** mejorado con context managers async

### 🛠️ Fixed - Connection Issues

- **Error de timeout residual** en IP 192.168.1.100 durante garbage collection
- **Conexiones colgadas** que causaban delays al finalizar scripts
- **ProtocolService cleanup** incompleto que dejaba conexiones activas
- **Timeout None** en librería onvif-zeep que causaba bloqueos indefinidos

### 📊 Enhanced - Example Stability

- **onvif_example.py** con cierre limpio de servicios y conexiones
- **Error handling robusto** en pruebas de conexión con IPs inválidas
- **Logging mejorado** para debugging de timeouts y conexiones
- **Export functionality** estable sin errores de conexión residual

---

## [0.7.3] - 2025-07-10

### ✨ Added - Migración Completa a MVP Architecture

- **ProtocolService** completamente migrado a async/await con APIs modernas
- **ONVIF Protocol Handler** refactorizado con soporte completo para perfiles detallados
- **RTSP Protocol Handler** optimizado con detección automática de streams
- **Amcrest Protocol Handler** implementado con soporte para múltiples modelos
- **Base Protocol Handler** con abstracciones comunes y error handling robusto

### 🔄 Changed - Legacy API Migration

- **Eliminación completa** de APIs síncronas legacy (ConnectionFactory, get_protocol_service)
- **Migración de ejemplos** a nueva arquitectura MVP (camera_detector.py, network_analyzer.py)
- **Refactorización de imports** con fallbacks para compatibilidad
- **Actualización de dependencias** y eliminación de referencias obsoletas

### 🛠️ Fixed - Integration Issues

- **Import errors** corregidos en scan_service.py con fallbacks absolutos
- **Dependencies missing** resueltas (cv2, requests) con instalación automática
- **Residual references** eliminadas de get_protocol_service en todo el codebase
- **Logging inconsistencies** corregidas con niveles apropiados y mensajes detallados

### 📊 Enhanced - Testing & Diagnostics

- **camera_detector.py** completamente migrado a servicios MVP con logging detallado
- **network_analyzer.py** refactorizado para usar ScanService, ProtocolService, ConfigService
- **onvif_example.py** actualizado con input interactivo y exportación de perfiles detallados
- **Logging mejorado** con información de timing, performance y detalles técnicos

### 🎯 Technical Improvements

- **Async/await consistency** en todos los protocol handlers
- **Error handling** robusto con excepciones específicas del dominio
- **Type hints** completos en todos los servicios y handlers
- **Resource management** optimizado con context managers async
- **Export functionality** mejorada con datos estructurados y timestamps

### 📁 Project Structure

- **Gitignore actualizado** para ignorar archivos generados en `/exports` y `/logs`
- **Archivos .gitkeep** creados para mantener estructuras de carpetas
- **Código legacy** completamente eliminado (src_old/, camera_detector_simple.py)
- **Documentación** actualizada con ejemplos de uso de nueva API

---

## [0.7.2] - 2025-07-10

### ✨ Added - Sistema de Temas Completo

- **ThemeService** para gestión de temas claro/oscuro
- **Configuración Material Design 3** optimizada para ambos temas
- **Persistencia de tema** con archivos de configuración JSON
- **Sistema de notificaciones** para cambios de tema
- **ThemeToggle** component para cambio rápido de tema
- **ThemeSelector** component para configuración avanzada
- **Integración con NavigationBar** para acceso rápido

### 🏗️ Enhanced - Mejoras de Apariencia

- **Tema claro como predeterminado** con paleta mejorada
- **Mejor contraste de colores** y accesibilidad
- **Aplicación unificada** del tema en todos los componentes
- **Página de Configuración** completamente rediseñada
- **Panel de navegación** en configuración con secciones organizadas

### 🛠️ Fixed - Problemas de Tema

- **Aplicación incorrecta** del tema oscuro por defecto
- **Compatibilidad de colores** con framework Flet
- **Cambio dinámico** de tema con actualización instantánea
- **Persistencia** de preferencias de tema entre sesiones

### 📊 Technical

- **ThemeService** con configuraciones light/dark completas
- **Persistencia JSON** para configuraciones de usuario
- **Integración de componentes** con sistema de temas
- **Optimización MD3** para mejor experiencia visual

---

## [0.7.1] - 2025-07-10

### ✨ Added - Sistema de Componentes Completo

- **ModernToolbar** con Material Design 3 y acciones configurables
- **SidePanel/CollapsibleSidePanel** para navegación lateral moderna
- **CameraGrid/CameraCard** con estados dinámicos y controles de reproducción
- **StatusBar** especializada con métricas en tiempo real
- **Funciones helper** específicas para diferentes contextos de uso

### 🏗️ Enhanced - Arquitectura Modular

- **Estructura MVP** refactorizada al 100% - todos los TODOs completados
- **Componentes reutilizables** organizados en subcarpetas temáticas
- **Sistema de importaciones** limpio y escalable en `__init__.py`
- **Separación de responsabilidades** clara entre layout, common y navigation

### 🛠️ Fixed - Code Quality

- **Linting errors** corregidos en main_view_new.py y progress_indicator.py  
- **Type checking** robusto con `type: ignore` donde es necesario
- **Error handling** defensivo para compatibilidad entre versiones de Flet
- **Documentación** completa en todos los componentes nuevos

### 📊 Technical

- **600+ líneas** de componentes UI implementados
- **Material Design 3** consistente en toda la interfaz
- **Responsive design** adaptativo con grids flexibles
- **Estado management** local en cada componente

---

## [0.7.0] - 2025-07-10

### ✨ Added - UI Moderna Completa

- **Material Design 3** completamente implementado con Flet
- **ColorScheme profesional** con `color_scheme_seed` y paleta coherente
- **Tipografía jerárquica** Material 3 (Display/Headline/Title/Body)
- **Navegación moderna** con barra de herramientas elevada y shadows
- **Panel lateral rediseñado** con cards organizados y headers descriptivos
- **Estados interactivos** (hover, loading, pressed) en todos los componentes
- **Progress indicators** con animaciones y feedback visual avanzado
- **Status bar moderna** con iconos de estado y colores semánticos

### 🏗️ Changed - Arquitectura MVP

- **Estructura MVP** reorganizada (65% completado)
- **Model Layer** completamente separado y organizado
- **View Layer** migrado a Flet con componentes modernos
- **Infrastructure Layer** consolidado (config, logging, utils)

### 🛠️ Technical

- **Migración Flet**: De Tkinter a Python + Flutter rendering
- **Window sizing**: 1400x900 optimizado para desktop
- **Theme system**: Light/dark mode con colores dinámicos
- **Responsive layout**: Adaptativo a diferentes tamaños de pantalla

### 📊 Performance

- **Memory usage**: Optimizado <200MB con 4 cámaras activas
- **Startup time**: <3 segundos para aplicación completa
- **UI responsiveness**: Smooth 60fps en interacciones

---

## [0.6.0] - 2025-07-10

### 🚀 Added - Inicio Migración Flet

- **Flet framework** integración inicial
- **Estructura MVP** base implementada
- **Model layer** reorganizado con entities y services
- **Services layer** completo (config, connection, data, protocol, scan)

### 🔄 Changed - Reorganización Arquitectónica

- **Separación clara** entre Model, View y Presenter layers
- **Business logic** extraído de UI components
- **Service pattern** implementado para todas las operaciones

### 🛠️ Technical

- **Python 3.9+** requirement establecido
- **Dependencies** reorganizadas y actualizadas
- **Project structure** rediseñada para escalabilidad

---

## [0.5.0] - 2025-06-13 - Última Versión Tkinter Estable

### ✨ Added - Funcionalidad Completa Tkinter

- **UX v0.2.0** optimizada con mejoras de usabilidad
- **Shortcuts de teclado** completos (F1-F9, Ctrl+combinations)
- **Métricas en tiempo real** (FPS, latencia, uptime, memoria)
- **Port Discovery** avanzado con validación en tiempo real
- **Sistema de layouts** inteligente (1x1 hasta 4x3)
- **Menú contextual** (click derecho) con opciones rápidas

### 🎨 Enhanced - Interfaz UX

- **Iconos modernos** en todos los botones y controles
- **Tooltips informativos** en elementos interactivos
- **Colores adaptativos** según estado de conexión
- **Feedback visual inmediato** para todas las acciones
- **Sistema de pestañas** organizado (Cámaras, Layout, Config, Discovery)

### 📊 Performance

- **Threading optimizado** para multiple camera streams
- **Memory management** mejorado (< 200MB con 4 cámaras)
- **CPU usage** optimizado (< 15% durante streaming)
- **Reconnection logic** automático (< 2 segundos)

---

## [0.4.0] - 2025-06-12

### ✨ Added - Protocolos Avanzados

- **Protocolo Generic** para cámaras chinas (16+ patrones RTSP)
- **Auto-detección** de puertos específicos por marca
- **Steren CCTV-235** soporte completo con dual-stream
- **TP-Link Tapo series** integración con auto-discovery

### 🔧 Enhanced - ONVIF Implementation

- **Multi-brand ONVIF** optimizado (Dahua, TP-Link, Steren)
- **Stream URI extraction** automático y confiable
- **Device discovery** con información completa del dispositivo
- **Profile management** automático para diferentes calidades

### 📋 Added - Configuration Management

- **Configuration persistence** con .env + JSON híbrido
- **Brand manager** con configuraciones específicas por marca
- **Logging system** estructurado y debugging avanzado

---

## [0.3.0] - 2025-06-12

### ✨ Added - Soporte Multi-Marca

- **Dahua Hero-K51H** soporte completo (4K, 13.86 FPS)
- **TP-Link Tapo C520WS** integración con multi-perfil
- **ONVIF Protocol** como protocolo principal
- **RTSP Protocol** universal con OpenCV

### 🏗️ Enhanced - Arquitectura SOLID

- **Factory Pattern** para creación de conexiones
- **Template Method** en BaseConnection
- **Singleton Pattern** para ConfigurationManager
- **Context Manager** para gestión automática de recursos

### 🛠️ Technical

- **Hardware testing** con 4 marcas diferentes
- **Performance benchmarks** establecidos
- **Error handling** robusto con reconexión automática

---

## [0.2.0] - 2025-06-10

### ✨ Added - Core Functionality

- **Real-time video streaming** con OpenCV
- **Camera connection management** básico
- **Snapshot capture** functionality
- **Basic UI** con Tkinter

### 🔧 Added - Protocols Foundation

- **RTSP connection** base implementation
- **HTTP/CGI** básico para cámaras compatibles
- **Connection factory** pattern inicial

### 📊 Added - Basic Features

- **Configuration loading** desde archivos
- **Basic logging** implementation
- **Error handling** fundamental

---

## [0.1.0] - 2025-06-10

### 🚀 Initial Release

- **Project setup** y estructura básica
- **Tkinter UI** foundation
- **OpenCV integration** para video display
- **Basic camera connection** proof of concept
- **SOLID principles** initial implementation

---

## 🔮 Roadmap - Próximas Versiones

### [0.8.0] - Planeado

- **Presenter Layer** completo (MVP 100%)
- **Event handling** profesional con delegation
- **Business logic** completamente separado de UI
- **Testing suite** básico (>85% coverage)

### [0.9.0] - Planeado

- **DuckDB Analytics** integration
- **Real-time metrics** dashboard
- **Performance monitoring** avanzado
- **Export/import** functionality

### [1.0.0] - Release Candidate

- **MVP Architecture** 100% completo
- **Testing suite** completo (>90% coverage)
- **Performance optimization** final
- **Documentation** completa

### [1.1.0] - Native Distribution

- **Flet packaging** nativo
- **Windows executable** (.exe) + installer
- **macOS application** (.app) + DMG
- **Linux executable** (.deb/.AppImage)
- **Auto-update system** functionality

---

## 📋 Notas de Migración

### Tkinter → Flet (0.5.0 → 0.7.0)

- **UI Framework**: Cambio completo de Tkinter a Flet
- **Architecture**: Evolución de MVC básico a MVP completo
- **Performance**: Mejora significativa en rendering y responsiveness
- **Compatibility**: Ejemplos Tkinter mantenidos en `examples/`

### Dependencies Updates

- **Python**: 3.8+ → 3.9+ (required for Flet)
- **New**: flet>=0.24.1, cryptography>=41.0.0, pandas>=2.0.0
- **Enhanced**: opencv-python, onvif-zeep con versiones específicas

---

**Formato**: [Unreleased] para cambios aún no lanzados  
**Tags**: [Major.Minor.Patch] siguiendo Semantic Versioning  
**Categorías**: Added, Changed, Deprecated, Removed, Fixed, Security
