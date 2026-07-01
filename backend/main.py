# FASTAPI DEL AGENTE INDY

# importo fastapi y la excepción http para crear la api y devolver errores
from fastapi import FastAPI, HTTPException
# importo el middleware de cors para permitir peticiones desde el frontend
from fastapi.middleware.cors import CORSMiddleware
# importo basemodel para definir los esquemas de entrada de cada endpoint
from pydantic import BaseModel
# importo optional para marcar campos que no son obligatorios
from typing import Optional
# importo sys para poder modificar la ruta de búsqueda de módulos
import sys
# importo os para construir rutas de archivos de forma compatible
import os

# añado la carpeta raíz del proyecto a la ruta de búsqueda de python
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# importo la clase del agente indy desde el paquete agente
from agente.indy import IndyAgent

# creo la aplicación fastapi con un título y una versión
app = FastAPI(title="Indy API", version="1.0.0")

# cors para el frontend react
# registro el middleware de cors en la aplicación
app.add_middleware(
    # uso la clase corsmiddleware como middleware
    CORSMiddleware,
    # permito peticiones solo desde estos dos orígenes locales del frontend
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    # permito que las peticiones incluyan credenciales
    allow_credentials=True,
    # permito todos los métodos http
    allow_methods=["*"],
    # permito todas las cabeceras http
    allow_headers=["*"],
)

# defino el agente indy una sola vez para reutilizarlo en toda la api
agente = IndyAgent()


# defino el esquema de entrada para pedir un análisis de película
class ConsultaRequest(BaseModel):
    # guardo el título de la película como texto obligatorio
    titulo: str
    # guardo el perfil del usuario como texto obligatorio
    perfil_usuario: str
    # guardo el año de la película como número opcional
    anio: Optional[int] = None
    # guardo el nombre del usuario como texto opcional
    nombre_usuario: Optional[str] = None
    # guardo si se debe forzar un nuevo análisis aunque exista caché
    forzar_nuevo: bool = False
    # guardo el id de tmdb si el usuario eligió la película de la lista de candidatos con póster
    tmdb_id: Optional[int] = None


# defino el esquema de entrada para comprobar si hay caché de una película
class CacheRequest(BaseModel):
    # guardo el título de la película como texto obligatorio
    titulo: str


# defino el esquema de entrada para el autocompletado de títulos con póster
class BuscarRequest(BaseModel):
    # guardo el texto que el usuario ha escrito hasta el momento
    titulo: str


# defino el endpoint raíz para comprobar que la api está viva
@app.get("/")
def root():
    # devuelvo un mensaje simple confirmando que indy está listo
    return {"status": "Indy está listo 🐾"}


# defino el endpoint que comprueba si ya existe un informe guardado
@app.post("/cache")
def comprobar_cache(req: CacheRequest):
    """comprueba si la película ya tiene informe guardado."""
    # pido al agente que busque en caché por el título recibido
    cache = agente.comprobar_cache(req.titulo)
    # si encuentro caché devuelvo el informe guardado y la fecha
    if cache:
        # devuelvo un objeto indicando que hay caché junto con sus datos
        return {"cache": True, "informe": cache["informe"], "fecha_consulta": cache["fecha_consulta"]}
    # si no hay caché devuelvo un objeto indicando que no existe
    return {"cache": False}


# defino el endpoint que autocompleta títulos con póster para elegir la coincidencia exacta
@app.post("/buscar")
def buscar_pelicula(req: BuscarRequest):
    """
    busca coincidencias en tmdb mientras el usuario escribe, con póster y año,
    para que elija la película exacta antes de lanzar el análisis completo.
    """
    # pido al buscador del agente la lista de candidatos para el texto recibido
    resultado = agente.buscador.buscar_candidatos(req.titulo)
    # compruebo si la búsqueda de candidatos falló por un error de conexión
    if not resultado["ok"]:
        # lanzo una excepción http 502 indicando que falló el servicio externo
        raise HTTPException(status_code=502, detail=resultado["error"])
    # devuelvo la lista de candidatos encontrados aunque esté vacía
    return resultado


# defino el endpoint que ejecuta el análisis completo de una película
@app.post("/analizar")
def analizar(req: ConsultaRequest):
    """ejecuta el agente y devuelve el informe completo."""
    # ejecuto el agente pasándole todos los datos de la petición
    resultado = agente.ejecutar(
        # paso el título recibido
        titulo=req.titulo,
        # paso el perfil del usuario recibido
        perfil_usuario=req.perfil_usuario,
        # paso el año recibido
        anio=req.anio,
        # paso el nombre del usuario recibido
        nombre_usuario=req.nombre_usuario,
        # paso si se debe forzar un nuevo análisis
        forzar_nuevo=req.forzar_nuevo,
        # paso el id de tmdb si el usuario eligió la película de la lista de candidatos
        tmdb_id=req.tmdb_id,
    )

    # compruebo si el resultado indica que algo falló
    if not resultado["ok"]:
        # recojo la lista de errores parciales si existen
        errores = resultado.get("errores_parciales", [])
        # recojo el mensaje de error principal o uno genérico
        detalle = resultado.get("error", "error desconocido")
        # si hay errores parciales añado el último al detalle
        if errores:
            # concateno el último error parcial al mensaje de detalle
            detalle += f" → {errores[-1]}"
        # lanzo una excepción http 500 con el detalle del error
        raise HTTPException(status_code=500, detail=detalle)

    # devuelvo el resultado completo si todo salió bien
    return resultado


# defino el esquema de entrada para pedir una recomendación rápida
class RecomendarRequest(BaseModel):
    # guardo el género deseado como texto opcional
    genero: Optional[str] = None
    # guardo la plataforma de streaming como texto obligatorio
    plataforma: str
    # guardo el perfil del usuario como texto opcional
    perfil_usuario: Optional[str] = None
    # guardo un prompt personalizado como texto opcional
    prompt_personalizado: Optional[str] = None
    # guardo la hora actual del usuario como texto opcional
    hora_actual: Optional[str] = None


# importo json para parsear la respuesta del modelo de lenguaje
import json

# defino el endpoint que recomienda una película según filtros o prompt libre
@app.post("/recomendar")
def recomendar(req: RecomendarRequest):
    """recomienda una película basándose en filtros o en un prompt personalizado con contexto de hora."""
    # compruebo si el usuario escribió un prompt personalizado
    if req.prompt_personalizado:
        # construyo el prompt para el modelo usando el texto libre del usuario
        prompt = f"""
        Eres Indy, un perro crítico de cine inteligente, exigente y con mucho criterio.
        El usuario te pide una recomendación de película adaptada a su situación actual:
        - Situación/Estado de ánimo del usuario: "{req.prompt_personalizado}"
        - Hora actual del usuario: {req.hora_actual or "No especificada"}
        - Plataforma de streaming: {req.plataforma}

        Debes elegir una película real, muy conocida y de alta calidad que se ajuste perfectamente a su estado de ánimo y a la hora del día (por ejemplo, si es tarde y está cansado, sugiere una película que no sea excesivamente larga o que sea fácil de digerir; si quiere algo profundo, recomiéndale una obra maestra). La película idealmente debe estar disponible en {req.plataforma} en España.

        Devuelve la respuesta estrictamente como un objeto JSON válido con este formato:
        {{
          "titulo": "Título oficial de la película, corto, sin subtítulos ni descripciones añadidas",
          "anio": 2010,
          "justificacion_eleccion": "Una frase corta al estilo de Indy explicando por qué esta película es la perfecta para su plan, teniendo en cuenta su estado de ánimo y la hora actual."
        }}
        Responde ÚNICAMENTE con el objeto JSON. No añadas introducciones, explicaciones adicionales, ni bloques de código markdown como ```json. Solo el JSON plano.
        """
    # si no hay prompt personalizado uso los filtros de género y perfil
    else:
        # construyo el prompt para el modelo usando género plataforma y perfil
        prompt = f"""
        Eres Indy, un perro crítico de cine inteligente, exigente y con mucho criterio.
        El usuario te pide una recomendación de película con estos filtros:
        - Género deseado: {req.genero}
        - Plataforma de streaming: {req.plataforma}
        - Perfil de espectador del usuario: {req.perfil_usuario} (que corresponde a perfiles como palomitero, independiente, fantastico, dramatico, curioso).

        Debes elegir una película real, muy conocida y de alta calidad que se ajuste perfectamente a este género y perfil, y que idealmente esté disponible en {req.plataforma} en España.
        Devuelve la respuesta estrictamente como un objeto JSON válido con este formato:
        {{
          "titulo": "Título oficial de la película, corto, sin subtítulos ni descripciones añadidas",
          "anio": 2010,
          "justificacion_eleccion": "Una frase corta al estilo de Indy justificando por qué esta película es la perfecta para su plan de hoy"
        }}
        Responde ÚNICAMENTE con el objeto JSON. No añadas introducciones, explicaciones adicionales, ni bloques de código markdown como ```json. Solo el JSON plano.
        """
    # intento llamar al modelo y parsear su respuesta
    try:
        # uso el cliente groq del veredicto del agente para pedir la respuesta
        respuesta = agente.veredicto.cliente.chat.completions.create(
            # uso el modelo configurado en el veredicto del agente
            model=agente.veredicto.modelo,
            # paso el mensaje de sistema y el prompt construido como mensaje de usuario
            messages=[
                # defino el rol de sistema indicando que responda en json estricto
                {"role": "system", "content": "Eres un recomendador de cine en formato JSON estricto."},
                # defino el rol de usuario con el prompt construido antes
                {"role": "user", "content": prompt},
            ],
            # fijo la temperatura para dar algo de variedad a la respuesta
            temperature=0.8,
            # limito el número máximo de tokens de la respuesta
            max_tokens=200,
        )
        # extraigo el texto de la respuesta y quito espacios sobrantes
        texto_raw = respuesta.choices[0].message.content.strip()

        # compruebo si el texto empieza con un bloque de código markdown
        if texto_raw.startswith("```"):
            # quito la primera línea que contiene la marca de bloque de código
            texto_raw = texto_raw.split("\n", 1)[1]
        # compruebo si el texto termina con un bloque de código markdown
        if texto_raw.endswith("```"):
            # quito la última línea que contiene la marca de cierre del bloque
            texto_raw = texto_raw.rsplit("\n", 1)[0]
        # quito espacios sobrantes tras limpiar el texto
        texto_raw = texto_raw.strip()

        # convierto el texto limpio en un objeto python a partir del json
        datos = json.loads(texto_raw)
        # devuelvo los datos parseados como respuesta del endpoint
        return datos
    # capturo cualquier error que ocurra durante la llamada o el parseo
    except Exception as e:
        # defino un diccionario de películas de respaldo por cada género
        respaldos = {
            # asigno una película de respaldo para el género acción
            "Acción": {"titulo": "Mad Max: Fury Road", "anio": 2015, "justificacion_eleccion": "Pura adrenalina y gasolina de la buena, colega."},
            # asigno una película de respaldo para el género comedia
            "Comedia": {"titulo": "Superbad", "anio": 2007, "justificacion_eleccion": "Risas absurdas garantizadas, ideal para desconectar."},
            # asigno una película de respaldo para el género drama
            "Drama": {"titulo": "The Shawshank Redemption", "anio": 1994, "justificacion_eleccion": "Un clásico carcelario que te tocará la fibra sensible."},
            # asigno una película de respaldo para el género ciencia ficción
            "Ciencia Ficción": {"titulo": "Interstellar", "anio": 2014, "justificacion_eleccion": "Para viajar por el espacio y doblar el tiempo desde el sofá."},
            # asigno una película de respaldo para el género terror
            "Terror": {"titulo": "The Conjuring", "anio": 2013, "justificacion_eleccion": "Sustos de los que te hacen saltar las palomitas."},
            # asigno una película de respaldo para el género thriller o misterio
            "Thriller/Misterio": {"titulo": "Shutter Island", "anio": 2010, "justificacion_eleccion": "Un rompecabezas mental que te mantendrá pegado a la pantalla."},
            # asigno una película de respaldo para el género animación
            "Animación": {"titulo": "Spirited Away", "anio": 2001, "justificacion_eleccion": "Una obra maestra mágica para soñar despierto."}
        }
        # busco la película de respaldo según el género recibido o uso una por defecto
        res = respaldos.get(req.genero, {"titulo": "Inception", "anio": 2010, "justificacion_eleccion": "Un sueño dentro de un sueño para estrujarte el cerebro."})
        # devuelvo la película de respaldo como resultado del endpoint
        return res
