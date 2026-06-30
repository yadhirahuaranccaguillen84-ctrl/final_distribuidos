"""
Router para la integración con la API externa de CLIENTES.
"""

import os
import requests
from fastapi import APIRouter, HTTPException, Query
from api.models import Cliente, ClientesResponse

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# Obtener la URL de la API externa desde el .env
API_CLIENTES_BASE = os.getenv("API_CLIENTES", "http://35.239.247.220:8001/").rstrip("/")

@router.get(
    "",
    response_model=ClientesResponse,
    summary="Listado de clientes (API Externa)",
    description="Retorna el listado paginado de clientes desde la API externa administrada.",
)
def get_clientes(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Clientes por página"),
):
    url = f"{API_CLIENTES_BASE}/clientes"
    try:
        response = requests.get(url, params={"pagina": pagina, "por_pagina": por_pagina})
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="No se encontraron clientes.")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al conectar con la API externa de clientes ({url}): {str(e)}",
        )

@router.get(
    "/{customer_id}",
    response_model=Cliente,
    summary="Detalle de un cliente (API Externa)",
    description="Busca un cliente específico por su ID en la API externa.",
)
def get_cliente(customer_id: int):
    url = f"{API_CLIENTES_BASE}/clientes/{customer_id}"
    try:
        response = requests.get(url)
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró el cliente con ID {customer_id} en la API externa.",
            )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error al conectar con la API externa de clientes ({url}): {str(e)}",
        )
