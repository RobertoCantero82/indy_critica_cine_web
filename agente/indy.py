# indy.py — orquestador principal del agente indy (loop react)

# importo la herramienta que busca los datos de la película
from agente.herramientas.buscador import Buscador
# importo la herramienta que genera el veredicto crítico
from agente.herramientas.veredicto import Veredicto
# importo la herramienta que guarda y consulta el informe
from agente.herramientas.informe import Informe
# importo los mensajes de carga que se muestran durante el proceso
from agente.sistema import MENSAJES_CARGA


# defino la clase principal que orquesta todo el agente
class IndyAgent:
    """
    orquestador principal del agente indy.
    implementa el loop react: percibir → razonar → actuar → observar.
    gestiona el estado de la sesión y el flujo completo de análisis.
    """

    # fijo el número máximo de iteraciones del loop para evitar bucles infinitos
    MAX_ITERACIONES = 10

    # defino el constructor de la clase
    def __init__(self):
        # buscador de datos de películas
        self.buscador = Buscador()
        # generador de veredicto
        self.veredicto = Veredicto()
        # gestor de informes
        self.informe = Informe()

        # estado de la sesión actual
        # guardo el título de la película consultada
        self.titulo = None
        # guardo el año de la película consultada
        self.anio = None
        # guardo el id de tmdb si el usuario eligió la película de la lista de candidatos
        self.tmdb_id = None
        # guardo el perfil del usuario que hace la consulta
        self.perfil_usuario = None
        # guardo el nombre del usuario que hace la consulta
        self.nombre_usuario = None
        # guardo los datos de la película una vez encontrados
        self.datos_pelicula = None
        # guardo el informe completo una vez generado
        self.informe_completo = None
        # guardo el número de iteraciones realizadas en el loop
        self.iteraciones = 0
        # guardo la lista de errores ocurridos durante la ejecución
        self.errores = []
        self.log = []  # registro de pasos del loop para la ui

    # — gestión del estado —

    # defino el método que reinicia el estado antes de cada consulta
    def _resetear_sesion(self):
        """limpia el estado antes de una nueva consulta."""
        # vacío el título guardado
        self.titulo = None
        # vacío el año guardado
        self.anio = None
        # vacío el id de tmdb guardado
        self.tmdb_id = None
        # vacío el perfil del usuario guardado
        self.perfil_usuario = None
        # vacío el nombre del usuario guardado
        self.nombre_usuario = None
        # vacío los datos de película guardados
        self.datos_pelicula = None
        # vacío el informe completo guardado
        self.informe_completo = None
        # reinicio el contador de iteraciones a cero
        self.iteraciones = 0
        # vacío la lista de errores
        self.errores = []
        # vacío el registro de pasos
        self.log = []

    # defino el método que añade un paso al registro de la sesión
    def _registrar_paso(self, mensaje: str):
        """añade un mensaje al log y lo devuelve para la ui."""
        # añado el mensaje a la lista de pasos
        self.log.append(mensaje)
        # devuelvo el mensaje añadido
        return mensaje

    # defino el método que controla el límite de iteraciones del loop
    def _incrementar_iteracion(self) -> bool:
        """
        incrementa el contador de iteraciones.
        devuelve false si se supera el límite máximo.
        """
        # sumo uno al contador de iteraciones
        self.iteraciones += 1
        # compruebo si se ha superado el límite permitido
        if self.iteraciones > self.MAX_ITERACIONES:
            # devuelvo falso si se ha superado el límite
            return False
        # devuelvo verdadero si todavía no se ha superado el límite
        return True

    # — fase 1: percibir —

    # defino el método que comprueba si la película ya tiene informe guardado
    def comprobar_cache(self, titulo: str) -> dict | None:
        """
        comprueba si la película ya tiene un informe guardado.
        devuelve el informe y la fecha o none si no existe.
        se llama desde la UI antes de ejecutar el agente.
        """
        # delego la búsqueda en caché a la herramienta de informe
        return self.informe.buscar_en_cache(titulo.strip())

    # defino el método que recibe el input del usuario y arranca la sesión
    def percibir(
        self,
        titulo: str,
        perfil_usuario: str,
        anio: int = None,
        nombre_usuario: str = None,
        tmdb_id: int = None,
    ) -> dict:
        """
        recibe el input del usuario y prepara el estado inicial.
        comprueba la caché antes de arrancar el loop.
        """
        # reinicio el estado de la sesión antes de empezar
        self._resetear_sesion()

        # guardo el título recibido quitando espacios sobrantes
        self.titulo = titulo.strip()
        # guardo el año recibido
        self.anio = anio
        # guardo el id de tmdb recibido si el usuario eligió la película de la lista de candidatos
        self.tmdb_id = tmdb_id
        # guardo el perfil del usuario recibido
        self.perfil_usuario = perfil_usuario
        # guardo el nombre del usuario recibido
        self.nombre_usuario = nombre_usuario

        # registro el mensaje de inicio en el log
        self._registrar_paso(MENSAJES_CARGA["inicio"])

        # compruebo si la película ya está en caché
        # busco si ya existe un informe guardado para este título
        cache = self.informe.buscar_en_cache(self.titulo)
        # si encuentro caché devuelvo directamente el informe guardado
        if cache:
            # devuelvo un diccionario indicando que hay caché disponible
            return {
                # indico que la percepción se completó correctamente
                "ok": True,
                # indico que existe caché para esta película
                "cache": True,
                # incluyo el informe encontrado en caché
                "informe": cache["informe"],
                # incluyo la fecha en la que se guardó el informe
                "fecha_consulta": cache["fecha_consulta"],
                # incluyo el log acumulado hasta el momento
                "log": self.log,
            }

        # si no hay caché devuelvo que se debe continuar con el loop
        return {"ok": True, "cache": False, "log": self.log}

    # — fase 2: razonar —

    # defino el método que decide la siguiente acción del loop
    def razonar(self) -> dict:
        """
        evalúa el estado actual y decide qué herramienta invocar a continuación.
        es el cerebro del loop react.
        devuelve la acción a ejecutar.
        """
        # si no tenemos datos de la película, hay que buscarlos
        # compruebo si todavía no se han obtenido los datos de la película
        if self.datos_pelicula is None:
            # devuelvo la acción de buscar los datos
            return {"accion": "buscar"}

        # si tenemos datos pero no informe, hay que generarlo
        # compruebo si ya hay datos pero todavía no hay informe generado
        if self.informe_completo is None:
            # comprobamos que los datos mínimos están disponibles
            # compruebo que los datos de película incluyan al menos el título
            if not self.datos_pelicula.get("titulo"):
                # devuelvo la acción de error si faltan datos mínimos
                return {"accion": "error", "motivo": "sin datos suficientes para continuar"}
            # devuelvo la acción de generar el informe
            return {"accion": "generar_informe"}

        # si tenemos informe pero no está guardado, hay que guardarlo
        # compruebo si hay informe generado pero todavía no se ha guardado
        if self.informe_completo and not self.informe_completo.get("guardado"):
            # devuelvo la acción de guardar el informe
            return {"accion": "guardar"}

        # todo completado: romper el bucle
        # devuelvo la acción de fin cuando ya todo está completado
        return {"accion": "fin"}

    # — fase 3: actuar —

    # defino el método que ejecuta la búsqueda de datos de la película
    def _actuar_buscar(self) -> bool:
        """
        invoca el buscador y guarda los datos en el estado.
        devuelve true si hay datos suficientes para continuar.
        """
        # registro el mensaje de que se está buscando
        self._registrar_paso(MENSAJES_CARGA["buscando"])

        # ejecuto el buscador con el título el año y el id de tmdb guardados
        datos = self.buscador.ejecutar(self.titulo, self.anio, self.tmdb_id)

        # registro errores parciales sin interrumpir
        # compruebo si el buscador devolvió errores parciales
        if datos.get("errores"):
            # añado esos errores a la lista de errores de la sesión
            self.errores.extend(datos["errores"])

        # si omdb ha fallado no tenemos datos básicos: paramos
        # compruebo si no se obtuvo ni siquiera el título de la película
        if not datos.get("titulo"):
            # determino el motivo del fallo a partir de los errores o uso uno genérico
            motivo = datos["errores"][0] if datos.get("errores") else "película no encontrada"
            # registro el mensaje de que no se encontraron datos
            self._registrar_paso(MENSAJES_CARGA["sin_datos"])
            # añado un error explicativo a la lista de errores
            self.errores.append(f"Indy no encontró '{self.titulo}' — prueba con el título en inglés si es una película extranjera. ({motivo})")
            # devuelvo falso indicando que la búsqueda falló
            return False

        # guardo los datos obtenidos en el estado de la sesión
        self.datos_pelicula = datos
        # devuelvo verdadero indicando que la búsqueda tuvo éxito
        return True

    # defino el método que genera el informe completo de la película
    def _actuar_generar_informe(self) -> bool:
        """
        invoca el generador de veredicto y guarda el informe en el estado.
        devuelve true si el informe se ha generado correctamente.
        """
        # registro el mensaje de que se está generando el informe
        self._registrar_paso(MENSAJES_CARGA["generando"])

        # ejecuto la herramienta de veredicto con los datos disponibles
        resultado = self.veredicto.ejecutar(
            # paso los datos de la película encontrados
            datos_pelicula=self.datos_pelicula,
            # paso el perfil del usuario
            perfil_usuario=self.perfil_usuario,
            # paso el nombre del usuario
            nombre_usuario=self.nombre_usuario,
        )

        # compruebo si la generación del veredicto falló
        if not resultado["ok"]:
            # añado el error devuelto a la lista de errores
            self.errores.append(resultado["error"])
            # devuelvo falso indicando que la generación falló
            return False

        # registro el mensaje de que se está verificando el informe
        self._registrar_paso(MENSAJES_CARGA["verificando"])

        # verifico que el informe tiene todas las secciones obligatorias
        # defino la lista de secciones que el informe debe contener sí o sí
        secciones_obligatorias = [
            "titulo_anio", "de_que_va", "critica_vs_publico",
            "indice_giros", "post_creditos", "streaming_espana",
            "banda_sonora", "snack", "veredicto",
        ]
        # extraigo el informe generado del resultado
        informe = resultado["informe"]
        # calculo qué secciones obligatorias faltan en el informe
        secciones_faltantes = [s for s in secciones_obligatorias if s not in informe]

        # compruebo si faltan secciones obligatorias
        if secciones_faltantes:
            # añado un error indicando qué secciones faltan
            self.errores.append(f"secciones incompletas: {secciones_faltantes}")
            # devuelvo falso indicando que el informe está incompleto
            return False

        # guardo el informe completo en el estado de la sesión
        self.informe_completo = informe
        # marco el informe como todavía no guardado en base de datos
        self.informe_completo["guardado"] = False
        # añado la url del póster obtenida de los datos de la película
        self.informe_completo["poster_url"] = self.datos_pelicula.get("poster_url")
        # añado el id del tráiler obtenido de los datos de la película
        self.informe_completo["youtube_trailer_id"] = self.datos_pelicula.get("youtube_trailer_id")

        # devuelvo verdadero indicando que el informe se generó correctamente
        return True

    # defino el método que guarda el informe completo en la base de datos
    def _actuar_guardar(self) -> bool:
        """
        invoca la herramienta informe y persiste el resultado en sqlite.
        devuelve true si el guardado ha sido exitoso.
        """
        # registro el mensaje de que se está guardando el informe
        self._registrar_paso(MENSAJES_CARGA["guardando"])

        # extraigo la sección de crítica versus público del informe
        critica_vs_publico = self.informe_completo.get("critica_vs_publico", {})

        # ejecuto la herramienta de informe para persistir los datos
        resultado = self.informe.ejecutar(
            # paso el título de la película
            titulo=self.datos_pelicula["titulo"],
            # paso el año de la película
            anio=self.datos_pelicula["anio"],
            # paso el perfil del usuario
            perfil_usuario=self.perfil_usuario,
            # paso la puntuación de la crítica
            puntuacion_critica=critica_vs_publico.get("puntuacion_critica"),
            # paso la puntuación del público
            puntuacion_publico=critica_vs_publico.get("puntuacion_publico"),
            # paso el texto del veredicto
            veredicto=self.informe_completo.get("veredicto", ""),
            # paso el informe completo a guardar
            informe_completo=self.informe_completo,
        )

        # compruebo si el guardado falló
        if not resultado["ok"]:
            # añado el error devuelto a la lista de errores
            self.errores.append(resultado["error"])
            # devuelvo falso indicando que el guardado falló
            return False

        # marco el informe como guardado en el estado
        self.informe_completo["guardado"] = True
        # guardo el identificador asignado por sqlite
        self.informe_completo["id_sqlite"] = resultado["id"]
        # guardo la fecha de consulta devuelta por el guardado
        self.informe_completo["fecha_consulta"] = resultado["fecha_consulta"]
        # devuelvo verdadero indicando que el guardado tuvo éxito
        return True

    # — fase 4: observar y loop principal —

    # defino el método que evalúa el resultado de la última acción ejecutada
    def observar(self, exito: bool, accion: str) -> dict:
        """
        evalúa el resultado de la acción ejecutada.
        decide si continuar el loop, reintentar o parar.
        """
        # registro el mensaje de que se está observando el resultado
        self._registrar_paso(MENSAJES_CARGA["observando"])

        # compruebo si la acción anterior tuvo éxito
        if exito:
            # devuelvo que se debe continuar el loop
            return {"continuar": True}

        # si la acción ha fallado, compruebo si puedo reintentar
        # compruebo si todavía quedan iteraciones disponibles para reintentar
        if self.iteraciones < self.MAX_ITERACIONES:
            # devuelvo que se debe continuar reintentando la misma acción
            return {"continuar": True, "reintentar": accion}

        # devuelvo que no se debe continuar si ya no quedan iteraciones
        return {"continuar": False}

    # defino el método principal que ejecuta todo el flujo del agente
    def ejecutar(
        self,
        titulo: str,
        perfil_usuario: str,
        anio: int = None,
        nombre_usuario: str = None,
        forzar_nuevo: bool = False,
        tmdb_id: int = None,
    ) -> dict:
        """
        punto de entrada principal del agente.
        ejecuta el loop react completo y devuelve el informe final.
        si forzar_nuevo=True ignora la caché y repite el análisis completo.
        """

        # — percibir —
        # ejecuto la fase de percepción con los datos recibidos
        percepcion = self.percibir(titulo, perfil_usuario, anio, nombre_usuario, tmdb_id)

        # compruebo si la percepción inicial falló
        if not percepcion["ok"]:
            # devuelvo un error indicando que la percepción falló
            return {"ok": False, "error": "error en la percepción inicial", "log": self.log}

        # si hay caché y el usuario no ha pedido repetir, devuelvo el informe guardado
        # compruebo si hay caché disponible y no se pidió forzar un nuevo análisis
        if percepcion.get("cache") and not forzar_nuevo:
            # registro el mensaje de fin del proceso
            self._registrar_paso(MENSAJES_CARGA["fin"])
            # devuelvo el informe obtenido de la caché
            return {
                # indico que la ejecución terminó correctamente
                "ok": True,
                # indico que el resultado proviene de caché
                "cache": True,
                # incluyo el informe obtenido de caché
                "informe": percepcion["informe"],
                # incluyo la fecha de la consulta guardada
                "fecha_consulta": percepcion["fecha_consulta"],
                # incluyo el log acumulado
                "log": self.log,
            }

        # — loop react —
        # inicio el bucle principal del agente que se repite hasta terminar
        while True:

            # control de iteraciones
            # compruebo si se ha superado el número máximo de iteraciones
            if not self._incrementar_iteracion():
                # registro el mensaje de que no se obtuvieron datos suficientes
                self._registrar_paso(MENSAJES_CARGA["sin_datos"])
                # devuelvo un error indicando que se alcanzó el límite de iteraciones
                return {
                    # indico que la ejecución no terminó correctamente
                    "ok": False,
                    # indico el motivo del fallo
                    "error": "límite de iteraciones alcanzado",
                    # incluyo los errores parciales acumulados
                    "errores_parciales": self.errores,
                    # incluyo el log acumulado
                    "log": self.log,
                }

            # — razonar: qué hago ahora —
            # pido al método razonar que decida la siguiente acción
            decision = self.razonar()
            # extraigo el nombre de la acción decidida
            accion = decision["accion"]

            # — actuar: ejecuto la acción decidida —
            # compruebo si la acción decidida es buscar datos
            if accion == "buscar":
                # ejecuto la búsqueda y guardo si tuvo éxito
                exito = self._actuar_buscar()

            # compruebo si la acción decidida es generar el informe
            elif accion == "generar_informe":
                # ejecuto la generación del informe y guardo si tuvo éxito
                exito = self._actuar_generar_informe()

            # compruebo si la acción decidida es guardar el informe
            elif accion == "guardar":
                # ejecuto el guardado del informe y guardo si tuvo éxito
                exito = self._actuar_guardar()

            # compruebo si la acción decidida es finalizar
            elif accion == "fin":
                # condición de salida: todo completado
                # registro el mensaje de fin del proceso
                self._registrar_paso(MENSAJES_CARGA["fin"])
                # devuelvo el resultado final completo del agente
                return {
                    # indico que la ejecución terminó correctamente
                    "ok": True,
                    # indico que el resultado no proviene de caché
                    "cache": False,
                    # incluyo el informe completo generado
                    "informe": self.informe_completo,
                    # incluyo el id del vídeo de youtube si existe
                    "youtube_video_id": self.datos_pelicula.get("youtube_video_id") if self.datos_pelicula else None,
                    # incluyo si el vídeo de youtube es lofi
                    "youtube_es_lofi": self.datos_pelicula.get("youtube_es_lofi", False) if self.datos_pelicula else False,
                    # incluyo la url del póster de la película
                    "poster_url": self.datos_pelicula.get("poster_url") if self.datos_pelicula else None,
                    # incluyo los errores parciales acumulados durante el proceso
                    "errores_parciales": self.errores,
                    # incluyo el log acumulado de todo el proceso
                    "log": self.log,
                }

            # compruebo si la acción decidida es un error irrecuperable
            elif accion == "error":
                # registro el mensaje de error en el log
                self._registrar_paso(MENSAJES_CARGA["error"])
                # devuelvo el error con el motivo indicado por razonar
                return {
                    # indico que la ejecución no terminó correctamente
                    "ok": False,
                    # incluyo el motivo del error o uno genérico
                    "error": decision.get("motivo", "error desconocido"),
                    # incluyo los errores parciales acumulados
                    "errores_parciales": self.errores,
                    # incluyo el log acumulado
                    "log": self.log,
                }

            # — observar: evalúo el resultado y decido si continuar —
            # ejecuto la fase de observación con el resultado de la acción
            observacion = self.observar(exito, accion)

            # compruebo si la observación indica que no se debe continuar
            if not observacion["continuar"]:
                # registro el mensaje de error en el log
                self._registrar_paso(MENSAJES_CARGA["error"])
                # devuelvo un error indicando que la acción no se pudo completar
                return {
                    # indico que la ejecución no terminó correctamente
                    "ok": False,
                    # incluyo el detalle de qué acción no se pudo completar
                    "error": f"no se ha podido completar la acción: {accion}",
                    # incluyo los errores parciales acumulados
                    "errores_parciales": self.errores,
                    # incluyo el log acumulado
                    "log": self.log,
                }
