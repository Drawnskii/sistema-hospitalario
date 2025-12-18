# 🏥 Sistema Hospitalario (Python Nativo + SSE)

Un sistema de gestión de citas médicas construido con una arquitectura de microservicios simulada dentro de un monolito modular.

**Características principales:**
* 🚀 **Zero Dependencies:** Construido 100% con Python estándar (sin Flask, Django, FastAPI).
* ⚡ **Real-Time:** Sistema de notificaciones en tiempo real usando **Server-Sent Events (SSE)** (sin WebSockets ni librerías externas).
* 🏗 **Arquitectura Limpia:** Separación estricta de capas (Frontend, Controller, Services, Logic, Data).
* 🗄 **Persistencia:** SQLite nativo.

---

## 📋 Requisitos Previos

Para ejecutar este sistema necesitas tener instalado:

* **Python 3.11** o superior.
    * *Se recomienda Python 3.11.9 para mejor rendimiento.*
* Un navegador web moderno (Chrome, Firefox, Edge).

> **Nota:** No es necesario instalar ninguna librería externa (`pip install` no es requerido), ya que todo usa la librería estándar de Python.

---

## 🚀 Instalación y Ejecución

Sigue estos pasos para levantar el sistema desde cero:

1.  **Clonar el repositorio:**
    ```bash
    git clone <TU_URL_DEL_REPO>
    cd sistema-hospitalario
    ```

2.  **Iniciar el Servidor:**
    El sistema debe ejecutarse desde la carpeta del backend para resolver correctamente las importaciones.
    
    ```bash
    cd backend
    python main.py
    ```

3.  **Verificar ejecución:**
    Deberías ver un mensaje en la terminal como:
    ```text
    --- ⚙️ Iniciando Sistema Hospitalario (Real-Time) ---
    Base de datos inicializada en: .../backend/data/hospital.db
    🚀 Servidor Real-Time corriendo en: http://localhost:8000
    ```

4.  **Abrir la Aplicación:**
    Ve a tu navegador e ingresa a: **`http://localhost:8000`**

---

## 🧪 Guía de Uso (Paso a Paso)

Para probar todas las funcionalidades (incluyendo las notificaciones en tiempo real), sigue este flujo:

### Paso 1: Configurar el Médico
1.  Ve a la pestaña **"Vista Médico"**.
2.  En "Registrar Nuevo Médico", llena los datos (Ej: *Dr. House*, *Diagnóstico*).
3.  Dale clic a **Registrar Médico**.
4.  En el apartado de abajo ("Gestionar Disponibilidad"), **selecciona al médico** que acabas de crear en el menú desplegable.
    * ⚠️ *Importante:* Al seleccionar el médico, se activa la conexión en tiempo real para recibir notificaciones.
5.  Selecciona una fecha/hora y dale a **Agregar Horario**.

### Paso 2: Agendar como Paciente
1.  Ve a la pestaña **"Vista Paciente"**.
2.  En "Seleccione Médico", elige al doctor que creaste.
3.  Verás el horario disponible en la tabla. Dale clic a **Reservar**.
4.  Ingresa tu nombre y apellido y confirma.
5.  **¡Observa la magia!** Regresa inmediatamente a la pestaña **"Vista Médico"**. Deberías ver una notificación amarilla indicando la nueva cita.

### Paso 3: Anular Cita (Prueba completa)
1.  En la "Vista Paciente", ve a la sección "Mis Turnos".
2.  Busca tus turnos por tu nombre.
3.  Dale clic al botón rojo **Anular Cita**.
4.  Regresa a la "Vista Médico". Verás una notificación roja en tiempo real avisando de la cancelación.

---

## 📂 Estructura del Proyecto

```text
/
├── backend/
│   ├── main.py              # Punto de entrada y Servidor HTTP/SSE
│   ├── data/                # Capa de Acceso a Datos (SQLite)
│   ├── logic/               # Reglas de Negocio y Modelos
│   └── services/            # Broker de Mensajería (Pub/Sub en memoria)
└── frontend/
    └── index.html           # SPA (Single Page Application) Vanilla JS