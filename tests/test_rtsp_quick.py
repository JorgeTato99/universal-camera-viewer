"""
Script de prueba rápida RTSP para la cámara TP-Link.
Bypasa el escaneo de puertos y prueba directamente las URLs RTSP.
"""

import cv2
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))


def test_rtsp_url(url: str, name: str = "") -> bool:
    """Prueba una URL RTSP y muestra el video si funciona."""
    print(f"\n{'='*60}")
    print(f"Probando: {name}")
    print(f"URL: {url.replace('mUidGT87gMxg8ce!Wxso3Guu8t.3*Q', '****')}")
    
    try:
        # Intentar conectar
        print("Conectando...", end='', flush=True)
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            print(" ❌ No se pudo abrir")
            return False
            
        # Intentar leer un frame
        ret, frame = cap.read()
        if not ret or frame is None:
            print(" ❌ No se pueden leer frames")
            cap.release()
            return False
            
        print(" ✅ CONECTADO!")
        
        # Obtener información
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Resolución: {width}x{height}")
        print(f"FPS: {fps}")
        
        # Mostrar video
        print("\nMostrando video... (presiona 'q' para salir)")
        
        while True:
            ret, frame = cap.read()
            if ret and frame is not None:
                # Redimensionar si es muy grande
                if width > 800:
                    scale = 800 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                    
                cv2.imshow(f"TP-Link Stream - {name}", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("Error leyendo frame")
                break
                
        cv2.destroyAllWindows()
        cap.release()
        
        print(f"\n✅ URL FUNCIONAL: {url}")
        return True
        
    except Exception as e:
        print(f" ❌ Error: {e}")
        return False


def main():
    """Prueba las URLs RTSP más comunes para TP-Link Tapo C520WS."""
    
    print("="*60)
    print(" PRUEBA RÁPIDA RTSP - TP-Link Tapo C520WS")
    print("="*60)
    
    # Datos de la cámara
    ip = "192.168.1.77"
    username = "admin-tato"
    password = "mUidGT87gMxg8ce!Wxso3Guu8t.3*Q"
    port = 554
    
    # URLs a probar (ordenadas por probabilidad)
    urls_to_test = [
        # URLs más comunes para TP-Link Tapo
        {
            'name': 'TP-Link Stream 1',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/stream1"
        },
        {
            'name': 'TP-Link Stream 2',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/stream2"
        },
        {
            'name': 'TP-Link H264 HD',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/h264_hd.sdp"
        },
        {
            'name': 'TP-Link H264 VGA',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/h264_vga.sdp"
        },
        # URLs genéricas comunes
        {
            'name': 'Genérico Live',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/live"
        },
        {
            'name': 'Genérico Video1',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/video1"
        },
        {
            'name': 'Genérico Ch1',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/ch1"
        },
        # URLs sin autenticación (algunas cámaras lo permiten)
        {
            'name': 'Sin Auth Stream1',
            'url': f"rtsp://{ip}:{port}/stream1"
        },
        # URLs con autenticación en la URL de forma diferente
        {
            'name': 'TP-Link MediaProfile',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/MediaInput/h264"
        },
        {
            'name': 'TP-Link Profile1',
            'url': f"rtsp://{username}:{password}@{ip}:{port}/profile1"
        }
    ]
    
    print(f"\nCámara: {ip}")
    print(f"Usuario: {username}")
    print(f"Puerto RTSP: {port}")
    print(f"\nProbando {len(urls_to_test)} URLs diferentes...")
    
    working_urls = []
    
    for url_info in urls_to_test:
        if test_rtsp_url(url_info['url'], url_info['name']):
            working_urls.append(url_info)
            # Preguntar si quiere seguir probando
            response = input("\n¿Desea probar más URLs? (s/n) [n]: ").strip().lower()
            if response != 's':
                break
    
    # Resumen final
    print("\n" + "="*60)
    print(" RESUMEN DE RESULTADOS")
    print("="*60)
    
    if working_urls:
        print(f"\n✅ Se encontraron {len(working_urls)} URLs funcionales:")
        for url_info in working_urls:
            print(f"\n{url_info['name']}:")
            print(f"  {url_info['url']}")
            
        # Actualizar seed_database.py con la URL correcta
        print("\n📝 Para actualizar la base de datos, usa esta URL en seed_database.py:")
        print(f"   url: \"{working_urls[0]['url']}\"")
    else:
        print("\n❌ No se encontraron URLs RTSP funcionales")
        print("\nPosibles causas:")
        print("- Las credenciales pueden ser incorrectas")
        print("- La cámara puede requerir configuración especial")
        print("- El protocolo RTSP puede estar deshabilitado")
        print("- La cámara puede usar un path RTSP no estándar")
        
        print("\n💡 Sugerencias:")
        print("1. Verifica las credenciales en la app de la cámara")
        print("2. Busca en el manual el path RTSP específico")
        print("3. Prueba con VLC: Media → Abrir ubicación de red")
        print("4. Revisa si RTSP está habilitado en la configuración de la cámara")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\nError inesperado: {e}")
        cv2.destroyAllWindows()