# Visor Universal de Cámaras Multi-Marca

**Visor Universal de Cámaras** con soporte completo para múltiples marcas: **Dahua Hero-K51H**, **TP-Link Tapo**, **Steren CCTV-235** y compatibles. Proporciona conexión y consumo de flujos de video desde aplicaciones Python con interfaz gráfica moderna.

**Estado del Proyecto**: 100% Completado - Visor funcional con 3 marcas, ONVIF optimizado como protocolo principal, RTSP como respaldo.

## Marcas y Protocolos Soportados

### ✅ **ONVIF (Protocolo Principal - 100% Funcional)**

- **Estado**: Implementado y optimizado para 3 marcas
- **Marcas soportadas**: Dahua Hero-K51H, TP-Link Tapo C520WS, Steren CCTV-235
- **Funcionalidades**: Descubrimiento automático, stream en tiempo real, snapshots HTTP
- **Rendimiento**: 13-20+ FPS según marca, conexión inmediata

### ✅ **RTSP con OpenCV (100% Funcional)**

- **Estado**: Implementación completa multi-marca
- **Marcas soportadas**: Todas (Dahua, TP-Link, Steren)
- **Funcionalidades**: Stream directo, snapshots, información de stream
- **Rendimiento**: 15-20+ FPS según marca y configuración

### ✅ **Conexiones Especializadas por Marca**

- **TPLinkConnection**: Implementación específica para Tapo (RTSP optimizado)
- **SterenConnection**: Implementación híbrida ONVIF+RTSP para CCTV-235
- **AmcrestConnection**: HTTP/CGI para modelos compatibles (no Hero-K51H)

### 📋 **SDK Oficial Dahua (Opcional)**

- **Estado**: Pendiente para funcionalidades avanzadas
- **Beneficio**: Acceso a características nativas exclusivas

---

## Guía de Inicio Rápido

### Pre-Requisitos

- Python 3.8+ (probado con Python 3.13.1)
- Git
- Cámara compatible: Dahua Hero-K51H, TP-Link Tapo C520WS, Steren CCTV-235 o similares

### 1. Configuración del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/tu-org/dahua-visor.git
cd dahua-visor

# Crear entorno virtual con Python 3.13.1 (o tu versión disponible)
python -m venv .venv

# Activar entorno virtual
# Windows:
.\.venv\\Scripts\\activate
# Linux/MacOS:
source .venv/bin/activate

# Verificar versión de Python
python --version
# Debe mostrar: Python 3.13.1 (o tu versión)

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración de la Cámara

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar .env con los datos de tu(s) cámara(s)
# Dahua Hero-K51H:
# DAHUA_IP=192.168.1.172
# DAHUA_USER=admin
# DAHUA_PASSWORD=tu_password_aquí

# TP-Link Tapo C520WS:
# TPLINK_IP=192.168.1.77
# TPLINK_USER=admin
# TPLINK_PASSWORD=tu_password_aquí

# Steren CCTV-235:
# STEREN_IP=192.168.1.178
# STEREN_USER=admin
# STEREN_PASSWORD=tu_password_aquí
```

**⚠️ Importante**: Si tu contraseña tiene caracteres especiales (%, &, etc.), déjalos tal como están. El sistema maneja automáticamente la codificación URL.

### 3. Prueba Rápida - Conexión ONVIF

```bash
# Ejecutar ejemplo ONVIF multi-marca
cd examples/protocols
python onvif_example.py
```

### 4. Visor en Tiempo Real Completo

```bash
# Ejecutar visor con interfaz gráfica multi-marca
cd examples/gui
python viewer_example.py
```

---

## Estructura del Proyecto

```bash
dahua-visor/
├── .cursor/rules/           # Estándares de desarrollo
├── src/
│   ├── connections/         # Módulos de conexión
│   │   ├── base_connection.py         # Clase base abstracta + Factory
│   │   ├── onvif_connection.py        # Conexión ONVIF multi-marca
│   │   ├── rtsp_connection.py         # Conexión RTSP genérica
│   │   ├── tplink_connection.py       # Conexión TP-Link especializada
│   │   ├── steren_connection.py       # Conexión Steren CCTV-235
│   │   └── amcrest_connection.py      # Conexión HTTP/CGI
│   ├── utils/              # Utilidades
│   │   └── config.py       # Gestión de configuración
│   └── viewer/             # Componentes del visor
│       ├── camera_widget.py
│       ├── control_panel.py
│       └── real_time_viewer.py
├── examples/               # Ejemplos y herramientas
│   ├── protocols/          # Ejemplos de conexión
│   │   ├── rtsp_example.py
│   │   ├── amcrest_example.py
│   │   └── onvif_example.py
│   ├── gui/                # Ejemplos de interfaz
│   │   └── viewer_example.py
│   └── diagnostics/        # Herramientas de diagnóstico
├── requirements.txt
├── .env.example
├── .env                    # Tu configuración (no versionado)
├── CURRENT_STATUS.md       # Estado detallado del proyecto
└── README.md
```

---

## Compatibilidad Verificada

### Dahua Hero-K51H (192.168.1.172)

- ✅ **ONVIF**: Excelente (13.86 FPS, 4K, puerto 80, sin workflow DMSS)
- ✅ **RTSP**: Excelente (15.32 FPS, 4K, requiere workflow DMSS previo)
- ❌ **HTTP CGI**: No compatible (modelo específico)

### TP-Link Tapo C520WS (192.168.1.77)

- ✅ **ONVIF**: Excelente (puerto 2020, detección automática)
- ✅ **RTSP**: Funcional (streams directos `/stream1`, `/stream2`)

### Steren CCTV-235 (192.168.1.178)

- ✅ **ONVIF**: Excelente (puerto 8000, dual-stream 4MP+360p)
- ✅ **RTSP**: Excelente (puerto 5543, 20+ FPS, `/live/channel0-1`)

### Herramientas de Diagnóstico

```bash
# Verificar diagnósticos disponibles
cd examples/diagnostics
ls -la

# Herramientas específicas según disponibilidad
python test_camera_connectivity.py  # (según lo que esté disponible)
```

---

## Ejemplos de Uso

### Conexión ONVIF Universal

```python
from src.connections import ConnectionFactory
from src.utils.config import ConfigurationManager

# Cargar configuración
config = ConfigurationManager()

# Crear conexión ONVIF (recomendado)
connection = ConnectionFactory.create_connection(
    connection_type='onvif', 
    config_manager=config,
    camera_brand='dahua'  # o 'tplink', 'steren'
)

with connection:
    # Obtener información del stream
    info = connection.get_stream_info()
    print(f"Marca: {info['brand']}")
    print(f"Resolución: {info['width']}x{info['height']}")
    print(f"FPS: {info['fps']}")
    
    # Capturar frames en tiempo real
    for i in range(10):
        frame = connection.get_frame()
        if frame is not None:
            print(f"Frame {i+1} capturado exitosamente")
    
    # Tomar snapshot de alta calidad
    connection.capture_snapshot("mi_snapshot.jpg")
```

### Conexión Multi-Marca Simplificada

```python
from src.connections import ConnectionFactory

# Steren CCTV-235 con protocolo híbrido
steren = ConnectionFactory.create_connection('steren', config, 'steren')

# TP-Link con RTSP optimizado
tplink = ConnectionFactory.create_connection('tplink', config, 'tplink')

# Dahua con ONVIF sin workflow
dahua = ConnectionFactory.create_connection('onvif', config, 'dahua')

# Usar cualquier conexión de la misma manera
with steren:
    frame = steren.get_frame()
    device_info = steren.get_device_info()
    print(f"Conectado a: {device_info['brand']} {device_info['model']}")
```

---

## Desarrollo y Testing

### Ejecutar Pruebas

```bash
# Activar entorno virtual
.\.venv\\Scripts\\activate  # Windows
source .venv/bin/activate   # Linux/MacOS

# Probar conexión ONVIF multi-marca
python examples/protocols/onvif_example.py

# Probar visor completo con interfaz gráfica
python examples/gui/viewer_example.py

# Probar conexión específica por marca
python examples/protocols/rtsp_example.py
```

### Características Técnicas

- **Arquitectura**: Modular siguiendo principios SOLID
- **Patrones**: Factory, Template Method, Context Manager
- **Logging**: Sistema estructurado para debugging
- **Manejo de Errores**: Excepciones específicas por tipo de conexión
- **Threading**: Soporte para operaciones asíncronas en el visor

---

## Roadmap

### Proyecto Completado (100%)

- [x] Arquitectura base con principios SOLID
- [x] Conexión ONVIF multi-marca (protocolo principal)
- [x] Conexión RTSP universal y especializada
- [x] Conexiones específicas por marca (TP-Link, Steren)
- [x] Implementación HTTP/CGI (para modelos compatibles)
- [x] Visor en tiempo real completo con interfaz gráfica
- [x] Panel de control con múltiples layouts
- [x] Sistema de configuración persistente
- [x] Herramientas de diagnóstico y testing

### Extensiones Opcionales

- [ ] Grabación de video desde el visor
- [ ] Detección de movimiento integrada
- [ ] Controles PTZ avanzados via ONVIF
- [ ] SDK oficial Dahua para características nativas
- [ ] Interfaz web adicional
- [ ] Soporte para más marcas de cámaras

---

## Contribuciones

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "Descripción del cambio"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Estándares de Código

- Seguir principios SOLID y Clean Code
- Comentarios en español, código en inglés
- Documentación obligatoria para todas las funciones
- Testing con hardware real cuando sea posible

---

## Soporte y Problemas

### Problemas Comunes

**Error de conexión:**

```bash
# Verificar conectividad básica
ping 192.168.1.172  # (o IP de tu cámara)

# Probar con VLC para verificar URLs:
# ONVIF Dahua: Automático via puerto 80
# RTSP Dahua: rtsp://admin:password@192.168.1.172:554/cam/realmonitor?channel=1&subtype=0
# RTSP TP-Link: rtsp://admin:password@192.168.1.77:554/stream1
# RTSP Steren: rtsp://admin:password@192.168.1.178:5543/live/channel0
```

**Problemas con Python 3.13.1:**

- Todas las dependencias son compatibles
- Si encuentras problemas, reporta el issue específico

**Protocolo recomendado por marca:**

- **Dahua Hero-K51H**: ONVIF (puerto 80) - Sin workflow DMSS requerido
- **TP-Link Tapo**: ONVIF (puerto 2020) o RTSP directo
- **Steren CCTV-235**: Implementación híbrida ONVIF+RTSP optimizada

---

## Licencia

MIT License - Ver archivo LICENSE para detalles.
