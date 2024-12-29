import os
import subprocess
import uuid
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
from marshmallow import Schema, fields, ValidationError
import logging
from threading import Thread
import imaplib

app = Flask(__name__)

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Almacenamiento en memoria para los logs y el estado de las migraciones
migrations = {}

# Esquema de validación para los datos de migración
class MigrationSchema(Schema):
    src_host = fields.String(required=True)
    src_port = fields.Integer(required=True)
    src_user = fields.String(required=True)
    src_password = fields.String(required=True)
    src_encryption = fields.String(validate=lambda x: x in ["none", "ssl", "tls"], required=True)
    dst_host = fields.String(required=True)
    dst_port = fields.Integer(required=True)
    dst_user = fields.String(required=True)
    dst_password = fields.String(required=True)
    dst_encryption = fields.String(validate=lambda x: x in ["none", "ssl", "tls"], required=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/migration_status', methods=['GET'])
def migration_status():
    return jsonify(migrations)


@app.route('/migrate', methods=['POST'])
def migrate():
    try:
        schema = MigrationSchema()
        data = schema.load(request.form.to_dict())

        migration_id = str(uuid.uuid4())  # Genera un ID único para la migración
        migrations[migration_id] = {"status": "in_progress", "log": []}

        # Guarda las contraseñas en las variables de entorno
        os.environ['SRC_PASSWORD'] = data['src_password']
        os.environ['DST_PASSWORD'] = data['dst_password']

        # Construye el comando imapsync
        command = construct_command(data)
        logger.info(f"Starting migration with ID {migration_id}: {command}")

        # Ejecuta la migración en un hilo separado
        thread = Thread(target=run_migration, args=(migration_id, command))
        thread.start()

        return jsonify({"migration_id": migration_id}), 202

    except ValidationError as err:
        logger.error(f"Validation error: {err.messages}")
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.exception("Unexpected error during migration")
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500


@app.route('/migration_log/<migration_id>', methods=['GET'])
def migration_log(migration_id):
    def generate():
        if migration_id in migrations:
            while migrations[migration_id]["status"] == "in_progress":
                while migrations[migration_id]["log"]:
                    line = migrations[migration_id]["log"].pop(0)
                    yield f"data: {line}\n\n"
            yield f"data: Migration completed with status {migrations[migration_id]['status']}\n\n"
        else:
            yield "data: Migration ID not found\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


def run_migration(migration_id, command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        for line in iter(process.stdout.readline, ''):
            logger.info(f"Migration {migration_id}: {line.strip()}")
            migrations[migration_id]["log"].append(line.strip())
        process.stdout.close()
        process.wait()
        if process.returncode == 0:
            migrations[migration_id]["status"] = "completed"
        else:
            migrations[migration_id]["status"] = "failed"
    except Exception as e:
        migrations[migration_id]["status"] = "error"
        migrations[migration_id]["log"].append(str(e))


def construct_command(data):
    command = [
        "imapsync",
        "--host1", data['src_host'],
        "--port1", str(data['src_port']),
        "--user1", data['src_user'],
        "--password1", os.environ['SRC_PASSWORD'],
        "--host2", data['dst_host'],
        "--port2", str(data['dst_port']),
        "--user2", data['dst_user'],
        "--password2", os.environ['DST_PASSWORD']
    ]
    if data.get('src_encryption') == 'ssl':
        command.append("--ssl1")
    elif data.get('src_encryption') == 'tls':
        command.append("--tls1")

    if data.get('dst_encryption') == 'ssl':
        command.append("--ssl2")
    elif data.get('dst_encryption') == 'tls':
        command.append("--tls2")

    return command


@app.route('/detect_ports', methods=['POST'])
def detect_ports():
    try:
        data = request.json
        src_host = data.get("src_host")
        dst_host = data.get("dst_host")

        if not src_host or not dst_host:
            return jsonify({"error": "Both src_host and dst_host are required"}), 400

        # Puertos comunes
        common_ports = {
            "non_ssl": 143,
            "ssl": 993
        }

        results = {}

        # Detectar puertos para el servidor de origen
        src_results = {}
        for key, port in common_ports.items():
            try:
                if key == "ssl":
                    server = imaplib.IMAP4_SSL(src_host, port)
                else:
                    server = imaplib.IMAP4(src_host, port)
                server.logout()
                src_results[key] = port
            except:
                src_results[key] = None

        results['src_non_ssl'] = src_results.get("non_ssl")
        results['src_ssl'] = src_results.get("ssl")

        # Detectar puertos para el servidor de destino
        dst_results = {}
        for key, port in common_ports.items():
            try:
                if key == "ssl":
                    server = imaplib.IMAP4_SSL(dst_host, port)
                else:
                    server = imaplib.IMAP4(dst_host, port)
                server.logout()
                dst_results[key] = port
            except:
                dst_results[key] = None

        results['dst_non_ssl'] = dst_results.get("non_ssl")
        results['dst_ssl'] = dst_results.get("ssl")

        return jsonify(results), 200

    except Exception as e:
        logger.exception("Error detecting ports")
        return jsonify({"error": "Failed to detect ports", "details": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, port=8181)
