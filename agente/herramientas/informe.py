# informe.py — herramienta 3: guarda el informe completo en sqlite

# importo os para construir rutas de archivos
import os
# importo json para serializar y deserializar el informe completo
import json
# importo sqlite3 para conectarme a la base de datos local
import sqlite3
# importo datetime para generar la fecha de cada consulta
from datetime import datetime

# ruta a la base de datos en la carpeta datos/ del proyecto
# construyo la ruta absoluta hasta el archivo de base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "datos", "indy.db")


# defino la clase informe que gestiona toda la persistencia en sqlite
class Informe:
    """
    gestiona la persistencia de informes en sqlite.
    inicializa la base de datos, comprueba la caché y guarda informes.
    """

    # defino el constructor que guarda la ruta y prepara la base de datos
    def __init__(self):
        # guardo la ruta de la base de datos en la instancia
        self.db_path = DB_PATH
        # inicializo la base de datos creando la tabla si hace falta
        self._inicializar_db()

    # — inicialización —

    # defino el método que crea la tabla de informes si no existe
    def _inicializar_db(self):
        """
        crea la tabla de informes si no existe.
        se ejecuta automáticamente al instanciar la clase.
        """
        # abro la conexión a la base de datos sqlite
        conexion = sqlite3.connect(self.db_path)
        # creo un cursor para ejecutar sentencias sql
        cursor = conexion.cursor()

        # ejecuto la sentencia que crea la tabla informes si no existe ya
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS informes (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo            TEXT NOT NULL,
                anio              TEXT,
                perfil_usuario    TEXT,
                puntuacion_critica REAL,
                puntuacion_publico REAL,
                veredicto         TEXT,
                informe_completo  TEXT,
                fecha_consulta    TEXT
            )
        """)

        # confirmo los cambios realizados en la base de datos
        conexion.commit()
        # cierro la conexión a la base de datos
        conexion.close()

    # — caché —

    # defino el método que busca si ya existe un informe guardado para un título
    def buscar_en_cache(self, titulo: str) -> dict | None:
        """
        comprueba si la película ya tiene un informe guardado.
        devuelve el informe más reciente o none si no existe.
        """
        # intento realizar la consulta y manejar posibles errores
        try:
            # abro la conexión a la base de datos sqlite
            conexion = sqlite3.connect(self.db_path)
            # creo un cursor para ejecutar la consulta
            cursor = conexion.cursor()

            # ejecuto la consulta que busca el informe más reciente para el título dado
            cursor.execute("""
                SELECT informe_completo, fecha_consulta
                FROM informes
                WHERE titulo = ?
                ORDER BY id DESC
                LIMIT 1
            """, (titulo,))

            # obtengo la primera fila del resultado si existe
            fila = cursor.fetchone()
            # cierro la conexión a la base de datos
            conexion.close()

            # compruebo si se encontró alguna fila
            if fila:
                # devuelvo el informe deserializado junto con su fecha de consulta
                return {
                    # convierto el texto json guardado de vuelta a un diccionario
                    "informe": json.loads(fila[0]),
                    # incluyo la fecha de la consulta guardada
                    "fecha_consulta": fila[1],
                }
            # devuelvo none si no se encontró ninguna fila
            return None

        # capturo cualquier excepción ocurrida durante la consulta
        except Exception as e:
            # devuelvo none si ocurrió algún error al consultar la caché
            return None

    # — guardado —

    # defino el método que guarda un nuevo informe en la base de datos
    def ejecutar(
        self,
        titulo: str,
        anio: str,
        perfil_usuario: str,
        puntuacion_critica: float,
        puntuacion_publico: float,
        veredicto: str,
        informe_completo: dict,
    ) -> dict:
        """
        herramienta 3 del agente indy.
        guarda el informe en sqlite solo después de emitir el veredicto.
        devuelve confirmación y el id del registro generado.
        """
        # intento realizar el guardado y manejar posibles errores
        try:
            # abro la conexión a la base de datos sqlite
            conexion = sqlite3.connect(self.db_path)
            # creo un cursor para ejecutar la inserción
            cursor = conexion.cursor()

            # genero la fecha y hora actuales en formato de texto
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ejecuto la sentencia que inserta el nuevo informe en la tabla
            cursor.execute("""
                INSERT INTO informes (
                    titulo, anio, perfil_usuario,
                    puntuacion_critica, puntuacion_publico,
                    veredicto, informe_completo, fecha_consulta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                # paso el título de la película
                titulo,
                # paso el año de la película
                anio,
                # paso el perfil del usuario
                perfil_usuario,
                # paso la puntuación de la crítica
                puntuacion_critica,
                # paso la puntuación del público
                puntuacion_publico,
                # paso el texto del veredicto
                veredicto,
                # serializo el informe completo a texto json
                json.dumps(informe_completo, ensure_ascii=False),
                # paso la fecha generada antes
                fecha,
            ))

            # confirmo la inserción en la base de datos
            conexion.commit()
            # obtengo el id autogenerado del registro insertado
            registro_id = cursor.lastrowid
            # cierro la conexión a la base de datos
            conexion.close()

            # devuelvo confirmación con el id y la fecha del registro guardado
            return {"ok": True, "id": registro_id, "fecha_consulta": fecha}

        # capturo cualquier excepción ocurrida durante el guardado
        except Exception as e:
            # devuelvo un error indicando que falló el guardado en sqlite
            return {"ok": False, "error": f"error al guardar en sqlite — {str(e)}"}
