/**
 * 🔧 Formatting Utilities - Universal Camera Viewer
 * Funciones de formateo para la aplicación
 */

/**
 * Formatea bytes a una unidad legible
 * @param bytes - Cantidad de bytes
 * @param decimals - Número de decimales (default: 2)
 * @returns String formateado (ej: "1.23 MB")
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Formatea duración en segundos a formato legible
 * @param seconds - Duración en segundos
 * @param format - Formato de salida ('full' | 'compact' | 'short')
 * @returns String formateado
 */
export function formatDuration(seconds: number, format: 'full' | 'compact' | 'short' = 'full'): string {
  if (seconds < 0) return '0s';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  switch (format) {
    case 'full':
      const parts = [];
      if (hours > 0) parts.push(`${hours} hora${hours !== 1 ? 's' : ''}`);
      if (minutes > 0) parts.push(`${minutes} minuto${minutes !== 1 ? 's' : ''}`);
      if (secs > 0 || parts.length === 0) parts.push(`${secs} segundo${secs !== 1 ? 's' : ''}`);
      return parts.join(', ');

    case 'compact':
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
      } else {
        return `${secs}s`;
      }

    case 'short':
      return [
        hours > 0 ? String(hours).padStart(2, '0') : null,
        String(minutes).padStart(2, '0'),
        String(secs).padStart(2, '0')
      ].filter(Boolean).join(':');

    default:
      return `${seconds}s`;
  }
}

/**
 * Formatea un número con separadores de miles
 * @param num - Número a formatear
 * @param locale - Locale para el formato (default: 'es-ES')
 * @returns String formateado
 */
export function formatNumber(num: number, locale: string = 'es-ES'): string {
  return num.toLocaleString(locale);
}

/**
 * Formatea una fecha a formato legible
 * @param date - Fecha a formatear (string, number o Date)
 * @param format - Formato deseado ('full' | 'date' | 'time' | 'relative')
 * @param locale - Locale para el formato (default: 'es-ES')
 * @returns String formateado
 */
export function formatDate(
  date: string | number | Date,
  format: 'full' | 'date' | 'time' | 'relative' = 'full',
  locale: string = 'es-ES'
): string {
  const dateObj = new Date(date);
  
  if (isNaN(dateObj.getTime())) {
    return 'Fecha inválida';
  }

  switch (format) {
    case 'full':
      return dateObj.toLocaleString(locale);
      
    case 'date':
      return dateObj.toLocaleDateString(locale);
      
    case 'time':
      return dateObj.toLocaleTimeString(locale);
      
    case 'relative':
      const now = new Date();
      const diffMs = now.getTime() - dateObj.getTime();
      const diffSecs = Math.floor(diffMs / 1000);
      const diffMins = Math.floor(diffSecs / 60);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffSecs < 60) return 'hace un momento';
      if (diffMins < 60) return `hace ${diffMins} minuto${diffMins !== 1 ? 's' : ''}`;
      if (diffHours < 24) return `hace ${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
      if (diffDays < 30) return `hace ${diffDays} día${diffDays !== 1 ? 's' : ''}`;
      
      return dateObj.toLocaleDateString(locale);
      
    default:
      return dateObj.toString();
  }
}

/**
 * Formatea un porcentaje
 * @param value - Valor entre 0 y 1 (o 0 y 100 si isPercent es true)
 * @param decimals - Número de decimales
 * @param isPercent - Si el valor ya está en porcentaje (0-100)
 * @returns String formateado con símbolo %
 */
export function formatPercent(value: number, decimals: number = 0, isPercent: boolean = false): string {
  const percent = isPercent ? value : value * 100;
  return `${percent.toFixed(decimals)}%`;
}

/**
 * Formatea una dirección IP con ceros a la izquierda opcionales
 * @param ip - Dirección IP
 * @param padZeros - Si debe rellenar con ceros
 * @returns IP formateada
 */
export function formatIP(ip: string, padZeros: boolean = false): string {
  if (!padZeros) return ip;
  
  const parts = ip.split('.');
  if (parts.length !== 4) return ip;
  
  return parts
    .map(part => part.padStart(3, '0'))
    .join('.');
}

/**
 * Trunca un texto agregando elipsis
 * @param text - Texto a truncar
 * @param maxLength - Longitud máxima
 * @param position - Posición del truncado ('end' | 'middle' | 'start')
 * @returns Texto truncado
 */
export function truncateText(
  text: string,
  maxLength: number,
  position: 'end' | 'middle' | 'start' = 'end'
): string {
  if (text.length <= maxLength) return text;
  
  const ellipsis = '...';
  const availableLength = maxLength - ellipsis.length;
  
  switch (position) {
    case 'start':
      return ellipsis + text.slice(-availableLength);
      
    case 'middle':
      const halfLength = Math.floor(availableLength / 2);
      return text.slice(0, halfLength) + ellipsis + text.slice(-halfLength);
      
    case 'end':
    default:
      return text.slice(0, availableLength) + ellipsis;
  }
}

/**
 * Formatea un valor de bitrate a una unidad apropiada
 * @param kbps - Bitrate en kilobits por segundo
 * @returns String formateado (ej: "2.5 Mbps")
 */
export function formatBitrate(kbps: number): string {
  if (kbps < 1000) {
    return `${kbps} kbps`;
  } else {
    const mbps = kbps / 1000;
    return `${mbps.toFixed(1)} Mbps`;
  }
}