# Visor Universal de Cámaras Multi-Marca

> **Sistema de videovigilancia profesional** con soporte nativo para múltiples marcas de cámaras IP: Dahua, TP-Link, Steren y cámaras genéricas chinas. Arquitectura modular SOLID con interfaz moderna y protocolos optimizados.

![Estado del Proyecto](https://img.shields.io/badge/Estado-100%25%20Completado-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B%20(Probado%203.13.1)-blue)
![Licencia](https://img.shields.io/badge/Licencia-MIT-green)
![Autor](https://img.shields.io/badge/Autor-JorgeTato99-orange)

## 🎯 **¿Qué es este proyecto?**

**Visor Universal de Cámaras** es una aplicación Python profesional que conecta, visualiza y controla cámaras IP de múltiples marcas desde una sola interfaz. Desarrollado con principios SOLID y arquitectura modular para máxima extensibilidad.

### **Características Principales**

- 🎥 **Soporte Multi-Marca**: Dahua, TP-Link, Steren, cámaras chinas genéricas
- 🚀 **Protocolos Optimizados**: ONVIF (principal), RTSP, HTTP/CGI, SDK nativo
- 🖥️ **Interfaz Moderna**: Layouts inteligentes, sistema de columnspan optimizado
- ⚡ **Alto Rendimiento**: 13-20+ FPS según marca, threading no-bloqueante
- 🔧 **Configuración Automática**: Detección de marca y configuración específica
- 📱 **Múltiples Layouts**: 1x1, 2x2, 3x3, 4x3 con columnspan inteligente
- 📸 **Snapshots HD**: Captura instantánea en alta calidad
- 🎮 **Controles PTZ**: Soporte ONVIF para pan/tilt/zoom
- 🔍 **Descubrimiento Avanzado**: Port Discovery con UX optimizada y herramientas de red

---

## 🚀 **Inicio Rápido (5 minutos)**

### **1. Instalación**

```bash
# Clonar y configurar
git clone https://github.com/JorgeTato99/universal-camera-viewer.git
cd universal-camera-viewer

# Entorno virtual
python -m venv .venv
.\.venv\Scripts\activate          # Windows
source .venv/bin/activate         # Linux/MacOS

# Dependencias
pip install -r requirements.txt
```

### **2. Configuración**

```bash
# Crear configuración
cp .env.example .env

# Editar .env con tus cámaras
# DAHUA_IP=192.168.1.172
# DAHUA_USER=admin
# DAHUA_PASSWORD=tu_password
```

### **3. Ejecutar**

```bash
# Visor completo con interfaz gráfica
python examples/gui/viewer_example.py

# O prueba rápida de conexión
python examples/protocols/onvif_example.py
```

---

## 📋 **Marcas y Compatibilidad**

| Marca | Modelo Probado | ONVIF | RTSP | Estado |
|-------|----------------|-------|------|--------|
| **Dahua** | Hero-K51H | ✅ Puerto 80 | ✅ Con DMSS | 🎯 Excelente |
| **TP-Link** | Tapo C520WS | ✅ Puerto 2020 | ✅ Directo | 🎯 Excelente |
| **Steren** | CCTV-235 | ✅ Puerto 8000 | ✅ Puerto 5543 | 🎯 Excelente |
| **China Genérica** | 8MP WiFi | 🔍 Detección Auto | ✅ 16+ patrones | 🎯 Excelente |

### **Rendimiento por Marca**

- **Dahua Hero-K51H**: 13.86 FPS (ONVIF), 15.32 FPS (RTSP), 4K
- **TP-Link Tapo**: Variable según perfil, detección automática
- **Steren CCTV-235**: 20+ FPS, dual-stream (4MP + 360p)
- **Cámaras Genéricas**: 5.9MP @ 12 FPS promedio

---

## 🖥️ **Interfaz y Características**

### **Sistema de Layouts Inteligente**

```text
Layouts Disponibles:
┌─────────────┬─────────────┬─────────────┐
│    1x1      │    2x2      │    3x3      │
│ ┌─────────┐ │ ┌───┬───┐   │ ┌─┬─┬─┐     │
│ │   Cam   │ │ │ 1 │ 2 │   │ │1│2│3│     │
│ └─────────┘ │ ├───┼───┤   │ ├─┼─┼─┤     │
│             │ │ 3 │ 4 │   │ │4│5│6│     │
│             │ └───┴───┘   │ ├─┼─┼─┤     │
│             │             │ │7│8│9│     │
│             │             │ └─┴─┴─┘     │
└─────────────┴─────────────┴─────────────┘
```

**Características del Layout:**

- **Columnspan Inteligente**: Cámaras solitarias ocupan todo el ancho
- **Redimensionado Automático**: Layout se adapta al número de cámaras
- **Configuración Persistente**: Se guarda automáticamente

### **Herramientas de Descubrimiento Avanzadas**

#### **🔍 Port Discovery con UX Optimizada**

**Características Principales:**

- **Validación en Tiempo Real**: IP, configuración y estado visual
- **Shortcuts de Teclado**: F5 (escanear), Esc (detener), Ctrl+L (limpiar)
- **Filtros Avanzados**: Búsqueda, mostrar/ocultar estados, estadísticas dinámicas
- **Exportación Múltiple**: CSV, JSON, TXT, HTML con reportes detallados
- **Historial Inteligente**: IPs utilizadas, autocompletado, patrones comunes

**Interfaz Mejorada:**

- **Barra de Estado**: Validación continua con indicadores visuales (✅/❌)
- **Estadísticas en Tiempo Real**: Contadores de puertos abiertos/cerrados
- **Vista Dual**: Tabla de resultados + consola técnica con colores
- **Tooltips Informativos**: Ayuda contextual en todos los controles
- **Animaciones Sutiles**: Feedback visual para mejor experiencia

**Funcionalidades Técnicas:**

- **Autocompletado de IP**: Patrones comunes (192.168.1.x, 10.0.0.x)
- **Presets de Configuración**: Rápido, balanceado, exhaustivo
- **Métricas de Rendimiento**: Velocidad, tiempo estimado, progreso detallado
- **Configuración Avanzada**: Diálogo modal con opciones técnicas

### **Panel de Control Avanzado**

- **Pestaña Configuración**: Protocolos, credenciales, puertos específicos
- **Pestaña Cámaras**: Gestión individual, snapshots HD, reconexión manual
- **Pestaña Layouts**: Control de layouts con previsualización
- **Pestaña Descubrimiento**: Port Discovery con herramientas de red

---

## 🔧 **Arquitectura Técnica**

### **Patrones de Diseño Implementados**

- **Factory Pattern**: `ConnectionFactory` para crear conexiones
- **Template Method**: `BaseConnection` como clase abstracta
- **Singleton**: `ConfigurationManager` para configuración global
- **Observer**: Sistema de eventos para UI
- **Component Pattern**: Módulos UI especializados y reutilizables

### **Estructura Modular**

```bash
src/
├── connections/          # Protocolos de conexión
│   ├── base_connection.py    # Clase abstracta base
│   ├── onvif_connection.py   # Protocolo ONVIF
│   ├── rtsp_connection.py    # Protocolo RTSP
│   ├── tplink_connection.py  # TP-Link especializado
│   ├── steren_connection.py  # Steren CCTV-235
│   └── generic_connection.py # Cámaras genéricas
├── viewer/               # Interfaz gráfica
│   ├── real_time_viewer.py   # Aplicación principal
│   ├── camera_widget.py      # Widget individual
│   └── control_panel.py      # Panel de control
├── gui/                  # Interfaces especializadas
│   ├── main_application.py   # Aplicación principal
│   └── discovery/            # Herramientas de descubrimiento
│       ├── port_discovery_view.py      # Vista principal
│       └── components/                 # Componentes modulares
│           ├── scan_config_panel.py        # Panel configuración
│           ├── scan_progress_panel.py      # Panel progreso
│           ├── scan_results_panel.py       # Panel resultados
│           ├── ip_selector_widget.py       # Selector IP avanzado
│           └── credentials_widget.py       # Widget credenciales
└── utils/                # Utilidades
    ├── config.py             # Gestor de configuración
    ├── brand_manager.py      # Gestor de marcas
    └── camera_brands.json    # Configuración de marcas
```

---

## 💻 **Ejemplos de Uso**

### **Conexión Básica**

```python
from src.connections import ConnectionFactory
from src.utils.config import ConfigurationManager

# Configuración automática
config = ConfigurationManager()

# Conexión ONVIF (recomendado)
connection = ConnectionFactory.create_connection(
    connection_type='onvif',
    config_manager=config,
    camera_brand='dahua'
)

# Usar la conexión
with connection:
    # Stream en tiempo real
    frame = connection.get_frame()
    
    # Información del dispositivo
    info = connection.get_device_info()
    print(f"Conectado: {info['brand']} {info['model']}")
    
    # Snapshot HD
    connection.capture_snapshot("snapshot.jpg")
```

### **Visor Multi-Cámara**

```python
from src.viewer import RealTimeViewer

# Crear visor con layout 2x2
viewer = RealTimeViewer()
viewer.set_layout("2x2")

# Agregar cámaras
viewer.add_camera("Dahua Principal", "onvif", "dahua")
viewer.add_camera("TP-Link Entrada", "onvif", "tplink")
viewer.add_camera("Steren Patio", "steren", "steren")

# Iniciar visualización
viewer.show()
```

### **Descubrimiento de Red**

```python
from src.gui.discovery import PortDiscoveryView

# Crear herramienta de descubrimiento
discovery = PortDiscoveryView(parent_container)

# Configurar escaneo
discovery.set_target_ip("192.168.1.0/24")
discovery.set_scan_mode("advanced")  # Con autenticación

# Iniciar escaneo con callbacks
discovery.start_scan(
    on_port_found=lambda port, service: print(f"Puerto {port}: {service}"),
    on_complete=lambda results: print(f"Escaneo completo: {len(results)} puertos")
)
```

---

## 🛠️ **Configuración Avanzada**

### **Variables de Entorno (.env)**

```bash
# Dahua Hero-K51H
DAHUA_IP=192.168.1.172
DAHUA_USER=admin
DAHUA_PASSWORD=tu_password
DAHUA_ONVIF_PORT=80

# TP-Link Tapo
TPLINK_IP=192.168.1.77
TPLINK_USER=admin
TPLINK_PASSWORD=tu_password
TPLINK_ONVIF_PORT=2020

# Steren CCTV-235
STEREN_IP=192.168.1.178
STEREN_USER=admin
STEREN_PASSWORD=tu_password

# Cámara Genérica (opcional)
GENERIC_IP=192.168.1.180
GENERIC_USER=admin
GENERIC_PASSWORD=tu_password
```

### **Configuración por Código**

```python
# Configuración manual específica
config = {
    'ip': '192.168.1.100',
    'user': 'admin',
    'password': 'mi_password',
    'onvif_port': 8000,
    'rtsp_port': 554,
    'brand': 'custom'
}

connection = ConnectionFactory.create_connection(
    'onvif', config_manager=None, camera_brand='custom'
)
connection.configure_manual(config)
```

---

## 🧪 **Testing y Ejemplos**

### **Estructura de Ejemplos**

```bash
examples/
├── protocols/                # Testing de protocolos
│   ├── onvif_example.py         # Prueba ONVIF multi-marca
│   ├── rtsp_example.py          # Prueba RTSP directo
│   └── amcrest_example.py       # Prueba HTTP/CGI
├── gui/                      # Interfaces gráficas
│   ├── viewer_example.py        # Visor completo
│   ├── components_demo.py       # Demo de componentes
│   └── discovery_demo.py        # Demo herramientas descubrimiento
├── testing/                  # Testing técnico
│   ├── performance_test.py      # Análisis de rendimiento
│   ├── protocol_comparison.py   # Comparación de protocolos
│   └── ux_testing.py           # Testing de experiencia de usuario
└── diagnostics/              # Herramientas de diagnóstico
    ├── camera_detector.py       # Detector de cámaras
    ├── network_analyzer.py      # Análisis de red
    └── port_scanner.py          # Scanner de puertos avanzado
```

### **Ejecutar Pruebas**

```bash
# Prueba de conectividad multi-marca
python examples/protocols/onvif_example.py

# Visor completo con todas las características
python examples/gui/viewer_example.py

# Demo de herramientas de descubrimiento
python examples/gui/discovery_demo.py

# Análisis de rendimiento
python examples/testing/performance_test.py

# Testing de UX y usabilidad
python examples/testing/ux_testing.py

# Detector automático de cámaras
python examples/diagnostics/camera_detector.py
```

---

## 🚨 **Solución de Problemas**

### **Problemas Comunes**

| Problema | Solución |
|----------|----------|
| **No conecta ONVIF** | Verificar puerto específico por marca |
| **RTSP timeout** | Para Dahua: ejecutar workflow DMSS previo |
| **Credenciales incorrectas** | Verificar caracteres especiales en .env |
| **Layout no se actualiza** | Usar layouts predefinidos en lugar de custom |
| **Port Discovery lento** | Ajustar timeout y usar modo "basic" para escaneos rápidos |
| **Scroll duplicado** | Problema resuelto en v0.2.0 - actualizar a última versión |

### **Logs y Debugging**

```bash
# Logs detallados disponibles en:
examples/logs/
├── viewer_example.log        # Log del visor principal
├── discovery_demo.log        # Log de herramientas descubrimiento
├── performance_test.log      # Log de rendimiento
├── protocol_comparison.log   # Log de comparación
└── ux_testing.log           # Log de testing UX

# Habilitar debug en código:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Verificación de Hardware**

```bash
# Verificar conectividad básica
ping 192.168.1.172

# Usar Port Discovery integrado para análisis completo
python examples/gui/discovery_demo.py

# Probar con VLC (URLs de referencia):
# Dahua ONVIF: Auto-detectado puerto 80
# TP-Link RTSP: rtsp://admin:pass@192.168.1.77:554/stream1
# Steren RTSP: rtsp://admin:pass@192.168.1.178:5543/live/channel0
```

---

## 📈 **Roadmap y Futuro**

### **Completado (100%)**

- ✅ Arquitectura modular SOLID
- ✅ Soporte 4 marcas principales
- ✅ Protocolos ONVIF, RTSP, HTTP/CGI
- ✅ Interfaz gráfica moderna
- ✅ Sistema de layouts inteligente
- ✅ Configuración persistente
- ✅ **Herramientas de descubrimiento avanzadas con UX optimizada**
- ✅ **Port Discovery con validación en tiempo real**
- ✅ **Exportación múltiple y reportes HTML**
- ✅ **Shortcuts de teclado y tooltips informativos**

### **Extensiones Futuras (Opcionales)**

- 📋 SDK oficial Dahua para características nativas
- 📋 Grabación de video integrada
- 📋 Detección de movimiento
- 📋 Interfaz web complementaria
- 📋 Soporte para más marcas
- 📋 **Perfiles de escaneo personalizables**
- 📋 **Historial de escaneos con comparación**
- 📋 **Descubrimiento automático de red**

---

## 🤝 **Contribuir**

### **Cómo Contribuir**

1. **Fork** del repositorio
2. **Crear rama**: `git checkout -b feature/nueva-funcionalidad`
3. **Seguir estándares**: SOLID, Clean Code, comentarios en español
4. **Testing**: Probar con hardware real cuando sea posible
5. **UX Testing**: Verificar usabilidad y experiencia de usuario
6. **Pull Request** con descripción detallada

### **Estándares de Desarrollo**

- **Código**: Inglés (nombres de variables, funciones, clases)
- **Comentarios**: Español (documentación y explicaciones)
- **Principios**: SOLID, DRY, KISS
- **UX**: Validación en tiempo real, tooltips, shortcuts de teclado
- **Testing**: Cobertura >90% para nuevas funcionalidades

---

## 📄 **Licencia y Soporte**

**Licencia**: MIT - Ver archivo `LICENSE` para detalles completos.

**Repositorio**: [https://github.com/JorgeTato99/universal-camera-viewer](https://github.com/JorgeTato99/universal-camera-viewer)

**Soporte**:

- 📖 Documentación técnica: `CURRENT_STATUS.md`
- 🐛 Issues: [GitHub Issues](https://github.com/JorgeTato99/universal-camera-viewer/issues)
- 💬 Discusiones: [GitHub Discussions](https://github.com/JorgeTato99/universal-camera-viewer/discussions)
- 🎯 UX Feedback: Reportar problemas de usabilidad

**Autor**: [JorgeTato99](https://github.com/JorgeTato99) - Desarrollado con principios de ingeniería de software moderna, arquitectura SOLID y enfoque en experiencia de usuario.

**Fecha de Creación**: Junio 2025

---

> **¿Listo para comenzar?** Ejecuta `python examples/gui/viewer_example.py` y conecta tu primera cámara en menos de 5 minutos. O prueba las herramientas de descubrimiento con `python examples/gui/discovery_demo.py`.
