# veredicto.py — herramienta 2: el llm genera cada sección del informe por separado

# importo os para leer variables de entorno
import os
# importo json para parsear las respuestas json del modelo
import json
# importo abc y abstractmethod aunque no se usen directamente en esta clase
from abc import ABC, abstractmethod
# importo groq para usar el cliente del modelo de lenguaje
from groq import Groq
# importo el system prompt y los perfiles definidos para el agente
from agente.sistema import SYSTEM_PROMPT, PERFILES
# importo load_dotenv para cargar las variables de entorno desde el archivo .env
from dotenv import load_dotenv
# importo path para construir la ruta del archivo .env
from pathlib import Path

# cargo las variables de entorno desde el archivo .env situado dos carpetas arriba
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


# defino la clase veredicto que genera todas las secciones del informe
class Veredicto:
    """
    genera el informe completo de indy sección por sección.
    cada método privado hace una llamada al llm para su parte del informe.
    el método ejecutar los orquesta todos y devuelve el json final.
    """

    # defino el constructor que prepara el cliente y el modelo a usar
    def __init__(self):
        # instancio el cliente de groq con su clave de api
        self.cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # guardo el nombre del modelo que se usará en todas las llamadas
        self.modelo = "llama-3.1-8b-instant"

    # — método auxiliar: llamada al llm —

    # defino el método auxiliar que hace una llamada estándar al modelo
    def _llamar_llm(self, prompt: str, max_tokens: int = 300) -> str:
        """
        hace una llamada al llm con el system prompt de indy.
        devuelve el texto de respuesta limpio.
        """
        # pido al modelo una respuesta usando el system prompt y el prompt recibido
        respuesta = self.cliente.chat.completions.create(
            # uso el modelo configurado en el constructor
            model=self.modelo,
            # construyo los mensajes con el system prompt y el prompt de usuario
            messages=[
                # defino el rol de sistema con las instrucciones generales de indy
                {"role": "system", "content": SYSTEM_PROMPT},
                # defino el rol de usuario con el prompt específico de la sección
                {"role": "user", "content": prompt},
            ],
            # fijo la temperatura para dar algo de variedad creativa
            temperature=0.7,
            # limito el número máximo de tokens según el parámetro recibido
            max_tokens=max_tokens,
        )
        # devuelvo el texto de la respuesta sin espacios sobrantes
        return respuesta.choices[0].message.content.strip()

    # — sección 1: de qué va —

    # defino el método que genera la sinopsis sin spoilers
    def _generar_de_que_va(self, datos: dict) -> str:
        """sinopsis sin spoilers en tono colega de bar."""
        # construyo el prompt con los datos de la película y las instrucciones de estilo
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
        # llamo al modelo con el prompt construido y un límite de tokens reducido
        return self._llamar_llm(prompt, max_tokens=200)

    # — sección 2: crítica vs público —

    # defino el método que compara las puntuaciones de crítica y público
    def _generar_critica_vs_publico(self, datos: dict) -> dict:
        """analiza la divergencia entre crítica y público."""
        # extraigo la puntuación de la crítica de los datos
        critica = datos.get("puntuacion_critica")
        # extraigo la puntuación del público de los datos
        publico = datos.get("puntuacion_publico")

        # compruebo si no hay ninguna de las dos puntuaciones disponibles
        if critica is None and publico is None:
            # devuelvo una estructura indicando que no hay datos
            return {
                # marco la puntuación de crítica como vacía
                "puntuacion_critica": None,
                # marco la puntuación de público como vacía
                "puntuacion_publico": None,
                # marco la diferencia como vacía
                "diferencia": None,
                # indico que no hay datos para decidir quién gana
                "quien_gana": "sin datos",
                # incluyo un comentario explicando la ausencia de datos
                "comentario": "No he encontrado puntuaciones para esta película.",
            }

        # calculo la diferencia entre público y crítica redondeada a un decimal
        diferencia = round((publico or 0) - (critica or 0), 1)
        # compruebo si la diferencia favorece claramente al público
        if diferencia > 0.5:
            # marco que gana el público
            quien_gana = "publico"
        # compruebo si la diferencia favorece claramente a la crítica
        elif diferencia < -0.5:
            # marco que gana la crítica
            quien_gana = "critica"
        # si la diferencia es pequeña considero que hay empate
        else:
            # marco que hay empate entre crítica y público
            quien_gana = "empate"

        # construyo el prompt con las puntuaciones y la diferencia calculada
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
        # llamo al modelo para obtener el comentario mordaz
        comentario = self._llamar_llm(prompt, max_tokens=150)

        # devuelvo la estructura completa con puntuaciones diferencia y comentario
        return {
            # incluyo la puntuación de la crítica
            "puntuacion_critica": critica,
            # incluyo la puntuación del público
            "puntuacion_publico": publico,
            # incluyo la diferencia calculada
            "diferencia": diferencia,
            # incluyo quién gana según la diferencia
            "quien_gana": quien_gana,
            # incluyo el comentario generado por el modelo
            "comentario": comentario,
        }

    # — sección 3: índice de giros —

    # defino el método que asigna una etiqueta de giros de guion
    def _generar_indice_giros(self, datos: dict) -> str:
        """asigna una de las 4 etiquetas de giros de guion."""
        # construyo el prompt con los datos de la película y las cuatro opciones posibles
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
        # llamo al modelo con un límite de tokens muy pequeño porque solo espero una etiqueta
        respuesta = self._llamar_llm(prompt, max_tokens=20).strip()

        # validación: si no devuelve una etiqueta válida busco coincidencia parcial
        # defino la lista de etiquetas válidas que puede devolver el modelo
        etiquetas_validas = ["🎯 Predecible", "🤔 Alguna sorpresa", "😮 Bastantes giros", "🤯 No te fíes de nadie"]
        # recorro las etiquetas válidas buscando si alguna aparece en la respuesta
        for etiqueta in etiquetas_validas:
            # compruebo si la etiqueta actual está contenida en la respuesta
            if etiqueta in respuesta:
                # devuelvo la etiqueta encontrada
                return etiqueta

        # fallback si el llm devuelve solo el emoji
        # compruebo si la respuesta contiene solo el emoji de predecible
        if "🎯" in respuesta:
            # devuelvo la etiqueta completa de predecible
            return "🎯 Predecible"
        # compruebo si la respuesta contiene solo el emoji de alguna sorpresa
        elif "🤔" in respuesta:
            # devuelvo la etiqueta completa de alguna sorpresa
            return "🤔 Alguna sorpresa"
        # compruebo si la respuesta contiene solo el emoji de bastantes giros
        elif "😮" in respuesta:
            # devuelvo la etiqueta completa de bastantes giros
            return "😮 Bastantes giros"
        # compruebo si la respuesta contiene solo el emoji de no te fíes de nadie
        elif "🤯" in respuesta:
            # devuelvo la etiqueta completa de no te fíes de nadie
            return "🤯 No te fíes de nadie"

        # devuelvo una etiqueta por defecto si no se pudo determinar ninguna
        return "🤔 Alguna sorpresa"

    # — sección 4: post-créditos —

    # defino el método que determina si hay escenas post créditos
    def _generar_post_creditos(self, datos: dict) -> str:
        """
        devuelve el indicador de post-créditos.
        si aftercredits no lo sabe, el llm intenta inferirlo.
        """
        # compruebo si el dato ya viene confirmado desde el buscador
        if datos.get("post_creditos") in ["sí", "no"]:
            # devuelvo directamente el dato ya confirmado
            return datos["post_creditos"]

        # fallback: el llm intenta inferirlo
        # construyo el prompt para que el modelo infiera la respuesta
        prompt = f"""
        La película es "{datos['titulo']}" ({datos['anio']}).
        Géneros: {', '.join(datos['generos'])}
        Director: {datos.get('director', 'desconocido')}

        ¿Tiene escenas durante o después de los créditos finales?
        Recuerda que la inmensa mayoría de las películas dramáticas, antiguas (anteriores a los 2000) o clásicas NO tienen post-créditos. Las películas modernas de superhéroes, Marvel, DC o ciertas comedias/sagas de acción SÍ suelen tener.

        Responde estrictamente con una sola palabra: sí o no o desconocido.
        Sin puntos, sin explicaciones ni rodeos.
        """
        # llamo al modelo con un límite de tokens muy pequeño y paso la respuesta a minúsculas
        respuesta = self._llamar_llm(prompt, max_tokens=10).lower()
        # compruebo si la respuesta indica afirmativamente con o sin tilde
        if "sí" in respuesta or "si" in respuesta:
            # devuelvo que sí tiene escenas post créditos
            return "sí"
        # compruebo si la respuesta indica negativamente
        elif "no" in respuesta:
            # devuelvo que no tiene escenas post créditos
            return "no"
        # si la respuesta no es clara
        else:
            # devuelvo que el dato es desconocido
            return "desconocido"

    # — sección 5: banda sonora —

    # defino el método que obtiene los datos de la banda sonora
    def _generar_banda_sonora(self, datos: dict) -> dict:
        """compositor, álbum y búsqueda en youtube."""
        # extraigo el compositor de los datos si está disponible
        compositor = datos.get("compositor") or None

        # construyo el prompt indicando si el compositor es conocido o debe inferirse
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
        # intento llamar al modelo y parsear la respuesta como json
        try:
            # llamo al modelo con un límite de tokens moderado
            raw = self._llamar_llm(prompt, max_tokens=150)
            # convierto el texto devuelto en un diccionario python
            return json.loads(raw)
        # si la llamada o el parseo fallan uso un valor de respaldo
        except Exception:
            # construyo un texto de búsqueda válido para una url reemplazando espacios
            titulo_busqueda = datos['titulo'].replace(" ", "+")
            # devuelvo una estructura de respaldo con los datos disponibles
            return {
                # uso el compositor ya conocido si lo había
                "compositor": compositor,
                # marco el álbum como no disponible
                "album": "no disponible",
                # construyo una url de búsqueda directa en youtube como respaldo
                "url_youtube": f"https://www.youtube.com/results?search_query={titulo_busqueda}+soundtrack",
            }

    # — sección 6: snack —

    # defino el método que recomienda un snack a juego con la película
    def _generar_snack(self, datos: dict) -> dict:
        """el llm elige el snack perfecto (comida + bebida) para esta película.
        el modelo tiende a repetir siempre la misma respuesta (empanadas argentinas)
        sea cual sea la ambientación, así que valido el resultado por código y
        reintento con un aviso explícito si detecto que ha vuelto a repetirla."""
        # construyo el prompt base, dejando hueco para un aviso extra en reintentos
        def construir_prompt(aviso_extra: str = "") -> str:
            return f"""
        La película es "{datos['titulo']}" ({datos['anio']}).
        Géneros: {', '.join(datos['generos'])}
        Director: {datos.get('director', 'desconocido')}
        Sinopsis: {datos.get('sinopsis', 'no disponible')}

        Antes de elegir nada, identifica mentalmente el país, región o zona geográfica concreta donde transcurre principalmente la trama de la película (no el país donde se rodó ni el país de origen del estudio, sino donde está ambientada la historia).

        Recomienda el maridaje de snacks perfecto para ver esta película, incluyendo:
        1. Una COMIDA tipo snack de cine.
        2. Una BEBIDA.

        Sigue este orden de prioridad para decidir qué proponer:
        1º. Si la sinopsis menciona literalmente alguna comida o bebida concreta, úsala o usa una variante directa de ella.
        2º. Si no, usa un plato o bebida típica del país, región o zona geográfica donde está ambientada la trama (el lugar que identificaste antes, no un país al azar).
        3º. Solo si la trama no tiene una ambientación geográfica real identificable (ciencia ficción, fantasía, animación abstracta), inspírate en el tono o el género en vez del lugar.
        {aviso_extra}
        IMPORTANTE: la comida y la bebida deben ser productos REALES y reconocibles que existan de verdad (un plato, un dulce, un snack envasado, una bebida concreta), NUNCA un nombre poético o inventado sin sentido literal. La conexión imaginativa con la película va en la justificación, no en el nombre del producto.

        El nombre de la comida y de la bebida deben ser CORTOS: máximo 2-3 palabras cada uno. Si quieres desarrollar la idea con más detalle, hazlo en la justificación, no en el nombre.

        Devuelve SOLO un JSON con esta estructura exacta, sin texto adicional ni bloques de código markdown:
        {{
          "ambientacion": "país, región o zona geográfica donde transcurre la trama",
          "comida": "nombre corto de la comida, 2-3 palabras, coherente con la ambientación",
          "bebida": "nombre corto de la bebida, 2-3 palabras, coherente con la ambientación",
          "justificacion": "Una o dos frases ingeniosas explicando la conexión del combo con la película, pudiendo desarrollar aquí el detalle que no cabía en el nombre"
        }}
        """

        # palabras clave que indican que la ambientación sí es realmente argentina o rioplatense
        claves_argentina = ("argentin", "buenos aires", "rioplatense", "patagonia")

        # función interna que llama al modelo y devuelve el dict ya parseado o None si falla
        def llamar(aviso_extra: str = "") -> dict | None:
            try:
                # llamo al modelo con un límite de tokens algo más amplio para evitar truncados
                raw = self._llamar_llm(construir_prompt(aviso_extra), max_tokens=220)
                # quito posibles bloques de código markdown antes de parsear
                raw = raw.strip()
                # compruebo si la respuesta empieza con un bloque de código
                if raw.startswith("```"):
                    # quito la primera línea con la marca de apertura del bloque
                    raw = raw.split("\n", 1)[1]
                # compruebo si la respuesta termina con un bloque de código
                if raw.endswith("```"):
                    # quito la última línea con la marca de cierre del bloque
                    raw = raw.rsplit("\n", 1)[0]
                # convierto el texto limpio en un diccionario python
                return json.loads(raw.strip())
            # si la llamada o el parseo fallan devuelvo None para que el caller decida
            except Exception:
                return None

        # primer intento sin avisos adicionales
        resultado = llamar()

        # compruebo si el resultado usa empanadas argentinas sin que la ambientación sea argentina de verdad
        if resultado:
            ambientacion = str(resultado.get("ambientacion", "")).lower()
            comida = str(resultado.get("comida", "")).lower()
            es_argentina = any(clave in ambientacion for clave in claves_argentina)
            if "empanada" in comida and not es_argentina:
                # reintento una vez señalando explícitamente el error cometido
                aviso = f'\n        Tu respuesta anterior fue "{resultado.get("comida")}", pero la ambientación real de esta película NO es Argentina. PROHIBIDO terminantemente usar la palabra "empanada" en este caso. Elige otra comida típica de la ambientación real que identificaste.\n'
                resultado = llamar(aviso) or resultado

        # si tengo un resultado válido lo devuelvo
        if resultado:
            return resultado

        # si la llamada o el parseo fallaron en ambos intentos uso un valor de respaldo
        return {
            # propongo palomitas clásicas como comida de respaldo
            "comida": "Palomitas de maíz clásicas con mantequilla",
            # propongo un refresco de cola como bebida de respaldo
            "bebida": "Refresco de cola bien frío",
            # incluyo una justificación genérica para el combo de respaldo
            "justificacion": "El combo de toda la vida para disfrutar del mejor cine sin complicaciones."
        }

    # — sección 8: alternativas —

    # defino el método que sugiere alternativas si el veredicto es negativo
    def _generar_alternativas(self, datos: dict, veredicto_negativo: bool) -> list | None:
        """
        solo se genera si el veredicto es negativo.
        devuelve 2-3 películas alternativas mejores.
        """
        # compruebo si el veredicto no fue negativo
        if not veredicto_negativo:
            # devuelvo none porque no hacen falta alternativas
            return None

        # construyo el prompt pidiendo alternativas relacionadas por género o temática
        prompt = f"""
La película "{datos['titulo']}" ({datos['anio']}) no merece la pena.
Géneros: {', '.join(datos['generos'])}
Director: {datos.get('director')}

Sugiere 2-3 películas alternativas mejores, relacionadas por género o temática.
Devuelve SOLO un JSON con esta estructura exacta:
["Título película 1", "Título película 2", "Título película 3"]
Sin texto adicional, solo el JSON.
"""
        # intento llamar al modelo y parsear la respuesta como una lista json
        try:
            # llamo al modelo con un límite de tokens reducido
            raw = self._llamar_llm(prompt, max_tokens=100)
            # convierto el texto devuelto en una lista python
            return json.loads(raw)
        # si la llamada o el parseo fallan devuelvo none
        except Exception:
            # devuelvo none si no se pudieron obtener alternativas válidas
            return None

    # defino el método auxiliar para llamadas al modelo con texto libre
    def _llamar_llm_libre(self, prompt: str, max_tokens: int = 350) -> str:
        """llamada al llm sin el system prompt JSON — para texto libre."""
        # pido al modelo una respuesta usando un system prompt distinto orientado a texto libre
        respuesta = self.cliente.chat.completions.create(
            # uso el modelo configurado en el constructor
            model=self.modelo,
            # construyo los mensajes con el system prompt libre y el prompt de usuario
            messages=[
                # defino el rol de sistema con una descripción breve de la personalidad de indy
                {"role": "system", "content": "Eres Indy, un crítico de cine con criterio propio, directo y con personalidad. Responde siempre en español."},
                # defino el rol de usuario con el prompt específico
                {"role": "user", "content": prompt},
            ],
            # fijo una temperatura algo más alta para dar más naturalidad al texto libre
            temperature=0.8,
            # limito el número máximo de tokens según el parámetro recibido
            max_tokens=max_tokens,
        )
        # devuelvo el texto de la respuesta sin espacios sobrantes
        return respuesta.choices[0].message.content.strip()

    # — sección 9: veredicto final —

    # defino el método que genera el veredicto final de la película
    def _generar_veredicto_final(self, datos: dict, perfil: str) -> dict:
        """
        el veredicto es texto libre — indy decide cómo contarlo.
        también decide si es positivo o negativo para el flujo de alternativas.
        """
        # obtengo la descripción del perfil del usuario o uso una genérica
        descripcion_perfil = PERFILES.get(perfil, "espectador general")

        # calculo una nota media orientativa a partir de las puntuaciones disponibles
        critica = datos.get("puntuacion_critica")
        publico = datos.get("puntuacion_publico")
        notas = [n for n in (critica, publico) if n is not None]
        media = round(sum(notas) / len(notas), 1) if notas else None

        # clasifico la calidad orientativa según la media para anclar el criterio del modelo
        if media is None:
            calidad = "sin datos suficientes — usa tu propio criterio sobre la película"
        elif media >= 7.5:
            calidad = "buena/notable"
        elif media >= 6:
            calidad = "correcta pero con peros"
        elif media >= 4.5:
            calidad = "mediocre — floja de verdad"
        else:
            calidad = "mala — no se sostiene"

        # construyo el prompt con todos los datos de la película y el perfil del usuario
        prompt = f"""
Película: "{datos['titulo']}" ({datos['anio']})
Géneros: {', '.join(datos['generos'])}
Director: {datos.get('director', 'desconocido')}
Puntuación crítica: {critica}/10
Puntuación público: {publico}/10
Nota media orientativa: {media}/10 → calidad {calidad}
Perfil del espectador: {descripcion_perfil}

CRITERIO DE DECISIÓN (esto manda por encima del tono simpático):
- La recomendación tiene que reflejar si la película es objetivamente buena o mala, no solo si "encaja" con el perfil por género.
- Si la nota media es baja (mediocre o mala), tu recomendación por defecto debe ser NO, salvo que sea una película de culto que ese perfil concreto disfrutaría pese a sus defectos evidentes (y en ese caso dilo explícitamente).
- No tengas miedo de decir NO. Eres un crítico honesto, no un vendedor de entradas. Que la película exista y tenga género no la hace recomendable.

Responde EXACTAMENTE en uno de estos dos formatos, sin nada más:

RECOMENDACIÓN: SÍ
RAZÓN: [frase de 8-12 palabras que explique POR QUÉ es recomendable para este perfil concreto. Ejemplo: "Un thriller de ritmo trepidante perfecto para el que busca adrenalina"]
PÁRRAFO: [3-4 frases con tu opinión como Indy. Con criterio y personalidad. Sin repetir la razón. Sin mencionar las puntuaciones con números. Adaptado al perfil del espectador.]

O bien:

RECOMENDACIÓN: NO
RAZÓN: [frase de 8-12 palabras explicando por qué NO merece la pena para este perfil. Ejemplo: "Efectos anticuados y guion perezoso que ni la nostalgia salva"]
PÁRRAFO: [3-4 frases honestas y directas sobre por qué falla la película. Sin piedad pero con clase. Nada de suavizarlo al final con un "aun así, dale una oportunidad".]

IMPORTANTE: el "perfil del espectador" describe los gustos de la persona que va a leer esto, NO es un personaje ni un elemento de la película. Nunca escribas el nombre del perfil (por ejemplo "El Fantástico", "El Palomitero") dentro de la razón ni del párrafo, ni hables de él en tercera persona como si apareciera en la trama. Úsalo solo para decidir el tono y el enfoque del texto.
"""
        # llamo al modelo libre para obtener el texto completo del veredicto
        raw = self._llamar_llm_libre(prompt, max_tokens=350)

        # importo re para extraer las partes del texto devuelto por el modelo
        import re

        # inicializo la recomendación con un valor por defecto que respeta la nota media
        # si el modelo no devuelve un formato parseable, mejor fiarse de los datos que asumir un "sí" a ciegas
        recomendacion = "NO" if (media is not None and media < 4.5) else "SÍ"
        # inicializo la razón como vacía
        razon = ""
        # inicializo el párrafo con todo el texto bruto por si no se puede parsear
        parrafo = raw.strip()

        # busco la línea que contiene la recomendación
        m = re.search(r'RECOMENDACI[OÓ]N\s*:\s*(.+)', raw, re.IGNORECASE)
        # compruebo si se encontró la línea de recomendación
        if m:
            # extraigo el valor encontrado y lo paso a mayúsculas
            val = m.group(1).strip().upper()
            # determino si la recomendación es positiva según las palabras encontradas
            recomendacion = "SÍ" if any(x in val for x in ("SÍ", "SI", "YES")) else "NO"

        # busco la línea que contiene la razón
        # tolero erratas del modelo en la etiqueta del párrafo, por ejemplo PÁRRAFA en vez de PÁRRAFO
        etiqueta_parrafo = r'P[AÁ]RR?AF[OA]?'

        # paro antes de la etiqueta del párrafo para no arrastrarla dentro de la razón
        # si el modelo responde todo en una sola línea sin saltos
        m = re.search(r'RAZ[OÓ]N\s*:\s*(.+?)(?=\s*' + etiqueta_parrafo + r'\s*:|$)', raw, re.IGNORECASE | re.DOTALL)
        # compruebo si se encontró la línea de razón
        if m:
            # extraigo el texto de la razón encontrada
            razon = m.group(1).strip()

        # busco el bloque de texto del párrafo que puede ocupar varias líneas, tolerando erratas en la etiqueta
        m = re.search(etiqueta_parrafo + r'\s*:\s*(.+)', raw, re.IGNORECASE | re.DOTALL)
        # compruebo si se encontró el bloque del párrafo
        if m:
            # extraigo el texto completo del párrafo encontrado
            parrafo = m.group(1).strip()

        # determino si el veredicto es negativo según la recomendación extraída
        es_negativo = recomendacion == "NO"
        # devuelvo una estructura con todos los datos del veredicto
        return {
            # incluyo la recomendación extraída
            "recomendacion": recomendacion,
            # incluyo la razón extraída
            "razon": razon,
            # incluyo el párrafo extraído
            "parrafo": parrafo,
            # incluyo si el veredicto es negativo
            "es_negativo": es_negativo,
            # incluyo el texto del párrafo como alias adicional
            "texto": parrafo,
        }

    # — método principal —

    # defino el método principal que orquesta todas las secciones del informe
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
        # intento generar todas las secciones y capturar cualquier error
        try:
            # genero primero el veredicto final porque determina si hay alternativas
            veredicto = self._generar_veredicto_final(datos_pelicula, perfil_usuario)

            # construyo el informe completo combinando todas las secciones generadas
            informe = {
                # construyo el título junto con el año entre paréntesis
                "titulo_anio": f"{datos_pelicula.get('titulo')} ({datos_pelicula.get('anio')})",
                # genero la sinopsis sin spoilers
                "de_que_va": self._generar_de_que_va(datos_pelicula),
                # genero la comparación entre crítica y público
                "critica_vs_publico": self._generar_critica_vs_publico(datos_pelicula),
                # genero la etiqueta del índice de giros
                "indice_giros": self._generar_indice_giros(datos_pelicula),
                # genero el dato de post créditos
                "post_creditos": self._generar_post_creditos(datos_pelicula),
                # incluyo las plataformas de streaming obtenidas por el buscador
                "streaming_espana": datos_pelicula.get("streaming_espana", []),
                # incluyo los tags curiosos obtenidos por el buscador
                "tags_curiosos": datos_pelicula.get("tags_curiosos", []),
                # genero los datos de la banda sonora
                "banda_sonora": self._generar_banda_sonora(datos_pelicula),
                # genero la recomendación de snack
                "snack": self._generar_snack(datos_pelicula),
                # incluyo si hay un perro con papel relevante obtenido por el buscador
                "alerta_indy": datos_pelicula.get("alerta_indy", False),
                # genero las alternativas si el veredicto fue negativo
                "alternativas": self._generar_alternativas(datos_pelicula, veredicto["es_negativo"]),
                # incluyo el párrafo del veredicto
                "veredicto": veredicto["parrafo"],
                # incluyo la recomendación del veredicto
                "veredicto_recomendacion": veredicto["recomendacion"],
                # incluyo la razón del veredicto
                "veredicto_razon": veredicto["razon"],
            }

            # devuelvo el informe completo indicando que todo salió bien
            return {"ok": True, "informe": informe}

        # capturo cualquier excepción ocurrida durante la generación del informe
        except Exception as e:
            # devuelvo un error indicando en qué falló la generación
            return {"ok": False, "error": f"error generando el informe — {str(e)}"}
