# 📦 Instalación y Setup

## ⚡ Quick Start

```bash
# 1. Clonar repositorio
git clone https://github.com/JorgeTato99/universal-camera-viewer.git
cd universal-camera-viewer

# 2. Instalar Frontend (USAR YARN)
yarn install       # ⚠️ NO usar npm install

# 3. Instalar Backend Python
pip install -r requirements.txt

# 4. Ejecutar aplicación
yarn tauri-dev     # Aplicación completa
```

## 🔧 Requisitos del Sistema

### Mínimos

- **Node.js:** 18+
- **Python:** 3.8+
- **RAM:** 4GB
- **Espacio:** 1GB
- **OS:** Windows 10+, Linux, macOS

### Recomendados

- **Node.js:** 20+
- **Python:** 3.11+
- **RAM:** 8GB
- **Procesador:** CPU multi-core para múltiples streams
- **Red:** Conexión estable 100Mbps+

### Requisitos Adicionales (Windows)

- **Rust:** Con toolchain MSVC (NO GNU)
- **Visual Studio Build Tools:** Para compilar Tauri
- **Yarn:** Gestor de paquetes (obligatorio)

## 📥 Instalación Detallada

### 1. **Preparar Herramientas Base**

#### Windows

```bash
# 1. Instalar Rust (IMPORTANTE: Seleccionar MSVC)
# Descargar desde: https://www.rust-lang.org/tools/install
# Durante instalación elegir: stable-x86_64-pc-windows-msvc

# 2. Instalar Node.js
# Descargar desde: https://nodejs.org/

# 3. Instalar Yarn (OBLIGATORIO en Windows)
npm install -g yarn

# 4. Verificar instalaciones
rustc --version
node --version
yarn --version
python --version
```

#### Linux/macOS

```bash
# Node.js con nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# Yarn
npm install -g yarn

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. **Instalar Dependencias del Proyecto**

```bash
# Frontend - IMPORTANTE: Usar Yarn
yarn install       # ✅ Correcto
# npm install     # ❌ NO USAR - Bug con dependencias nativas

# Backend Python
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt

# Para desarrollo
pip install -r requirements-dev.txt
```

### 3. **Configuración Inicial**

```bash
# Copiar configuración de ejemplo
cp .env.example .env

# Editar .env con credenciales de cámaras
# DAHUA_IP=192.168.1.172
# DAHUA_USER=admin
# DAHUA_PASSWORD=tu_password
```

### 4. **Verificar Instalación**

```bash
# Verificar herramientas
make rust-check    # Verifica Rust y dependencias nativas
make status        # Estado general del proyecto

# Verificar que las dependencias nativas estén instaladas
dir node_modules\@tauri-apps\cli-win32-x64-msvc    # Windows
ls node_modules/@tauri-apps/cli-*                  # Linux/Mac
```

## 🐧 Instalación Linux/Ubuntu

```bash
# Dependencias del sistema
sudo apt update
sudo apt install build-essential curl wget
sudo apt install python3-pip python3-venv python3-dev

# Dependencias para Tauri
sudo apt install libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev

# OpenCV dependencies
sudo apt install libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx

# Continuar con instalación normal
```

## 🍎 Instalación macOS

```bash
# Con Homebrew
brew install python@3.11
brew install node
brew install yarn

# Xcode Command Line Tools (para Rust)
xcode-select --install

# Continuar con instalación normal
```

## 🚨 Troubleshooting

### Error: `Cannot find module '@tauri-apps/cli-win32-x64-msvc'`

**Causa:** Usaste npm install en lugar de yarn

```bash
# Solución
rm -rf node_modules
yarn install       # Usar Yarn, no npm
```

### Error: `Microsoft Visual C++ 14.0 or greater is required`

**Causa:** Falta MSVC toolchain

```bash
# Instalar Visual Studio Build Tools
# Descargar desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Instalar "Desktop development with C++"
```

### Error: `No module named 'cv2'`

```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python-headless>=4.8.0
```

### Error: Puerto 5173 ocupado

```bash
# Verificar qué usa el puerto
netstat -ano | findstr :5173    # Windows
lsof -i :5173                    # Linux/Mac

# Matar proceso o cambiar puerto en vite.config.ts
```

### Error: ONVIF connection failed

```bash
# Verificar conectividad
ping <camera-ip>

# Verificar puertos según marca
# Dahua: 80, TP-Link: 2020, Steren: 8000
telnet <camera-ip> <puerto>
```

## 🔐 Configuración de Seguridad

### Variables de Entorno (.env)

```bash
# Configuración general
DEBUG_MODE=false
LOG_LEVEL=INFO

# Credenciales por marca
DAHUA_IP=192.168.1.172
DAHUA_USER=admin
DAHUA_PASSWORD=secure_password

TPLINK_IP=192.168.1.77
TPLINK_USER=admin
TPLINK_PASSWORD=secure_password

STEREN_IP=192.168.1.178
STEREN_USER=admin
STEREN_PASSWORD=secure_password
```

## 📊 Verificación del Setup

```bash
# Frontend
yarn dev           # Debe abrir http://localhost:5173

# Backend Python
python run_python.py    # Ejecuta backend legacy Flet

# Aplicación completa
yarn tauri-dev     # Frontend + Backend integrados

# Tests
make test          # Tests Python
yarn test          # Tests React (si están configurados)
```

## 🎯 Próximos Pasos

1. **[🪟 Configuración Windows](WINDOWS_SETUP.md)** - Detalles específicos Windows
2. **[💻 Guía de Desarrollo](development.md)** - Workflow y comandos
3. **[🏛️ Arquitectura](ARCHITECTURE.md)** - Entender el diseño

---

**💡 Tip:** Si tienes problemas con npm, recuerda siempre usar `yarn` en este proyecto

---

### 📚 Navegación

[📑 Índice](README.md) | [Siguiente: Configuración Windows →](WINDOWS_SETUP.md)
