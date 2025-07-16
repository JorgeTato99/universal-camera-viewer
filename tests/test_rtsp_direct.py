"""
Script simple para probar conexión RTSP directa.

Útil para verificar rápidamente si las credenciales y URL funcionan.
"""

import cv2
import sys
from typing import Optional


def test_rtsp_url(url: str) -> bool:
    """
    Prueba una URL RTSP específica.
    
    Args:
        url: URL RTSP completa con credenciales
        
    Returns:
        True si la conexión fue exitosa
    """
    print(f"\nProbando URL RTSP...")
    print(f"URL (sin credenciales): {sanitize_url(url)}")
    
    try:
        # Configurar timeout más corto para pruebas rápidas
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        
        # Configurar propiedades
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Verificar si se abrió
        if not cap.isOpened():
            print("❌ No se pudo abrir el stream")
            return False
        
        print("✓ Stream abierto exitosamente")
        
        # Intentar leer un frame
        ret, frame = cap.read()
        if not ret or frame is None:
            print("❌ No se pueden leer frames")
            cap.release()
            return False
        
        # Obtener información del stream
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"✓ Stream funcionando correctamente")
        print(f"  - Resolución: {width}x{height}")
        print(f"  - FPS: {fps}")
        
        # Mostrar el frame por 5 segundos
        print("\nMostrando preview del stream...")
        cv2.imshow("Test RTSP Stream", frame)
        print("Presiona cualquier tecla para cerrar...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def sanitize_url(url: str) -> str:
    """Oculta credenciales en la URL."""
    if '@' in url:
        parts = url.split('@')
        if len(parts) == 2:
            protocol_part = parts[0].split('://')
            if len(protocol_part) == 2:
                return f"{protocol_part[0]}://****:****@{parts[1]}"
    return url


def build_dahua_url(ip: str, username: str, password: str, 
                    port: int = 554, channel: int = 1, 
                    subtype: int = 0) -> str:
    """
    Construye URL RTSP para cámaras Dahua.
    
    Args:
        ip: IP de la cámara
        username: Usuario
        password: Contraseña
        port: Puerto RTSP (default 554)
        channel: Canal (default 1)
        subtype: 0=principal, 1=secundario
        
    Returns:
        URL RTSP completa
    """
    return f"rtsp://{username}:{password}@{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}"


def main():
    """Función principal."""
    print("=" * 50)
    print(" PRUEBA DIRECTA DE CONEXIÓN RTSP")
    print("=" * 50)
    
    # Pedir datos de conexión
    print("\nIngrese los datos de conexión:")
    ip = input("IP de la cámara [192.168.1.172]: ").strip() or "192.168.1.172"
    username = input("Usuario [admin]: ").strip() or "admin"
    password = input("Contraseña: ").strip()
    
    if not password:
        print("❌ La contraseña es requerida")
        return
    
    # Preguntar qué probar
    print("\n¿Qué desea probar?")
    print("1. URL Dahua principal (HD)")
    print("2. URL Dahua secundaria (SD)")
    print("3. URL personalizada")
    print("4. Probar múltiples URLs comunes")
    
    choice = input("\nSeleccione opción (1-4) [1]: ").strip() or "1"
    
    if choice == "1":
        url = build_dahua_url(ip, username, password, subtype=0)
        test_rtsp_url(url)
        
    elif choice == "2":
        url = build_dahua_url(ip, username, password, subtype=1)
        test_rtsp_url(url)
        
    elif choice == "3":
        print("\nIngrese la URL RTSP completa:")
        print("Ejemplo: rtsp://user:pass@192.168.1.172:554/path")
        url = input("URL: ").strip()
        if url:
            test_rtsp_url(url)
        else:
            print("❌ URL vacía")
            
    elif choice == "4":
        # Probar múltiples URLs comunes
        urls = [
            # Dahua
            build_dahua_url(ip, username, password, subtype=0),
            build_dahua_url(ip, username, password, subtype=1),
            f"rtsp://{username}:{password}@{ip}:554/live",
            # Hikvision
            f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/101",
            f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/102",
            # Genérico
            f"rtsp://{username}:{password}@{ip}:554/stream1",
            f"rtsp://{username}:{password}@{ip}:554/stream2",
            f"rtsp://{username}:{password}@{ip}:554/video1",
            f"rtsp://{username}:{password}@{ip}:554/ch01.264",
        ]
        
        print(f"\nProbando {len(urls)} URLs diferentes...")
        for i, url in enumerate(urls, 1):
            print(f"\n--- Prueba {i}/{len(urls)} ---")
            if test_rtsp_url(url):
                print(f"\n✓ URL funcionando: {sanitize_url(url)}")
                break
        else:
            print("\n❌ Ninguna URL funcionó")
    
    print("\n" + "=" * 50)
    print(" Prueba finalizada")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")