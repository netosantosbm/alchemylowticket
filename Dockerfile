# ==========================================
# Estágio 1: Build do Frontend React (Vite)
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==========================================
# Estágio 2: Imagem de Produção FastAPI (Python)
# ==========================================
FROM python:3.11-slim AS production

# Evita geração de bytecode .pyc e buffer de saída
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FRONTEND_DIST=/app/frontend_dist
ENV PORT=8000
ENV HOST=0.0.0.0

WORKDIR /app

# Instala dependências mínimas do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala bibliotecas Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código do backend e modelos
COPY backend/models.py ./models.py
COPY backend/app ./app

# Copia os arquivos compilados do frontend do estágio 1
COPY --from=frontend-builder /build/dist /app/frontend_dist

# Porta padrão de escuta
EXPOSE 8000

# Healthcheck interno
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/api/health || exit 1

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
