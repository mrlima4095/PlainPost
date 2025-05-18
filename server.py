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

from datetime import datetime


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
        
        if self.request['action'] == "signup": return self.send(client_socket, self.signup(self.request['username'], self.request['password']))
        
        if self.auth(self.request['username'], self.request['password']):
            if self.request['action'] == "": return
            elif self.request['action'] == "send": self.send(client_socket, self.send_mail(self.request['username'], self.request['to'], self.request['content']))
            elif self.request['action'] == "read":
            elif self.request['action'] == "clear":
            elif self.request['action'] == "delete":
            elif self.request['action'] == "me":
            else: self.send(client_socket, "2")

        else: self.send(client_socket, "1")


    def auth(self, username, password):

        if os.path.exists(username):
            with open(username, "r") as file:
                user_data = json.load(file)
                
                if user_data['password'] == password: return True
                else: return False
        else: return False
    def singup(self, username, password):
        if os.path.exists(username): return "3"
        else:
            with open(username, "wt+") as file:
                user_data = {}
                
                user_data['username'] = username
                user_data['password'] = password
                user_data['coins'] = "0"
                user_data['mails'] = []
                
                json.dump(user_data, file, indent=4)
                
            return "0"

    def send_mail(self, sender, target, content):
        if os.path.exists(username): 
            with open(username, "r") as file:
                user_data = json.load(file)
                
                user_data['mails'].append(datetime.now().strftime(f"[%M:%H %d/%m/%Y - {sender}] {content}"))
            
            with open(username, "wt+") as file:
                json.dump(user_data, file, indent=4)
                
            return "0"
        else: return "4"
    def read_mail(self, username):
        with open(username, "r") as file:
            user_data = json.load(file)
            
            return '\n'.join(user_data['mails'])
            
    def send(self, client_socket, text): client_socket.sendall(text.encode('utf-8'))
    def read(self, client_socket): return client_socket.recv(4095).decode('utf-8').strip()

if __name__ == '__main__':
    Server().start()

