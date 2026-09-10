# Multi-stage Dockerfile for SANJAL Block Planner
# Stage 1: Build the React + Vite Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python FastAPI Backend + Serve Frontend Static Assets
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    FRONTEND_DIST=/app/frontend/dist

# Install minimal build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application source
COPY backend/ ./backend/

# Copy built frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Working directory in backend
WORKDIR /app/backend

# Seed data if empty and run application
CMD sh -c "python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
