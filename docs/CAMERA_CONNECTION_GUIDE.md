# Guía de Conexión de Cámaras

## Conexión con Cámaras Dahua

### Configuración Requerida

1. **Habilitar ONVIF en la cámara**:
   - Acceder a la interfaz web de la cámara
   - Ir a Configuración → Red → Integración → ONVIF
   - Habilitar ONVIF
   - Crear usuario ONVIF si es necesario

2. **Puertos comunes**:
   - **ONVIF**: 80 (por defecto), también puede ser 8000 o 8080
   - **RTSP**: 554 (estándar)
   - **HTTP**: 80

3. **URLs RTSP para Dahua**:
   ```
   # Stream principal (HD)
   rtsp://usuario:contraseña@IP:554/cam/realmonitor?channel=1&subtype=0
   
   # Stream secundario (SD)
   rtsp://usuario:contraseña@IP:554/cam/realmonitor?channel=1&subtype=1
   ```

### Solución de Problemas

#### Error: "Sender not Authorized"
- Verificar que las credenciales sean correctas
- Confirmar que ONVIF esté habilitado
- Verificar el puerto ONVIF (probar 80, 8000, 8080)
- Asegurarse de que el usuario tenga permisos ONVIF

#### No se puede conectar
1. Verificar conectividad de red:
   ```bash
   ping IP_DE_LA_CAMARA
   ```

2. Verificar puertos abiertos:
   ```bash
   # Windows
   Test-NetConnection -ComputerName IP_DE_LA_CAMARA -Port 554
   
   # Linux/Mac
   nc -zv IP_DE_LA_CAMARA 554
   ```

3. Probar conexión RTSP directa:
   ```bash
   python tests/test_rtsp_direct.py
   ```

## Pruebas de Conexión

### Script de Prueba Completo
```bash
# Prueba interactiva con ONVIF y RTSP
python tests/test_camera_connection.py
```

### Script de Prueba RTSP Directa
```bash
# Prueba rápida solo RTSP
python tests/test_rtsp_direct.py
```

## Marcas Soportadas

### Dahua
- **Puerto ONVIF**: 80
- **Puerto RTSP**: 554
- **URL Principal**: `/cam/realmonitor?channel=1&subtype=0`
- **URL Secundaria**: `/cam/realmonitor?channel=1&subtype=1`

### TP-Link (Tapo)
- **Puerto ONVIF**: 2020
- **Puerto RTSP**: 554
- **URL**: `/stream1` o `/stream2`

### Hikvision
- **Puerto ONVIF**: 80
- **Puerto RTSP**: 554
- **URL Principal**: `/Streaming/Channels/101`
- **URL Secundaria**: `/Streaming/Channels/102`

### Steren
- **Puerto ONVIF**: 8000
- **Puerto RTSP**: 5543
- **URL**: Varía según modelo

## Configuración en la Aplicación

1. **Agregar cámara**:
   - IP: Dirección IP de la cámara
   - Usuario: Usuario con permisos ONVIF/RTSP
   - Contraseña: Contraseña del usuario
   - Marca: Seleccionar marca para configuración automática

2. **Verificar conexión**:
   - La aplicación intentará conectar por ONVIF primero
   - Si ONVIF falla, intentará RTSP directo
   - Los logs mostrarán el progreso de conexión

3. **Streaming**:
   - Una vez conectada, el video se mostrará automáticamente
   - FPS objetivo: 13-20 según la red
   - Resolución: Se ajusta automáticamente

## Logs y Depuración

Los logs de conexión se encuentran en:
- Frontend: Consola del navegador (F12)
- Backend: Terminal donde se ejecuta el servidor Python

Para más detalles de depuración, configurar el nivel de log:
```python
# En src-python/main.py
logging.basicConfig(level=logging.DEBUG)
```