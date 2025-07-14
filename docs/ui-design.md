# 🎨 Diseño UI - Material Design 3

## 🎯 Filosofía de Diseño

**Universal Camera Viewer** implementa **Material Design 3** con **React + Material-UI v7** para crear una experiencia moderna, accesible y consistente.

### **Principios Clave**

- ✨ **Modern First**: Material Design 3 con componentes elevados
- 🎨 **Adaptive Colors**: Temas dinámicos light/dark
- 📱 **Responsive**: Adaptable a diferentes tamaños de pantalla
- ♿ **Accessible**: Contraste y navegación accesible
- ⚡ **Performance**: Renderizado optimizado con React 19

## 🎨 Sistema de Diseño

### **Design Tokens** (`src/design-system/tokens.ts`)

```typescript
// Espaciado basado en 8dp grid
export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

// Paleta de colores personalizada
export const colors = {
  // Estados de cámara
  camera: {
    connected: '#4caf50',
    connecting: '#ff9800',
    disconnected: '#f44336',
    error: '#d32f2f',
  },
  
  // Colores semánticos
  success: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20' },
  warning: { main: '#ed6c02', light: '#ff9800', dark: '#e65100' },
  error: { main: '#d32f2f', light: '#ef5350', dark: '#c62828' },
  info: { main: '#0288d1', light: '#03a9f4', dark: '#01579b' },
};

// Sistema tipográfico
export const typography = {
  h1: { fontSize: '2.5rem', fontWeight: 600 },
  h2: { fontSize: '2rem', fontWeight: 600 },
  h3: { fontSize: '1.75rem', fontWeight: 500 },
  body1: { fontSize: '1rem', lineHeight: 1.5 },
  caption: { fontSize: '0.875rem', color: 'text.secondary' },
};
```

### **Configuración de Tema** (`src/design-system/theme.ts`)

```typescript
import { createTheme, ThemeOptions } from '@mui/material/styles';

// Tema Light
export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
  },
  
  components: {
    // Personalización de componentes MUI
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

// Tema Dark
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
      light: '#e3f2fd',
      dark: '#42a5f5',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  // Misma configuración de componentes
});
```

## 🏗️ Arquitectura de Componentes

### **Estructura de Carpetas**

```
src/
├── app/
│   ├── providers/
│   │   └── AppProviders.tsx    # Theme + Router providers
│   └── router/
│       └── AppRouter.tsx        # Rutas de la aplicación
│
├── features/                    # Páginas principales
│   ├── cameras/
│   │   ├── CamerasPage.tsx
│   │   └── components/
│   │       ├── CameraCard.tsx
│   │       └── CameraGrid.tsx
│   ├── scanner/
│   ├── analytics/
│   ├── settings/
│   └── streaming/
│
├── components/                  # Componentes compartidos
│   ├── layout/
│   │   ├── AppLayout.tsx
│   │   └── NavigationBar.tsx
│   ├── feedback/
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorBoundary.tsx
│   └── camera/
│       ├── VideoPlayer.tsx
│       └── CameraStatus.tsx
│
└── design-system/
    ├── tokens.ts               # Design tokens
    └── theme.ts                # Temas MUI
```

### **Componentes Principales**

#### NavigationBar
```tsx
<AppBar position="static" elevation={2}>
  <Toolbar>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <VideocamIcon />
      <Typography variant="h6">
        Universal Camera Viewer
      </Typography>
    </Box>
    
    <Box sx={{ flexGrow: 1 }} />
    
    <Box sx={{ display: 'flex', gap: 1 }}>
      <Button startIcon={<CameraAltIcon />}>
        Cámaras
      </Button>
      <Button startIcon={<SearchIcon />}>
        Escanear
      </Button>
    </Box>
  </Toolbar>
</AppBar>
```

#### CameraCard
```tsx
<Paper 
  elevation={2}
  sx={{
    p: 2,
    borderRadius: 2,
    transition: 'all 0.3s ease',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: 4,
    },
  }}
>
  <Box sx={{ position: 'relative' }}>
    <VideoPlayer cameraId={camera.id} />
    <Chip
      label={camera.status}
      color={getStatusColor(camera.status)}
      size="small"
      sx={{ position: 'absolute', top: 8, right: 8 }}
    />
  </Box>
  
  <Typography variant="h6" sx={{ mt: 2 }}>
    {camera.name}
  </Typography>
  
  <Typography variant="body2" color="text.secondary">
    {camera.ip} • {camera.brand}
  </Typography>
</Paper>
```

## 📱 Diseño Responsive

### **Breakpoints**

```typescript
// MUI default breakpoints
xs: 0px     // Móvil
sm: 600px   // Tablet portrait
md: 900px   // Tablet landscape
lg: 1200px  // Desktop
xl: 1536px  // Desktop grande

// Uso en componentes
<Grid container spacing={2}>
  <Grid item xs={12} sm={6} md={4} lg={3}>
    <CameraCard />
  </Grid>
</Grid>
```

### **Layout Adaptativo**

```tsx
const useResponsive = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  
  return { isMobile, isTablet, isDesktop };
};
```

## 🎯 Estados y Animaciones

### **Estados de Componentes**

```typescript
// Estados de cámara con colores
const cameraStates = {
  connected: {
    color: colors.camera.connected,
    icon: <CheckCircleIcon />,
    animation: 'pulse',
  },
  connecting: {
    color: colors.camera.connecting,
    icon: <CircularProgress size={20} />,
    animation: 'rotate',
  },
  disconnected: {
    color: colors.camera.disconnected,
    icon: <ErrorIcon />,
    animation: 'shake',
  },
};
```

### **Transiciones CSS**

```typescript
// Transiciones suaves
const transitions = {
  fast: 'all 0.2s ease',
  medium: 'all 0.3s ease',
  slow: 'all 0.5s ease',
};

// Animaciones
const animations = {
  fadeIn: keyframes`
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  `,
  pulse: keyframes`
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
  `,
};
```

## 🔧 Integración con Estado Global

### **Zustand Store**

```typescript
// src/stores/uiStore.ts
interface UIStore {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  theme: 'light',
  sidebarOpen: true,
  toggleTheme: () => set((state) => ({ 
    theme: state.theme === 'light' ? 'dark' : 'light' 
  })),
  toggleSidebar: () => set((state) => ({ 
    sidebarOpen: !state.sidebarOpen 
  })),
}));
```

## 📊 Componentes Especializados

### **VideoPlayer para Streaming**

```tsx
interface VideoPlayerProps {
  cameraId: string;
  onError?: (error: Error) => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  cameraId, 
  onError 
}) => {
  const [frame, setFrame] = useState<string>('');
  
  useEffect(() => {
    // Escuchar eventos de Tauri
    const unlisten = listen<FrameEvent>('video_frame', (event) => {
      if (event.payload.cameraId === cameraId) {
        setFrame(`data:image/jpeg;base64,${event.payload.frame}`);
      }
    });
    
    return () => { unlisten.then(fn => fn()); };
  }, [cameraId]);
  
  return (
    <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
      <img 
        src={frame || '/placeholder-camera.png'}
        alt="Camera view"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
    </Box>
  );
};
```

## 🎯 Mejores Prácticas

1. **Usar sx prop para estilos inline** en lugar de CSS modules
2. **Aprovechar el tema MUI** para consistencia
3. **Componentes pequeños y reutilizables**
4. **Lazy loading** para páginas pesadas
5. **Error boundaries** para manejo de errores
6. **Skeleton loaders** durante carga

## 📝 Migración de Flet a React

### Mapeo de Componentes

| Flet | React + MUI |
|------|-------------|
| `ft.Container` | `<Box>` |
| `ft.Text` | `<Typography>` |
| `ft.ElevatedButton` | `<Button variant="contained">` |
| `ft.Card` | `<Paper>` |
| `ft.Column` | `<Stack direction="column">` |
| `ft.Row` | `<Stack direction="row">` |
| `ft.IconButton` | `<IconButton>` |
| `ft.Image` | `<img>` o custom `<VideoPlayer>` |

---

### 📚 Navegación

[← Anterior: Características Detalladas](FEATURES.md) | [📑 Índice](README.md) | [Siguiente: Compatibilidad de Cámaras →](CAMERA_COMPATIBILITY.md)