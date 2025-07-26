"""
Script para verificar el esquema de la tabla camera_publications.
"""

import sqlite3
from pathlib import Path

def check_schema():
    """Verifica el esquema de la tabla camera_publications."""
    db_path = Path(__file__).parent / "data" / "camera_data.db"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Obtener información de la tabla
        cursor.execute("PRAGMA table_info(camera_publications)")
        columns = cursor.fetchall()
        
        print("Columnas de la tabla camera_publications:")
        print("=" * 50)
        for col in columns:
            print(f"{col[1]:20} {col[2]:15} {col[3]:5} {col[4]:10} {col[5]:5}")
        
        # Verificar si existe la columna is_remote
        column_names = [col[1] for col in columns]
        print("\n" + "=" * 50)
        print(f"¿Existe columna 'is_remote'? {'is_remote' in column_names}")
        
        # Mostrar algunas filas de ejemplo
        print("\nPrimeras 5 filas de camera_publications:")
        print("=" * 50)
        cursor.execute("SELECT * FROM camera_publications LIMIT 5")
        rows = cursor.fetchall()
        
        if rows:
            # Imprimir encabezados
            print(" | ".join(column_names[:5]) + " ...")
            print("-" * 50)
            for row in rows:
                print(" | ".join(str(val)[:15] for val in row[:5]) + " ...")
        else:
            print("No hay filas en la tabla")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()