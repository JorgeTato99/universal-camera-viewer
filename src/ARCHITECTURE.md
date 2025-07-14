# 🏗️ **Arquitectura Frontend React - Universal Camera Viewer**

## **📋 Overview**

Esta es la arquitectura frontend completa para Universal Camera Viewer, construida con **React 19**, **TypeScript**, **Material-UI v7**, **Zustand**, y **Tauri** para comunicación con el backend Python.

## **🗂️ Estructura de Carpetas**

```bash
src/
├── 📁 app/                     # Configuración de aplicación
│   ├── providers/              # Context providers (Theme, Router)
│   ├── router/                 # Configuración de routing
│   └── theme/                  # Configuración de temas
├── 📁 components/              # Componentes compartidos/reutilizables
│   ├── ui/                     # Componentes básicos de UI
│   ├── layout/                 # Componentes de layout
│   └── common/                 # Componentes de negocio comunes
├── 📁 design-system/           # Sistema de diseño completo
│   ├── tokens.ts               # Tokens fundamentales (colores, tipografía, espaciado)
│   ├── theme.ts                # Configuración Material-UI
│   ├── colors.ts               # Paleta de colores y funciones utilitarias
│   ├── typography.ts           # Sistema de tipografía
│   ├── spacing.ts              # Sistema de espaciado y layout
│   ├── breakpoints.ts          # Breakpoints responsive
│   ├── components.ts           # Estilos de componentes específicos
│   └── index.ts                # Export principal del design system
├── 📁 features/                # Módulos por funcionalidad (Feature-based)
│   ├── cameras/                # Gestión de cámaras
│   ├── scanner/                # Descubrimiento de red
│   ├── analytics/              # Métricas y analytics
│   ├── settings/               # Configuración
│   └── streaming/              # Streaming de video
├── 📁 hooks/                   # Custom React hooks
├── 📁 services/                # Comunicación con backend
│   ├── tauri/                  # Interfaz Tauri
│   ├── python/                 # Servicios Python backend
│   └── api/                    # APIs externas
├── 📁 stores/                  # Estado global (Zustand)
├── 📁 types/                   # Definiciones TypeScript
├── 📁 utils/                   # Funciones de utilidad
├── 📁 assets/                  # Recursos estáticos
│   ├── icons/
│   ├── images/
│   └── styles/
├── 📁 lib/                     # Configuraciones de librerías
└── 📄 UI_UX_DESIGN_GUIDE.md   # Guía completa del sistema de diseño
```

## **🎯 Principios de Arquitectura**

### **1. Feature-Based Architecture**

- Organización por funcionalidad, no por tipo de archivo
- Cada feature es independiente y autocontenido
- Escalabilidad y mantenibilidad maximizadas

### **2. Separación de Responsabilidades**

- **Components**: UI y presentación
- **Hooks**: Lógica reutilizable y side effects
- **Services**: Comunicación con backend
- **Stores**: Gestión de estado global
- **Types**: Contratos de datos

### **3. Inmutabilidad y State Management**

- **Zustand** para estado global con subscripciones selectivas
- Estado local con React hooks para UI específica
- Persistencia automática de configuraciones críticas

## **📦 Stack Tecnológico**

### **Core**

- **React 19** - Framework principal
- **TypeScript** - Tipado estático
- **Vite** - Build tool y dev server

### **UI & Styling**

- **Material-UI v7** - Componentes y theming
- **Material Design 3** - Sistema de diseño
- **Responsive Design** - Breakpoints adaptativos

### **Estado & Datos**

- **Zustand** - State management
- **React Router DOM v7** - Routing
- **React Query** (futuro) - Server state management

### **Backend Communication**

- **Tauri API** - Comunicación con Python backend
- **Event-driven** - Eventos en tiempo real
- **Type-safe** - Contratos TypeScript

## **🔗 Comunicación Backend**

### **Tauri Commands**

```typescript
// Ejemplo de comando de cámara
const result = await tauriService.connectCamera(cameraId, config);
```

### **Event Listeners**

```typescript
// Ejemplo de evento de streaming
await tauriService.addEventListener(TauriEvents.FRAME_RECEIVED, (frame) => {
  streamingStore.updateFrame(frame.camera_id, frame.frame_data);
});
```

## **🗃️ Gestión de Estado**

### **Store Structure**

- **appStore** - Configuración global y navegación
- **cameraStore** - Gestión de cámaras y UI
- **scannerStore** - Estado de escaneo de red
- **streamingStore** - Sesiones de streaming activas
- **notificationStore** - Sistema de notificaciones

### **Ejemplo de Uso**

```typescript
const { cameras, addCamera, updateCamera } = useCameraStore();
const { showSuccess, showError } = useNotificationStore();
```

## **🎨 Sistema de Diseño**

### **Design System Completo**

Universal Camera Viewer implementa un sistema de diseño robusto basado en **Material Design 3** con extensiones específicas para aplicaciones de cámaras IP:

#### **Tokens de Diseño** (`src/design-system/tokens.ts`)
- **Colores**: Paleta completa con estados específicos para cámaras
- **Tipografía**: Jerarquía clara con variantes para IPs y métricas
- **Espaciado**: Escala consistente de 4px a 96px
- **Breakpoints**: Responsividad optimizada para grids de cámaras
- **Sombras**: Elevaciones Material Design 3
- **Bordes**: Radios y anchos estandarizados

#### **Colores Semánticos**
```typescript
// Estados de cámaras
connected: '#4caf50'    // Verde
connecting: '#ff9800'   // Naranja
disconnected: '#f44336' // Rojo
streaming: '#2196f3'    // Azul
error: '#f44336'        // Rojo
unavailable: '#9e9e9e'  // Gris
```

#### **Tipografía Especializada**
- **Roboto**: Fuente principal para UI
- **Roboto Mono**: IPs, códigos y métricas
- **Variantes específicas**: Nombres de cámaras, estados, métricas de streaming

#### **Componentes Temáticos**
```typescript
// Estilos específicos por uso
cardStyles.camera      // Cards de cámaras
buttonStyles.connect   // Botones de conexión
statusStyles.connected // Estados de cámaras
gridStyles.cameraGrid  // Grids responsivos
```

#### **Breakpoints Inteligentes**
- **xs**: 0px - 1 columna (móvil)
- **sm**: 600px - 2 columnas (tablet)
- **md**: 900px - 2 columnas (desktop)
- **lg**: 1200px - 3 columnas (desktop grande)
- **xl**: 1536px - 4 columnas (pantallas grandes)

#### **Funciones Utilitarias**
```typescript
getCameraStatusColor(status)   // Color por estado
getCameraGridColumns(width)    // Columnas por ancho
getPadding('md')              // Espaciado consistente
truncateText(2)               // Truncar texto
```

### **Theming Avanzado**

#### **Modo Claro/Oscuro**
- Paletas optimizadas para cada modo
- Transiciones suaves entre temas
- Persistencia de preferencias

#### **Tema Material-UI Personalizado**
```typescript
// Configuración extendida
const theme = createTheme({
  palette: { /* colores del design system */ },
  typography: { /* tipografía especializada */ },
  components: { /* componentes customizados */ }
});
```

#### **Colores de Estado**
- **Éxito**: Conexiones exitosas
- **Advertencia**: Estados transitorios
- **Error**: Fallos de conexión
- **Info**: Información general

### **Guía de Uso**

Consultar `src/UI_UX_DESIGN_GUIDE.md` para:
- Implementación práctica
- Mejores prácticas
- Ejemplos de código
- Patrones de diseño
- Accesibilidad WCAG 2.1 AA

## **🚀 Rutas y Navegación**

```typescript
/                     → Redirect a /cameras
/cameras              → Gestión de cámaras
/cameras/:cameraId    → Vista de streaming específica
/scanner              → Descubrimiento de red
/analytics            → Métricas y dashboard
/settings             → Configuración del sistema
```

## **📱 Características Implementadas**

### **✅ Completado**

- ✅ Estructura base de carpetas
- ✅ Sistema de tipos TypeScript completo
- ✅ Stores Zustand configurados
- ✅ Routing con React Router DOM
- ✅ Material-UI theming completo
- ✅ Servicio Tauri base
- ✅ Páginas placeholder funcionales
- ✅ **Sistema de diseño completo**
- ✅ **Tokens de diseño (colores, tipografía, espaciado)**
- ✅ **Tema Material-UI integrado**
- ✅ **Componentes específicos para cámaras**
- ✅ **Breakpoints responsive**
- ✅ **Guía de uso UI/UX**

### **🔄 En Progreso**

- 🔄 Componentes UI específicos
- 🔄 Hooks custom para lógica de negocio
- 🔄 Servicios específicos por feature
- 🔄 Testing setup

### **📋 Pendiente**

- ⏳ Implementación completa de features
- ⏳ Componentes de video streaming
- ⏳ Sistema de notificaciones UI
- ⏳ Error boundaries avanzados
- ⏳ Performance optimization
- ⏳ Accesibilidad (WCAG)

## **🛠️ Comandos de Desarrollo**

```bash
# Desarrollo
yarn tauri dev

# Build de producción
yarn tauri build

# Linting
yarn lint

# Type checking
yarn type-check
```

## **📈 Siguientes Pasos**

1. **Implementar Feature Cameras** - Grid de cámaras y conexiones
2. **Sistema de Streaming** - Componentes de video en tiempo real
3. **Scanner Implementation** - UI para descubrimiento de red
4. **Analytics Dashboard** - Métricas y gráficos
5. **Settings Panel** - Configuración avanzada
6. **Testing Suite** - Unit tests y integration tests
7. **Performance Optimization** - Lazy loading y optimizaciones
8. **Documentation** - Storybook y guías de desarrollo

## **🎯 Beneficios de Esta Arquitectura**

### **Escalabilidad**

- Fácil agregar nuevas features sin afectar existentes
- Componentes reutilizables y modulares

### **Mantenibilidad**

- Código organizado y predecible
- Separación clara de responsabilidades

### **Developer Experience**

- TypeScript para mejor IDE support
- Hot reload con Vite
- Estado predecible con Zustand

### **Performance**

- Lazy loading de features
- Estado optimizado
- Comunicación eficiente con backend

### **User Experience**

- Material Design 3 moderno
- Responsive design
- Estados de carga y error claros

---

> **Nota**: Esta arquitectura está diseñada para ser la base sólida de Universal Camera Viewer v2.0, aprovechando las mejores prácticas de React y las capacidades de Tauri para crear una aplicación desktop moderna y eficiente.
