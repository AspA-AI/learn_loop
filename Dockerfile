#
# Railway single-service deployment for monorepo:
# - Build React/Vite frontend
# - Run FastAPI backend (and serve built frontend assets)
#

### Stage 1: build frontend
FROM node:20.19-alpine AS web
WORKDIR /app/client

COPY client/package.json client/package-lock.json ./
RUN npm ci

# Build-time API base URL (same-origin by default)
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY client/ ./
RUN npm run build

### Stage 2: run backend
FROM python:3.12-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    SERVE_CLIENT=true

WORKDIR /app/api

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./

# Copy built frontend into FastAPI container
COPY --from=web /app/client/dist ./static

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]


