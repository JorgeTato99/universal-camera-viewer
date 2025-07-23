# 💻 Guía de Desarrollo

## 🚀 Setup Inicial

```bash
# Configuración completa de desarrollo
make fresh-start

# O paso a paso:
yarn install        # Frontend (USAR YARN)
make install-dev    # Backend Python
make install-pre-commit
make check-all
```

## 🔄 Workflow de Desarrollo

### 1. **Preparar Feature Branch**

```bash
git checkout -b feature/nueva-funcionalidad
```

### 2. **Setup Base de Datos**

```bash
# Recrear base de datos con datos de ejemplo (recomendado)
python src-python/migrate_database.py --force --no-backup

# Verificar que se creó correctamente
python src-python/seed_database.py --verify-only
```

**Scripts de Base de Datos:**
- `migrate_database.py`: Recrea la DB completa desde cero + seeds
- `create_database.py`: Solo crea estructura de tablas (vacía)  
- `seed_database.py`: Inserta/actualiza datos de ejemplo

### 3. **Desarrollo Local**

```bash
# Aplicación completa (Tauri + React + Python)
yarn tauri-dev

# Solo Frontend (React)
yarn dev           # http://localhost:5173

# Solo Backend (Python Flet legacy)
make run           # o python run_python.py

# Con debug
make run-debug
```

### 3. **Verificación de Calidad**

```bash
# Formatear código Python
make format

# Verificar calidad completa
make check-all

# Tests
make test-cov

# Verificar Rust/dependencias
make rust-check
```

### 4. **Pre-commit**

```bash
# Automático con hooks instalados
git commit -m "feat: nueva funcionalidad"

# Manual
make pre-commit
```

## 🛠️ Comandos Esenciales

### **Desarrollo Frontend (Yarn)**

```bash
yarn dev           # Frontend solo
yarn tauri-dev     # App completa con hot reload
yarn build         # Build producción frontend
yarn tauri-build   # Build app nativa
yarn preview       # Preview del build
```

### **Desarrollo Backend (Make)**

```bash
make run           # Ejecutar backend Python
make run-debug     # Ejecutar con debug
make format        # Formatear código
make lint          # Verificar linting
make test          # Ejecutar tests
make type-check    # Verificar tipos
```

### **Comandos Combinados**

```bash
make tauri-dev     # Wrapper para yarn tauri-dev
make frontend-dev  # Wrapper para yarn dev
make yarn-install  # Wrapper para yarn install
make status        # Estado del proyecto
```

## 🏗️ Estructura de Desarrollo

```bash
# Frontend (React/TypeScript)
src/
├── components/       # 🎨 Componentes React
│   ├── Camera/      # Componentes de cámara
│   ├── Controls/    # Controles UI
│   └── Layout/      # Layout components
├── hooks/           # 🪝 Custom React hooks
├── services/        # 📡 Servicios y APIs
├── store/           # 🗃️ Estado global (Zustand)
└── types/           # 📝 TypeScript types

# Backend (Python MVP)
src-python/
├── models/          # 🗃️ Capa de datos
│   ├── camera_model.py
│   └── streaming/   # Modelos de streaming
├── views/           # 🎨 UI Flet (legacy, referencia)
├── presenters/      # 🔗 Lógica MVP (20% completo)
│   ├── camera_presenter.py
│   └── streaming/   # Presenters de video
├── services/        # ⚙️ Servicios de negocio
│   ├── protocol_service.py
│   └── video/       # Servicios de streaming
└── utils/           # 🛠️ Utilidades
    └── video/       # Frame converter
```

## 🎯 Tareas Prioritarias

### **Sprint Actual (Migración Tauri)**

1. **🔗 Configurar Python Sidecar**

   ```typescript
   // En src-tauri/tauri.conf.json
   "bundle": {
     "externalBin": [
       "scripts/python_sidecar"
     ]
   }
   ```

2. **⚛️ Implementar Componentes React**

   ```typescript
   // Crear en src/components/
   - Camera/VideoPlayer.tsx     # Display de video
   - Camera/CameraGrid.tsx      # Grid de cámaras
   - Controls/ConnectionPanel.tsx
   ```

3. **🔌 Conectar IPC Frontend-Backend**

   ```typescript
   // En src/services/
   - cameraService.ts   # Comandos Tauri
   - streamService.ts   # Eventos de video
   ```

### **Próximo Sprint**

1. **Completar Presenter Layer (80% restante)**
2. **Integración DuckDB Analytics**
3. **Test Suite Completo**

## 🔧 Herramientas de Desarrollo

### **VS Code Extensions Recomendadas**

```json
{
  "recommendations": [
    // Python
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    
    // TypeScript/React
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "dsznajder.es7-react-js-snippets",
    
    // Tauri/Rust
    "rust-lang.rust-analyzer",
    "tauri-apps.tauri-vscode"
  ]
}
```

### **Configuración de Proyecto**

```json
// .vscode/settings.json ya configurado con:
- Python paths apuntando a src-python/
- Formateo automático con Black
- TypeScript/React con Prettier
- Exclusiones de archivos temporales
```

## 🐛 Debugging

### **Debug Frontend (React DevTools)**

```bash
# Instalar React DevTools
yarn add -D @react-devtools/core

# En yarn tauri-dev, abrir DevTools con F12
```

### **Debug Backend (Python)**

```python
# Usar logging en lugar de print
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")

# Debug específico de cámaras
python examples/protocols/onvif_example.py
python examples/network/port_scanner.py
```

### **Debug Tauri IPC**

```typescript
// En frontend
import { invoke } from '@tauri-apps/api/core';

// Log comandos
console.log('Invoking command:', commandName, args);

// En Rust (src-tauri/src/main.rs)
println!("Command received: {:?}", command);
```

## 📊 Métricas de Calidad

### **Code Quality Gates**

- **Coverage Python:** >80% para servicios core
- **Linting:** 0 errores en flake8
- **Type Hints:** >70% coverage con mypy
- **TypeScript:** strict mode habilitado
- **Security:** Sin vulnerabilidades altas

### **Performance Targets**

- **Startup:** <3 segundos
- **Hot Reload:** <1 segundo
- **Build Time:** <2 minutos
- **Bundle Size:** <50MB

## 🚨 Problemas Comunes

### **Error: Cannot find module '@tauri-apps/...'**

```bash
# SIEMPRE usar yarn
rm -rf node_modules
yarn install       # NO npm install
```

### **Error: Python imports failing**

```bash
# Verificar PYTHONPATH
cd src-python
python -c "import sys; print(sys.path)"

# O usar imports relativos
from ..services import protocol_service
```

### **Error: Puerto 5173 ocupado**

```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5173
kill -9 <PID>
```

### **Error: Rust compilation failed**

```bash
# Verificar toolchain
rustup default stable-msvc    # Windows
rustup default stable         # Linux/Mac

# Limpiar y reconstruir
cd src-tauri
cargo clean
cd ..
yarn tauri-build
```

## 🎨 Guías de Estilo

### **React/TypeScript**

```typescript
// Componentes funcionales con TypeScript
interface VideoPlayerProps {
  cameraId: string;
  onError?: (error: Error) => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  cameraId, 
  onError 
}) => {
  // Hooks al inicio
  const [frame, setFrame] = useState<string>('');
  
  // Effects después
  useEffect(() => {
    // Lógica
  }, [cameraId]);
  
  // Render al final
  return <img src={frame} alt="Camera view" />;
};
```

### **Python (Google Style)**

```python
def connect_camera(
    ip: str, 
    protocol: CameraProtocol,
    timeout: float = 10.0
) -> ConnectionResult:
    """Conecta a una cámara usando el protocolo especificado.
    
    Args:
        ip: Dirección IP de la cámara
        protocol: Protocolo a usar (ONVIF, RTSP, HTTP)
        timeout: Timeout de conexión en segundos
        
    Returns:
        ConnectionResult con estado y metadata
        
    Raises:
        CameraConnectionError: Si no se puede conectar
    """
    # Implementación
```

## 🎯 Próximos Pasos

1. **[🏛️ Arquitectura Técnica](ARCHITECTURE.md)** - Entender MVP y Tauri
2. **[📡 API y Servicios](api-services.md)** - Backend APIs
3. **[📦 Deployment](deployment.md)** - Build y distribución

---

**💡 Tips:**

- Usa `make help` para ver todos los comandos
- Siempre `yarn` en lugar de `npm`
- Ejecuta `make check-all` antes de commits
- Revisa logs en `python_sidecar.log`

---

### 📚 Navegación

[← Anterior: Configuración Windows](WINDOWS_SETUP.md) | [📑 Índice](README.md) | [Siguiente: Arquitectura Técnica →](ARCHITECTURE.md)
