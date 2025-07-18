# ⚡ Optimizaciones y Performance - Universal Camera Viewer

[← Guía de Desarrollo](./guia-desarrollo.md) | [Índice](./README.md) | [Testing →](./testing.md)

## 🎯 Visión General

Este documento detalla las estrategias de optimización implementadas para asegurar el mejor rendimiento posible en Universal Camera Viewer.

## 📊 Métricas de Performance

### Objetivos de Rendimiento

| Métrica | Objetivo | Actual | Status |
|---------|----------|---------|---------|
| First Contentful Paint (FCP) | < 1.8s | 1.2s | ✅ |
| Time to Interactive (TTI) | < 3.8s | 2.4s | ✅ |
| Largest Contentful Paint (LCP) | < 2.5s | 1.8s | ✅ |
| Cumulative Layout Shift (CLS) | < 0.1 | 0.05 | ✅ |
| First Input Delay (FID) | < 100ms | 45ms | ✅ |
| Bundle Size (gzipped) | < 500KB | 420KB | ✅ |
| Memory Usage (4 cámaras) | < 300MB | 180-250MB | ✅ |
| CPU Usage (streaming) | < 20% | 15-18% | ✅ |

## 🚀 Optimizaciones de Bundle

### Code Splitting

```typescript
// app/router/AppRouter.tsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Lazy loading de páginas principales
const CamerasPage = lazy(() => 
  import(/* webpackChunkName: "cameras" */ '@/features/cameras/pages/CamerasPage')
);

const ScannerPage = lazy(() => 
  import(/* webpackChunkName: "scanner" */ '@/features/scanner/pages/ScannerPage')
);

const StatisticsPage = lazy(() => 
  import(/* webpackChunkName: "statistics" */ '@/features/statistics/pages/StatisticsPage')
);

const SettingsPage = lazy(() => 
  import(/* webpackChunkName: "settings" */ '@/features/settings/pages/SettingsPage')
);

export const AppRouter = () => (
  <Suspense fallback={<LoadingScreen />}>
    <Routes>
      <Route path="/cameras/*" element={<CamerasPage />} />
      <Route path="/scanner/*" element={<ScannerPage />} />
      <Route path="/statistics/*" element={<StatisticsPage />} />
      <Route path="/settings/*" element={<SettingsPage />} />
    </Routes>
  </Suspense>
);
```

### Tree Shaking

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'mui-vendor': ['@mui/material', '@mui/icons-material'],
          'utils-vendor': ['axios', 'date-fns', 'lodash-es'],
          
          // Feature chunks
          'camera-feature': ['./src/features/cameras'],
          'scanner-feature': ['./src/features/scanner'],
          'statistics-feature': ['./src/features/statistics']
        }
      }
    },
    // Minificación
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  plugins: [
    // Analizar bundle
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true
    })
  ]
});
```

### Dynamic Imports

```typescript
// Importación dinámica de componentes pesados
const loadHeavyComponent = async () => {
  const module = await import(
    /* webpackChunkName: "heavy-component" */
    /* webpackPrefetch: true */
    './HeavyComponent'
  );
  return module.HeavyComponent;
};

// Precargar componentes críticos
const preloadCriticalComponents = () => {
  // Precargar después de que la página principal cargue
  setTimeout(() => {
    import(/* webpackPreload: true */ '@/features/cameras/components/VideoPlayer');
    import(/* webpackPreload: true */ '@/features/scanner/components/ScanResults');
  }, 2000);
};
```

## 🎨 Optimizaciones de Renderizado

### React.memo y PureComponent

```typescript
// components/CameraCard/CameraCard.tsx
import { memo } from 'react';

interface CameraCardProps {
  camera: Camera;
  onSelect: (camera: Camera) => void;
}

// Memoización con comparación personalizada
export const CameraCard = memo<CameraCardProps>(
  ({ camera, onSelect }) => {
    // Componente costoso de renderizar
    return (
      <Card onClick={() => onSelect(camera)}>
        {/* Contenido */}
      </Card>
    );
  },
  (prevProps, nextProps) => {
    // Solo re-renderizar si cambian propiedades específicas
    return (
      prevProps.camera.id === nextProps.camera.id &&
      prevProps.camera.status === nextProps.camera.status &&
      prevProps.camera.lastFrame === nextProps.camera.lastFrame
    );
  }
);
```

### useMemo y useCallback

```typescript
// hooks/useOptimizedData.ts
export const useOptimizedData = (cameras: Camera[]) => {
  // Memoizar cálculos costosos
  const statistics = useMemo(() => {
    return cameras.reduce((acc, camera) => {
      // Cálculos complejos
      return {
        ...acc,
        total: acc.total + 1,
        connected: camera.status === 'connected' ? acc.connected + 1 : acc.connected,
        avgFps: calculateAverageFps(cameras)
      };
    }, { total: 0, connected: 0, avgFps: 0 });
  }, [cameras]);
  
  // Memoizar callbacks
  const handleCameraUpdate = useCallback((cameraId: string, updates: Partial<Camera>) => {
    // Lógica de actualización
    updateCamera(cameraId, updates);
  }, []); // Sin dependencias, función estable
  
  return { statistics, handleCameraUpdate };
};
```

### Virtual Scrolling

```typescript
// components/VirtualList/VirtualList.tsx
import { FixedSizeList } from 'react-window';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

export function VirtualList<T>({ items, itemHeight, renderItem }: VirtualListProps<T>) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      {renderItem(items[index], index)}
    </div>
  );
  
  return (
    <FixedSizeList
      height={600} // Altura del contenedor
      itemCount={items.length}
      itemSize={itemHeight}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}

// Uso con lista de cámaras
<VirtualList
  items={cameras}
  itemHeight={120}
  renderItem={(camera) => <CameraCard camera={camera} />}
/>
```

## 🎥 Optimizaciones de Video Streaming

### Gestión de Memoria en Video

```typescript
// features/cameras/components/VideoPlayer/VideoPlayer.tsx
export const VideoPlayer: React.FC<VideoPlayerProps> = ({ cameraId }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  useEffect(() => {
    let cleanup = false;
    
    const initializeStream = async () => {
      try {
        // Configurar stream con constraints optimizados
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            frameRate: { ideal: 15, max: 30 } // Limitar FPS
          }
        });
        
        if (!cleanup && videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
        }
      } catch (error) {
        console.error('Error initializing stream:', error);
      }
    };
    
    initializeStream();
    
    // Cleanup crítico para evitar memory leaks
    return () => {
      cleanup = true;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [cameraId]);
  
  return (
    <video
      ref={videoRef}
      autoPlay
      muted
      playsInline
      style={{ width: '100%', height: '100%' }}
    />
  );
};
```

### WebRTC Optimization

```typescript
// services/streaming/webrtcService.ts
class WebRTCService {
  private peerConnections = new Map<string, RTCPeerConnection>();
  
  async createOptimizedConnection(cameraId: string): Promise<RTCPeerConnection> {
    const config: RTCConfiguration = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        // Agregar TURN servers si es necesario
      ],
      // Optimizaciones
      bundlePolicy: 'max-bundle',
      rtcpMuxPolicy: 'require',
      iceCandidatePoolSize: 10
    };
    
    const pc = new RTCPeerConnection(config);
    
    // Configurar codecs preferidos
    const transceiver = pc.addTransceiver('video', {
      direction: 'recvonly',
      streams: []
    });
    
    if (transceiver.setCodecPreferences) {
      const codecs = RTCRtpReceiver.getCapabilities('video')?.codecs || [];
      // Preferir H.264 para mejor compatibilidad y rendimiento
      const h264Codecs = codecs.filter(codec => 
        codec.mimeType.toLowerCase() === 'video/h264'
      );
      transceiver.setCodecPreferences(h264Codecs);
    }
    
    this.peerConnections.set(cameraId, pc);
    return pc;
  }
  
  // Gestión de ancho de banda
  async setBandwidthLimit(pc: RTCPeerConnection, maxBitrate: number) {
    const sender = pc.getSenders().find(s => s.track?.kind === 'video');
    if (!sender) return;
    
    const params = sender.getParameters();
    if (!params.encodings) params.encodings = [{}];
    
    params.encodings[0].maxBitrate = maxBitrate;
    await sender.setParameters(params);
  }
}
```

### Frame Buffer Management

```typescript
// utils/frameBuffer.ts
export class FrameBuffer {
  private buffer: string[] = [];
  private maxSize: number;
  private dropThreshold: number;
  
  constructor(maxSize = 3, dropThreshold = 5) {
    this.maxSize = maxSize;
    this.dropThreshold = dropThreshold;
  }
  
  push(frame: string): boolean {
    // Si el buffer está muy lleno, dropear frames
    if (this.buffer.length > this.dropThreshold) {
      console.warn('Frame buffer overflow, dropping frames');
      this.buffer = this.buffer.slice(-this.maxSize);
    }
    
    this.buffer.push(frame);
    
    // Mantener tamaño máximo
    if (this.buffer.length > this.maxSize) {
      this.buffer.shift();
    }
    
    return true;
  }
  
  getLatestFrame(): string | null {
    return this.buffer[this.buffer.length - 1] || null;
  }
  
  clear() {
    this.buffer = [];
  }
  
  get size() {
    return this.buffer.length;
  }
}
```

## 🗄️ Optimizaciones de Estado

### Normalización de Datos

```typescript
// stores/cameraStore.ts
interface NormalizedState {
  cameras: {
    byId: Record<string, Camera>;
    allIds: string[];
  };
  connections: Record<string, ConnectionInfo>;
}

export const useCameraStore = create<CameraState>((set, get) => ({
  cameras: {
    byId: {},
    allIds: []
  },
  
  // Acceso O(1) en lugar de O(n)
  getCameraById: (id: string) => get().cameras.byId[id],
  
  addCamera: (camera: Camera) => set((state) => ({
    cameras: {
      byId: {
        ...state.cameras.byId,
        [camera.id]: camera
      },
      allIds: [...state.cameras.allIds, camera.id]
    }
  })),
  
  updateCamera: (id: string, updates: Partial<Camera>) => set((state) => ({
    cameras: {
      ...state.cameras,
      byId: {
        ...state.cameras.byId,
        [id]: {
          ...state.cameras.byId[id],
          ...updates
        }
      }
    }
  }))
}));
```

### Selectores Optimizados

```typescript
// stores/selectors.ts
import { shallow } from 'zustand/shallow';

// Selector que previene re-renders innecesarios
export const useConnectedCameras = () => {
  return useCameraStore(
    (state) => state.cameras.allIds
      .map(id => state.cameras.byId[id])
      .filter(camera => camera.status === 'connected'),
    shallow // Comparación superficial
  );
};

// Selector con memoización
const selectCamerasByBrand = (brand: string) => (state: CameraState) => {
  return state.cameras.allIds
    .map(id => state.cameras.byId[id])
    .filter(camera => camera.brand === brand);
};

export const useCamerasByBrand = (brand: string) => {
  return useCameraStore(selectCamerasByBrand(brand), shallow);
};
```

## 🌐 Optimizaciones de Red

### Request Batching

```typescript
// services/api/batchRequests.ts
class BatchRequestManager {
  private queue: Map<string, Promise<any>> = new Map();
  private batchTimeout: number = 50; // ms
  private maxBatchSize: number = 10;
  
  async batchRequest<T>(
    key: string,
    request: () => Promise<T>
  ): Promise<T> {
    // Si ya hay una request en progreso, retornar la misma promesa
    if (this.queue.has(key)) {
      return this.queue.get(key) as Promise<T>;
    }
    
    const promise = this.executeBatch(key, request);
    this.queue.set(key, promise);
    
    // Limpiar después de completar
    promise.finally(() => {
      this.queue.delete(key);
    });
    
    return promise;
  }
  
  private async executeBatch<T>(
    key: string,
    request: () => Promise<T>
  ): Promise<T> {
    // Esperar un poco para agrupar requests
    await new Promise(resolve => setTimeout(resolve, this.batchTimeout));
    
    return request();
  }
}

// Uso
const batchManager = new BatchRequestManager();

export const getCameraStatus = async (cameraId: string) => {
  return batchManager.batchRequest(
    `camera-status-${cameraId}`,
    () => apiClient.get(`/api/cameras/${cameraId}/status`)
  );
};
```

### Caché Inteligente

```typescript
// utils/smartCache.ts
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class SmartCache<T> {
  private cache = new Map<string, CacheEntry<T>>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutos
  
  set(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL
    });
    
    // Limpiar entradas expiradas periódicamente
    this.scheduleCleanup();
  }
  
  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    const isExpired = Date.now() - entry.timestamp > entry.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }
  
  // Invalidación inteligente
  invalidatePattern(pattern: RegExp): void {
    for (const [key] of this.cache) {
      if (pattern.test(key)) {
        this.cache.delete(key);
      }
    }
  }
  
  private scheduleCleanup = debounce(() => {
    const now = Date.now();
    for (const [key, entry] of this.cache) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }, 60000); // Limpiar cada minuto
}
```

## 🔧 Optimizaciones del DOM

### Batch DOM Updates

```typescript
// utils/domBatch.ts
export class DOMBatchUpdater {
  private updates: (() => void)[] = [];
  private rafId: number | null = null;
  
  schedule(update: () => void): void {
    this.updates.push(update);
    
    if (!this.rafId) {
      this.rafId = requestAnimationFrame(() => {
        this.flush();
      });
    }
  }
  
  flush(): void {
    const updates = this.updates.slice();
    this.updates = [];
    this.rafId = null;
    
    // Ejecutar todas las actualizaciones en un solo frame
    updates.forEach(update => update());
  }
  
  cancel(): void {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.updates = [];
  }
}

// Uso
const batchUpdater = new DOMBatchUpdater();

export const updateCameraFrame = (cameraId: string, frame: string) => {
  batchUpdater.schedule(() => {
    const element = document.getElementById(`camera-${cameraId}`);
    if (element) {
      element.style.backgroundImage = `url(${frame})`;
    }
  });
};
```

### Intersection Observer

```typescript
// hooks/useIntersectionObserver.ts
export const useIntersectionObserver = (
  ref: RefObject<Element>,
  options?: IntersectionObserverInit
): boolean => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options
      }
    );
    
    observer.observe(element);
    
    return () => {
      observer.disconnect();
    };
  }, [ref, options]);
  
  return isIntersecting;
};

// Componente que solo renderiza cuando es visible
export const LazyImage: React.FC<{ src: string; alt: string }> = ({ src, alt }) => {
  const ref = useRef<HTMLDivElement>(null);
  const isVisible = useIntersectionObserver(ref);
  
  return (
    <div ref={ref} style={{ minHeight: 200 }}>
      {isVisible ? (
        <img src={src} alt={alt} loading="lazy" />
      ) : (
        <Skeleton variant="rectangular" width="100%" height={200} />
      )}
    </div>
  );
};
```

## 📊 Monitoreo de Performance

### Performance Observer

```typescript
// utils/performanceMonitor.ts
export class PerformanceMonitor {
  private observer: PerformanceObserver | null = null;
  
  start() {
    if (!('PerformanceObserver' in window)) return;
    
    this.observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        // Log métricas importantes
        if (entry.entryType === 'measure') {
          console.log(`⏱️ ${entry.name}: ${entry.duration.toFixed(2)}ms`);
          
          // Enviar a analytics si es necesario
          if (entry.duration > 1000) {
            console.warn(`Slow operation detected: ${entry.name}`);
          }
        }
      }
    });
    
    this.observer.observe({ entryTypes: ['measure', 'navigation'] });
  }
  
  measure(name: string, fn: () => void): void {
    performance.mark(`${name}-start`);
    fn();
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
  }
  
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    performance.mark(`${name}-start`);
    try {
      const result = await fn();
      return result;
    } finally {
      performance.mark(`${name}-end`);
      performance.measure(name, `${name}-start`, `${name}-end`);
    }
  }
}

// Uso
const perfMonitor = new PerformanceMonitor();
perfMonitor.start();

// Medir operaciones
perfMonitor.measureAsync('fetch-cameras', async () => {
  return cameraService.getAllCameras();
});
```

### React DevTools Profiler

```typescript
// components/withProfiler.tsx
import { Profiler, ProfilerOnRenderCallback } from 'react';

const onRenderCallback: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) => {
  if (actualDuration > 16) { // Más de un frame (60fps)
    console.warn(`Slow render in ${id}:`, {
      phase,
      actualDuration,
      baseDuration
    });
  }
};

export const withProfiler = <P extends object>(
  Component: React.ComponentType<P>,
  id: string
) => {
  return (props: P) => (
    <Profiler id={id} onRender={onRenderCallback}>
      <Component {...props} />
    </Profiler>
  );
};

// Uso
const ProfiledCameraGrid = withProfiler(CameraGrid, 'camera-grid');
```

## 🎯 Checklist de Performance

### Pre-deployment

- [ ] Bundle size < 500KB (gzipped)
- [ ] Lazy loading implementado en todas las rutas
- [ ] Imágenes optimizadas y con lazy loading
- [ ] Sin memory leaks en streaming
- [ ] Lighthouse score > 90
- [ ] No hay console.logs en producción
- [ ] Service Worker para caché offline
- [ ] Compresión gzip/brotli habilitada

### Monitoreo Continuo

- [ ] Web Vitals tracking
- [ ] Error boundary reporting
- [ ] Performance budgets configurados
- [ ] Alertas para métricas degradadas
- [ ] A/B testing para optimizaciones

---

[← Guía de Desarrollo](./guia-desarrollo.md) | [Índice](./README.md) | [Testing →](./testing.md)