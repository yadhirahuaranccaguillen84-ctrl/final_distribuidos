"""
Router para el módulo de RENTAS.

Endpoints:
  GET /rentals/active              – Lista de rentas activas (sin devolver)
  GET /rentals/active/{rental_id}  – Detalle de una renta activa específica
  GET /rentals/returned            – Lista de rentas devueltas
  GET /rentals/returned/{rental_id}– Detalle de una renta devuelta específica
  GET /rentals/{rental_id}         – Consulta genérica de cualquier renta por ID
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from api.database import fetch_all, fetch_one
from api.models import ActiveRental, ReturnedRental

router = APIRouter(prefix="/rentals", tags=["Rentas"])


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
    description="Retorna todas las rentas que aún no han sido devueltas.",
)
def get_active_rentals(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    store_id: Optional[int] = Query(None, description="Filtrar por tienda"),
    overdue_only: bool = Query(False, description="Solo rentas con retraso"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
):
    query = _ACTIVE_RENTAL_SELECT
    params: list = []
    conditions: list[str] = []

    if customer_id is not None:
        conditions.append(f"r.customer_id = %s")
        params.append(customer_id)

    if store_id is not None:
        conditions.append(f"i.store_id = %s")
        params.append(store_id)

    if overdue_only:
        conditions.append("(CURRENT_DATE - r.rental_date::date) > f.rental_duration")

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY r.rental_date DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    rows = fetch_all(query, tuple(params))
    return rows


@router.get(
    "/active/{rental_id}",
    response_model=ActiveRental,
    summary="Detalle de renta activa",
    description="Retorna el detalle de una renta activa específica por su ID.",
)
def get_active_rental(rental_id: int):
    query = _ACTIVE_RENTAL_SELECT + " AND r.rental_id = %s"
    row = fetch_one(query, (rental_id,))
    if not row:
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
    description="Retorna el historial de rentas que ya fueron devueltas.",
)
def get_returned_rentals(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    store_id: Optional[int] = Query(None, description="Filtrar por tienda"),
    late_only: bool = Query(False, description="Solo devoluciones tardías"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
):
    query = _RETURNED_RENTAL_SELECT
    params: list = []
    conditions: list[str] = []

    if customer_id is not None:
        conditions.append("r.customer_id = %s")
        params.append(customer_id)

    if store_id is not None:
        conditions.append("i.store_id = %s")
        params.append(store_id)

    if late_only:
        conditions.append(
            "(r.return_date::date - r.rental_date::date) > f.rental_duration"
        )

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY r.return_date DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    rows = fetch_all(query, tuple(params))
    return rows


@router.get(
    "/returned/{rental_id}",
    response_model=ReturnedRental,
    summary="Detalle de devolución",
    description="Retorna el detalle de una renta devuelta específica por su ID.",
)
def get_returned_rental(rental_id: int):
    query = _RETURNED_RENTAL_SELECT + " AND r.rental_id = %s"
    row = fetch_one(query, (rental_id,))
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró una renta devuelta con ID {rental_id}.",
        )
    return row
