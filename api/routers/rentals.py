"""
Router para el módulo de RENTAS.

Endpoints:
  GET /rentals/active              – Lista de rentas activas (sin devolver)
  GET /rentals/active/{rental_id}  – Detalle de una renta activa específica
  GET /rentals/returned            – Lista de rentas devueltas
  GET /rentals/returned/{rental_id}– Detalle de una renta devuelta específica
"""

import os
import requests
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from api.database import fetch_all, fetch_one
from api.models import ActiveRental, ReturnedRental

router = APIRouter(prefix="/rentals", tags=["Rentas"])

# URL de la API externa de Alquileres
API_ALQUILERES = os.getenv("API_ALQUILERES", "http://34.176.33.216:8000/api/v1/rentals")

def get_external_rentals(
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    inventory_id: Optional[int] = None,
    category_name: Optional[str] = None,
    day: Optional[bool] = None,
    week: Optional[bool] = None,
) -> list[dict]:
    """
    Realiza una petición a la API de alquileres externa.
    """
    params = {}
    if customer_id is not None:
        params["customer_id"] = customer_id
    if status is not None:
        params["status"] = status
    if inventory_id is not None:
        params["inventory_id"] = inventory_id
    if category_name is not None:
        params["category_name"] = category_name
    if day is not None:
        params["day"] = "true" if day else "false"
    if week is not None:
        params["week"] = "true" if week else "false"

    try:
        response = requests.get(API_ALQUILERES, params=params, timeout=5)
        response.raise_for_status()
        res_data = response.json()
        if isinstance(res_data, dict) and "data" in res_data:
            return res_data["data"]
        return []
    except Exception as e:
        print(f"Error al obtener alquileres desde API externa: {e}")
        return []

def map_to_active_rental(ext: dict) -> dict:
    """
    Mapea un alquiler externo a la estructura de un ActiveRental para respuesta.
    """
    rental_date_str = ext.get("rental_date") or ""
    rental_date = None
    days_rented = 0
    if rental_date_str:
        try:
            # Reemplazar Z por nada para evitar problemas con fromisoformat en versiones previas
            rental_date = datetime.fromisoformat(rental_date_str.replace("Z", ""))
            days_rented = (datetime.now() - rental_date).days
        except Exception:
            rental_date = datetime.now()
    else:
        rental_date = datetime.now()

    rental_duration = 7  # duración por defecto para externos
    overdue = days_rented > rental_duration

    return {
        "rental_id": ext.get("rental_id", 0),
        "rental_date": rental_date,
        "customer_id": ext.get("customer_id", 0),
        "customer_name": ext.get("fullName") or "External Customer",
        "customer_email": None,
        "film_id": 0,
        "film_title": ext.get("title") or "External Film",
        "inventory_id": ext.get("inventory_id", 0),
        "store_id": 1,
        "staff_id": ext.get("staff_id", 1),
        "rental_duration": rental_duration,
        "days_rented": max(0, days_rented),
        "overdue": overdue
    }

def map_to_returned_rental(ext: dict) -> dict:
    """
    Mapea un alquiler externo devuelto a la estructura de ReturnedRental.
    """
    rental_date_str = ext.get("rental_date") or ""
    return_date_str = ext.get("return_date") or ""
    rental_date = None
    return_date = None
    rental_duration_days = 0

    try:
        if rental_date_str:
            rental_date = datetime.fromisoformat(rental_date_str.replace("Z", ""))
        if return_date_str:
            return_date = datetime.fromisoformat(return_date_str.replace("Z", ""))
        if rental_date and return_date:
            rental_duration_days = (return_date - rental_date).days
    except Exception:
        pass

    if not rental_date:
        rental_date = datetime.now()
    if not return_date:
        return_date = datetime.now()

    on_time = rental_duration_days <= 7

    return {
        "rental_id": ext.get("rental_id", 0),
        "rental_date": rental_date,
        "return_date": return_date,
        "customer_id": ext.get("customer_id", 0),
        "customer_name": ext.get("fullName") or "External Customer",
        "customer_email": None,
        "film_id": 0,
        "film_title": ext.get("title") or "External Film",
        "inventory_id": ext.get("inventory_id", 0),
        "store_id": 1,
        "staff_id": ext.get("staff_id", 1),
        "rental_duration_days": max(0, rental_duration_days),
        "on_time": on_time
    }


# ─────────────────────────────────────────────────────────────────
#  Rentas activas
# ─────────────────────────────────────────────────────────────────

_ACTIVE_RENTAL_SELECT = """
SELECT
    r.rental_id,
    r.rental_date,
    r.customer_id,
    (c.first_name || ' ' || c.last_name)  AS customer_name,
    c.email                                AS customer_email,
    i.film_id,
    f.title                                AS film_title,
    r.inventory_id,
    i.store_id,
    r.staff_id,
    f.rental_duration,
    -- días transcurridos desde la renta hasta hoy
    (CURRENT_DATE - r.rental_date::date)   AS days_rented,
    -- sobredue si los días rentados superan la duración permitida
    ((CURRENT_DATE - r.rental_date::date) > f.rental_duration) AS overdue
FROM rental r
JOIN customer  c ON c.customer_id  = r.customer_id
JOIN inventory i ON i.inventory_id = r.inventory_id
JOIN film      f ON f.film_id      = i.film_id
WHERE r.return_date IS NULL
"""

@router.get(
    "/active",
    response_model=list[ActiveRental],
    summary="Rentas activas",
    description="Retorna todas las rentas activas que aún no han sido devueltas, fusionando los alquileres de la base de datos local y la API externa.",
)
def get_active_rentals(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    store_id: Optional[int] = Query(None, description="Filtrar por tienda"),
    inventory_id: Optional[int] = Query(None, description="Filtrar por ID de inventario físico"),
    category_name: Optional[str] = Query(None, description="Filtrar por categoría de película"),
    day: Optional[bool] = Query(None, description="Listar alquileres del día"),
    week: Optional[bool] = Query(None, description="Listar alquileres de la semana"),
    overdue_only: bool = Query(False, description="Solo rentas con retraso"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
):
    # ── 1. CONSULTA BD LOCAL ──
    query = _ACTIVE_RENTAL_SELECT
    params: list = []
    conditions: list[str] = []

    if customer_id is not None:
        conditions.append("r.customer_id = %s")
        params.append(customer_id)

    if store_id is not None:
        conditions.append("i.store_id = %s")
        params.append(store_id)

    if inventory_id is not None:
        conditions.append("r.inventory_id = %s")
        params.append(inventory_id)

    if category_name:
        query = query.replace(
            "FROM rental r",
            "FROM rental r JOIN film_category fc ON fc.film_id = f.film_id JOIN category cat ON cat.category_id = fc.category_id"
        )
        conditions.append("cat.name = %s")
        params.append(category_name)

    if day:
        conditions.append("r.rental_date::date = CURRENT_DATE")
    elif week:
        conditions.append("r.rental_date::date >= CURRENT_DATE - 7")

    if overdue_only:
        conditions.append("(CURRENT_DATE - r.rental_date::date) > f.rental_duration")

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY r.rental_date DESC"
    
    db_rows = fetch_all(query, tuple(params))

    # ── 2. CONSULTA API EXTERNA (API_ALQUILERES) ──
    ext_active_raw = get_external_rentals(
        customer_id=customer_id,
        status="ALQUILADO",
        inventory_id=inventory_id,
        category_name=category_name,
        day=day,
        week=week
    )
    ext_active = [map_to_active_rental(r) for r in ext_active_raw]

    # Aplicar filtros post-consulta en los externos si aplica
    if store_id is not None:
        ext_active = [r for r in ext_active if r["store_id"] == store_id]
    if overdue_only:
        ext_active = [r for r in ext_active if r["overdue"]]

    # ── 3. FUSIÓN Y PAGINACIÓN ──
    merged = db_rows + ext_active

    # Reordenar por rental_date DESC
    def get_rental_date(item):
        d = item.get("rental_date")
        if isinstance(d, str):
            try:
                return datetime.fromisoformat(d.replace("Z", ""))
            except ValueError:
                return datetime.min
        return d or datetime.min

    merged.sort(key=get_rental_date, reverse=True)

    # Rebanar acorde a limit/offset
    return merged[offset : offset + limit]


@router.get(
    "/active/{rental_id}",
    response_model=ActiveRental,
    summary="Detalle de renta activa",
    description="Retorna el detalle de una renta activa específica por su ID.",
)
def get_active_rental(rental_id: int):
    # Buscar primero localmente
    query = _ACTIVE_RENTAL_SELECT + " AND r.rental_id = %s"
    row = fetch_one(query, (rental_id,))
    if not row:
        # Consultar externos si no se encontró en DB local
        ext_rentals = get_external_rentals(status="ALQUILADO")
        for r in ext_rentals:
            if r.get("rental_id") == rental_id:
                return map_to_active_rental(r)
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró una renta activa con ID {rental_id}.",
        )
    return row


# ─────────────────────────────────────────────────────────────────
#  Rentas devueltas
# ─────────────────────────────────────────────────────────────────

_RETURNED_RENTAL_SELECT = """
SELECT
    r.rental_id,
    r.rental_date,
    r.return_date,
    r.customer_id,
    (c.first_name || ' ' || c.last_name)                              AS customer_name,
    c.email                                                            AS customer_email,
    i.film_id,
    f.title                                                            AS film_title,
    r.inventory_id,
    i.store_id,
    r.staff_id,
    -- días que estuvo en posesión del cliente
    (r.return_date::date - r.rental_date::date)                       AS rental_duration_days,
    -- devuelta a tiempo si no superó el límite de días permitido
    ((r.return_date::date - r.rental_date::date) <= f.rental_duration) AS on_time
FROM rental r
JOIN customer  c ON c.customer_id  = r.customer_id
JOIN inventory i ON i.inventory_id = r.inventory_id
JOIN film      f ON f.film_id      = i.film_id
WHERE r.return_date IS NOT NULL
"""

@router.get(
    "/returned",
    response_model=list[ReturnedRental],
    summary="Películas devueltas",
    description="Retorna el historial completo de devoluciones fusionadas con la API externa.",
)
def get_returned_rentals(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    store_id: Optional[int] = Query(None, description="Filtrar por tienda"),
    inventory_id: Optional[int] = Query(None, description="Filtrar por ID de inventario físico"),
    category_name: Optional[str] = Query(None, description="Filtrar por categoría de película"),
    day: Optional[bool] = Query(None, description="Listar devoluciones del día"),
    week: Optional[bool] = Query(None, description="Listar devoluciones de la semana"),
    late_only: bool = Query(False, description="Solo devoluciones tardías"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
):
    # ── 1. CONSULTA BD LOCAL ──
    query = _RETURNED_RENTAL_SELECT
    params: list = []
    conditions: list[str] = []

    if customer_id is not None:
        conditions.append("r.customer_id = %s")
        params.append(customer_id)

    if store_id is not None:
        conditions.append("i.store_id = %s")
        params.append(store_id)

    if inventory_id is not None:
        conditions.append("r.inventory_id = %s")
        params.append(inventory_id)

    if category_name:
        query = query.replace(
            "FROM rental r",
            "FROM rental r JOIN film_category fc ON fc.film_id = f.film_id JOIN category cat ON cat.category_id = fc.category_id"
        )
        conditions.append("cat.name = %s")
        params.append(category_name)

    if day:
        conditions.append("r.rental_date::date = CURRENT_DATE")
    elif week:
        conditions.append("r.rental_date::date >= CURRENT_DATE - 7")

    if late_only:
        conditions.append("(r.return_date::date - r.rental_date::date) > f.rental_duration")

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY r.return_date DESC"
    
    db_rows = fetch_all(query, tuple(params))

    # ── 2. CONSULTA API EXTERNA (API_ALQUILERES) ──
    ext_ret_raw = get_external_rentals(
        customer_id=customer_id,
        status="RETORNADO",
        inventory_id=inventory_id,
        category_name=category_name,
        day=day,
        week=week
    )
    ext_ret = [map_to_returned_rental(r) for r in ext_ret_raw]

    # Aplicar filtros post-consulta
    if store_id is not None:
        ext_ret = [r for r in ext_ret if r["store_id"] == store_id]
    if late_only:
        ext_ret = [r for r in ext_ret if not r["on_time"]]

    # ── 3. FUSIÓN Y PAGINACIÓN ──
    merged = db_rows + ext_ret

    def get_return_date(item):
        d = item.get("return_date")
        if isinstance(d, str):
            try:
                return datetime.fromisoformat(d.replace("Z", ""))
            except ValueError:
                return datetime.min
        return d or datetime.min

    merged.sort(key=get_return_date, reverse=True)

    return merged[offset : offset + limit]


@router.get(
    "/returned/{rental_id}",
    response_model=ReturnedRental,
    summary="Detalle de devolución",
    description="Retorna el detalle de una renta devuelta específica por su ID.",
)
def get_returned_rental(rental_id: int):
    # Buscar primero localmente
    query = _RETURNED_RENTAL_SELECT + " AND r.rental_id = %s"
    row = fetch_one(query, (rental_id,))
    if not row:
        # Consultar externos si no se encontró en DB local
        ext_rentals = get_external_rentals(status="RETORNADO")
        for r in ext_rentals:
            if r.get("rental_id") == rental_id:
                return map_to_returned_rental(r)
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró una renta devuelta con ID {rental_id}.",
        )
    return row
