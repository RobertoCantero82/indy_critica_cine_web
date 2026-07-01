<p align="center">
  <img src="rc_logo_indy.svg" alt="RC logo animado" width="680"/>
</p>

<h1 align="center">Indy — ¿Vale la pena verla?</h1>

<p align="center"><em>Un agente de IA con personalidad de perro crítico de cine que decide, con criterio propio, si una película merece tu tiempo.</em></p>

---

## 🐾 Descripción

**Indy** es un agente conversacional que analiza cualquier película y emite un veredicto honesto, película recomendable o no, adaptado al perfil del espectador que pregunta. No es un agregador de puntuaciones: cruza datos reales de varias fuentes (crítica, público, plataformas de streaming, curiosidades) con un modelo de lenguaje que decide y argumenta como lo haría un cinéfilo con carácter.

El proyecto nació como agente de terminal y ha evolucionado a una aplicación web completa: **backend en FastAPI** que orquesta el agente con un bucle **ReAct** (percibir → razonar → actuar → observar), y **frontend en React + Vite** con una experiencia de usuario cuidada. Existe el autocompletado de títulos con póster, pegatinas de perfil ilustradas y un informe final con formato de ficha de cine.

---

## ✨ Funcionalidades

- **Búsqueda con autocompletado**: escribes el título y aparecen coincidencias reales de TMDB con póster, título y año (sin necesidad de indicar el año a mano ni adivinar el título original en inglés).
- **Veredicto con criterio real**: la recomendación pondera la nota media de crítica y público, no repite el mismo "sí" de forma automática y una película floja recibe un "no" honesto.
- **Perfiles de espectador**: 5 perfiles ilustrados (Palomitero, Cinéfilo, Fantasioso, Intenso, Curioso) que cambian el tono y el enfoque del análisis.
- **Informe completo por película**:
  - Sinopsis sin spoilers
  - Comparativa crítica vs. público con comentario propio
  - Índice de giros de guión
  - Escenas post-créditos
  - Dónde verla en streaming (España)
  - Banda sonora con enlace a YouTube
  - Snack a juego con la ambientación de la película
  - Datos curiosos (sustos, muertes de animales, cuarta pared...)
  - Alternativas mejores si el veredicto es negativo
- **Caché de análisis**: si una película ya se analizó antes, se ofrece reutilizar el informe guardado o repetir el análisis desde cero.
- **"Voy a tener suerte"**: chat libre donde describes tu plan o estado de ánimo e Indy recomienda una película acorde, con plataforma de streaming incluida.

---

## 🧠 Cómo funciona el agente

Indy implementa un bucle **ReAct** con tres herramientas independientes:

```
percibir  → comprueba si la película ya está en caché
razonar   → decide qué herramienta ejecutar a continuación
actuar    → Buscador → Veredicto → Informe
observar  → evalúa el resultado y reintenta si algo falla
```

| Herramienta | Función |
|---|---|
| `Buscador` | Consulta TMDB, OMDb, la disponibilidad en streaming, escenas post-créditos y curiosidades. Si el usuario eligió la película de la lista de candidatos, resuelve todo por `tmdb_id` exacto en vez de adivinar el título |
| `Veredicto` | Genera cada sección del informe con el modelo de lenguaje (Groq / Llama 3.1), incluida la recomendación final ponderada por las puntuaciones reales |
| `Informe` | Persiste el análisis en SQLite y gestiona la caché por título |

---

## 🗂️ Estructura del proyecto

```
indy_critica_cine_web/
├── agente/
│   ├── indy.py                  # orquestador del bucle ReAct
│   ├── sistema.py                # personalidad, tono y perfiles de Indy
│   └── herramientas/
│       ├── buscador.py           # TMDB, OMDb, streaming, curiosidades
│       ├── veredicto.py          # generación del informe con el LLM
│       └── informe.py            # persistencia en SQLite
│
├── backend/
│   ├── main.py                   # API FastAPI
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── Formulario.jsx    # búsqueda, autocompletado y perfiles
│   │       ├── Informe.jsx       # ficha final del análisis
│   │       └── Cargando.jsx
│   └── public/                   # pegatinas de perfil y assets estáticos
│
├── datos/
│   └── indy.db                   # caché de análisis en SQLite
│
├── iniciar_demo.vbs              # arranca backend + frontend en segundo plano
├── detener_demo.bat              # los detiene
└── presentacion/
```

---

## 🛠️ Tecnologías

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688)
![Groq](https://img.shields.io/badge/Groq-Llama_3.1-orange)
![React](https://img.shields.io/badge/React-18-61DAFB)
![Vite](https://img.shields.io/badge/Vite-4-646CFF)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57)

**APIs externas**: [Groq](https://groq.com/) (LLM) · [TMDB](https://www.themoviedb.org/) · [OMDb](http://www.omdbapi.com/) · Streaming Availability (RapidAPI) · [DoesTheDogDie](https://www.doesthedogdie.com/) · YouTube Data API

---

## 🚀 Arrancar el proyecto

### Opción rápida (Windows)

Doble clic en **`iniciar_demo.vbs`** — arranca backend y frontend en segundo plano y abre el navegador solo. Para pararlos, doble clic en **`detener_demo.bat`**.

### Manual

**Backend**
```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Frontend en `http://localhost:5173` · Backend en `http://localhost:8000`

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```
GROQ_API_KEY=
OMDB_API_KEY=
TMDB_API_KEY=
RAPIDAPI_KEY=
YOUTUBE_API_KEY=
DOESTHEDOGDIE_API_KEY=
```

---

## 👤 Autor

**Roberto Cantero** — proyecto final de bootcamp
