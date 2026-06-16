"""
Router para el módulo de PAGOS.

Endpoints:
  GET /payments                        – Lista paginada de todos los pagos
  GET /payments/{payment_id}           – Detalle de un pago específico
  GET /payments/customer/{customer_id} – Todos los pagos de un cliente
  GET /payments/summary                – Resumen total de pagos por cliente
  GET /payments/rental/{rental_id}     – Pagos asociados a una renta específica
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from api.database import fetch_all, fetch_one
from api.models import Payment, CustomerPaymentSummary

router = APIRouter(prefix="/payments", tags=["Pagos"])


# ─────────────────────────────────────────────
#  Fragmento SELECT reutilizable
# ─────────────────────────────────────────────
_PAYMENT_SELECT = """
SELECT
    p.payment_id,
    p.customer_id,
    (c.first_name || ' ' || c.last_name) AS customer_name,
    c.email                               AS customer_email,
    p.staff_id,
    p.rental_id,
    p.amount,
    p.payment_date
FROM payment p
JOIN customer c ON c.customer_id = p.customer_id
"""


@router.get(
    "",
    response_model=list[Payment],
    summary="Listado de pagos",
    description=(
        "Retorna todos los pagos registrados. "
        "Soporta filtros opcionales por cliente y rgo de fechas."
    ),
)
def get_payments(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    date_from: Optional[str] = Query(
        None, description="Fecha inicial (YYYY-MM-DD)", example="2007-01-01"
    ),
    date_to: Optional[str] = Query(
        None, description="Fecha final (YYYY-MM-DD)", example="2007-06-30"
    ),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
):
    query = _PAYMENT_SELECT
    params: list = []
    conditions: list[str] = []

    if customer_id is not None:
        conditions.append("p.customer_id = %s")
        params.append(customer_id)

    if date_from:
        conditions.append("p.payment_date >= %s::timestamp")
        params.append(date_from)

    if date_to:
        conditions.append("p.payment_date <= (%s::date + interval '1 day')::timestamp")
        params.append(date_to)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY p.payment_date DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    return fetch_all(query, tuple(params))


@router.get(
    "/summary",
    response_model=list[CustomerPaymentSummary],
    summary="Resumen de pagos por cliente",
    description="Retorna el total de pagos y monto acumulado agrupado por cliente.",
)
def get_payment_summary(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = """
    SELECT
        c.customer_id,
        (c.first_name || ' ' || c.last_name) AS customer_name,
        c.email                               AS customer_email,
        COUNT(p.payment_id)                   AS total_payments,
        COALESCE(SUM(p.amount), 0)            AS total_amount
    FROM customer c
    LEFT JOIN payment p ON p.customer_id = c.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.email
    ORDER BY total_amount DESC
    LIMIT %s OFFSET %s
    """
    return fetch_all(query, (limit, offset))


@router.get(
    "/customer/{customer_id}",
    response_model=list[Payment],
    summary="Pagos de un cliente",
    description="Retorna todos los pagos realizados por un cliente específico.",
)
def get_payments_by_customer(
    customer_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = (
        _PAYMENT_SELECT
        + " WHERE p.customer_id = %s"
        + " ORDER BY p.payment_date DESC LIMIT %s OFFSET %s"
    )
    rows = fetch_all(query, (customer_id, limit, offset))
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron pagos para el cliente con ID {customer_id}.",
        )
    return rows


@router.get(
    "/rental/{rental_id}",
    response_model=list[Payment],
    summary="Pagos de una renta",
    description="Retorna los pagos asociados a una renta específica.",
)
def get_payments_by_rental(rental_id: int):
    query = _PAYMENT_SELECT + " WHERE p.rental_id = %s ORDER BY p.payment_date"
    rows = fetch_all(query, (rental_id,))
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron pagos para la renta con ID {rental_id}.",
        )
    return rows


@router.get(
    "/{payment_id}",
    response_model=Payment,
    summary="Detalle de un pago",
    description="Retorna el detalle de un pago específico por su ID.",
)
def get_payment(payment_id: int):
    query = _PAYMENT_SELECT + " WHERE p.payment_id = %s"
    row = fetch_one(query, (payment_id,))
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el pago con ID {payment_id}.",
        )
    return row
