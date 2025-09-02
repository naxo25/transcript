FROM python:3.11-slim

# Instalar ffmpeg y otras dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app.py .

# Exponer el puerto (Render usa PORT env variable)
EXPOSE 10000

# Variables de entorno para optimización
ENV WHISPER_MODEL=tiny
ENV PYTHONUNBUFFERED=1

# Comando optimizado: 1 worker, 1 thread, timeout largo
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "300", "--workers", "1", "--threads", "1", "--worker-class", "sync", "app:app"]