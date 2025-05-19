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
import sqlite3
import threading
import os
import json
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

        self.db = sqlite3.connect("mailserver.db", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                coins INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT,
                sender TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(recipient) REFERENCES users(username)
            )
        ''')
        self.db.commit()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"[+] Listening on port {self.port}")

            while True:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()

    def handle_client(self, client_socket, addr):
        request = json.loads(self.read(client_socket))

        if request['action'] == "signup":
            return self.send(client_socket, self.signup(request['username'], request['password']))

        if self.auth(request['username'], request['password']):
            action = request.get("action", "")
            if action == "send":
                self.send(client_socket, self.send_mail(request['username'], request['to'], request['content']))
            elif action == "read":
                self.send(client_socket, self.read_mail(request['username']))
            elif action == "clear":
                self.send(client_socket, self.clear(request['username']))
            else:
                self.send(client_socket, "2")
        else:
            self.send(client_socket, "1")

    def auth(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        return self.cursor.fetchone() is not None

    def signup(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            return "3"  # Usuário já existe

        self.cursor.execute("INSERT INTO users (username, password, coins) VALUES (?, ?, 0)", (username, password))
        self.db.commit()
        return "0"

    def send_mail(self, sender, target, content):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (target,))
        if self.cursor.fetchone() is None:
            return "4"  # Destinatário não encontrado

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        full_content = f"[{timestamp} - {sender}] {content}"
        self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)",
                            (target, sender, full_content, timestamp))
        self.db.commit()
        return "0"

    def read_mail(self, username):
        self.cursor.execute("SELECT content FROM mails WHERE recipient = ?", (username,))
        mails = [row["content"] for row in self.cursor.fetchall()]
        return '\n'.join(mails) if mails else "No messages"

    def clear(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.db.commit()
        return "0"

    def send(self, client_socket, text):
        client_socket.sendall(text.encode('utf-8'))

    def read(self, client_socket):
        return client_socket.recv(4095).decode('utf-8').strip()


if __name__ == '__main__':
    Server().start()