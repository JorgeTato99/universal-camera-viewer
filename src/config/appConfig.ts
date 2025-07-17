/**
 * 🎯 App Configuration - Universal Camera Viewer
 * Configuración global de la aplicación
 */

// Importar versión del package.json
import packageJson from '../../package.json';

export const APP_CONFIG = {
  // Información de la aplicación
  app: {
    name: 'Universal Camera Viewer',
    shortName: 'UCV',
    version: packageJson.version, // Se obtiene automáticamente del package.json
    description: 'Sistema profesional de videovigilancia IP con streaming en tiempo real',
  },

  // Información de la empresa
  company: {
    name: 'Kipustec',
    fullName: 'Kipustec S.A. de C.V.',
    website: 'https://kipustec.com',
    email: 'contacto@kipustec.com',
    year: new Date().getFullYear(),
  },

  // Copyright y licencia
  legal: {
    copyright: `© ${new Date().getFullYear()} Kipustec - All Rights Reserved`,
    copyrightShort: `© ${new Date().getFullYear()} Kipustec`,
    license: 'Propietario',
    trademark: 'Universal Camera Viewer® es una marca registrada de Kipustec S.A. de C.V.',
  },

  // Información técnica
  technical: {
    minPythonVersion: '3.8',
    minNodeVersion: '18.0.0',
    supportedCameras: ['Dahua', 'TP-Link', 'Steren', 'Hikvision', 'Xiaomi', 'Reolink'],
    protocols: ['ONVIF', 'RTSP', 'HTTP/CGI'],
  },

  // URLs y enlaces
  links: {
    github: 'https://github.com/JorgeTato99/universal-camera-viewer',
    documentation: 'https://docs.kipustec.com/ucv',
    support: 'https://support.kipustec.com',
    updates: 'https://updates.kipustec.com/ucv',
  },

  // Configuración de desarrollo
  development: {
    author: 'Jorge Tato',
    authorGithub: 'https://github.com/JorgeTato99',
    team: 'Kipustec Development Team',
  },
} as const;

// Helpers para acceso rápido
export const getAppVersion = () => `v${APP_CONFIG.app.version}`;
export const getAppName = () => APP_CONFIG.app.name;
export const getCopyright = () => APP_CONFIG.legal.copyright;
export const getCompanyName = () => APP_CONFIG.company.name;