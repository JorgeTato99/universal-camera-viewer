# Visor Universal de Cámaras Multi-Marca

> **Sistema de videovigilancia profesional** con soporte nativo para múltiples marcas de cámaras IP: Dahua, TP-Link, Steren y cámaras genéricas chinas. Arquitectura modular SOLID con interfaz moderna y protocolos optimizados.

![Estado del Proyecto](https://img.shields.io/badge/Estado-100%25%20Completado-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B%20(Probado%203.13.1)-blue)
![Licencia](https://img.shields.io/badge/Licencia-MIT-green)

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

---

## 🚀 **Inicio Rápido (5 minutos)**

### **1. Instalación**

```bash
# Clonar y configurar
git clone https://github.com/tu-org/universal-visor.git
cd universal-visor

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

### **Panel de Control Avanzado**

- **Pestaña Configuración**: Protocolos, credenciales, puertos
- **Pestaña Cámaras**: Gestión individual, snapshots, reconexión
- **Pestaña Layouts**: Cambio dinámico, configuraciones predefinidas

---

## 🔧 **Arquitectura Técnica**

### **Patrones de Diseño Implementados**

- **Factory Pattern**: `ConnectionFactory` para crear conexiones
- **Template Method**: `BaseConnection` como clase abstracta
- **Singleton**: `ConfigurationManager` para configuración global
- **Observer**: Sistema de eventos para UI

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
│   └── discovery/            # Herramientas de descubrimiento
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
│   └── components_demo.py       # Demo de componentes
├── testing/                  # Testing técnico
│   ├── performance_test.py      # Análisis de rendimiento
│   └── protocol_comparison.py   # Comparación de protocolos
└── diagnostics/              # Herramientas de diagnóstico
    ├── camera_detector.py       # Detector de cámaras
    └── network_analyzer.py      # Análisis de red
```

### **Ejecutar Pruebas**

```bash
# Prueba de conectividad multi-marca
python examples/protocols/onvif_example.py

# Visor completo con todas las características
python examples/gui/viewer_example.py

# Análisis de rendimiento
python examples/testing/performance_test.py

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

### **Logs y Debugging**

```bash
# Logs detallados disponibles en:
examples/logs/
├── viewer_example.log        # Log del visor principal
├── performance_test.log      # Log de rendimiento
└── protocol_comparison.log   # Log de comparación

# Habilitar debug en código:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Verificación de Hardware**

```bash
# Verificar conectividad básica
ping 192.168.1.172

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

### **Extensiones Futuras (Opcionales)**

- 📋 SDK oficial Dahua para características nativas
- 📋 Grabación de video integrada
- 📋 Detección de movimiento
- 📋 Interfaz web complementaria
- 📋 Soporte para más marcas

---

## 🤝 **Contribuir**

### **Cómo Contribuir**

1. **Fork** del repositorio
2. **Crear rama**: `git checkout -b feature/nueva-funcionalidad`
3. **Seguir estándares**: SOLID, Clean Code, comentarios en español
4. **Testing**: Probar con hardware real cuando sea posible
5. **Pull Request** con descripción detallada

### **Estándares de Desarrollo**

- **Código**: Inglés (nombres de variables, funciones, clases)
- **Comentarios**: Español (documentación y explicaciones)
- **Principios**: SOLID, DRY, KISS
- **Testing**: Cobertura >90% para nuevas funcionalidades

---

## 📄 **Licencia y Soporte**

**Licencia**: MIT - Ver archivo `LICENSE` para detalles completos.

**Soporte**:

- 📖 Documentación técnica: `CURRENT_STATUS.md`
- 🐛 Issues: GitHub Issues
- 💬 Discusiones: GitHub Discussions

**Autor**: Desarrollado con principios de ingeniería de software moderna y arquitectura SOLID.

---

> **¿Listo para comenzar?** Ejecuta `python examples/gui/viewer_example.py` y conecta tu primera cámara en menos de 5 minutos.
