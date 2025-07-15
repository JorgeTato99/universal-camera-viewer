# Esquema de Base de Datos - Universal Camera Viewer

## Diseño en Tercera Forma Normal (3FN)

Este documento describe la estructura de la base de datos siguiendo las mejores prácticas internacionales y estándares de diseño.

## Convenciones Utilizadas

### 1. **Identificadores (Primary Keys)**

- **UUID v4** para entidades principales (`camera_id`, `scan_id`, `snapshot_id`)
  - Formato: `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`
  - Únicos globalmente, inmutables, distribuibles
- **INTEGER AUTOINCREMENT** para tablas secundarias
  - Eficiente para JOINs internos
  - Menor espacio en índices

### 2. **Nomenclatura**

- **Primary Keys**: `tabla_id` (ej: `camera_id`, `credential_id`)
- **Foreign Keys**: Mismo nombre que el PK referenciado
- **Booleanos**: Prefijo `is_` o `has_` (ej: `is_active`, `has_audio`)
- **Timestamps**: Sufijo `_at` (ej: `created_at`, `updated_at`)
- **Contadores**: Prefijo según contexto (ej: `total_`, `max_`, `average_`)

### 3. **Tipos de Datos**

- **TEXT**: Strings, UUIDs, JSONs
- **INTEGER**: Números enteros, booleanos (0/1)
- **REAL**: Números decimales
- **TIMESTAMP**: Fechas y horas (ISO 8601)
- **JSON**: Datos estructurados complejos

## Diagrama de Relaciones

```bash
cameras (1) ─────┬──── (N) camera_credentials
                 ├──── (N) camera_protocols  
                 ├──── (N) camera_endpoints
                 ├──── (N) camera_capabilities
                 ├──── (N) stream_profiles
                 ├──── (1) camera_statistics
                 ├──── (N) connection_logs
                 ├──── (N) camera_events
                 ├──── (N) snapshots
                 └──── (N) recordings

network_scans (1) ────── (N) scan_results

system_config (standalone)
config_templates (standalone)
```

## Tablas Principales

### 1. **cameras** - Información Principal de Cámaras

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| camera_id | TEXT PK | UUID v4 único | CHECK formato UUID |
| code | TEXT UNIQUE | Código legible opcional | ej: "Dahua_IPC-HDW1200SP_192_168_1_100" |
| brand | TEXT NOT NULL | Marca de la cámara | |
| model | TEXT NOT NULL | Modelo específico | |
| display_name | TEXT NOT NULL | Nombre para mostrar | CHECK length > 0 |
| ip_address | TEXT NOT NULL | Dirección IP | |
| mac_address | TEXT | Dirección MAC | |
| firmware_version | TEXT | Versión del firmware | |
| hardware_version | TEXT | Versión del hardware | |
| serial_number | TEXT UNIQUE | Serial del fabricante | |
| location | TEXT | Ubicación física | |
| description | TEXT | Descripción adicional | |
| is_active | BOOLEAN | Estado activo | DEFAULT 1 |
| created_at | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |
| created_by | TEXT | Usuario creador | |
| updated_by | TEXT | Usuario que actualizó | |

### 2. **camera_credentials** - Credenciales de Acceso

Separada por seguridad, permite múltiples credenciales por cámara.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| credential_id | INTEGER PK | ID único |
| camera_id | TEXT FK | Referencia a cameras |
| username | TEXT | Nombre de usuario |
| password_encrypted | TEXT | Contraseña encriptada |
| auth_type | TEXT | Tipo de autenticación (basic, digest, etc) |
| api_key | TEXT | API key si aplica |
| certificate_path | TEXT | Ruta a certificado SSL |
| is_default | BOOLEAN | Si es la credencial por defecto |

### 3. **camera_protocols** - Configuración de Protocolos

Un registro por cada protocolo soportado por la cámara.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| protocol_id | INTEGER PK | ID único |
| camera_id | TEXT FK | Referencia a cameras |
| protocol_type | TEXT | Tipo (ONVIF, RTSP, HTTP, etc) |
| port | INTEGER | Puerto del protocolo |
| is_enabled | BOOLEAN | Si está habilitado |
| is_primary | BOOLEAN | Si es el protocolo principal |
| version | TEXT | Versión del protocolo |
| configuration | TEXT | Config adicional en JSON |

### 4. **camera_endpoints** - URLs y Endpoints Descubiertos

Almacena todas las URLs descubiertas o configuradas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| endpoint_id | INTEGER PK | ID único |
| camera_id | TEXT FK | Referencia a cameras |
| endpoint_type | TEXT | Tipo (rtsp_main, snapshot, etc) |
| url | TEXT | URL completa |
| protocol | TEXT | Protocolo usado |
| is_verified | BOOLEAN | Si fue verificada exitosamente |
| last_verified | TIMESTAMP | Última verificación |
| response_time_ms | INTEGER | Tiempo de respuesta |
| priority | INTEGER | Prioridad de uso (0=mayor) |
| metadata | TEXT | Metadata adicional JSON |

### 5. **camera_capabilities** - Capacidades de la Cámara

Features y capacidades soportadas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| capability_id | INTEGER PK | ID único |
| camera_id | TEXT FK | Referencia a cameras |
| capability_type | TEXT | Tipo (ptz, audio, ir, etc) |
| is_supported | BOOLEAN | Si está soportado |
| configuration | TEXT | Config específica JSON |

### 6. **stream_profiles** - Perfiles de Streaming

Configuraciones de streaming disponibles.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| profile_id | INTEGER PK | ID único |
| camera_id | TEXT FK | Referencia a cameras |
| profile_name | TEXT | Nombre del perfil |
| stream_type | TEXT | Tipo (main, sub, third) |
| resolution | TEXT | Resolución (1920x1080) |
| fps | INTEGER | Frames por segundo |
| bitrate | INTEGER | Bitrate en kbps |
| codec | TEXT | Codec usado |
| quality | TEXT | Calidad (high, medium, low) |
| channel | INTEGER | Canal (default 1) |
| subtype | INTEGER | Subtipo (default 0) |
| is_default | BOOLEAN | Si es el perfil por defecto |

### 7. **camera_statistics** - Estadísticas de Uso

Una fila por cámara con estadísticas acumuladas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| stat_id | INTEGER PK | ID único |
| camera_id | TEXT FK UNIQUE | Referencia a cameras |
| total_connections | INTEGER | Total de conexiones |
| successful_connections | INTEGER | Conexiones exitosas |
| failed_connections | INTEGER | Conexiones fallidas |
| total_uptime_minutes | INTEGER | Minutos total activo |
| total_data_mb | REAL | MB totales transferidos |
| average_fps | REAL | FPS promedio |
| average_latency_ms | INTEGER | Latencia promedio |
| last_connection_at | TIMESTAMP | Última conexión |
| last_error_at | TIMESTAMP | Último error |
| last_error_message | TEXT | Mensaje del último error |

### 8. **connection_logs** - Historial de Conexiones

Log detallado de cada intento de conexión.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| log_id | INTEGER PK | ID único |
| camera_id | TEXT FK | Referencia a cameras |
| connection_type | TEXT | Tipo de conexión |
| protocol_used | TEXT | Protocolo usado |
| endpoint_used | TEXT | URL/endpoint usado |
| status | TEXT | Estado (success, failed) |
| error_code | TEXT | Código de error |
| error_message | TEXT | Mensaje de error |
| duration_ms | INTEGER | Duración en ms |
| bytes_transferred | INTEGER | Bytes transferidos |
| timestamp | TIMESTAMP | Fecha/hora del evento |

### 9. **network_scans** - Escaneos de Red

Registro de escaneos realizados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| scan_id | TEXT PK | ID único del escaneo |
| scan_type | TEXT | Tipo de escaneo |
| target_network | TEXT | Red objetivo |
| start_time | TIMESTAMP | Inicio del escaneo |
| end_time | TIMESTAMP | Fin del escaneo |
| duration_seconds | REAL | Duración en segundos |
| total_hosts_scanned | INTEGER | Hosts escaneados |
| cameras_found | INTEGER | Cámaras encontradas |
| status | TEXT | Estado del escaneo |
| created_by | TEXT | Usuario que inició |
| metadata | TEXT | Metadata adicional |

### 10. **scan_results** - Resultados de Escaneo

Resultados detallados por cada host encontrado.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| result_id | INTEGER PK | ID único |
| scan_id | TEXT FK | Referencia a network_scans |
| ip_address | TEXT | IP encontrada |
| mac_address | TEXT | MAC encontrada |
| hostname | TEXT | Hostname si existe |
| is_camera | BOOLEAN | Si es una cámara |
| detected_brand | TEXT | Marca detectada |
| detected_model | TEXT | Modelo detectado |
| open_ports | TEXT | Puertos abiertos JSON |
| protocols_detected | TEXT | Protocolos detectados JSON |
| response_time_ms | INTEGER | Tiempo de respuesta |
| metadata | TEXT | Metadata adicional |

## Ventajas de esta Estructura

### 1. **Normalización Completa (3FN)**

- **Sin redundancia**: Cada dato existe en un solo lugar
- **Sin dependencias transitivas**: Todos los campos dependen directamente de la PK
- **Actualizaciones atómicas**: Cambiar un dato no requiere actualizar múltiples registros

### 2. **Seguridad Mejorada**

- **Credenciales separadas**: En tabla aparte con encriptación
- **Múltiples credenciales**: Soporte para diferentes usuarios por cámara
- **Auditoría completa**: Logs detallados de todas las conexiones

### 3. **Flexibilidad**

- **Múltiples URLs**: Puede almacenar todas las URLs descubiertas
- **Protocolos dinámicos**: Fácil agregar nuevos protocolos
- **Capacidades extensibles**: Sistema de capacidades genérico

### 4. **Performance**

- **Índices optimizados**: En todos los campos de búsqueda frecuente
- **Triggers automáticos**: Para mantener timestamps actualizados
- **Separación de datos**: Estadísticas separadas de configuración

### 5. **Escalabilidad**

- **Diseño modular**: Fácil agregar nuevas tablas sin afectar existentes
- **Relaciones claras**: Foreign keys mantienen integridad
- **Datos históricos**: Logs y estadísticas sin límite

## Casos de Uso

### 1. **Guardar una Nueva Cámara con Configuración Completa**

```sql
-- 1. Insertar cámara
INSERT INTO cameras (camera_id, brand, model, display_name, ip_address)
VALUES ('dahua_dh-ipc-hfw1230s_192168150', 'dahua', 'dh-ipc-hfw1230s', 'Cámara Entrada', '192.168.1.50');

-- 2. Insertar credenciales
INSERT INTO camera_credentials (camera_id, username, password_encrypted, is_default)
VALUES ('dahua_dh-ipc-hfw1230s_192168150', 'admin', 'encrypted_password', TRUE);

-- 3. Insertar protocolos
INSERT INTO camera_protocols (camera_id, protocol_type, port, is_primary)
VALUES 
  ('dahua_dh-ipc-hfw1230s_192168150', 'ONVIF', 80, TRUE),
  ('dahua_dh-ipc-hfw1230s_192168150', 'RTSP', 554, FALSE);

-- 4. Insertar endpoints descubiertos
INSERT INTO camera_endpoints (camera_id, endpoint_type, url, is_verified)
VALUES 
  ('dahua_dh-ipc-hfw1230s_192168150', 'rtsp_main', 
   'rtsp://admin:password@192.168.1.50:554/cam/realmonitor?channel=1&subtype=0', TRUE),
  ('dahua_dh-ipc-hfw1230s_192168150', 'snapshot', 
   'http://192.168.1.50/cgi-bin/snapshot.cgi', TRUE);
```

### 2. **Recuperar Configuración Completa para Conectar**

```sql
SELECT 
  c.*, 
  cc.username, 
  cc.password_encrypted,
  cp.protocol_type,
  cp.port,
  ce.url,
  ce.endpoint_type
FROM cameras c
LEFT JOIN camera_credentials cc ON c.camera_id = cc.camera_id AND cc.is_default = TRUE
LEFT JOIN camera_protocols cp ON c.camera_id = cp.camera_id AND cp.is_primary = TRUE
LEFT JOIN camera_endpoints ce ON c.camera_id = ce.camera_id AND ce.is_verified = TRUE
WHERE c.camera_id = 'dahua_dh-ipc-hfw1230s_192168150';
```

### 3. **Actualizar Estadísticas después de Conexión**

```sql
-- Actualizar estadísticas
UPDATE camera_statistics 
SET 
  total_connections = total_connections + 1,
  successful_connections = successful_connections + 1,
  last_connection_at = CURRENT_TIMESTAMP
WHERE camera_id = 'dahua_dh-ipc-hfw1230s_192168150';

-- Insertar log de conexión
INSERT INTO connection_logs (camera_id, protocol_used, endpoint_used, status, duration_ms)
VALUES ('dahua_dh-ipc-hfw1230s_192168150', 'RTSP', 'rtsp://...', 'success', 250);
```

## Migración desde Estructura Anterior

Para migrar desde la estructura anterior, se necesitará:

1. **Migrar tabla cameras**: Dividir campos en nuevas tablas
2. **Extraer protocolos**: Del campo JSON a tabla normalizada
3. **Crear registros de credenciales**: Con valores por defecto
4. **Generar estadísticas iniciales**: Desde contadores existentes

La migración se puede hacer gradualmente manteniendo compatibilidad hacia atrás.
