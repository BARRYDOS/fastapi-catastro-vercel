from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from docxtpl import DocxTemplate
import json
import io
import os

app = FastAPI(title="Catastro → DOCX", version="1.0")

# CORS Middleware de respaldo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ¡EL MIDDLEWARE MÁGICO QUE ARREGLA CORS EN VERCEL!
@app.middleware("http")
async def cors_and_preflight_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content={"detail": "Preflight OK"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Modelos Pydantic (sin cambios)
class Terreno(BaseModel):
    valor_terreno_propio: int = Field(..., ge=0)
    metros_terreno_propio: Optional[float] = None
    valor_terreno_comun: int = Field(..., ge=0)
    metros_terreno_comun: int = Field(..., ge=0)

class Construccion(BaseModel):
    valor_construccion_propia: int = Field(..., ge=0)
    metros_construccion_propia: int = Field(..., ge=0)
    valor_construccion_comun: int = Field(..., ge=0)
    metros_construccion_comun: int = Field(..., ge=0)

class Impuesto(BaseModel):
    recargo: Optional[float] = None
    multa: Optional[float] = None
    gastos: Optional[float] = None
    subsidios: Optional[float] = None
    suma: Optional[float] = None
    ultimo_periodo_pagado: Optional[str] = None
    impuesto_predial: Optional[float] = None
    cantidad_con_letra: Optional[str] = None

class Predio(BaseModel):
    clave_catastral: str = Field(..., pattern=r"^\d{3}-\d{2}-\d{3}-\d{2}-\d{2}-[A-Z0-9]+$")
    folio: int = Field(..., gt=0)
    direccion: str
    contribuyente: str
    terreno: Terreno
    construccion: Construccion
    impuesto: Impuesto

class DocumentoCatastral(BaseModel):
    archivo: str
    predio: List[Predio]

# Endpoints
@app.get("/")
@app.get("/api")
async def root():
    return {
        "message": "¡API FastAPI + Vercel + Oracle APEX = ÉXITO TOTAL! 🚀",
        "status": "ok",
        "cors": "Middleware infalible activado",
        "endpoints": ["/api", "/api/health", "/api/test-cors", "/api/generar-docx"]
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": "2025-11-25"}

@app.post("/api/generar-json")
async def generar_docx_json(doc_data: DocumentoCatastral):
    # ... mismo código que antes, pero acepta JSON directo

@app.get("/api/test-cors")
async def test_cors():
    return {"message": "¡CORS desde APEX: 100% FUNCIONANDO! 🎉", "test": "Éxito"}

@app.post("/api/generar-docx")
async def generar_docx(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Solo JSON, por favor 😊")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        doc_data = DocumentoCatastral.model_validate(data)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"JSON roto: {e}")
    except Exception as e:
        raise HTTPException(422, f"Validación falló: {e}")

    template_path = "templates/1785-003.docx"
    if not os.path.exists(template_path):
        raise HTTPException(500, f"Plantilla perdida en {template_path}")

    try:
        doc = DocxTemplate(template_path)
        doc.render(doc_data.model_dump())

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        nombre_archivo = doc_data.archivo
        if not nombre_archivo.lower().endswith(".docx"):
            nombre_archivo += ".docx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'}
        )
    except Exception as e:
        raise HTTPException(500, f"DOCX error: {str(e)}")
