/**
 * 🔍 Publishing Validation Utils - Universal Camera Viewer
 * Funciones de validación para el módulo de publicación
 */

/**
 * Valida si una URL es válida para MediaMTX
 * @param url - URL a validar
 * @returns true si la URL es válida
 */
export function validateMediaMTXUrl(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  try {
    // Intentar parsear la URL
    const parsed = new URL(url);
    
    // Verificar protocolo soportado
    const supportedProtocols = ['rtsp:', 'rtmp:', 'http:', 'https:'];
    if (!supportedProtocols.includes(parsed.protocol)) {
      return false;
    }
    
    // Verificar que tenga host
    if (!parsed.hostname) {
      return false;
    }
    
    // Para RTSP/RTMP, verificar puerto por defecto si no está especificado
    if (parsed.protocol === 'rtsp:' && !parsed.port) {
      // RTSP usa puerto 554 por defecto
      return true;
    }
    
    if (parsed.protocol === 'rtmp:' && !parsed.port) {
      // RTMP usa puerto 1935 por defecto
      return true;
    }
    
    return true;
  } catch (error) {
    // Si no se puede parsear, no es válida
    return false;
  }
}

/**
 * Valida credenciales de MediaMTX
 * @param username - Nombre de usuario
 * @param password - Contraseña
 * @returns Objeto con validación y mensajes de error
 */
export function validateMediaMTXCredentials(
  username: string,
  password: string
): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Validar username
  if (!username || username.trim().length === 0) {
    errors.push('El nombre de usuario es requerido');
  } else if (username.length < 3) {
    errors.push('El nombre de usuario debe tener al menos 3 caracteres');
  } else if (username.length > 50) {
    errors.push('El nombre de usuario no puede exceder 50 caracteres');
  }
  
  // Validar password
  if (!password || password.length === 0) {
    errors.push('La contraseña es requerida');
  } else if (password.length < 4) {
    errors.push('La contraseña debe tener al menos 4 caracteres');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Normaliza una URL de MediaMTX agregando valores por defecto
 * @param url - URL a normalizar
 * @returns URL normalizada
 */
export function normalizeMediaMTXUrl(url: string): string {
  if (!url) return '';
  
  try {
    const parsed = new URL(url);
    
    // Agregar puerto por defecto si no está especificado
    if (!parsed.port) {
      switch (parsed.protocol) {
        case 'rtsp:':
          parsed.port = '554';
          break;
        case 'rtmp:':
          parsed.port = '1935';
          break;
        case 'http:':
          parsed.port = '80';
          break;
        case 'https:':
          parsed.port = '443';
          break;
      }
    }
    
    return parsed.toString();
  } catch (error) {
    return url;
  }
}

/**
 * Extrae información de una URL de MediaMTX
 * @param url - URL a analizar
 * @returns Información extraída
 */
export function parseMediaMTXUrl(url: string): {
  protocol: string;
  hostname: string;
  port: string;
  pathname: string;
  isValid: boolean;
} | null {
  if (!validateMediaMTXUrl(url)) {
    return null;
  }
  
  try {
    const parsed = new URL(url);
    
    return {
      protocol: parsed.protocol.replace(':', ''),
      hostname: parsed.hostname,
      port: parsed.port || getDefaultPort(parsed.protocol),
      pathname: parsed.pathname,
      isValid: true
    };
  } catch (error) {
    return null;
  }
}

/**
 * Obtiene el puerto por defecto para un protocolo
 * @param protocol - Protocolo (con o sin ':')
 * @returns Puerto por defecto
 */
function getDefaultPort(protocol: string): string {
  const proto = protocol.replace(':', '');
  
  switch (proto) {
    case 'rtsp':
      return '554';
    case 'rtmp':
      return '1935';
    case 'http':
      return '80';
    case 'https':
      return '443';
    default:
      return '';
  }
}

/**
 * Valida un nombre de servidor MediaMTX
 * @param name - Nombre del servidor
 * @returns Objeto con validación y mensaje de error
 */
export function validateServerName(name: string): {
  isValid: boolean;
  error?: string;
} {
  if (!name || name.trim().length === 0) {
    return { isValid: false, error: 'El nombre es requerido' };
  }
  
  if (name.length < 3) {
    return { isValid: false, error: 'El nombre debe tener al menos 3 caracteres' };
  }
  
  if (name.length > 50) {
    return { isValid: false, error: 'El nombre no puede exceder 50 caracteres' };
  }
  
  // Validar caracteres permitidos (alfanumérico, espacios, guiones, guiones bajos)
  const validPattern = /^[a-zA-Z0-9\s\-_]+$/;
  if (!validPattern.test(name)) {
    return { 
      isValid: false, 
      error: 'El nombre solo puede contener letras, números, espacios, guiones y guiones bajos' 
    };
  }
  
  return { isValid: true };
}

/**
 * Genera un nombre único para un servidor
 * @param baseName - Nombre base
 * @param existingNames - Lista de nombres existentes
 * @returns Nombre único
 */
export function generateUniqueServerName(
  baseName: string,
  existingNames: string[]
): string {
  let name = baseName;
  let counter = 1;
  
  while (existingNames.includes(name)) {
    name = `${baseName} ${counter}`;
    counter++;
  }
  
  return name;
}