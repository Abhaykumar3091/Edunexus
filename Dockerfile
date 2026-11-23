# Multi-stage Dockerfile for Heroku Container Deployment
# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend + Static Host
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ ./backend/

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /frontend/dist ./frontend/dist

ENV PORT=8000
ENV PYTHONPATH=/app/backend

EXPOSE 8000

CMD uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
