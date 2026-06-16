"""
Lanzador de la Interfaz Gráfica (HTML) de Sakila.
"""

import os
import webbrowser
import time
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

# Obtener puerto de la API o usar 8000 por defecto
port = os.getenv("API_PORT", "8000")
host = os.getenv("API_HOST", "localhost")

# Si el host es 0.0.0.0 (para docker/red), usamos localhost para abrir el navegador
if host == "0.0.0.0":
    host = "localhost"

url = f"http://{host}:{port}/"

def launch():
    print(f"🚀 Abriendo Dashboard de Sakila en: {url}")
    print("Asegúrate de que el servidor (main.py) esté corriendo.")
    
    # Abrir el navegador predeterminado
    webbrowser.open(url)

if __name__ == "__main__":
    launch()
