# 🎨 Diseño UI - Material Design 3

## 🎯 Filosofía de Diseño

**Universal Camera Viewer** implementa **Material Design 3** con **Flet** para crear una experiencia moderna, accesible y consistente.

### **Principios Clave**

- ✨ **Modern First**: Material Design 3 con componentes elevados
- 🎨 **Adaptive Colors**: ColorScheme dinámico basado en colores semilla
- 📱 **Responsive**: Adaptable a diferentes tamaños de pantalla
- ♿ **Accessible**: Contraste y navegación accesible
- ⚡ **Performance**: Animaciones fluidas y rendering optimizado

## 🎨 Sistema de Colores

### **Color Scheme Principal**

```python
# Color seed: BLUE_700 (#1976d2)
color_scheme = ft.ColorScheme.from_seed(ft.Colors.BLUE_700)

# Paleta resultante
PRIMARY = "#1976d2"           # Azul principal
ON_PRIMARY = "#ffffff"        # Texto sobre primario
PRIMARY_CONTAINER = "#d0e2ff" # Contenedor primario claro
ON_PRIMARY_CONTAINER = "#001d36"

SECONDARY = "#535f70"         # Azul grisáceo
ON_SECONDARY = "#ffffff"
SECONDARY_CONTAINER = "#d7e3f7"
ON_SECONDARY_CONTAINER = "#101c2b"

SURFACE = "#fefbff"          # Superficie principal
ON_SURFACE = "#1a1c1e"       # Texto principal
SURFACE_VARIANT = "#dfe2eb"   # Superficie variante
ON_SURFACE_VARIANT = "#42474e"
```

### **Estados Interactivos**

```python
# Estados de componentes
HOVER_OVERLAY = "rgba(25, 118, 210, 0.08)"    # 8% primario
PRESSED_OVERLAY = "rgba(25, 118, 210, 0.12)"  # 12% primario  
FOCUS_OVERLAY = "rgba(25, 118, 210, 0.12)"    # 12% primario
DISABLED_OVERLAY = "rgba(26, 28, 30, 0.12)"   # 12% on_surface
```

## 🏗️ Arquitectura de Componentes

### **Jerarquía de Layout**

```python
# Estructura principal
MainView
├── AppBar                    # Barra superior
│   ├── Leading (Logo)
│   ├── Title  
│   └── Actions (Settings, Help)
├── NavigationBar            # Navegación Material 3
│   ├── Destination: Scan
│   ├── Destination: Cameras  
│   └── Destination: Analytics
├── Body Container
│   ├── SidePanel (Card)     # Panel lateral elevado
│   │   ├── Connection Card
│   │   ├── Config Card
│   │   └── Status Card
│   └── MainContent
│       ├── CameraGrid       # Grid de cámaras
│       └── StatusBar        # Barra de estado
└── FloatingActionButton     # FAB para acciones rápidas
```

### **Componentes Personalizados**

#### **ElevatedCard**

```python
class ElevatedCard(ft.Container):
    def __init__(self, content, title=None, **kwargs):
        super().__init__(
            content=ft.Column([
                ft.Text(title, style=ft.TextThemeStyle.TITLE_MEDIUM) if title else None,
                content
            ], tight=True),
            padding=16,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=3,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 1)
            ),
            **kwargs
        )
```

#### **ModernTextField**

```python
class ModernTextField(ft.TextField):
    def __init__(self, label, hint_text=None, prefix_icon=None, **kwargs):
        super().__init__(
            label=label,
            hint_text=hint_text,
            prefix_icon=prefix_icon,
            border=ft.InputBorder.OUTLINE,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.SURFACE_VARIANT,
            **kwargs
        )
```

#### **StatusChip**

```python
class StatusChip(ft.Container):
    def __init__(self, status, text):
        color_map = {
            'connected': ft.Colors.GREEN,
            'disconnected': ft.Colors.RED,
            'scanning': ft.Colors.ORANGE,
            'idle': ft.Colors.GREY
        }
        
        super().__init__(
            content=ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=color_map[status]),
                ft.Text(text, size=12)
            ], tight=True),
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=16,
            bgcolor=f"{color_map[status]}20"  # 20% opacity
        )
```

## 📱 Responsive Design

### **Breakpoints y Adaptaciones**

```python
class ResponsiveLayout:
    MOBILE = 600
    TABLET = 900  
    DESKTOP = 1200
    
    def get_layout_config(self, width: int) -> dict:
        if width < self.MOBILE:
            return {
                'side_panel_width': width,           # Full width
                'camera_grid_columns': 1,
                'navigation_type': 'bottom_sheet',   # NavigationBar en bottom
                'show_labels': False
            }
        elif width < self.TABLET:
            return {
                'side_panel_width': 300,
                'camera_grid_columns': 2,
                'navigation_type': 'rail',           # NavigationRail lateral
                'show_labels': True
            }
        else:
            return {
                'side_panel_width': 350,
                'camera_grid_columns': 3,
                'navigation_type': 'drawer',         # NavigationDrawer expandible
                'show_labels': True
            }
```

### **Adaptive Components**

```python
def build_adaptive_navigation(self, width: int) -> ft.Control:
    """Construye navegación adaptativa según ancho de pantalla"""
    config = self.responsive.get_layout_config(width)
    
    destinations = [
        ft.NavigationDestination(
            icon=ft.Icons.RADAR_OUTLINED,
            selected_icon=ft.Icons.RADAR,
            label="Escanear"
        ),
        ft.NavigationDestination(
            icon=ft.Icons.VIDEOCAM_OUTLINED,
            selected_icon=ft.Icons.VIDEOCAM,
            label="Cámaras"
        ),
        ft.NavigationDestination(
            icon=ft.Icons.ANALYTICS_OUTLINED,
            selected_icon=ft.Icons.ANALYTICS,
            label="Analytics"
        )
    ]
    
    if config['navigation_type'] == 'bottom_sheet':
        return ft.NavigationBar(destinations=destinations)
    elif config['navigation_type'] == 'rail':
        return ft.NavigationRail(destinations=destinations)
    else:
        return ft.NavigationDrawer(destinations=destinations)
```

## 🎭 Sistema de Animaciones

### **Transiciones Fluidas**

```python
class AnimationManager:
    def __init__(self):
        self.duration = 200  # ms
        self.curve = ft.AnimationCurve.EASE_OUT
        
    def slide_in_from_right(self, control: ft.Control) -> ft.AnimatedSwitcher:
        """Animación de entrada desde derecha"""
        return ft.AnimatedSwitcher(
            content=control,
            transition=ft.AnimatedSwitcherTransition.SLIDE_FROM_RIGHT,
            duration=self.duration,
            reverse_duration=self.duration,
            switch_in_curve=self.curve,
            switch_out_curve=self.curve
        )
        
    def fade_in(self, control: ft.Control) -> ft.AnimatedOpacity:
        """Animación de fade in"""
        return ft.AnimatedOpacity(
            opacity=1,
            duration=self.duration,
            curve=self.curve,
            content=control
        )
        
    def scale_on_tap(self, control: ft.Control) -> ft.GestureDetector:
        """Efecto de escala al hacer tap"""
        return ft.GestureDetector(
            content=ft.AnimatedContainer(
                content=control,
                duration=100,
                curve=ft.AnimationCurve.EASE_OUT
            ),
            on_tap_down=lambda e: self._scale_down(e.control),
            on_tap_up=lambda e: self._scale_up(e.control),
            on_tap_cancel=lambda e: self._scale_up(e.control)
        )
```

### **Estados de Loading**

```python
class LoadingStates:
    @staticmethod
    def spinner() -> ft.ProgressRing:
        """Spinner de carga Material 3"""
        return ft.ProgressRing(
            width=24,
            height=24,
            stroke_width=3,
            color=ft.Colors.PRIMARY
        )
        
    @staticmethod
    def skeleton_card() -> ft.Container:
        """Skeleton loading para cards"""
        return ft.Container(
            width=300,
            height=200,
            border_radius=12,
            gradient=ft.LinearGradient(
                colors=[
                    ft.Colors.SURFACE_VARIANT,
                    ft.Colors.SURFACE,
                    ft.Colors.SURFACE_VARIANT
                ],
                stops=[0.0, 0.5, 1.0]
            ),
            animate=ft.Animation(2000, ft.AnimationCurve.LINEAR)
        )
        
    @staticmethod
    def progress_indicator(progress: float) -> ft.Container:
        """Indicador de progreso con porcentaje"""
        return ft.Container(
            content=ft.Column([
                ft.ProgressBar(value=progress, height=8, border_radius=4),
                ft.Text(f"{progress*100:.0f}%", size=12, text_align=ft.TextAlign.CENTER)
            ], spacing=8),
            padding=16
        )
```

## 🌙 Sistema de Temas

### **Configuración de Tema**

```python
class ThemeManager:
    def __init__(self):
        self.current_theme = "auto"  # auto, light, dark
        
    def get_theme_data(self) -> ft.Theme:
        """Genera configuración de tema Material 3"""
        return ft.Theme(
            color_scheme_seed=ft.Colors.BLUE_700,
            use_material3=True,
            visual_density=ft.ThemeVisualDensity.ADAPTIVE,
            font_family="Roboto"
        )
        
    def get_dark_theme_data(self) -> ft.Theme:
        """Tema oscuro Material 3"""
        return ft.Theme(
            color_scheme_seed=ft.Colors.BLUE_700,
            use_material3=True,
            visual_density=ft.ThemeVisualDensity.ADAPTIVE,
            font_family="Roboto"
        )
```

### **Configuración de Tipografía**

```python
# Material Design 3 Typography Scale
TYPOGRAPHY = {
    'display_large': ft.TextStyle(size=57, weight=ft.FontWeight.W400),
    'display_medium': ft.TextStyle(size=45, weight=ft.FontWeight.W400),
    'display_small': ft.TextStyle(size=36, weight=ft.FontWeight.W400),
    
    'headline_large': ft.TextStyle(size=32, weight=ft.FontWeight.W400),
    'headline_medium': ft.TextStyle(size=28, weight=ft.FontWeight.W400),
    'headline_small': ft.TextStyle(size=24, weight=ft.FontWeight.W400),
    
    'title_large': ft.TextStyle(size=22, weight=ft.FontWeight.W400),
    'title_medium': ft.TextStyle(size=16, weight=ft.FontWeight.W500),
    'title_small': ft.TextStyle(size=14, weight=ft.FontWeight.W500),
    
    'body_large': ft.TextStyle(size=16, weight=ft.FontWeight.W400),
    'body_medium': ft.TextStyle(size=14, weight=ft.FontWeight.W400),
    'body_small': ft.TextStyle(size=12, weight=ft.FontWeight.W400),
    
    'label_large': ft.TextStyle(size=14, weight=ft.FontWeight.W500),
    'label_medium': ft.TextStyle(size=12, weight=ft.FontWeight.W500),
    'label_small': ft.TextStyle(size=11, weight=ft.FontWeight.W500)
}
```

## 🎯 Guidelines de UX

### **Principios de Interacción**

1. **🎯 Feedback Inmediato**
   - Hover states en todos los elementos interactivos
   - Pressed states con animaciones de escala
   - Loading states durante operaciones asíncronas

2. **📍 Navegación Clara**
   - Breadcrumbs para navegación profunda
   - Estados activos visibles en navegación
   - Shortcuts de teclado documentados

3. **⚠️ Manejo de Errores**
   - Snackbars para errores no críticos
   - Dialogs para errores que requieren acción
   - Estados de error inline en formularios

4. **📊 Información Contextual**
   - Tooltips para iconos sin etiqueta
   - Status chips para estados de conexión
   - Progress indicators para operaciones largas

### **Patrones de Interacción**

```python
# Patrón: Confirmación de acciones destructivas
def show_delete_confirmation(self, item_name: str):
    return ft.AlertDialog(
        title=ft.Text("Confirmar eliminación"),
        content=ft.Text(f"¿Eliminar {item_name}? Esta acción no se puede deshacer."),
        actions=[
            ft.TextButton("Cancelar", on_click=self.close_dialog),
            ft.ElevatedButton(
                "Eliminar", 
                style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR),
                on_click=self.confirm_delete
            )
        ]
    )

# Patrón: Feedback de acciones exitosas
def show_success_snackbar(self, message: str):
    return ft.SnackBar(
        content=ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN),
            ft.Text(message)
        ]),
        bgcolor=ft.Colors.SURFACE_VARIANT
    )
```

## 📏 Especificaciones de Diseño

### **Spacing System (8dp Grid)**

```python
SPACING = {
    'xs': 4,    # 0.5 units
    'sm': 8,    # 1 unit
    'md': 16,   # 2 units  
    'lg': 24,   # 3 units
    'xl': 32,   # 4 units
    'xxl': 48   # 6 units
}

# Aplicación en componentes
card_padding = SPACING['md']      # 16dp
button_spacing = SPACING['sm']    # 8dp
section_spacing = SPACING['lg']   # 24dp
```

### **Elevación y Sombras**

```python
ELEVATION = {
    'level_0': None,  # Sin sombra
    'level_1': ft.BoxShadow(         # Cards en reposo
        spread_radius=0,
        blur_radius=3,
        color=ft.Colors.BLACK12,
        offset=ft.Offset(0, 1)
    ),
    'level_2': ft.BoxShadow(         # Cards hover
        spread_radius=0, 
        blur_radius=6,
        color=ft.Colors.BLACK12,
        offset=ft.Offset(0, 2)
    ),
    'level_3': ft.BoxShadow(         # FAB, Dialogs
        spread_radius=0,
        blur_radius=12,
        color=ft.Colors.BLACK12, 
        offset=ft.Offset(0, 4)
    )
}
```

## 🎯 Próximos Pasos

1. **[🏛️ Entender Arquitectura](architecture.md)** - Estructura MVP del proyecto
2. **[💻 Setup Desarrollo](development.md)** - Configurar entorno de desarrollo
3. **[📦 Instalación](installation.md)** - Setup inicial del proyecto

---

**🎨 Design System:** Material Design 3 completo con Flet  
**📱 Responsive:** Adaptativo a mobile, tablet y desktop  
**♿ Accessibility:** Contraste y navegación accesible por defecto

---

### 📚 Navegación

[← Anterior: Características Detalladas](FEATURES.md) | [📑 Índice](README.md) | [Siguiente: Compatibilidad de Cámaras →](CAMERA_COMPATIBILITY.md)
