# 📦 Deployment y Distribución - v0.8.0

## 🚀 Build de Aplicación con Tauri

### **Prerrequisitos**

```bash
# Windows (IMPORTANTE: Ver docs/WINDOWS_SETUP.md)
- Rust con toolchain MSVC (NO GNU)
- Visual Studio Build Tools o Visual Studio
- Node.js 18+ y Yarn (OBLIGATORIO - npm tiene bugs)

# Verificar instalación
make rust-check
yarn --version
rustc --version
```

### **Build de Producción**

```bash
# Build completo con Yarn (RECOMENDADO)
yarn tauri-build

# O usando Make
make tauri-build

# Build específico para Windows
yarn tauri build --target x86_64-pc-windows-msvc
```

### **Resultado del Build**

```
src-tauri/target/release/
├── universal-camera-viewer.exe    # Ejecutable principal
└── bundle/
    ├── msi/
    │   └── Universal Camera Viewer_0.1.0_x64_en-US.msi
    └── nsis/
        └── Universal Camera Viewer_0.1.0_x64-setup.exe
```

## 📋 Configuración de Build

### **Configuración en tauri.conf.json**

```json
{
  "productName": "Universal Camera Viewer",
  "version": "0.8.0",
  "identifier": "com.universalcameraviewer.app",
  
  "build": {
    "frontendDist": "../dist",
    "beforeBuildCommand": "yarn build"
  },
  
  "bundle": {
    "active": true,
    "targets": ["msi", "nsis"],    // Windows installers
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/icon.ico"
    ],
    "resources": [
      "scripts/python_sidecar.py",  // Python backend
      "../.env.example"             // Configuración ejemplo
    ],
    "externalBin": [
      "scripts/dist/python_sidecar"  // Ejecutable Python empaquetado
    ]
  }
}
```

### **Optimización del Build**

```bash
# Build optimizado para tamaño
RUSTFLAGS="-C link-arg=-s" yarn tauri build

# Build con compresión UPX (opcional)
# Instalar UPX primero: https://upx.github.io/
yarn tauri build
upx --best --lzma src-tauri/target/release/*.exe

# IMPORTANTE en Windows: Usar PowerShell
$env:RUSTFLAGS="-C link-arg=-s"
yarn tauri build
```

## 🪟 Distribución Windows

### **MSI Installer**

```bash
# Genera automáticamente con yarn tauri-build
# Ubicación: src-tauri/target/release/bundle/msi/

# Características del MSI:
- Instalación silenciosa: msiexec /i app.msi /quiet
- Desinstalación limpia vía Panel de Control
- Registro automático en Windows
- Tamaño: ~25-30MB
```

### **NSIS Installer (EXE)**

```bash
# También generado automáticamente
# Ubicación: src-tauri/target/release/bundle/nsis/

# Características del NSIS:
- Instalador gráfico moderno
- Opciones de instalación personalizadas
- Creación de accesos directos
- Tamaño: ~25-30MB
```

### **Firma de Código**

```json
// En tauri.conf.json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.sectigo.com"
    }
  }
}
```

## 🐧 Distribución Linux

### **AppImage**

```bash
# Build para Linux
yarn tauri build --target x86_64-unknown-linux-gnu

# Genera:
# - target/release/bundle/appimage/app.AppImage
# - Ejecutable universal para cualquier distro Linux
# - No requiere instalación
```

### **Debian Package (.deb)**

```bash
# También generado automáticamente
# target/release/bundle/deb/app_0.8.0_amd64.deb

# Instalación:
sudo dpkg -i app_0.8.0_amd64.deb
```

## 🍎 Distribución macOS

### **DMG y App Bundle**

```bash
# Build para macOS (desde macOS)
yarn tauri build --target x86_64-apple-darwin

# Genera:
# - target/release/bundle/dmg/app.dmg
# - target/release/bundle/macos/app.app
```

### **Firma y Notarización**

```bash
# Configurar en tauri.conf.json
{
  "bundle": {
    "macOS": {
      "frameworks": [],
      "minimumSystemVersion": "10.15",
      "exceptionDomain": "",
      "signingIdentity": "Developer ID Application: Your Name",
      "entitlements": "entitlements.plist"
    }
  }
}
```

## 🚀 Integración del Python Sidecar

### **Empaquetado del Backend Python**

```bash
# 1. Crear ejecutable Python con PyInstaller
cd scripts

# Windows:
pyinstaller --onefile `
  --name python_sidecar `
  --add-data "../src-python;src-python" `
  --hidden-import="src-python" `
  python_sidecar.py

# Linux/macOS:
pyinstaller --onefile \
  --name python_sidecar \
  --add-data "../src-python:src-python" \
  --hidden-import="src-python" \
  python_sidecar.py
```

### **Comunicación Frontend-Backend**

```typescript
// En el frontend React
import { Command } from '@tauri-apps/plugin-shell';

// Iniciar Python sidecar
const sidecar = Command.sidecar('python_sidecar');
const child = await sidecar.spawn();

// Enviar comandos
await child.write(JSON.stringify({
  action: 'connect_camera',
  params: { cameraId: 'cam1' }
}) + '\n');

// Escuchar respuestas
child.on('data', (data) => {
  const response = JSON.parse(data);
  console.log('Python response:', response);
});
```

## 📊 Métricas de Build

### **Tamaños Típicos**

| Componente | Tamaño | Comprimido |
|------------|--------|------------|
| Frontend (dist/) | ~2MB | ~500KB |
| Tauri Runtime | ~15MB | ~8MB |
| Python Sidecar | ~25MB | ~10MB |
| **Total App** | **~40-50MB** | **~20-25MB** |

### **Tiempos de Build**

- **Primera build**: 5-10 minutos
- **Builds subsecuentes**: 1-3 minutos
- **Hot reload (dev)**: < 1 segundo

## 🔧 Automatización CI/CD

### **GitHub Actions**

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            rust-target: x86_64-pc-windows-msvc
          - os: ubuntu-latest
            rust-target: x86_64-unknown-linux-gnu
          - os: macos-latest
            rust-target: x86_64-apple-darwin
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 20
          
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.rust-target }}
      
      - name: Install Yarn
        run: npm install -g yarn
        
      - name: Install dependencies
        run: yarn install
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Build Python Sidecar
        run: |
          pip install pyinstaller
          pip install -r requirements.txt
          cd scripts
          pyinstaller --onefile --name python_sidecar python_sidecar.py
        
      - name: Build Tauri App
        run: yarn tauri build --target ${{ matrix.rust-target }}
        
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.os }}-build
          path: src-tauri/target/release/bundle/
```

## 🐛 Troubleshooting Builds

### **Error: MSVC toolchain not found**

```bash
# Instalar Visual Studio Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Seleccionar "Desktop development with C++"

# Verificar instalación correcta:
rustup show
# Debe mostrar: stable-x86_64-pc-windows-msvc
```

### **Error: Module not found (Windows)**

```bash
# SIEMPRE usar Yarn (npm tiene bug con dependencias nativas)
Remove-Item -Recurse -Force node_modules
yarn install    # NO npm install

# Verificar instalación correcta:
Test-Path node_modules/@tauri-apps/cli-win32-x64-msvc
Test-Path node_modules/@rollup/rollup-win32-x64-msvc
```

### **Build muy lento**

```bash
# Limpiar cache
cargo clean
Remove-Item -Recurse -Force src-tauri/target
Remove-Item -Recurse -Force dist
yarn tauri build

# Usar build incremental
yarn tauri build --no-bundle  # Solo compilar, sin empaquetar
```

### **Reducir tamaño del ejecutable**

```bash
# En Cargo.toml
[profile.release]
opt-level = "z"     # Optimizar para tamaño
lto = true          # Link Time Optimization
codegen-units = 1   # Mejor optimización
strip = true        # Eliminar símbolos
```

## 📝 Checklist de Release

- [ ] Incrementar versión en `src-tauri/tauri.conf.json`
- [ ] Incrementar versión en `package.json`
- [ ] Incrementar versión en `src-tauri/Cargo.toml`
- [ ] Actualizar CHANGELOG.md
- [ ] Ejecutar tests Python: `make test`
- [ ] Ejecutar tests frontend: `yarn test`
- [ ] Build local: `yarn tauri build`
- [ ] Probar instalador en máquina limpia
- [ ] Verificar Python sidecar funciona correctamente
- [ ] Crear tag: `git tag v0.8.0`
- [ ] Push tag: `git push origin v0.8.0`
- [ ] CI/CD genera releases automáticamente

---

### 📚 Navegación

[← Anterior: API y Servicios](api-services.md) | [📑 Índice](README.md)