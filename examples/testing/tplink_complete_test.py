"""
Test completo para cámaras TP-Link Tapo (C520WS y compatibles).
Consolida pruebas RTSP y ONVIF con análisis técnico detallado.

Funcionalidades incluidas:
- Test de conectividad de red básica
- Pruebas exhaustivas RTSP (múltiples URLs)
- Análisis ONVIF completo con discovery
- Captura de snapshots y verificación de frames
- Métricas de rendimiento y compatibilidad
- Reporte técnico detallado

Compatible con: TP-Link Tapo C520WS, C200, C210 y modelos similares
"""

import sys
import time
import logging
import socket
import cv2
import os
from datetime import datetime
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from dotenv import load_dotenv
    from onvif import ONVIFCamera
    import requests
    from requests.auth import HTTPDigestAuth
except ImportError as e:
    print(f"❌ Error importando dependencias: {e}")
    print("Instala con: pip install python-dotenv onvif-zeep requests opencv-python")
    sys.exit(1)


def setup_logging():
    """Configura logging para tests de TP-Link."""
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "tplink_complete_test.log"
    
    # Limpiar configuración existente
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    print(f"📝 Logs guardándose en: {log_file}")


class TPLinkCompleteTester:
    """
    Tester completo para cámaras TP-Link Tapo.
    Incluye pruebas RTSP, ONVIF y análisis técnico.
    """
    
    def __init__(self):
        """Inicializar configuración desde .env"""
        load_dotenv()
        
        self.camera_ip = os.getenv('TP_LINK_IP', '192.168.1.77')
        self.username = os.getenv('TP_LINK_USER', 'admin-tato')
        self.password = os.getenv('TP_LINK_PASSWORD', '')
        self.rtsp_port = int(os.getenv('RTSP_PORT', '554'))
        self.onvif_port = int(os.getenv('ONVIF_PORT', '2020'))
        
        self.logger = logging.getLogger(__name__)
        
        # Resultados de tests
        self.results = {
            'device_info': {},
            'network_tests': {},
            'rtsp_tests': {},
            'onvif_tests': {},
            'performance': {},
            'recommendations': [],
            'errors': []
        }
        
        self.logger.info(f"=== INICIANDO TEST COMPLETO TP-LINK ===")
        self.logger.info(f"IP: {self.camera_ip}, Usuario: {self.username}")
        
        if not self.password:
            self.logger.error("❌ No se encontró TP_LINK_PASSWORD en .env")
            raise ValueError("Configurar TP_LINK_PASSWORD en archivo .env")
    
    def test_network_connectivity(self) -> dict:
        """
        Verificar conectividad de red básica.
        
        Returns:
            Diccionario con resultados de conectividad
        """
        print("\n" + "="*60)
        print("🔍 TEST DE CONECTIVIDAD DE RED")
        print("="*60)
        
        network_results = {
            'ping_ok': False,
            'http_ok': False,
            'rtsp_port_ok': False,
            'onvif_port_ok': False,
            'response_times': {}
        }
        
        # Test puertos críticos
        test_ports = [
            (80, 'HTTP'),
            (self.rtsp_port, 'RTSP'),
            (self.onvif_port, 'ONVIF'),
            (8000, 'HTTP-Alt'),
            (8080, 'HTTP-8080')
        ]
        
        for port, protocol in test_ports:
            start_time = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((self.camera_ip, port))
                response_time = time.time() - start_time
                sock.close()
                
                if result == 0:
                    print(f"✅ {protocol} puerto {port}: OK ({response_time:.2f}s)")
                    network_results[f'{protocol.lower()}_port_ok'] = True
                    network_results['response_times'][protocol] = response_time
                    self.logger.info(f"Puerto {port} ({protocol}): Conectividad OK - {response_time:.2f}s")
                else:
                    print(f"❌ {protocol} puerto {port}: Sin conectividad")
                    self.logger.warning(f"Puerto {port} ({protocol}): Sin conectividad")
                    
            except Exception as e:
                print(f"❌ {protocol} puerto {port}: Error - {str(e)}")
                self.logger.error(f"Puerto {port} ({protocol}): Error - {str(e)}")
        
        # Test HTTP básico
        try:
            response = requests.get(f"http://{self.camera_ip}", timeout=5)
            network_results['http_ok'] = True
            print("✅ HTTP responde correctamente")
            self.logger.info("HTTP responde correctamente")
        except requests.exceptions.Timeout:
            print("⚠️ HTTP timeout - Puerto abierto pero sin respuesta")
            self.logger.warning("HTTP timeout")
        except requests.exceptions.ConnectionError:
            print("❌ HTTP no disponible")
            self.logger.warning("HTTP no disponible")
        except Exception as e:
            print(f"ℹ️ HTTP test: {str(e)}")
            self.logger.info(f"HTTP test: {str(e)}")
        
        self.results['network_tests'] = network_results
        return network_results
    
    def test_rtsp_protocols(self) -> dict:
        """
        Probar diferentes URLs RTSP para TP-Link Tapo.
        
        Returns:
            Diccionario con resultados RTSP
        """
        print("\n" + "="*60)
        print("🎥 TEST DE PROTOCOLOS RTSP")
        print("="*60)
        
        rtsp_results = {
            'successful_urls': [],
            'failed_urls': [],
            'best_quality': None,
            'performance_metrics': {}
        }
        
        # URLs RTSP comunes para TP-Link Tapo
        test_urls = [
            f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/stream1",
            f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/stream2",
            f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/live",
            f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/h264_stream",
            f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{self.camera_ip}:{self.rtsp_port}/stream1",  # Sin autenticación
        ]
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n🔍 Probando URL {i}: rtsp://.../...")
            safe_url = url.replace(self.password, '***')
            self.logger.info(f"Probando RTSP URL {i}: {safe_url}")
            
            try:
                start_time = time.time()
                cap = cv2.VideoCapture(url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    connection_time = time.time() - start_time
                    
                    # Obtener primer frame
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        print(f"   ✅ Conexión exitosa!")
                        print(f"      Resolución: {width}x{height}")
                        print(f"      FPS: {fps}")
                        print(f"      Tiempo conexión: {connection_time:.2f}s")
                        
                        # Guardar snapshot
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        snapshot_dir = Path(__file__).parent.parent / "logs" / "snapshots"
                        snapshot_dir.mkdir(exist_ok=True)
                        snapshot_path = snapshot_dir / f"tplink_rtsp_{timestamp}_url{i}.jpg"
                        cv2.imwrite(str(snapshot_path), frame)
                        
                        # Test de estabilidad con múltiples frames
                        frames_captured = 0
                        frame_times = []
                        
                        for j in range(10):
                            frame_start = time.time()
                            ret, frame = cap.read()
                            if ret:
                                frames_captured += 1
                                frame_times.append(time.time() - frame_start)
                            time.sleep(0.1)
                        
                        avg_frame_time = sum(frame_times) / len(frame_times) if frame_times else 0
                        
                        url_info = {
                            'url': safe_url,
                            'resolution': f"{width}x{height}",
                            'fps': fps,
                            'connection_time': connection_time,
                            'frames_captured': frames_captured,
                            'avg_frame_time': avg_frame_time,
                            'snapshot_path': str(snapshot_path)
                        }
                        
                        rtsp_results['successful_urls'].append(url_info)
                        
                        print(f"      Frames capturados: {frames_captured}/10")
                        print(f"      Snapshot guardado: {snapshot_path}")
                        
                        self.logger.info(f"RTSP URL {i} exitosa: {width}x{height} @ {fps}fps")
                    else:
                        print("   ⚠️ Conexión establecida pero sin frames")
                        rtsp_results['failed_urls'].append({'url': safe_url, 'reason': 'Sin frames'})
                        self.logger.warning(f"RTSP URL {i}: Conexión sin frames")
                else:
                    print("   ❌ No se pudo abrir stream")
                    rtsp_results['failed_urls'].append({'url': safe_url, 'reason': 'No se pudo abrir'})
                    self.logger.warning(f"RTSP URL {i}: No se pudo abrir stream")
                
                cap.release()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                rtsp_results['failed_urls'].append({'url': safe_url, 'reason': str(e)})
                self.logger.error(f"RTSP URL {i}: Error - {str(e)}")
            
            time.sleep(1)  # Pausa entre intentos
        
        # Determinar mejor calidad
        if rtsp_results['successful_urls']:
            best_url = max(rtsp_results['successful_urls'], 
                          key=lambda x: int(x['resolution'].split('x')[0]) * int(x['resolution'].split('x')[1]))
            rtsp_results['best_quality'] = best_url
            
            print(f"\n🏆 Mejor calidad encontrada:")
            print(f"   URL: {best_url['url']}")
            print(f"   Resolución: {best_url['resolution']}")
            print(f"   FPS: {best_url['fps']}")
        
        self.results['rtsp_tests'] = rtsp_results
        return rtsp_results
    
    def test_onvif_protocol(self) -> dict:
        """
        Probar protocolo ONVIF completo.
        
        Returns:
            Diccionario con resultados ONVIF
        """
        print("\n" + "="*60)
        print("🔧 TEST DE PROTOCOLO ONVIF")
        print("="*60)
        
        onvif_results = {
            'connection_ok': False,
            'device_info': {},
            'services': [],
            'profiles': [],
            'capabilities': [],
            'snapshot_ok': False,
            'ptz_available': False,
            'connection_time': 0
        }
        
        # Probar diferentes puertos ONVIF
        onvif_ports = [2020, 80, 8080, 8000]
        
        for port in onvif_ports:
            print(f"\n🔍 Probando ONVIF puerto: {port}")
            self.logger.info(f"Probando ONVIF puerto {port}")
            
            try:
                start_time = time.time()
                
                # Crear cliente ONVIF
                cam = ONVIFCamera(
                    self.camera_ip, 
                    port, 
                    self.username, 
                    self.password
                )
                
                # Test información del dispositivo
                device_service = cam.create_devicemgmt_service()
                device_info = device_service.GetDeviceInformation()
                
                connection_time = time.time() - start_time
                onvif_results['connection_ok'] = True
                onvif_results['connection_time'] = connection_time
                
                print("   ✅ Conexión ONVIF exitosa!")
                print(f"      Tiempo conexión: {connection_time:.2f}s")
                print(f"      Fabricante: {device_info.Manufacturer}")
                print(f"      Modelo: {device_info.Model}")
                print(f"      Firmware: {device_info.FirmwareVersion}")
                print(f"      Serie: {device_info.SerialNumber}")
                
                onvif_results['device_info'] = {
                    'manufacturer': device_info.Manufacturer,
                    'model': device_info.Model,
                    'firmware': device_info.FirmwareVersion,
                    'serial': device_info.SerialNumber
                }
                
                self.logger.info(f"ONVIF puerto {port} exitoso: {device_info.Manufacturer} {device_info.Model}")
                
                # Test servicios de media
                try:
                    media_service = cam.create_media_service()
                    profiles = media_service.GetProfiles()
                    
                    print(f"      Perfiles disponibles: {len(profiles)}")
                    
                    profile_info = []
                    for i, profile in enumerate(profiles):
                        profile_data = {
                            'name': profile.Name,
                            'token': profile.token
                        }
                        profile_info.append(profile_data)
                        print(f"        Perfil {i+1}: {profile.Name}")
                        
                        # Test snapshot URI
                        try:
                            snapshot_uri = media_service.GetSnapshotUri({'ProfileToken': profile.token})
                            print(f"          Snapshot URI disponible")
                            onvif_results['snapshot_ok'] = True
                            self.logger.info(f"Snapshot URI disponible para perfil {profile.Name}")
                        except Exception as e:
                            self.logger.warning(f"Snapshot URI error para perfil {profile.Name}: {str(e)}")
                    
                    onvif_results['profiles'] = profile_info
                    
                except Exception as e:
                    print(f"      ⚠️ Error en servicios de media: {str(e)}")
                    self.logger.warning(f"Error servicios media ONVIF: {str(e)}")
                
                # Test servicios PTZ
                try:
                    ptz_service = cam.create_ptz_service()
                    # Si llegamos aquí, PTZ está disponible
                    onvif_results['ptz_available'] = True
                    print("      ✅ Servicios PTZ disponibles")
                    self.logger.info("Servicios PTZ disponibles")
                except Exception as e:
                    print("      ℹ️ PTZ no disponible (normal para cámaras fijas)")
                    self.logger.info("PTZ no disponible")
                
                # Test capacidades
                try:
                    capabilities = device_service.GetCapabilities()
                    caps_info = []
                    if hasattr(capabilities, 'Media') and capabilities.Media:
                        caps_info.append('Media')
                    if hasattr(capabilities, 'PTZ') and capabilities.PTZ:
                        caps_info.append('PTZ')
                    if hasattr(capabilities, 'Events') and capabilities.Events:
                        caps_info.append('Events')
                    
                    onvif_results['capabilities'] = caps_info
                    print(f"      Capacidades: {', '.join(caps_info)}")
                    self.logger.info(f"Capacidades ONVIF: {', '.join(caps_info)}")
                    
                except Exception as e:
                    self.logger.warning(f"Error obteniendo capacidades: {str(e)}")
                
                break  # Salir del loop si conexión exitosa
                
            except Exception as e:
                print(f"   ❌ Error puerto {port}: {str(e)}")
                self.logger.warning(f"ONVIF puerto {port} error: {str(e)}")
                continue
        
        if not onvif_results['connection_ok']:
            print("\n❌ No se pudo establecer conexión ONVIF en ningún puerto")
            self.logger.error("No se pudo establecer conexión ONVIF")
        
        self.results['onvif_tests'] = onvif_results
        return onvif_results
    
    def analyze_performance(self) -> dict:
        """
        Analizar el rendimiento general de la cámara.
        
        Returns:
            Diccionario con métricas de rendimiento
        """
        print("\n" + "="*60)
        print("📊 ANÁLISIS DE RENDIMIENTO")
        print("="*60)
        
        performance = {
            'overall_score': 0,
            'connectivity_score': 0,
            'protocol_compatibility': 0,
            'recommended_protocol': None,
            'performance_notes': []
        }
        
        # Evaluar conectividad (30% del score)
        network_score = 0
        if self.results.get('network_tests', {}).get('http_ok'): network_score += 25
        if self.results.get('network_tests', {}).get('rtsp_port_ok'): network_score += 25
        if self.results.get('network_tests', {}).get('onvif_port_ok'): network_score += 50
        
        performance['connectivity_score'] = network_score
        
        # Evaluar compatibilidad de protocolos (70% del score)
        protocol_score = 0
        rtsp_working = len(self.results.get('rtsp_tests', {}).get('successful_urls', []))
        onvif_working = self.results.get('onvif_tests', {}).get('connection_ok', False)
        
        if rtsp_working > 0:
            protocol_score += min(rtsp_working * 20, 60)  # Máximo 60 puntos por RTSP
        
        if onvif_working:
            protocol_score += 40  # 40 puntos por ONVIF
        
        performance['protocol_compatibility'] = min(protocol_score, 100)
        
        # Score general
        performance['overall_score'] = int((network_score * 0.3) + (protocol_score * 0.7))
        
        # Recomendación de protocolo
        if onvif_working and rtsp_working > 0:
            performance['recommended_protocol'] = 'ONVIF'
            performance['performance_notes'].append('ONVIF y RTSP disponibles - ONVIF recomendado')
        elif onvif_working:
            performance['recommended_protocol'] = 'ONVIF'
            performance['performance_notes'].append('Solo ONVIF disponible')
        elif rtsp_working > 0:
            performance['recommended_protocol'] = 'RTSP'
            performance['performance_notes'].append('Solo RTSP disponible')
        else:
            performance['recommended_protocol'] = None
            performance['performance_notes'].append('Ningún protocolo funcional detectado')
        
        print(f"📈 Score General: {performance['overall_score']}/100")
        print(f"📡 Conectividad: {performance['connectivity_score']}/100")
        print(f"🔌 Protocolos: {performance['protocol_compatibility']}/100")
        print(f"💡 Protocolo Recomendado: {performance['recommended_protocol'] or 'Ninguno'}")
        
        for note in performance['performance_notes']:
            print(f"   • {note}")
        
        self.results['performance'] = performance
        return performance
    
    def generate_recommendations(self) -> list:
        """
        Generar recomendaciones específicas basadas en los resultados.
        
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Recomendaciones basadas en conectividad
        if not self.results.get('network_tests', {}).get('http_ok'):
            recommendations.append("Verificar que la cámara esté encendida y conectada a la red")
        
        # Recomendaciones basadas en RTSP
        rtsp_successful = len(self.results.get('rtsp_tests', {}).get('successful_urls', []))
        if rtsp_successful == 0:
            recommendations.append("RTSP no funcional - Verificar que RTSP esté habilitado en la cámara")
            recommendations.append("Confirmar credenciales correctas para RTSP")
        elif rtsp_successful > 1:
            recommendations.append(f"RTSP funcional con {rtsp_successful} URLs - Usar la de mejor calidad")
        
        # Recomendaciones basadas en ONVIF
        if not self.results.get('onvif_tests', {}).get('connection_ok'):
            recommendations.append("ONVIF no disponible - Verificar que esté habilitado en configuración")
            recommendations.append("Algunos modelos Tapo requieren activación manual de ONVIF")
        else:
            recommendations.append("ONVIF funcional - Protocolo recomendado para integración")
        
        # Recomendaciones de configuración
        best_rtsp = self.results.get('rtsp_tests', {}).get('best_quality')
        if best_rtsp:
            recommendations.append(f"Usar RTSP: {best_rtsp['url']} para mejor calidad")
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def generate_final_report(self):
        """Generar reporte final completo."""
        print("\n" + "="*80)
        print("📋 REPORTE FINAL - TP-LINK TAPO TEST COMPLETO")
        print("="*80)
        
        # Información general
        print(f"\n🎯 DISPOSITIVO ANALIZADO:")
        print(f"   IP: {self.camera_ip}")
        print(f"   Usuario: {self.username}")
        
        device_info = self.results.get('onvif_tests', {}).get('device_info', {})
        if device_info:
            print(f"   Fabricante: {device_info.get('manufacturer', 'N/A')}")
            print(f"   Modelo: {device_info.get('model', 'N/A')}")
            print(f"   Firmware: {device_info.get('firmware', 'N/A')}")
        
        # Resumen de conectividad
        network = self.results.get('network_tests', {})
        print(f"\n🌐 CONECTIVIDAD:")
        print(f"   HTTP (80): {'✅' if network.get('http_ok') else '❌'}")
        print(f"   RTSP ({self.rtsp_port}): {'✅' if network.get('rtsp_port_ok') else '❌'}")
        print(f"   ONVIF ({self.onvif_port}): {'✅' if network.get('onvif_port_ok') else '❌'}")
        
        # Resumen RTSP
        rtsp = self.results.get('rtsp_tests', {})
        successful_rtsp = len(rtsp.get('successful_urls', []))
        print(f"\n🎥 RTSP:")
        print(f"   URLs funcionales: {successful_rtsp}")
        if rtsp.get('best_quality'):
            best = rtsp['best_quality']
            print(f"   Mejor calidad: {best['resolution']} @ {best['fps']} FPS")
        
        # Resumen ONVIF
        onvif = self.results.get('onvif_tests', {})
        print(f"\n🔧 ONVIF:")
        print(f"   Conexión: {'✅' if onvif.get('connection_ok') else '❌'}")
        if onvif.get('profiles'):
            print(f"   Perfiles: {len(onvif['profiles'])}")
        print(f"   Snapshots: {'✅' if onvif.get('snapshot_ok') else '❌'}")
        print(f"   PTZ: {'✅' if onvif.get('ptz_available') else '❌'}")
        
        # Score y recomendaciones
        performance = self.results.get('performance', {})
        print(f"\n📊 EVALUACIÓN:")
        print(f"   Score General: {performance.get('overall_score', 0)}/100")
        print(f"   Protocolo Recomendado: {performance.get('recommended_protocol', 'Ninguno')}")
        
        print(f"\n💡 RECOMENDACIONES:")
        for rec in self.results.get('recommendations', []):
            print(f"   • {rec}")
        
        # Configuración sugerida
        print(f"\n⚙️ CONFIGURACIÓN SUGERIDA PARA PROYECTO:")
        if performance.get('recommended_protocol') == 'ONVIF':
            print(f"   Protocolo: ONVIF")
            print(f"   IP: {self.camera_ip}")
            print(f"   Usuario: {self.username}")
            print(f"   Puerto: {self.onvif_port}")
        elif performance.get('recommended_protocol') == 'RTSP':
            best = rtsp.get('best_quality')
            if best:
                print(f"   Protocolo: RTSP")
                print(f"   URL: {best['url']}")
                print(f"   Resolución: {best['resolution']}")
        
        print(f"\n✅ Test completado exitosamente")
        self.logger.info("Test completo TP-Link finalizado")
    
    def run_complete_test(self):
        """Ejecutar todos los tests en secuencia."""
        print("🚀 INICIANDO TEST COMPLETO TP-LINK TAPO")
        print("="*80)
        
        try:
            # 1. Test de conectividad
            self.test_network_connectivity()
            
            # 2. Test RTSP
            self.test_rtsp_protocols()
            
            # 3. Test ONVIF
            self.test_onvif_protocol()
            
            # 4. Análisis de rendimiento
            self.analyze_performance()
            
            # 5. Generar recomendaciones
            self.generate_recommendations()
            
            # 6. Reporte final
            self.generate_final_report()
            
        except Exception as e:
            print(f"\n❌ Error durante el test: {str(e)}")
            self.logger.error(f"Error durante test completo: {str(e)}")
            raise


def main():
    """Función principal."""
    setup_logging()
    
    try:
        tester = TPLinkCompleteTester()
        tester.run_complete_test()
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrumpido por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        print("\n🔧 Sugerencias:")
        print("1. Verificar archivo .env con TP_LINK_* configuraciones")
        print("2. Confirmar conectividad de red con la cámara")
        print("3. Revisar logs para más detalles")
        
    finally:
        print("\n📝 Revisar logs en examples/logs/ para información detallada")


if __name__ == "__main__":
    main() 