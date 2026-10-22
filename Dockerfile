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
ENV PORT=8050
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

# Otimizações de memória para VPS enxuta
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV PYTHONMALLOC=malloc

# Porta padrão de escuta
EXPOSE 8050

# Comando de inicialização otimizado para baixo consumo de RAM (1 worker assíncrono)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8050} --workers 1"]
