# 🏗️ Arquitectura del Scanner - Universal Camera Viewer

## 📋 Resumen

El módulo de Scanner permite el descubrimiento automático de cámaras IP en la red local. Implementa un flujo de 3 pasos: escaneo de red, análisis de puertos y prueba de acceso.

## 🎯 Flujo de Datos

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Componente    │────▶│     Store       │────▶│    Service      │
│   (React UI)    │     │   (Zustand)     │     │  (HTTP/WS)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   Backend API   │
                                                 │   (FastAPI)     │
                                                 └─────────────────┘
```

## 📦 Componentes

### 1. **UI Components** (`/components/`)

- **NetworkScanPanel**: Configuración y control del escaneo de red
- **PortScanPanel**: Análisis detallado de puertos en IPs específicas
- **AccessTestPanel**: Prueba de credenciales y protocolos
- **ScanResults**: Lista de dispositivos encontrados
- **ScanSummary**: Resumen y estadísticas del escaneo

### 2. **Types** (`/types/scanner.types.ts`)

Define todas las interfaces y tipos necesarios:
- `ScanConfig`: Configuración del escaneo
- `DeviceScanResult`: Resultado por dispositivo
- `PortScanResult`: Estado de puertos
- `AccessTestResult`: Resultado de prueba de acceso

### 3. **Service** (`/services/scanner/scannerService.ts`)

Maneja la comunicación con el backend:
- HTTP requests para iniciar/detener escaneos
- WebSocket para actualizaciones en tiempo real
- Transformación de datos entre frontend y backend

### 4. **Store** (`/stores/scannerStore.ts`)

Estado global del scanner (Zustand):
```typescript
interface ScannerStore {
  // Estado
  currentScan: NetworkDiscovery | null;
  results: DeviceScanResult[];
  selectedDevice: DeviceScanResult | null;
  
  // Acciones
  startNetworkScan: (config) => Promise<void>;
  startPortScan: (config) => Promise<void>;
  testAccess: (config) => Promise<void>;
  selectDevice: (device) => void;
  cancelScan: () => Promise<void>;
}
```

## 🔌 Puntos de Integración

### Backend Endpoints Requeridos

#### 1. **Escaneo de Red**
```
POST /api/v2/scanner/start
Body: {
  network_ranges: string[],
  ports: number[],
  timeout: number,
  max_threads: number,
  include_onvif: boolean,
  include_rtsp: boolean,
  include_http: boolean,
  test_authentication: boolean
}
Response: { scan_id: string, status: string }
```

```
GET /api/v2/scanner/status/{scan_id}
Response: NetworkDiscovery
```

```
GET /api/v2/scanner/results/{scan_id}
Response: DeviceScanResult[]
```

```
POST /api/v2/scanner/stop/{scan_id}
Response: { status: "cancelled" }
```

#### 2. **Escaneo de Puertos**
```
POST /api/v2/scanner/ports/{ip}
Body: { ports: number[], timeout: number }
Response: { scan_id: string }
```

```
GET /api/v2/scanner/ports/{ip}/results
Response: PortScanResult[]
```

#### 3. **Prueba de Acceso**
```
POST /api/v2/scanner/test-access
Body: {
  ip: string,
  port: number,
  protocol: string,
  credentials: { username: string, password: string },
  tryAllProtocols?: boolean
}
Response: AccessTestResult[]
```

#### 4. **WebSocket**
```
WS /ws/scanner/{scan_id}

Mensajes esperados:
- { type: "progress", data: ScanProgress }
- { type: "device_found", data: DeviceScanResult }
- { type: "port_found", data: PortScanResult }
- { type: "scan_complete", data: NetworkDiscovery }
- { type: "error", data: { message: string } }
```

## 🔄 Flujo de Integración

### Paso 1: Escaneo de Red

1. Usuario configura parámetros en `NetworkScanPanel`
2. Al hacer clic en "Iniciar":
   ```typescript
   // En el componente
   const config = {
     mode: scanMode,
     ipRange: ipRange,
     speed: scanSpeed,
   };
   
   // Llamar al store
   await useScannerStore.getState().startNetworkScan(config);
   ```

3. El store llama al servicio:
   ```typescript
   // En el store
   const scanId = await scannerService.startNetworkScan(config);
   // El servicio conecta WebSocket automáticamente
   ```

4. Actualizaciones por WebSocket:
   ```typescript
   // El servicio recibe mensajes y actualiza el store
   handleWebSocketMessage(message) {
     if (message.type === "device_found") {
       // Agregar dispositivo a results
     }
   }
   ```

### Paso 2: Escaneo de Puertos

1. Usuario selecciona IP y configura puertos
2. Inicia escaneo específico:
   ```typescript
   await useScannerStore.getState().startPortScan({
     ip: selectedIP,
     categories: { onvif: true, rtsp: true, ... },
     customPorts: [...]
   });
   ```

### Paso 3: Prueba de Acceso

1. Usuario ingresa credenciales
2. Prueba conexión:
   ```typescript
   const results = await scannerService.testCameraAccess({
     ip: selectedIP,
     port: selectedPort,
     protocol: "onvif",
     credentials: { username, password },
     tryAllProtocols: true
   });
   ```

3. Si exitoso, habilitar "Agregar Cámara"

## 🚀 Para Implementar la Integración

### 1. Actualizar el Store

```typescript
// scannerStore.ts
import { scannerService } from '../services/scanner/scannerService';

// Agregar acciones reales
startNetworkScan: async (config) => {
  try {
    const scanId = await scannerService.startNetworkScan(config);
    set({ 
      currentScan: { 
        scan_id: scanId, 
        status: ScanStatus.SCANNING,
        // ... 
      } 
    });
  } catch (error) {
    // Manejar error
  }
},
```

### 2. Conectar Componentes

Reemplazar los `console.log` y simulaciones temporales con llamadas reales al store:

```typescript
// En NetworkScanPanel
const handleStartScan = async () => {
  const config = { /* ... */ };
  await useScannerStore.getState().startNetworkScan(config);
};
```

### 3. Implementar WebSocket Handlers

En el servicio, actualizar el store cuando lleguen mensajes:

```typescript
// En scannerService.ts
private handleWebSocketMessage(message: any): void {
  const store = useScannerStore.getState();
  
  switch (message.type) {
    case "device_found":
      store.addDeviceResult(message.data);
      break;
    // ... otros casos
  }
}
```

### 4. Manejo de Errores

Implementar manejo consistente de errores:
- Mostrar toast/snackbar para errores de red
- Estados de error en componentes
- Reintentos automáticos para WebSocket

## 📝 Notas Importantes

1. **Autenticación**: Si el backend requiere auth, agregar headers en apiClient
2. **CORS**: Asegurar que el backend permita peticiones desde el frontend
3. **Timeouts**: Configurar timeouts apropiados para operaciones largas
4. **Cache**: Considerar cachear resultados de escaneos recientes
5. **Performance**: El escaneo puede ser intensivo, limitar threads en backend

## 🧪 Testing

Para probar sin backend real:
1. Usar MSW (Mock Service Worker) para interceptar peticiones
2. Simular respuestas WebSocket
3. Usar datos mock en desarrollo

```typescript
// Ejemplo con MSW
import { rest } from 'msw';

export const scannerHandlers = [
  rest.post('/api/v2/scanner/start', (req, res, ctx) => {
    return res(
      ctx.json({ scan_id: 'mock-scan-123', status: 'scanning' })
    );
  }),
  // ... otros handlers
];
```