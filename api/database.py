"""
Módulo de conexión a la base de datos PostgreSQL (Supabase / Sakila).
Usa variables de entorno definidas en el archivo .env de la raíz del proyecto.
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Carga el .env desde la carpeta raíz del proyecto (un nivel arriba de /api)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))


def get_connection():
    """Retorna una conexión nueva a la base de datos PostgreSQL."""

    # Si existe DATABASE_URL tiene prioridad
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_DB_HOST"),
            port=int(os.getenv("SUPABASE_DB_PORT", 5432)),
            dbname=os.getenv("SUPABASE_DB_NAME", "postgres"),
            user=os.getenv("SUPABASE_DB_USER"),
            password=os.getenv("SUPABASE_DB_PASSWORD"),
            sslmode="require",
        )

    conn.autocommit = False
    return conn


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Ejecuta una consulta SELECT y retorna todos los registros como lista de dicts."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Ejecuta una consulta SELECT y retorna un único registro como dict."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
