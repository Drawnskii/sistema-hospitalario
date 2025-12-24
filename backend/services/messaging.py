import queue
import json
import threading
import pika
from typing import Dict
from logic.services import IEventPublisher

class RabbitMQMessageBroker(IEventPublisher):
    """
    Adapter para RabbitMQ.
    Implementa el patrón Pub/Sub usando un Exchange tipo 'Topic'.
    
    Arquitectura:
    - Publicar: Envía mensaje al Exchange 'hospital_events' con routing_key 'medico.{id}'
    - Suscribir: Crea una cola temporal en RabbitMQ, la une al Exchange y 
      usa un hilo para pasar mensajes a la queue.Queue de Python.
    """

    EXCHANGE_NAME = 'hospital_events'

    def __init__(self, host='localhost'):
        self.host = host
        # Mantenemos referencia a los hilos de escucha para poder cerrarlos si es necesario
        # Diccionario: { medico_id: [ { 'queue': python_queue, 'thread': thread_obj, 'stop_event': event } ] }
        self._active_subscriptions: Dict[int, list] = {}

    def _get_connection(self):
        """Crea una conexión nueva a RabbitMQ."""
        params = pika.ConnectionParameters(host=self.host)
        return pika.BlockingConnection(params)

    def publicar_evento(self, topico: str, mensaje: dict) -> None:
        """
        Abre conexión momentánea, publica al Exchange y cierra.
        """
        destinatario_id = mensaje.get('medico_id')
        routing_key = f"medico.{destinatario_id}"
        
        try:
            connection = self._get_connection()
            channel = connection.channel()
            
            # Declarar el exchange (si no existe) tipo 'topic'
            channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type='topic')
            
            # Publicar
            body = json.dumps(mensaje)
            channel.basic_publish(
                exchange=self.EXCHANGE_NAME,
                routing_key=routing_key,
                body=body
            )
            
            print(f"📣 [RABBITMQ] Enviado a {routing_key}: {mensaje['tipo']}")
            connection.close()
        except Exception as e:
            print(f"❌ [RABBITMQ] Error publicando: {e}")

    def suscribir(self, medico_id: int) -> queue.Queue:
        """
        Inicia un hilo que escucha a RabbitMQ y vuelca los datos en una cola thread-safe de Python.
        Devuelve la cola de Python para que el controlador la consuma (SSE).
        """
        python_q = queue.Queue()
        stop_event = threading.Event()
        
        # Iniciamos el consumidor en un hilo separado para no bloquear el servidor web
        listener_thread = threading.Thread(
            target=self._rabbit_consumer_worker,
            args=(medico_id, python_q, stop_event),
            daemon=True
        )
        listener_thread.start()

        # Guardar referencia para poder limpiar después
        if medico_id not in self._active_subscriptions:
            self._active_subscriptions[medico_id] = []
        
        self._active_subscriptions[medico_id].append({
            'queue': python_q,
            'thread': listener_thread,
            'stop_event': stop_event
        })

        print(f"📡 [RABBITMQ] Listener iniciado para Médico {medico_id}")
        return python_q

    def desuscribir(self, medico_id: int, q: queue.Queue):
        """
        Señaliza al hilo que debe detenerse y limpia referencias.
        """
        if medico_id in self._active_subscriptions:
            subs = self._active_subscriptions[medico_id]
            # Buscar la suscripción específica que corresponde a esa cola
            target_sub = next((s for s in subs if s['queue'] == q), None)
            
            if target_sub:
                print(f"🔕 [RABBITMQ] Deteniendo listener para Médico {medico_id}...")
                target_sub['stop_event'].set() # Señal para detener el bucle del hilo
                # Nota: El hilo morirá cuando intente leer de Rabbit y detecte el evento o timeout
                subs.remove(target_sub)
                
            if not self._active_subscriptions[medico_id]:
                del self._active_subscriptions[medico_id]

    def _rabbit_consumer_worker(self, medico_id: int, python_q: queue.Queue, stop_event: threading.Event):
        """
        Lógica que corre en el hilo secundario:
        Conecta a RabbitMQ -> Crea cola temporal -> Consume -> Pone en Python Queue
        """
        routing_key = f"medico.{medico_id}"
        connection = None
        try:
            connection = self._get_connection()
            channel = connection.channel()
            
            channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type='topic')
            
            # Cola exclusiva y temporal (se borra al desconectar)
            result = channel.queue_declare(queue='', exclusive=True, auto_delete=True)
            queue_name = result.method.queue
            
            channel.queue_bind(exchange=self.EXCHANGE_NAME, queue=queue_name, routing_key=routing_key)
            
            # Consumo manual con timeout para poder revisar stop_event
            for method_frame, properties, body in channel.consume(queue_name, inactivity_timeout=1):
                if stop_event.is_set():
                    break
                
                if method_frame:
                    msg = json.loads(body)
                    python_q.put(msg)
                    channel.basic_ack(method_frame.delivery_tag)
                    
        except Exception as e:
            print(f"❌ Error en listener de Médico {medico_id}: {e}")
        finally:
            if connection and connection.is_open:
                connection.close()
            print(f"🏁 Listener Médico {medico_id} finalizado.")