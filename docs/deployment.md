# 📦 Deployment y Distribución

> Guía para despliegue en producción del sistema de videovigilancia

## 🎯 Arquitectura de Deployment

El sistema consta de dos componentes principales:

1. **Backend FastAPI** - Servidor Python con API REST y WebSocket
2. **Frontend React** - Aplicación web estática

## 🐳 Docker Deployment (Recomendado)

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: 
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
    restart: unless-stopped
    
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### Dockerfile Backend

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src-python/ ./src-python/
COPY run_api.py .

# Crear directorio de datos
RUN mkdir -p data

# Puerto
EXPOSE 8000

# Comando
CMD ["python", "run_api.py"]
```

### Dockerfile Frontend

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar package files
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copiar código y build
COPY src/ ./src/
COPY public/ ./public/
COPY index.html vite.config.ts tsconfig*.json ./
RUN yarn build

# Nginx para servir
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy para API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🖥️ Deployment Manual

### Backend en Servidor Linux

```bash
# 1. Clonar repositorio
git clone https://github.com/JorgeTato99/universal-camera-viewer.git
cd universal-camera-viewer

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos
python src-python/seed_database.py --clear

# 5. Configurar systemd service
sudo nano /etc/systemd/system/camera-viewer.service
```

#### Systemd Service

```ini
[Unit]
Description=Universal Camera Viewer API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/universal-camera-viewer
Environment="PATH=/opt/universal-camera-viewer/venv/bin"
ExecStart=/opt/universal-camera-viewer/venv/bin/python run_api.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y arrancar
sudo systemctl enable camera-viewer
sudo systemctl start camera-viewer
```

### Frontend con Nginx

```bash
# 1. Build del frontend
yarn install
yarn build

# 2. Copiar a nginx
sudo cp -r dist/* /var/www/camera-viewer/

# 3. Configurar nginx
sudo nano /etc/nginx/sites-available/camera-viewer
```

## 🚀 PM2 Deployment

### Instalación PM2

```bash
npm install -g pm2
```

### Configuración PM2

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'camera-viewer-api',
    script: 'python',
    args: 'run_api.py',
    cwd: '/opt/universal-camera-viewer',
    interpreter: '/opt/universal-camera-viewer/venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      APP_ENV: 'production',
      LOG_LEVEL: 'INFO'
    }
  }]
}
```

```bash
# Iniciar con PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## ☁️ Cloud Deployment

### AWS EC2

```bash
# 1. Lanzar instancia Ubuntu 22.04
# 2. Configurar Security Groups
#    - Puerto 80 (HTTP)
#    - Puerto 443 (HTTPS)
#    - Puerto 8000 (API) - solo interno

# 3. Instalar dependencias
sudo apt update
sudo apt install python3-pip python3-venv nginx certbot

# 4. Configurar SSL con Let's Encrypt
sudo certbot --nginx -d tu-dominio.com
```

### DigitalOcean App Platform

```yaml
# app.yaml
name: universal-camera-viewer
services:
  - name: api
    github:
      repo: JorgeTato99/universal-camera-viewer
      branch: main
    build_command: pip install -r requirements.txt
    run_command: python run_api.py
    http_port: 8000
    
  - name: frontend
    github:
      repo: JorgeTato99/universal-camera-viewer
      branch: main
    build_command: yarn install && yarn build
    static_sites:
      - path: /
        source_dir: dist
```

## 🔧 Variables de Entorno

### Producción (.env.production)

```bash
# API
APP_ENV=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///data/camera_data.db

# Security
ENCRYPTION_KEY_PATH=/secure/path/.encryption_key

# CORS
CORS_ORIGINS=https://tu-dominio.com

# Limits
MAX_CONCURRENT_STREAMS=10
MAX_UPLOAD_SIZE=10485760
```

## 📊 Monitoreo

### Prometheus Metrics

```python
# src-python/api/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

camera_connections = Counter('camera_connections_total', 
                           'Total camera connections',
                           ['camera_id', 'status'])
                           
stream_duration = Histogram('stream_duration_seconds',
                          'Stream duration in seconds',
                          ['camera_id'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "database": check_db_connection(),
        "active_streams": video_stream_service.get_active_count()
    }
```

## 🔒 Seguridad en Producción

### Checklist de Seguridad

- [ ] HTTPS habilitado con certificado válido
- [ ] Firewall configurado (solo puertos necesarios)
- [ ] Rate limiting implementado
- [ ] CORS configurado correctamente
- [ ] Secrets en variables de entorno
- [ ] Base de datos con backups automáticos
- [ ] Logs centralizados
- [ ] Monitoreo de errores (Sentry)

### Nginx Security Headers

```nginx
# Agregar a nginx.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' ws: wss:; img-src 'self' data:; style-src 'self' 'unsafe-inline';" always;
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/
          
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/universal-camera-viewer
            git pull
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart camera-viewer
```

## 📈 Escalabilidad

### Arquitectura para Alta Disponibilidad

```bash
                    ┌─────────────┐
                    │ Load Balancer│
                    └──────┬──────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
       ┌────▼────┐                  ┌────▼────┐
       │ API Node 1│                │ API Node 2│
       └────┬────┘                  └────┬────┘
            │                             │
            └──────────┬─────────────────┘
                       │
                  ┌────▼────┐
                  │ Database │
                  │ (Primary)│
                  └─────────┘
```

### Consideraciones

1. **Base de datos**: Migrar a PostgreSQL para múltiples nodos
2. **Archivos**: Usar S3 o almacenamiento compartido
3. **WebSocket**: Configurar sticky sessions en load balancer
4. **Cache**: Implementar Redis para sesiones compartidas

## 🎯 Performance Tuning

### Optimizaciones Python

```python
# Usar uvloop para mejor performance
import uvloop
uvloop.install()

# Configurar workers
uvicorn.run(
    "api.main:app",
    host="0.0.0.0",
    port=8000,
    workers=4,  # CPU cores
    loop="uvloop"
)
```

### Optimizaciones Nginx

```nginx
# Ajustes de performance
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript;
}
```

---

**Última actualización**: v0.9.5 - Julio 2025
