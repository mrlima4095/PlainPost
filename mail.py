#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import socket
import sqlite3
import threading
import os
import json
from datetime import datetime


class Server:
    def __init__(self):

        self.host = "0.0.0.0"
        self.port = 10142

        self.db = sqlite3.connect("mailserver.db", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                coins INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT,
                sender TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(recipient) REFERENCES users(username)
            )
        """)
        self.db.commit()

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
        try: 
            raw = self.read(client_socket)
            request = json.loads(raw)
        except json.decoder.JSONDecodeError: return self.send(client_socket, "5")

        if not 'action' in request:
            return self.send(client_socket, "5")

        if request['action'] == "signup":
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (request['username'],))
            if self.cursor.fetchone():
                return self.send(client_socket, "3")

            self.cursor.execute("INSERT INTO users (username, password, coins, role) VALUES (?, ?, 0, 'user')", (request['username'], request['password']))
            self.db.commit()
            return self.send(client_socket, "0")

        if self.auth(request):            
            print(datetime.now().strftime(f"[+] [%H:%M %d/%m/%Y - {request['username']}] {addr[0]} -> {raw}"))
                
            if request['action'] == "send":
                status = self.send_mail(request['username'], request['to'], request['content'])

                self.send(client_socket, status)
            elif request['action'] == "read":
                status = self.read_mail(request['username'])

                self.send(client_socket, status)
            elif request['action'] == "clear": 
                status = self.clear(request['username'])

                self.send(client_socket, status)
            elif request['action'] == "transfer":
                status = self.transfer_coins(request['username'], request['to'], request['amount'])

                self.send(client_socket, status)
            elif request['action'] == "changepass":
                status = self.change_password(request['username'], request['newpass'])

                self.send(client_socket, status)
            elif request['action'] == "me":
                status = self.show_info(request['username'])

                self.send(client_socket, status)
            elif request['action'] == "coins": 
                status = self.show_coins(request['username'])

                self.send(client_socket, status)
            elif request['action'] == "helpadm":
                status = self.send_mail(request['username'], "admin", request['content'])

                self.send(client_socket, status)
            elif request['action'] == "signoff": 
                status = self.signoff(request['username'])

                self.send(client_socket, status)
            elif request['action'] == "status": self.send(client_socket, "0")
            else: self.send(client_socket, "2")
        else: self.send(client_socket, "1") 

        client_socket.close()

    def auth(self, request):
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (request['username'], request['password']))
        return self.cursor.fetchone() is not None

    def show_info(self, username):
        self.cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if row: return f"[{row['role']}] {username}"
        else: return "4"
    def show_coins(self, username):
        self.cursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if row: return row['coins']
        else: return "4"

    # User auth tools
    def signoff(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.db.commit()
        return "0"
    def change_password(self, username, newpass):
        if not newpass:
            return "8"

        self.cursor.execute("UPDATE users SET password = ? WHERE username = ?", (newpass, username))
        self.db.commit()
        return "0"


    # Mail Tools
    def send_mail(self, sender, target, content):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (target,))
        if self.cursor.fetchone() is None:
            return "4"

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

    def transfer_coins(self, sender, recipient, amount):
        try:
            amount = int(amount)
            if amount <= 0:
                return "6"
        except ValueError:
            return "6"

        self.cursor.execute("SELECT coins FROM users WHERE username = ?", (recipient,))
        recipient_row = self.cursor.fetchone()
        if recipient_row is None:
            return "4"

        self.cursor.execute("SELECT coins FROM users WHERE username = ?", (sender,))
        sender_row = self.cursor.fetchone()
        if sender_row["coins"] < amount:
            return "7"

        self.cursor.execute("UPDATE users SET coins = coins - ? WHERE username = ?", (amount, sender))
        self.cursor.execute("UPDATE users SET coins = coins + ? WHERE username = ?", (amount, recipient))
        self.db.commit()
        
        return "0"

    
    # Socket Operations (Read and Write)
    def send(self, client_socket, text): client_socket.sendall(f"{text}\n".encode('utf-8'))
    def read(self, client_socket): return client_socket.recv(4095).decode('utf-8').strip()


if __name__ == '__main__':
    Server().start()
