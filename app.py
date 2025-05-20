from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import json

app = Flask(__name__)
CORS(app)

TCP_HOST = '0.0.0.0'
TCP_PORT = 10142


@app.route(('/badmail'), methods=['POST'])
def badmail():
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload."}), 400

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", TCP_PORT))
            s.sendall((json.dumps(payload) + "\n").encode('utf-8'))
            response = s.recv(4096).decode('utf-8').strip()
    except Exception as e:
        response = "9"

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10143)