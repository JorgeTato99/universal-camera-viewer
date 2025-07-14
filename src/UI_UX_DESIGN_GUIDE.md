# 🎨 **Universal Camera Viewer - Guía de Diseño UI/UX**

## **📋 Descripción General**

Este documento define el sistema de diseño completo para Universal Camera Viewer, una aplicación React de monitoreo de cámaras IP con Material-UI v7 y Material Design 3.

## **🎯 Filosofía de Diseño**

### **Principios Fundamentales**
- **Claridad**: Interfaz intuitiva para operadores de cámaras
- **Eficiencia**: Acceso rápido a funciones críticas
- **Consistencia**: Experiencia uniforme en toda la aplicación
- **Accesibilidad**: Cumplimiento WCAG 2.1 AA
- **Responsividad**: Adaptación a diferentes tamaños de pantalla

### **Audiencia Objetivo**
- Operadores de seguridad
- Técnicos de sistemas
- Administradores de red
- Personal de monitoreo

## **🎨 Sistema de Tokens**

### **Colores Principales**

```typescript
// Uso en componentes
import { colorTokens } from './design-system/tokens';

const primaryColor = colorTokens.primary[500]; // #2196f3
const secondaryColor = colorTokens.secondary[500]; // #4caf50
```

**Paleta de Colores:**
- **Primario**: Azul tecnológico (#2196f3) - Navegación y acciones principales
- **Secundario**: Verde éxito (#4caf50) - Estados positivos y confirmaciones
- **Estados de Cámaras**:
  - Conectado: `#4caf50` (Verde)
  - Conectando: `#ff9800` (Naranja)
  - Desconectado: `#f44336` (Rojo)
  - Streaming: `#2196f3` (Azul)
  - Error: `#f44336` (Rojo)
  - No disponible: `#9e9e9e` (Gris)

### **Tipografía**

```typescript
// Uso en componentes
import { typography } from './design-system/typography';

const titleStyle = typography.variants.h1;
const cameraNameStyle = typography.camera.name;
```

**Jerarquía de Texto:**
- **H1-H6**: Títulos principales con peso decreciente
- **Body1/Body2**: Texto de párrafo principal y secundario
- **Caption**: Texto pequeño para metadatos
- **Monospace**: IPs, códigos, métricas (Roboto Mono)

**Variantes Específicas para Cámaras:**
- `camera.name`: Nombre de cámara
- `camera.ip`: Dirección IP
- `camera.status`: Estado de conexión
- `camera.metrics`: Métricas de streaming

### **Espaciado**

```typescript
// Uso en componentes
import { spacing, getPadding, getMargin } from './design-system/spacing';

const containerStyle = {
  ...getPadding('lg'),
  ...getMargin('md', 'bottom'),
};
```

**Escala de Espaciado:**
- `xs`: 4px - Espaciado mínimo
- `sm`: 8px - Espaciado pequeño
- `md`: 16px - Espaciado estándar
- `lg`: 24px - Espaciado grande
- `xl`: 32px - Espaciado extra grande

## **📱 Componentes del Sistema**

### **Botones**

```typescript
// Uso con estilos del design system
import { buttonStyles } from './design-system/components';

// Botón principal
<Button sx={buttonStyles.primary}>Conectar Cámara</Button>

// Botón específico para conectar
<Button sx={buttonStyles.connect}>Conectar</Button>

// Botón específico para desconectar
<Button sx={buttonStyles.disconnect}>Desconectar</Button>
```

### **Cards de Cámaras**

```typescript
// Card optimizado para cámaras
import { cardStyles } from './design-system/components';

<Card sx={cardStyles.camera}>
  <CardContent>
    {/* Contenido de la cámara */}
  </CardContent>
</Card>
```

### **Estados de Conexión**

```typescript
// Chips de estado
import { statusStyles } from './design-system/components';

<Chip 
  label="Conectado" 
  sx={statusStyles.connected} 
/>

<Chip 
  label="Desconectado" 
  sx={statusStyles.disconnected} 
/>
```

### **Formularios**

```typescript
// Formulario con estilos consistentes
import { formStyles } from './design-system/components';

<Box sx={formStyles.container}>
  <TextField
    label="IP de la Cámara"
    sx={formStyles.field}
  />
</Box>
```

## **📐 Layouts y Grids**

### **Grid de Cámaras**

```typescript
// Grid responsivo automático
import { gridStyles } from './design-system/components';

<Box sx={gridStyles.cameraGrid}>
  {cameras.map(camera => (
    <CameraCard key={camera.id} camera={camera} />
  ))}
</Box>
```

### **Configuración Responsiva**

```typescript
// Breakpoints del sistema
import { breakpoints, getCameraGridColumns } from './design-system/breakpoints';

// Obtener número de columnas según ancho de pantalla
const columns = getCameraGridColumns(windowWidth);
```

**Breakpoints:**
- `xs`: 0px - Móvil pequeño (1 columna)
- `sm`: 600px - Móvil grande (2 columnas)
- `md`: 900px - Tablet (2 columnas)
- `lg`: 1200px - Desktop (3 columnas)
- `xl`: 1536px - Desktop grande (4 columnas)

## **🎨 Uso del Tema**

### **Configuración del Tema**

```typescript
// AppProviders.tsx
import { getTheme } from './design-system/theme';

const theme = getTheme('light'); // o 'dark'

<ThemeProvider theme={theme}>
  <App />
</ThemeProvider>
```

### **Acceso a Colores del Tema**

```typescript
// En componentes
import { useTheme } from '@mui/material/styles';

const MyComponent = () => {
  const theme = useTheme();
  
  return (
    <Box sx={{
      backgroundColor: theme.palette.primary.main,
      color: theme.palette.primary.contrastText,
    }}>
      Contenido
    </Box>
  );
};
```

### **Colores Específicos de Cámaras**

```typescript
// Colores de estado de cámaras
import { cameraStatusColors } from './design-system/theme';

const getStatusColor = (status: string) => {
  return cameraStatusColors[status] || cameraStatusColors.unavailable;
};
```

## **🔧 Funciones Utilitarias**

### **Colores**

```typescript
import { 
  hexToRgba, 
  getCameraStatusColor, 
  getChartColors 
} from './design-system/colors';

// Convertir hex a rgba
const transparentBlue = hexToRgba('#2196f3', 0.5);

// Obtener color de estado
const statusColor = getCameraStatusColor('connected');

// Generar colores para gráficos
const chartColors = getChartColors(5);
```

### **Tipografía**

```typescript
import { 
  getTypographyStyles, 
  truncateText 
} from './design-system/typography';

// Aplicar estilos de tipografía
const titleStyle = getTypographyStyles('h1');

// Truncar texto
const ellipsisStyle = truncateText(2); // 2 líneas máximo
```

### **Breakpoints**

```typescript
import { 
  mediaQuery, 
  shouldCollapseSidebar 
} from './design-system/breakpoints';

// Media query
const mobileQuery = mediaQuery('sm');

// Lógica de sidebar
const shouldCollapse = shouldCollapseSidebar(windowWidth);
```

## **🚀 Mejores Prácticas**

### **Consistencia Visual**

1. **Siempre usar tokens del design system**
   ```typescript
   // ✅ Correcto
   color: colorTokens.primary[500]
   
   // ❌ Incorrecto
   color: '#2196f3'
   ```

2. **Usar variantes de tipografía definidas**
   ```typescript
   // ✅ Correcto
   <Typography variant="h1">Título</Typography>
   
   // ❌ Incorrecto
   <Typography sx={{ fontSize: '2rem', fontWeight: 'bold' }}>Título</Typography>
   ```

3. **Aplicar espaciado consistente**
   ```typescript
   // ✅ Correcto
   sx={getPadding('md')}
   
   // ❌ Incorrecto
   sx={{ padding: '16px' }}
   ```

### **Accesibilidad**

1. **Contraste adecuado**
   - Los colores del sistema cumplen WCAG 2.1 AA
   - Usar `contrastText` para texto sobre colores de marca

2. **Tamaños de toque**
   - Botones mínimo 44px de alto
   - Área de toque adecuada en móviles

3. **Texto alternativo**
   - Iconos descriptivos
   - Estados de cámaras claramente identificados

### **Responsive Design**

1. **Grid adaptativo**
   ```typescript
   // Usar configuración automática
   sx={gridStyles.responsiveGrid}
   ```

2. **Breakpoints consistentes**
   ```typescript
   // Usar funciones del sistema
   const columns = getCameraGridColumns(width);
   ```

3. **Sidebar responsivo**
   ```typescript
   // Colapsar automáticamente
   const collapsed = shouldCollapseSidebar(width);
   ```

## **🎯 Componentes Específicos por Página**

### **Página de Cámaras**
- Grid responsivo de cards
- Estados visuales claros
- Botones de acción contextuales
- Métricas en tiempo real

### **Página de Escáner**
- Indicadores de progreso
- Resultados tabulares
- Filtros y ordenamiento
- Estados de carga

### **Página de Analytics**
- Gráficos con paleta consistente
- Métricas destacadas
- Layouts de dashboard
- Exportación de datos

### **Página de Configuración**
- Formularios estructurados
- Validación visual
- Guardado automático
- Respaldos y restauración

## **📊 Métricas y Performance**

### **Carga de Recursos**
- Fuentes optimizadas (Roboto)
- Iconos SVG vectoriales
- Imágenes responsive
- Lazy loading de componentes

### **Experiencia de Usuario**
- Transiciones suaves (300ms)
- Feedback visual inmediato
- Estados de carga claros
- Manejo de errores consistente

## **🔄 Mantenimiento del Sistema**

### **Actualización de Tokens**
1. Modificar valores en `tokens.ts`
2. Regenerar tema automáticamente
3. Probar en modo claro y oscuro
4. Validar contraste y accesibilidad

### **Nuevos Componentes**
1. Definir en `components.ts`
2. Documentar uso en esta guía
3. Crear ejemplos de implementación
4. Agregar tests de componente

### **Extensiones Futuras**
- Más variantes de color
- Componentes especializados
- Animaciones avanzadas
- Temas personalizables

---

## **📞 Contacto y Soporte**

Para dudas sobre el sistema de diseño o implementación de nuevos componentes, consultar la documentación técnica en `src/design-system/` o revisar los ejemplos de uso en los componentes existentes.

**Versión**: 2.0.0  
**Última actualización**: 2024  
**Compatibilidad**: React 19, Material-UI v7, TypeScript 5+ 