"""
Script para limpiar publicaciones huérfanas en la base de datos.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def clean_orphan_publications():
    """Limpia publicaciones sin proceso FFmpeg activo."""
    db_path = Path(__file__).parent / "data" / "camera_data.db"
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Ver todas las publicaciones (activas e inactivas)
        cursor.execute("""
            SELECT publication_id, camera_id, server_id, session_id, created_at, is_active
            FROM camera_publications
            ORDER BY camera_id, created_at DESC
        """)
        
        all_pubs = cursor.fetchall()
        print(f"\nTotal de publicaciones en BD: {len(all_pubs)}")
        
        # Agrupar por camera_id
        camera_pubs = {}
        for pub in all_pubs:
            camera_id = pub['camera_id']
            if camera_id not in camera_pubs:
                camera_pubs[camera_id] = []
            camera_pubs[camera_id].append(pub)
        
        # Mostrar publicaciones por cámara
        print("\nPublicaciones por cámara:")
        for camera_id, pubs in camera_pubs.items():
            print(f"\nCámara {camera_id}:")
            for pub in pubs:
                status = "ACTIVA" if pub['is_active'] else "inactiva"
                print(f"  - ID: {pub['publication_id']}, Server: {pub['server_id']}, "
                      f"Estado: {status}, Creada: {pub['created_at']}")
        
        # Contar publicaciones activas
        active_count = sum(1 for pub in all_pubs if pub['is_active'])
        print(f"\nPublicaciones activas: {active_count}")
        
        if active_count > 0:
            print("\nOpciones:")
            print("1. Desactivar TODAS las publicaciones")
            print("2. Desactivar solo duplicados (mantener la más reciente por cámara)")
            print("3. Eliminar TODAS las publicaciones de la BD")
            print("4. No hacer nada")
            
            response = input("\nSeleccione una opción (1-4): ")
            
            if response == '1':
                # Desactivar todas
                cursor.execute("""
                    UPDATE camera_publications
                    SET is_active = 0, 
                        stop_time = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE is_active = 1
                """)
                conn.commit()
                print(f"Se desactivaron {cursor.rowcount} publicaciones.")
                
            elif response == '2':
                # Desactivar duplicados
                for camera_id, pubs in camera_pubs.items():
                    active_pubs = [p for p in pubs if p['is_active']]
                    if len(active_pubs) > 1:
                        # Ordenar por fecha de creación (más reciente primero)
                        active_pubs.sort(key=lambda p: p['created_at'], reverse=True)
                        # Desactivar todas excepto la más reciente
                        for pub in active_pubs[1:]:
                            cursor.execute("""
                                UPDATE camera_publications
                                SET is_active = 0, 
                                    stop_time = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE publication_id = ?
                            """, (pub['publication_id'],))
                        print(f"Desactivados {len(active_pubs)-1} duplicados para cámara {camera_id}")
                conn.commit()
                
            elif response == '3':
                # Eliminar todas
                confirm = input("¿Está seguro de que desea ELIMINAR TODAS las publicaciones? (escriba 'SI' para confirmar): ")
                if confirm == 'SI':
                    cursor.execute("DELETE FROM camera_publications")
                    conn.commit()
                    print(f"Se eliminaron {cursor.rowcount} publicaciones.")
                else:
                    print("Operación cancelada.")
                    
            else:
                print("No se realizaron cambios.")
        else:
            print("No hay publicaciones activas.")
                
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_orphan_publications()