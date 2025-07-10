# 📱 Deployment y Distribución

## 🚀 Build de Aplicación

### **Build Standalone con Flet**

```bash
# Build automático con make
make build-app

# Build manual
cd src
flet pack main.py --name "Universal Camera Viewer" --icon ../assets/icon.ico
```

### **Opciones de Build**

```bash
# Build básico
flet pack main.py

# Build con configuración completa
flet pack main.py \
  --name "Universal Camera Viewer" \
  --description "Visor Universal de Cámaras Multi-Marca" \
  --version "0.7.0" \
  --author "Your Name" \
  --icon ../assets/icon.ico \
  --add-data "../config/*:config/" \
  --add-data "../data/camera_brands.json:data/"
```

## 📦 Packaging con PyInstaller

### **Setup con make**

```bash
# Build distribución completa
make build

# Verificar empaquetado
make release-check
```

### **Configuración Manual**

```bash
# Instalar PyInstaller
pip install pyinstaller

# Generar spec file
pyinstaller --onefile --windowed src/main.py

# Build con spec personalizado
pyinstaller universal_camera_viewer.spec
```

### **Spec File Personalizado**

```python
# universal_camera_viewer.spec
a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config/*.json', 'config'),
        ('src/utils/camera_brands.json', 'utils'),
        ('assets/*', 'assets')
    ],
    hiddenimports=[
        'flet',
        'cv2',
        'onvif',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UniversalCameraViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
```

## 🌐 Distribución Web

### **Flet Web Build**

```python
# src/main.py - Configuración para web
import flet as ft

def main(page: ft.Page):
    # Configuración de página
    page.title = "Universal Camera Viewer"
    page.theme_mode = ft.ThemeMode.SYSTEM
    
    # Tu aplicación aquí
    
if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,  # Para web
        port=8080,
        host="0.0.0.0"  # Accessible desde la red
    )
```

### **Deploy Web Server**

```bash
# Desarrollo local
flet run --web src/main.py

# Producción con gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 src.main:app
```

## 📱 Build Multiplataforma

### **Windows (.exe)**

```bash
# En Windows
make build-app

# Resultado: dist/UniversalCameraViewer.exe
```

### **Linux (AppImage)**

```bash
# En Linux
pip install appimage-builder

# Configurar AppImageBuilder.yml
appimage-builder --recipe AppImageBuilder.yml
```

### **macOS (.app)**

```bash
# En macOS
flet pack main.py --target-platform macos

# Firmar aplicación (opcional)
codesign --deep --force --verify --verbose --sign "Developer ID" dist/main.app
```

### **Cross-platform con Docker**

```dockerfile
# Dockerfile.build
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY config/ config/
COPY assets/ assets/

# Build para la plataforma target
CMD ["python", "-m", "flet", "pack", "src/main.py"]
```

## 🔧 Configuración de Ambiente

### **Variables de Entorno para Producción**

```bash
# .env.production
DEBUG_MODE=false
LOG_LEVEL=WARNING
CAMERA_SCAN_TIMEOUT=30
MAX_CONCURRENT_CONNECTIONS=5
ENABLE_ANALYTICS=true
DATABASE_PATH=./data/camera_data.db
```

### **Configuración por Ambiente**

```python
# config/production.json
{
    "app": {
        "debug": false,
        "auto_scan": false,
        "max_cameras": 20
    },
    "ui": {
        "theme": "auto",
        "animations": true,
        "window_size": [1200, 800]
    },
    "performance": {
        "scan_threads": 4,
        "connection_timeout": 10,
        "retry_attempts": 3
    }
}
```

## 📊 Monitoreo y Analytics

### **Integración con Analytics**

```python
# src/utils/analytics.py
import duckdb
from datetime import datetime

class AnalyticsService:
    def __init__(self):
        self.db = duckdb.connect('data/analytics.db')
        
    def log_camera_connection(self, ip: str, brand: str, success: bool):
        """Log connection attempts for analytics"""
        
    def generate_usage_report(self) -> dict:
        """Generate usage statistics"""
```

### **Performance Monitoring**

```python
# src/utils/monitoring.py
import psutil
import time

class PerformanceMonitor:
    def get_system_stats(self) -> dict:
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
            'active_connections': len(self.connection_manager.connections)
        }
```

## 🚀 CI/CD Pipeline

### **GitHub Actions Example**

```yaml
# .github/workflows/build.yml
name: Build and Release

on:
  push:
    tags: ['v*']

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Build application
      run: make build-app
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: windows-build
        path: dist/
```

## 📦 Distribución de Releases

### **Crear Release**

```bash
# Preparar release
make check-all
make build
make release-check

# Tag de versión
git tag v0.7.0
git push origin v0.7.0
```

### **Estructura de Release**

```bash
releases/
├── v0.7.0/
│   ├── windows/
│   │   └── UniversalCameraViewer-v0.7.0-windows.exe
│   ├── linux/
│   │   └── UniversalCameraViewer-v0.7.0-linux.AppImage
│   ├── macos/
│   │   └── UniversalCameraViewer-v0.7.0-macos.app
│   └── source/
│       └── universal-camera-viewer-v0.7.0.tar.gz
```

## 🔐 Seguridad en Distribución

### **Code Signing**

```bash
# Windows
signtool sign /f certificate.pfx /p password dist/UniversalCameraViewer.exe

# macOS  
codesign --sign "Developer ID Application" dist/UniversalCameraViewer.app
```

### **Verificación de Integridad**

```bash
# Generar checksums
cd dist/
sha256sum UniversalCameraViewer.exe > checksums.txt
md5sum UniversalCameraViewer.exe >> checksums.txt
```

## 🚨 Troubleshooting de Build

### **Error: Missing dependencies**

```bash
# Verificar todas las dependencias
pip freeze > current_deps.txt
diff requirements.txt current_deps.txt
```

### **Error: Flet pack fails**

```bash
# Limpiar cache de Flet
rm -rf ~/.flet
flet doctor  # Verificar instalación
```

### **Error: Large executable size**

```bash
# Optimizar build
pip install upx-ucl
pyinstaller --upx-dir=/path/to/upx main.spec
```

## 📋 Checklist de Release

- [ ] ✅ Todos los tests pasan (`make test`)
- [ ] ✅ Code quality OK (`make check-all`)
- [ ] ✅ Documentación actualizada
- [ ] ✅ Versión bumpeada en pyproject.toml
- [ ] ✅ CHANGELOG.md actualizado
- [ ] ✅ Build exitoso en todas las plataformas
- [ ] ✅ Release notes preparadas
- [ ] ✅ Code signing aplicado
- [ ] ✅ Checksums generados

## 🎯 Próximos Pasos

1. **[📦 Setup Inicial](installation.md)** - Instalar dependencias
2. **[💻 Desarrollo](development.md)** - Configurar entorno dev
3. **[🏛️ Arquitectura](architecture.md)** - Entender estructura

---

**📱 Distribución:** Ejecutables nativos para Windows, Linux, macOS  
**🌐 Web:** Deploy con Flet server para acceso remoto  
**🚀 CI/CD:** Automatización completa de build y release
