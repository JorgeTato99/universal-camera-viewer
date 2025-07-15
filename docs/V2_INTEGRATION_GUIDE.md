# Guía de Integración V2 - Nueva Estructura 3FN

## Resumen de Cambios

Esta guía explica cómo integrar los nuevos componentes y servicios que soportan la estructura de base de datos normalizada 3FN.

## 1. Backend - Python

### Nuevo Servicio: CameraManagerService

```python
from services.camera_manager_service import camera_manager_service

# Inicializar el servicio
await camera_manager_service.initialize()

# Crear una cámara
camera_data = {
    'brand': 'dahua',
    'model': 'DH-IPC-HFW2431S',
    'display_name': 'Cámara Principal',
    'ip': '192.168.1.50',
    'username': 'admin',
    'password': 'password123',
    'location': 'Entrada principal'
}
camera = await camera_manager_service.create_camera(camera_data)

# Obtener cámara con configuración completa
camera = await camera_manager_service.get_camera(camera_id)

# Guardar endpoint descubierto
await camera_manager_service.save_discovered_endpoint(
    camera_id=camera_id,
    endpoint_type='rtsp_main',
    url='rtsp://192.168.1.50:554/cam/realmonitor?channel=1&subtype=0',
    verified=True
)
```

### Nuevos Endpoints API V2

```python
# En tu main.py de FastAPI
from routers.cameras_v2 import router as cameras_v2_router

app.include_router(cameras_v2_router, prefix="/api/v2")
```

Endpoints disponibles:
- `GET /api/v2/cameras` - Lista todas las cámaras
- `GET /api/v2/cameras/{camera_id}` - Obtiene una cámara
- `POST /api/v2/cameras` - Crea una nueva cámara
- `PUT /api/v2/cameras/{camera_id}` - Actualiza una cámara
- `DELETE /api/v2/cameras/{camera_id}` - Elimina una cámara
- `POST /api/v2/cameras/{camera_id}/connect` - Conecta a una cámara
- `POST /api/v2/cameras/{camera_id}/disconnect` - Desconecta una cámara
- `POST /api/v2/cameras/test-connection` - Prueba conexión sin guardar
- `POST /api/v2/cameras/{camera_id}/endpoints` - Agrega endpoint descubierto

### Actualización del DataService

El DataService ahora incluye métodos para la nueva estructura:

```python
# Guardar cámara con toda su configuración
await data_service.save_camera_with_config(
    camera=camera_model,
    credentials={'username': 'admin', 'password': 'pass'},
    endpoints=[{
        'type': 'rtsp_main',
        'url': 'rtsp://...',
        'verified': True
    }]
)

# Obtener configuración completa
config = await data_service.get_camera_full_config(camera_id)

# Guardar endpoint descubierto
await data_service.save_discovered_endpoint(
    camera_id=camera_id,
    endpoint_type='rtsp_main',
    url='rtsp://...',
    verified=True
)
```

## 2. Frontend - React/TypeScript

### Nuevos Tipos (camera.types.v2.ts)

```typescript
import {
  CameraResponse,
  CreateCameraRequest,
  UpdateCameraRequest,
  ConnectionStatus,
  ProtocolType,
  AuthType,
  isConnected,
  hasCredentials,
  getPrimaryProtocol,
  getVerifiedEndpoint,
} from '@/types/camera.types.v2';

// El tipo principal es CameraResponse que incluye:
// - Información básica (brand, model, display_name)
// - Credenciales (sin contraseña)
// - Protocolos configurados
// - Endpoints descubiertos
// - Perfiles de streaming
// - Capacidades
// - Estadísticas
```

### Nuevo Servicio (cameraService.v2.ts)

```typescript
import { cameraServiceV2 } from '@/services/python/cameraService.v2';

// Listar cámaras
const cameras = await cameraServiceV2.listCameras();

// Crear cámara
const newCamera = await cameraServiceV2.createCamera({
  brand: 'dahua',
  model: 'DH-IPC-HFW2431S',
  display_name: 'Cámara Principal',
  ip: '192.168.1.50',
  username: 'admin',
  password: 'password123',
  location: 'Entrada principal'
});

// Actualizar credenciales
await cameraServiceV2.updateCredentials(
  cameraId,
  'newUsername',
  'newPassword'
);

// Probar conexión
const result = await cameraServiceV2.testConnection({
  ip: '192.168.1.50',
  username: 'admin',
  password: 'password123',
  protocol: ProtocolType.ONVIF
});
```

### Nuevo Store (cameraStore.v2.ts)

```typescript
import { useCameraStoreV2 } from '@/stores/cameraStore.v2';

function CameraManager() {
  const {
    cameras,
    selectedCamera,
    isLoading,
    loadCameras,
    connectCamera,
    disconnectCamera,
    updateCredentials,
    getFilteredCameras,
    getCameraStats,
  } = useCameraStoreV2();

  // El store maneja automáticamente:
  // - Carga inicial de cámaras
  // - Filtrado por estado, marca, ubicación
  // - Estadísticas agregadas
  // - Gestión de errores
  // - Estados de carga por cámara
}
```

### Componentes Nuevos

#### CameraDetailsCard

Muestra información completa de una cámara con tabs:

```tsx
import { CameraDetailsCard } from '@/features/cameras/components/CameraDetailsCard';

<CameraDetailsCard
  camera={camera}
  onEdit={() => handleEdit(camera.camera_id)}
  onDelete={() => handleDelete(camera.camera_id)}
/>
```

Features:
- Tab General: Información básica, ubicación, descripción
- Tab Connection: Protocolos, endpoints descubiertos
- Tab Statistics: Métricas de conexión, errores
- Tab Advanced: Perfiles de streaming, capacidades
- Gestión de credenciales integrada
- Botones de conexión/desconexión

#### CameraFormDialog

Formulario completo para crear/editar cámaras:

```tsx
import { CameraFormDialog } from '@/features/cameras/components/CameraFormDialog';

<CameraFormDialog
  open={dialogOpen}
  onClose={() => setDialogOpen(false)}
  onSubmit={async (data) => {
    if (mode === 'create') {
      await cameraServiceV2.createCamera(data);
    } else {
      await cameraServiceV2.updateCamera(cameraId, data);
    }
  }}
  initialData={editingCamera}
  mode={mode}
/>
```

Features:
- Validación de formulario
- Test de conexión integrado
- Tabs para organizar campos
- Configuración de puertos opcionales
- Preview de contraseña

## 3. Migración de Componentes Existentes

### Actualizar importaciones

```typescript
// Antes
import { Camera, ConnectionStatus } from '@/types/camera.types';
import { cameraService } from '@/services/python/cameraService';
import { useCameraStore } from '@/stores/cameraStore';

// Después
import { CameraResponse, ConnectionStatus } from '@/types/camera.types.v2';
import { cameraServiceV2 } from '@/services/python/cameraService.v2';
import { useCameraStoreV2 } from '@/stores/cameraStore.v2';
```

### Actualizar referencias a campos

```typescript
// Antes
camera.connection_config.ip
camera.stats.connection_attempts

// Después
camera.ip_address
camera.statistics?.total_connections
```

### Nuevos helpers disponibles

```typescript
import {
  isConnected,
  hasCredentials,
  getPrimaryProtocol,
  getVerifiedEndpoint,
  getDefaultStreamProfile,
} from '@/types/camera.types.v2';

// Verificar si tiene credenciales configuradas
if (hasCredentials(camera)) {
  // Puede conectarse
}

// Obtener endpoint RTSP verificado
const rtspUrl = getVerifiedEndpoint(camera, 'rtsp_main')?.url;

// Obtener protocolo primario
const protocol = getPrimaryProtocol(camera);
```

## 4. Ejemplo de Integración Completa

### Página de Gestión de Cámaras

```tsx
import React, { useState } from 'react';
import { Grid, Button, Box } from '@mui/material';
import { Add } from '@mui/icons-material';
import { useCameraStoreV2 } from '@/stores/cameraStore.v2';
import { CameraDetailsCard } from '@/features/cameras/components/CameraDetailsCard';
import { CameraFormDialog } from '@/features/cameras/components/CameraFormDialog';
import { cameraServiceV2 } from '@/services/python/cameraService.v2';

export function CamerasPageV2() {
  const [formOpen, setFormOpen] = useState(false);
  const { 
    getFilteredCameras, 
    loadCameras 
  } = useCameraStoreV2();
  
  const cameras = getFilteredCameras();

  const handleCreateCamera = async (data: CameraFormData) => {
    await cameraServiceV2.createCamera(data);
    await loadCameras(); // Recargar lista
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={3}>
        <Typography variant="h4">Cameras</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setFormOpen(true)}
        >
          Add Camera
        </Button>
      </Box>

      <Grid container spacing={3}>
        {cameras.map(camera => (
          <Grid item xs={12} md={6} lg={4} key={camera.camera_id}>
            <CameraDetailsCard camera={camera} />
          </Grid>
        ))}
      </Grid>

      <CameraFormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleCreateCamera}
        mode="create"
      />
    </Box>
  );
}
```

## 5. Consideraciones de Migración

### Base de Datos

1. Ejecutar script de migración:
```bash
python src-python/migrate_database.py
```

2. Las credenciales necesitarán ser re-ingresadas (por seguridad)
3. Las URLs descubiertas se preservarán si existen

### API

1. Los endpoints v1 siguen funcionando
2. Migrar gradualmente a v2 para nuevas features
3. V2 incluye más información en las respuestas

### Frontend

1. Componentes v1 pueden coexistir con v2
2. Migrar página por página
3. El store v2 es independiente del v1

## 6. Troubleshooting

### Error: "Camera not found"
- Verificar que la migración de DB se completó
- Revisar que el camera_id es correcto

### Error: "Invalid credentials"
- Las credenciales no se migraron por seguridad
- Re-ingresar username/password

### Error: "Endpoint not verified"
- La URL no ha sido probada exitosamente
- Usar test connection para verificar

### Performance lento al cargar cámaras
- El store v2 carga más datos
- Considerar paginación para >50 cámaras
- Usar filtros para reducir resultados

## 7. Mejores Prácticas

1. **Siempre encriptar credenciales** - Nunca almacenar en texto plano
2. **Verificar endpoints** - Probar URLs antes de guardar
3. **Usar transacciones** - Para operaciones múltiples
4. **Cachear datos** - El store maneja cache automático
5. **Manejar errores** - Mostrar mensajes claros al usuario

## 8. Roadmap Futuro

- [ ] Bulk import/export de configuraciones
- [ ] Detección automática de cámaras en la red
- [ ] Templates de configuración por marca
- [ ] Histórico de cambios de configuración
- [ ] API GraphQL como alternativa a REST