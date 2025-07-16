# 📋 Integraciones Pendientes - Universal Camera Viewer

Este documento lista todas las funcionalidades que están implementadas en el frontend pero requieren integración con el backend o servicios externos.

## 📅 Fecha de última actualización: 2025-01-16

---

## 1. 🔍 Scanner (Escáner de Red)

### Ubicación: `src/features/scanner/`

#### NetworkScanPanel.tsx

```typescript
// Línea 108-120: handleStartScan
/**
 * TODO: Conectar con servicio real de escaneo
 * Endpoint esperado: POST /api/v2/scanner/network/start
 * Body: { mode: 'auto' | 'manual', ipRange?: string, scanSpeed: 'fast' | 'normal' | 'deep' }
 */

// Línea 122-128: handleStopScan  
/**
 * TODO: Conectar con servicio real para detener escaneo
 * Endpoint esperado: POST /api/v2/scanner/network/stop
 * Body: { scanId: string }
 */
```

#### PortScanPanel.tsx

```typescript
// Línea 95-107: handleStartScan
/**
 * TODO: Conectar con servicio real de escaneo de puertos
 * Endpoint esperado: POST /api/v2/scanner/ports/start
 * Body: { 
 *   devices: DeviceScanResult[], 
 *   portRange: string, 
 *   scanSpeed: 'fast' | 'normal' | 'thorough' 
 * }
 */
```

#### AccessTestPanel.tsx

```typescript
// Línea 112-125: handleTestAccess
/**
 * TODO: Conectar con servicio real de prueba de acceso
 * Endpoint esperado: POST /api/v2/scanner/access/test
 * Body: { 
 *   devices: DeviceScanResult[], 
 *   credentials: { username: string, password: string },
 *   testOnvif: boolean,
 *   testRtsp: boolean,
 *   testHttp: boolean
 * }
 */
```

#### scannerService.ts

```typescript
// TODO: Reemplazar todas las funciones mock con llamadas reales a la API
// Ver comentarios detallados en cada método del servicio
```

---

## 2. 💬 About Dialog (Acerca de)

### Ubicación: `src/components/dialogs/AboutDialog.tsx`

#### Verificación de actualizaciones

```typescript
// Línea 177-196: checkForUpdates
/**
 * TODO: Conectar con servicio real de actualizaciones
 * 
 * Implementación sugerida:
 * - Endpoint: GET https://api.github.com/repos/user/repo/releases/latest
 * - O servicio propio: GET /api/v2/updates/check
 * 
 * Respuesta esperada:
 * {
 *   version: string,
 *   releaseDate: string,
 *   changelog: string[],
 *   downloadUrl: string
 * }
 */

// Línea 737-739: Botón de descarga de actualización
/**
 * TODO: Implementar descarga de actualización
 * - Abrir URL de descarga en navegador
 * - O implementar descarga con progreso usando Tauri
 */

// Línea 815: Navegación a configuración
/**
 * TODO: Implementar navegación programática
 * - Cerrar el dialog
 * - Navegar a /settings/general/updates
 */
```

#### Exportación de licencia

```typescript
// Línea 920-922: Exportar PDF
/**
 * TODO: Implementar exportación de licencia a PDF
 * - Usar biblioteca como jsPDF o react-pdf
 * - O endpoint del backend: GET /api/v2/license/export
 */
```

---

## 3. ⚙️ Quick Settings Menu (Configuración Rápida)

### Ubicación: `src/components/menus/QuickSettingsMenu.tsx`

#### Persistencia de configuración

```typescript
// Línea 82-91: handleVolumeChange, handleQualityChange, etc.
/**
 * TODO: Persistir cambios en el backend
 * 
 * Endpoints sugeridos:
 * - PUT /api/v2/settings/quick
 * - Body: QuickSettings object
 * 
 * O usar store de Zustand con persistencia local
 */

// Línea 110-112: handleOpenRecordingsFolder
/**
 * TODO: Abrir carpeta de grabaciones
 * - Usar API de Tauri para abrir explorador de archivos
 * - Command: open_folder(path: string)
 */
```

---

## 4. 🎯 TopBar (Barra Superior)

### Ubicación: `src/components/layout/TopBar.tsx`

#### Indicador de actualizaciones

```typescript
// Línea 46: Estado hasUpdate
/**
 * TODO: Conectar con servicio de actualizaciones
 * - Suscribirse a eventos de actualización via WebSocket
 * - O polling cada X minutos
 * - Mostrar badge cuando updateAvailable === true
 */

// Línea 75-83: useEffect para verificar actualizaciones
/**
 * TODO: Reemplazar simulación con verificación real
 * - Llamar a servicio de actualizaciones al montar
 * - Configurar intervalo de verificación periódica
 */
```

#### Controles de ventana

```typescript
// Línea 48-59: handleMinimize, handleMaximize, handleClose
/**
 * TODO: Implementar controles de ventana con Tauri
 * 
 * Imports necesarios:
 * import { appWindow } from '@tauri-apps/api/window';
 * 
 * Implementación:
 * - handleMinimize: await appWindow.minimize()
 * - handleMaximize: await appWindow.toggleMaximize()
 * - handleClose: await appWindow.close()
 */
```

---

## 5. 📄 License Dialog (Diálogo de Licencia)

### Ubicación: `src/components/dialogs/LicenseDialog.tsx`

#### Funciones de exportación

```typescript
// Línea 102-123: handlePrint
/**
 * NOTA: Ya implementado con window.print()
 * Posible mejora: Usar CSS específico para impresión
 */

// Línea 125-135: handleDownload
/**
 * NOTA: Ya implementado con Blob y descarga local
 * Posible mejora: Agregar analytics de descarga
 */
```

---

## 6. 🎨 Theme Toggle (Cambio de Tema)

### Ubicación: `src/components/ui/ThemeToggle.tsx`

```typescript
// Línea 79-82: handleThemeChange
/**
 * NOTA: Ya conectado con store de Zustand
 * La persistencia del tema se maneja en el store
 */
```

---

## 📌 Notas Generales de Implementación

### WebSocket Events

Los siguientes eventos de WebSocket necesitan ser implementados:

1. **Scanner Events**
   - `scanner:network:progress` - Progreso del escaneo de red
   - `scanner:network:device_found` - Dispositivo encontrado
   - `scanner:port:progress` - Progreso del escaneo de puertos
   - `scanner:access:result` - Resultado de prueba de acceso

2. **Update Events**
   - `update:available` - Nueva actualización disponible
   - `update:download:progress` - Progreso de descarga

### Configuración de Endpoints

Todos los endpoints deben configurarse en:

- `src/config/api.config.ts` (crear si no existe)
- Variables de entorno para diferentes ambientes

### Manejo de Errores

Todos los servicios deben implementar:

- Reintentos con backoff exponencial
- Manejo de errores de red
- Notificaciones al usuario
- Logs para debugging

### Testing

Crear tests para:

- Servicios mockeados
- Componentes con estados de carga/error
- Integración con WebSocket

---

## 🚀 Prioridades de Implementación

1. **Alta Prioridad**
   - Scanner: Conexión con backend existente
   - Actualizaciones: Sistema de notificaciones
   - Quick Settings: Persistencia de preferencias

2. **Media Prioridad**
   - Controles de ventana Tauri
   - Exportación de licencia a PDF
   - WebSocket para eventos en tiempo real

3. **Baja Prioridad**
   - Analytics de uso
   - Mejoras de impresión
   - Animaciones adicionales

---

## 📞 Contacto para Dudas

Para cualquier duda sobre estas integraciones, consultar:

- Documentación del API: `/docs/api/`
- Equipo de Backend: `backend@kipustec.com`
- Arquitecto de Software: Jorge Tato

---

Última actualización por: Claude AI
Fecha: 2025-01-16
