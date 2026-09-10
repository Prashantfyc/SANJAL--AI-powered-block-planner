FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    FRONTEND_DIST=/app/frontend/dist

# Install backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source, compiled frontend, and launcher
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/
COPY start.py ./

EXPOSE 8000

CMD ["python", "start.py"]
