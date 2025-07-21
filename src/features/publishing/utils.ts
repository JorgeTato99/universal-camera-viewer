/**
 * 🛠️ Publishing Utils - Universal Camera Viewer
 * Utilidades para el módulo de publicación MediaMTX
 */

import { format, formatDistance, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';
import { PublishingStatus, PublishMetrics } from './types';

/**
 * Formatea duración en segundos a formato legible
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  
  return `${minutes}m ${secs}s`;
}

/**
 * Formatea bytes a unidad legible
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Formatea bitrate a unidad legible
 */
export function formatBitrate(kbps: number): string {
  if (kbps < 1000) {
    return `${kbps} Kbps`;
  }
  
  return `${(kbps / 1000).toFixed(1)} Mbps`;
}

/**
 * Formatea fecha ISO a formato local
 */
export function formatDate(dateString: string, formatStr = 'dd/MM/yyyy HH:mm:ss'): string {
  try {
    return format(parseISO(dateString), formatStr, { locale: es });
  } catch {
    return dateString;
  }
}

/**
 * Formatea fecha ISO a distancia relativa
 */
export function formatRelativeTime(dateString: string): string {
  try {
    return formatDistance(parseISO(dateString), new Date(), { 
      addSuffix: true,
      locale: es 
    });
  } catch {
    return dateString;
  }
}

/**
 * Calcula el porcentaje de uptime
 */
export function calculateUptime(uptimeSeconds: number, totalSeconds: number): number {
  if (totalSeconds === 0) return 0;
  return Math.round((uptimeSeconds / totalSeconds) * 100);
}

/**
 * Obtiene el color de severidad para métricas
 */
export function getMetricSeverityColor(metric: number, thresholds: { good: number; warning: number }): string {
  if (metric >= thresholds.good) return '#4caf50'; // Verde
  if (metric >= thresholds.warning) return '#ff9800'; // Naranja
  return '#f44336'; // Rojo
}

/**
 * Agrupa métricas por intervalo de tiempo
 */
export function groupMetricsByInterval(
  metrics: PublishMetrics[], 
  intervalMinutes: number
): PublishMetrics[] {
  if (metrics.length === 0) return [];
  
  const grouped: Map<string, PublishMetrics[]> = new Map();
  
  metrics.forEach(metric => {
    const date = parseISO(metric.timestamp);
    const intervalKey = Math.floor(date.getTime() / (intervalMinutes * 60 * 1000));
    
    if (!grouped.has(intervalKey.toString())) {
      grouped.set(intervalKey.toString(), []);
    }
    
    grouped.get(intervalKey.toString())!.push(metric);
  });
  
  // Promediar métricas por intervalo
  return Array.from(grouped.values()).map(group => {
    const avgFps = group.reduce((sum, m) => sum + m.fps, 0) / group.length;
    const avgBitrate = group.reduce((sum, m) => sum + m.bitrate_kbps, 0) / group.length;
    const avgViewers = group.reduce((sum, m) => sum + m.viewers, 0) / group.length;
    const totalFrames = group.reduce((sum, m) => sum + m.frames_sent, 0);
    const totalBytes = group.reduce((sum, m) => sum + m.bytes_sent, 0);
    
    return {
      fps: Math.round(avgFps * 10) / 10,
      bitrate_kbps: Math.round(avgBitrate),
      viewers: Math.round(avgViewers),
      frames_sent: totalFrames,
      bytes_sent: totalBytes,
      timestamp: group[0].timestamp
    };
  });
}

/**
 * Valida URL de MediaMTX
 */
export function validateMediaMTXUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ['rtsp:', 'rtmp:', 'http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

/**
 * Genera un path único para publicación
 */
export function generatePublishPath(template: string, cameraId: string): string {
  const timestamp = Date.now();
  const randomId = Math.random().toString(36).substring(7);
  
  return template
    .replace('{camera_id}', cameraId)
    .replace('{timestamp}', timestamp.toString())
    .replace('{random}', randomId);
}

/**
 * Convierte estado a booleano para indicar si está activo
 */
export function isPublishingActive(status: PublishingStatus): boolean {
  return status === PublishingStatus.RUNNING || status === PublishingStatus.STARTING;
}

/**
 * Calcula estadísticas de métricas
 */
export function calculateMetricStats(metrics: PublishMetrics[]): {
  avgFps: number;
  maxFps: number;
  minFps: number;
  avgBitrate: number;
  maxBitrate: number;
  minBitrate: number;
  totalData: number;
} {
  if (metrics.length === 0) {
    return {
      avgFps: 0,
      maxFps: 0,
      minFps: 0,
      avgBitrate: 0,
      maxBitrate: 0,
      minBitrate: 0,
      totalData: 0
    };
  }
  
  const fpsValues = metrics.map(m => m.fps);
  const bitrateValues = metrics.map(m => m.bitrate_kbps);
  
  return {
    avgFps: Math.round(fpsValues.reduce((a, b) => a + b) / fpsValues.length * 10) / 10,
    maxFps: Math.max(...fpsValues),
    minFps: Math.min(...fpsValues),
    avgBitrate: Math.round(bitrateValues.reduce((a, b) => a + b) / bitrateValues.length),
    maxBitrate: Math.max(...bitrateValues),
    minBitrate: Math.min(...bitrateValues),
    totalData: metrics.reduce((sum, m) => sum + m.bytes_sent, 0)
  };
}

/**
 * Exporta datos a CSV
 */
export function exportToCSV(data: any[], filename: string): void {
  if (data.length === 0) return;
  
  // Obtener headers
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escapar comillas y envolver en comillas si contiene comas
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');
  
  // Crear blob y descargar
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}