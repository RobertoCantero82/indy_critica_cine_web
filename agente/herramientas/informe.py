# informe.py — herramienta 3: guarda el informe completo en sqlite

import os
import json
import sqlite3
from datetime import datetime

# ruta a la base de datos en la carpeta datos/ del proyecto
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "datos", "indy.db")


class Informe:
    """
    gestiona la persistencia de informes en sqlite.
    inicializa la base de datos, comprueba la caché y guarda informes.
    """

    def __init__(self):
        self.db_path = DB_PATH
        self._inicializar_db()

    # — inicialización —

    def _inicializar_db(self):
        """
        crea la tabla de informes si no existe.
        se ejecuta automáticamente al instanciar la clase.
        """
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()

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

        conexion.commit()
        conexion.close()

    # — caché —

    def buscar_en_cache(self, titulo: str) -> dict | None:
        """
        comprueba si la película ya tiene un informe guardado.
        devuelve el informe más reciente o none si no existe.
        """
        try:
            conexion = sqlite3.connect(self.db_path)
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT informe_completo, fecha_consulta
                FROM informes
                WHERE titulo = ?
                ORDER BY id DESC
                LIMIT 1
            """, (titulo,))

            fila = cursor.fetchone()
            conexion.close()

            if fila:
                return {
                    "informe": json.loads(fila[0]),
                    "fecha_consulta": fila[1],
                }
            return None

        except Exception as e:
            return None

    # — guardado —

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
        try:
            conexion = sqlite3.connect(self.db_path)
            cursor = conexion.cursor()

            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO informes (
                    titulo, anio, perfil_usuario,
                    puntuacion_critica, puntuacion_publico,
                    veredicto, informe_completo, fecha_consulta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                titulo,
                anio,
                perfil_usuario,
                puntuacion_critica,
                puntuacion_publico,
                veredicto,
                json.dumps(informe_completo, ensure_ascii=False),
                fecha,
            ))

            conexion.commit()
            registro_id = cursor.lastrowid
            conexion.close()

            return {"ok": True, "id": registro_id, "fecha_consulta": fecha}

        except Exception as e:
            return {"ok": False, "error": f"error al guardar en sqlite — {str(e)}"}