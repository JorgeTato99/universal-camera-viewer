# Configuración para Windows - Universal Camera Viewer

## 🔧 Requisitos del Sistema

### 1. Rust + MSVC Toolchain

Para compilar Tauri en Windows, necesitas:

1. **Instalar Rust**:
   - Descarga desde: https://www.rust-lang.org/tools/install
   - Ejecuta `rustup-init.exe`
   - **IMPORTANTE**: Selecciona `stable-x86_64-pc-windows-msvc`
   - NO uses el toolchain GNU, debe ser MSVC

2. **Visual Studio Build Tools**:
   - Si no tienes Visual Studio instalado, descarga Build Tools:
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Instala "Desktop development with C++"

### 2. Node.js y Yarn

1. **Node.js** (v18 o superior):
   - Descarga desde: https://nodejs.org/

2. **Yarn** (OBLIGATORIO):
   ```bash
   npm install -g yarn
   ```

## ⚠️ Bug Crítico de NPM en Windows

### El Problema

NPM tiene un bug que **NO instala dependencias opcionales nativas** en Windows, específicamente:
- `@tauri-apps/cli-win32-x64-msvc`
- `@rollup/rollup-win32-x64-msvc`

Esto causa errores como:
```
Error: Cannot find module '@tauri-apps/cli-win32-x64-msvc'
```

### La Solución: Usar Yarn

Yarn sí respeta e instala correctamente las dependencias opcionales nativas.

**SIEMPRE usa Yarn en lugar de npm:**
```bash
# ❌ NO USES
npm install
npm run dev
npm run tauri-dev

# ✅ USA ESTO
yarn install
yarn dev
yarn tauri-dev
```

## 📋 Guía de Instalación Paso a Paso

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/JorgeTato99/universal-camera-viewer.git
   cd universal-camera-viewer
   ```

2. **Instalar dependencias del Frontend**:
   ```bash
   yarn install    # IMPORTANTE: Usar yarn, no npm
   ```

3. **Instalar dependencias de Python**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Verificar instalación**:
   ```bash
   # Verificar Rust
   rustc --version
   cargo --version
   
   # Verificar que las dependencias nativas están instaladas
   dir node_modules\@tauri-apps\cli-win32-x64-msvc
   dir node_modules\@rollup\rollup-win32-x64-msvc
   ```

## 🚀 Ejecutar la Aplicación

```bash
# Desarrollo con hot reload
yarn tauri-dev

# Build de producción
yarn tauri-build
```

## 🔍 Solución de Problemas

### Error: "Cannot find module '@tauri-apps/cli-win32-x64-msvc'"
- **Causa**: Usaste npm install
- **Solución**: 
  ```bash
  rm -rf node_modules
  yarn install
  ```

### Error: "error: Microsoft Visual C++ 14.0 or greater is required"
- **Causa**: Falta MSVC toolchain
- **Solución**: Instalar Visual Studio Build Tools con C++

### Puerto 5173 ocupado
- **Causa**: Otra aplicación usa el puerto
- **Solución**: Cerrar la otra aplicación o cambiar puerto en `vite.config.ts`

## 📝 Notas Adicionales

- El puerto de Vite (5173) está configurado tanto en `vite.config.ts` como en `tauri.conf.json`
- Si cambias el puerto, actualiza ambos archivos
- Los logs de Python sidecar se guardan en `python_sidecar.log`
- Los builds de producción se generan en `src-tauri/target/release`