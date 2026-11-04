# Imagen base
FROM python:3.12-slim

# Variables de entorno de Python
ENV PYTHONDONTWRITEBYTECODE=1
# Logs sin buffer
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo de la aplicacion
COPY . .

# Puerto
EXPOSE 5000

# Gunicorn ejecuta la app Flask. --preload crea las tablas y los datos
# iniciales una sola vez antes de lanzar los workers.
CMD ["gunicorn", "--preload", "--bind", "0.0.0.0:5000", "--workers", "3", "run:app"]
