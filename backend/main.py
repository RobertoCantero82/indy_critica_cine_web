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


class RecomendarRequest(BaseModel):
    genero: Optional[str] = None
    plataforma: str
    perfil_usuario: Optional[str] = None
    prompt_personalizado: Optional[str] = None
    hora_actual: Optional[str] = None


import json

@app.post("/recomendar")
def recomendar(req: RecomendarRequest):
    """recomienda una película basándose en filtros o en un prompt personalizado con contexto de hora."""
    if req.prompt_personalizado:
        prompt = f"""
        Eres Indy, un perro crítico de cine inteligente, exigente y con mucho criterio.
        El usuario te pide una recomendación de película adaptada a su situación actual:
        - Situación/Estado de ánimo del usuario: "{req.prompt_personalizado}"
        - Hora actual del usuario: {req.hora_actual or "No especificada"}
        - Plataforma de streaming: {req.plataforma}

        Debes elegir una película real, muy conocida y de alta calidad que se ajuste perfectamente a su estado de ánimo y a la hora del día (por ejemplo, si es tarde y está cansado, sugiere una película que no sea excesivamente larga o que sea fácil de digerir; si quiere algo profundo, recomiéndale una obra maestra). La película idealmente debe estar disponible en {req.plataforma} en España.
        
        Devuelve la respuesta estrictamente como un objeto JSON válido con este formato:
        {{
          "titulo": "Título de la película en español o inglés original",
          "anio": 2010,
          "justificacion_eleccion": "Una frase corta al estilo de Indy explicando por qué esta película es la perfecta para su plan, teniendo en cuenta su estado de ánimo y la hora actual."
        }}
        Responde ÚNICAMENTE con el objeto JSON. No añadas introducciones, explicaciones adicionales, ni bloques de código markdown como ```json. Solo el JSON plano.
        """
    else:
        prompt = f"""
        Eres Indy, un perro crítico de cine inteligente, exigente y con mucho criterio.
        El usuario te pide una recomendación de película con estos filtros:
        - Género deseado: {req.genero}
        - Plataforma de streaming: {req.plataforma}
        - Perfil de espectador del usuario: {req.perfil_usuario} (que corresponde a perfiles como palomitero, independiente, fantastico, dramatico, curioso).

        Debes elegir una película real, muy conocida y de alta calidad que se ajuste perfectamente a este género y perfil, y que idealmente esté disponible en {req.plataforma} en España.
        Devuelve la respuesta estrictamente como un objeto JSON válido con este formato:
        {{
          "titulo": "Título de la película en español o inglés original",
          "anio": 2010,
          "justificacion_eleccion": "Una frase corta al estilo de Indy justificando por qué esta película es la perfecta para su plan de hoy"
        }}
        Responde ÚNICAMENTE con el objeto JSON. No añadas introducciones, explicaciones adicionales, ni bloques de código markdown como ```json. Solo el JSON plano.
        """
    try:
        # Llamar al cliente Groq del agente para obtener la recomendación
        respuesta = agente.veredicto.cliente.chat.completions.create(
            model=agente.veredicto.modelo,
            messages=[
                {"role": "system", "content": "Eres un recomendador de cine en formato JSON estricto."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=200,
        )
        texto_raw = respuesta.choices[0].message.content.strip()
        
        # Intentar limpiar posibles bloques markdown si el LLM los pone
        if texto_raw.startswith("```"):
            texto_raw = texto_raw.split("\n", 1)[1]
        if texto_raw.endswith("```"):
            texto_raw = texto_raw.rsplit("\n", 1)[0]
        texto_raw = texto_raw.strip()
        
        datos = json.loads(texto_raw)
        return datos
    except Exception as e:
        # Si falla el parseo o la llamada, devolver una película de respaldo clásica según el género
        respaldos = {
            "Acción": {"titulo": "Mad Max: Fury Road", "anio": 2015, "justificacion_eleccion": "Pura adrenalina y gasolina de la buena, colega."},
            "Comedia": {"titulo": "Superbad", "anio": 2007, "justificacion_eleccion": "Risas absurdas garantizadas, ideal para desconectar."},
            "Drama": {"titulo": "The Shawshank Redemption", "anio": 1994, "justificacion_eleccion": "Un clásico carcelario que te tocará la fibra sensible."},
            "Ciencia Ficción": {"titulo": "Interstellar", "anio": 2014, "justificacion_eleccion": "Para viajar por el espacio y doblar el tiempo desde el sofá."},
            "Terror": {"titulo": "The Conjuring", "anio": 2013, "justificacion_eleccion": "Sustos de los que te hacen saltar las palomitas."},
            "Thriller/Misterio": {"titulo": "Shutter Island", "anio": 2010, "justificacion_eleccion": "Un rompecabezas mental que te mantendrá pegado a la pantalla."},
            "Animación": {"titulo": "Spirited Away", "anio": 2001, "justificacion_eleccion": "Una obra maestra mágica para soñar despierto."}
        }
        res = respaldos.get(req.genero, {"titulo": "Inception", "anio": 2010, "justificacion_eleccion": "Un sueño dentro de un sueño para estrujarte el cerebro."})
        return res
