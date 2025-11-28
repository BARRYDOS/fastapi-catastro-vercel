"""
Handler para Vercel - Este archivo es el punto de entrada
Coloca este archivo en: api/main.py
"""
from mangum import Mangum
from index import app

# Mangum convierte FastAPI para que funcione en Vercel
handler = Mangum(app)
