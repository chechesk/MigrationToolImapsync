# Utiliza una imagen base de Ubuntu
FROM ubuntu:20.04

# Establece el directorio de trabajo
WORKDIR /app

# Configura las variables de entorno para que no haya prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Actualiza el sistema e instala las dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    libauthen-ntlm-perl \
    libclass-load-perl \
    libcrypt-openssl-rsa-perl \
    libcrypt-ssleay-perl \
    libdata-uniqid-perl \
    libdigest-hmac-perl \
    libdist-checkconflicts-perl \
    libencode-imaputf7-perl \
    libfile-copy-recursive-perl \
    libfile-tail-perl \
    libio-compress-perl \
    libio-socket-inet6-perl \
    libio-socket-ssl-perl \
    libio-tee-perl \
    libjson-webtoken-perl \
    libmail-imapclient-perl \
    libmodule-scandeps-perl \
    libnet-dbus-perl \
    libnet-ssleay-perl \
    libpar-packer-perl \
    libproc-processtable-perl \
    libreadonly-perl \
    libregexp-common-perl \
    libsys-meminfo-perl \
    libterm-readkey-perl \
    libtest-fatal-perl \
    libtest-mock-guard-perl \
    libtest-mockobject-perl \
    libtest-pod-perl \
    libtest-requires-perl \
    libtest-simple-perl \
    libunicode-string-perl \
    liburi-perl \
    libtest-nowarnings-perl \
    libtest-deep-perl \
    libtest-warn-perl \
    make \
    time \
    cpanminus \
    wget && \
    cpanm Mail::IMAPClient && \
    wget -N https://raw.githubusercontent.com/imapsync/imapsync/master/imapsync && \
    chmod +x imapsync && \
    mv imapsync /usr/local/bin/ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos y la aplicación al contenedor
COPY myapp/requirements.txt /app/requirements.txt
COPY myapp /app

# Instala las dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Define variables de entorno para Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expone el puerto en el que Flask se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["flask", "run"]
