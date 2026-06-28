# buscador.py — herramienta 1: obtiene datos de la película desde apis externas

import os
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class Herramienta(ABC):
    """clase base para todas las herramientas del agente indy."""

    @abstractmethod
    def ejecutar(self, **kwargs) -> dict:
        raise NotImplementedError


class Buscador(Herramienta):

    def __init__(self):
        self.omdb_key = os.getenv("OMDB_API_KEY")
        self.tmdb_key = os.getenv("TMDB_API_KEY")
        self.streaming_key = os.getenv("STREAMING_API_KEY")
        self.dogdie_key = os.getenv("DOESTHEDOGDIE_API_KEY")
        self.youtube_key = os.getenv("YOUTUBE_API_KEY")
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def _titulo_en_ingles(self, titulo: str) -> str | None:
        """usa el llm para obtener el título original en inglés de una película."""
        import re
        try:
            resp = self.groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "user",
                    "content": (
                        f"What is the original English title of the movie '{titulo}'? "
                        "Reply with ONLY the English title. No year, no parentheses, no explanations. "
                        "Examples: 'El Padrino' → 'The Godfather' | 'Cazafantasmas' → 'Ghostbusters' | 'Inception' → 'Inception'"
                    ),
                }],
                temperature=0,
                max_tokens=20,
            )
            raw = resp.choices[0].message.content.strip()
            # eliminar años, paréntesis, comillas y texto extra
            titulo_en = re.sub(r'\s*\(.*?\)', '', raw)  # quita (1984), (film), etc.
            titulo_en = titulo_en.strip().strip('"').strip("'").strip()
            return titulo_en if titulo_en else None
        except Exception:
            return None

    def _buscar_omdb(self, titulo: str) -> dict:
        """búsqueda fuzzy en omdb con ?s= — útil cuando ?t= no encuentra exacto."""
        try:
            resp = requests.get(
                "http://www.omdbapi.com/",
                params={"apikey": self.omdb_key, "s": titulo, "type": "movie"},
                timeout=5,
            )
            datos = resp.json()
            if datos.get("Response") != "True" or not datos.get("Search"):
                return {"ok": False, "error": "sin resultados"}
            # primer resultado → consultamos por imdbID para tener todos los datos
            imdb_id = datos["Search"][0]["imdbID"]
            resp2 = requests.get(
                "http://www.omdbapi.com/",
                params={"apikey": self.omdb_key, "i": imdb_id},
                timeout=5,
            )
            datos2 = resp2.json()
            if datos2.get("Response") != "True":
                return {"ok": False, "error": "sin datos del film"}
            critica = publico = None
            for r in datos2.get("Ratings", []):
                if r["Source"] == "Rotten Tomatoes":
                    critica = float(r["Value"].replace("%", "")) / 10
                if r["Source"] == "Internet Movie Database":
                    publico = float(r["Value"].split("/")[0])
            return {
                "ok": True,
                "titulo": datos2.get("Title"),
                "anio": datos2.get("Year"),
                "duracion_min": datos2.get("Runtime"),
                "generos": datos2.get("Genre", "").split(", "),
                "director": datos2.get("Director"),
                "sinopsis": datos2.get("Plot"),
                "puntuacion_critica": critica,
                "puntuacion_publico": publico,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _consultar_omdb(self, titulo: str, anio: int = None) -> dict:
        """puntuaciones y metadatos básicos desde omdb."""
        try:
            params = {"apikey": self.omdb_key, "t": titulo, "type": "movie"}
            if anio:
                params["y"] = anio

            respuesta = requests.get(
                "http://www.omdbapi.com/",
                params=params,
                timeout=5
            )
            datos = respuesta.json()
            if datos.get("Response") != "True":
                return {"ok": False, "error": datos.get("Error", "sin respuesta")}

            critica = None
            publico = None
            for rating in datos.get("Ratings", []):
                if rating["Source"] == "Rotten Tomatoes":
                    critica = float(rating["Value"].replace("%", "")) / 10
                if rating["Source"] == "Internet Movie Database":
                    publico = float(rating["Value"].split("/")[0])

            return {
                "ok": True,
                "titulo": datos.get("Title"),
                "anio": datos.get("Year"),
                "duracion_min": datos.get("Runtime"),
                "generos": datos.get("Genre", "").split(", "),
                "director": datos.get("Director"),
                "sinopsis": datos.get("Plot"),
                "puntuacion_critica": critica,
                "puntuacion_publico": publico,
            }

        except Exception as e:
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    def _consultar_tmdb(self, titulo: str) -> dict:
        """sinopsis en español y compositor desde tmdb."""
        try:
            busqueda = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={"api_key": self.tmdb_key, "query": titulo, "language": "es-ES"},
                timeout=5,
            )
            resultados = busqueda.json().get("results", [])

            if not resultados:
                return {"ok": False, "error": "película no encontrada en tmdb"}

            tmdb_id = resultados[0]["id"]

            detalle = requests.get(
                f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                params={"api_key": self.tmdb_key, "language": "es-ES", "append_to_response": "credits"},
                timeout=5,
            )
            datos = detalle.json()

            compositor = None
            for persona in datos.get("credits", {}).get("crew", []):
                if persona.get("job") == "Original Music Composer":
                    compositor = persona.get("name")
                    break

            return {
                "ok": True,
                "sinopsis": datos.get("overview"),
                "compositor": compositor,
                "titulo_original": datos.get("original_title"),
            }

        except Exception as e:
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    def _consultar_streaming(self, titulo: str) -> dict:
        """plataformas de streaming disponibles en españa — api v4."""
        try:
            respuesta = requests.get(
                "https://streaming-availability.p.rapidapi.com/shows/search/title",
                headers={
                    "X-RapidAPI-Key": self.streaming_key,
                    "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com",
                },
                params={"title": titulo, "country": "es", "show_type": "movie"},
                timeout=10,
            )
            datos = respuesta.json()
            plataformas = []
            # nueva estructura v4: lista de shows con streamingOptions
            for show in datos if isinstance(datos, list) else []:
                opciones = show.get("streamingOptions", {}).get("es", [])
                for opcion in opciones:
                    servicio = opcion.get("service", {}).get("name", "")
                    if servicio and servicio not in plataformas:
                        plataformas.append(servicio)

            return {"ok": True, "plataformas": plataformas}

        except Exception as e:
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    def _consultar_post_creditos(self, titulo: str) -> dict:
        """indica si la película tiene escenas post-créditos."""
        try:
            titulo_url = titulo.lower().replace(" ", "-")
            respuesta = requests.get(
                f"https://aftercredits.com/movie/{titulo_url}/",
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"},
            )

            if respuesta.status_code != 200:
                return {"ok": False, "error": "página no encontrada"}

            texto = respuesta.text.lower()
            if "yes" in texto or "there is" in texto:
                return {"ok": True, "post_creditos": "sí"}
            elif "no" in texto or "there are no" in texto:
                return {"ok": True, "post_creditos": "no"}
            else:
                return {"ok": True, "post_creditos": "desconocido"}

        except Exception as e:
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    def _consultar_alerta_indy(self, titulo: str) -> dict:
        """comprueba si los perros tienen un papel relevante en la película."""
        try:
            respuesta = requests.get(
                "https://www.doesthedogdie.com/media/search",
                params={"q": titulo},
                headers={"Accept": "application/json", "X-API-KEY": self.dogdie_key},
                timeout=10,
            )
            if respuesta.status_code != 200:
                return {"ok": False, "error": f"status {respuesta.status_code}"}

            datos = respuesta.json()

            for item in datos.get("data", []):
                for topico in item.get("topicItemStats", []):
                    pregunta = topico.get("topic", {}).get("simpleQuestion", "").lower()
                    if pregunta.startswith("does a dog"):
                        votos_si = topico.get("doesItYes", 0)
                        votos_no = topico.get("doesItNo", 0)
                        return {"ok": True, "alerta_indy": votos_si > votos_no}

            return {"ok": True, "alerta_indy": False}

        except Exception as e:
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    def _consultar_youtube(self, titulo: str, compositor: str = None) -> dict:
        """busca el id del video oficial de la banda sonora en youtube."""
        import re

        query = f"{titulo} soundtrack official"
        if compositor:
            query = f"{compositor} {titulo} soundtrack"

        if self.youtube_key:
            try:
                respuesta = requests.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "key": self.youtube_key,
                        "q": query,
                        "part": "snippet",
                        "type": "video",
                        "maxResults": 1,
                        "videoCategoryId": "10",
                    },
                    timeout=5,
                )
                datos = respuesta.json()
                items = datos.get("items", [])
                if not items:
                    return {"ok": False, "error": "no se encontró vídeo"}
                return {"ok": True, "video_id": items[0]["id"]["videoId"]}
            except Exception as e:
                return {"ok": False, "error": f"error api — {str(e)}"}

        # fallback sin api key: scraping de la página de resultados
        try:
            url = "https://www.youtube.com/results"
            resp = requests.get(
                url,
                params={"search_query": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=8,
            )
            ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if ids:
                return {"ok": True, "video_id": ids[0]}
            return {"ok": False, "error": "no se encontró vídeo"}
        except Exception as e:
            return {"ok": False, "error": f"error scraping — {str(e)}"}

    def ejecutar(self, titulo: str, anio: int = None) -> dict:
        """consolida los resultados de todas las fuentes."""
        resultado = {
            "titulo": None,
            "anio": None,
            "duracion_min": None,
            "generos": [],
            "director": None,
            "compositor": None,
            "sinopsis": None,
            "puntuacion_critica": None,
            "puntuacion_publico": None,
            "post_creditos": "desconocido",
            "streaming_espana": [],
            "alerta_indy": False,
            "youtube_video_id": None,
            "errores": [],
        }

        # 1) traducir título al inglés vía llm
        titulo_en = self._titulo_en_ingles(titulo) or titulo

        # 2) búsqueda exacta con el título traducido
        omdb = self._consultar_omdb(titulo_en, anio)

        # 3) búsqueda exacta con el título original si el traducido falló
        if not omdb["ok"] and titulo_en.lower() != titulo.lower():
            omdb = self._consultar_omdb(titulo, anio)

        # 4) búsqueda fuzzy (?s=) con ambos títulos como último recurso
        if not omdb["ok"]:
            omdb = self._buscar_omdb(titulo_en)
        if not omdb["ok"] and titulo_en.lower() != titulo.lower():
            omdb = self._buscar_omdb(titulo)

        if not omdb["ok"]:
            resultado["errores"].append(f"omdb: {omdb['error']}")
            return resultado

        resultado.update({
            "titulo": omdb["titulo"],
            "anio": omdb["anio"],
            "duracion_min": omdb["duracion_min"],
            "generos": omdb["generos"],
            "director": omdb["director"],
            "sinopsis": omdb["sinopsis"],
            "puntuacion_critica": omdb["puntuacion_critica"],
            "puntuacion_publico": omdb["puntuacion_publico"],
        })

        tmdb = self._consultar_tmdb(titulo)
        if tmdb["ok"]:
            if tmdb.get("sinopsis"):
                resultado["sinopsis"] = tmdb["sinopsis"]
            resultado["compositor"] = tmdb.get("compositor")
        else:
            resultado["errores"].append(f"tmdb: {tmdb['error']}")

        streaming = self._consultar_streaming(resultado["titulo"])
        if streaming["ok"]:
            resultado["streaming_espana"] = streaming["plataformas"]
        else:
            resultado["errores"].append(f"streaming: {streaming['error']}")

        post = self._consultar_post_creditos(resultado["titulo"])
        if post["ok"]:
            resultado["post_creditos"] = post["post_creditos"]
        else:
            resultado["errores"].append(f"aftercredits: {post['error']}")

        perro = self._consultar_alerta_indy(resultado["titulo"])
        if perro["ok"]:
            resultado["alerta_indy"] = perro["alerta_indy"]
        else:
            resultado["errores"].append(f"doesthedogdie: {perro['error']}")

        # youtube — id del video de la banda sonora
        yt = self._consultar_youtube(resultado["titulo"], resultado.get("compositor"))
        if yt["ok"]:
            resultado["youtube_video_id"] = yt["video_id"]
        else:
            resultado["errores"].append(f"youtube: {yt['error']}")

        return resultado