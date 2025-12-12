# docker/Dockerfile
FROM python:3.12-slim

# Prevents Python from writing pyc files and buffers stdout/stderr less
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# App directory
WORKDIR /app

# System deps (kept minimal). tzdata is useful for consistent timezone handling.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better build caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source
COPY app /app/app

# Data volume (SQLite DB will live here)
RUN mkdir -p /data
ENV DB_PATH=/data/stocks.db

EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
