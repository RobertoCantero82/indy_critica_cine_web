# OBTIENE DATOS DE LA PELÍCULA DESDE APIS

# importo os para leer variables de entorno
import os
# importo requests para hacer peticiones http a las apis externas
import requests
# importo abc y abstractmethod para definir la clase base abstracta
from abc import ABC, abstractmethod
# importo load_dotenv para cargar las variables de entorno desde el archivo .env
from dotenv import load_dotenv
# importo path para construir la ruta del archivo .env
from pathlib import Path
# importo groq para usar el cliente del modelo de lenguaje
from groq import Groq
# importo beautifulsoup para parsear html en el scraping
from bs4 import BeautifulSoup
# importo datetime para saber si una película todavía no se ha estrenado
from datetime import datetime

# cargo las variables de entorno desde el archivo .env situado dos carpetas arriba
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


# defino la clase base abstracta que deben implementar todas las herramientas
class Herramienta(ABC):
    """clase base para todas las herramientas del agente indy."""

    # declaro el método abstracto que cada herramienta debe implementar
    @abstractmethod
    def ejecutar(self, **kwargs) -> dict:
        # lanzo un error si una subclase no implementa este método
        raise NotImplementedError


# defino la clase buscador que hereda de la clase base herramienta
class Buscador(Herramienta):

    # defino el constructor que carga todas las claves de api necesarias
    def __init__(self):
        # guardo la clave de la api de omdb
        self.omdb_key = os.getenv("OMDB_API_KEY")
        # guardo la clave de la api de tmdb
        self.tmdb_key = os.getenv("TMDB_API_KEY")
        # guardo la clave de la api de streaming usando un nombre alternativo si hace falta
        self.streaming_key = os.getenv("STREAMING_API_KEY") or os.getenv("RAPIDAPI_KEY")
        # guardo la clave de la api de doesthedogdie
        self.dogdie_key = os.getenv("DOESTHEDOGDIE_API_KEY")
        # guardo la clave de la api de youtube
        self.youtube_key = os.getenv("YOUTUBE_API_KEY")
        # instancio el cliente de groq con su clave correspondiente
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # defino el método que traduce el título al inglés usando el modelo de lenguaje
    def _titulo_en_ingles(self, titulo: str) -> str | None:
        """usa el llm para obtener el título original en inglés de una película."""
        # importo re para limpiar el texto devuelto por el modelo
        import re
        # intento llamar al modelo y procesar la respuesta
        try:
            # pido al modelo el título original en inglés de la película
            resp = self.groq.chat.completions.create(
                # uso un modelo rápido y económico para esta tarea sencilla
                model="llama-3.1-8b-instant",
                # construyo el mensaje de usuario con instrucciones y ejemplos
                messages=[{
                    # defino el rol como usuario
                    "role": "user",
                    # incluyo la pregunta junto con instrucciones de formato y ejemplos
                    "content": (
                        f"What is the original English title of the movie '{titulo}'? "
                        "Reply with ONLY the English title. No year, no parentheses, no explanations. "
                        "Examples: 'El Padrino' → 'The Godfather' | 'Cazafantasmas' → 'Ghostbusters' | 'Inception' → 'Inception'"
                    ),
                }],
                # fijo la temperatura a cero para obtener una respuesta determinista
                temperature=0,
                # limito la respuesta a pocos tokens porque solo necesito un título
                max_tokens=20,
            )
            # extraigo el texto de la respuesta y quito espacios sobrantes
            raw = resp.choices[0].message.content.strip()
            # eliminar años, paréntesis, comillas y texto extra
            # quito cualquier paréntesis con su contenido como años o aclaraciones
            titulo_en = re.sub(r'\s*\(.*?\)', '', raw)  # quita (1984), (film), etc.
            # quito comillas y espacios sobrantes del título resultante
            titulo_en = titulo_en.strip().strip('"').strip("'").strip()
            # devuelvo el título limpio o none si quedó vacío
            return titulo_en if titulo_en else None
        # capturo cualquier error y devuelvo none en ese caso
        except Exception:
            # devuelvo none si la llamada al modelo falló
            return None

    # defino el método que hace una búsqueda aproximada en omdb
    def _buscar_omdb(self, titulo: str) -> dict:
        """búsqueda fuzzy en omdb con ?s= — útil cuando ?t= no encuentra exacto."""
        # intento realizar la búsqueda y manejar posibles errores
        try:
            # hago la petición de búsqueda aproximada a omdb
            resp = requests.get(
                # uso el endpoint principal de omdb
                "http://www.omdbapi.com/",
                # paso la clave de api el texto de búsqueda y el tipo de contenido
                params={"apikey": self.omdb_key, "s": titulo, "type": "movie"},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # convierto la respuesta a un diccionario json
            datos = resp.json()
            # compruebo si la respuesta indica que no hubo resultados
            if datos.get("Response") != "True" or not datos.get("Search"):
                # devuelvo un error indicando que no hubo resultados
                return {"ok": False, "error": "sin resultados"}
            # primer resultado → consultamos por imdbID para tener todos los datos
            # extraigo el identificador imdb del primer resultado encontrado
            imdb_id = datos["Search"][0]["imdbID"]
            # hago una segunda petición a omdb usando el identificador imdb
            resp2 = requests.get(
                # uso el mismo endpoint principal de omdb
                "http://www.omdbapi.com/",
                # paso la clave de api y el identificador imdb
                params={"apikey": self.omdb_key, "i": imdb_id},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # convierto la segunda respuesta a un diccionario json
            datos2 = resp2.json()
            # compruebo si la segunda respuesta no fue exitosa
            if datos2.get("Response") != "True":
                # devuelvo un error indicando que faltan datos del film
                return {"ok": False, "error": "sin datos del film"}
            # inicializo las puntuaciones de crítica y público como vacías
            critica = publico = None
            # recorro la lista de puntuaciones devueltas por omdb
            for r in datos2.get("Ratings", []):
                # compruebo si la fuente es rotten tomatoes
                if r["Source"] == "Rotten Tomatoes":
                    # convierto el porcentaje de rotten tomatoes a una escala de diez
                    critica = float(r["Value"].replace("%", "")) / 10
                # compruebo si la fuente es imdb
                if r["Source"] == "Internet Movie Database":
                    # extraigo la puntuación de imdb como número
                    publico = float(r["Value"].split("/")[0])
            # devuelvo un diccionario con todos los datos encontrados
            return {
                # indico que la búsqueda fue exitosa
                "ok": True,
                # incluyo el título de la película
                "titulo": datos2.get("Title"),
                # incluyo el año de la película
                "anio": datos2.get("Year"),
                # incluyo la duración en minutos
                "duracion_min": datos2.get("Runtime"),
                # incluyo la lista de géneros separados por coma
                "generos": datos2.get("Genre", "").split(", "),
                # incluyo el director de la película
                "director": datos2.get("Director"),
                # incluyo la sinopsis de la película
                "sinopsis": datos2.get("Plot"),
                # incluyo la puntuación de la crítica calculada antes
                "puntuacion_critica": critica,
                # incluyo la puntuación del público calculada antes
                "puntuacion_publico": publico,
            }
        # capturo cualquier excepción ocurrida durante la búsqueda
        except Exception as e:
            # devuelvo el error capturado como texto
            return {"ok": False, "error": str(e)}

    # defino el método que consulta omdb de forma exacta por título
    def _consultar_omdb(self, titulo: str, anio: int = None) -> dict:
        """puntuaciones y metadatos básicos desde omdb."""
        # intento realizar la consulta y manejar posibles errores
        try:
            # construyo los parámetros básicos de la consulta exacta
            params = {"apikey": self.omdb_key, "t": titulo, "type": "movie"}
            # añado el año a los parámetros si fue proporcionado
            if anio:
                # incluyo el año en los parámetros de búsqueda
                params["y"] = anio

            # hago la petición exacta a omdb con los parámetros construidos
            respuesta = requests.get(
                # uso el endpoint principal de omdb
                "http://www.omdbapi.com/",
                # paso los parámetros construidos antes
                params=params,
                # limito el tiempo de espera de la petición
                timeout=5
            )
            # convierto la respuesta a un diccionario json
            datos = respuesta.json()
            # compruebo si la respuesta no fue exitosa
            if datos.get("Response") != "True":
                # devuelvo el error indicado por omdb o uno genérico
                return {"ok": False, "error": datos.get("Error", "sin respuesta")}

            # inicializo la puntuación de la crítica como vacía
            critica = None
            # inicializo la puntuación del público como vacía
            publico = None
            # recorro la lista de puntuaciones devueltas por omdb
            for rating in datos.get("Ratings", []):
                # compruebo si la fuente es rotten tomatoes
                if rating["Source"] == "Rotten Tomatoes":
                    # convierto el porcentaje de rotten tomatoes a una escala de diez
                    critica = float(rating["Value"].replace("%", "")) / 10
                # compruebo si la fuente es imdb
                if rating["Source"] == "Internet Movie Database":
                    # extraigo la puntuación de imdb como número
                    publico = float(rating["Value"].split("/")[0])

            # devuelvo un diccionario con todos los datos encontrados
            return {
                # indico que la consulta fue exitosa
                "ok": True,
                # incluyo el título de la película
                "titulo": datos.get("Title"),
                # incluyo el año de la película
                "anio": datos.get("Year"),
                # incluyo la duración en minutos
                "duracion_min": datos.get("Runtime"),
                # incluyo la lista de géneros separados por coma
                "generos": datos.get("Genre", "").split(", "),
                # incluyo el director de la película
                "director": datos.get("Director"),
                # incluyo la sinopsis de la película
                "sinopsis": datos.get("Plot"),
                # incluyo la puntuación de la crítica calculada antes
                "puntuacion_critica": critica,
                # incluyo la puntuación del público calculada antes
                "puntuacion_publico": publico,
            }

        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método que busca coincidencias en tmdb para que el usuario elija la película exacta
    def buscar_candidatos(self, titulo: str, limite: int = 6) -> dict:
        """
        autocompletado con póster: busca en tmdb por texto libre (sin año)
        y devuelve varias coincidencias para que el usuario elija la correcta
        antes de lanzar el análisis completo.
        """
        # intento realizar la búsqueda y manejar posibles errores
        try:
            # hago la petición de búsqueda de películas a tmdb en español
            resp = requests.get(
                # uso el endpoint de búsqueda de películas de tmdb
                "https://api.themoviedb.org/3/search/movie",
                # paso el texto de búsqueda el idioma y excluyo contenido para adultos
                params={"api_key": self.tmdb_key, "query": titulo, "language": "es-ES", "include_adult": "false"},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # extraigo la lista de resultados devuelta por tmdb
            resultados = resp.json().get("results", [])
            # construyo la lista de candidatos a partir de los primeros resultados
            candidatos = []
            # recorro los resultados hasta el límite indicado
            for r in resultados[:limite]:
                # extraigo el año a partir de la fecha de estreno si existe
                anio = (r.get("release_date") or "")[:4] or None
                # extraigo la ruta del póster si está disponible
                poster_path = r.get("poster_path")
                # añado el candidato con los datos mínimos para mostrar y para reconsultar por id
                candidatos.append({
                    # incluyo el id de tmdb para poder resolver el resto de datos sin ambigüedad
                    "tmdb_id": r.get("id"),
                    # incluyo el título en español devuelto por tmdb
                    "titulo": r.get("title"),
                    # incluyo el título original para referencia
                    "titulo_original": r.get("original_title"),
                    # incluyo el año extraído de la fecha de estreno
                    "anio": anio,
                    # construyo una miniatura del póster en tamaño pequeño para la lista de resultados
                    "poster_url": f"https://image.tmdb.org/t/p/w185{poster_path}" if poster_path else None,
                    # incluyo un fragmento corto de la sinopsis como ayuda visual
                    "sinopsis": (r.get("overview") or "")[:160],
                })
            # devuelvo la lista de candidatos aunque esté vacía
            return {"ok": True, "candidatos": candidatos}
        # capturo cualquier excepción de conexión ocurrida durante la búsqueda
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método que consulta el detalle de tmdb ya conociendo su id exacto
    def _consultar_tmdb_por_id(self, tmdb_id: int) -> dict:
        """
        mismo resultado que _consultar_tmdb pero sin volver a buscar por texto:
        se usa cuando el usuario ya eligió la película exacta de la lista de candidatos.
        """
        # intento realizar la consulta y manejar posibles errores
        try:
            # hago la petición de detalle de la película incluyendo créditos
            detalle = requests.get(
                # uso el endpoint de detalle de película con el id ya conocido
                f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                # paso la clave de api el idioma y pido los créditos adicionales
                params={"api_key": self.tmdb_key, "language": "es-ES", "append_to_response": "credits"},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # convierto la respuesta de detalle a un diccionario json
            datos = detalle.json()
            # compruebo si tmdb indica explícitamente que no encontró el id
            if datos.get("success") is False:
                # devuelvo el error indicado por tmdb o uno genérico
                return {"ok": False, "error": datos.get("status_message", "película no encontrada en tmdb")}

            # inicializo el compositor como vacío
            compositor = None
            # recorro el equipo técnico incluido en los créditos
            for persona in datos.get("credits", {}).get("crew", []):
                # compruebo si la persona tiene el cargo de compositor original
                if persona.get("job") == "Original Music Composer":
                    # guardo el nombre del compositor encontrado
                    compositor = persona.get("name")
                    # dejo de buscar una vez encontrado el compositor
                    break

            # extraigo la ruta del póster devuelta por tmdb
            poster_path = datos.get("poster_path")
            # construyo la url completa del póster si existe la ruta
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            # devuelvo un diccionario con los datos obtenidos de tmdb
            return {
                # indico que la consulta fue exitosa
                "ok": True,
                # incluyo la sinopsis en español
                "sinopsis": datos.get("overview"),
                # incluyo el compositor encontrado
                "compositor": compositor,
                # incluyo el título original de la película
                "titulo_original": datos.get("original_title"),
                # incluyo la url del póster construida antes
                "poster_url": poster_url,
            }
        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método que mapea un id de tmdb a su id de imdb equivalente
    def _obtener_imdb_id(self, tmdb_id: int) -> str | None:
        """traduce un id de tmdb a su id de imdb para poder consultar omdb sin depender del texto del título."""
        # intento realizar la consulta y manejar posibles errores
        try:
            # hago la petición al endpoint de identificadores externos de tmdb
            resp = requests.get(
                # uso el endpoint de identificadores externos con el id de tmdb ya conocido
                f"https://api.themoviedb.org/3/movie/{tmdb_id}/external_ids",
                # paso la clave de api necesaria
                params={"api_key": self.tmdb_key},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # devuelvo el id de imdb encontrado o none si no viene en la respuesta
            return resp.json().get("imdb_id") or None
        # capturo cualquier excepción ocurrida durante la consulta y la ignoro
        except Exception:
            # devuelvo none si la consulta falló por cualquier motivo
            return None

    # defino el método que consulta omdb directamente por id de imdb
    def _consultar_omdb_por_imdb_id(self, imdb_id: str) -> dict:
        """
        consulta omdb por id exacto de imdb — la vía más fiable posible,
        porque no depende de que el texto del título coincida.
        """
        # intento realizar la consulta y manejar posibles errores
        try:
            # hago la petición a omdb usando el identificador imdb como parámetro
            resp = requests.get(
                # uso el endpoint principal de omdb
                "http://www.omdbapi.com/",
                # paso la clave de api y el identificador imdb
                params={"apikey": self.omdb_key, "i": imdb_id},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # convierto la respuesta a un diccionario json
            datos = resp.json()
            # compruebo si la respuesta no fue exitosa
            if datos.get("Response") != "True":
                # devuelvo el error indicado por omdb o uno genérico
                return {"ok": False, "error": datos.get("Error", "sin datos del film")}

            # inicializo las puntuaciones de crítica y público como vacías
            critica = publico = None
            # recorro la lista de puntuaciones devueltas por omdb
            for r in datos.get("Ratings", []):
                # compruebo si la fuente es rotten tomatoes
                if r["Source"] == "Rotten Tomatoes":
                    # convierto el porcentaje de rotten tomatoes a una escala de diez
                    critica = float(r["Value"].replace("%", "")) / 10
                # compruebo si la fuente es imdb
                if r["Source"] == "Internet Movie Database":
                    # extraigo la puntuación de imdb como número
                    publico = float(r["Value"].split("/")[0])

            # devuelvo un diccionario con todos los datos encontrados
            return {
                # indico que la consulta fue exitosa
                "ok": True,
                # incluyo el título de la película
                "titulo": datos.get("Title"),
                # incluyo el año de la película
                "anio": datos.get("Year"),
                # incluyo la duración en minutos
                "duracion_min": datos.get("Runtime"),
                # incluyo la lista de géneros separados por coma
                "generos": datos.get("Genre", "").split(", "),
                # incluyo el director de la película
                "director": datos.get("Director"),
                # incluyo la sinopsis de la película
                "sinopsis": datos.get("Plot"),
                # incluyo la puntuación de la crítica calculada antes
                "puntuacion_critica": critica,
                # incluyo la puntuación del público calculada antes
                "puntuacion_publico": publico,
            }
        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método que resuelve todos los datos a partir de un id de tmdb ya elegido por el usuario
    def _resolver_por_tmdb_id(self, tmdb_id: int, titulo_fallback: str) -> tuple[dict, dict | None]:
        """
        cuando el usuario ya eligió la película exacta de la lista de candidatos,
        nos apoyamos en el id de tmdb en vez de en el llm adivinando el título en inglés.
        """
        # consulto el detalle de tmdb directamente por el id ya conocido
        tmdb_detalle = self._consultar_tmdb_por_id(tmdb_id)
        # extraigo el título original en inglés si la consulta fue exitosa
        titulo_en = tmdb_detalle.get("titulo_original") if tmdb_detalle.get("ok") else None
        # obtengo el id de imdb equivalente para consultar omdb de forma exacta
        imdb_id = self._obtener_imdb_id(tmdb_id)
        # compruebo si obtuve el id de imdb
        if imdb_id:
            # consulto omdb por el id de imdb que es la vía más fiable
            omdb = self._consultar_omdb_por_imdb_id(imdb_id)
        # si no hay id de imdb pero sí tengo el título original en inglés
        elif titulo_en:
            # consulto omdb por el título original en inglés obtenido de tmdb
            omdb = self._consultar_omdb(titulo_en, None)
        # como último recurso uso el título tal cual lo escribió el usuario
        else:
            # consulto omdb con el título de respaldo recibido
            omdb = self._consultar_omdb(titulo_fallback, None)
        # devuelvo tanto el resultado de omdb como el detalle de tmdb ya consultado
        return omdb, tmdb_detalle

    # defino el método que consulta tmdb para obtener sinopsis y compositor
    def _consultar_tmdb(self, titulo: str, anio: str = None) -> dict:
        """sinopsis en español y compositor desde tmdb."""
        # intento realizar la consulta y manejar posibles errores
        try:
            # construyo los parámetros de búsqueda con idioma español
            params = {"api_key": self.tmdb_key, "query": titulo, "language": "es-ES"}
            # añado el año a los parámetros si fue proporcionado
            if anio:
                # incluyo solo los primeros cuatro caracteres del año
                params["year"] = str(anio)[:4]
            # hago la petición de búsqueda de películas a tmdb
            busqueda = requests.get(
                # uso el endpoint de búsqueda de películas de tmdb
                "https://api.themoviedb.org/3/search/movie",
                # paso los parámetros construidos antes
                params=params,
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # extraigo la lista de resultados de la búsqueda
            resultados = busqueda.json().get("results", [])

            # compruebo si no hubo resultados en la búsqueda
            if not resultados:
                # devuelvo un error indicando que no se encontró la película
                return {"ok": False, "error": "película no encontrada en tmdb"}

            # extraigo el identificador tmdb del primer resultado
            tmdb_id = resultados[0]["id"]

            # hago una petición de detalle de la película incluyendo créditos
            detalle = requests.get(
                # uso el endpoint de detalle de película con su id
                f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                # paso la clave de api el idioma y pido los créditos adicionales
                params={"api_key": self.tmdb_key, "language": "es-ES", "append_to_response": "credits"},
                # limito el tiempo de espera de la petición
                timeout=5,
            )
            # convierto la respuesta de detalle a un diccionario json
            datos = detalle.json()

            # inicializo el compositor como vacío
            compositor = None
            # recorro el equipo técnico incluido en los créditos
            for persona in datos.get("credits", {}).get("crew", []):
                # compruebo si la persona tiene el cargo de compositor original
                if persona.get("job") == "Original Music Composer":
                    # guardo el nombre del compositor encontrado
                    compositor = persona.get("name")
                    # dejo de buscar una vez encontrado el compositor
                    break

            # extraigo la ruta del póster devuelta por tmdb
            poster_path = datos.get("poster_path")
            # construyo la url completa del póster si existe la ruta
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            # devuelvo un diccionario con los datos obtenidos de tmdb
            return {
                # indico que la consulta fue exitosa
                "ok": True,
                # incluyo la sinopsis en español
                "sinopsis": datos.get("overview"),
                # incluyo el compositor encontrado
                "compositor": compositor,
                # incluyo el título original de la película
                "titulo_original": datos.get("original_title"),
                # incluyo la url del póster construida antes
                "poster_url": poster_url,
            }

        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método que consulta las plataformas de streaming disponibles
    def _consultar_streaming(self, titulo: str, anio: str = None) -> dict:
        """plataformas de streaming disponibles en españa — api v4."""
        # intento realizar la consulta y manejar posibles errores
        try:
            # hago la petición a la api de streaming availability
            respuesta = requests.get(
                # uso el endpoint de búsqueda por título de la api
                "https://streaming-availability.p.rapidapi.com/shows/search/title",
                # paso las cabeceras requeridas con la clave y el host de rapidapi
                headers={
                    "X-RapidAPI-Key": self.streaming_key,
                    "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com",
                },
                # paso el título el país españa y el tipo de contenido película
                params={"title": titulo, "country": "es", "show_type": "movie"},
                # limito el tiempo de espera de la petición
                timeout=10,
            )
            # compruebo si el código de estado no es satisfactorio
            if respuesta.status_code != 200:
                # devuelvo un error indicando el código de estado recibido
                return {"ok": False, "error": f"status {respuesta.status_code}"}
            # convierto la respuesta a un diccionario o lista json
            datos = respuesta.json()
            # construyo la lista de shows devueltos si la respuesta es una lista
            shows = datos if isinstance(datos, list) else []

            # normalizo el título buscado para poder compararlo sin mayúsculas
            titulo_normalizado = titulo.strip().lower()
            # intento extraer el año como número para comparar con el de cada show
            try:
                # convierto el año recibido a entero usando solo los primeros cuatro dígitos
                anio_buscado = int(str(anio)[:4]) if anio else None
            # si el año no es un número válido lo trato como desconocido
            except (ValueError, TypeError):
                # marco el año buscado como ninguno
                anio_buscado = None

            # me quedo solo con los shows cuyo título coincide exactamente con el buscado
            shows_coincidentes = [s for s in shows if s.get("title", "").strip().lower() == titulo_normalizado]
            # si ninguno coincide exactamente evito mezclar resultados de títulos distintos
            if not shows_coincidentes:
                # devuelvo una lista vacía en vez de arriesgarme a mostrar otra película
                return {"ok": True, "plataformas": []}

            # si tengo el año busco entre los coincidentes el que además coincide en año
            show_elegido = shows_coincidentes[0]
            # compruebo si tengo un año de referencia para afinar la elección
            if anio_buscado:
                # recorro los shows con título coincidente buscando el mismo año
                for s in shows_coincidentes:
                    # comparo el año de estreno del show con el año buscado
                    if str(s.get("releaseYear", "")).strip() == str(anio_buscado):
                        # me quedo con este show como el correcto
                        show_elegido = s
                        # dejo de buscar porque ya encontré la coincidencia exacta
                        break

            # inicializo la lista de plataformas encontradas
            plataformas = []
            # extraigo las opciones de streaming disponibles en españa solo del show elegido
            opciones = show_elegido.get("streamingOptions", {}).get("es", [])
            # recorro cada opción de streaming encontrada
            for opcion in opciones:
                # extraigo el nombre del servicio de streaming
                servicio = opcion.get("service", {}).get("name", "")
                # extraigo el enlace directo a la película en ese servicio
                link = opcion.get("link", "")
                # compruebo que el servicio tenga un nombre válido
                if servicio:
                    # compruebo que el servicio no esté ya añadido a la lista
                    if not any(p["nombre"] == servicio for p in plataformas):
                        # añado la plataforma con su nombre y su enlace
                        plataformas.append({
                            # guardo el nombre del servicio
                            "nombre": servicio,
                            # guardo el enlace directo o la página principal del servicio
                            "url": link or opcion.get("service", {}).get("homePage", "")
                        })

            # devuelvo la lista de plataformas encontradas
            return {"ok": True, "plataformas": plataformas}

        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método que comprueba si la película tiene escenas post créditos
    def _consultar_post_creditos(self, titulo: str, anio: int = None) -> dict:
        """indica si la película tiene escenas post-créditos."""
        # intento realizar la consulta y manejar posibles errores
        try:
            # quito caracteres no alfanuméricos del título para formar la url
            titulo_limpio = "".join(c for c in titulo.lower() if c.isalnum() or c == " ").strip()
            # sustituyo los espacios por guiones para formar la url
            titulo_url = titulo_limpio.replace(" ", "-")
            # construyo la url de la página de la película en aftercredits
            url = f"https://aftercredits.com/movie/{titulo_url}/"
            # hago la petición a la página de aftercredits simulando un navegador
            respuesta = requests.get(
                # uso la url construida antes
                url,
                # limito el tiempo de espera de la petición
                timeout=5,
                # simulo un navegador para evitar bloqueos
                headers={"User-Agent": "Mozilla/5.0"},
            )

            # compruebo si la página no existe y si tengo el año disponible
            if respuesta.status_code == 404 and anio:
                # construyo una url alternativa incluyendo el año
                url_con_anio = f"https://aftercredits.com/movie/{titulo_url}-{anio}/"
                # repito la petición con la url alternativa
                respuesta = requests.get(
                    # uso la url alternativa construida con el año
                    url_con_anio,
                    # limito el tiempo de espera de la petición
                    timeout=5,
                    # simulo un navegador para evitar bloqueos
                    headers={"User-Agent": "Mozilla/5.0"},
                )

            # compruebo si la respuesta final no fue satisfactoria
            if respuesta.status_code != 200:
                # devuelvo un error indicando el código de estado recibido
                return {"ok": False, "error": f"status {respuesta.status_code}"}

            # parseo el html de la respuesta con beautifulsoup
            soup = BeautifulSoup(respuesta.text, "html.parser")
            # inicializo el valor de escena durante créditos como desconocido
            during_val = "desconocido"
            # inicializo el valor de escena después de créditos como desconocido
            after_val = "desconocido"

            # recorro todos los párrafos de la página
            for p in soup.find_all("p"):
                # extraigo el texto del párrafo actual
                text = p.get_text()
                # compruebo si el párrafo habla de escenas durante los créditos
                if "during credits?" in text.lower():
                    # busco la etiqueta en negrita que contiene la respuesta
                    strong = p.find("strong") or p.find("b")
                    # si la encuentro guardo su texto en minúsculas
                    if strong:
                        # guardo el valor encontrado para durante los créditos
                        during_val = strong.get_text().strip().lower()
                # compruebo si el párrafo habla de escenas después de los créditos
                if "after credits?" in text.lower():
                    # busco la etiqueta en negrita que contiene la respuesta
                    strong = p.find("strong") or p.find("b")
                    # si la encuentro guardo su texto en minúsculas
                    if strong:
                        # guardo el valor encontrado para después de los créditos
                        after_val = strong.get_text().strip().lower()

            # compruebo si alguno de los dos valores indica que sí hay escena
            if "yes" in during_val or "yes" in after_val:
                # devuelvo que sí tiene escenas post créditos
                return {"ok": True, "post_creditos": "sí"}
            # compruebo si ambos valores indican que no hay escena
            elif "no" in during_val and "no" in after_val:
                # devuelvo que no tiene escenas post créditos
                return {"ok": True, "post_creditos": "no"}
            # si no se pudo determinar con claridad
            else:
                # devuelvo que el dato es desconocido
                return {"ok": True, "post_creditos": "desconocido"}

        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino la lista ordenada de coincidencias que traduce los temas más habituales de doesthedogdie
    TRADUCCIONES_TAGS = [
        ("animal die",           "¿Muere algún animal?"),
        ("fourth wall",          "¿Rompe la cuarta pared?"),
        ("jump scare",           "¿Hay sustos repentinos?"),
    ]

    # defino el método que traduce una pregunta de doesthedogdie al español
    def _traducir_tag(self, does_name: str) -> str | None:
        """traduce un tema conocido de doesthedogdie o devuelve none si no lo reconozco."""
        # paso el texto a minúsculas para poder compararlo
        texto = does_name.lower()
        # recorro la lista de coincidencias en orden de prioridad
        for clave, traduccion in self.TRADUCCIONES_TAGS:
            # compruebo si la clave aparece dentro del texto original
            if clave in texto:
                # devuelvo la traducción encontrada
                return traduccion
        # devuelvo none si no reconozco el tema
        return None

    # defino el método que busca la película en doesthedogdie y devuelve su id
    def _buscar_id_doesthedogdie(self, titulo: str) -> int | None:
        """busca la película por título y devuelve el id del primer resultado."""
        # hago la petición de búsqueda al endpoint real de doesthedogdie
        respuesta = requests.get(
            # uso el endpoint de búsqueda por texto de doesthedogdie
            "https://www.doesthedogdie.com/dddsearch",
            # paso el título como parámetro de búsqueda
            params={"q": titulo},
            # paso las cabeceras con el tipo de contenido y la clave de api
            headers={"Accept": "application/json", "X-API-KEY": self.dogdie_key},
            # limito el tiempo de espera de la petición
            timeout=10,
        )
        # compruebo si el código de estado no es satisfactorio
        if respuesta.status_code != 200:
            # devuelvo none si la búsqueda falló
            return None
        # extraigo la lista de elementos encontrados
        items = respuesta.json().get("items", [])
        # devuelvo el id del primer elemento encontrado o none si no hay ninguno
        return items[0]["id"] if items else None

    # defino el método que recoge los tags curiosos de doesthedogdie
    def _consultar_tags_curiosos(self, titulo: str) -> dict:
        """comprueba si muere un perro y recoge otros tags curiosos de la película."""
        # intento realizar la consulta y manejar posibles errores
        try:
            # busco el id de la película en doesthedogdie
            item_id = self._buscar_id_doesthedogdie(titulo)
            # compruebo si no se encontró la película
            if not item_id:
                # devuelvo un error indicando que no se encontró la película
                return {"ok": False, "error": "película no encontrada en doesthedogdie"}

            # pido el detalle de la película con todos sus temas votados
            respuesta = requests.get(
                # uso el endpoint de detalle con el id encontrado
                f"https://www.doesthedogdie.com/media/{item_id}",
                # paso las cabeceras con el tipo de contenido y la clave de api
                headers={"Accept": "application/json", "X-API-KEY": self.dogdie_key},
                # limito el tiempo de espera de la petición
                timeout=10,
            )
            # compruebo si el código de estado no es satisfactorio
            if respuesta.status_code != 200:
                # devuelvo un error indicando el código de estado recibido
                return {"ok": False, "error": f"status {respuesta.status_code}"}

            # convierto la respuesta a un diccionario json
            datos = respuesta.json()

            # inicializo la alerta del perro como falsa
            alerta_indy = False
            # inicializo la lista de tags curiosos como vacía
            tags_curiosos = []

            # recorro los temas votados ordenados de más a menos votados
            temas = sorted(
                # uso la lista de temas devuelta por doesthedogdie
                datos.get("topicItemStats", []),
                # ordeno por la suma de votos a favor y en contra
                key=lambda t: (t.get("yesSum") or 0) + (t.get("noSum") or 0),
                # ordeno de mayor a menor número de votos
                reverse=True,
            )

            # recorro los temas ya ordenados por popularidad
            for topico in temas:
                # extraigo el nombre de la pregunta del tema
                does_name = topico.get("topic", {}).get("doesName", "")
                # extraigo el número de votos que dicen que sí
                votos_si = topico.get("yesSum", 0) or 0
                # extraigo el número de votos que dicen que no
                votos_no = topico.get("noSum", 0) or 0
                # salto este tema si no tiene votos suficientes para decidir
                if votos_si + votos_no == 0 or not does_name:
                    # paso al siguiente tema de la lista
                    continue
                # determino la respuesta mayoritaria del tema
                respuesta_topico = "sí" if votos_si > votos_no else "no"
                # compruebo si el tema trata sobre si muere el perro
                if "dog" in does_name.lower() and "die" in does_name.lower():
                    # marco la alerta indy según la respuesta mayoritaria
                    alerta_indy = respuesta_topico == "sí"
                # traduzco el tema al español si lo reconozco
                pregunta = self._traducir_tag(does_name)
                # salto este tema si no tengo una traducción reconocida
                if not pregunta:
                    # paso al siguiente tema de la lista
                    continue
                # evito añadir la misma pregunta traducida más de una vez
                if any(t["pregunta"] == pregunta for t in tags_curiosos):
                    # paso al siguiente tema de la lista
                    continue
                # añado el tema traducido a la lista de tags curiosos
                tags_curiosos.append({"pregunta": pregunta, "respuesta": respuesta_topico})
                # dejo de buscar cuando ya tengo suficientes tags curiosos
                if len(tags_curiosos) >= 6:
                    # interrumpo el recorrido de temas
                    break

            # devuelvo la alerta indy y los tags curiosos encontrados
            return {"ok": True, "alerta_indy": alerta_indy, "tags_curiosos": tags_curiosos}

        # capturo cualquier excepción de conexión ocurrida durante la consulta
        except Exception as e:
            # devuelvo un error indicando que falló la conexión
            return {"ok": False, "error": f"error de conexión — {str(e)}"}

    # defino el método genérico que busca un vídeo en youtube para una consulta dada
    def _buscar_video_youtube(self, query: str, category_id: str = None) -> dict:
        """busca el id del primer vídeo de youtube que coincide con la consulta."""
        # importo re para extraer ids de vídeo del html en el fallback
        import re

        # compruebo si tengo una clave de api de youtube disponible
        if self.youtube_key:
            # intento usar la api oficial de youtube
            try:
                # construyo los parámetros básicos de la búsqueda
                params = {
                    # incluyo la clave de api
                    "key": self.youtube_key,
                    # incluyo la consulta de búsqueda recibida
                    "q": query,
                    # pido solo la información básica del snippet
                    "part": "snippet",
                    # filtro los resultados para que sean solo vídeos
                    "type": "video",
                    # filtro para descartar vídeos que no se puedan incrustar en un iframe
                    "videoEmbeddable": "true",
                    # limito el número de resultados a uno solo
                    "maxResults": 1,
                }
                # añado el filtro de categoría si se proporcionó uno
                if category_id:
                    # incluyo la categoría en los parámetros de búsqueda
                    params["videoCategoryId"] = category_id
                # hago la petición de búsqueda a la api de youtube
                respuesta = requests.get(
                    # uso el endpoint de búsqueda de la api de youtube
                    "https://www.googleapis.com/youtube/v3/search",
                    # paso los parámetros construidos antes
                    params=params,
                    # limito el tiempo de espera de la petición
                    timeout=5,
                )
                # convierto la respuesta a un diccionario json
                datos = respuesta.json()
                # extraigo la lista de elementos devueltos
                items = datos.get("items", [])
                # compruebo si no se encontró ningún vídeo
                if not items:
                    # devuelvo un error indicando que no hay vídeo
                    return {"ok": False, "error": "no se encontró vídeo"}
                # devuelvo el identificador del primer vídeo encontrado
                return {"ok": True, "video_id": items[0]["id"]["videoId"]}
            # capturo cualquier excepción ocurrida al llamar a la api
            except Exception as e:
                # devuelvo un error indicando que falló la llamada a la api
                return {"ok": False, "error": f"error api — {str(e)}"}

        # fallback sin api key: scraping de la página de resultados
        # intento obtener el vídeo mediante scraping si no hay clave de api
        try:
            # construyo la url de la página de resultados de youtube
            url = "https://www.youtube.com/results"
            # hago la petición a la página de resultados simulando un navegador
            resp = requests.get(
                # uso la url construida antes
                url,
                # paso la consulta de búsqueda como parámetro
                params={"search_query": query},
                # simulo un navegador real para evitar bloqueos
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                # limito el tiempo de espera de la petición
                timeout=8,
            )
            # busco en el html todos los identificadores de vídeo presentes
            ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            # compruebo si se encontró al menos un identificador
            if ids:
                # devuelvo el primer identificador de vídeo encontrado
                return {"ok": True, "video_id": ids[0]}
            # devuelvo un error si no se encontró ningún identificador
            return {"ok": False, "error": "no se encontró vídeo"}
        # capturo cualquier excepción ocurrida durante el scraping
        except Exception as e:
            # devuelvo un error indicando que falló el scraping
            return {"ok": False, "error": f"error scraping — {str(e)}"}

    # defino el método que busca el vídeo de la banda sonora en youtube
    def _consultar_youtube(self, titulo: str, compositor: str = None) -> dict:
        """busca el id del video oficial de la banda sonora en youtube."""
        # construyo la consulta base con el título de la película
        query = f"{titulo} soundtrack official"
        # si hay compositor lo incluyo en la consulta para afinar la búsqueda
        if compositor:
            # reconstruyo la consulta incluyendo el nombre del compositor
            query = f"{compositor} {titulo} soundtrack"
        # delego la búsqueda en el método genérico filtrando por categoría de música
        return self._buscar_video_youtube(query, category_id="10")

    # defino el método que busca el tráiler oficial de la película en youtube
    def _consultar_trailer(self, titulo: str, anio: str = None) -> dict:
        """busca el id del tráiler oficial de la película en youtube."""
        # construyo la consulta incluyendo el año si está disponible para afinar la búsqueda
        query = f"{titulo} {anio} official trailer" if anio else f"{titulo} official trailer"
        # delego la búsqueda en el método genérico sin filtrar por categoría
        return self._buscar_video_youtube(query)

    # defino el método principal que combina todas las fuentes de datos
    def ejecutar(self, titulo: str, anio: int = None, tmdb_id: int = None) -> dict:
        """
        consolida los resultados de todas las fuentes.
        si se recibe tmdb_id (el usuario ya eligió la película en la lista de candidatos
        con póster) se resuelve todo por id exacto, sin depender de que el llm adivine
        el título en inglés ni de coincidencias de texto en omdb.
        """
        # inicializo el diccionario de resultado con valores por defecto
        resultado = {
            # inicializo el título como vacío
            "titulo": None,
            # inicializo el año como vacío
            "anio": None,
            # inicializo la duración como vacía
            "duracion_min": None,
            # inicializo la lista de géneros como vacía
            "generos": [],
            # inicializo el director como vacío
            "director": None,
            # inicializo el compositor como vacío
            "compositor": None,
            # inicializo la sinopsis como vacía
            "sinopsis": None,
            # inicializo la puntuación de la crítica como vacía
            "puntuacion_critica": None,
            # inicializo la puntuación del público como vacía
            "puntuacion_publico": None,
            # inicializo el dato de post créditos como desconocido
            "post_creditos": "desconocido",
            # inicializo la lista de plataformas de streaming como vacía
            "streaming_espana": [],
            # inicializo la alerta indy como falsa
            "alerta_indy": False,
            # inicializo la lista de tags curiosos como vacía
            "tags_curiosos": [],
            # inicializo el id de vídeo de youtube como vacío
            "youtube_video_id": None,
            # inicializo el indicador de vídeo lofi como falso
            "youtube_es_lofi": False,
            # inicializo el id del tráiler de youtube como vacío
            "youtube_trailer_id": None,
            # inicializo la url del póster como vacía
            "poster_url": None,
            # inicializo la lista de errores como vacía
            "errores": [],
        }

        # si el usuario ya eligió la película exacta de la lista de candidatos con póster
        # compruebo si recibí un id de tmdb para resolver todo sin ambigüedad
        if tmdb_id:
            # resuelvo omdb y el detalle de tmdb directamente por id, sin adivinar nada
            omdb, tmdb_extra = self._resolver_por_tmdb_id(tmdb_id, titulo)
        # si no hay id de tmdb caigo en el flujo clásico de adivinar el título
        else:
            # 1) traducir título al inglés vía llm
            # traduzco el título al inglés o uso el original si falla la traducción
            titulo_en = self._titulo_en_ingles(titulo) or titulo

            # 2) búsqueda exacta con el título traducido
            # consulto omdb usando el título traducido
            omdb = self._consultar_omdb(titulo_en, anio)

            # 3) búsqueda exacta con el título original si el traducido falló
            # si la búsqueda con el título traducido falló pruebo con el original
            if not omdb["ok"] and titulo_en.lower() != titulo.lower():
                # repito la consulta exacta usando el título original
                omdb = self._consultar_omdb(titulo, anio)

            # 4) búsqueda fuzzy (?s=) con ambos títulos como último recurso
            # si la búsqueda exacta sigue fallando pruebo la búsqueda fuzzy con el título traducido
            if not omdb["ok"]:
                # ejecuto la búsqueda fuzzy con el título traducido
                omdb = self._buscar_omdb(titulo_en)
            # si la fuzzy con el traducido falló y los títulos son distintos pruebo con el original
            if not omdb["ok"] and titulo_en.lower() != titulo.lower():
                # ejecuto la búsqueda fuzzy con el título original
                omdb = self._buscar_omdb(titulo)

            # sin id de tmdb todavía no tengo el detalle de tmdb consultado
            tmdb_extra = None

        # compruebo si todas las búsquedas en omdb fallaron
        if not omdb["ok"]:
            # añado el error de omdb a la lista de errores
            resultado["errores"].append(f"omdb: {omdb['error']}")
            # devuelvo el resultado vacío porque sin omdb no hay datos básicos
            return resultado

        # actualizo el resultado con los datos básicos obtenidos de omdb
        resultado.update({
            # guardo el título devuelto por omdb
            "titulo": omdb["titulo"],
            # guardo el año devuelto por omdb
            "anio": omdb["anio"],
            # guardo la duración devuelta por omdb
            "duracion_min": omdb["duracion_min"],
            # guardo los géneros devueltos por omdb
            "generos": omdb["generos"],
            # guardo el director devuelto por omdb
            "director": omdb["director"],
            # guardo la sinopsis devuelta por omdb
            "sinopsis": omdb["sinopsis"],
            # guardo la puntuación de crítica devuelta por omdb
            "puntuacion_critica": omdb["puntuacion_critica"],
            # guardo la puntuación de público devuelta por omdb
            "puntuacion_publico": omdb["puntuacion_publico"],
        })

        # reutilizo el detalle de tmdb ya consultado por id si lo tengo, para no repetir la llamada
        # compruebo si ya tengo un detalle de tmdb válido resuelto por id
        if tmdb_extra and tmdb_extra.get("ok"):
            # reutilizo directamente ese detalle sin volver a buscar por texto
            tmdb = tmdb_extra
        # si no lo tengo consulto tmdb buscando por el título ya confirmado por omdb
        else:
            # consulto tmdb para obtener la sinopsis en español y el compositor
            tmdb = self._consultar_tmdb(resultado["titulo"], resultado.get("anio"))
        # compruebo si la consulta a tmdb fue exitosa
        if tmdb["ok"]:
            # compruebo si tmdb devolvió una sinopsis válida
            if tmdb.get("sinopsis"):
                # sustituyo la sinopsis por la versión en español de tmdb
                resultado["sinopsis"] = tmdb["sinopsis"]
            # guardo el compositor devuelto por tmdb
            resultado["compositor"] = tmdb.get("compositor")
            resultado["poster_url"] = tmdb.get("poster_url")  # solo tmdb, sin CORS
        # si la consulta a tmdb falló
        else:
            # añado el error de tmdb a la lista de errores
            resultado["errores"].append(f"tmdb: {tmdb['error']}")

        # consulto las plataformas de streaming disponibles
        streaming = self._consultar_streaming(resultado["titulo"], resultado.get("anio"))
        # compruebo si la consulta de streaming fue exitosa
        if streaming["ok"]:
            # guardo la lista de plataformas encontradas
            resultado["streaming_espana"] = streaming["plataformas"]
        # si la consulta de streaming falló
        else:
            # añado el error de streaming a la lista de errores
            resultado["errores"].append(f"streaming: {streaming['error']}")

        # compruebo si la película todavía no se ha estrenado para evitar datos de otra película
        try:
            # extraigo el año como número entero a partir del texto devuelto por omdb
            anio_estreno = int(str(resultado.get("anio", ""))[:4])
        # si el año no es un número válido lo trato como desconocido
        except (ValueError, TypeError):
            # marco el año de estreno como ninguno
            anio_estreno = None
        # marco la película como no estrenada si su año es posterior al actual
        pelicula_no_estrenada = anio_estreno is not None and anio_estreno > datetime.now().year

        # consulto si la película tiene escenas post créditos solo si ya se ha estrenado
        if not pelicula_no_estrenada:
            # consulto si la película tiene escenas post créditos
            post = self._consultar_post_creditos(resultado["titulo"], resultado.get("anio"))
            # compruebo si la consulta de post créditos fue exitosa
            if post["ok"]:
                # guardo el dato de post créditos obtenido
                resultado["post_creditos"] = post["post_creditos"]
            # si la consulta de post créditos falló
            else:
                # añado el error de aftercredits a la lista de errores
                resultado["errores"].append(f"aftercredits: {post['error']}")

            # consulto los tags curiosos y si hay un perro con papel relevante
            perro = self._consultar_tags_curiosos(resultado["titulo"])
            # compruebo si la consulta de tags curiosos fue exitosa
            if perro["ok"]:
                # guardo el valor de alerta indy obtenido
                resultado["alerta_indy"] = perro["alerta_indy"]
                # guardo la lista de tags curiosos obtenida
                resultado["tags_curiosos"] = perro["tags_curiosos"]
            # si la consulta de tags curiosos falló
            else:
                # añado el error de doesthedogdie a la lista de errores
                resultado["errores"].append(f"doesthedogdie: {perro['error']}")
        # si la película todavía no se ha estrenado
        else:
            # dejo constancia de que se omitieron estas consultas por ser una película futura
            resultado["errores"].append("película sin estrenar: se omiten post-créditos y datos curiosos para evitar datos de otra película")

        # youtube — id del video de la banda sonora; si no hay, fallback lofi de cine
        # consulto el vídeo de la banda sonora en youtube
        yt = self._consultar_youtube(resultado["titulo"], resultado.get("compositor"))
        # compruebo si se encontró el vídeo de la banda sonora
        if yt["ok"]:
            # guardo el id del vídeo encontrado
            resultado["youtube_video_id"] = yt["video_id"]
            # marco que el vídeo no es un lofi de respaldo
            resultado["youtube_es_lofi"] = False
        # si no se encontró el vídeo de la banda sonora
        else:
            # añado el error de youtube a la lista de errores
            resultado["errores"].append(f"youtube: {yt['error']}")
            # determino el primer género disponible o uso uno genérico
            genero = resultado["generos"][0] if resultado.get("generos") else "film"
            # busco un vídeo lofi de respaldo relacionado con el género
            yt_lofi = self._consultar_youtube(f"lofi {genero} cinematic beats relaxing")
            # compruebo si se encontró el vídeo lofi de respaldo
            if yt_lofi["ok"]:
                # guardo el id del vídeo lofi encontrado
                resultado["youtube_video_id"] = yt_lofi["video_id"]
                # marco que el vídeo sí es un lofi de respaldo
                resultado["youtube_es_lofi"] = True

        # busco el tráiler oficial de la película de forma independiente a la banda sonora
        trailer = self._consultar_trailer(resultado["titulo"], resultado.get("anio"))
        # compruebo si se encontró el tráiler
        if trailer["ok"]:
            # guardo el id del tráiler encontrado
            resultado["youtube_trailer_id"] = trailer["video_id"]
        # si no se encontró el tráiler
        else:
            # añado el error del tráiler a la lista de errores
            resultado["errores"].append(f"youtube trailer: {trailer['error']}")

        # devuelvo el resultado consolidado con todos los datos obtenidos
        return resultado
