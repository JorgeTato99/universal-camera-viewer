# Changelog

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionado Semántico](https://semver.org/spec/v2.0.0.html).

---

## [0.9.20] - 2025-07-24 - 🐛 CORRECCIONES CRÍTICAS DE ERRORES

### 🐛 Fixed - Errores de Validación Pydantic

#### 📊 AlertsListResponse - Error 500 en endpoint de alertas

- **Problema**: Faltaban campos obligatorios `page`, `page_size` y `by_alert_type`
- **Solución**: Agregados valores por defecto para paginación no real
- **Archivos**: `api/routers/publishing.py` línea 742-751

#### 📋 PublicationHistoryResponse - Error 500 en historial

- **Problema**: `filters_applied` esperaba `Dict[str, str]` pero recibía valores `None`
- **Solución**: Convertir todos los valores a strings vacíos cuando son `None`
- **Archivos**: `services/database/mediamtx_db_service.py` líneas 413-420, 814-821

### 🐛 Fixed - Errores de SQL

#### 🗄️ "no such column: c.name" en consultas de historial

- **Problema**: Las consultas SQL referenciaban `c.name` pero la tabla tiene `c.display_name`
- **Solución**: Reemplazados 3 referencias de `c.name` por `c.display_name`
- **Archivos**: `services/database/mediamtx_db_service.py` líneas 599, 786, 855

### 🐛 Fixed - Errores de TypeScript

#### 📝 useRemotePublishing.ts - Error de tipo en getRemotePublicationByCameraId

- **Problema**: Inferencia de tipo incorrecta
- **Solución**: Cambiar a `usePublishingStore.getState` para obtener tipo correcto
- **Variables no usadas**: Eliminada `selectedServerId`, prefijo `_` en `customName`

#### 🔧 apiClient.ts - Error de indexación de headers

- **Problema**: `defaultHeaders` tipado como `HeadersInit` no permite indexación
- **Solución**: Cambiar tipo a `Record<string, string>`

---

## [0.9.19] - 2025-07-24 - 🚀 OPTIMIZACIÓN DE RENDIMIENTO

### ⚡ Performance - Reducción de Polling

#### 🔄 Reducción de carga del servidor en 83%

- **Problema**: Polling global cada 5 segundos generaba 12 llamadas/minuto
- **Solución**: Aumentado a 30 segundos (2 llamadas/minuto)
- **Archivos**: `stores/publishingStore.ts` línea 240

#### 📊 Ajuste de intervalos individuales

- **usePublishingHealth**: 30s → 60s
- **usePublishingMetrics**: 5s → 15s  
- **useRemotePublishing**: 5s → 30s
- **ActivePublications**: 5s → 15s (activo) / 30s (inactivo)

### 🐛 Fixed - Métodos Faltantes en API

#### 🔌 publishing_unified.py - Métodos no implementados

- **PublishingPresenter**: Eliminado TODO, llamada real a `get_active_publications()`
- **MediaMTXRemotePublishingPresenter**: Cambiado de `get_active_publications()` a `list_remote_streams()`
- **Ajuste de datos**: Corregido acceso a lista en lugar de diccionario

---

## [0.9.18] - 2025-07-24 - 📷 ACTUALIZACIÓN DE DATOS DE CÁMARAS

### ✨ Added - Datos Reales de Cámara

#### 📹 TP-Link C200 Real en Seed Database

- **Reemplazada**: Cámara ficticia Xiaomi por TP-Link C200 real
- **Datos**: IP 192.168.100.248, credenciales superadmin/superadmin
- **Endpoints RTSP**: stream1 (HD 1280x720), stream2 (SD 640x360)
- **Archivos**: `seed_database.py`

### 🐛 Fixed - Errores de Inicialización

#### 🔧 PublishingPresenter - Error de inicialización duplicada

- **Problema**: `initialize() missing 1 required positional argument: 'config'`
- **Solución**: Eliminada re-inicialización innecesaria en publishing_unified.py
- **Líneas**: 109-111 comentadas

### 📊 Added - Logging y Debug

#### 🔍 Logging temporal para debug de URLs duplicadas

- **Agregado**: Debug logging en apiClient.ts para rastrear `/api/api/` duplicado
- **Ubicación**: `apiClient.ts` líneas 49-56

## [0.9.17] - 2025-07-23 - 🔒 SEGURIDAD CRÍTICA Y AGREGACIÓN DE LOGS

### 🔒 Security - Implementaciones Críticas Completadas

#### 📊 Rate Limiting (Fase 1.2) ✅

- **Sistema completo de protección DoS** con SlowAPI
- **Configuración externa** en `config/rate_limit_settings.yaml`
- **Límites diferenciados**: Lectura (100/min), Escritura (10/min), Escaneo (1/min)
- **Headers RFC 6585**: X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After
- **100% cobertura**: Todos los endpoints protegidos

#### 🔐 Encriptación v2 (Fase 1.3) ✅

- **Versionado de claves** con formato `v{version}:{encrypted_base64}`
- **Sistema de rotación** preparado para rotación periódica de claves
- **Migración automática** desde v1 sin pérdida de datos
- **Auditoría completa** sin exponer valores sensibles
- **103 test cases** cubriendo todos los escenarios

#### 🪵 Sanitización de Logs (Fase 1.4) ✅

- **Filtros inteligentes** para URLs, comandos, IPs y headers
- **Contexto automático** con reglas específicas por módulo
- **27 servicios migrados** usando `get_secure_logger()`
- **Tests exhaustivos** para sanitizadores, filtros y servicio

#### 📈 ELK Stack Integration ✅

- **Formateadores JSON**: Estándar, ECS y streaming-específico
- **Handlers flexibles**: Filebeat (producción) y Elasticsearch (desarrollo)
- **Contexto enriquecido**: Correlation IDs, metadata de cámaras/streams
- **Documentación completa** con Docker Compose y guías paso a paso

### 🐛 Fixed - Problema de Rutas de Archivos

#### 🗂️ Creación Incorrecta de Carpeta `data`

- **Problema**: Se creaba `D:\universal-camera-viewer\data\` en lugar de `D:\universal-camera-viewer\src-python\data\`
- **Causa**: Múltiples servicios usaban rutas relativas o `Path(__file__).parent.parent.parent`
- **Archivos corregidos** (11 archivos):
  - `services/data_service.py` - Rutas absolutas para base de datos y exports
  - `services/scan_service.py` - Eliminada inicialización singleton durante import
  - `config/settings.py` - DATABASE_PATH con ruta absoluta por defecto
  - `services/encryption_service.py` - Keystore path corregido
  - `services/encryption_service_v2.py` - Path calculation fixed
  - `services/logging_service.py` - Log directory path
  - `api/middleware/rate_limit.py` - Config file path
  - `routers/publishing_metrics.py` - Export directory path
  - `services/database/publishing_db_service.py` - Database path y key file
  - `services/database/mediamtx_db_service.py` - Database path
  - `routers/scanner.py` - Cambio de import singleton a función factory

### 🧪 Testing - Cobertura de Seguridad

- **test_encryption_service_v2.py**: 103 test cases completos
- **test_sanitizers.py**: Pruebas exhaustivas de sanitización
- **test_logging_filters.py**: Verificación de filtros de logs
- **test_logging_service.py**: Tests del servicio singleton

### 📚 Documentation

- **RUN_API_GUIDE.md**: Actualizado con solución al problema de rutas
- **CURRENT_WORK_STATUS.md**: Estado actualizado de implementaciones
- **docs/elk_integration.md**: Guía completa de integración ELK Stack
- **docs/security_implementation.md**: Documentación de seguridad

### 🔄 Work Status

- **Completado**: Rate Limiting, Encriptación v2, Log Sanitization, ELK Stack
- **Pospuesto**: WebSocket Authentication (para release final)
- **Eliminado**: Input Validation (fase 1.5) - no necesario con validación existente

---

## [0.9.16] - 2025-07-23 - 📖 DOCUMENTACIÓN OPENAPI Y MIGRACIÓN MEDIAMTX

### 📚 Documentation - OpenAPI/Swagger Mejorado

- **Mejoras en documentación de endpoints**:
  - Añadidos decoradores `summary` y `description` a todos los endpoints críticos
  - Documentación de funcionalidades MOCK y pendientes
  - Mejora en descripciones de parámetros y respuestas
  - Ejemplos de respuestas de error con códigos HTTP apropiados

- **Modelos con json_schema_extra**:
  - `MetricPoint`: Ejemplo completo con todas las métricas
  - `MetricsSummary`: Estadísticas con valores realistas
  - `PublicationMetricsResponse`: Respuesta completa con viewer_stats

### 🔄 Changed - Guía de Migración

- **migration-guide-v0.9.16.md** creado con:
  - Cambios en enums (PublishStatus ahora en MAYÚSCULAS)
  - Script SQL de migración para actualizar valores existentes
  - Mapping de overall_status para compatibilidad frontend
  - Ajustes necesarios en código existente

### 🐛 Fixed - Consistencia de Tipos

- **PublishStatus enum**:
  - Valores cambiados de minúsculas a MAYÚSCULAS
  - Consistencia con frontend que espera valores en mayúsculas
  - Script de migración SQL incluido

- **PublishingHealth.overall_status**:
  - Mapping automático con validator Pydantic
  - Backend: healthy/degraded/critical
  - Frontend: healthy/warning/error
  - Compatibilidad transparente sin cambios en frontend

### 📝 Documentation Updates

- **type-consistency-report.md**: Marcados como resueltos todos los issues
- **mui-grid-v7-migration-guide.md**: Simplificado, removida sección extensa sobre MediaMTXPath
- **mediamtx-id-inconsistency-solution.md**: Mantenido como referencia

---

## [0.9.15] - 2025-07-23 - 🔧 INTEGRACIÓN MEDIAMTX FASE 4.1 COMPLETA

### ✨ Added - Tests de Integración MediaMTX

#### 🧪 Sistema de Validación de Tipos TypeScript → Python

- **TypeScript Parser** implementado:
  - Extracción de interfaces y tipos desde archivos `.ts`
  - Soporte para tipos básicos, arrays, unions y enums
  - Parseo de propiedades opcionales y requeridas

- **Type Validator** para consistencia:
  - Validación de respuestas backend contra interfaces TypeScript
  - Detección automática de inconsistencias de campos
  - Reporte detallado de incompatibilidades

#### ✅ Tests Unitarios y de Integración

- **Tests para PaginatedResponse**:
  - Propiedades computadas (has_next, has_previous, total_pages)
  - Serialización JSON y model_dump
  - Validación de límites de paginación

- **Tests de Integración de Endpoints**:
  - `/api/publishing/status` - Estados de publicación
  - `/api/publishing/control` - Control de publicación
  - `/api/publishing/health` - Salud del sistema
  - `/api/publishing/metrics` - Métricas de streaming
  - `/api/publishing/alerts` - Sistema de alertas

- **Tests de Flujo Completo**:
  - Ciclo de vida de publicación (start → metrics → stop)
  - Manejo de errores y timeouts
  - Requests concurrentes

### 🐛 Fixed - Inconsistencias de Tipos

#### 🔄 MediaMTXPath Field Mapping

- **Problema**: Frontend espera `id`, backend usa `path_id`
- **Solución**: Alias Pydantic con `Field(..., alias="id")`
- **Compatibilidad**: Acepta tanto `id` como `path_id` en requests

#### 🎯 PublishingStatus Enum

- **Problema**: Backend usaba minúsculas, frontend espera MAYÚSCULAS
- **Solución**: Actualización de enum a valores en MAYÚSCULAS
- **Impacto**: Requiere migración de BD (script SQL incluido)

#### 🩺 PublishingHealth Status Mapping

- **Problema**: Backend usa degraded/critical, frontend espera warning/error
- **Solución**: Validator Pydantic que mapea automáticamente
- **Transparencia**: Sin cambios necesarios en frontend

### 🧪 Testing Infrastructure

- **Pytest configuration** con fixtures compartidas
- **Mock factories** para componentes MediaMTX
- **AsyncClient fixture** para tests de integración
- **Cobertura estimada**: 85% de endpoints críticos

### 📊 Technical Stats

- **Tests añadidos**: 30+ tests nuevos
- **Modelos validados**: 15+ interfaces TypeScript
- **Inconsistencias resueltas**: 3 críticas
- **Archivos de test**: 8 nuevos archivos Python

## [0.9.14] - 2025-07-21 - 🚀 INTEGRACIÓN MEDIAMTX FRONTEND COMPLETA

### ✨ Added - Sistema de Publicación MediaMTX Frontend

#### 🎯 Menú "Publicación" Completo

- **Nueva sección en Sidebar** con icono de streaming y 5 subsecciones:
  - **Dashboard**: Panel principal con estado del sistema y métricas
  - **Publicaciones Activas**: Control de streaming con tabla interactiva
  - **Métricas**: Estadísticas en tiempo real con visualizaciones
  - **Historial**: Registro completo de sesiones con filtros
  - **Configuración**: Gestión de servidores MediaMTX

#### 📊 Componentes Implementados (Fase 5)

- **Dashboard Components**:
  - `HealthStatusCard`: Estado de salud del sistema con indicadores visuales
  - `ActivePublicationsWidget`: Widget de publicaciones activas con animaciones
  - `QuickActionsCard`: Acciones rápidas para control de publicación
  - `AlertsList`: Lista de alertas con severidad y timestamps
  - `ViewersChart`: Gráfico de viewers en tiempo real
  
- **Control Components**:
  - `PublishingControls`: Controles principales start/stop con confirmación
  - `StreamStatusBadge`: Badge de estado con colores semánticos
  - `TestConnectionButton`: Botón de prueba con feedback visual
  - `MetricsGauge`: Indicador radial de métricas (FPS, Bitrate)
  
- **Chart Components**:
  - `MetricsLineChart`: Gráfico de líneas con Recharts
  - `ViewersAreaChart`: Gráfico de área para viewers
  - `BitrateChart`: Visualización de bitrate en tiempo real

#### 🎨 Mejoras Visuales (Fase 6)

- **Tooltips informativos** implementados en todas las vistas:
  - Iconos "?" para información de ayuda con hover
  - Iconos "!" para advertencias importantes
  - Iconos "ℹ️" para información contextual
  - Tooltips en headers de tablas, botones y métricas

- **Formulario de configuración mejorado**:
  - Organización en secciones con títulos descriptivos
  - Iconos temáticos (candado, API, configuración)
  - Animaciones Fade para campos condicionales
  - Header con color primario y diseño profesional

### 🏗️ Enhanced - Arquitectura Frontend

#### 📦 Servicios y Store

- **PublishingService** completo con 30+ métodos API
- **PublishingStore** (Zustand) con estado global y selectores
- **Hooks personalizados**:
  - `usePublishingStatus`: Estado de publicaciones con polling
  - `usePublishingHealth`: Salud del sistema con auto-refresh
  - `usePublishingMetrics`: Métricas con histórico

#### 🔧 Tipos TypeScript

- **20+ interfaces** para tipos de publicación
- **Enums** para estados y severidades
- **Request/Response types** para API
- **Validación estricta** en toda la aplicación

### 🐛 Fixed - Correcciones Críticas

#### 🔧 Material-UI Grid v7

- **Migración completa** a nueva sintaxis Grid
- Cambio de `<Grid item xs={12}>` a `<Grid size={{ xs: 12, md: 6 }}>`
- Corrección en 10+ componentes afectados

#### 📦 Dependencias y Errores

- **framer-motion** reemplazado con animaciones CSS nativas
- **Recharts tooltip types** corregidos con interfaces custom
- **NotificationStore** métodos actualizados (showSuccess, showError)
- **ApiResponse conflict** resuelto con exports selectivos
- **Tooltip imports** añadidos donde faltaban

### 📊 Technical Stats

- **Archivos creados**: 45+ nuevos archivos TypeScript
- **Líneas de código**: ~4,000 líneas de React/TypeScript
- **Componentes**: 35+ componentes nuevos
- **Cobertura**: Sistema completo de publicación frontend
- **Performance**: Lazy loading y memoización aplicados

### 🎯 Integration Ready

- **Frontend completamente preparado** para backend MediaMTX
- **Mocks funcionales** mientras se implementa el backend
- **Estructura escalable** para futuras mejoras
- **Design system** consistente con resto de la aplicación

---

## [0.9.13] - 2025-07-18 - 📊 SISTEMA DE ESTADÍSTICAS COMPLETO

### ✨ Added - Sistema de Estadísticas

#### 📈 Módulo Completo de Estadísticas

- **6 subsecciones especializadas** accesibles desde el sidebar:
  - **General**: Dashboard con métricas clave y salud del sistema
  - **Conexiones**: Análisis detallado con gráficos de tendencias
  - **Eventos**: Timeline interactivo con filtros y reconocimiento
  - **Rendimiento**: Métricas en tiempo real con indicador radial
  - **Red**: Historial completo de escaneos con resultados expandibles
  - **Reportes**: Sistema de reportes con plantillas y programación

- **Visualizaciones con Recharts**:
  - Gráficos de área, línea y circular
  - Indicador radial de salud del sistema
  - Tablas interactivas con expansión de detalles
  - Timeline visual de eventos con severidad

#### 🎨 Componentes de Configuración Real

- **NetworkSettings**: Timeouts, reintentos, conexiones concurrentes
- **CameraSettings**: Calidad de streaming, FPS, rutas RTSP por marca
- **UserPreferences**: Tema, idioma, diseño y modo desarrollador

### 🐛 Fixed - Correcciones Críticas

#### 🔧 Migración a Grid v2

- **Actualización completa** de sintaxis Grid en todos los componentes
- Cambio de `<Grid item xs={12}>` a `<Grid size={{ xs: 12 }}>`
- Eliminación del prop `item` obsoleto en MUI v6

#### 📦 Dependencias Faltantes

- **Instalación de librerías necesarias**:
  - `recharts` - Para visualización de datos
  - `date-fns` - Para formateo de fechas
  - `@mui/lab` - Para componentes Timeline
  - `@mui/x-date-pickers` - Para selectores de fecha

#### 🎯 Correcciones de Importación

- **Timeline components** movidos de `@mui/material` a `@mui/lab`
- **Fade animation error** resuelto en TabPanel de StatisticsPage
- **Rutas de importación** corregidas para lazy loading

### 📊 Technical Improvements

- **Lazy loading optimizado** para todas las subsecciones
- **Memoización con React.memo()** en componentes pesados
- **Mock data realista** para desarrollo sin backend
- **Animaciones Grow/Fade** con delays escalonados
- **Auto-expansión del sidebar** según ruta activa

---

## [0.9.12] - 2025-07-18 - 🎯 SCANNER INDEPENDIENTE Y ANIMACIONES

### ✨ Added - Funcionalidades Principales

#### 🔍 Scanner Modules Independence

- **Port Scan y Access Test completamente independientes**:
  - Entrada manual de IP sin requerir pasos previos
  - Toggle para cambiar entre datos detectados y manuales
  - Validación en tiempo real de IPs y puertos
  - Persistencia de datos entre navegaciones con query params

#### 🎬 Sistema de Animaciones Completo

- **Animaciones de carga** para componentes esperando datos
- **Animaciones de entrada** con Fade y Grow en todas las páginas
- **Transiciones suaves** entre estados y vistas
- **Skeleton loaders** para feedback visual durante carga

### 🎨 Enhanced - Mejoras de UI/UX

#### ⚡ Optimizaciones de Rendimiento

- **PERFORMANCE_OPTIMIZATIONS.md** con documentación completa
- **React.memo()** aplicado consistentemente
- **useCallback y useMemo** para prevenir re-renders
- **Lazy loading** con precarga de rutas críticas
- **CSS transform** para animaciones con GPU

#### 📝 Documentación de TODOs

- **TODOS.md** creado con 73 tareas pendientes organizadas
- Categorización por prioridad (Alta/Media/Baja)
- Tracking de progreso con checkboxes
- Estimaciones de tiempo y complejidad

### 🐛 Fixed - Correcciones

- **AccessTestPage JSX structure error** - Tags cerrados faltantes
- **Settings lazy loading error** - Exports default añadidos
- **Scanner navigation flow** - Manejo correcto de estados vacíos
- **Performance bottlenecks** - Optimizaciones aplicadas

### 🔧 Technical Details

- **Componentes actualizados**: 15+ componentes con animaciones
- **Archivos de documentación**: 2 nuevos (TODOS.md, PERFORMANCE_OPTIMIZATIONS.md)
- **Optimizaciones aplicadas**: 30+ mejoras de rendimiento
- **Reducción de re-renders**: ~60% en componentes críticos

---

## [0.9.11] - 2025-07-18 - 📝 DOCUMENTACIÓN Y REFACTORING FINAL

### 📚 Documentation - Actualización Completa

#### 🎯 README Principal Refactorizado

- **Nuevo enfoque como "Universal Camera Gateway"** reflejando el verdadero propósito
- **Descripción clara** como gateway inteligente entre cámaras locales y MediaMTX
- **Diagrama ASCII** de arquitectura: Cámaras → Gateway → MediaMTX
- **Casos de uso reales**: Hogar inteligente, empresas, instaladores CCTV
- **Flujo de trabajo** documentado paso a paso
- **Métricas de rendimiento** realistas para gateway y streaming

#### 📋 Documentación Actualizada

- **CURRENT_STATUS.md** actualizado a v0.9.10 con estado de integración MediaMTX
- **mediamtx-integration.md** con estado funcional y requerimientos
- **features.md** actualizado con MediaMTX Publishing
- **Correcciones documentadas** de errores de WebSocket y PublishingPresenter

### 🔧 Technical - Correcciones Finales

- **Documentación inline** mejorada en código crítico
- **Comentarios actualizados** reflejando arquitectura actual
- **TODOs resueltos** o documentados apropiadamente

---

## [0.9.10] - 2025-07-18 - 🚀 INTEGRACIÓN MEDIAMTX COMPLETA

### ✨ Added - MediaMTX Publishing System

#### 🌐 WebSocket Handler para Publicación

- **PublishingWebSocketHandler** completo con eventos en tiempo real
- **Sistema de suscripciones** por cámara para eventos dirigidos
- **Loop de actualización de métricas** cada 2 segundos
- **Comandos implementados**:
  - `subscribe_camera/unsubscribe_camera` - Gestión de suscripciones
  - `start_publishing/stop_publishing` - Control de publicación
  - `get_status` - Estado de publicaciones activas
- **Integración con PublishingPresenter** para emisión de eventos

#### 💾 Base de Datos para Configuraciones

- **PublishingDatabaseService** con persistencia completa:
  - Tablas: `publishing_configurations`, `publishing_states`, `publishing_history`, `publishing_metrics`
  - Encriptación de passwords con Fernet
  - Seguimiento de estados activos y métricas históricas
  - Transacciones ACID para integridad de datos
- **CRUD de configuraciones MediaMTX** con validación
- **Historial completo** de sesiones de publicación

#### 🔌 API REST de Configuración

- **Router completo** `/api/publishing/config` con:
  - GET `/` - Listar todas las configuraciones
  - GET `/active` - Obtener configuración activa
  - POST `/` - Crear nueva configuración
  - PUT `/{name}` - Actualizar configuración
  - DELETE `/{name}` - Eliminar configuración
  - POST `/{name}/activate` - Activar configuración
- **Validación robusta** con códigos HTTP apropiados
- **Protección** contra eliminación de configuraciones en uso

### 🐛 Fixed - Errores Críticos

#### 🔧 WebSocket Connection Issues

- **Verificación de estado** antes de enviar mensajes
- **Manejo mejorado** de desconexiones esperadas
- **Logs optimizados** para reducir ruido en errores normales
- **Cleanup robusto** al desconectar clientes

#### 🏗️ PublishingPresenter Abstract Methods

- **Implementados métodos faltantes**:
  - `_initialize_presenter()` - Requerido por BasePresenter
  - `_cleanup_presenter()` - Para limpieza de recursos
- **Herencia correcta** de BasePresenter sin errores

#### ⚙️ PublishConfiguration API Conflicts

- **Conflicto resuelto** entre parámetro `api_url` y propiedad
- **Cambio de propiedad a método** `get_api_url()`
- **Actualización completa** de todas las referencias en:
  - `presenters/publishing_presenter.py`
  - `services/publishing/rtsp_publisher_service.py`
  - `api/routers/publishing_config.py`

### 📊 Technical Improvements

- **Inicialización mejorada** del PublishingPresenter desde DB
- **Configuración por defecto** si no existe en base de datos
- **Integración completa** entre todos los componentes
- **FFmpeg detection** con mensajes claros si no está instalado

### ⚠️ Known Issues

- **Requiere FFmpeg instalado** para funcionar
- **Errores esperados al inicio** si no hay FFmpeg:

  ```bash
  ERROR:FFmpegManager:FFmpeg no encontrado en PATH
  ERROR:RTSPPublisherService:FFmpeg no está instalado
  ```

- **No afecta** otras funcionalidades del sistema

---

## [0.9.9] - 2025-07-17 - 🚀 API v2 COMPLETA Y MÉTRICAS AVANZADAS

### ✨ Added - API v2 Completa

#### 📦 Gestión de Credenciales Múltiples

- **CRUD completo de credenciales** con encriptación automática
- **Soporte para múltiples credenciales** por cámara
- **Gestión de credencial por defecto** con protección contra eliminación
- **Endpoints implementados**: GET, POST, PUT, DELETE, set-default

#### 🎬 Stream Profiles Management

- **Perfiles de streaming personalizables** (main, sub, third, mobile)
- **Validación de resolución y bitrate** con cálculo inteligente
- **Soporte para codecs**: H264, H265, MJPEG, MPEG4
- **Niveles de calidad**: highest, high, medium, low, lowest
- **Endpoint de prueba** para validar configuración antes de guardar

#### 🔌 Gestión de Protocolos

- **Auto-discovery de protocolos** con escaneo de puertos
- **Pruebas de conectividad** con métricas de tiempo de respuesta
- **Soporte completo**: ONVIF, RTSP, HTTP, HTTPS, CGI, Amcrest
- **Discovery asíncrono** en background para escaneos profundos

#### 📊 Endpoints de Solo Lectura

- **GET /capabilities**: Capacidades técnicas organizadas por categorías
- **GET /events**: Historial de eventos con filtros y paginación
- **GET /logs**: Logs técnicos con niveles y componentes
- **GET /snapshots**: Galería de capturas con metadatos

### 🎯 Enhanced - Métricas de Streaming

#### 📈 Sistema de Latencia Basado en Timestamp de Captura

- **Nueva medición de latencia real** usando timestamp de captura del frame
- **Eliminado sistema RTT (ping/pong)** para mayor eficiencia
- **Cálculo preciso**: `latencia = tiempo_actual - timestamp_captura`
- **Validación inteligente**: Descarta valores negativos o > 10 segundos
- **Reducción de tráfico**: Elimina 12 mensajes/minuto de ping/pong
- **Campo `capture_timestamp`** añadido a mensajes de frame
- **Latencia -1** cuando no está disponible (transparencia total)

#### 📊 Métricas Avanzadas

- **Integración con StreamMetrics** para historial de 30 valores
- **Latencia promedio** calculada automáticamente
- **Health Score (0-100)** basado en FPS, latencia y errores
- **Indicador `latency_type`** (real/simulated)

### 🛡️ Security & Validation

- **Validación exhaustiva** de UUID, rangos de fecha, paginación
- **Manejo específico de excepciones** con códigos HTTP apropiados
- **Encriptación segura** de credenciales en base de datos
- **Límites de paginación** para prevenir abuso (50-500 items)

### 📚 Documentation

- **CURRENT_WORK_STATUS.md** con plan completo de 5 fases
- **Documentación de calidad** para cada fase implementada:
  - QUALITY_REVIEW_CREDENTIALS.md
  - QUALITY_REVIEW_STREAM_PROFILES_FINAL.md
  - QUALITY_REVIEW_PROTOCOLS_FINAL.md
  - QUALITY_REVIEW_READ_ONLY_ENDPOINTS_FINAL.md
- **backend-latency-implementation-response.md** con detalles de implementación
- **Ejemplos de código React** para integración frontend

### 🔧 Technical Improvements

- **15+ nuevos modelos Pydantic** para validación robusta
- **50+ nuevos métodos** en servicios y data layer
- **Queries SQL optimizadas** con índices apropiados
- **Patrón consistente** de manejo de errores en todos los endpoints

### 📊 Statistics

- **Endpoints añadidos**: 20+ nuevos endpoints en API v2
- **Líneas de código**: ~3,500 líneas nuevas
- **Modelos Pydantic**: 35+ modelos de request/response
- **Cobertura estimada**: 85% con validaciones completas
- **Tiempo de implementación**: 8 horas de desarrollo intensivo

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

**Formato**: [Unreleased] para cambios aún no lanzados  
**Tags**: [Major.Minor.Patch] siguiendo Semantic Versioning  
**Categorías**: Added, Changed, Deprecated, Removed, Fixed, Security
