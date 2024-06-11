import os
import subprocess
from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__)

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Assuming index.html exists with appropriate form

def validate_input(data):
    required_fields = ['src_host', 'src_user', 'src_password', 'dst_host', 'dst_user', 'dst_password']
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f"{field.replace('_', ' ').capitalize()} is required.")

def construct_command(data):
    command = [
        "imapsync",
        "--host1", data['src_host'],
        "--user1", data['src_user'],
        "--password1", os.environ['SRC_PASSWORD'],  # Using environment variables for passwords
        "--host2", data['dst_host'],
        "--user2", data['dst_user'],
        "--password2", os.environ['DST_PASSWORD']  # Using environment variables for passwords
    ]
    if data.get('src_use_ssl', False) in ['True', 'on']:
        command.append("--ssl1")
    if data.get('dst_use_ssl', False) in ['True', 'on']:
        command.append("--ssl2")
    return command

def execute_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

@app.route('/migrate', methods=['POST'])
def migrate():
    try:
        data = request.form.to_dict()
        validate_input(data)

        # Set environment variables for passwords
        os.environ['SRC_PASSWORD'] = data['src_password']
        os.environ['DST_PASSWORD'] = data['dst_password']

        command = construct_command(data)
        logger.info(f"Executing command: {command}")
        returncode, stdout, stderr = execute_command(command)

        if returncode == 0:
            logger.info("Migration completed successfully.")
            return jsonify({"message": "Migration completed successfully.", "output": stdout})
        else:
            logger.error(f"Migration failed: {stderr}")
            return jsonify({"error": "Migration failed", "details": stderr}), 500

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.exception("Unexpected error during migration")
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
