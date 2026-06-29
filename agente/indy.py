# indy.py — orquestador principal del agente indy (loop react)

from agente.herramientas.buscador import Buscador
from agente.herramientas.veredicto import Veredicto
from agente.herramientas.informe import Informe
from agente.herramientas.pegatina import Pegatina
from agente.sistema import MENSAJES_CARGA


class IndyAgent:
    """
    orquestador principal del agente indy.
    implementa el loop react: percibir → razonar → actuar → observar.
    gestiona el estado de la sesión y el flujo completo de análisis.
    """

    MAX_ITERACIONES = 10

    def __init__(self):
        self.buscador = Buscador()
        self.veredicto = Veredicto()
        self.informe = Informe()
        self.pegatina = Pegatina()

        # estado de la sesión actual
        self.titulo = None
        self.anio = None
        self.perfil_usuario = None
        self.nombre_usuario = None
        self.datos_pelicula = None
        self.informe_completo = None
        self.iteraciones = 0
        self.errores = []
        self.log = []  # registro de pasos del loop para la ui

    # — gestión del estado —

    def _resetear_sesion(self):
        """limpia el estado antes de una nueva consulta."""
        self.titulo = None
        self.anio = None
        self.perfil_usuario = None
        self.nombre_usuario = None
        self.datos_pelicula = None
        self.informe_completo = None
        self.iteraciones = 0
        self.errores = []
        self.log = []

    def _registrar_paso(self, mensaje: str):
        """añade un mensaje al log y lo devuelve para la ui."""
        self.log.append(mensaje)
        return mensaje

    def _incrementar_iteracion(self) -> bool:
        """
        incrementa el contador de iteraciones.
        devuelve false si se supera el límite máximo.
        """
        self.iteraciones += 1
        if self.iteraciones > self.MAX_ITERACIONES:
            return False
        return True

    # — fase 1: percibir —

    def comprobar_cache(self, titulo: str) -> dict | None:
        """
        comprueba si la película ya tiene un informe guardado.
        devuelve el informe y la fecha o none si no existe.
        se llama desde la UI antes de ejecutar el agente.
        """
        return self.informe.buscar_en_cache(titulo.strip())

    def percibir(
        self,
        titulo: str,
        perfil_usuario: str,
        anio: int = None,
        nombre_usuario: str = None,
    ) -> dict:
        """
        recibe el input del usuario y prepara el estado inicial.
        comprueba la caché antes de arrancar el loop.
        """
        self._resetear_sesion()

        self.titulo = titulo.strip()
        self.anio = anio
        self.perfil_usuario = perfil_usuario
        self.nombre_usuario = nombre_usuario

        self._registrar_paso(MENSAJES_CARGA["inicio"])

        # compruebo si la película ya está en caché
        cache = self.informe.buscar_en_cache(self.titulo)
        if cache:
            return {
                "ok": True,
                "cache": True,
                "informe": cache["informe"],
                "fecha_consulta": cache["fecha_consulta"],
                "log": self.log,
            }

        return {"ok": True, "cache": False, "log": self.log}

    # — fase 2: razonar —

    def razonar(self) -> dict:
        """
        evalúa el estado actual y decide qué herramienta invocar a continuación.
        es el cerebro del loop react.
        devuelve la acción a ejecutar.
        """
        # si no tenemos datos de la película, hay que buscarlos
        if self.datos_pelicula is None:
            return {"accion": "buscar"}

        # si tenemos datos pero no informe, hay que generarlo
        if self.informe_completo is None:
            # comprobamos que los datos mínimos están disponibles
            if not self.datos_pelicula.get("titulo"):
                return {"accion": "error", "motivo": "sin datos suficientes para continuar"}
            return {"accion": "generar_informe"}

        # si tenemos informe pero no está guardado, hay que guardarlo
        if self.informe_completo and not self.informe_completo.get("guardado"):
            return {"accion": "guardar"}

        # todo completado: romper el bucle
        return {"accion": "fin"}

    # — fase 3: actuar —

    def _actuar_buscar(self) -> bool:
        """
        invoca el buscador y guarda los datos en el estado.
        devuelve true si hay datos suficientes para continuar.
        """
        self._registrar_paso(MENSAJES_CARGA["buscando"])

        datos = self.buscador.ejecutar(self.titulo, self.anio)

        # registro errores parciales sin interrumpir
        if datos.get("errores"):
            self.errores.extend(datos["errores"])

        # si omdb ha fallado no tenemos datos básicos: paramos
        if not datos.get("titulo"):
            motivo = datos["errores"][0] if datos.get("errores") else "película no encontrada"
            self._registrar_paso(MENSAJES_CARGA["sin_datos"])
            self.errores.append(f"Indy no encontró '{self.titulo}' — prueba con el título en inglés si es una película extranjera. ({motivo})")
            return False

        self.datos_pelicula = datos
        return True

    def _actuar_generar_informe(self) -> bool:
        """
        invoca el generador de veredicto y guarda el informe en el estado.
        devuelve true si el informe se ha generado correctamente.
        """
        self._registrar_paso(MENSAJES_CARGA["generando"])

        resultado = self.veredicto.ejecutar(
            datos_pelicula=self.datos_pelicula,
            perfil_usuario=self.perfil_usuario,
            nombre_usuario=self.nombre_usuario,
        )

        if not resultado["ok"]:
            self.errores.append(resultado["error"])
            return False

        self._registrar_paso(MENSAJES_CARGA["verificando"])

        # verifico que el informe tiene todas las secciones obligatorias
        secciones_obligatorias = [
            "titulo_anio", "de_que_va", "critica_vs_publico",
            "indice_giros", "post_creditos", "streaming_espana",
            "banda_sonora", "snack", "veredicto",
        ]
        informe = resultado["informe"]
        secciones_faltantes = [s for s in secciones_obligatorias if s not in informe]

        if secciones_faltantes:
            self.errores.append(f"secciones incompletas: {secciones_faltantes}")
            return False

        self.informe_completo = informe
        self.informe_completo["guardado"] = False
        self.informe_completo["poster_url"] = self.datos_pelicula.get("poster_url")

        # Generar pegatina coleccionable de la película
        try:
            res_pegatina = self.pegatina.ejecutar(
                titulo=self.datos_pelicula.get("titulo"),
                generos=self.datos_pelicula.get("generos", []),
                director=self.datos_pelicula.get("director", "")
            )
            if res_pegatina.get("ok"):
                self.informe_completo["pegatina_url"] = res_pegatina["pegatina_url"]
            else:
                self.informe_completo["pegatina_url"] = None
                if res_pegatina.get("error"):
                    self.errores.append(f"Error en pegatina: {res_pegatina['error']}")
        except Exception as e:
            self.informe_completo["pegatina_url"] = None
            self.errores.append(f"Excepción al generar pegatina: {str(e)}")

        return True

    def _actuar_guardar(self) -> bool:
        """
        invoca la herramienta informe y persiste el resultado en sqlite.
        devuelve true si el guardado ha sido exitoso.
        """
        self._registrar_paso(MENSAJES_CARGA["guardando"])

        critica_vs_publico = self.informe_completo.get("critica_vs_publico", {})

        resultado = self.informe.ejecutar(
            titulo=self.datos_pelicula["titulo"],
            anio=self.datos_pelicula["anio"],
            perfil_usuario=self.perfil_usuario,
            puntuacion_critica=critica_vs_publico.get("puntuacion_critica"),
            puntuacion_publico=critica_vs_publico.get("puntuacion_publico"),
            veredicto=self.informe_completo.get("veredicto", ""),
            informe_completo=self.informe_completo,
            pegatina_url=self.informe_completo.get("pegatina_url"),
        )

        if not resultado["ok"]:
            self.errores.append(resultado["error"])
            return False

        self.informe_completo["guardado"] = True
        self.informe_completo["id_sqlite"] = resultado["id"]
        self.informe_completo["fecha_consulta"] = resultado["fecha_consulta"]
        return True

    # — fase 4: observar y loop principal —

    def observar(self, exito: bool, accion: str) -> dict:
        """
        evalúa el resultado de la acción ejecutada.
        decide si continuar el loop, reintentar o parar.
        """
        self._registrar_paso(MENSAJES_CARGA["observando"])

        if exito:
            return {"continuar": True}

        # si la acción ha fallado, compruebo si puedo reintentar
        if self.iteraciones < self.MAX_ITERACIONES:
            return {"continuar": True, "reintentar": accion}

        return {"continuar": False}

    def ejecutar(
        self,
        titulo: str,
        perfil_usuario: str,
        anio: int = None,
        nombre_usuario: str = None,
        forzar_nuevo: bool = False,
    ) -> dict:
        """
        punto de entrada principal del agente.
        ejecuta el loop react completo y devuelve el informe final.
        si forzar_nuevo=True ignora la caché y repite el análisis completo.
        """

        # — percibir —
        percepcion = self.percibir(titulo, perfil_usuario, anio, nombre_usuario)

        if not percepcion["ok"]:
            return {"ok": False, "error": "error en la percepción inicial", "log": self.log}

        # si hay caché y el usuario no ha pedido repetir, devuelvo el informe guardado
        if percepcion.get("cache") and not forzar_nuevo:
            self._registrar_paso(MENSAJES_CARGA["fin"])
            return {
                "ok": True,
                "cache": True,
                "informe": percepcion["informe"],
                "fecha_consulta": percepcion["fecha_consulta"],
                "log": self.log,
            }

        # — loop react —
        while True:

            # control de iteraciones
            if not self._incrementar_iteracion():
                self._registrar_paso(MENSAJES_CARGA["sin_datos"])
                return {
                    "ok": False,
                    "error": "límite de iteraciones alcanzado",
                    "errores_parciales": self.errores,
                    "log": self.log,
                }

            # — razonar: qué hago ahora —
            decision = self.razonar()
            accion = decision["accion"]

            # — actuar: ejecuto la acción decidida —
            if accion == "buscar":
                exito = self._actuar_buscar()

            elif accion == "generar_informe":
                exito = self._actuar_generar_informe()

            elif accion == "guardar":
                exito = self._actuar_guardar()

            elif accion == "fin":
                # condición de salida: todo completado
                self._registrar_paso(MENSAJES_CARGA["fin"])
                return {
                    "ok": True,
                    "cache": False,
                    "informe": self.informe_completo,
                    "youtube_video_id": self.datos_pelicula.get("youtube_video_id") if self.datos_pelicula else None,
                    "youtube_es_lofi": self.datos_pelicula.get("youtube_es_lofi", False) if self.datos_pelicula else False,
                    "poster_url": self.datos_pelicula.get("poster_url") if self.datos_pelicula else None,
                    "errores_parciales": self.errores,
                    "log": self.log,
                }

            elif accion == "error":
                self._registrar_paso(MENSAJES_CARGA["error"])
                return {
                    "ok": False,
                    "error": decision.get("motivo", "error desconocido"),
                    "errores_parciales": self.errores,
                    "log": self.log,
                }

            # — observar: evalúo el resultado y decido si continuar —
            observacion = self.observar(exito, accion)

            if not observacion["continuar"]:
                self._registrar_paso(MENSAJES_CARGA["error"])
                return {
                    "ok": False,
                    "error": f"no se ha podido completar la acción: {accion}",
                    "errores_parciales": self.errores,
                    "log": self.log,
                }