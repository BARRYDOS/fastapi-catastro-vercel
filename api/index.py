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
    valor_terreno_propio: Optional[str] = None
    metros_terreno_propio: Optional[str] = None
    valor_terreno_comun: Optional[str] = None
    metros_terreno_comun: Optional[str] = None

class Construccion(BaseModel):
    valor_construccion_propia: Optional[str] = None
    metros_construccion_propia: Optional[str] = None
    valor_construccion_comun: Optional[str] = None
    metros_construccion_comun: Optional[str] = None

class Impuesto(BaseModel):
    recargo: Optional[str] = None
    multa: Optional[str] = None
    gastos: Optional[str] = None
    subsidios: Optional[str] = None
    suma: Optional[str] = None
    ultimo_periodo_pagado: Optional[str] = None
    impuesto_predial: Optional[str] = None
    monto_a_pagar: Optional[str] = None
    cantidad_con_letra: Optional[str] = None

class Documento(BaseModel):
    fecha_actual: Optional[str] = None
    tipo_documento: int = Field
    fecha_documento: Optional[str] = None
    fecha_ini_vigencia: Optional[str] = None
    fecha_fin_vigencia: Optional[str] = None


class Predio(BaseModel):
    clave_catastral: Optional[str] = None
    folio: int = Field
    direccion: Optional[str] = None
    contribuyente: Optional[str] = None
    terreno: Terreno
    construccion: Construccion
    impuesto: Impuesto
    documento: Documento

class DocumentoCatastral(BaseModel):
    archivo: Optional[str] = None
    plantilla_tipo_documento: Optional[str] = None
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
        raise HTTPException(400, "Solo archivos .json")

    try:
        content = await file.read()
        data = json.loads(content)
        doc_data = DocumentoCatastral.model_validate(data)
    except Exception as e:
        raise HTTPException(422, f"Error en validación: {str(e)}")

    # Cargar plantilla
    template_path = "templates/"+doc_data.plantilla_tipo_documento
    if not os.path.exists(template_path):
        raise HTTPException(500, "Plantilla no encontrada")

    doc = DocxTemplate(template_path)

    # Renderizar
    doc.render(doc_data.model_dump())

    # Guardar en memoria
    #output = io.BytesIO()
    #doc.save(output)
    doc.save(doc_data.archivo)
    #output.seek(0)

    # Nombre del archivo de salida
    nombre_salida = doc_data.archivo.replace(".docx", "_generado.docx")

    #return StreamingResponse(
    #    output,
    #    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    #    headers={"Content-Disposition": f"attachment; filename={doc_data.archivo}"},
    #)




    # Convertir un solo archivo
    # convert(doc_data.archivo, "output.pdf")

    return FileResponse(
            path=doc_data.archivo,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            # media_type="application/pdf"
            # filename="Datos históricos por sitio.docx"   # nombre que verá el usuario
    )
