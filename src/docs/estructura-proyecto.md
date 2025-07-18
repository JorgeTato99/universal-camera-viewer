# 📁 Estructura del Proyecto - Universal Camera Viewer

[← Arquitectura](./arquitectura.md) | [Índice](./README.md) | [Flujo de Datos →](./flujo-datos.md)

## 🎯 Visión General

El proyecto sigue una estructura modular y escalable, organizando el código por features y responsabilidades.

## 📂 Estructura de Carpetas

```
src/
├── 📱 app/                    # Configuración core de la aplicación
│   ├── providers/            # Providers de contexto global
│   ├── router/              # Configuración de rutas
│   └── theme/               # Configuración de temas (legacy)
│
├── 🎨 assets/                # Recursos estáticos
│   ├── icons/               # Iconos SVG personalizados
│   ├── images/              # Imágenes y logos
│   └── styles/              # Estilos globales CSS
│
├── 🧩 components/            # Componentes reutilizables
│   ├── common/              # Componentes genéricos
│   ├── dialogs/             # Diálogos y modales
│   ├── feedback/            # Estados de error/carga
│   ├── layout/              # Layout principal
│   ├── menus/               # Menús contextuales
│   └── ui/                  # Componentes UI base
│
├── ⚙️ config/                # Configuración de la app
│   └── appConfig.ts         # Constantes y configuración
│
├── 🎨 design-system/         # Sistema de diseño
│   ├── tokens.ts            # Design tokens
│   ├── theme.ts             # Tema de Material-UI
│   └── typography.ts        # Sistema tipográfico
│
├── 📚 docs/                  # Documentación del proyecto
│   └── *.md                 # Archivos de documentación
│
├── ✨ features/              # Módulos por funcionalidad
│   ├── cameras/             # Gestión de cámaras
│   ├── scanner/             # Escaneo de red
│   ├── settings/            # Configuración
│   └── statistics/          # Estadísticas
│
├── 🪝 hooks/                 # Custom React hooks
│   ├── useCamera.ts         # Hook para cámaras
│   └── useTheme.ts          # Hook para temas
│
├── 📡 services/              # Servicios y APIs
│   ├── api/                 # Cliente API REST
│   ├── python/              # Servicios Python
│   ├── scanner/             # Servicio de escaneo
│   └── tauri/               # Bridge con Tauri
│
├── 🗄️ stores/                # Estado global (Zustand)
│   ├── appStore.ts          # Estado de la app
│   ├── cameraStore.ts       # Estado de cámaras
│   └── streamingStore.ts    # Estado de streaming
│
├── 🔤 types/                 # TypeScript types
│   ├── api.types.ts         # Tipos de API
│   ├── camera.types.ts      # Tipos de cámara
│   └── common.types.ts      # Tipos comunes
│
└── 🛠️ utils/                 # Utilidades
    ├── constants.ts         # Constantes
    └── helpers.ts           # Funciones helper
```

## 📋 Descripción Detallada

### 📱 `/app` - Core de la Aplicación

```mermaid
graph LR
    A[main.tsx] -->|Renderiza| B[App.tsx]
    B -->|Envuelve con| C[AppProviders]
    C -->|Contiene| D[AppRouter]
    D -->|Define| E[Rutas]
```

- **`AppProviders.tsx`**: Agrupa todos los providers (Theme, Router, etc.)
- **`AppRouter.tsx`**: Define rutas con lazy loading y error boundaries

### 🧩 `/components` - Componentes Reutilizables

#### Organización por Categoría:
- **`common/`**: Botones, inputs, cards genéricos
- **`dialogs/`**: AboutDialog, LicenseDialog
- **`feedback/`**: Estados de error y carga
- **`layout/`**: MainLayout, Sidebar, TopBar
- **`ui/`**: Componentes UI específicos

#### Ejemplo de Componente:
```typescript
// components/layout/Sidebar.tsx
export const Sidebar: React.FC<SidebarProps> = memo(({ 
  collapsed, 
  onToggle 
}) => {
  // Lógica del componente
});
```

### ✨ `/features` - Módulos de Funcionalidad

Cada feature es un módulo independiente con su propia estructura:

```
features/cameras/
├── components/          # Componentes específicos
├── pages/              # Páginas/vistas
├── hooks/              # Hooks del feature
├── utils/              # Utilidades
└── types.ts            # Tipos locales
```

#### Features Principales:

1. **📷 Cameras**: Visualización y gestión de cámaras
2. **🔍 Scanner**: Detección de dispositivos en red
3. **⚙️ Settings**: Configuración de la aplicación
4. **📊 Statistics**: Métricas y análisis

### 🗄️ `/stores` - Gestión de Estado

Usando Zustand para estado global:

```typescript
// stores/cameraStore.ts
interface CameraStore {
  cameras: Camera[];
  selectedCamera: Camera | null;
  addCamera: (camera: Camera) => void;
  removeCamera: (id: string) => void;
}
```

#### Stores Disponibles:
- **`appStore`**: Estado general de la aplicación
- **`cameraStore`**: Gestión de cámaras
- **`streamingStore`**: Estado de streaming
- **`notificationStore`**: Sistema de notificaciones

### 📡 `/services` - Capa de Servicios

```mermaid
graph TB
    subgraph "Services Layer"
        A[CameraService]
        B[StreamingService]
        C[ScannerService]
    end
    
    subgraph "Communication"
        D[WebSocket]
        E[REST API]
        F[Tauri IPC]
    end
    
    A --> D
    A --> E
    B --> D
    C --> E
    C --> F
```

#### Tipos de Servicios:
- **API Services**: Comunicación REST
- **WebSocket Services**: Datos en tiempo real
- **Tauri Services**: Operaciones nativas

### 🎨 `/design-system` - Sistema de Diseño

Centraliza todos los aspectos visuales:

```typescript
// design-system/tokens.ts
export const colorTokens = {
  primary: {
    50: '#e3f2fd',
    500: '#2196f3',
    900: '#0d47a1'
  }
};

// design-system/theme.ts
export const lightTheme = createTheme({
  palette: {
    primary: {
      main: colorTokens.primary[500]
    }
  }
});
```

### 🔤 `/types` - TypeScript Types

Organización de tipos:
- **Globales**: En `types/` raíz
- **Por Feature**: En `features/*/types.ts`
- **Compartidos**: En `types/common.types.ts`

## 📏 Convenciones de Nomenclatura

### Archivos y Carpetas
- **Componentes**: PascalCase (`CameraCard.tsx`)
- **Utilities**: camelCase (`formatDate.ts`)
- **Types**: camelCase con `.types` (`camera.types.ts`)
- **Carpetas**: kebab-case (`design-system`)

### Exports
```typescript
// Named exports para utilities
export const formatDate = () => {};

// Default export para componentes
export default CameraCard;

// Barrel exports en index.ts
export { CameraCard } from './CameraCard';
```

## 🔄 Flujo de Importación

```mermaid
graph TD
    A[main.tsx] --> B[App.tsx]
    B --> C[features/*]
    C --> D[components/*]
    D --> E[design-system/*]
    
    C --> F[services/*]
    F --> G[types/*]
    
    C --> H[stores/*]
    H --> G
    
    style A fill:#f9f,stroke:#333,stroke-width:4px
    style E fill:#9f9,stroke:#333,stroke-width:2px
    style G fill:#99f,stroke:#333,stroke-width:2px
```

## 🚫 Anti-patterns a Evitar

1. ❌ Importaciones circulares
2. ❌ Lógica de negocio en componentes UI
3. ❌ Estado local cuando debería ser global
4. ❌ Componentes muy grandes (> 300 líneas)
5. ❌ Mezclar responsabilidades

## ✅ Best Practices

1. ✅ Un archivo = Una responsabilidad
2. ✅ Componentes pequeños y enfocados
3. ✅ Types en archivos separados
4. ✅ Barrel exports para APIs limpias
5. ✅ Lazy loading para features grandes

---

[← Arquitectura](./arquitectura.md) | [Índice](./README.md) | [Flujo de Datos →](./flujo-datos.md)