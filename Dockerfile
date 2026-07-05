# ---- Etapa 1: compilo el frontend ----
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # genera /app/frontend/dist

# ---- Etapa 2: backend + servir ----
FROM python:3.11-slim
WORKDIR /app

# instalo dependencias de python
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# copio el paquete del agente (backend/main.py hace "from agente.indy import IndyAgent")
COPY agente/ ./agente/

# creo la carpeta de datos vacía para la caché sqlite (se genera en tiempo de ejecución)
RUN mkdir -p datos

# copio el backend
COPY backend/ ./backend/

# copio el frontend ya compilado como carpeta estática servida por fastapi
COPY --from=frontend /app/frontend/dist ./static

EXPOSE 7860
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
