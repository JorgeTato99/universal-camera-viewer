# 📦 Instalación y Setup

## ⚡ Quick Start

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd universal-camera-viewer

# 2. Instalar dependencias
make install

# 3. Ejecutar aplicación
make run
```

## 🔧 Requisitos del Sistema

### Mínimos

- **Python:** 3.9+
- **RAM:** 4GB
- **Espacio:** 500MB
- **OS:** Windows 10+, Linux, macOS

### Recomendados

- **Python:** 3.11+
- **RAM:** 8GB
- **Procesador:** CPU multi-core para múltiples streams
- **Red:** Conexión estable 100Mbps+

## 📥 Instalación Detallada

### 1. **Preparar Entorno Python**

```bash
# Verificar Python
python --version  # >= 3.9

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. **Instalar Dependencias**

```bash
# Producción
pip install -r requirements.txt

# Desarrollo completo
pip install -r requirements-dev.txt

# Con make (recomendado)
make install-dev
```

### 3. **Configuración Inicial**

```bash
# Copiar configuración de ejemplo
cp .env.example .env

# Editar configuración (opcional)
# Configurar IPs, credenciales, etc.
```

### 4. **Verificar Instalación**

```bash
# Verificar estado
make status

# Ejecutar tests básicos
make test

# Ejecutar aplicación
make run
```

## 🐧 Instalación Linux/Ubuntu

```bash
# Dependencias del sistema
sudo apt update
sudo apt install python3-pip python3-venv python3-dev

# OpenCV dependencies
sudo apt install libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx

# Continuar con instalación normal
```

## 🍎 Instalación macOS

```bash
# Con Homebrew
brew install python@3.11
brew install make

# Continuar con instalación normal
```

## 🚨 Troubleshooting

### Error: `No module named 'cv2'`

```bash
pip uninstall opencv-python
pip install opencv-python-headless>=4.8.0
```

### Error: ONVIF connection failed

```bash
# Verificar conectividad de red
ping <camera-ip>

# Verificar puertos
telnet <camera-ip> 80
```

### Error: Permission denied (Linux)

```bash
# Agregar usuario a grupo video
sudo usermod -a -G video $USER
# Reiniciar sesión
```

### Error: Dependencies conflict

```bash
# Limpiar e instalar de nuevo
make clean
pip cache purge
make install
```

## 🔐 Configuración de Seguridad

### Variables de Entorno

```bash
# .env file
CAMERA_DEFAULT_USERNAME=admin
CAMERA_DEFAULT_PASSWORD=your_secure_password
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### Credenciales por Marca

```bash
# Dahua
DAHUA_USERNAME=admin
DAHUA_PASSWORD=password

# TP-Link
TPLINK_USERNAME=admin
TPLINK_PASSWORD=password

# Steren
STEREN_USERNAME=admin
STEREN_PASSWORD=password
```

## 📊 Verificación del Setup

```bash
# Estado completo
make status

# Test de conexión de cámaras
make network-test

# Análisis de rendimiento
make performance

# Verificar calidad de código
make check-all
```

## 🎯 Próximos Pasos

1. **[💻 Configurar Desarrollo](development.md)** - Setup para contribuir
2. **[🏛️ Entender Arquitectura](architecture.md)** - Conocer el diseño
3. **[🌐 Configurar Cámaras](camera-protocols.md)** - Conectar dispositivos

---

**💡 Tip:** Usa `make help` para ver todos los comandos disponibles
