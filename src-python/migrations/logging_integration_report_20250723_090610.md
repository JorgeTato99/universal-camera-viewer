# Reporte de Integración de Logging Seguro

**Fecha**: 2025-07-23 09:06:10
**Modo**: APLICADO

## Resumen

- Archivos analizados: 27
- Archivos que requieren sanitización manual: 3

## Cambios por Archivo

### services\camera_manager_service.py

**Imports actualizados**:
- `import logging`

---

### services\config_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `ConfigService`

---

### services\connection_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\create_database.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\data_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `DataService`

---

### services\encryption_service.py

**Imports actualizados**:
- `import logging`

---

### services\encryption_service_v2.py

**Imports actualizados**:
- `import logging`

**⚠️ Logs sensibles detectados**:
- Token en log

---

### services\mediamtx_metrics_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\protocol_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `self.__class__.__name__`

---

### services\scan_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\theme_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\websocket_stream_service.py

**Imports actualizados**:
- `import logging`

**⚠️ Logs sensibles detectados**:
- password en log
- Password en f-string

---

### services\database\mediamtx_db_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\database\publishing_db_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\protocol_handlers\amcrest_handler.py

**Imports actualizados**:
- `import logging`

---

### services\protocol_handlers\base_handler.py

**Imports actualizados**:
- `import logging`

---

### services\protocol_handlers\onvif_handler.py

**Imports actualizados**:
- `import logging`

**⚠️ Logs sensibles detectados**:
- password en log
- Token en log
- Password en f-string

---

### services\protocol_handlers\rtsp_handler.py

**Imports actualizados**:
- `import logging`

---

### services\publishing\ffmpeg_manager.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `self.__class__.__name__`

---

### services\publishing\mediamtx_client.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `self.__class__.__name__`

---

### services\publishing\mediamtx_paths_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`
- `self.__class__.__name__`

---

### services\publishing\rtsp_publisher_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `self.__class__.__name__`

---

### services\publishing\rtsp_publisher_service_backup.py

**Imports actualizados**:
- `import logging`

---

### services\publishing\viewer_analytics_service.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`
- `self.__class__.__name__`

---

### services\video\frame_processor.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\video\stream_manager.py

**Imports actualizados**:
- `import logging`

**Loggers actualizados**:
- `__name__`

---

### services\video\video_stream_service.py

**Imports actualizados**:
- `import logging`

---

