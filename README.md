Aquí tienes el **README.md** actualizado y mejorado. He modificado la sección de características para reflejar el uso de RabbitMQ, agregado los pasos de instalación de dependencias y creado una sección dedicada "🛠️ Guía Avanzada: RabbitMQ" que cubre la instalación, el monitoreo y la creación de la cola de depuración.

---

# 🏥 Sistema Hospitalario (Python + RabbitMQ + SSE)

Un sistema de gestión de citas médicas construido con una **Arquitectura Hexagonal** y comunicación asíncrona mediante **RabbitMQ**.

**Características principales:**

* 🧠 **Arquitectura Event-Driven:** Desacoplamiento total entre servicios usando un Broker de Mensajería (RabbitMQ).
* ⚡ **Real-Time:** Notificaciones instantáneas al navegador usando **Server-Sent Events (SSE)**.
* 🏗 **Arquitectura Limpia:** Separación estricta de capas (Frontend, Controller, Services, Logic, Data).
* 🐍 **Python 3.11:** Backend robusto y moderno.
* 🗄 **Persistencia:** SQLite nativo.

---

## 📋 Requisitos Previos

Para ejecutar este sistema necesitas tener instalado:

1. **Python 3.11** o superior.
2. **RabbitMQ Server** corriendo localmente (ver guía más abajo).
3. Un navegador web moderno (Chrome, Firefox, Edge).

---

## 🚀 Instalación y Ejecución

Sigue estos pasos para levantar el sistema desde cero:

### 1. Clonar el repositorio

```bash
git clone https://github.com/Drawnskii/sistema-hospitalario.git
cd sistema-hospitalario

```

### 2. Instalar Dependencias

El proyecto ahora utiliza librerías externas (principalmente `pika` para la conexión con RabbitMQ).

```bash
cd backend
pip install -r requirements.txt

```

### 3. Iniciar RabbitMQ

Asegúrate de que tu servidor RabbitMQ esté encendido antes de correr el código (ver sección **Guía RabbitMQ** si no lo tienes).

### 4. Iniciar el Servidor

Ejecuta el sistema desde la carpeta `backend`:

```bash
python main.py

```

### 5. Verificar ejecución

Deberías ver en la consola:

```text
--- ⚙️ Iniciando Sistema Hospitalario (Event-Driven) ---
📡 [RABBITMQ] Conexión establecida exitosamente.
🚀 Servidor Real-Time corriendo en: http://localhost:8000

```

Ve a tu navegador e ingresa a: **`http://localhost:8000`**

---

## 🛠️ Guía Avanzada: RabbitMQ

Este proyecto utiliza RabbitMQ como bus de eventos. Aquí tienes todo lo necesario para instalarlo, monitorearlo y depurarlo.

### A. Instalación de RabbitMQ (Cualquier SO)

La forma más rápida y limpia de tener RabbitMQ con el panel de administración es usando **Docker**. Si no usas Docker, sigue las instrucciones nativas.

#### Opción 1: Docker (Recomendada)

Si tienes Docker instalado, solo corre este comando en tu terminal:

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

```

*Esto descarga la imagen, habilita el plugin de administración y expone los puertos necesarios.*

#### Opción 2: Instalación Nativa

* **Windows:** Usa Chocolatey (`choco install rabbitmq`) o descarga el instalador oficial desde [rabbitmq.com](https://www.rabbitmq.com/download.html).
* **MacOS:** Usa Homebrew: `brew install rabbitmq`.
* **Linux (Ubuntu/Debian):** `sudo apt-get install rabbitmq-server`.
* *Nota:* En instalaciones nativas, debes habilitar el panel manualmente:
```bash
rabbitmq-plugins enable rabbitmq_management

```





---

### B. Monitoreo desde el Navegador

Una vez instalado y corriendo, puedes ver gráficamente qué está pasando en tu sistema.

1. Abre tu navegador y ve a: **`http://localhost:15672`**
2. Inicia sesión con las credenciales por defecto:
* **User:** `guest`
* **Password:** `guest`



Aquí verás las conexiones activas, canales y el flujo de mensajes en tiempo real.

---

### C. Tutorial: Crear `cola_debug` (Ver mensajes de Python)

Para poder inspeccionar los mensajes JSON que envía el código Python sin necesidad de usar `print()`, crearemos una cola de depuración que intercepte todos los eventos.

**Pasos en el Panel de RabbitMQ:**

1. **Crear la Cola:**
* Ve a la pestaña **Queues**.
* En "Add a new queue", escribe en *Name*: `cola_debug`.
* Deja el resto por defecto y presiona **Add queue**.


2. **Enlazar al Exchange (Binding):**
* Haz clic en el nombre de la cola recién creada (`cola_debug`).
* Busca la sección **Bindings**.
* En el campo *From exchange*, escribe: `hospital_events` (este es el nombre que usa el código Python).
* En *Routing key*, escribe: `#`
* *(El símbolo `#` es un comodín que significa "recibir todo los mensajes de cualquier médico").*


* Haz clic en **Bind**.


3. **Probar:**
* Usa la aplicación hospitalaria (registra un médico o pide un turno).
* Regresa a RabbitMQ, entra a `cola_debug` y busca la sección **Get messages**.
* Presiona el botón **Get Message(s)**.
* ¡Verás el JSON exacto que viajó por el sistema!



---

## 🧪 Guía de Uso (Flujo Principal)

1. **Configurar Médico:** Ve a "Vista Médico", registra uno nuevo (Ej: Dr. House) y selecciona su nombre en "Gestionar Disponibilidad" para conectarte al sistema SSE.
2. **Agendar:** Ve a "Vista Paciente", elige al Dr. House y reserva un turno.
3. **Verificación:**
* En la web: El médico recibirá una alerta visual amarilla.
* En RabbitMQ: La gráfica de la cola subirá y podrás ver el mensaje en `cola_debug`.



---

## 📂 Estructura del Proyecto

```text
/
├── backend/
│   ├── main.py              # Servidor HTTP y Configuración
│   ├── requirements.txt     # Librerías externas (pika, etc.)
│   ├── data/                # Capa de Acceso a Datos (SQLite)
│   ├── logic/               # Reglas de Negocio
│   └── services/            # Adaptador de RabbitMQ (Publisher/Subscriber)
└── frontend/
    └── index.html           # SPA Vanilla JS

```