from enum import Enum
from datetime import datetime
from typing import Optional

class EstadoTurno(Enum):
    PENDIENTE = "PENDIENTE"     # Reservado pero esperando confirmación (opcional)
    CONFIRMADO = "CONFIRMADO"   # Reservado en firme
    ANULADO = "ANULADO"
    FINALIZADO = "FINALIZADO"

class Medico:
    def __init__(self, 
                 nombre: str, 
                 apellido: str, 
                 especialidad: str, 
                 id: Optional[int] = None):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad = especialidad

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "especialidad": self.especialidad
        }

class Disponibilidad:
    def __init__(self, 
                 medico_id: int, 
                 fecha_hora: datetime, 
                 estado: str = "DISPONIBLE", 
                 id: Optional[int] = None):
        self.id = id
        self.medico_id = medico_id
        self.fecha_hora = fecha_hora
        self.estado = estado # 'DISPONIBLE', 'RESERVADO'

class Turno:
    def __init__(self, 
                 medico_id: int, 
                 paciente_nombre: str, 
                 paciente_apellido: str,
                 fecha_hora: datetime, 
                 estado: EstadoTurno = EstadoTurno.CONFIRMADO,
                 id: Optional[int] = None):
        self.id = id
        self.medico_id = medico_id
        self.paciente_nombre = paciente_nombre
        self.paciente_apellido = paciente_apellido
        self.fecha_hora = fecha_hora
        self.estado = estado