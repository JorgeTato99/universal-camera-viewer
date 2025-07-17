# Changelog

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionado Semántico](https://semver.org/spec/v2.0.0.html).

---

## [0.9.8] - 2025-07-17 - 🔧 REORGANIZACIÓN Y OPTIMIZACIONES

### ✨ Added - Funcionalidades de Streaming

#### 🎥 Reorganización del Módulo de Streaming

- **Eliminación del módulo streaming duplicado** y consolidación en cameras
- **Integración completa de WebSocket** después de conexión exitosa
- **Manejo automático de desconexión** con cleanup de recursos WebSocket
- **Componente VideoStream optimizado** con Canvas y requestAnimationFrame
- **Conversión base64 a Blob** para mejor rendimiento de memoria

### 🎨 Enhanced - Optimizaciones de UI

#### ⚡ Rendimiento y Re-renders

- **React.memo en VideoStream** para prevenir re-renders innecesarios
- **useCallback en CameraCard** para optimizar callbacks de métricas
- **Eliminación de memoización incorrecta** en LiveViewPage
- **Logs de debug optimizados** para reducir ruido en consola
- **FPS real del streaming** mostrado correctamente (9-15 FPS)

#### 🔄 Estado de Conexión

- **Actualización correcta del UI** al conectar/desconectar cámaras
- **Estado inicial correcto** - todas las cámaras empiezan desconectadas
- **Prevención de reconexión automática** al recargar la página
- **Manejo de errores de desconexión** cuando no existe WebSocket

### 🐛 Fixed - Correcciones Importantes

- **VideoPlayer is not defined** - Reemplazado con CameraVideoPreview/VideoStream
- **streamingService.offFrame error** - Uso correcto de función unsubscribe
- **Parpadeo/flickering de video** - Implementación con Canvas y Blob URLs
- **Error de desconexión WebSocket** - Verificación de conexión antes de detener
- **UI no actualizándose** - Eliminación de memoización incorrecta en filtros

### 📝 Documentation - Backend Instructions

- **backend-latency-implementation.md** creado con instrucciones para implementar métricas de latencia
- **Documentación detallada** de la estructura esperada de métricas
- **Ejemplos de implementación** con código real y simulado

### 🔧 Technical - Detalles de Implementación

#### Arquitectura de Streaming

- WebSocket se conecta automáticamente después de conexión exitosa de cámara
- VideoStream usa Canvas API para renderizado sin parpadeo
- Blob URLs en lugar de base64 directo para mejor performance
- RequestAnimationFrame para sincronización suave con browser

#### Optimizaciones de Store

- Store actualiza correctamente el estado de conexión
- Eliminación de recargas innecesarias de cámara después de conectar
- Verificación de conexión WebSocket antes de intentar desconectar

### 📌 Notes - Problemas Conocidos

- **Latencia siempre muestra 0ms** - Backend no envía el campo `latency` en métricas
- **Múltiples logs de isConnected** - Reducidos pero algunos persisten por naturaleza de React

---

## [0.9.7] - 2025-01-16 - 🎨 INTERFAZ DE USUARIO MEJORADA

### ✨ Added - Nuevas Funcionalidades

#### 🔍 Sistema de Escaneo de Red (Scanner)

- **Vista completa de Scanner** con flujo de 3 pasos:
  1. Escaneo de red para detectar dispositivos
  2. Escaneo de puertos para identificar servicios
  3. Prueba de acceso con credenciales
- **Componentes especializados**:
  - `NetworkScanPanel` - Configuración de escaneo con modos auto/manual
  - `PortScanPanel` - Análisis de puertos por velocidad
  - `AccessTestPanel` - Validación de credenciales
  - `ScanResults` - Visualización en tiempo real de dispositivos encontrados
  - `ScanSummary` - Resumen del progreso del escaneo
- **Servicio Scanner** (`scannerService.ts`) con arquitectura preparada para WebSocket
- **Animaciones fluidas** con keyframes personalizados y transiciones suaves

#### 💬 Diálogo "Acerca de" Mejorado

- **Rediseño completo con tabs**:
  - Tab Información: Stack tecnológico y características principales
  - Tab Actualizaciones: Sistema de verificación y descarga
  - Tab Licencia: Vista previa y acceso a licencia completa
- **Indicador de actualizaciones** en TopBar con badge animado
- **LicenseDialog** separado con funciones de impresión y descarga

#### ⚙️ Menú de Configuración Rápida

- **QuickSettingsMenu** accesible desde TopBar
- **Controles rápidos**:
  - Volumen de alertas con slider
  - Calidad de streaming (auto/HD/SD)
  - Toggle de notificaciones
  - Selector de idioma (ES/EN)
  - Acceso directo a carpeta de grabaciones
- **Diferenciación clara** entre configuración rápida y completa

### 🎨 Enhanced - Mejoras de Interfaz

#### 🎯 TopBar Mejorada

- **Animaciones en todos los íconos**:
  - Rotación en configuración
  - Pulso en ayuda
  - Transformaciones suaves en controles de ventana
- **Tooltips informativos** en todos los botones
- **Badge de notificación** cuando hay actualizaciones disponibles
- **Eliminación del ícono de notificaciones** (redundante con QuickSettings)

#### 🌊 Animaciones y Transiciones

- **Keyframes personalizados**: `slideInLeft`, `fadeInUp`, `pulseAnimation`, `shimmer`, `rippleEffect`
- **Transiciones con cubic-bezier** para movimientos naturales
- **Efectos de hover mejorados** en todos los componentes interactivos
- **Skeleton loaders** para estados de carga

### 📝 Changed - Cambios Importantes

#### 🏗️ Arquitectura Frontend

- **Documentación inline detallada** de integraciones pendientes:
  - Todos los TODOs incluyen endpoints esperados
  - Estructuras de datos request/response documentadas
  - Ejemplos de implementación con código funcional
- **Emojis identificadores**: 🚀 para integraciones, 🔧 para mocks
- **Referencias cruzadas** entre componentes relacionados

#### 📄 Documentación de Integración

- **Creación de `PENDING_INTEGRATIONS.md`** con resumen de todas las funcionalidades pendientes
- **TODOs mejorados** en el código con:
  - Contexto completo de la funcionalidad
  - Endpoints del backend esperados
  - Código de ejemplo para implementación
  - Notas sobre dependencias y configuración

### 🐛 Fixed - Correcciones

- **Import duplicado de React** en TopBar.tsx
- **Etiquetas JSX no cerradas** en NetworkScanPanel.tsx
- **Imports faltantes** de `keyframes`, `alpha`, `borderTokens`
- **Badge import** consolidado en Material-UI imports

### 🔧 Technical - Detalles Técnicos

#### Componentes Creados

- `/src/features/scanner/` - Módulo completo de escaneo
- `/src/components/dialogs/LicenseDialog.tsx` - Diálogo de licencia
- `/src/components/menus/QuickSettingsMenu.tsx` - Menú de configuración rápida

#### Integraciones Documentadas

- Sistema de actualizaciones con GitHub Releases API
- WebSocket para eventos de escaneo en tiempo real
- Tauri API para controles de ventana
- Sistema i18n para internacionalización
- Persistencia de configuración con Zustand

### 📌 Notes - Notas para Desarrolladores

- **Mock data funcional** mientras se implementa el backend
- **Todos los componentes** siguen el design system establecido
- **Animaciones optimizadas** para rendimiento
- **Código preparado** para integración inmediata con backend

---

## [0.9.6] - 2025-07-16 - 📚 REORGANIZACIÓN DE DOCUMENTACIÓN

### 📝 Documentation - Reestructuración Completa

- **Documentación reorganizada** en carpeta `docs/`:
  - Todos los archivos renombrados a minúsculas (excepto README.md)
  - Estructura lógica con secciones agrupadas
  - Índice principal actualizado con navegación clara
  - Eliminación de contenido duplicado

- **Archivos renombrados**:
  - `ARCHITECTURE.md` → `architecture.md`
  - `DATABASE_SCHEMA_3FN.md` → `database-schema.md`
  - `FEATURES.md` → `features.md`
  - `WINDOWS_SETUP.md` → `windows-setup.md`

- **Documentación actualizada**:
  - `api-services.md` - Reescrito completamente para API v2 y WebSocket
  - `deployment.md` - Migrado de Tauri a FastAPI/Docker
  - `camera-compatibility.md` - Creado con guía completa de cámaras

### 🧹 Code Cleanup - Limpieza de Proyecto

- **Análisis de carpeta `config/`**:
  - Identificada como obsoleta (legacy de versiones con Flet)
  - ConfigService comentado en dependencies.py
  - Puede ser eliminada de forma segura

### 📊 Organization - Mejoras de Estructura

- **README.md principal** en docs/:
  - Reorganizado con secciones temáticas
  - Estado actualizado a v0.9.5
  - Enlaces de navegación corregidos
  - Tabla de estado de documentación actualizada

---

## [0.9.5] - 2025-07-16 - 🔐 CONSOLIDACIÓN DE SEGURIDAD Y PATHS

### 🛡️ Security - Rutas Absolutas y Encriptación

- **EncryptionService mejorado** con rutas absolutas:
  - Eliminación de problemas con `os.chdir()` en run_api.py
  - Clave de encriptación única en `data/.encryption_key`
  - Prevención de múltiples claves en diferentes ubicaciones
  - Consolidación de todas las operaciones a ruta del proyecto

- **DataService actualizado** con paths absolutos:
  - Base de datos siempre en `data/camera_data.db`
  - Eliminación de bases de datos duplicadas
  - Consistencia en todas las operaciones de archivo

### 🐛 Fixed - Problemas de Autenticación

- **Credenciales Dahua corregidas**:
  - Password actualizado en seed_database.py
  - Encriptación correcta de credenciales
  - Autenticación ONVIF funcionando
  - Conexión RTSP estable con cámara real

### 📚 Documentation - Actualización Completa

- **README.md** actualizado con comandos de base de datos
- **CURRENT_STATUS.md** actualizado con problemas resueltos
- **DATABASE_SCHEMA_3FN.md** con sección de gestión de BD

---

## [0.9.4] - 2025-07-16 - 🗄️ MEJORAS DE BASE DE DATOS

### ✨ Added - Opciones de Gestión de BD

- **Opciones en seed_database.py**:
  - `--clear` para limpiar y recrear con datos de prueba
  - `--force` para recreación completa con backup
  - Manejo de errores de constraint UNIQUE
  - Eliminación de caracteres Unicode problemáticos

- **migrate_database.py reescrito**:
  - Eliminación de imports no existentes
  - Creación de backup antes de migración
  - Recreación limpia de estructura 3FN

### 🛠️ Fixed - Problemas de Encoding

- **UnicodeEncodeError resuelto**:
  - Eliminación de emojis en seed_database.py
  - Compatibilidad con terminal Windows
  - Encoding UTF-8 explícito en archivos

### 🔧 Changed - Estructura de Proyecto

- **Consolidación de archivos**:
  - Una sola base de datos en `data/`
  - Eliminación de `src-python/data/`
  - Limpieza de archivos temporales

---

## [0.9.3] - 2025-07-14 - 🗄️ BASE DE DATOS PROFESIONAL 3FN

### ✨ Added - Nueva Estructura de Base de Datos

- **Base de datos completamente rediseñada** siguiendo Tercera Forma Normal (3FN):
  - 16 tablas normalizadas con relaciones claras
  - Sistema de IDs con UUID v4 para unicidad global
  - Campo `code` único para referencias legibles (ej: "CAM-DAHUA-REAL-172")
  - Índices optimizados para búsquedas frecuentes
  - Triggers para actualización automática de timestamps
  - Vistas precalculadas para consultas complejas

- **Scripts de gestión de datos**:
  - `create_database.py` - Crea base de datos desde cero con verificación
  - `seed_database.py` - Pobla con 6 cámaras de prueba reales
  - Eliminación de migración (no necesaria, setup limpio)

- **Seguridad mejorada**:
  - `EncryptionService` con AES-256 Fernet
  - Credenciales siempre encriptadas en DB
  - Múltiples credenciales por cámara soportadas
  - Auditoría con campos `created_by`/`updated_by`

### 📚 Documentation

- **DATABASE_SCHEMA_3FN.md** - Documentación completa del esquema
- **DATABASE_REDESIGN_SUMMARY.md** - Resumen del rediseño
- README actualizado con nuevos comandos de DB

---

## [0.9.2] - 2025-07-14 - 🏗️ API V2 Y COMPONENTES FRONTEND

### ✨ Added - API v2 Completa

- **Backend API v2**:
  - `CameraManagerService` - Servicio de alto nivel para gestión de cámaras
  - Modelos Pydantic completos para request/response
  - Router `/api/v2` con todos los endpoints CRUD
  - Integración con nueva estructura de DB

- **Frontend Components v2**:
  - Tipos TypeScript actualizados (`camera.types.v2.ts`)
  - Servicio API v2 (`cameraService.v2.ts`)
  - Store Zustand v2 con filtrado avanzado (`cameraStore.v2.ts`)
  - `CameraDetailsCard` - Vista detallada con tabs
  - `CameraFormDialog` - Formulario crear/editar con validación

### 📚 Documentation

- **V2_INTEGRATION_GUIDE.md** - Guía completa de integración
- Ejemplos de uso y mejores prácticas

---

## [0.9.1] - 2025-07-14 - 🏗️ REFACTORING Y MEJORAS DE CALIDAD

### 🔄 Changed - Refactoring Arquitectónico Mayor

- **Cumplimiento estricto del patrón MVP**:
  - Creación de `WebSocketStreamService` para separar lógica de negocio del handler
  - Eliminación de acceso directo a Presenter desde WebSocket handler
  - Implementación correcta del flujo: Handler → Service → Presenter
  - Separación clara de responsabilidades entre capas

### 🛡️ Security - Gestión de Credenciales

- **Eliminación de credenciales hardcodeadas**:
  - Creación de `config/settings.py` para gestión centralizada
  - Documentación completa en `.env.example` con todas las variables necesarias
  - Preparación para futuro almacenamiento seguro en base de datos

### 🐛 Fixed - Correcciones de Código

- **Métodos duplicados eliminados**:
  - `is_streaming` renombrado a `is_camera_streaming` en VideoStreamPresenter
  - Eliminación de métodos de compatibilidad obsoletos
- **Corrección de patrones async/await**:
  - Reemplazo de `time.sleep()` por `await asyncio.sleep()` en RTSPStreamManager
  - Método `_attempt_reconnect` corregido para ser asíncrono
- **Problemas de UI corregidos**:
  - Timer de conexión ahora se detiene correctamente al desconectar
  - FPS y latencia se resetean a 0 al desconectar
  - Corrección de error "Cannot access 'isConnected' before initialization"

### 🎨 Code Quality - Mejoras de Calidad

- **Logging profesionalizado**:
  - Eliminación completa de emojis en mensajes de log (más de 100 instancias)
  - Mensajes más concisos y profesionales
  - Mantenimiento de información útil para debugging
- **Organización mejorada**:
  - Imports optimizados y organizados
  - Eliminación de código muerto y referencias obsoletas
  - Documentación mejorada en métodos críticos

### 📚 Documentation - Actualización

- **Variables de entorno documentadas**:
  - `.env.example` actualizado con secciones organizadas
  - Comentarios explicativos para cada variable
  - Valores por defecto claramente indicados

---

## [0.9.0] - 2025-07-14 - 🎉 CICLO COMPLETO FUNCIONAL

### ✨ Added - Streaming Completo Funcional

- **Streaming en tiempo real completamente funcional**:
  - Conexión exitosa con cámara Dahua real (Hero-K51H)
  - Transmisión fluida de video a 13-15 FPS
  - Conversión correcta de colores BGR a JPEG
  - Área de video limpia sin overlays
  - Contador de tiempo de conexión real
  - Actualización de métricas cada segundo

### 🐛 Fixed - Problemas Finales Resueltos

- **Corrección de inversión de colores**:
  - Eliminada conversión innecesaria BGR→RGB
  - Frames enviados directamente en formato BGR para cv2.imencode
  - Colores naturales restaurados (piel y objetos con colores correctos)
- **Métricas actualizándose correctamente**:
  - FPS calculado con ventana deslizante de 30 frames
  - Latencia simulada de 20-70ms
  - Contador de tiempo en línea con formato HH:MM:SS
- **UI completamente pulida**:
  - Métricas movidas fuera del área de video
  - Información técnica en header de la tarjeta
  - Estado visual claro de conexión/desconexión

### 📚 Documentation - Actualización Completa

- **CURRENT_STATUS.md** actualizado a v0.9.0 con estado FUNCIONAL
- **README.md** actualizado con características de streaming real
- **docs/FEATURES.md** marcando streaming como funcional
- **docs/ARCHITECTURE.md** con arquitectura WebSocket documentada

---

## [0.8.7] - 2025-07-14

### ✨ Added - WebSocket Streaming Funcional

- **Streaming WebSocket real implementado**:
  - Conexión exitosa con cámara Dahua (192.168.1.172)
  - RTSP URL correcta: `/cam/realmonitor?channel=1&subtype=0`
  - Transmisión de frames base64 funcionando
  - Heartbeat ping/pong cada 30 segundos
  - Reconexión automática con backoff

### 🐛 Fixed - Problemas de Conexión

- **Errores de configuración corregidos**:
  - ConnectionConfig con parámetros correctos (rtsp_port vs protocol)
  - Abstract methods renombrados (_initialize_presenter)
  - StreamStatus.STREAMING en lugar de ACTIVE
  - RTSP path específico para Dahua
- **WebSocket mejorado**:
  - Manejo correcto de mensajes ping
  - Prevención de envío después de cierre
  - Limpieza de conexiones al desconectar
  - Frontend deteniendo stream correctamente

### 🔄 Changed - UI/UX Improvements

- **Reorganización de información en CameraCard**:
  - Métricas (FPS, MS) movidas al header
  - Área de video completamente limpia
  - Tiempo de conexión real implementado
  - VideoPlayer sin overlay de estado

---

## [0.8.6] - 2025-07-14

### ✨ Added - Integración Real de Cámaras

- **Preparación para conexión con cámaras reales**:
  - StreamHandler con soporte para credenciales reales
  - VideoStreamPresenter integrado completamente
  - ConnectionConfig con todos los parámetros necesarios
  - Logging detallado para debugging

### 🐛 Fixed - WebSocket y Streaming Service

- **Mejoras en StreamingService**:
  - Singleton mejorado por cámara
  - Prevención de conexiones duplicadas
  - Mejor gestión de reconexión
  - Logs detallados para debugging

### 🔄 Changed - Video Display

- **Área de video mejorada**:
  - Relación de aspecto cambiada de 4:3 a 16:9
  - CSS aspectRatio para mantener proporciones
  - Mejor uso del espacio en la tarjeta

---

## [0.8.5] - 2025-07-14

### ✨ Added - Real Camera Integration Base

- **Base para integración con cámaras reales**:
  - Configuración inicial para cámara Dahua
  - Estructura para credenciales reales
  - VideoStreamPresenter preparado
  - Sistema de fallback a mock

### 📊 Changed - Mock Data

- **Expansión de cámaras mock** de 3 a 6:
  - Hikvision DS-2CD2043G2-I (Entrada Principal)
  - Xiaomi Mi Home Security 360 (Pasillo)
  - Reolink RLC-810A (Jardín Trasero)
  - Todas las cámaras inician en estado desconectado

---

## [0.8.4] - 2025-07-14

### ✨ Added - Video Streaming Components

- **Componentes de streaming de video**:
  - `VideoPlayer` completo con controles y métricas en tiempo real
  - `CameraVideoPreview` para estado desconectado
  - Integración con WebSocket para streaming base64
  - Visualización de FPS, latencia y estado de conexión
  - Controles de play/pause, fullscreen, snapshot

### 🎨 Changed - Camera UI

- **CameraCard mejorado**:
  - Integración con VideoPlayer para streaming real
  - Información técnica movida arriba del video
  - Botones rebalanceados a 1/3 del ancho cada uno
  - Estados visuales mejorados para conectado/desconectado

### 🐛 Fixed - API Integration

- **Corrección de integración API**:
  - FastAPI endpoints devolviendo formato correcto
  - Manejo de trailing slashes en URLs
  - CameraService adaptado para manejar respuestas array y ApiResponse
  - Solución temporal para formato de respuesta inconsistente

---

## [0.8.3] - 2025-07-14

### ✨ Added - FastAPI Backend

- **Backend FastAPI completo**:
  - Servidor API REST con estructura profesional
  - WebSocket endpoints para streaming de video
  - Routers para cameras, scanner, config, streaming
  - Middlewares CORS configurados para desarrollo
  - Sistema de logging estructurado

- **WebSocket streaming implementado**:
  - ConnectionManager para gestión de clientes
  - StreamHandler con soporte para múltiples cámaras
  - Generación de frames mock con OpenCV
  - Métricas de streaming en tiempo real
  - Protocolo de mensajes estructurado

### 🔧 Changed - Architecture Migration

- **Migración de Tauri a FastAPI + React**:
  - Backend Python puro con FastAPI
  - Frontend React standalone
  - Servicios TypeScript para consumir API REST
  - WebSocket service para streaming en tiempo real
  - Scripts de desarrollo para ejecutar ambos servidores

### 📚 Added - API Documentation

- **Documentación OpenAPI automática**:
  - Swagger UI en `/docs`
  - ReDoc en `/redoc`
  - Schemas Pydantic para validación
  - Ejemplos de uso en cada endpoint

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

---

**Formato**: [Unreleased] para cambios aún no lanzados  
**Tags**: [Major.Minor.Patch] siguiendo Semantic Versioning  
**Categorías**: Added, Changed, Deprecated, Removed, Fixed, Security
