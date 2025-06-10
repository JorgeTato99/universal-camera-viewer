# Visor Universal de Cámaras - Módulo Dahua

Este módulo forma parte del proyecto *Visor Universal de Cámaras* y proporciona la lógica necesaria para conectar y consumir flujos de video de cámaras Dahua (por ejemplo, la Dahua Hero-K51H) desde aplicaciones Python.

**Estado del Proyecto**: 52% Completado - RTSP implementado y probado, arquitectura base completa, visor en tiempo real en desarrollo.

## Métodos de Conexión Implementados

### ✅ RTSP con OpenCV (100% Funcional)

- **Estado**: Completamente implementado y probado con Hero-K51H
- **Funcionalidades**: Stream en tiempo real, snapshots, información de stream, manejo de errores
- **Rendimiento**: 4K @ 15 FPS verificado en hardware real

### ✅ HTTP/CGI Endpoints (100% Implementado - Incompatible con Hero-K51H)

- **Estado**: Implementación completa con requests directo
- **Limitación**: Hero-K51H no soporta endpoints HTTP CGI (verificado mediante herramientas de diagnóstico)
- **Funcionalidades**: Snapshots, información de dispositivo, controles PTZ, presets
- **Nota**: Listo para modelos Dahua compatibles con HTTP CGI

### 🔄 ONVIF (Próxima Prioridad)

- **Estado**: Por implementar
- **Objetivo**: Protocolo universal para máxima compatibilidad

### 📋 SDK Oficial Dahua (Pendiente)

- **Estado**: Planificado para fase avanzada
- **Requisito**: Descarga desde portal Dahua Partner

---

## Guía de Inicio Rápido

### Pre-Requisitos

- Python 3.8+ (probado con Python 3.13.1)
- Git
- Cámara Dahua Hero-K51H o compatible

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

# Editar .env con los datos de tu cámara
# CAMERA_IP=192.168.1.172
# CAMERA_USER=admin
# CAMERA_PASSWORD=tu_password_aquí
```

**⚠️ Importante**: Si tu contraseña tiene caracteres especiales (%, &, etc.), déjalos tal como están. El sistema maneja automáticamente la codificación URL.

### 3. Prueba Rápida - Conexión RTSP

```bash
# Ejecutar ejemplo RTSP básico
cd examples/protocols
python rtsp_example.py
```

### 4. Visor en Tiempo Real (Beta)

```bash
# Ejecutar visor con interfaz gráfica
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
│   │   ├── base.py         # Clase base abstracta
│   │   ├── rtsp.py         # Conexión RTSP (100% funcional)
│   │   └── amcrest.py      # Conexión HTTP/CGI (incompatible con Hero-K51H)
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

- ✅ **RTSP**: Excelente (4K @ 15 FPS, stream estable)
- ❌ **HTTP CGI**: No compatible (puertos abiertos pero sin respuesta HTTP)
- 🔄 **ONVIF**: Por verificar
- 📋 **SDK**: Por probar

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

### Conexión RTSP Básica

```python
from src.connections.rtsp import RTSPConnection
from src.utils.config import ConfigurationManager

# Cargar configuración
config = ConfigurationManager()

# Crear conexión RTSP
with RTSPConnection(config) as rtsp:
    # Obtener información del stream
    info = rtsp.get_stream_info()
    print(f"Resolución: {info['width']}x{info['height']}")
    print(f"FPS: {info['fps']}")
    
    # Capturar frames en tiempo real
    for i in range(10):
        frame = rtsp.get_frame()
        if frame is not None:
            print(f"Frame {i+1} capturado exitosamente")
    
    # Tomar snapshot
    rtsp.capture_snapshot("mi_snapshot.jpg")
```

### Usar el Factory Pattern

```python
from src.connections.factory import ConnectionFactory

# Crear conexión usando factory
connection = ConnectionFactory.create_connection('rtsp', config)
with connection:
    frame = connection.get_frame()
    # ... tu código aquí
```

---

## Desarrollo y Testing

### Ejecutar Pruebas

```bash
# Activar entorno virtual
.\.venv\\Scripts\\activate  # Windows
source .venv/bin/activate   # Linux/MacOS

# Probar conexión RTSP
python examples/protocols/rtsp_example.py

# Probar visor con interfaz gráfica
python examples/gui/viewer_example.py
```

### Características Técnicas

- **Arquitectura**: Modular siguiendo principios SOLID
- **Patrones**: Factory, Template Method, Context Manager
- **Logging**: Sistema estructurado para debugging
- **Manejo de Errores**: Excepciones específicas por tipo de conexión
- **Threading**: Soporte para operaciones asíncronas en el visor

---

## Roadmap

### Fase Actual (52% Completado)

- [x] Arquitectura base con principios SOLID
- [x] Conexión RTSP completamente funcional
- [x] Implementación HTTP/CGI (para modelos compatibles)
- [x] Herramientas de diagnóstico
- [x] Sistema de configuración
- [x] Inicio del visor en tiempo real

### Próximas Fases

- [ ] Implementación ONVIF (universal)
- [ ] Completar visor en tiempo real
- [ ] Grabación de video
- [ ] Detección de movimiento
- [ ] Interfaz web opcional
- [ ] SDK oficial Dahua

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

**Error de conexión RTSP:**

```bash
# Verificar conectividad
ping 192.168.1.172
# Probar con VLC primero:
# rtsp://admin:password@192.168.1.172:554/cam/realmonitor?channel=1&subtype=0
```

**Problemas con Python 3.13.1:**

- Todas las dependencias son compatibles
- Si encuentras problemas, reporta el issue específico

**Cámara no responde a HTTP:**

- Normal para Hero-K51H, usar RTSP
- Usar herramientas de diagnóstico para verificar

---

## Licencia

MIT License - Ver archivo LICENSE para detalles.
