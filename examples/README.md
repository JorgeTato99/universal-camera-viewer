# Examples - Visor Universal de Cámaras Dahua

Esta carpeta contiene ejemplos organizados y consolidados para el **Visor Universal de Cámaras - Módulo Dahua**. Toda la funcionalidad previamente dispersa ha sido reorganizada en una estructura lógica y fácil de navegar.

## 📁 Estructura Reorganizada

```bash
examples/
├── protocols/              # Ejemplos de protocolos de conexión
│   ├── onvif_example.py    # ONVIF completo (principal)
│   ├── rtsp_example.py     # RTSP con workflow DMSS
│   ├── amcrest_example.py  # HTTP/Amcrest (compatibilidad)
│   └── sdk_example.py      # SDK Dahua (placeholder)
│
├── gui/                    # Ejemplos de interfaz gráfica
│   ├── viewer_example.py   # Visor completo con GUI
│   └── components_demo.py  # Demo de componentes individuales
│
├── testing/                # Scripts de testing técnico
│   ├── onvif_integration_test.py  # Test integración ONVIF
│   ├── performance_test.py        # Benchmarking completo
│   └── protocol_comparison.py     # Comparación técnica
│
├── diagnostics/            # Herramientas de diagnóstico
│   ├── camera_detector.py  # Detector de cámaras en red
│   └── network_analyzer.py # Análisis de conectividad
│
└── logs/                   # Directorio de logs
    └── .gitkeep
```

## 🚀 Empezar Rápido

### Para Usuarios Finales

```bash
# Ejecutar el visor completo
python examples/gui/viewer_example.py
```

### Para Desarrolladores

```bash
# Probar protocolo ONVIF (recomendado)
python examples/protocols/onvif_example.py

# Analizar performance
python examples/testing/performance_test.py

# Diagnosticar conectividad
python examples/diagnostics/network_analyzer.py
```

## 📋 Guía de Ejemplos

### 🔌 Protocolos (`protocols/`)

#### **onvif_example.py** - PROTOCOLO PRINCIPAL ⭐

- **Uso**: Ejemplo completo de ONVIF para Hero-K51H
- **Funciones**: Conexión, servicios, snapshots, streaming
- **Recomendado**: ✅ Protocolo principal
- **Ejecutar**: `python examples/protocols/onvif_example.py`

#### **rtsp_example.py** - PROTOCOLO BACKUP

- **Uso**: RTSP con workflow DMSS para Hero-K51H
- **Funciones**: Sleep/wake, streaming, snapshots
- **Recomendado**: ⚠️ Requiere workflow DMSS previo
- **Ejecutar**: `python examples/protocols/rtsp_example.py`

#### **amcrest_example.py** - COMPATIBILIDAD

- **Uso**: HTTP/CGI para cámaras compatibles
- **Funciones**: Snapshots, streaming, PTZ
- **Recomendado**: ❌ Hero-K51H no compatible
- **Ejecutar**: `python examples/protocols/amcrest_example.py`

#### **sdk_example.py** - FUTURO

- **Uso**: Placeholder para SDK nativo Dahua
- **Estado**: 🚧 En desarrollo
- **Funciones**: Login seguro, streaming nativo

### 🖥️ GUI (`gui/`)

#### **viewer_example.py** - APLICACIÓN COMPLETA

- **Uso**: Visor universal con interfaz gráfica
- **Funciones**: Multi-cámara, layouts, panel control
- **Target**: Usuarios finales
- **Ejecutar**: `python examples/gui/viewer_example.py`

#### **components_demo.py** - DEMO TÉCNICO

- **Uso**: Verificación de componentes del sistema
- **Funciones**: Test imports, dependencias, GUI
- **Target**: Desarrolladores
- **Ejecutar**: `python examples/gui/components_demo.py`

### 🧪 Testing (`testing/`)

#### **onvif_integration_test.py** - TEST AVANZADO

- **Uso**: Testing técnico completo de ONVIF
- **Funciones**: Factory pattern, context manager, performance
- **Target**: QA y desarrolladores
- **Ejecutar**: `python examples/testing/onvif_integration_test.py`

#### **performance_test.py** - BENCHMARKING

- **Uso**: Comparación de performance entre protocolos
- **Funciones**: FPS, latencia, análisis de estabilidad
- **Target**: Optimización
- **Ejecutar**: `python examples/testing/performance_test.py`

#### **protocol_comparison.py** - ANÁLISIS TÉCNICO

- **Uso**: Comparación técnica de protocolos
- **Funciones**: Compatibilidad, características, recomendaciones
- **Target**: Arquitectura
- **Ejecutar**: `python examples/testing/protocol_comparison.py`

### 🔧 Diagnostics (`diagnostics/`)

#### **camera_detector.py** - DETECTOR DE RED

- **Uso**: Escaneo y detección de cámaras en red
- **Funciones**: Port scanning, protocol detection
- **Target**: Setup y troubleshooting
- **Ejecutar**: `python examples/diagnostics/camera_detector.py`

#### **network_analyzer.py** - ANÁLISIS DE RED

- **Uso**: Diagnóstico de conectividad y performance
- **Funciones**: Ping, latencia, bandwidth, routing
- **Target**: Troubleshooting de red
- **Ejecutar**: `python examples/diagnostics/network_analyzer.py`

## 🎯 Casos de Uso Comunes

### Setup Inicial

1. **Detectar cámara**: `python examples/diagnostics/camera_detector.py`
2. **Analizar red**: `python examples/diagnostics/network_analyzer.py`
3. **Probar ONVIF**: `python examples/protocols/onvif_example.py`
4. **Ejecutar visor**: `python examples/gui/viewer_example.py`

### Desarrollo

1. **Verificar sistema**: `python examples/gui/components_demo.py`
2. **Test integración**: `python examples/testing/onvif_integration_test.py`
3. **Benchmark**: `python examples/testing/performance_test.py`

### Troubleshooting

1. **Problemas de red**: `python examples/diagnostics/network_analyzer.py`
2. **Comparar protocolos**: `python examples/testing/protocol_comparison.py`
3. **Detectar dispositivos**: `python examples/diagnostics/camera_detector.py`

## 📝 Configuración

Todos los ejemplos utilizan la configuración del archivo `.env` en la raíz del proyecto:

```env
CAMERA_IP=192.168.1.172
CAMERA_USER=admin
CAMERA_PASSWORD=tu_password
ONVIF_PORT=80
RTSP_PORT=554
HTTP_PORT=80
```

## 🗂️ Logs

Todos los ejemplos generan logs en `examples/logs/`:

- `onvif_example.log` - Logs del protocolo ONVIF
- `rtsp_example.log` - Logs del protocolo RTSP  
- `performance_test.log` - Logs de performance
- `camera_detector.log` - Logs de detección
- `network_analyzer.log` - Logs de análisis de red
- Y más...

## 🔄 Migración desde Estructura Anterior

### Archivos Consolidados

Los siguientes archivos fueron **consolidados** en la nueva estructura:

| Archivo Original | Nuevo Ubicación | Funcionalidad |
|-----------------|----------------|---------------|
| `test_onvif_simple.py` | `protocols/onvif_example.py` | Ejemplo básico ONVIF |
| `test_onvif_discovery.py` | `protocols/onvif_example.py` | Discovery de servicios |
| `test_onvif_integration.py` | `testing/onvif_integration_test.py` | Testing avanzado |
| `test_gui_onvif.py` | `testing/onvif_integration_test.py` | GUI integration |
| `test_performance_comparison.py` | `testing/performance_test.py` | Benchmarking |
| `test_viewer_components.py` | `gui/components_demo.py` | Demo componentes |
| `viewer_example.py` | `gui/viewer_example.py` | Visor principal |

### Beneficios de la Reorganización

- ✅ **60% menos archivos**: De 16+ archivos a 9 archivos organizados
- ✅ **Eliminación de redundancia**: Sin duplicación de funcionalidades
- ✅ **Estructura lógica**: Separación clara por propósito
- ✅ **Mejor mantenimiento**: Código consolidado y organizado
- ✅ **Documentación clara**: Cada archivo con propósito específico

## 🎉 Recomendaciones

### Para Hero-K51H

1. **Protocolo Principal**: ONVIF (`protocols/onvif_example.py`)
2. **Protocolo Backup**: RTSP (`protocols/rtsp_example.py`)
3. **Aplicación**: GUI Viewer (`gui/viewer_example.py`)

### Para Desarrollo

1. **Testing**: Usar `testing/` para validación
2. **Diagnóstico**: Usar `diagnostics/` para troubleshooting
3. **Protocolos**: Extender `protocols/` para nuevos protocolos

---

**📚 Documentación completa**: Ver `README.md` principal del proyecto  
**🐛 Issues**: Reportar en el repositorio principal  
**🤝 Contribuciones**: Ver guías de contribución del proyecto
