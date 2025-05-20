#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

TCP_HOST = '127.0.0.1'
TCP_PORT = 10142

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        print(f"[HTTP] Data: {post_data.decode(errors='ignore')}")

        try:
            with socket.create_connection((TCP_HOST, TCP_PORT)) as tcp_sock:
                tcp_sock.sendall(post_data)

                tcp_sock.settimeout(10)
                response = tcp_sock.recv(4096)
                print(f"[TCP] Resposta do servidor TCP: {response.decode(errors='ignore')}")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Erro ao conectar com TCP: {e}".encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

if __name__ == '__main__':
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, ProxyHandler)
    print("Servidor proxy HTTP rodando em http://localhost:8080")
    httpd.serve_forever()
