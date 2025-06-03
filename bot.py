import os
import time
import random
import requests
import threading
import socket

class Bot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None
        self.db = {}
        self.lock = threading.Lock()  # proteção threads no db

    def start(self):
        try:
            headers = { "Content-Type": "application/json" }
            response = requests.post("https://servidordomal.fun/api/signup", json={"username": self.username, "password": self.password}, headers=headers)
            
            if response.status_code == 200: 
                self.token = response.json().get('response', '')
            elif response.status_code == 409: 
                try:
                    headers = { "Content-Type": "application/json" }
                    response = requests.post("https://servidordomal.fun/api/login", json={"username": self.username, "password": self.password}, headers=headers)
                    
                    if response.status_code == 200: 
                        self.token = response.json().get('response', '')
                    elif response.status_code == 401: 
                        print("[-] Bad credentials!")
                except Exception as e: 
                    return print(f"[-] {e}")
        except Exception as e: 
            return print(f"[-] {e}")

    def request(self, payload):
        try:
            headers = { "Authorization": self.token, "Content-Type": "application/json" }
            response = requests.post("https://servidordomal.fun/api/mail", json=payload, headers=headers )
            return response.json().get('response', '')
        except Exception as e: 
            return print(f"[-] {e}")

    def generate_code(self):
        while True:
            code = random.randint(100000, 999999)
            with self.lock:
                if str(code) not in self.db:
                    # Expira o código em 5 minutos
                    def expire(c=code): 
                        with self.lock:
                            if str(c) in self.db:
                                del self.db[str(c)]
                                print(f"[-] Code expired: {c}")

                    timer = threading.Timer(300, expire)
                    timer.start()

                    self.db[str(code)] = timer
                    print(f"[+] Generated code: {code}")
                    return str(code)

    def CheckUser(self):
        messages = self.request({"action": "read"})

        if not messages:
            print("[-] Reading failed!")
            return

        messages = messages.split('\n')
        for message in messages:
            try:
                sender = message.split(']')[0]
                sender = sender.split('-')[1].strip()
                content = message.split(']')[1].strip()
            except IndexError:
                continue

            with self.lock:
                if content in self.db:
                    print(f"[+] {sender} -> {content}")
                    self.db[content].cancel()
                    del self.db[content]

        thr = threading.Timer(10, self.CheckUser)
        thr.start()

    def socket_server(self, host='127.0.0.1', port=10142):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(31522)
        print(f"[+] Listening on {port}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        with conn:
            print(f"[+] Connection from {addr}")
            try:
                data = conn.recv(1024).decode().strip().lower()

                if data == "gen":
                    code = self.generate_code()
                    conn.sendall(code.encode())
                elif data == "check":
                    threading.Thread(target=self.CheckUser, daemon=True).start()
                    conn.sendall(b"Check triggered")
                else:
                    conn.sendall(b"Invalid command")
            except Exception as e:
                print(f"[-] Error handling client {addr}: {e}")
app = Bot("","")
app.start()
app.CheckUser()

threading.Thread(target=app.socket_server, daemon=True).start()


while True:
    time.sleep(1)