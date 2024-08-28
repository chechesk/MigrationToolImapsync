import os
import subprocess
import uuid
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
import logging
from threading import Thread

app = Flask(__name__)

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Almacenamiento en memoria para los logs y el estado de las migraciones
migrations = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/migration_status', methods=['GET'])
def migration_status():
    return jsonify(migrations)

@app.route('/migrate', methods=['POST'])
def migrate():
    try:
        data = request.form.to_dict()
        migration_id = str(uuid.uuid4())  # Genera un ID único para la migración
        migrations[migration_id] = {"status": "in_progress", "log": []}

        # Guarda las contraseñas en las variables de entorno
        os.environ['SRC_PASSWORD'] = data['src_password']
        os.environ['DST_PASSWORD'] = data['dst_password']

        # Construye el comando imapsync
        command = construct_command(data)
        logger.info(f"Starting migration with ID {migration_id}: {command}")

        # Correr la migración en un hilo separado para no bloquear la respuesta
        thread = Thread(target=run_migration, args=(migration_id, command))
        thread.start()

        return jsonify({"migration_id": migration_id}), 202

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

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
        "--user1", data['src_user'],
        "--password1", os.environ['SRC_PASSWORD'],
        "--host2", data['dst_host'],
        "--user2", data['dst_user'],
        "--password2", os.environ['DST_PASSWORD']
    ]
    if data.get('src_use_ssl', False) in ['True', 'on']:
        command.append("--ssl1")
    if data.get('dst_use_ssl', False) in ['True', 'on']:
        command.append("--ssl2")
    return command

if __name__ == '__main__':
    app.run(debug=True)
