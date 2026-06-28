# veredicto.py — herramienta 2: el llm genera cada sección del informe por separado

import os
import json
from abc import ABC, abstractmethod
from groq import Groq
from agente.sistema import SYSTEM_PROMPT, PERFILES
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")



class Veredicto:
    """
    genera el informe completo de indy sección por sección.
    cada método privado hace una llamada al llm para su parte del informe.
    el método ejecutar los orquesta todos y devuelve el json final.
    """

    def __init__(self):
        self.cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.modelo = "llama-3.1-8b-instant"

    # — método auxiliar: llamada al llm —

    def _llamar_llm(self, prompt: str, max_tokens: int = 300) -> str:
        """
        hace una llamada al llm con el system prompt de indy.
        devuelve el texto de respuesta limpio.
        """
        respuesta = self.cliente.chat.completions.create(
            model=self.modelo,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return respuesta.choices[0].message.content.strip()

    # — sección 1: de qué va —

    def _generar_de_que_va(self, datos: dict) -> str:
        """sinopsis sin spoilers en tono colega de bar."""
        prompt = f"""
La película es "{datos['titulo']}" ({datos['anio']}).
Géneros: {', '.join(datos['generos'])}
Director: {datos.get('director', 'desconocido')}

TAREA: Escribe 2-3 frases describiendo la PREMISA de esta película, como si se lo contaras a un amigo en un bar antes de entrar al cine.

PREMISA significa: el punto de partida. Quién es el protagonista y cuál es su situación inicial. NADA más.

PROHIBIDO absolutamente:
- Mencionar qué le pasa al protagonista durante la película
- Revelar si algo sale bien o mal
- Usar palabras como: "descubrirá", "aprenderá", "logrará", "conseguirá", "resultará", "acaba", "termina", "pero", "sin embargo", "hasta que"
- Hablar del desarrollo o el desenlace
- Parafrasear la sinopsis oficial

EJEMPLO de lo que NO quiero (spoiler): "Woody es un juguete que se ve separado de su dueño y debe encontrar el camino de vuelta"
EJEMPLO de lo que SÍ quiero (premisa): "Woody es el juguete favorito de Andy, un niño que lo tiene en un pedestal... hasta que llega un recién llegado que amenaza su trono"

Tono cercano, con chispa, directo. Sin tecnicismos.
Solo devuelve el texto, sin etiquetas ni explicaciones.
"""
        return self._llamar_llm(prompt, max_tokens=200)

    # — sección 2: crítica vs público —

    def _generar_critica_vs_publico(self, datos: dict) -> dict:
        """analiza la divergencia entre crítica y público."""
        critica = datos.get("puntuacion_critica")
        publico = datos.get("puntuacion_publico")

        if critica is None and publico is None:
            return {
                "puntuacion_critica": None,
                "puntuacion_publico": None,
                "diferencia": None,
                "quien_gana": "sin datos",
                "comentario": "No he encontrado puntuaciones para esta película.",
            }

        diferencia = round((publico or 0) - (critica or 0), 1)
        if diferencia > 0.5:
            quien_gana = "publico"
        elif diferencia < -0.5:
            quien_gana = "critica"
        else:
            quien_gana = "empate"

        prompt = f"""
La película "{datos['titulo']}" tiene estas puntuaciones:
- Crítica especializada: {critica}/10
- Público general: {publico}/10
- Diferencia: {diferencia} puntos

Escribe UNA frase mordaz y con personalidad comentando esta situación.
- Si la crítica gana: defiende al público, cuestiona a los críticos con humor
- Si el público gana: celebra que el pueblo tiene razón, lánzate contra los snobs
- Si hay empate: comenta el consenso con algo de ironía
Indy siempre está del lado del público. Sé directo y con chispa.
Solo devuelve la frase, sin etiquetas ni explicaciones.
"""
        comentario = self._llamar_llm(prompt, max_tokens=150)

        return {
            "puntuacion_critica": critica,
            "puntuacion_publico": publico,
            "diferencia": diferencia,
            "quien_gana": quien_gana,
            "comentario": comentario,
        }

    # — sección 3: índice de giros —

    def _generar_indice_giros(self, datos: dict) -> str:
        """asigna una de las 4 etiquetas de giros de guion."""
        prompt = f"""
La película es "{datos['titulo']}" ({datos['anio']}).
Géneros: {', '.join(datos['generos'])}
Sinopsis: {datos['sinopsis']}

Elige EXACTAMENTE una de estas cuatro etiquetas según los giros de guion de la película.
Debes devolver la etiqueta COMPLETA, incluyendo el emoji y el texto:
- 🎯 Predecible
- 🤔 Alguna sorpresa
- 😮 Bastantes giros
- 🤯 No te fíes de nadie

Devuelve ÚNICAMENTE una de esas cuatro opciones exactas, copiada tal cual. Sin explicaciones, sin puntos, sin nada más.
"""
        respuesta = self._llamar_llm(prompt, max_tokens=20).strip()

        # validación: si no devuelve una etiqueta válida busco coincidencia parcial
        etiquetas_validas = ["🎯 Predecible", "🤔 Alguna sorpresa", "😮 Bastantes giros", "🤯 No te fíes de nadie"]
        for etiqueta in etiquetas_validas:
            if etiqueta in respuesta:
                return etiqueta

        # fallback si el llm devuelve solo el emoji
        if "🎯" in respuesta:
            return "🎯 Predecible"
        elif "🤔" in respuesta:
            return "🤔 Alguna sorpresa"
        elif "😮" in respuesta:
            return "😮 Bastantes giros"
        elif "🤯" in respuesta:
            return "🤯 No te fíes de nadie"

        return "🤔 Alguna sorpresa"

    # — sección 4: post-créditos —

    def _generar_post_creditos(self, datos: dict) -> str:
        """
        devuelve el indicador de post-créditos.
        si aftercredits no lo sabe, el llm intenta inferirlo.
        """
        if datos.get("post_creditos") in ["sí", "no"]:
            return datos["post_creditos"]

        # fallback: el llm intenta inferirlo
        prompt = f"""
La película es "{datos['titulo']}" ({datos['anio']}).
Géneros: {', '.join(datos['generos'])}

¿Tiene escenas post-créditos? Responde SOLO con una de estas tres opciones:
sí / no / desconocido
Sin explicaciones ni texto adicional.
"""
        respuesta = self._llamar_llm(prompt, max_tokens=10).lower()
        if "sí" in respuesta or "si" in respuesta:
            return "sí"
        elif "no" in respuesta:
            return "no"
        else:
            return "desconocido"

    # — sección 5: banda sonora —

    def _generar_banda_sonora(self, datos: dict) -> dict:
        """compositor, álbum y búsqueda en youtube."""
        compositor = datos.get("compositor") or None

        prompt = f"""
La película es "{datos['titulo']}" ({datos['anio']}).
Director: {datos.get('director', 'desconocido')}
{"Compositor conocido: " + compositor if compositor else "El compositor no está disponible — infiere quién compuso la banda sonora basándote en tu conocimiento de la película."}

Devuelve SOLO un JSON con esta estructura exacta, sin texto adicional:
{{"compositor": "nombre del compositor real", "album": "nombre del álbum de la banda sonora", "url_youtube": "https://www.youtube.com/results?search_query=titulo+soundtrack"}}

Para url_youtube construye la URL con el título de la película y "soundtrack" o "banda sonora oficial".
Si no conoces el compositor con certeza, pon "Compositor desconocido" en el campo compositor.
Solo el JSON, sin explicaciones.
"""
        try:
            raw = self._llamar_llm(prompt, max_tokens=150)
            return json.loads(raw)
        except Exception:
            titulo_busqueda = datos['titulo'].replace(" ", "+")
            return {
                "compositor": compositor,
                "album": "no disponible",
                "url_youtube": f"https://www.youtube.com/results?search_query={titulo_busqueda}+soundtrack",
            }

    # — sección 6: snack —

    def _generar_snack(self, datos: dict) -> dict:
        """el llm elige el snack perfecto para esta película."""
        prompt = f"""
La película es "{datos['titulo']}" ({datos['anio']}).
Géneros: {', '.join(datos['generos'])}
Director: {datos.get('director', 'desconocido')}

Elige el snack perfecto para ver esta película. Sé creativo y específico — nada de "palomitas" a secas.
Piensa en el tono de la película, su género, su época o su director para encontrar algo original.
Ejemplos del nivel de creatividad que buscamos: "gin tonic con hielo porque la película te va a dejar frío",
"chuches ácidas para los giros de guion", "whisky solo como el protagonista".
Justifícalo en una frase corta con humor e ingenio.
Devuelve SOLO un JSON con esta estructura exacta, sin texto adicional:
{{"snack": "...", "justificacion": "..."}}
"""
        try:
            raw = self._llamar_llm(prompt, max_tokens=150)
            return json.loads(raw)
        except Exception:
            return {"snack": "palomitas con mantequilla", "justificacion": "el clásico que nunca falla."}

    # — sección 7: alerta indy —

    def _generar_alerta_indy(self, datos: dict) -> str | None:
        """
        solo se activa si doesthedogdie confirma que los perros
        tienen un papel relevante en la película.
        """
        if not datos.get("alerta_indy"):
            return None

        prompt = f"""
La película "{datos['titulo']}" tiene perros con un papel relevante.
Escribe una advertencia corta y emotiva al estilo de Indy — con personalidad canina,
recordando que esta sección es un homenaje a un perro llamado Indy.
Una o dos frases máximo. Solo el texto, sin etiquetas.
"""
        return self._llamar_llm(prompt, max_tokens=100)

    # — sección 8: alternativas —

    def _generar_alternativas(self, datos: dict, veredicto_negativo: bool) -> list | None:
        """
        solo se genera si el veredicto es negativo.
        devuelve 2-3 películas alternativas mejores.
        """
        if not veredicto_negativo:
            return None

        prompt = f"""
La película "{datos['titulo']}" ({datos['anio']}) no merece la pena.
Géneros: {', '.join(datos['generos'])}
Director: {datos.get('director')}

Sugiere 2-3 películas alternativas mejores, relacionadas por género o temática.
Devuelve SOLO un JSON con esta estructura exacta:
["Título película 1", "Título película 2", "Título película 3"]
Sin texto adicional, solo el JSON.
"""
        try:
            raw = self._llamar_llm(prompt, max_tokens=100)
            return json.loads(raw)
        except Exception:
            return None

    def _llamar_llm_libre(self, prompt: str, max_tokens: int = 350) -> str:
        """llamada al llm sin el system prompt JSON — para texto libre."""
        respuesta = self.cliente.chat.completions.create(
            model=self.modelo,
            messages=[
                {"role": "system", "content": "Eres Indy, un crítico de cine con criterio propio, directo y con personalidad. Responde siempre en español."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=max_tokens,
        )
        return respuesta.choices[0].message.content.strip()

    # — sección 9: veredicto final —

    def _generar_veredicto_final(self, datos: dict, perfil: str) -> dict:
        """
        el veredicto es texto libre — indy decide cómo contarlo.
        también decide si es positivo o negativo para el flujo de alternativas.
        """
        descripcion_perfil = PERFILES.get(perfil, "espectador general")

        prompt = f"""
Película: "{datos['titulo']}" ({datos['anio']})
Géneros: {', '.join(datos['generos'])}
Director: {datos.get('director', 'desconocido')}
Puntuación crítica: {datos.get('puntuacion_critica')}/10
Puntuación público: {datos.get('puntuacion_publico')}/10
Perfil del espectador: {descripcion_perfil}

Responde EXACTAMENTE en este formato, sin nada más:

RECOMENDACIÓN: SÍ
RAZÓN: [frase de 8-12 palabras que explique POR QUÉ es recomendable para este perfil concreto. Ejemplo: "Un thriller de ritmo trepidante perfecto para el que busca adrenalina"]
PÁRRAFO: [3-4 frases con tu opinión como Indy. Con criterio y personalidad. Sin repetir la razón. Sin mencionar las puntuaciones con números. Adaptado al perfil del espectador.]

O si no la recomiendas:

RECOMENDACIÓN: NO
RAZÓN: [frase de 8-12 palabras explicando por qué NO encaja con este perfil]
PÁRRAFO: [3-4 frases honestas. Sin piedad pero con clase.]
"""
        raw = self._llamar_llm_libre(prompt, max_tokens=350)

        import re

        recomendacion = "SÍ"
        razon = ""
        parrafo = raw.strip()

        # extraer RECOMENDACIÓN
        m = re.search(r'RECOMENDACI[OÓ]N\s*:\s*(.+)', raw, re.IGNORECASE)
        if m:
            val = m.group(1).strip().upper()
            recomendacion = "SÍ" if any(x in val for x in ("SÍ", "SI", "YES")) else "NO"

        # extraer RAZÓN (una línea)
        m = re.search(r'RAZ[OÓ]N\s*:\s*(.+)', raw, re.IGNORECASE)
        if m:
            razon = m.group(1).strip()

        # extraer PÁRRAFO (puede ser multilínea — todo lo que sigue hasta fin de texto)
        m = re.search(r'P[AÁ]RRAFO\s*:\s*(.+)', raw, re.IGNORECASE | re.DOTALL)
        if m:
            parrafo = m.group(1).strip()

        es_negativo = recomendacion == "NO"
        return {
            "recomendacion": recomendacion,
            "razon": razon,
            "parrafo": parrafo,
            "es_negativo": es_negativo,
            "texto": parrafo,
        }

    # — método principal —

    def ejecutar(
        self,
        datos_pelicula: dict,
        perfil_usuario: str,
        nombre_usuario: str = None,
    ) -> dict:
        """
        orquesta todas las secciones del informe.
        devuelve el informe completo como dict o un error si algo falla.
        """
        try:
            veredicto = self._generar_veredicto_final(datos_pelicula, perfil_usuario)

            informe = {
                "titulo_anio": f"{datos_pelicula.get('titulo')} ({datos_pelicula.get('anio')})",
                "de_que_va": self._generar_de_que_va(datos_pelicula),
                "critica_vs_publico": self._generar_critica_vs_publico(datos_pelicula),
                "indice_giros": self._generar_indice_giros(datos_pelicula),
                "post_creditos": self._generar_post_creditos(datos_pelicula),
                "streaming_espana": datos_pelicula.get("streaming_espana", []),
                "banda_sonora": self._generar_banda_sonora(datos_pelicula),
                "snack": self._generar_snack(datos_pelicula),
                "alerta_indy": self._generar_alerta_indy(datos_pelicula),
                "alternativas": self._generar_alternativas(datos_pelicula, veredicto["es_negativo"]),
                "veredicto": veredicto["parrafo"],
                "veredicto_recomendacion": veredicto["recomendacion"],
                "veredicto_razon": veredicto["razon"],
            }

            return {"ok": True, "informe": informe}

        except Exception as e:
            return {"ok": False, "error": f"error generando el informe — {str(e)}"}