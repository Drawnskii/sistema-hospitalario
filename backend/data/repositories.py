import sqlite3
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from data.database import DatabaseConfig

# Estos modelos serán actualizados/creados en el próximo paso (Capa Logic)
# Usamos 'import' dentro de los métodos o strings para evitar errores circulares por ahora
# pero idealmente deberían estar arriba.
from logic.models import Turno, Medico, Disponibilidad

# --- REPOSITORIO DE MÉDICOS ---
class IMedicoRepository(ABC):
    @abstractmethod
    def save(self, medico: Medico) -> Medico: pass
    @abstractmethod
    def find_all(self) -> List[Medico]: pass
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Medico]: pass

class SqliteMedicoRepository(IMedicoRepository):
    def save(self, medico: Medico) -> Medico:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        if medico.id is None:
            sql = "INSERT INTO medicos (nombre, apellido, especialidad) VALUES (?, ?, ?)"
            cursor.execute(sql, (medico.nombre, medico.apellido, medico.especialidad))
            medico.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return medico

    def find_all(self) -> List[Medico]:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medicos")
        rows = cursor.fetchall()
        conn.close()
        # Mapeo simple
        return [Medico(id=r['id'], nombre=r['nombre'], apellido=r['apellido'], especialidad=r['especialidad']) for r in rows]

    def find_by_id(self, id: int) -> Optional[Medico]:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medicos WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Medico(id=row['id'], nombre=row['nombre'], apellido=row['apellido'], especialidad=row['especialidad'])
        return None


# --- REPOSITORIO DE DISPONIBILIDAD ---
class IDisponibilidadRepository(ABC):
    @abstractmethod
    def save(self, disponibilidad: Disponibilidad) -> Disponibilidad: pass
    @abstractmethod
    def find_by_medico(self, medico_id: int) -> List[Disponibilidad]: pass
    @abstractmethod
    def marcar_reservada(self, medico_id: int, fecha: datetime) -> None: pass
    @abstractmethod
    def marcar_disponible(self, medico_id: int, fecha: datetime) -> None: pass

class SqliteDisponibilidadRepository(IDisponibilidadRepository):
    def save(self, disp: Disponibilidad) -> Disponibilidad:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        fecha_str = disp.fecha_hora.isoformat()
        
        sql = "INSERT INTO disponibilidad (medico_id, fecha_hora, estado) VALUES (?, ?, ?)"
        cursor.execute(sql, (disp.medico_id, fecha_str, disp.estado))
        disp.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return disp

    def find_by_medico(self, medico_id: int) -> List[Disponibilidad]:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        # Traemos solo las disponibles o todas según se necesite. 
        # El frontend filtrará, pero aquí traemos todo el calendario del médico.
        sql = "SELECT * FROM disponibilidad WHERE medico_id = ? ORDER BY fecha_hora ASC"
        cursor.execute(sql, (medico_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Disponibilidad(id=r['id'], medico_id=r['medico_id'], fecha_hora=datetime.fromisoformat(r['fecha_hora']), estado=r['estado']) for r in rows]

    def marcar_reservada(self, medico_id: int, fecha: datetime) -> None:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        fecha_str = fecha.isoformat()
        sql = "UPDATE disponibilidad SET estado = 'RESERVADO' WHERE medico_id = ? AND fecha_hora = ?"
        cursor.execute(sql, (medico_id, fecha_str))
        conn.commit()
        conn.close()

    def marcar_disponible(self, medico_id: int, fecha: datetime) -> None:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        fecha_str = fecha.isoformat()
        sql = "UPDATE disponibilidad SET estado = 'DISPONIBLE' WHERE medico_id = ? AND fecha_hora = ?"
        cursor.execute(sql, (medico_id, fecha_str))
        conn.commit()
        conn.close()


# --- REPOSITORIO DE TURNOS (Actualizado) ---
class ITurnosRepository(ABC):
    @abstractmethod
    def save(self, turno: Turno) -> Turno: pass
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Turno]: pass
    @abstractmethod
    def find_by_paciente(self, nombre: str, apellido: str) -> List[Turno]: pass
    @abstractmethod
    def delete_by_id(self, id: int) -> None: pass
    
    # Nuevas validaciones
    @abstractmethod
    def existe_conflicto_paciente(self, nombre: str, apellido: str, fecha: datetime) -> bool: pass
    @abstractmethod
    def existe_conflicto_medico(self, medico_id: int, fecha: datetime) -> bool: pass

class SqliteTurnosRepository(ITurnosRepository):
    def save(self, turno: Turno) -> Turno:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        fecha_str = turno.fecha_hora.isoformat()
        
        # Mapeo seguro del Enum a string
        estado_str = turno.estado.value if hasattr(turno.estado, 'value') else turno.estado

        if turno.id is None:
            sql = """
                INSERT INTO turnos (medico_id, paciente_nombre, paciente_apellido, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (turno.medico_id, turno.paciente_nombre, turno.paciente_apellido, fecha_str, estado_str))
            turno.id = cursor.lastrowid
        else:
            sql = """
                UPDATE turnos 
                SET medico_id=?, paciente_nombre=?, paciente_apellido=?, fecha_hora=?, estado=?
                WHERE id=?
            """
            cursor.execute(sql, (turno.medico_id, turno.paciente_nombre, turno.paciente_apellido, fecha_str, estado_str, turno.id))

        conn.commit()
        conn.close()
        return turno

    def find_by_id(self, id: int) -> Optional[Turno]:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM turnos WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            from logic.models import EstadoTurno # Import diferido
            return Turno(
                id=row['id'],
                medico_id=row['medico_id'],
                paciente_nombre=row['paciente_nombre'],
                paciente_apellido=row['paciente_apellido'],
                fecha_hora=datetime.fromisoformat(row['fecha_hora']),
                estado=EstadoTurno(row['estado'])
            )
        return None

    def find_by_paciente(self, nombre: str, apellido: str) -> List[Turno]:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM turnos WHERE paciente_nombre = ? AND paciente_apellido = ? ORDER BY fecha_hora DESC"
        cursor.execute(sql, (nombre, apellido))
        rows = cursor.fetchall()
        conn.close()
        from logic.models import EstadoTurno
        return [
            Turno(
                id=r['id'],
                medico_id=r['medico_id'],
                paciente_nombre=r['paciente_nombre'],
                paciente_apellido=r['paciente_apellido'],
                fecha_hora=datetime.fromisoformat(r['fecha_hora']),
                estado=EstadoTurno(r['estado'])
            ) for r in rows
        ]

    def delete_by_id(self, id: int) -> None:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM turnos WHERE id = ?", (id,))
        conn.commit()
        conn.close()

    # REGLA: Un cliente no puede tener cita a la misma hora (aunque sea otro médico)
    def existe_conflicto_paciente(self, nombre: str, apellido: str, fecha: datetime) -> bool:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        fecha_str = fecha.isoformat()
        # Buscamos turnos activos (no anulados)
        sql = """
            SELECT count(*) FROM turnos 
            WHERE paciente_nombre = ? AND paciente_apellido = ? 
            AND fecha_hora = ? AND estado != 'ANULADO'
        """
        cursor.execute(sql, (nombre, apellido, fecha_str))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    # REGLA: Un horario de un médico no puede tener más de un cliente
    def existe_conflicto_medico(self, medico_id: int, fecha: datetime) -> bool:
        conn = DatabaseConfig.get_connection()
        cursor = conn.cursor()
        fecha_str = fecha.isoformat()
        sql = """
            SELECT count(*) FROM turnos 
            WHERE medico_id = ? AND fecha_hora = ? AND estado != 'ANULADO'
        """
        cursor.execute(sql, (medico_id, fecha_str))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0