#imagen de base
From python:3.12-slim

#variables de entorno
ENV pythondontwritebytecode=1
#logs
ENV pythonnunbuffered=1
#directorio de trabajo
WORKDIR /app

#dependencias del sistema

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \ 
    && rm -rf /var/lib/apt/lists/*

#dependencias de pythond

COPY requirements.txt .

#Instalamos las dependencias

RUN pip install --no-cache-dir -r requirements.txt

#codigo de la aplicacion

COPY . .

#puerto

EXPOSE 5000

#Guinicorn exect app en flask

CMD [ "gunicorns","--bind","0.0.0.0:5000","--workers","3","run:app" ]