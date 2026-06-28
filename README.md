# 🐾 Indy Web — FastAPI + React

Versión web del agente Indy. Backend en FastAPI, frontend en React + Tailwind.

## Estructura

```
indy-web/
├── backend/
│   └── main.py          ← API FastAPI
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── Formulario.jsx
│   │       ├── Informe.jsx
│   │       └── Cargando.jsx
│   └── package.json
├── agente/              ← copia del agente (mismas herramientas)
└── datos/               ← SQLite
```

## Arrancar

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend en http://localhost:5173 · Backend en http://localhost:8000

## Variables de entorno

Copia `.env.example` a `.env` y rellena las keys:

```
GROQ_API_KEY=
OMDB_API_KEY=
TMDB_API_KEY=
STREAMING_API_KEY=
DOESTHEDOGDIE_API_KEY=
YOUTUBE_API_KEY=
```
