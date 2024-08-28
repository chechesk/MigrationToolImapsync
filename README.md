# Herramienta de Migración de Correo Electrónico con Flask e Imapsync

Esta es una aplicación web construida con Flask que permite la migración de correos electrónicos entre servidores IMAP utilizando `imapsync`. La aplicación soporta múltiples migraciones simultáneas y permite ver el progreso de cada migración en tiempo real desde la interfaz web.

## Características

- **Migración de correos electrónicos** entre dos servidores IMAP utilizando `imapsync`.
- **Soporte para múltiples migraciones** simultáneas.
- **Visualización del log en tiempo real** de cada migración directamente desde la interfaz web.
- **Persistencia de migraciones**: puedes ver y continuar monitoreando las migraciones activas incluso si cierras y vuelves a abrir la página.

## Requisitos

- **Docker**: para ejecutar la aplicación en un contenedor.
- **Python 3**: si prefieres ejecutar la aplicación localmente sin Docker.
- **Perl**: requerido para ejecutar `imapsync` junto con las dependencias necesarias.

## Configuración y Ejecución

### Usando Docker

1. **Construir la Imagen Docker**:

   ```bash
   docker build -t migration-tool .
   
2. **Ejecutar el Contenedorr**:
   ```bash
    docker run -p 5000:5000 migration-tool
3. **Acceder a la Aplicación**:

   Abre tu navegador y navega a http://localhost:5000 para acceder a la interfaz de la aplicación.

