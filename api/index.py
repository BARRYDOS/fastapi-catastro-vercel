from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import json
import os
import tempfile

app = FastAPI()

# CORS - Permite llamadas desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: específica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELOS =====
class Terreno(BaseModel):
    valor_terreno_propio: str
    metros_terreno_propio: str
    valor_terreno_comun: str
    metros_terreno_comun: str

class Construccion(BaseModel):
    valor_construccion_propia: str
    metros_construccion_propia: str
    valor_construccion_comun: str
    metros_construccion_comun: str

class Impuesto(BaseModel):
    impuesto_predial: str
    cantidad_con_letra: str

class Predio(BaseModel):
    clave_catastral: str
    folio: int
    direccion: str
    contribuyente: str
    terreno: Terreno
    construccion: Construccion
    impuesto: Impuesto

class DatosRequest(BaseModel):
    archivo: str
    predio: List[Predio]

# ===== ENDPOINTS =====
@app.get("/")
def root():
    return {"status": "ok", "message": "API funcionando correctamente"}

@app.get("/api")
def api_root():
    return {"status": "ok", "endpoints": ["/api/generar-docx"]}

@app.post("/api/generar-docx")
async def generar_docx(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Solo se permiten archivos .json")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        doc_data = DocumentoCatastral.model_validate(data)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"JSON inválido: {e}")
    except Exception as e:
        raise HTTPException(422, f"Error de validación: {e}")

    template_path = "./1785-003.docx"
    if not os.path.exists(template_path):
        raise HTTPException(500, "Plantilla no encontrada en /templates")

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
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Error al generar DOCX: {str(e)}")

# Vercel necesita que exportes 'app'
# No agregues 'handler' ni nada más al final
