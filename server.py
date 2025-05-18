#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Criar contas
# Requisições de API
# | Ver meus dados
# | Mudar senha
# | Enviar email
# | Ler emails
# | Deletar emails
# | Deletar todos emails
# | Apagar conta

import sys
import socket
import subprocess
import threading
import os, json

class Server:
    def __init__(self):
        self.config = {}

        with open("server.properties", "r") as file:
            for line in file.readlines():
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    self.config[key.strip()] = value.strip()

        self.host = self.config['host']
        self.port = int(self.config['port'])

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(31522)
            print(f"[+] Listening on port {self.port}")

            while True:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()

    def handle_client(self, client_socket, addr):
        self.request = json.loads(self.read(client_socket))

        if self.auth(self.request['user'], self.request['password']):


        else: self.send(client_socket, "Login failed!")


    def auth(self, username, password):

        if os.path.exists(username):
            with open() as user_data:
        else:
            return False



    def send(self, client_socket, text): client_socket.sendall(text.encode('utf-8'))
    def read(self, client_socket): return client_socket.recv(4095).decode('utf-8').strip()

if __name__ == '__main__':
    Server().start()
