# 🌐 Protocolos de Cámara

## 📋 Protocolos Soportados

El sistema soporta **4 marcas** de cámaras con **3 protocolos principales**:

| Protocolo | Descripción | Puerto | Uso |
|-----------|-------------|--------|-----|
| **ONVIF** | Estándar industrial IP | 80, 8080 | Universal |
| **RTSP** | Real Time Streaming Protocol | 554 | Streaming directo |
| **HTTP/CGI** | APIs REST personalizadas | 80, 8080 | Marcas específicas |

## 🏷️ Configuración por Marca

### **🔵 Dahua Cameras**

```python
# Configuración Dahua
DAHUA_CONFIG = {
    "primary_protocol": "onvif",
    "secondary_protocol": "http_cgi",
    "default_ports": [80, 554, 8080],
    "auth_method": "digest",
    "stream_formats": ["h264", "mjpeg"]
}
```

**Endpoints de API:**

```bash
# Stream principal
http://{ip}/cam/realmonitor?channel=1&subtype=0

# Información del dispositivo  
http://{ip}/cgi-bin/magicBox.cgi?action=getDeviceInfo

# PTZ Control
http://{ip}/cgi-bin/ptz.cgi?action=start&channel=0&code=Up
```

### **🟠 TP-Link Cameras**

```python
# Configuración TP-Link
TPLINK_CONFIG = {
    "primary_protocol": "onvif", 
    "secondary_protocol": "rtsp",
    "default_ports": [554, 8080, 80],
    "auth_method": "basic",
    "stream_formats": ["h264"]
}
```

**URLs de Stream:**

```bash
# RTSP Stream
rtsp://{username}:{password}@{ip}:554/stream1

# HTTP Stream
http://{ip}:8080/stream/0?username={user}&password={pass}
```

### **🟡 Steren Cameras**

```python
# Configuración Steren
STEREN_CONFIG = {
    "primary_protocol": "http_cgi",
    "secondary_protocol": "onvif", 
    "default_ports": [80, 8080],
    "auth_method": "basic",
    "stream_formats": ["mjpeg", "h264"]
}
```

**API Endpoints:**

```bash
# Stream de video
http://{ip}/cgi-bin/mjpg/video.cgi?channel=0

# Snapshot
http://{ip}/cgi-bin/snapshot.cgi?channel=0

# Estado del dispositivo
http://{ip}/cgi-bin/hi3510/param.cgi?cmd=getserverinfo
```

### **⚫ Generic ONVIF**

```python
# Configuración Genérica
GENERIC_CONFIG = {
    "primary_protocol": "onvif",
    "secondary_protocol": "rtsp",
    "default_ports": [80, 554, 8080, 8899],
    "auth_method": "auto_detect",
    "stream_formats": ["h264", "mjpeg", "h265"]
}
```

## 🔧 Implementación de Protocolos

### **ONVIF Protocol Handler**

```python
# src/services/protocol_service.py
class ONVIFHandler:
    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username  
        self.password = password
        self.client = None
        
    async def connect(self) -> bool:
        """Establece conexión ONVIF"""
        try:
            from onvif import ONVIFCamera
            self.client = ONVIFCamera(
                self.ip, 80, 
                self.username, self.password
            )
            # Verificar servicios disponibles
            services = self.client.devicemgmt.GetServices()
            return len(services) > 0
        except Exception as e:
            logger.error(f"ONVIF connection failed: {e}")
            return False
            
    async def get_stream_uri(self) -> str:
        """Obtiene URI del stream principal"""
        media_service = self.client.create_media_service()
        profiles = media_service.GetProfiles()
        
        if profiles:
            stream_setup = media_service.create_type('GetStreamUri')
            stream_setup.ProfileToken = profiles[0].token
            stream_setup.StreamSetup = {
                'Stream': 'RTP-Unicast',
                'Transport': {'Protocol': 'RTSP'}
            }
            return media_service.GetStreamUri(stream_setup).Uri
        return None
```

### **RTSP Stream Handler**

```python
class RTSPHandler:
    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.cap = None
        
    async def connect(self) -> bool:
        """Conecta al stream RTSP"""
        import cv2
        self.cap = cv2.VideoCapture(self.stream_url)
        return self.cap.isOpened()
        
    async def get_frame(self) -> np.ndarray:
        """Captura frame actual"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            return frame if ret else None
        return None
        
    def disconnect(self):
        """Cierra conexión"""
        if self.cap:
            self.cap.release()
```

### **HTTP/CGI Handler**

```python
class HTTPCGIHandler:
    def __init__(self, ip: str, brand: str, credentials: dict):
        self.ip = ip
        self.brand = brand
        self.session = requests.Session()
        self.session.auth = (
            credentials['username'], 
            credentials['password']
        )
        
    async def get_snapshot(self) -> bytes:
        """Captura snapshot via HTTP"""
        endpoints = {
            'steren': f'http://{self.ip}/cgi-bin/snapshot.cgi',
            'dahua': f'http://{self.ip}/cgi-bin/snapshot.cgi?channel=0'
        }
        
        url = endpoints.get(self.brand)
        if url:
            response = self.session.get(url, timeout=10)
            return response.content if response.status_code == 200 else None
        return None
        
    async def get_device_info(self) -> dict:
        """Obtiene información del dispositivo"""
        endpoints = {
            'steren': f'http://{self.ip}/cgi-bin/hi3510/param.cgi?cmd=getserverinfo',
            'dahua': f'http://{self.ip}/cgi-bin/magicBox.cgi?action=getDeviceInfo'
        }
        
        url = endpoints.get(self.brand)
        if url:
            response = self.session.get(url, timeout=5)
            return self._parse_device_info(response.text)
        return {}
```

## 🔍 Auto-detección de Protocolos

### **Protocol Detection Algorithm**

```python
class ProtocolDetector:
    def __init__(self, ip: str):
        self.ip = ip
        self.detection_results = {}
        
    async def detect_all_protocols(self) -> dict:
        """Detecta todos los protocolos disponibles"""
        tasks = [
            self._test_onvif(),
            self._test_rtsp(),
            self._test_http_cgi()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'onvif': results[0] if not isinstance(results[0], Exception) else False,
            'rtsp': results[1] if not isinstance(results[1], Exception) else False, 
            'http_cgi': results[2] if not isinstance(results[2], Exception) else False
        }
        
    async def _test_onvif(self) -> bool:
        """Test ONVIF availability"""
        ports_to_test = [80, 8080, 8899]
        for port in ports_to_test:
            try:
                # Test ONVIF SOAP endpoint
                url = f"http://{self.ip}:{port}/onvif/device_service"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=3) as response:
                        if response.status in [200, 400, 401]:  # 401 = auth required
                            return True
            except:
                continue
        return False
        
    async def _test_rtsp(self) -> bool:
        """Test RTSP availability"""
        try:
            # Test RTSP port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, 554), timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
            
    async def _test_http_cgi(self) -> bool:
        """Test HTTP/CGI endpoints"""
        common_endpoints = [
            "/cgi-bin/snapshot.cgi",
            "/cgi-bin/mjpg/video.cgi", 
            "/cam/realmonitor"
        ]
        
        for endpoint in common_endpoints:
            try:
                url = f"http://{self.ip}{endpoint}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=2) as response:
                        if response.status in [200, 401]:
                            return True
            except:
                continue
        return False
```

## 📊 Métricas de Conexión

### **Connection Quality Monitor**

```python
class ConnectionQualityMonitor:
    def __init__(self):
        self.metrics = {}
        
    def measure_connection_quality(self, ip: str, protocol: str) -> dict:
        """Mide calidad de conexión"""
        start_time = time.time()
        
        # Test de latencia
        latency = self._ping_test(ip)
        
        # Test de ancho de banda
        bandwidth = self._bandwidth_test(ip, protocol)
        
        # Estabilidad de conexión
        stability = self._stability_test(ip, protocol)
        
        return {
            'latency_ms': latency,
            'bandwidth_mbps': bandwidth,
            'stability_score': stability,
            'overall_score': self._calculate_overall_score(latency, bandwidth, stability)
        }
        
    def _ping_test(self, ip: str) -> float:
        """Test de latencia simple"""
        import subprocess
        try:
            result = subprocess.run(
                ['ping', '-n', '1', ip], 
                capture_output=True, text=True, timeout=5
            )
            # Parsear tiempo de respuesta
            # Implementación específica del OS
            return 0.0  # Placeholder
        except:
            return 999.0
```

## 🚨 Diagnósticos y Troubleshooting

### **Comandos de Diagnóstico**

```bash
# Diagnóstico completo de red
make network-test

# Test específico de cámara
python examples/diagnostics/camera_detector.py --ip 192.168.1.100

# Test de protocolos
python examples/testing/protocol_comparison.py
```

### **Problemas Comunes**

#### **Error: ONVIF Authentication Failed**

```python
# Solución: Verificar credenciales y método de auth
auth_methods = ['digest', 'basic', 'none']
for method in auth_methods:
    try:
        camera = ONVIFCamera(ip, port, user, pass, auth_method=method)
        # Test connection
        break
    except AuthenticationError:
        continue
```

#### **Error: RTSP Stream Timeout**

```python
# Solución: Ajustar timeouts y buffer size
cv2.CAP_PROP_BUFFERSIZE = 1  # Reduce buffer lag
cv2.CAP_PROP_FPS = 15        # Limit FPS
```

#### **Error: HTTP/CGI 404 Not Found**

```python
# Solución: Auto-detectar endpoints válidos
common_endpoints = [
    '/cgi-bin/snapshot.cgi',
    '/tmpfs/auto.jpg', 
    '/axis-cgi/jpg/image.cgi'
]
```

## 🎯 Próximos Pasos

1. **[📦 Instalación](installation.md)** - Setup inicial del proyecto
2. **[🏛️ Arquitectura](architecture.md)** - Entender la estructura MVP
3. **[📡 Services API](api-services.md)** - Documentación de servicios

---

**🌐 Protocolos:** ONVIF, RTSP, HTTP/CGI con auto-detección  
**🏷️ Marcas:** Dahua, TP-Link, Steren, Generic con configuraciones optimizadas  
**🔍 Detección:** Automática de protocolos disponibles por marca

---

### 📚 Navegación

[← Anterior: Compatibilidad de Cámaras](CAMERA_COMPATIBILITY.md) | [📑 Índice](README.md) | [Siguiente: API y Servicios →](api-services.md)
