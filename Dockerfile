# Utiliza una imagen base oficial de Python
FROM python:3.9-slim

# Instala las dependencias necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    perl \
    libio-tee-perl \
    libunicode-string-perl \
    libauthen-ntlm-perl \
    ca-certificates \
    wget && \
    wget -O /usr/local/bin/imapsync https://raw.githubusercontent.com/imapsync/imapsync/master/imapsync && \
    chmod +x /usr/local/bin/imapsync && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos y la aplicación al contenedor
COPY myapp/requirements.txt /app/requirements.txt
COPY myapp /app

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Define variables de entorno para Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expone el puerto en el que Flask se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["flask", "run"]
