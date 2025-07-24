# 📡 Publishing Module - Universal Camera Viewer

Módulo para gestión de publicación de streams a servidores MediaMTX locales y remotos.

## 🏗️ Arquitectura

El módulo sigue la arquitectura establecida del proyecto:

```
publishing/
├── components/          # Componentes React
│   ├── auth/           # Autenticación con servidores
│   ├── control/        # Controles de publicación
│   ├── dashboard/      # Dashboards y widgets
│   ├── forms/          # Formularios
│   └── remote/         # Publicación remota
├── hooks/              # Hooks personalizados
├── services/           # Servicios de comunicación
├── types/              # TypeScript types
└── utils/              # Utilidades

```

## 🚀 Características Implementadas

### Fase 1-3 (Backend)
✅ Autenticación JWT con servidores MediaMTX remotos
✅ API Client para operaciones CRUD
✅ Publicación con FFmpeg a servidores remotos
✅ Gestión de estado y métricas

### Fase 4 (Frontend)
✅ **MediaMTXAuthDialog**: Diálogo de autenticación con validación
✅ **RemotePublishingCard**: Control individual de publicación por cámara
✅ **RemoteServerSelector**: Selector de servidor con indicadores de estado
✅ **RemoteMetricsDisplay**: Visualización de métricas en tiempo real
✅ **RemotePublishingDashboard**: Dashboard principal de gestión

## 🔧 Servicios

### mediamtxRemoteService
Servicio principal para comunicación con servidores MediaMTX remotos:
- Autenticación y gestión de tokens
- Publicación/despublicación de cámaras
- Monitoreo de estado y métricas
- Cache local de estados

## 🪝 Hooks Personalizados

### useMediaMTXAuth
Gestión de autenticación con servidores:
```typescript
const {
  servers,
  authStatuses,
  authenticate,
  logout,
  isAuthenticated
} = useMediaMTXAuth();
```

### useRemotePublishing
Control de publicación remota por cámara:
```typescript
const {
  remotePublication,
  isPublishing,
  startPublishing,
  stopPublishing
} = useRemotePublishing({ cameraId });
```

## 📋 Funcionalidades Pendientes / Mock Data

### 1. **Carga de Servidores MediaMTX**
- **Ubicación**: `useMediaMTXAuth` hook (línea 34)
- **Estado actual**: Datos mock hardcodeados
- **TODO**: Implementar endpoint `/api/mediamtx/servers` para obtener lista real

### 2. **Estado de Publicaciones Remotas**
- **Ubicación**: `RemotePublishingDashboard` (línea 108)
- **Estado actual**: Map vacío (`remotePublications = new Map()`)
- **TODO**: Conectar con store real o endpoint de estado

### 3. **Acciones de Publicación en Dashboard**
- **Ubicación**: `RemotePublishingDashboard` (líneas 184-196)
- **Estado actual**: Solo console.log
- **TODO**: Integrar con mediamtxRemoteService real

### 4. **Integración con Store Global**
- **Ubicación**: `publishingStore.remote.ts`
- **Estado actual**: Extensión del store creada pero no integrada
- **TODO**: Combinar con publishingStore principal usando zustand slices

### 5. **Endpoints de Backend Faltantes**
Los siguientes endpoints necesitan implementación en el backend:
- `GET /api/mediamtx/servers` - Lista de servidores configurados
- `POST /api/mediamtx/servers` - Agregar nuevo servidor
- `PUT /api/mediamtx/servers/:id` - Actualizar servidor
- `DELETE /api/mediamtx/servers/:id` - Eliminar servidor

## 🎨 Guías de Diseño

El módulo sigue estrictamente el sistema de diseño establecido:

- **Colores primarios**: #2196f3 (azul profesional)
- **Estados**: success (#4caf50), warning (#ff9800), error (#f44336)
- **Espaciado**: Sistema base 8px
- **Animaciones**: 300ms con easing estándar
- **Componentes**: Material-UI v6 con tema personalizado

## 📦 Uso

### Ejemplo básico de publicación remota:

```tsx
import { RemotePublishingDashboard } from '@/features/publishing/components/dashboard';

function PublishingPage() {
  return (
    <RemotePublishingDashboard
      onConfigureServer={() => {/* abrir configuración */}}
      onViewMetrics={() => {/* ver métricas */}}
    />
  );
}
```

### Ejemplo de autenticación:

```tsx
import { MediaMTXAuthDialog } from '@/features/publishing/components/auth';
import { useMediaMTXAuth } from '@/features/publishing/hooks';

function ServerConfig() {
  const { servers, authenticate } = useMediaMTXAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  
  return (
    <>
      <Button onClick={() => setDialogOpen(true)}>
        Autenticar Servidor
      </Button>
      
      <MediaMTXAuthDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        server={servers[0]}
        onAuthSuccess={(server) => {
          console.log('Autenticado:', server);
        }}
      />
    </>
  );
}
```

## 🧪 Testing

Para probar la funcionalidad remota:

1. **Mock de servidor MediaMTX**:
   - El hook `useMediaMTXAuth` incluye servidores de prueba
   - Usuario: `admin`, Contraseña: cualquiera (mock)

2. **Simular publicación**:
   - Use el dashboard con cámaras existentes
   - La autenticación funciona pero las acciones son mock

## 🔜 Próximos Pasos

1. Implementar endpoints faltantes en backend
2. Conectar servicios con API real
3. Integrar store remoto con store principal
4. Agregar WebSocket para actualizaciones en tiempo real
5. Implementar visor WebRTC para streams remotos

## 📚 Referencias

- [MediaMTX API Docs](https://github.com/bluenviron/mediamtx)
- [Material-UI v6](https://mui.com/)
- [Zustand](https://github.com/pmndrs/zustand)