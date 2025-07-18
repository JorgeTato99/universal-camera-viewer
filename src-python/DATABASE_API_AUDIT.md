# Auditoría de Cobertura de API vs Base de Datos

## Fecha: 2025-01-18

Este documento analiza la cobertura de las APIs existentes contra las tablas de la base de datos y documenta las APIs faltantes.

## 📊 Resumen de Cobertura

- **Total de tablas**: 16
- **Tablas con API completa**: 6 (37.5%)
- **Tablas con API parcial**: 4 (25%)
- **Tablas sin API**: 6 (37.5%)

## ✅ Tablas con Cobertura Completa

### 1. **cameras**

- **APIs existentes**:
  - `GET /cameras` - Listar cámaras
  - `POST /cameras` - Crear cámara
  - `GET /cameras/{id}` - Obtener cámara
  - `PUT /cameras/{id}` - Actualizar cámara
  - `DELETE /cameras/{id}` - Eliminar cámara
  - `GET /cameras/{id}/status` - Estado de cámara
- **Estado**: ✅ Completo

### 2. **camera_credentials**

- **APIs existentes**:
  - `GET /credentials` - Listar credenciales
  - `POST /credentials` - Crear credencial
  - `GET /credentials/{id}` - Obtener credencial
  - `PUT /credentials/{id}` - Actualizar credencial
  - `DELETE /credentials/{id}` - Eliminar credencial
  - `POST /credentials/{id}/test` - Probar credencial
- **Estado**: ✅ Completo

### 3. **camera_protocols**

- **APIs existentes**:
  - `GET /cameras/{id}/protocols` - Listar protocolos
  - `PUT /cameras/{id}/protocols/{type}` - Actualizar protocolo
  - `POST /cameras/{id}/protocols/{type}/test` - Probar protocolo
  - `POST /cameras/{id}/protocols/discover` - Descubrir protocolos
- **Estado**: ✅ Completo

### 4. **stream_profiles**

- **APIs existentes**:
  - `GET /stream-profiles` - Listar perfiles
  - `POST /stream-profiles` - Crear perfil
  - `GET /stream-profiles/{id}` - Obtener perfil
  - `PUT /stream-profiles/{id}` - Actualizar perfil
  - `DELETE /stream-profiles/{id}` - Eliminar perfil
  - `POST /stream-profiles/{id}/apply` - Aplicar perfil
- **Estado**: ✅ Completo

### 5. **network_scans**

- **APIs existentes**:
  - `POST /scanner/scan` - Iniciar escaneo
  - `GET /scanner/scan/{id}/progress` - Progreso de escaneo
  - `GET /scanner/scan/{id}/results` - Resultados de escaneo
  - `POST /scanner/scan/{id}/stop` - Detener escaneo
  - `DELETE /scanner/scan/{id}` - Eliminar escaneo
- **Estado**: ✅ Completo

### 6. **scan_results**

- **APIs existentes**:
  - Cubierto por `GET /scanner/scan/{id}/results`
  - `POST /scanner/quick-scan` - Escaneo rápido
  - `POST /scanner/detect-protocols` - Detectar protocolos
- **Estado**: ✅ Completo

## ⚠️ Tablas con Cobertura Parcial

### 1. **camera_endpoints**

- **APIs existentes**:
  - `GET /cameras/{id}/protocols/endpoints` - Obtener endpoints
- **APIs faltantes**:

  ```
  POST /cameras/{id}/endpoints - Crear endpoint manual
  PUT /cameras/{id}/endpoints/{id} - Actualizar endpoint
  DELETE /cameras/{id}/endpoints/{id} - Eliminar endpoint
  POST /cameras/{id}/endpoints/{id}/verify - Verificar endpoint
  ```

### 2. **connection_logs**

- **APIs existentes**:
  - `GET /connections/{id}/history` - Historial básico
- **APIs faltantes**:

  ```
  GET /connections/logs - Listar todos los logs con filtros
  GET /connections/logs/stats - Estadísticas agregadas
  DELETE /connections/logs - Limpiar logs antiguos
  GET /connections/logs/export - Exportar logs
  ```

### 3. **camera_events**

- **APIs existentes**:
  - WebSocket `/events` - Stream de eventos en tiempo real
- **APIs faltantes**:

  ```
  GET /events - Listar eventos históricos
  GET /events/{id} - Obtener detalle de evento
  PUT /events/{id}/acknowledge - Reconocer evento
  DELETE /events - Limpiar eventos antiguos
  GET /events/stats - Estadísticas de eventos
  ```

### 4. **system_config**

- **APIs existentes**:
  - `GET /config` - Obtener configuración (parcial)
  - `PUT /config` - Actualizar configuración (parcial)
- **APIs faltantes**:

  ```
  GET /config/categories - Listar categorías
  GET /config/{category} - Obtener config por categoría
  POST /config/reset - Restaurar valores por defecto
  GET /config/validation - Obtener reglas de validación
  ```

## ❌ Tablas sin APIs

### 1. **camera_capabilities**

- **APIs faltantes**:

  ```
  GET /cameras/{id}/capabilities - Listar capacidades
  POST /cameras/{id}/capabilities/detect - Auto-detectar capacidades
  PUT /cameras/{id}/capabilities/{type} - Actualizar capacidad
  GET /capabilities/types - Listar tipos de capacidades
  ```

### 2. **camera_statistics**

- **APIs faltantes**:

  ```
  GET /cameras/{id}/statistics - Estadísticas de cámara
  GET /statistics/summary - Resumen global
  POST /statistics/reset - Reiniciar estadísticas
  GET /statistics/export - Exportar estadísticas
  ```

### 3. **snapshots**

- **APIs faltantes**:

  ```
  GET /snapshots - Listar snapshots
  POST /cameras/{id}/snapshots - Capturar snapshot
  GET /snapshots/{id} - Obtener snapshot
  DELETE /snapshots/{id} - Eliminar snapshot
  GET /snapshots/{id}/download - Descargar snapshot
  POST /snapshots/cleanup - Limpiar snapshots antiguos
  ```

### 4. **recordings**

- **APIs faltantes**:

  ```
  GET /recordings - Listar grabaciones
  POST /cameras/{id}/recordings/start - Iniciar grabación
  POST /cameras/{id}/recordings/stop - Detener grabación
  GET /recordings/{id} - Obtener info de grabación
  DELETE /recordings/{id} - Eliminar grabación
  GET /recordings/{id}/download - Descargar grabación
  GET /recordings/{id}/stream - Stream de grabación
  ```

### 5. **config_templates**

- **APIs faltantes**:

  ```
  GET /templates - Listar plantillas
  POST /templates - Crear plantilla
  GET /templates/{id} - Obtener plantilla
  PUT /templates/{id} - Actualizar plantilla
  DELETE /templates/{id} - Eliminar plantilla
  POST /templates/{id}/apply - Aplicar plantilla a cámara
  ```

### 6. **Vistas (camera_overview, verified_endpoints)**

- **APIs faltantes**:

  ```
  GET /cameras/overview - Vista general de cámaras
  GET /endpoints/verified - Endpoints verificados
  ```

## 📝 APIs Adicionales Recomendadas

### 1. **Dashboard/Métricas**

```
GET /dashboard/stats - Estadísticas generales del sistema
GET /dashboard/health - Estado de salud del sistema
GET /dashboard/alerts - Alertas activas
```

### 2. **Búsqueda y Filtrado**

```
POST /search/cameras - Búsqueda avanzada de cámaras
POST /search/events - Búsqueda de eventos
POST /search/logs - Búsqueda en logs
```

### 3. **Importación/Exportación**

```
GET /export/cameras - Exportar configuración de cámaras
POST /import/cameras - Importar configuración de cámaras
GET /backup/database - Backup de base de datos
POST /restore/database - Restaurar base de datos
```

### 4. **Mantenimiento**

```
POST /maintenance/cleanup - Limpiar datos antiguos
POST /maintenance/optimize - Optimizar base de datos
GET /maintenance/status - Estado de mantenimiento
```

## 🎯 Prioridad de Implementación

### Alta Prioridad (Funcionalidad Core)

1. **camera_capabilities** - Necesario para gestión completa de cámaras
2. **camera_statistics** - Importante para monitoreo
3. **snapshots** - Funcionalidad básica esperada
4. **camera_endpoints** (completar) - Gestión de URLs

### Media Prioridad (Mejora UX)

5. **recordings** - Funcionalidad avanzada
6. **connection_logs** (completar) - Debugging y análisis
7. **camera_events** (completar) - Historial de eventos
8. **config_templates** - Facilita configuración

### Baja Prioridad (Nice to Have)

9. **system_config** (completar) - Ya funcional parcialmente
10. APIs de dashboard y búsqueda
11. APIs de importación/exportación
12. APIs de mantenimiento

## 📊 Estimación de Esfuerzo

- **Total de endpoints faltantes**: ~65
- **Tiempo estimado por endpoint**: 30-60 minutos
- **Tiempo total estimado**: 32-65 horas
- **Con testing incluido**: 50-100 horas

## 🔧 Recomendaciones

1. **Crear un router por entidad faltante**:
   - `capabilities.py`
   - `statistics.py`
   - `snapshots.py`
   - `recordings.py`
   - `templates.py`

2. **Usar los schemas de validación ya creados** como base

3. **Implementar paginación** en todos los endpoints de listado

4. **Agregar filtros avanzados** en endpoints de búsqueda

5. **Documentar con OpenAPI** todos los nuevos endpoints

6. **Crear tests unitarios** para cada nuevo endpoint

## 📄 Plantilla de Implementación

Para cada tabla sin API, seguir esta estructura:

```python
# routers/{entity}.py
from fastapi import APIRouter, HTTPException, status, Depends
from api.schemas.requests.{entity}_requests import *
from api.schemas.responses.{entity}_responses import *
from api.dependencies.validation_deps import *

router = APIRouter(
    prefix="/{entities}",
    tags=["{entities}"],
    responses={404: {"description": "Not found"}}
)

# Implementar CRUD completo
# GET / - Listar con paginación y filtros
# POST / - Crear nuevo
# GET /{id} - Obtener por ID
# PUT /{id} - Actualizar
# DELETE /{id} - Eliminar
# + Endpoints específicos según entidad
```
