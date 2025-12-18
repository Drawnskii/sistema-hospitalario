from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

# --- CORRECCIÓN DE IMPORTS (Sin prefijo 'backend.') ---
# Asumimos que ejecutamos main.py desde la carpeta backend/
from logic.models import Turno, Medico, Disponibilidad, EstadoTurno
from logic.dtos import AgendarTurnoDTO, CrearMedicoDTO, AgregarDisponibilidadDTO
from data.repositories import ITurnosRepository, IMedicoRepository, IDisponibilidadRepository

# --- Interfaz para Notificaciones (Pub/Sub) ---
class IEventPublisher(ABC):
    @abstractmethod
    def publicar_evento(self, topico: str, mensaje: dict) -> None:
        pass

# --- SERVICIO DE GESTIÓN MÉDICA ---
class MedicoService:
    def __init__(self, medico_repo: IMedicoRepository, disp_repo: IDisponibilidadRepository):
        self.medico_repo = medico_repo
        self.disp_repo = disp_repo

    def registrar_medico(self, dto: CrearMedicoDTO) -> Medico:
        nuevo_medico = Medico(
            nombre=dto.nombre, 
            apellido=dto.apellido, 
            especialidad=dto.especialidad
        )
        return self.medico_repo.save(nuevo_medico)

    def obtener_todos(self) -> List[Medico]:
        return self.medico_repo.find_all()

    def agregar_disponibilidad(self, dto: AgregarDisponibilidadDTO) -> Disponibilidad:
        # Validar duplicados
        horarios = self.disp_repo.find_by_medico(dto.medico_id)
        for h in horarios:
            if h.fecha_hora == dto.fecha_hora:
                raise ValueError("El médico ya tiene este horario configurado.")

        nueva_disp = Disponibilidad(
            medico_id=dto.medico_id,
            fecha_hora=dto.fecha_hora,
            estado="DISPONIBLE"
        )
        return self.disp_repo.save(nueva_disp)

    def obtener_disponibilidad(self, medico_id: int) -> List[Disponibilidad]:
        return self.disp_repo.find_by_medico(medico_id)


# --- SERVICIO DE AGENDAMIENTO (Turnos) ---
class AgendamientoService:
    def __init__(self, 
                 turno_repo: ITurnosRepository,
                 disp_repo: IDisponibilidadRepository,
                 event_publisher: IEventPublisher):
        self.turno_repo = turno_repo
        self.disp_repo = disp_repo
        self.event_publisher = event_publisher

    def agendar_turno(self, dto: AgendarTurnoDTO) -> Turno:
        # 1. Validar REGLA: Cliente no puede tener cita a la misma hora
        if self.turno_repo.existe_conflicto_paciente(dto.paciente_nombre, dto.paciente_apellido, dto.fecha_hora):
            raise ValueError(f"El paciente {dto.paciente_nombre} {dto.paciente_apellido} ya tiene un turno a las {dto.fecha_hora}.")

        # 2. Validar REGLA: El horario del médico debe estar DISPONIBLE
        horarios = self.disp_repo.find_by_medico(dto.medico_id)
        slot_encontrado = None
        for h in horarios:
            if h.fecha_hora == dto.fecha_hora:
                slot_encontrado = h
                break
        
        if not slot_encontrado:
             raise ValueError("El médico no atiende en ese horario.")
        
        if slot_encontrado.estado != "DISPONIBLE":
            raise ValueError("El horario seleccionado ya no está disponible.")

        # 3. Crear el Turno
        nuevo_turno = Turno(
            medico_id=dto.medico_id,
            paciente_nombre=dto.paciente_nombre,
            paciente_apellido=dto.paciente_apellido,
            fecha_hora=dto.fecha_hora,
            estado=EstadoTurno.CONFIRMADO
        )
        
        # 4. Guardar
        turno_guardado = self.turno_repo.save(nuevo_turno)
        self.disp_repo.marcar_reservada(dto.medico_id, dto.fecha_hora)

        # 5. Notificar
        evento = {
            "tipo": "TURNO_AGENDADO",
            "medico_id": dto.medico_id,
            "paciente": f"{dto.paciente_nombre} {dto.paciente_apellido}",
            "fecha": dto.fecha_hora.isoformat(),
            "mensaje": "Nueva cita agendada"
        }
        self.event_publisher.publicar_evento("notificaciones.medicos", evento)

        return turno_guardado

    def anular_turno(self, turno_id: int) -> None:
        turno = self.turno_repo.find_by_id(turno_id)
        if not turno:
            raise ValueError("Turno no encontrado")
        
        if turno.estado == EstadoTurno.ANULADO:
            return 

        turno.estado = EstadoTurno.ANULADO
        self.turno_repo.save(turno)
        self.disp_repo.marcar_disponible(turno.medico_id, turno.fecha_hora)

        evento = {
            "tipo": "TURNO_CANCELADO",
            "medico_id": turno.medico_id,
            "paciente": f"{turno.paciente_nombre} {turno.paciente_apellido}",
            "fecha": turno.fecha_hora.isoformat(),
            "mensaje": "Cita cancelada por el paciente"
        }
        self.event_publisher.publicar_evento("notificaciones.medicos", evento)

    def listar_por_paciente(self, nombre: str, apellido: str) -> List[Turno]:
        return self.turno_repo.find_by_paciente(nombre, apellido)