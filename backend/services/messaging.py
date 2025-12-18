import queue
from typing import List, Dict
from logic.services import IEventPublisher

class InMemoryMessageBroker(IEventPublisher):
    """
    Broker de Mensajería en Tiempo Real (SSE).
    Mantiene una lista de clientes conectados (suscriptores) y les 
    envía los mensajes inmediatamente cuando ocurren.
    """
    def __init__(self):
        # Diccionario: { medico_id: [Cola1, Cola2, ...] }
        # Un médico puede tener varias pestañas abiertas, por eso una lista de colas.
        self._subscribers: Dict[int, List[queue.Queue]] = {}

    def suscribir(self, medico_id: int) -> queue.Queue:
        """
        Crea una nueva cola para un cliente que acaba de conectarse.
        """
        q = queue.Queue()
        if medico_id not in self._subscribers:
            self._subscribers[medico_id] = []
        self._subscribers[medico_id].append(q)
        print(f"📡 [BROKER] Médico {medico_id} conectado. Suscriptores activos: {len(self._subscribers[medico_id])}")
        return q

    def desuscribir(self, medico_id: int, q: queue.Queue):
        """
        Elimina la cola cuando el cliente cierra la conexión.
        """
        if medico_id in self._subscribers:
            if q in self._subscribers[medico_id]:
                self._subscribers[medico_id].remove(q)
            if not self._subscribers[medico_id]:
                del self._subscribers[medico_id]
        print(f"🔕 [BROKER] Cliente desconectado del Médico {medico_id}")

    def publicar_evento(self, topico: str, mensaje: dict) -> None:
        """
        Distribuye el mensaje a todas las colas activas del médico destinatario.
        """
        destinatario_id = mensaje.get('medico_id')
        
        print(f"📣 [EVENTO] {mensaje['tipo']} para Médico {destinatario_id}")

        if destinatario_id in self._subscribers:
            # Enviar a todas las conexiones abiertas de ese médico
            for q in self._subscribers[destinatario_id]:
                q.put(mensaje)