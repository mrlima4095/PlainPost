from flask import Flask, request, jsonify
import socket
import json

app = Flask(__name__)

TCP_HOST = '0.0.0.0'
TCP_PORT = 10142

def communicate_with_tcp_server(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_HOST, TCP_PORT))
            s.sendall((json.dumps(payload) + "\n").encode('utf-8'))
            response = s.recv(4096).decode('utf-8').strip()
            return response
    except Exception as e:
        return str(e)

@app.route(('/badmail'), methods=['POST'])
def badmail():
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload."}), 400

    response = communicate_with_tcp_server(payload)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10143)