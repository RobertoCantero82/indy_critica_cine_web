# main.py — api fastapi del agente indy

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from agente.indy import IndyAgent

app = FastAPI(title="Indy API", version="1.0.0")

# cors para el frontend react
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agente = IndyAgent()


class ConsultaRequest(BaseModel):
    titulo: str
    perfil_usuario: str
    anio: Optional[int] = None
    nombre_usuario: Optional[str] = None
    forzar_nuevo: bool = False


class CacheRequest(BaseModel):
    titulo: str


@app.get("/")
def root():
    return {"status": "Indy está listo 🐾"}


@app.post("/cache")
def comprobar_cache(req: CacheRequest):
    """comprueba si la película ya tiene informe guardado."""
    cache = agente.comprobar_cache(req.titulo)
    if cache:
        return {"cache": True, "informe": cache["informe"], "fecha_consulta": cache["fecha_consulta"]}
    return {"cache": False}


@app.post("/analizar")
def analizar(req: ConsultaRequest):
    """ejecuta el agente y devuelve el informe completo."""
    resultado = agente.ejecutar(
        titulo=req.titulo,
        perfil_usuario=req.perfil_usuario,
        anio=req.anio,
        nombre_usuario=req.nombre_usuario,
        forzar_nuevo=req.forzar_nuevo,
    )

    if not resultado["ok"]:
        errores = resultado.get("errores_parciales", [])
        detalle = resultado.get("error", "error desconocido")
        if errores:
            detalle += f" → {errores[-1]}"
        raise HTTPException(status_code=500, detail=detalle)

    return resultado
