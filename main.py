"""
Punto de entrada principal de la API REST — Sakila / Supabase
=============================================================

Ejecutar en desarrollo:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

O con las variables del .env:
    python main.py
"""

import os
from dotenv import load_dotenv

# Carga el .env antes de cualquier importación que lo necesite
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from api.routers import rentals, payments, clientes


# ─────────────────────────────────────────────
#  Configuración de la aplicación FastAPI
# ─────────────────────────────────────────────
app = FastAPI(
    title="Sakila API — Sistemas Operativos",
    description=(
        "API REST construida con **FastAPI** sobre la base de datos **Sakila** "
        "alojada en **Supabase (PostgreSQL)**.\n\n"
        "Proporciona endpoints para consultar:\n"
        "- 🎬 Rentas activas (películas no devueltas)\n"
        "- ✅ Rentas devueltas (historial de devoluciones)\n"
        "- 💳 Pagos realizados por los clientes\n"
    ),
    version="1.0.0",
)

# ─────────────────────────────────────────────
#  CORS — permite llamadas desde cualquier origen
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
#  Registro de routers
# ─────────────────────────────────────────────
app.include_router(rentals.router)
app.include_router(payments.router)
app.include_router(clientes.router)


# ─────────────────────────────────────────────
#  Endpoints de interfaz y salud
# ─────────────────────────────────────────────
@app.get("/", tags=["UI"], summary="Dashboard Principal")
def root():
    """Sirve la interfaz gráfica construida en HTML."""
    return FileResponse("cliente_ui.html")


@app.get("/health", tags=["Estado"], summary="Estado del servidor")
def health():
    """Endpoint de comprobación de vida — útil para load-balancers."""
    from api.database import get_connection

    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"

    return JSONResponse(
        content={
            "status": "ok" if db_status == "ok" else "degraded",
            "database": db_status,
        },
        status_code=200 if db_status == "ok" else 503,
    )


# ─────────────────────────────────────────────
#  Arranque directo: python main.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info",
    )
