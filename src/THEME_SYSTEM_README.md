# 🌓 **Sistema de Temas Dark/Light Mode - Universal Camera Viewer**

## **📋 Descripción General**

Sistema completo de temas dark/light mode implementado para Universal Camera Viewer con:

- **Persistencia automática** de preferencias
- **Detección de tema del sistema**
- **Transiciones suaves** entre temas
- **Componentes responsivos** al tema
- **Hook personalizado** para manejo de estado

---

## **🎨 Componentes del Sistema**

### **1. Store de Estado Global** (`src/stores/appStore.ts`)

```typescript
// Tipos de tema disponibles
export type ThemeMode = "light" | "dark" | "system";

// Estado del tema
interface AppState {
  themeMode: ThemeMode;           // Preferencia del usuario
  effectiveTheme: "light" | "dark"; // Tema efectivo final
  // ... otros estados
}

// Acciones disponibles
const actions = {
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;         // Alterna entre light/dark
  setEffectiveTheme: (theme: "light" | "dark") => void;
}
```

### **2. Hook Personalizado** (`src/hooks/useTheme.ts`)

```typescript
import { useTheme } from '../hooks/useTheme';

const { 
  theme,           // Tema Material-UI
  themeMode,       // light | dark | system
  effectiveTheme,  // light | dark (resuelto)
  isDark,          // boolean
  isLight,         // boolean
  toggleTheme,     // function
  setThemeMode     // function
} = useTheme();
```

### **3. Componente ThemeToggle** (`src/components/ui/ThemeToggle.tsx`)

```typescript
import { ThemeToggle } from '../components/ui/ThemeToggle';

<ThemeToggle 
  size="small"     // small | medium | large
  showLabel={false} // Mostrar etiquetas
  variant="icon"   // icon | button
/>
```

---

## **🚀 Implementación**

### **Paso 1: Configurar Providers**

```typescript
// src/app/providers/AppProviders.tsx
import { AppProviders } from './app/providers/AppProviders';

function App() {
  return (
    <AppProviders>
      {/* Tu aplicación */}
    </AppProviders>
  );
}
```

### **Paso 2: Usar el Hook en Componentes**

```typescript
import { useTheme } from '../hooks/useTheme';

function MyComponent() {
  const { effectiveTheme, isDark, toggleTheme } = useTheme();

  return (
    <Box 
      sx={{
        backgroundColor: isDark 
          ? colorTokens.background.dark 
          : colorTokens.background.light,
        color: isDark 
          ? colorTokens.text.dark.primary 
          : colorTokens.text.primary
      }}
    >
      <Button onClick={toggleTheme}>
        Cambiar a {isDark ? 'claro' : 'oscuro'}
      </Button>
    </Box>
  );
}
```

### **Paso 3: Añadir ThemeToggle a la UI**

```typescript
import { ThemeToggle } from '../components/ui/ThemeToggle';

function TopBar() {
  return (
    <AppBar>
      <Toolbar>
        {/* Otros controles */}
        <ThemeToggle size="small" />
      </Toolbar>
    </AppBar>
  );
}
```

---

## **🎨 Tokens de Diseño**

### **Colores por Tema**

```typescript
// Modo claro
const lightColors = {
  background: colorTokens.background.light,  // #fafafa
  paper: colorTokens.background.paper,       // #ffffff
  text: colorTokens.neutral[900],            // #212121
  border: colorTokens.neutral[300],          // #e0e0e0
};

// Modo oscuro
const darkColors = {
  background: colorTokens.background.dark,      // #121212
  paper: colorTokens.background.darkPaper,     // #1e1e1e
  text: colorTokens.neutral[50],               // #fafafa
  border: colorTokens.neutral[700],            // #616161
};
```

### **Sombras por Tema**

```typescript
// Sombras modo claro
shadowTokens.md // Sombras normales

// Sombras modo oscuro
shadowTokens.dark.md // Sombras más intensas para contraste
```

---

## **🔧 Funciones Utilitarias**

### **Detección del Sistema**

```typescript
// Detecta automáticamente la preferencia del sistema
const getSystemTheme = (): "light" | "dark" => {
  if (typeof window !== "undefined") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches 
      ? "dark" 
      : "light";
  }
  return "light";
};
```

### **Resolución de Tema Efectivo**

```typescript
// Resuelve el tema final basado en la preferencia
const resolveEffectiveTheme = (themeMode: ThemeMode): "light" | "dark" => {
  if (themeMode === "system") {
    return getSystemTheme();
  }
  return themeMode;
};
```

---

## **💾 Persistencia**

### **Configuración Zustand**

```typescript
export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Estado inicial
      themeMode: "light",
      effectiveTheme: "light",
      // ... implementación
    }),
    {
      name: "app-store",
      partialize: (state) => ({
        themeMode: state.themeMode,
        // Otros campos a persistir
      }),
    }
  )
);
```

### **Escucha de Cambios del Sistema**

```typescript
// En initialize()
if (typeof window !== "undefined") {
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  
  const handleSystemThemeChange = (e: MediaQueryListEvent) => {
    const { themeMode } = get();
    if (themeMode === "system") {
      get().setEffectiveTheme(e.matches ? "dark" : "light");
    }
  };
  
  mediaQuery.addEventListener("change", handleSystemThemeChange);
}
```

---

## **🎯 Mejores Prácticas**

### **1. Usar Tokens del Design System**

```typescript
// ✅ Correcto
const styles = {
  backgroundColor: effectiveTheme === 'dark' 
    ? colorTokens.background.dark 
    : colorTokens.background.light
};

// ❌ Incorrecto
const styles = {
  backgroundColor: isDark ? '#121212' : '#fafafa'
};
```

### **2. Componentes Responsivos al Tema**

```typescript
function ThemedComponent() {
  const { effectiveTheme } = useTheme();
  
  return (
    <Card
      sx={{
        backgroundColor: effectiveTheme === 'dark' 
          ? colorTokens.background.darkPaper 
          : colorTokens.background.paper,
        border: `1px solid ${effectiveTheme === 'dark' 
          ? colorTokens.neutral[700] 
          : colorTokens.neutral[300]}`,
      }}
    >
      {/* Contenido */}
    </Card>
  );
}
```

### **3. Transiciones Suaves**

```typescript
const styles = {
  transition: 'all 0.2s ease',
  backgroundColor: effectiveTheme === 'dark' 
    ? colorTokens.background.dark 
    : colorTokens.background.light,
};
```

---

## **📱 Estados del ThemeToggle**

### **Opciones Disponibles**

1. **Claro** (`light`)
   - Icono: ☀️ LightMode
   - Descripción: "Tema claro"

2. **Oscuro** (`dark`)
   - Icono: 🌙 DarkMode
   - Descripción: "Tema oscuro"

3. **Sistema** (`system`)
   - Icono: ⚙️ SettingsBrightness
   - Descripción: "Seguir preferencia del sistema"

### **Menú Contextual**

- **Diseño**: Menu desplegable con opciones
- **Indicador**: Checkmark en opción activa
- **Colores**: Responsive al tema actual
- **Accesibilidad**: Tooltips y navegación por teclado

---

## **🐛 Debugging**

### **Verificar Estado del Tema**

```typescript
import { useAppStore } from '../stores/appStore';

function DebugTheme() {
  const { themeMode, effectiveTheme } = useAppStore();
  
  console.log('Modo configurado:', themeMode);
  console.log('Tema efectivo:', effectiveTheme);
  console.log('Preferencia sistema:', 
    window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light'
  );
  
  return null;
}
```

### **Forzar Tema para Testing**

```typescript
// Forzar tema oscuro
useAppStore.getState().setThemeMode('dark');

// Forzar tema claro
useAppStore.getState().setThemeMode('light');

// Seguir sistema
useAppStore.getState().setThemeMode('system');
```

---

## **🔮 Extensiones Futuras**

### **Temas Personalizados**

```typescript
// Posible implementación futura
export type ThemeMode = "light" | "dark" | "system" | "custom";

interface CustomTheme {
  name: string;
  colors: Partial<typeof colorTokens>;
}
```

### **Programación Automática**

```typescript
// Auto-cambio según hora del día
interface ScheduledTheme {
  lightStart: string; // "06:00"
  darkStart: string;  // "18:00"
  enabled: boolean;
}
```

---

## **📞 Soporte**

Para problemas con el sistema de temas:

1. **Verificar persistencia**: Revisar localStorage
2. **Comprobar providers**: Asegurar que AppProviders envuelve la app
3. **Validar imports**: Verificar imports de hooks y componentes
4. **Testear MediaQuery**: Comprobar soporte del navegador

**Versión**: 2.0.0  
**Compatibilidad**: React 19, Material-UI v7, Zustand 4+
