from dataclasses import dataclass
from datetime import datetime

@dataclass
class CrearMedicoDTO:
    nombre: str
    apellido: str
    especialidad: str

@dataclass
class AgregarDisponibilidadDTO:
    medico_id: int
    fecha_hora: datetime

@dataclass
class AgendarTurnoDTO:
    medico_id: int
    paciente_nombre: str
    paciente_apellido: str
    fecha_hora: datetime