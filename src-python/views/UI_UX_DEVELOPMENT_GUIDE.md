# Guía de Desarrollo UI/UX Moderna con Flet
*Orientada para Modelos de AI - Universal Camera Viewer*

## 📋 Índice
1. [Principios Fundamentales](#principios-fundamentales)
2. [Material Design 3 en Flet](#material-design-3-en-flet)
3. [Arquitectura de Componentes](#arquitectura-de-componentes)
4. [Patrones de UI Modernos](#patrones-de-ui-modernos)
5. [Responsive Design](#responsive-design)
6. [Animaciones y Transiciones](#animaciones-y-transiciones)
7. [Accesibilidad](#accesibilidad)
8. [Performance y Optimización](#performance-y-optimización)
9. [Componentes Modernos](#componentes-modernos)
10. [Mejores Prácticas](#mejores-prácticas)

---

## 🎯 Principios Fundamentales

### **1. Material Design 3 (Material You)**
```python
# USAR: Colores semánticos del sistema
ft.Colors.PRIMARY           # Color primario dinámico
ft.Colors.ON_PRIMARY        # Texto sobre color primario
ft.Colors.SURFACE           # Superficies de contenido
ft.Colors.ON_SURFACE        # Texto sobre superficies
ft.Colors.OUTLINE_VARIANT   # Bordes sutiles

# EVITAR: Colores hardcodeados
ft.Colors.BLUE_500  # ❌ No usar colores específicos
"#FF0000"          # ❌ No usar hex directo
```

### **2. Elevación y Profundidad**
```python
# Sombras Material 3
ft.BoxShadow(
    spread_radius=0,
    blur_radius=6,
    color=ft.Colors.with_opacity(0.10, ft.Colors.SHADOW),
    offset=ft.Offset(0, 2)
)

# Niveles de elevación
ELEVATION_LEVELS = {
    "surface": 0,      # Superficie base
    "card": 1,         # Cards y elementos
    "app_bar": 2,      # Barras de navegación
    "fab": 3,          # Botones flotantes
    "dialog": 5        # Diálogos y modales
}
```

### **3. Tipografía Moderna**
```python
# Jerarquía tipográfica
TYPOGRAPHY = {
    "display_large": {"size": 57, "weight": ft.FontWeight.W_400},
    "display_medium": {"size": 45, "weight": ft.FontWeight.W_400},
    "display_small": {"size": 36, "weight": ft.FontWeight.W_400},
    "headline_large": {"size": 32, "weight": ft.FontWeight.W_600},
    "headline_medium": {"size": 28, "weight": ft.FontWeight.W_600},
    "headline_small": {"size": 24, "weight": ft.FontWeight.W_600},
    "title_large": {"size": 22, "weight": ft.FontWeight.W_500},
    "title_medium": {"size": 16, "weight": ft.FontWeight.W_500},
    "title_small": {"size": 14, "weight": ft.FontWeight.W_500},
    "body_large": {"size": 16, "weight": ft.FontWeight.W_400},
    "body_medium": {"size": 14, "weight": ft.FontWeight.W_400},
    "body_small": {"size": 12, "weight": ft.FontWeight.W_400},
    "label_large": {"size": 14, "weight": ft.FontWeight.W_500},
    "label_medium": {"size": 12, "weight": ft.FontWeight.W_500},
    "label_small": {"size": 11, "weight": ft.FontWeight.W_500}
}
```

---

## 🎨 Material Design 3 en Flet

### **1. Sistema de Colores**
```python
# Paleta de colores dinámica
class ColorScheme:
    def __init__(self):
        # Colores primarios
        self.primary = ft.Colors.PRIMARY
        self.on_primary = ft.Colors.ON_PRIMARY
        self.primary_container = ft.Colors.PRIMARY_CONTAINER
        self.on_primary_container = ft.Colors.ON_PRIMARY_CONTAINER
        
        # Colores secundarios
        self.secondary = ft.Colors.SECONDARY
        self.on_secondary = ft.Colors.ON_SECONDARY
        self.secondary_container = ft.Colors.SECONDARY_CONTAINER
        self.on_secondary_container = ft.Colors.ON_SECONDARY_CONTAINER
        
        # Colores de superficie
        self.surface = ft.Colors.SURFACE
        self.on_surface = ft.Colors.ON_SURFACE
        self.surface_variant = ft.Colors.SURFACE_VARIANT
        self.on_surface_variant = ft.Colors.ON_SURFACE_VARIANT
        
        # Colores de estado
        self.error = ft.Colors.ERROR
        self.on_error = ft.Colors.ON_ERROR
        self.success = ft.Colors.GREEN_600
        self.warning = ft.Colors.ORANGE_600
```

### **2. Componentes con Estados**
```python
# Botones con estados interactivos
ft.FilledButton(
    text="Acción Principal",
    style=ft.ButtonStyle(
        bgcolor={
            ft.ControlState.DEFAULT: ft.Colors.PRIMARY,
            ft.ControlState.HOVERED: ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY),
            ft.ControlState.PRESSED: ft.Colors.with_opacity(0.8, ft.Colors.PRIMARY),
            ft.ControlState.DISABLED: ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)
        },
        color={
            ft.ControlState.DEFAULT: ft.Colors.ON_PRIMARY,
            ft.ControlState.DISABLED: ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
        },
        elevation={
            ft.ControlState.DEFAULT: 1,
            ft.ControlState.HOVERED: 3,
            ft.ControlState.PRESSED: 1
        }
    )
)
```

### **3. Borders y Shapes**
```python
# Bordes redondeados modernos
BORDER_RADIUS = {
    "none": 0,
    "extra_small": 4,
    "small": 8,
    "medium": 12,
    "large": 16,
    "extra_large": 28,
    "full": 50
}

# Aplicación
ft.Container(
    border_radius=BORDER_RADIUS["medium"],  # 12px
    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
)
```

---

## 🏗️ Arquitectura de Componentes

### **1. Estructura Jerárquica**
```
src/views/
├── components/
│   ├── common/          # Componentes básicos reutilizables
│   │   ├── modern_button.py
│   │   ├── stat_card.py
│   │   └── progress_indicator.py
│   ├── layout/          # Componentes de diseño
│   │   ├── toolbar.py
│   │   ├── side_panel.py
│   │   └── status_bar.py
│   └── navigation/      # Navegación
│       └── navigation_bar.py
├── pages/               # Páginas completas
│   ├── cameras_page.py
│   ├── scan_page.py
│   └── settings_page.py
└── main_view.py        # Vista principal
```

### **2. Componente Base Moderno**
```python
class ModernComponent(ft.Container):
    """Componente base con Material Design 3."""
    
    def __init__(
        self,
        content: ft.Control,
        elevation: int = 0,
        color_scheme: str = "primary",
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Configuración base
        self.bgcolor = ft.Colors.SURFACE
        self.border_radius = 12
        self.padding = ft.padding.all(16)
        
        # Sombra según elevación
        if elevation > 0:
            self.shadow = self._create_shadow(elevation)
        
        # Aplicar esquema de color
        self._apply_color_scheme(color_scheme)
        
        # Contenido
        self.content = content
    
    def _create_shadow(self, elevation: int) -> ft.BoxShadow:
        """Crea sombra según nivel de elevación."""
        return ft.BoxShadow(
            spread_radius=0,
            blur_radius=elevation * 2,
            color=ft.Colors.with_opacity(0.1, ft.Colors.SHADOW),
            offset=ft.Offset(0, elevation)
        )
```

### **3. Composición de Componentes**
```python
# CORRECTO: Composición modular
class CameraCard(ModernComponent):
    def __init__(self, camera_data: CameraInfo):
        # Header
        header = self._build_header(camera_data)
        
        # Content
        content = self._build_content(camera_data)
        
        # Actions
        actions = self._build_actions(camera_data)
        
        # Componer
        full_content = ft.Column([header, content, actions])
        
        super().__init__(
            content=full_content,
            elevation=1,
            color_scheme="surface"
        )
```

---

## 🎛️ Patrones de UI Modernos

### **1. Cards y Superficies**
```python
# Card moderna con elevación
ft.Container(
    content=your_content,
    bgcolor=ft.Colors.SURFACE,
    border_radius=16,
    padding=ft.padding.all(20),
    shadow=ft.BoxShadow(
        spread_radius=0,
        blur_radius=8,
        color=ft.Colors.with_opacity(0.12, ft.Colors.SHADOW),
        offset=ft.Offset(0, 4)
    ),
    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
)
```

### **2. Layouts Flexibles**
```python
# Layout responsivo con Row y Column
ft.Row([
    # Sidebar
    ft.Container(
        content=sidebar_content,
        width=280,
        padding=ft.padding.all(16)
    ),
    
    # Main content
    ft.Container(
        content=main_content,
        expand=True,  # Ocupa espacio restante
        padding=ft.padding.all(20)
    )
], spacing=0)
```

### **3. Grids Modernos**
```python
# Grid responsivo
ft.GridView(
    expand=True,
    runs_count=3,           # Número de columnas
    max_extent=300,         # Ancho máximo por item
    child_aspect_ratio=1.2, # Relación aspecto
    spacing=16,             # Espacio horizontal
    run_spacing=16,         # Espacio vertical
    padding=ft.padding.all(16)
)
```

### **4. Navegación Moderna**
```python
# Navigation Bar con Material 3
ft.NavigationBar(
    destinations=[
        ft.NavigationDestination(
            icon=ft.Icons.VIDEOCAM_OUTLINED,
            selected_icon=ft.Icons.VIDEOCAM,
            label="Cámaras"
        ),
        ft.NavigationDestination(
            icon=ft.Icons.SEARCH_OUTLINED,
            selected_icon=ft.Icons.SEARCH,
            label="Escaneo"
        )
    ],
    on_change=handle_nav_change
)
```

---

## 📱 Responsive Design

### **1. Breakpoints**
```python
BREAKPOINTS = {
    "mobile": 480,
    "tablet": 768,
    "desktop": 1024,
    "wide": 1440
}

def get_screen_size(page_width: int) -> str:
    """Determina el tamaño de pantalla."""
    if page_width < BREAKPOINTS["mobile"]:
        return "mobile"
    elif page_width < BREAKPOINTS["tablet"]:
        return "tablet"
    elif page_width < BREAKPOINTS["desktop"]:
        return "desktop"
    else:
        return "wide"
```

### **2. Layouts Adaptativos**
```python
def create_responsive_layout(page_width: int) -> ft.Control:
    """Crea layout según tamaño de pantalla."""
    
    screen_size = get_screen_size(page_width)
    
    if screen_size == "mobile":
        return ft.Column([
            header,
            main_content,
            footer
        ])
    else:
        return ft.Row([
            sidebar,
            ft.Container(
                content=ft.Column([header, main_content, footer]),
                expand=True
            )
        ])
```

### **3. Componentes Flexibles**
```python
# Grid que se adapta al ancho
def create_responsive_grid(page_width: int) -> ft.GridView:
    columns = max(1, page_width // 320)  # Mínimo 320px por columna
    
    return ft.GridView(
        runs_count=columns,
        max_extent=320,
        child_aspect_ratio=1.3,
        spacing=16,
        run_spacing=16
    )
```

---

## ✨ Animaciones y Transiciones

### **1. Transiciones Suaves**
```python
# Container con transición
ft.Container(
    content=your_content,
    animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
    bgcolor=ft.Colors.SURFACE
)

# Opacidad animada
ft.Container(
    content=your_content,
    animate_opacity=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
)
```

### **2. Micro-interacciones**
```python
# Botón con hover effect
ft.Container(
    content=ft.Text("Hover me"),
    bgcolor=ft.Colors.SURFACE,
    padding=ft.padding.all(12),
    border_radius=8,
    animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
    on_hover=lambda e: animate_hover(e.control, e.data)
)

def animate_hover(control: ft.Container, is_hover: bool):
    if is_hover:
        control.bgcolor = ft.Colors.SURFACE_VARIANT
        control.shadow = ft.BoxShadow(blur_radius=8)
    else:
        control.bgcolor = ft.Colors.SURFACE
        control.shadow = ft.BoxShadow(blur_radius=2)
    control.update()
```

### **3. Loading States**
```python
# Skeleton loading
ft.Container(
    height=60,
    bgcolor=ft.Colors.SURFACE_VARIANT,
    border_radius=8,
    animate=ft.animation.Animation(
        1000, 
        ft.AnimationCurve.EASE_IN_OUT,
        reverse=True,
        repeat=True
    )
)

# Progress ring moderno
ft.ProgressRing(
    width=40,
    height=40,
    color=ft.Colors.PRIMARY,
    bgcolor=ft.Colors.SURFACE_VARIANT,
    stroke_width=4
)
```

---

## ♿ Accesibilidad

### **1. Semántica y Etiquetas**
```python
# Tooltips informativos
ft.IconButton(
    icon=ft.Icons.SETTINGS,
    tooltip="Abrir configuración",
    on_click=open_settings
)

# Etiquetas semánticas
ft.TextField(
    label="Dirección IP",
    hint_text="Ej: 192.168.1.100",
    helper_text="Ingrese la IP de la cámara"
)
```

### **2. Contraste y Legibilidad**
```python
# Verificar contraste WCAG
def check_contrast_ratio(fg_color: str, bg_color: str) -> float:
    """Verifica ratio de contraste WCAG."""
    # Implementar cálculo de contraste
    pass

# Colores accesibles
ACCESSIBLE_COLORS = {
    "high_contrast": {
        "text": ft.Colors.BLACK,
        "background": ft.Colors.WHITE
    },
    "low_light": {
        "text": ft.Colors.WHITE,
        "background": ft.Colors.GREY_900
    }
}
```

### **3. Navegación por Teclado**
```python
# Focus management
ft.FilledButton(
    text="Botón",
    autofocus=True,  # Focus automático
    on_click=handle_click
)

# Tab order
ft.Column([
    ft.TextField(tab_index=1),
    ft.TextField(tab_index=2),
    ft.FilledButton(text="Submit", tab_index=3)
])
```

---

## ⚡ Performance y Optimización

### **1. Lazy Loading**
```python
# Lista virtual para grandes datasets
ft.ListView(
    expand=True,
    spacing=8,
    controls=[
        create_item(item) for item in visible_items  # Solo items visibles
    ]
)
```

### **2. Memoización de Componentes**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def create_camera_card(camera_id: str, camera_data: dict) -> ft.Container:
    """Crea card de cámara con memoización."""
    return ft.Container(
        content=build_camera_content(camera_data),
        # ... resto de configuración
    )
```

### **3. Optimización de Updates**
```python
# Batch updates
def update_cameras_batch(cameras: List[CameraInfo]):
    """Actualiza múltiples cámaras en batch."""
    
    # Preparar todos los cambios
    updates = []
    for camera in cameras:
        updates.append(create_camera_update(camera))
    
    # Aplicar todos los cambios de una vez
    page.update_batch(updates)
```

---

## 🧩 Componentes Modernos

### **1. Floating Action Button**
```python
ft.FloatingActionButton(
    icon=ft.Icons.ADD,
    bgcolor=ft.Colors.PRIMARY,
    foreground_color=ft.Colors.ON_PRIMARY,
    tooltip="Agregar cámara",
    on_click=add_camera,
    shape=ft.CircleBorder()
)
```

### **2. Chips y Tags**
```python
ft.Chip(
    label=ft.Text("Conectado"),
    leading=ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN),
    bgcolor=ft.Colors.GREEN_100,
    selected=True,
    on_click=handle_chip_click
)
```

### **3. Snackbars y Toasts**
```python
# Snackbar moderno
page.snack_bar = ft.SnackBar(
    content=ft.Text("Cámara conectada exitosamente"),
    bgcolor=ft.Colors.SUCCESS,
    action="Deshacer",
    action_color=ft.Colors.ON_SUCCESS,
    duration=4000
)
page.snack_bar.open = True
```

### **4. Dialogs Modernos**
```python
ft.AlertDialog(
    title=ft.Text("Confirmar acción"),
    content=ft.Text("¿Estás seguro que deseas continuar?"),
    actions=[
        ft.TextButton("Cancelar", on_click=close_dialog),
        ft.FilledButton("Confirmar", on_click=confirm_action)
    ],
    shape=ft.RoundedRectangleBorder(radius=16)
)
```

---

## 🎯 Mejores Prácticas

### **1. Estructura de Archivos**
```python
# CORRECTO: Un componente por archivo
# modern_button.py
class ModernButton(ft.Container):
    pass

# INCORRECTO: Múltiples componentes en un archivo
# components.py - ❌ Evitar
class Button1, Button2, Button3: pass
```

### **2. Naming Conventions**
```python
# CORRECTO: Nombres descriptivos
class CameraConnectionButton(ft.FilledButton):
    pass

# INCORRECTO: Nombres genéricos
class Btn1(ft.FilledButton):  # ❌ Evitar
    pass
```

### **3. Props y Configuration**
```python
# CORRECTO: Props tipadas
@dataclass
class ButtonConfig:
    text: str
    variant: str = "filled"
    color_scheme: str = "primary"
    disabled: bool = False

class ModernButton(ft.Container):
    def __init__(self, config: ButtonConfig):
        pass
```

### **4. State Management**
```python
# CORRECTO: Estado centralizado
class ComponentState:
    def __init__(self):
        self.is_loading = False
        self.error_message = None
        self.data = None
    
    def set_loading(self, loading: bool):
        self.is_loading = loading
        self.notify_listeners()
```

### **5. Error Handling**
```python
# CORRECTO: Manejo de errores graceful
def create_camera_card(camera_data: dict) -> ft.Container:
    try:
        return ft.Container(
            content=build_camera_content(camera_data)
        )
    except Exception as e:
        logger.error(f"Error creating camera card: {e}")
        return ft.Container(
            content=ft.Text("Error loading camera"),
            bgcolor=ft.Colors.ERROR_CONTAINER
        )
```

---

## 🚀 Checklist de Desarrollo

### **Antes de Implementar**
- [ ] Definir esquema de colores Material 3
- [ ] Establecer jerarquía tipográfica
- [ ] Planificar estructura de componentes
- [ ] Considerar estados responsive
- [ ] Verificar accesibilidad

### **Durante Desarrollo**
- [ ] Usar colores semánticos del sistema
- [ ] Implementar estados interactivos
- [ ] Agregar transiciones suaves
- [ ] Optimizar para performance
- [ ] Testear en diferentes tamaños

### **Después de Implementar**
- [ ] Verificar contraste WCAG
- [ ] Testear navegación por teclado
- [ ] Validar responsive design
- [ ] Optimizar tiempo de carga
- [ ] Documentar componente

---

## 📚 Recursos Adicionales

### **Referencias Material Design 3**
- [Material 3 Design System](https://m3.material.io/)
- [Color System](https://m3.material.io/styles/color/overview)
- [Typography](https://m3.material.io/styles/typography/overview)

### **Flet Documentation**
- [Flet Controls](https://flet.dev/docs/controls)
- [Flet Styling](https://flet.dev/docs/guides/styling)
- [Flet Layout](https://flet.dev/docs/guides/layout)

### **Herramientas de Desarrollo**
- [Material Theme Builder](https://m3.material.io/theme-builder)
- [Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

*Esta guía debe ser actualizada conforme evolucionen las capacidades de Flet y las mejores prácticas de UI/UX moderna.* 