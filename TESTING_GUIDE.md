# 🧪 Guía de Pruebas del Backend

Esta guía explica cómo probar que el backend funcione correctamente con la nueva estructura de base de datos 3FN.

## 📋 Prerrequisitos

1. **Base de datos creada y poblada**:
   ```bash
   # Crear base de datos
   python src-python/services/create_database.py
   
   # Poblar con datos de prueba
   python src-python/seed_database.py
   ```

2. **Dependencias instaladas**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Pasos para Probar el Backend

### 1. Iniciar el Servidor API

```bash
# Opción 1: Script de inicio
python run_api.py

# Opción 2: Comando directo
cd src-python
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:
```
[STARTING] Universal Camera Viewer API v2.0.0
[SERVER] http://0.0.0.0:8000
[DOCS] http://0.0.0.0:8000/docs
[RELOAD] Enabled
```

### 2. Verificar que el Servidor Responde

Abre tu navegador y visita:
- **API Root**: http://localhost:8000/
- **Documentación Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Ejecutar Script de Pruebas Completo

En otra terminal, ejecuta:

```bash
python test_backend_complete.py
```

Este script probará:
- ✅ Endpoints API
- ✅ WebSocket para streaming
- ✅ Operaciones de base de datos

### 4. Pruebas Manuales con Swagger

Ve a http://localhost:8000/docs y prueba:

#### 📷 Endpoints de Cámaras

1. **GET /api/cameras** - Lista todas las cámaras
   - Debería mostrar las 6 cámaras SEED
   - Cada cámara tiene id, nombre, IP, estado, etc.

2. **GET /api/cameras/{camera_id}** - Obtener cámara específica
   - Usa un ID de la lista anterior
   - Muestra información detallada

3. **POST /api/cameras/connect** - Conectar a una cámara
   ```json
   {
     "camera_id": "d8df1ba2-8400-42a6-b489-b20b5f6c741a",
     "username": "admin",
     "password": "admin123"
   }
   ```

#### 🆕 API v2 (Nueva Estructura 3FN)

1. **GET /api/v2/cameras** - Lista cámaras desde DB
   - Datos reales de la base de datos
   - Incluye configuración completa

2. **POST /api/v2/cameras** - Crear nueva cámara
   ```json
   {
     "brand": "hikvision",
     "model": "DS-2CD2043G2-I",
     "display_name": "Cámara de Prueba",
     "ip": "192.168.1.200",
     "username": "admin",
     "password": "admin123",
     "rtsp_port": 554,
     "onvif_port": 80
   }
   ```

3. **GET /api/v2/cameras/{camera_id}/full** - Configuración completa
   - Muestra todas las relaciones 3FN
   - Credenciales, protocolos, endpoints, estadísticas

#### 🔍 Scanner de Red

1. **POST /api/scanner/scan** - Iniciar escaneo
   ```json
   {
     "network_range": "192.168.1.0/24",
     "start_ip": 100,
     "end_ip": 110,
     "scan_common_ports": true
   }
   ```

2. **GET /api/scanner/status** - Estado del escaneo

### 5. Probar WebSocket Streaming

1. Usa una herramienta como [WebSocket King](https://websocketking.com/) o similar

2. Conecta a:
   ```
   ws://localhost:8000/ws/stream/test_camera_id
   ```

3. Envía mensaje de inicio:
   ```json
   {
     "action": "start_stream",
     "params": {
       "quality": "medium",
       "fps": 30
     }
   }
   ```

4. Deberías recibir frames en formato:
   ```json
   {
     "type": "frame",
     "camera_id": "test_camera_id",
     "data": "base64_encoded_jpeg",
     "timestamp": "2025-01-15T10:30:00.123Z",
     "frame_number": 1
   }
   ```

## 🔍 Verificar la Base de Datos

### Con SQLite Browser

1. Instala [DB Browser for SQLite](https://sqlitebrowser.org/)
2. Abre `data/camera_data.db`
3. Verifica las tablas:
   - `cameras` - 6+ registros
   - `camera_credentials` - Credenciales encriptadas
   - `camera_protocols` - Protocolos configurados
   - `camera_endpoints` - URLs de streaming
   - `camera_statistics` - Métricas

### Con Script Python

```python
# Verificar datos directamente
python src-python/test_db_integration.py
```

## 📊 Métricas de Éxito

El backend funciona correctamente si:

1. **API responde** en http://localhost:8000/docs
2. **Lista cámaras** muestra 6+ registros
3. **WebSocket** conecta y envía frames
4. **Base de datos** tiene todas las tablas creadas
5. **No hay errores** en los logs del servidor

## 🐛 Solución de Problemas

### Error: "No module named 'api'"
```bash
# Asegúrate de estar en el directorio correcto
cd D:\universal-camera-viewer
python run_api.py
```

### Error: "No such table: cameras"
```bash
# Recrear base de datos
python src-python/services/create_database.py
python src-python/seed_database.py
```

### Error: "Address already in use"
```bash
# Matar proceso en puerto 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### WebSocket no conecta
- Verifica que el servidor esté corriendo
- Revisa que no haya firewall bloqueando
- Usa `ws://` no `wss://` para desarrollo local

## 🎯 Próximos Pasos

Si todas las pruebas pasan:

1. **Configurar cámaras reales**: Actualiza credenciales en la DB
2. **Probar streaming real**: Conecta a cámaras físicas
3. **Ejecutar frontend**: `yarn dev` para UI completa
4. **Monitorear rendimiento**: Revisa métricas en `/api/stats`

---

💡 **Tip**: Mantén el servidor corriendo con `--reload` durante desarrollo para ver cambios automáticamente.