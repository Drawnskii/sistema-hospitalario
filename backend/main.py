import http.server
import socketserver
import json
import re
import os
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date

# --- IMPORTS DE CAPAS ---
from data.database import DatabaseConfig
from data.repositories import SqliteMedicoRepository, SqliteTurnosRepository, SqliteDisponibilidadRepository
from logic.services import MedicoService, AgendamientoService
from logic.dtos import CrearMedicoDTO, AgregarDisponibilidadDTO, AgendarTurnoDTO
from logic.models import EstadoTurno
from services.messaging import InMemoryMessageBroker

# Configuración
PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.path.join(BASE_DIR, '..', 'frontend', 'index.html')

# ==========================================
# 1. INICIALIZACIÓN
# ==========================================
print("--- ⚙️ Iniciando Sistema Hospitalario (Real-Time) ---")

DatabaseConfig.initialize_db()

medico_repo = SqliteMedicoRepository()
disp_repo = SqliteDisponibilidadRepository()
turno_repo = SqliteTurnosRepository()
broker = InMemoryMessageBroker()

medico_service = MedicoService(medico_repo, disp_repo)
agendamiento_service = AgendamientoService(turno_repo, disp_repo, broker)

print("--- ✅ Dependencias cargadas ---")

# ==========================================
# 2. CONTROLADOR HTTP
# ==========================================
class HospitalHTTPHandler(http.server.BaseHTTPRequestHandler):
    
    def _send_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, EstadoTurno):
                return obj.value
            raise TypeError(f"Type {type(obj)} not serializable")

        self.wfile.write(json.dumps(data, default=json_serial).encode('utf-8'))

    def _send_error(self, message, status=400):
        try:
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": message}).encode('utf-8'))
        except: pass

    def _serve_frontend(self):
        try:
            with open(FRONTEND_PATH, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self._send_error(f"Error: No se encuentra frontend/index.html", 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # --- GET ---
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip('/')
        query_params = parse_qs(parsed_url.query)

        if path == '' or path == '/' or path == '/index.html':
            self._serve_frontend()
            return

        # API: NOTIFICACIONES REAL-TIME (SSE)
        if path == '/api/notificaciones':
            medico_id = query_params.get('medico_id', [None])[0]
            if not medico_id:
                self._send_error("Falta medico_id", 400)
                return

            # Configuración de Headers para Server-Sent Events
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Suscribirse al broker
            cola_mensajes = broker.suscribir(int(medico_id))

            try:
                while True:
                    # Esperamos mensaje (bloqueante pero eficiente)
                    mensaje = cola_mensajes.get()
                    
                    # Formato SSE: "data: {json}\n\n"
                    payload = f"data: {json.dumps(mensaje)}\n\n"
                    self.wfile.write(payload.encode('utf-8'))
                    self.wfile.flush() # Forzar envío inmediato
            except (BrokenPipeError, ConnectionResetError):
                # El cliente cerró el navegador
                broker.desuscribir(int(medico_id), cola_mensajes)
            return

        # Listar Médicos
        elif path == '/api/medicos':
            try:
                medicos = medico_service.obtener_todos()
                resp = [m.to_dict() for m in medicos]
                self._send_response(resp)
            except Exception as e:
                self._send_error(str(e), 500)

        # Consultar Disponibilidad
        elif path == '/api/disponibilidad':
            medico_id = query_params.get('medico_id', [None])[0]
            if not medico_id:
                self._send_error("Falta parametro medico_id")
                return
            try:
                slots = medico_service.obtener_disponibilidad(int(medico_id))
                resp = [{
                    "id": s.id, "medico_id": s.medico_id, 
                    "fecha_hora": s.fecha_hora, "estado": s.estado
                } for s in slots]
                self._send_response(resp)
            except Exception as e:
                self._send_error(str(e), 500)

        # Buscar Turnos
        elif path == '/api/turnos':
            nombre = query_params.get('nombre', [None])[0]
            apellido = query_params.get('apellido', [None])[0]
            if not nombre or not apellido:
                self._send_error("Faltan parametros nombre y apellido")
                return
            try:
                turnos = agendamiento_service.listar_por_paciente(nombre, apellido)
                resp = [{
                    "id": t.id, "medico_id": t.medico_id,
                    "fecha_hora": t.fecha_hora, "estado": t.estado
                } for t in turnos]
                self._send_response(resp)
            except Exception as e:
                self._send_error(str(e), 500)
        else:
            self._send_error("Ruta no encontrada", 404)

    # --- POST ---
    def do_POST(self):
        path = self.path.rstrip('/')
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
        except:
            self._send_error("JSON invalido", 400)
            return

        if path == '/api/medicos':
            try:
                dto = CrearMedicoDTO(data['nombre'], data['apellido'], data['especialidad'])
                nuevo = medico_service.registrar_medico(dto)
                self._send_response(nuevo.to_dict(), 201)
            except Exception as e:
                self._send_error(str(e), 400)

        elif path == '/api/disponibilidad':
            try:
                dto = AgregarDisponibilidadDTO(int(data['medico_id']), datetime.fromisoformat(data['fecha_hora']))
                nuevo = medico_service.agregar_disponibilidad(dto)
                self._send_response({"mensaje": "Disponibilidad creada", "id": nuevo.id}, 201)
            except Exception as e:
                self._send_error(str(e), 400)

        elif path == '/api/turnos':
            try:
                dto = AgendarTurnoDTO(
                    int(data['medico_id']), data['paciente_nombre'], 
                    data['paciente_apellido'], datetime.fromisoformat(data['fecha_hora'])
                )
                turno = agendamiento_service.agendar_turno(dto)
                self._send_response({"mensaje": "Turno confirmado", "id": turno.id}, 201)
            except ValueError as ve:
                self._send_error(str(ve), 409) 
            except Exception as e:
                print(f"ERROR: {e}")
                self._send_error(str(e), 500)
        else:
            self._send_error("Ruta no encontrada", 404)

    # --- DELETE ---
    def do_DELETE(self):
        path = self.path.rstrip('/')
        match = re.search(r'/api/turnos/(\d+)', path)
        if match:
            try:
                agendamiento_service.anular_turno(int(match.group(1)))
                self._send_response({"mensaje": "Turno anulado"})
            except Exception as e:
                self._send_error(str(e), 500)
        else:
            self._send_error("Ruta no encontrada", 404)

# --- SERVIDOR MULTIHILO (ThreadingTCPServer) ---
# Necesario para que SSE no bloquee el servidor
class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Usamos ThreadingHTTPServer en lugar de TCPServer simple
    with ThreadingHTTPServer(("", PORT), HospitalHTTPHandler) as httpd:
        print(f"🚀 Servidor Real-Time corriendo en: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()