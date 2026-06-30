"""
Modelos Pydantic utilizados como esquemas de respuesta de la API REST.
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────────
#  Rentas activas (películas que aún no han sido
#  devueltas — return_date IS NULL)
# ─────────────────────────────────────────────────
class ActiveRental(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rental_id: int
    rental_date: datetime
    customer_id: int
    customer_name: str
    customer_email: Optional[str]
    film_id: int
    film_title: str
    inventory_id: int
    store_id: int
    staff_id: int
    rental_duration: int          # días que tiene permitido tener la película
    days_rented: int              # días que lleva rentada hasta hoy
    overdue: bool                 # True si ya superó el tiempo permitido


# ─────────────────────────────────────────────────
#  Películas devueltas (return_date IS NOT NULL)
# ─────────────────────────────────────────────────
class ReturnedRental(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rental_id: int
    rental_date: datetime
    return_date: datetime
    customer_id: int
    customer_name: str
    customer_email: Optional[str]
    film_id: int
    film_title: str
    inventory_id: int
    store_id: int
    staff_id: int
    rental_duration_days: int     # días que estuvo rentada
    on_time: bool                 # True si fue devuelta a tiempo


# ─────────────────────────────────────────────────
#  Pagos
# ─────────────────────────────────────────────────
class Payment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    customer_id: int
    customer_name: str
    customer_email: Optional[str]
    staff_id: int
    rental_id: int
    amount: Decimal
    payment_date: datetime


# ─────────────────────────────────────────────────
#  Resumen de pagos por cliente
# ─────────────────────────────────────────────────
class CustomerPaymentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    customer_name: str
    customer_email: Optional[str]
    total_payments: int
    total_amount: Decimal


# ─────────────────────────────────────────────────
#  Modelos para API externa de Clientes
# ─────────────────────────────────────────────────
class Cliente(BaseModel):
    customer_id: int
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    dni: Optional[str] = None
    store_id: Optional[int] = None
    estado: Optional[str] = None
    fecha_registro: Optional[str] = None

class ClientesResponse(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
    items: list[Cliente]


# ─────────────────────────────────────────────────
#  Respuesta genérica de error
# ─────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    detail: str

