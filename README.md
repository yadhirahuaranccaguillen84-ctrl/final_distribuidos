# 🎬 Sakila — API REST & Dashboard de Cliente

> Sistema completo de gestión de alquiler de películas construido con **FastAPI + Python** y **CustomTkinter**, sobre la base de datos **Sakila** alojada en **Supabase (PostgreSQL)**.  
> Incluye API REST de solo lectura y una interfaz gráfica de escritorio para consultar rentas activas, devoluciones y pagos.

---

## 📋 Tabla de contenidos

- [Requisitos previos](#requisitos-previos)
- [Instalación y configuración](#instalación-y-configuración)
- [Ejecución del servidor API](#ejecución-del-servidor-api)
- [Interfaz gráfica — Dashboard del Cliente](#interfaz-gráfica--dashboard-del-cliente)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Endpoints disponibles](#endpoints-disponibles)
  - [Estado del servidor](#estado-del-servidor)
  - [Rentas activas](#rentas-activas)
  - [Películas devueltas](#películas-devueltas)
  - [Pagos](#pagos)
- [Documentación interactiva](#documentación-interactiva)
- [Parámetros de consulta comunes](#parámetros-de-consulta-comunes)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Variables de entorno](#variables-de-entorno)

---

## Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| Python | 3.11 |
| pip | 23+ |
| Acceso a la base de datos Supabase | — |

---

## Instalación y configuración

```bash
# 1. Clona o descarga el repositorio
cd FINAL_SISTEMAS_OPERATIVOS

# 2. (Recomendado) Crea un entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Revisa el archivo .env en la raíz del proyecto
#    (ya contiene las credenciales de la base de datos Supabase)
```

El archivo `.env` ya está configurado con las credenciales de Supabase. Si necesitas apuntar a otra base de datos, edita las variables `SUPABASE_DB_*` o define `DATABASE_URL`.

---

## Ejecución del servidor API

```bash
# Opción A — arranque directo (lee API_HOST y API_PORT del .env)
python main.py

# Opción B — uvicorn con recarga automática (desarrollo)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor quedará disponible en **`http://localhost:8000`**.

---

## Interfaz Gráfica — Dashboard Web

La interfaz ha sido migrada a una **Web UI moderna** construida con HTML5, CSS3 y JavaScript. No requiere instalación de librerías gráficas pesadas y es servida directamente por el servidor FastAPI.

### Características de la Web UI

- 📱 **Diseño Responsivo** — Se adapta a cualquier tamaño de pantalla.
- 🌙 **Modo Oscuro Integrado** — Conmutación fluida entre temas.
- 📊 **Visualización de Datos Reales** — Conexión directa a los endpoints de la API.
- 🚦 **Indicadores de Estado** — Badges de colores para rentas vencidas (Ámbar) y devoluciones tardías (Rojo).
- ⚡ **Sin Configuración** — Solo necesitas abrir la URL del servidor.

### Cómo acceder

1. Inicia el servidor (ver sección siguiente).
2. Abre tu navegador en [http://localhost:8000](http://localhost:8000).
3. Alternativamente, puedes ejecutar el comando `python cliente_ui.py` para abrirla automáticamente.

---

## Ejecución del servidor API

```bash
# Ejecutar el servidor (incluye la API y la Interfaz Web)
python main.py
```

El Dashboard y la API estarán disponibles en:
- **Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Documentación API:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Estructura del proyecto

```
FINAL_SISTEMAS_OPERATIVOS/
├── .env                        # Variables de entorno (credenciales DB + API_ENDPOINT)
├── main.py                     # Punto de entrada del servidor API
├── cliente_ui.py               # Interfaz gráfica de escritorio (CustomTkinter)
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
├── SQL/
│   ├── sakila-supabase.sql     # Schema de la base de datos
│   └── postgres-sakila-insert-data.sql
└── api/
    ├── __init__.py
    ├── database.py             # Conexión y helpers de consulta
    ├── models.py               # Modelos Pydantic (esquemas de respuesta)
    └── routers/
        ├── __init__.py
        ├── rentals.py          # Endpoints de rentas
        └── payments.py         # Endpoints de pagos
```

---

## Endpoints disponibles

### Estado del servidor

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Información básica de la API |
| `GET` | `/health` | Comprueba la conexión con la base de datos |

---

### Rentas activas

> Películas que el cliente **aún no ha devuelto** (`return_date IS NULL`).

#### `GET /rentals/active`

Retorna la lista de todas las rentas activas.

**Parámetros de consulta (query params):**

| Parámetro | Tipo | Por defecto | Descripción |
|-----------|------|-------------|-------------|
| `customer_id` | integer | — | Filtrar por ID de cliente |
| `store_id` | integer | — | Filtrar por ID de tienda |
| `overdue_only` | boolean | `false` | Solo rentas con retraso (días rentados > duración permitida) |
| `limit` | integer | `100` | Máximo de registros (1–500) |
| `offset` | integer | `0` | Desplazamiento para paginación |

**Ejemplo de respuesta:**

```json
[
  {
    "rental_id": 1,
    "rental_date": "2007-05-24T22:53:30",
    "customer_id": 130,
    "customer_name": "Charlotte Hunter",
    "customer_email": "charlotte.hunter@sakilacustomer.org",
    "film_id": 16,
    "film_title": "ALAMO VIDEOTAPE",
    "inventory_id": 67,
    "store_id": 1,
    "staff_id": 1,
    "rental_duration": 6,
    "days_rented": 42,
    "overdue": true
  }
]
```

---

#### `GET /rentals/active/{rental_id}`

Retorna el detalle de **una sola renta activa** por su ID.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `rental_id` | integer | ID de la renta |

**Respuesta exitosa:** `200 OK` — objeto `ActiveRental`  
**No encontrado:** `404 Not Found`

---

### Películas devueltas

> Rentas donde el cliente **ya entregó** la película (`return_date IS NOT NULL`).

#### `GET /rentals/returned`

Retorna el historial completo de devoluciones.

**Parámetros de consulta:**

| Parámetro | Tipo | Por defecto | Descripción |
|-----------|------|-------------|-------------|
| `customer_id` | integer | — | Filtrar por ID de cliente |
| `store_id` | integer | — | Filtrar por ID de tienda |
| `late_only` | boolean | `false` | Solo devoluciones tardías |
| `limit` | integer | `100` | Máximo de registros (1–500) |
| `offset` | integer | `0` | Desplazamiento para paginación |

**Ejemplo de respuesta:**

```json
[
  {
    "rental_id": 2,
    "rental_date": "2007-05-24T23:00:00",
    "return_date": "2007-05-26T22:04:30",
    "customer_id": 459,
    "customer_name": "Tommy Collazo",
    "customer_email": "tommy.collazo@sakilacustomer.org",
    "film_id": 333,
    "film_title": "FREAKY POCUS",
    "inventory_id": 1525,
    "store_id": 2,
    "staff_id": 1,
    "rental_duration_days": 2,
    "on_time": true
  }
]
```

---

#### `GET /rentals/returned/{rental_id}`

Retorna el detalle de **una sola devolución** por el ID de la renta.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `rental_id` | integer | ID de la renta |

**Respuesta exitosa:** `200 OK` — objeto `ReturnedRental`  
**No encontrado:** `404 Not Found`

---

### Pagos

#### `GET /payments`

Retorna la lista paginada de todos los pagos.

**Parámetros de consulta:**

| Parámetro | Tipo | Por defecto | Descripción |
|-----------|------|-------------|-------------|
| `customer_id` | integer | — | Filtrar por ID de cliente |
| `date_from` | string | — | Fecha inicial en formato `YYYY-MM-DD` |
| `date_to` | string | — | Fecha final en formato `YYYY-MM-DD` |
| `limit` | integer | `100` | Máximo de registros (1–500) |
| `offset` | integer | `0` | Desplazamiento para paginación |

**Ejemplo de respuesta:**

```json
[
  {
    "payment_id": 17503,
    "customer_id": 341,
    "customer_name": "Peter Menard",
    "customer_email": "peter.menard@sakilacustomer.org",
    "staff_id": 2,
    "rental_id": 1520,
    "amount": "7.99",
    "payment_date": "2007-01-24T21:40:19.996577"
  }
]
```

---

#### `GET /payments/{payment_id}`

Retorna el detalle de **un solo pago** por su ID.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `payment_id` | integer | ID del pago |

**Respuesta exitosa:** `200 OK` — objeto `Payment`  
**No encontrado:** `404 Not Found`

---

#### `GET /payments/customer/{customer_id}`

Retorna **todos los pagos** realizados por un cliente específico.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `customer_id` | integer | ID del cliente |

**Parámetros de consulta:** `limit`, `offset`

**Respuesta exitosa:** `200 OK` — lista de `Payment`  
**Sin resultados:** `404 Not Found`

---

#### `GET /payments/rental/{rental_id}`

Retorna los pagos asociados a **una renta específica**.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `rental_id` | integer | ID de la renta |

**Respuesta exitosa:** `200 OK` — lista de `Payment`  
**Sin resultados:** `404 Not Found`

---

#### `GET /payments/summary`

Retorna el **resumen de pagos por cliente**: total de transacciones y monto acumulado, ordenado de mayor a menor.

**Parámetros de consulta:** `limit`, `offset`

**Ejemplo de respuesta:**

```json
[
  {
    "customer_id": 526,
    "customer_name": "Karl Seal",
    "customer_email": "karl.seal@sakilacustomer.org",
    "total_payments": 45,
    "total_amount": "221.55"
  }
]
```

---

## Documentación interactiva

FastAPI genera automáticamente dos interfaces de documentación:

| Interfaz | URL |
|----------|-----|
| **Swagger UI** (recomendada) | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |

Desde Swagger UI puedes **probar cada endpoint directamente** en el navegador sin necesidad de herramientas externas.

---

## Parámetros de consulta comunes

Todos los endpoints de listado soportan paginación:

| Parámetro | Tipo | Por defecto | Descripción |
|-----------|------|-------------|-------------|
| `limit` | integer | `100` | Número de registros por página (máx. 500) |
| `offset` | integer | `0` | Registro de inicio (para avanzar páginas) |

**Ejemplo de paginación:**
```
GET /payments?limit=20&offset=40
```
→ Página 3 con registros del 41 al 60.

---

## Ejemplos de uso

### Con `curl`

```bash
# Todas las rentas activas
curl http://localhost:8000/rentals/active

# Rentas activas con retraso de la tienda 1
curl "http://localhost:8000/rentals/active?store_id=1&overdue_only=true"

# Historial de devoluciones de un cliente
curl "http://localhost:8000/rentals/returned?customer_id=130"

# Pagos entre fechas específicas
curl "http://localhost:8000/payments?date_from=2007-02-01&date_to=2007-02-28"

# Resumen de pagos (top clientes)
curl "http://localhost:8000/payments/summary?limit=10"

# Pagos de un cliente específico
curl http://localhost:8000/payments/customer/341

# Verificar salud del servidor
curl http://localhost:8000/health
```

### Con Python (`requests`)

```python
import requests

BASE = "http://localhost:8000"

# Rentas activas con retraso
resp = requests.get(f"{BASE}/rentals/active", params={"overdue_only": True, "limit": 50})
print(resp.json())

# Pagos de un cliente
resp = requests.get(f"{BASE}/payments/customer/130")
print(resp.json())

# Resumen de pagos
resp = requests.get(f"{BASE}/payments/summary", params={"limit": 20})
for item in resp.json():
    print(f"{item['customer_name']}: ${item['total_amount']}")
```

### Desde otro servidor (URL pública)

Si el servidor está desplegado en, por ejemplo, `https://api.example.com`:

```bash
curl "https://api.example.com/rentals/active?overdue_only=true"
curl "https://api.example.com/payments/summary?limit=10"
```

---

## Variables de entorno

El archivo `.env` en la raíz controla la configuración:

```env
# Conexión a PostgreSQL / Supabase
SUPABASE_DB_HOST=<host>
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=<usuario>
SUPABASE_DB_PASSWORD=<contraseña>

# Opcional: URL completa (tiene prioridad sobre los campos individuales)
# DATABASE_URL=postgresql://usuario:contraseña@host:5432/postgres

# Configuración del servidor API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false   # true activa recarga automática (solo desarrollo)

# URL base de la API (usado por la interfaz gráfica cliente_ui.py)
API_ENDPOINT=http://localhost:8000
# Si la API está desplegada en otro servidor:
# API_ENDPOINT=https://tu-api.ejemplo.com
```

---

## Códigos de respuesta HTTP

| Código | Significado |
|--------|-------------|
| `200 OK` | Solicitud exitosa |
| `404 Not Found` | El recurso solicitado no existe |
| `422 Unprocessable Entity` | Parámetro inválido (tipo de dato incorrecto) |
| `500 Internal Server Error` | Error interno del servidor |
| `503 Service Unavailable` | No se puede conectar con la base de datos |

---

*Desarrollado para el curso de **Sistemas Operativos — CICLO 8** | UTP*
