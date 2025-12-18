import sqlite3
import os

# --- CORRECCIÓN DE RUTA ---
# Obtenemos la ruta absoluta del directorio donde está este archivo (backend/data)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Unimos esa ruta con el nombre del archivo. 
# Resultado: .../tu_proyecto/backend/data/hospital.db
DB_NAME = os.path.join(BASE_DIR, "hospital.db")

class DatabaseConfig:
    @staticmethod
    def get_connection():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def initialize_db():
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        
        # 1. Tabla MÉDICOS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            especialidad TEXT NOT NULL
        );
        """)

        # 2. Tabla DISPONIBILIDAD
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disponibilidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medico_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY(medico_id) REFERENCES medicos(id)
        );
        """)
        
        # 3. Tabla TURNOS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medico_id INTEGER NOT NULL,
            paciente_nombre TEXT NOT NULL,
            paciente_apellido TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY(medico_id) REFERENCES medicos(id)
        );
        """)
        
        conn.commit()
        conn.close()
        print(f"Base de datos inicializada en: {DB_NAME}")

if __name__ == "__main__":
    DatabaseConfig.initialize_db()