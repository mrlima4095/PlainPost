#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import socket
import subprocess
import threading
import os

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
        self.send(client_socket, "Password:\n")

        passwd = 
        if passwd != self.config['passwd']: 
            self.send(client_socket, "Wrong Password!\n")
            client_socket.close(); print(f"[-] {addr[0]} - bad login")

            return

        print(f"[+] {addr[0]} connected")

        try:
            while True:
                command = client_socket.recv(4096).decode('utf-8').strip()
                if not command:
                    print(f"[-] {addr[0]} disconnected")
                    break

                self.send(client_socket, self.execute_command(command))

        except Exception as e:
            print(f"[-] {addr[0]} -- {e}")

        finally:
            client_socket.close()

    def execute_command(self, command):
        try: return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e: return e.output.decode('utf-8')

    def send(self, client_socket, text): client_socket.sendall(text.encode('utf-8'))
    def read(self, client_socket): return client_socket.recv(4095).decode('utf-8').strip()

if __name__ == '__main__':
    Server().start()
