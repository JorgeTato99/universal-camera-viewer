# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Cursor Rules Reference

This project uses structured Cursor rules located in `.cursor/rules/`. Key rules to follow:

### 🎯 Cursor Rules Organization

The project follows strict development rules defined in `.cursor/rules/`:

1. **Architecture Rules**
   - `01-mvp-architecture.mdc` - MVP pattern with SOLID principles
   - `README.mdc` - Overview and rule application guide

2. **Coding Standards**
   - `02-coding-conventions.mdc` - Language conventions (English code, Spanish docs)
   - `03-type-hints.mdc` - Mandatory type annotations

3. **Layer-Specific Rules**
   - `04-models-layer.mdc` - Domain models and validation
   - `05-flet-views.mdc` - UI components with Material Design 3
   - `06-presenters-layer.mdc` - Business logic coordination
   - `07-services-layer.mdc` - External services and APIs

4. **Technical Patterns**
   - `08-error-handling.mdc` - Exception hierarchy and recovery
   - `09-async-patterns.mdc` - Asynchronous programming patterns

**⚠️ Important**: These rules are automatically applied by Cursor. Always review the specific `.mdc` files in `.cursor/rules/` for detailed implementation guidelines before writing code.

## Common Development Commands

### Running the Application
```bash
# Main Flet application with Material Design 3 UI
python src/main.py

# Legacy Tkinter viewer (if needed for compatibility)
python examples/gui/viewer_example.py

# Port discovery tools with optimized UX
python examples/gui/discovery_demo.py
```

### Development Workflow
```bash
# Install all dependencies (production + dev)
make install-dev

# Run linting and formatting
make format      # Format code with black and isort
make lint        # Run flake8 checks
make type-check  # Run mypy type checking

# Run all quality checks
make check-all

# Run tests
make test        # Basic test run
make test-cov    # Tests with coverage report
```

### Building and Packaging
```bash
# Build distribution packages
make build

# Build standalone Flet application
make build-app

# Clean build artifacts
make clean
```

## High-Level Architecture

This project implements **Model-View-Presenter (MVP)** pattern with strict separation of concerns:

### Core Architecture Layers

1. **Model Layer** (`src/models/`) - ✅ Complete
   - Domain entities and state management
   - `CameraModel`: Camera configurations and status
   - `ConnectionModel`: Active connection states
   - `ScanModel`: Network scan results

2. **View Layer** (`src/views/`) - ✅ 95% Complete
   - Flet UI components with Material Design 3
   - `MainView`: Primary application interface with navigation
   - `CameraView`: Camera management interface
   - Component hierarchy uses modern Material 3 patterns

3. **Presenter Layer** (`src/presenters/`) - 🚧 20% Complete
   - Business logic coordination between View and Model
   - Currently migrating from direct service calls to MVP pattern
   - Priority: Complete presenter implementations for proper MVP

4. **Services Layer** (`src/services/`) - ✅ Complete
   - `ProtocolService`: ONVIF, RTSP, HTTP/CGI protocol handling
   - `ConnectionService`: Camera connection management
   - `ScanService`: Network scanning and discovery
   - `ConfigService`: Configuration persistence
   - `DataService`: Database operations

### Key Architectural Principles

- **No direct View → Service communication**: Views must go through Presenters
- **Async operations**: All I/O operations use async/await patterns
- **Error boundaries**: Each layer handles its own errors appropriately
- **State management**: Only Presenters coordinate state between layers

### Protocol Support by Camera Brand

- **Dahua**: ONVIF (port 80), RTSP (requires DMSS workflow)
- **TP-Link**: ONVIF (port 2020), RTSP direct
- **Steren**: ONVIF (port 8000), RTSP (port 5543)
- **Generic**: Auto-detection with 16+ RTSP patterns

### Critical Implementation Notes

1. **MVP Migration**: Currently migrating from mixed architecture to pure MVP. When implementing new features, always use Presenter pattern.

2. **Flet UI State**: Never modify UI directly from services. All UI updates must flow through presenters.

3. **Connection Handling**: Each camera brand has specific connection requirements. Always check `protocol_handlers/` for brand-specific implementations.

4. **Performance Targets**: 
   - FPS: 13-20+ depending on camera
   - Memory: < 200MB for 4 cameras
   - CPU: < 15% during active streaming

5. **Testing**: When adding new features, ensure they're testable in isolation. Services should not depend on UI, and presenters should be mockable.

### Current Development Priorities

1. Complete Presenter layer implementation (80% remaining)
2. Add DuckDB integration for analytics
3. Implement comprehensive test suite
4. Package as native executable with Flet

### Code Style Requirements

#### Language Conventions (02-coding-conventions.mdc)
- **Code in English**: Variables, functions, classes, constants
  - Examples: `camera_model`, `connect_camera()`, `CameraModel`, `MAX_RETRIES`
- **Documentation in Spanish**: Comments, docstrings, TODOs
  - Use Google-style docstrings in Spanish
  - Inline comments explain "why" not "what"

#### Type Hints (03-type-hints.mdc)
- **Mandatory type hints**: ALL functions, methods, and class variables
- **No `Any` without justification**: Use specific types
- **Import from typing**: `Optional`, `List`, `Dict`, `Callable`, etc.
- **Use `Optional[T]` for nullable**: Not `Union[T, None]`

#### Async Patterns (09-async-patterns.mdc)
- **All I/O must be async**: Network, file operations, database
- **Never use `time.sleep()`**: Use `await asyncio.sleep()`
- **Proper task cleanup**: Always cancel and await tasks
- **Timeout on network operations**: Use `asyncio.timeout()`
- **Concurrent operations**: Use `asyncio.gather()` for parallel work

#### Error Handling (08-error-handling.mdc)
- **Custom domain exceptions**: Inherit from `CameraViewerError`
- **User-friendly messages**: Show comprehensible errors to users
- **Detailed logging**: Technical details for debugging
- **Recovery patterns**: Retry with exponential backoff
- **Never silence critical errors**: Always log unexpected exceptions

#### MVP Architecture Rules
- **View → Presenter**: Via callbacks only (`on_action`, `on_navigation`)
- **Presenter → View**: Via public update methods
- **Presenter → Service**: Async business operations
- **Service → Presenter**: Via event listeners
- **Never**: View directly accessing Service or Model persistence

#### Naming Conventions
- **Files**: `snake_case.py` (e.g., `camera_model.py`)
- **Classes**: `PascalCase` (e.g., `CameraModel`)
- **Functions/Variables**: `snake_case` (e.g., `connect_camera`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_CONNECTIONS`)
- **Private**: Prefix with `_` (e.g., `_internal_method`)

#### Layer-Specific Rules
- **Models**: Pure domain logic, no I/O, validation in `__post_init__`
- **Views**: UI only, no business logic, Material Design 3 components
- **Presenters**: Async coordination, state management, error handling
- **Services**: Singleton pattern, async operations, event-driven

### Example Code Patterns

#### Model with Validation (04-models-layer.mdc)
```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import ipaddress

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

@dataclass
class CameraModel:
    """Modelo de dominio para una cámara IP."""
    camera_id: str
    ip: str
    brand: str
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    
    def __post_init__(self):
        """Validación automática después de inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """Valida la integridad del modelo."""
        if not self.camera_id:
            raise ValidationError("camera_id es obligatorio")
        try:
            ipaddress.ip_address(self.ip)
        except ValueError:
            raise InvalidIPAddressError(self.ip)
```

#### Presenter with MVP Pattern (06-presenters-layer.mdc)
```python
class CameraPresenter(BasePresenter):
    """Presenter para gestión de cámaras."""
    
    def __init__(self, scan_service: ScanService, connection_service: ConnectionService):
        super().__init__()
        self._scan_service = scan_service
        self._connection_service = connection_service
        self._cameras: Dict[str, CameraModel] = {}
    
    async def _handle_view_action(self, action: str, params: Dict[str, Any]) -> None:
        """Maneja acciones desde la vista."""
        try:
            if action == "connect_camera":
                await self._connect_camera(params["camera_id"])
        except CameraConnectionError as e:
            self._show_user_error(f"Error de conexión: {e.message}")
    
    async def _connect_camera(self, camera_id: str) -> None:
        """Conecta a una cámara específica."""
        camera = self._cameras.get(camera_id)
        if not camera:
            raise ValidationError(f"Cámara {camera_id} no encontrada")
        
        try:
            camera.status = ConnectionStatus.CONNECTING
            await self._update_view_cameras()
            
            success = await self._connection_service.connect_camera(
                ip=camera.ip,
                timeout=10.0
            )
            
            camera.status = ConnectionStatus.CONNECTED if success else ConnectionStatus.ERROR
        finally:
            await self._update_view_cameras()
```

#### Service with Async Pattern (07-services-layer.mdc)
```python
class ConnectionService(BaseService):
    """Servicio singleton para conexiones."""
    
    @handle_service_errors(
        error_message="Error conectando cámara",
        error_code="CAM_CONNECTION_FAILED"
    )
    async def connect_camera(self, ip: str, timeout: float = 10.0) -> bool:
        """
        Establece conexión con una cámara IP.
        
        Args:
            ip: Dirección IP de la cámara
            timeout: Timeout de conexión en segundos
            
        Returns:
            True si la conexión fue exitosa
        """
        # Verificar cache
        cache_key = f"connection:{ip}"
        if cached := self._get_cached(cache_key):
            return cached
        
        try:
            async with asyncio.timeout(timeout):
                session = await self._get_session(ip)
                async with session.get(f"http://{ip}/api/status") as response:
                    is_connected = response.status < 400
                    
            # Cache resultado
            self._set_cache(cache_key, is_connected, ttl_seconds=300)
            
            # Emitir evento
            self._emit_event("connection_change", ip, is_connected)
            
            return is_connected
            
        except asyncio.TimeoutError:
            raise CameraConnectionError(ip, "Timeout de conexión")
```

#### View with Flet (05-flet-views.mdc)
```python
class CameraGridView(BaseView):
    """Vista para grilla de cámaras."""
    
    def build(self) -> ft.Control:
        """Construye la grilla de cámaras."""
        return ft.Container(
            content=ft.Column([
                self._build_header(),
                self._build_camera_grid(),
            ]),
            padding=ft.padding.all(16)
        )
    
    def _on_connect_clicked(self, camera_id: str) -> None:
        """Maneja click en conectar - solo emite evento."""
        if self.on_action:
            self.on_action("connect_camera", {"camera_id": camera_id})
    
    def set_cameras_data(self, cameras: List[Dict[str, Any]]) -> None:
        """Actualiza datos desde Presenter."""
        self._cameras_data = cameras
        self.update()
```