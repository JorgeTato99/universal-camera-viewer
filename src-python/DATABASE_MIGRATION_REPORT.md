# Informe de Migración de Base de Datos - Estructura 3FN

## Resumen Ejecutivo

Este informe identifica todos los puntos del código que interactúan con la base de datos y necesitan actualización para la nueva estructura normalizada 3FN con 16 tablas.

## Archivos y Servicios Identificados

### 1. **DataService** (`services/data_service.py`)
**Estado**: ⚠️ Parcialmente actualizado
**Líneas críticas**: 306-344, 430-511, 734-768, 962-1332

#### Cambios necesarios:
- ✅ Métodos nuevos ya implementados:
  - `save_camera_with_config()` (líneas 963-1089)
  - `get_camera_full_config()` (líneas 1090-1182)
  - `save_discovered_endpoint()` (líneas 1183-1236)
  - `update_connection_stats()` (líneas 1237-1289)
  
- ❌ Métodos antiguos que necesitan deprecación:
  - `save_camera_data()` (líneas 430-482) - usa estructura antigua
  - `_save_camera_to_db()` (líneas 483-511) - INSERT en tabla antigua
  - `_load_recent_cameras_to_cache()` (líneas 354-391) - SELECT de tabla antigua
  - `_get_camera_from_db()` (líneas 536-581) - SELECT de tabla antigua
  - `_get_filtered_cameras()` (líneas 734-768) - SELECT de tabla antigua

#### Queries SQL a actualizar:
```sql
-- Viejo (línea 362-368):
SELECT * FROM cameras 
WHERE last_seen > datetime('now', '-1 day')

-- Nuevo:
SELECT c.*, cs.last_connection_at 
FROM cameras c
JOIN camera_statistics cs ON c.camera_id = cs.camera_id
WHERE cs.last_connection_at > datetime('now', '-1 day')
```

### 2. **CameraManagerService** (`services/camera_manager_service.py`)
**Estado**: ✅ Bien implementado
**Líneas críticas**: 101-114, 115-204, 208-271

#### Implementación correcta:
- Usa los nuevos métodos del DataService
- Maneja correctamente la estructura 3FN
- Convierte entre modelos de dominio y DB

### 3. **API Router cameras.py** (`routers/cameras.py`)
**Estado**: ❌ Usa datos mock
**Líneas críticas**: 109-188, 195-233

#### Cambios necesarios:
- Reemplazar datos mock con llamadas a CameraManagerService
- Implementar persistencia real en endpoints:
  - `list_cameras()` (línea 195)
  - `connect_camera()` (línea 273)
  - `disconnect_camera()` (línea 304)

### 4. **API Router cameras_v2.py** (`routers/cameras_v2.py`)
**Estado**: ✅ Correctamente implementado
**Líneas críticas**: 160-201, 237-304

#### Implementación correcta:
- Usa CameraManagerService
- Maneja la nueva estructura correctamente
- Endpoints completos para CRUD

### 5. **CameraPresenter** (`presenters/camera_presenter.py`)
**Estado**: ⚠️ Necesita actualización
**Líneas críticas**: 105-137

#### Cambios necesarios:
- Actualizar `_load_camera_model()` para usar CameraManagerService
- Cambiar de DataService a CameraManagerService para consistencia

### 6. **ConfigService** (`services/config_service.py`)
**Estado**: ❓ Por revisar completamente
- Puede necesitar integración con tabla `system_config`

### 7. **Servicios de Video/Streaming**
**Estado**: ✅ No requieren cambios
- Trabajan con modelos en memoria
- No acceden directamente a la DB

## Tablas de la Nueva Estructura y su Uso

### Tablas Principales (ya en uso):
1. ✅ **cameras** - Información básica
2. ✅ **camera_credentials** - Credenciales encriptadas
3. ✅ **camera_protocols** - Protocolos configurados
4. ✅ **camera_endpoints** - URLs descubiertas
5. ✅ **camera_statistics** - Métricas agregadas
6. ✅ **connection_logs** - Historial de conexiones

### Tablas por Implementar:
7. ❌ **camera_capabilities** - Features soportadas
8. ❌ **stream_profiles** - Perfiles de streaming
9. ❌ **camera_events** - Eventos importantes
10. ❌ **network_scans** - Escaneos de red
11. ❌ **scan_results** - Resultados de escaneo
12. ❌ **snapshots** - Capturas guardadas
13. ❌ **recordings** - Grabaciones
14. ❌ **system_config** - Configuración global
15. ❌ **config_templates** - Plantillas por marca

## Plan de Migración Recomendado

### Fase 1: Deprecar métodos antiguos (Inmediato)
1. Marcar como deprecated los métodos antiguos en DataService
2. Crear wrapper methods que usen la nueva estructura
3. Actualizar logs para advertir sobre uso de métodos antiguos

### Fase 2: Actualizar componentes (1-2 días)
1. Actualizar CameraPresenter para usar CameraManagerService
2. Migrar cameras.py a usar datos reales en lugar de mock
3. Implementar cache mejorado en DataService con nueva estructura

### Fase 3: Implementar tablas faltantes (3-5 días)
1. Implementar gestión de capabilities
2. Agregar stream_profiles
3. Integrar system_config con ConfigService
4. Implementar eventos y logs

### Fase 4: Migración de datos (1 día)
1. Script de migración de datos existentes
2. Validación de integridad
3. Backup antes de migración

## Código de Ejemplo para Migración

### Wrapper para compatibilidad:
```python
# En DataService
async def save_camera_data(self, camera: CameraModel) -> bool:
    """
    DEPRECATED: Use save_camera_with_config instead.
    Mantiene compatibilidad con código antiguo.
    """
    self.logger.warning("DEPRECATED: save_camera_data() - use save_camera_with_config()")
    
    credentials = {
        'username': camera.connection_config.username,
        'password': camera.connection_config.password
    }
    
    return await self.save_camera_with_config(camera, credentials)
```

### Actualización de CameraPresenter:
```python
# En CameraPresenter._load_camera_model()
async def _load_camera_model(self) -> None:
    """Carga el modelo de cámara usando CameraManagerService."""
    try:
        from services.camera_manager_service import camera_manager_service
        
        self._camera_model = await camera_manager_service.get_camera(self.camera_id)
        self.logger.info(f"Modelo de cámara cargado: {self.camera_id}")
        
    except CameraNotFoundError:
        # Crear nuevo modelo si no existe
        self._camera_model = CameraModel(
            brand="Unknown",
            model="Unknown", 
            display_name=self.camera_id,
            connection_config=ConnectionConfig(
                ip="",
                username="admin",
                password=""
            )
        )
```

## Conclusiones

1. La nueva estructura 3FN está bien diseñada y parcialmente implementada
2. Los servicios principales (CameraManagerService, cameras_v2.py) ya usan la nueva estructura
3. Quedan componentes legacy que necesitan actualización
4. La migración puede hacerse de forma gradual sin romper funcionalidad

## Prioridades Inmediatas

1. 🔴 **Alta**: Deprecar métodos antiguos en DataService
2. 🟡 **Media**: Actualizar CameraPresenter 
3. 🟡 **Media**: Migrar cameras.py de mock a datos reales
4. 🟢 **Baja**: Implementar tablas adicionales (capabilities, events, etc.)

## Métricas de Éxito

- [ ] Todos los métodos antiguos marcados como deprecated
- [ ] Cero queries directas a tabla `cameras` antigua
- [ ] Todos los componentes usando CameraManagerService
- [ ] Tests pasando con nueva estructura
- [ ] Performance igual o mejor que estructura anterior