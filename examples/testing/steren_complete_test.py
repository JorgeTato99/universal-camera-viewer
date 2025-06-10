"""
Analizador Completo para Cámaras Steren CCTV-235
=================================================

Script integral que:
1. Detecta puertos y protocolos disponibles
2. Prueba conexiones ONVIF/RTSP/HTTP
3. Extrae perfiles completos
4. Exporta resultados a archivos JSON

Autor: Universal Visor Team
Fecha: 2024
"""

import sys
import os
import socket
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# cspell:disable
# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Importaciones opcionales
try:
    from onvif import ONVIFCamera
    from onvif.exceptions import ONVIFError
    ONVIF_AVAILABLE = True
except ImportError:
    ONVIF_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class SterenAnalyzer:
    """
    Analizador completo para cámaras Steren CCTV-235.
    """
    
    def __init__(self):
        self.config = {}
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'device_info': {},
            'port_scan': {},
            'protocol_tests': {},
            'onvif_profiles': [],
            'exported_files': [],
            'summary': {}
        }
        
        # Puertos comunes para cámaras IP
        self.common_ports = {
            80: 'HTTP',
            443: 'HTTPS',
            554: 'RTSP',
            8000: 'HTTP-Alt',
            8080: 'HTTP-Proxy',
            8443: 'HTTPS-Alt',
            5543: 'RTSP-Alt',
            37777: 'Dahua-TCP',
            3702: 'ONVIF-Discovery'
        }
    
    def print_banner(self):
        """Muestra el banner inicial."""
        print("🎯 ANALIZADOR COMPLETO STEREN CCTV-235")
        print("="*50)
        print("📡 Detección automática de puertos y protocolos")
        print("🔍 Análisis ONVIF con extracción de perfiles")
        print("📄 Exportación completa a archivos JSON")
        print("="*50)
        print()
    
    def load_env_config(self):
        """Carga configuración desde .env si está disponible."""
        env_config = {
            'ip': '',
            'user': 'admin',
            'password': ''
        }
        
        if DOTENV_AVAILABLE:
            try:
                env_path = Path(__file__).parent.parent.parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path, override=True)
                    env_config = {
                        'ip': os.getenv("STEREN_IP", ""),
                        'user': os.getenv("STEREN_USER", "admin"),
                        'password': os.getenv("STEREN_PASSWORD", "")
                    }
                    print("✅ Configuración cargada desde .env")
                else:
                    print("⚠️ Archivo .env no encontrado")
            except Exception as e:
                print(f"⚠️ Error cargando .env: {str(e)}")
        else:
            print("⚠️ python-dotenv no disponible")
        
        return env_config
    
    def get_user_config(self, env_config):
        """Obtiene configuración del usuario con valores por defecto."""
        print("\n📋 CONFIGURACIÓN DE CONEXIÓN")
        print("-" * 30)
        
        # IP de la cámara
        default_ip = env_config.get('ip', '192.168.1.178')
        if default_ip:
            ip_prompt = f"IP de la cámara [{default_ip}]: "
        else:
            ip_prompt = "IP de la cámara (ej: 192.168.1.178): "
        
        ip = input(ip_prompt).strip()
        if not ip:
            ip = default_ip
        
        # Usuario
        default_user = env_config.get('user', 'admin')
        user_prompt = f"Usuario [{default_user}]: "
        user = input(user_prompt).strip()
        if not user:
            user = default_user
        
        # Contraseña
        default_password = env_config.get('password', '')
        if default_password:
            password_prompt = f"Contraseña [{'*' * len(default_password)}]: "
        else:
            password_prompt = "Contraseña: "
        
        password = input(password_prompt).strip()
        if not password and default_password:
            password = default_password
        
        return {
            'ip': ip,
            'user': user,
            'password': password
        }
    
    def get_user_options(self):
        """Obtiene opciones de ejecución del usuario."""
        print("\n⚙️ OPCIONES DE ANÁLISIS")
        print("-" * 25)
        
        # Prueba de conexiones
        test_connections = input("¿Probar conexiones en puertos abiertos? [S/n]: ").strip().lower()
        test_connections = test_connections not in ['n', 'no', '0']
        
        # Extracción de perfiles
        extract_profiles = input("¿Extraer perfiles ONVIF a archivos JSON? [S/n]: ").strip().lower()
        extract_profiles = extract_profiles not in ['n', 'no', '0']
        
        return {
            'test_connections': test_connections,
            'extract_profiles': extract_profiles
        }
    
    def scan_port(self, host, port, timeout=3):
        """
        Escanea un puerto específico.
        
        Args:
            host: IP a escanear
            port: Puerto a probar
            timeout: Timeout en segundos
            
        Returns:
            bool: True si el puerto está abierto
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def scan_ports(self, host):
        """
        Escanea puertos comunes en paralelo.
        
        Args:
            host: IP a escanear
            
        Returns:
            dict: Puertos abiertos con su protocolo
        """
        print(f"🔍 Escaneando puertos en {host}...")
        
        open_ports = {}
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            # Crear tareas para cada puerto
            future_to_port = {
                executor.submit(self.scan_port, host, port): port 
                for port in self.common_ports.keys()
            }
            
            # Recolectar resultados
            for future in future_to_port:
                port = future_to_port[future]
                try:
                    if future.result():
                        protocol = self.common_ports[port]
                        open_ports[port] = protocol
                        print(f"   ✅ Puerto {port} ({protocol}) - ABIERTO")
                except:
                    pass
        
        if not open_ports:
            print("   ❌ No se encontraron puertos abiertos")
        else:
            print(f"   📊 Total puertos abiertos: {len(open_ports)}")
        
        return open_ports
    
    def test_http_connection(self, host, port, timeout=10):
        """Prueba conexión HTTP."""
        if not REQUESTS_AVAILABLE:
            return {'success': False, 'error': 'requests no disponible'}
        
        try:
            url = f"http://{host}:{port}"
            response = requests.get(url, timeout=timeout)
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'url': url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_rtsp_connection(self, host, port, username, password, timeout=15):
        """Prueba conexión RTSP."""
        if not CV2_AVAILABLE:
            return {'success': False, 'error': 'opencv no disponible'}
        
        try:
            # Probar diferentes paths RTSP comunes
            rtsp_paths = [
                f"rtsp://{username}:{password}@{host}:{port}/live/channel0",
                f"rtsp://{username}:{password}@{host}:{port}/live/channel1",
                f"rtsp://{username}:{password}@{host}:{port}/stream1",
                f"rtsp://{username}:{password}@{host}:{port}/stream2",
                f"rtsp://{host}:{port}/live/channel0",
                f"rtsp://{host}:{port}/stream1"
            ]
            
            working_streams = []
            
            for rtsp_url in rtsp_paths:
                try:
                    cap = cv2.VideoCapture(rtsp_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    start_time = time.time()
                    success = False
                    
                    # Intentar leer frame por hasta 5 segundos
                    while time.time() - start_time < 5:
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            working_streams.append({
                                'url': rtsp_url,
                                'resolution': (frame.shape[1], frame.shape[0]),
                                'connection_time': time.time() - start_time
                            })
                            success = True
                            break
                        time.sleep(0.1)
                    
                    cap.release()
                    
                    if success:
                        break  # Solo probar hasta encontrar uno que funcione
                        
                except Exception as e:
                    continue
            
            if working_streams:
                return {
                    'success': True,
                    'streams': working_streams
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudieron conectar streams RTSP'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_onvif_connection(self, host, port, username, password):
        """Prueba conexión ONVIF."""
        if not ONVIF_AVAILABLE:
            return {'success': False, 'error': 'python-onvif-zeep no disponible'}
        
        try:
            # Crear conexión ONVIF
            camera = ONVIFCamera(host, port, username, password)
            
            # Obtener información del dispositivo
            device_service = camera.create_devicemgmt_service()
            device_info = device_service.GetDeviceInformation()
            
            # Obtener perfiles de media
            media_service = camera.create_media_service()
            profiles = media_service.GetProfiles()
            
            profile_data = []
            for profile in profiles:
                profile_info = {
                    'name': getattr(profile, 'Name', 'Unknown'),
                    'token': getattr(profile, 'token', None),
                    'video_config': None,
                    'audio_config': None
                }
                
                # Obtener configuración de video
                if hasattr(profile, 'VideoEncoderConfiguration'):
                    video_config = profile.VideoEncoderConfiguration
                    profile_info['video_config'] = {
                        'name': getattr(video_config, 'Name', 'Unknown'),
                        'encoding': getattr(video_config, 'Encoding', 'Unknown'),
                        'resolution': None
                    }
                    
                    if hasattr(video_config, 'Resolution'):
                        res = video_config.Resolution
                        profile_info['video_config']['resolution'] = {
                            'width': getattr(res, 'Width', 0),
                            'height': getattr(res, 'Height', 0)
                        }
                
                # Obtener configuración de audio
                if hasattr(profile, 'AudioEncoderConfiguration'):
                    audio_config = profile.AudioEncoderConfiguration
                    profile_info['audio_config'] = {
                        'name': getattr(audio_config, 'Name', 'Unknown'),
                        'encoding': getattr(audio_config, 'Encoding', 'Unknown'),
                        'bitrate': getattr(audio_config, 'Bitrate', 0),
                        'sample_rate': getattr(audio_config, 'SampleRate', 0)
                    }
                
                profile_data.append(profile_info)
            
            return {
                'success': True,
                'device_info': {
                    'manufacturer': device_info.Manufacturer,
                    'model': device_info.Model,
                    'firmware': device_info.FirmwareVersion,
                    'serial': device_info.SerialNumber
                },
                'profiles': profile_data,
                'camera_available': True,  # Indicador sin objeto
                'media_service_available': True,
                'camera_object': camera,  # Mantener para uso local (no se serializa)
                'media_service_object': media_service  # Mantener para uso local (no se serializa)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def serialize_onvif_object(self, obj, max_depth=3, current_depth=0):
        """Serializa objetos ONVIF a formato JSON."""
        if current_depth >= max_depth:
            return str(obj)
        
        if obj is None:
            return None
        
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        if isinstance(obj, (list, tuple)):
            return [self.serialize_onvif_object(item, max_depth, current_depth + 1) for item in obj]
        
        if isinstance(obj, dict):
            return {k: self.serialize_onvif_object(v, max_depth, current_depth + 1) for k, v in obj.items()}
        
        if hasattr(obj, '__dict__'):
            result = {}
            for attr in dir(obj):
                if not attr.startswith('_'):
                    try:
                        value = getattr(obj, attr)
                        if not callable(value):
                            result[attr] = self.serialize_onvif_object(value, max_depth, current_depth + 1)
                    except:
                        result[attr] = f"<Error accessing {attr}>"
            return result
        
        return str(obj)
    
    def extract_full_profiles(self, camera, media_service, profiles):
        """Extrae perfiles completos con toda la información disponible."""
        full_profiles = []
        
        for i, profile in enumerate(profiles):
            profile_name = getattr(profile, 'Name', f'Profile_{i}')
            print(f"   📊 Extrayendo {profile_name}...")
            
            # Serializar perfil completo
            profile_data = {
                'profile_name': profile_name,
                'extraction_timestamp': datetime.now().isoformat(),
                'profile_structure': self.serialize_onvif_object(profile),
                'stream_uris': [],
                'snapshot_uris': [],
                'tokens_found': []
            }
            
            # Buscar tokens
            token = getattr(profile, 'token', None)
            if token:
                profile_data['tokens_found'].append({
                    'attribute': 'token',
                    'value': token,
                    'location': 'root'
                })
                
                # Intentar obtener Stream URIs
                for stream_type, protocol in [('RTP-Unicast', 'RTSP'), ('HTTP', 'HTTP')]:
                    try:
                        stream_uri = media_service.GetStreamUri({
                            'StreamSetup': {
                                'Stream': stream_type,
                                'Transport': {'Protocol': protocol}
                            },
                            'ProfileToken': token
                        })
                        profile_data['stream_uris'].append({
                            'type': f"{stream_type}/{protocol}",
                            'url': stream_uri.Uri
                        })
                    except Exception as e:
                        profile_data['stream_uris'].append({
                            'type': f"{stream_type}/{protocol}",
                            'error': str(e)
                        })
                
                # Intentar obtener Snapshot URI
                try:
                    snapshot_uri = media_service.GetSnapshotUri({'ProfileToken': token})
                    profile_data['snapshot_uris'].append({
                        'type': 'Snapshot',
                        'url': snapshot_uri.Uri
                    })
                except Exception as e:
                    profile_data['snapshot_uris'].append({
                        'type': 'Snapshot',
                        'error': str(e)
                    })
            
            full_profiles.append(profile_data)
        
        return full_profiles
    
    def save_profile_json(self, profile_data, base_path):
        """Guarda un perfil individual en archivo JSON."""
        safe_name = profile_data['profile_name'].replace('/', '_').replace('\\', '_').replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"steren_profile_{safe_name}_{timestamp}.json"
        filepath = base_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 Guardado: {filename}")
        return str(filepath)
    
    def save_complete_results(self, base_path):
        """Guarda resultados completos del análisis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"steren_complete_analysis_{timestamp}.json"
        filepath = base_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Análisis completo guardado: {filename}")
        return str(filepath)
    
    def test_protocol_connections(self, host, open_ports, username, password):
        """Prueba conexiones de diferentes protocolos."""
        print(f"\n🔌 PROBANDO CONEXIONES EN {host}")
        print("-" * 40)
        
        protocol_results = {}
        
        for port, protocol in open_ports.items():
            print(f"🧪 Probando {protocol} en puerto {port}...")
            
            if protocol in ['HTTP', 'HTTP-Alt', 'HTTP-Proxy']:
                result = self.test_http_connection(host, port)
                protocol_results[f"{protocol}_{port}"] = result
                
                if result['success']:
                    print(f"   ✅ HTTP {port}: {result['status_code']}")
                else:
                    print(f"   ❌ HTTP {port}: {result['error']}")
            
            elif protocol in ['RTSP', 'RTSP-Alt']:
                result = self.test_rtsp_connection(host, port, username, password)
                protocol_results[f"{protocol}_{port}"] = result
                
                if result['success']:
                    print(f"   ✅ RTSP {port}: {len(result['streams'])} stream(s)")
                    for stream in result['streams']:
                        print(f"      📺 {stream['resolution']} - {stream['url']}")
                else:
                    print(f"   ❌ RTSP {port}: {result['error']}")
            
            # ONVIF puede estar en varios puertos
            if port in [80, 8000, 8080, 3702]:
                result = self.test_onvif_connection(host, port, username, password)
                protocol_results[f"ONVIF_{port}"] = result
                
                if result['success']:
                    device_info = result['device_info']
                    print(f"   ✅ ONVIF {port}: {device_info['manufacturer']} {device_info['model']}")
                    print(f"      📋 Perfiles: {len(result['profiles'])}")
                    
                    # Guardar info del dispositivo
                    self.results['device_info'] = device_info
                    
                    # Si se solicita extracción de perfiles
                    if hasattr(self, 'extract_profiles') and self.extract_profiles:
                        try:
                            print("   🔍 Extrayendo perfiles completos...")
                            camera = result['camera_object']
                            media_service = result['media_service_object']
                            profiles = media_service.GetProfiles()
                            
                            full_profiles = self.extract_full_profiles(camera, media_service, profiles)
                            self.results['onvif_profiles'] = full_profiles
                            
                            # Guardar cada perfil en archivo separado
                            base_path = Path(__file__).parent
                            for profile_data in full_profiles:
                                json_file = self.save_profile_json(profile_data, base_path)
                                self.results['exported_files'].append(json_file)
                                
                        except Exception as e:
                            print(f"   ⚠️ Error extrayendo perfiles: {str(e)}")
                else:
                    print(f"   ❌ ONVIF {port}: {result['error']}")
        
        # Limpiar objetos no serializables antes de retornar
        for protocol_name, result in protocol_results.items():
            if isinstance(result, dict):
                # Remover objetos no serializables para JSON
                result.pop('camera_object', None)
                result.pop('media_service_object', None)
        
        return protocol_results
    
    def generate_summary(self):
        """Genera resumen del análisis."""
        summary = {
            'total_ports_scanned': len(self.common_ports),
            'open_ports_found': len(self.results['port_scan']),
            'successful_connections': 0,
            'onvif_available': False,
            'rtsp_streams_found': 0,
            'profiles_extracted': len(self.results['onvif_profiles']),
            'files_exported': len(self.results['exported_files']),
            'recommendations': []
        }
        
        # Contar conexiones exitosas
        for protocol, result in self.results['protocol_tests'].items():
            if result.get('success', False):
                summary['successful_connections'] += 1
                
                if 'ONVIF' in protocol:
                    summary['onvif_available'] = True
                
                if 'RTSP' in protocol and 'streams' in result:
                    summary['rtsp_streams_found'] += len(result['streams'])
        
        # Generar recomendaciones
        if summary['onvif_available']:
            summary['recommendations'].append("✅ ONVIF disponible - Recomendado para integración completa")
        
        if summary['rtsp_streams_found'] > 0:
            summary['recommendations'].append(f"🎥 {summary['rtsp_streams_found']} stream(s) RTSP encontrados")
        
        if summary['profiles_extracted'] > 0:
            summary['recommendations'].append(f"📊 {summary['profiles_extracted']} perfil(es) exportados exitosamente")
        
        if not summary['successful_connections']:
            summary['recommendations'].append("⚠️ No se pudieron establecer conexiones - Verificar credenciales")
        
        self.results['summary'] = summary
        return summary
    
    def run_analysis(self):
        """Ejecuta el análisis completo."""
        self.print_banner()
        
        # Cargar configuración
        env_config = self.load_env_config()
        self.config = self.get_user_config(env_config)
        options = self.get_user_options()
        
        # Guardar opciones para uso posterior
        self.extract_profiles = options['extract_profiles']
        
        # Validar IP
        if not self.config['ip']:
            print("❌ IP requerida para continuar")
            return
        
        print(f"\n🎯 Iniciando análisis de {self.config['ip']}")
        print("="*50)
        
        # 1. Escaneo de puertos
        open_ports = self.scan_ports(self.config['ip'])
        self.results['port_scan'] = open_ports
        
        if not open_ports:
            print("❌ No se encontraron puertos abiertos. Terminando análisis.")
            return
        
        # 2. Prueba de conexiones (si se solicita)
        if options['test_connections']:
            protocol_results = self.test_protocol_connections(
                self.config['ip'], 
                open_ports, 
                self.config['user'], 
                self.config['password']
            )
            self.results['protocol_tests'] = protocol_results
        
        # 3. Generar resumen
        summary = self.generate_summary()
        
        # 4. Guardar resultados completos
        base_path = Path(__file__).parent
        complete_file = self.save_complete_results(base_path)
        
        # 5. Mostrar resumen final
        print(f"\n🎉 ANÁLISIS COMPLETADO")
        print("="*30)
        print(f"🔍 Puertos escaneados: {summary['total_ports_scanned']}")
        print(f"✅ Puertos abiertos: {summary['open_ports_found']}")
        print(f"🔌 Conexiones exitosas: {summary['successful_connections']}")
        print(f"📊 Perfiles extraídos: {summary['profiles_extracted']}")
        print(f"📄 Archivos exportados: {summary['files_exported']}")
        
        if summary['recommendations']:
            print(f"\n💡 RECOMENDACIONES:")
            for rec in summary['recommendations']:
                print(f"   {rec}")
        
        print(f"\n📁 Archivos generados:")
        print(f"   📄 {Path(complete_file).name}")
        for exported_file in self.results['exported_files']:
            print(f"   📄 {Path(exported_file).name}")


def main():
    """Función principal."""
    try:
        analyzer = SterenAnalyzer()
        analyzer.run_analysis()
    except KeyboardInterrupt:
        print("\n⚠️ Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {str(e)}")


if __name__ == "__main__":
    main() 