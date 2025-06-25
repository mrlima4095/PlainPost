import os
import time
import random
import requests
import threading
import socket
import json

class Bot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None
        self.db = {}
        self.used = {} 
        self.lock = threading.Lock()

    def start(self):
        try:
            headers = { "Content-Type": "application/json" }
            response = requests.post("https://archsource.xyz/api/signup", json={"username": self.username, "password": self.password}, headers=headers)
            
            if response.status_code == 200: 
                self.token = response.json().get('response', '')
            elif response.status_code == 409: 
                response = requests.post("https://archsource.xyz/api/login", json={"username": self.username, "password": self.password}, headers=headers)
                if response.status_code == 200: 
                    self.token = response.json().get('response', '')
                elif response.status_code == 401: return print("[-] Bad credentials!")
        except Exception as e: return print(f"[-] {e}")

        print("[+] Bot online")

    def request(self, payload):
        try:
            headers = { "Authorization": self.token, "Content-Type": "application/json" }
            response = requests.post("https://archsource.xyz/api/mail", json=payload, headers=headers )
            return response.json().get('response', '')
        except Exception as e: 
            print(f"[-] {e}")
            return ''

    def generate_code(self):
        while True:
            code = random.randint(100000, 999999)
            with self.lock:
                if str(code) not in self.db:
                    def expire(c=code): 
                        with self.lock:
                            if str(c) in self.db:
                                del self.db[str(c)]
                                print(f"[-] Code expired: {c}")

                    timer = threading.Timer(300, expire)
                    timer.start()

                    self.db[str(code)] = {"timer": timer, "user": None}
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
                sender = message.split(']')[0].split('-')[1].strip()
                content = message.split(']')[1].strip()
            except IndexError:
                continue

            with self.lock:
                if content in self.db:
                    print(f"[+] {sender} -> {content}")
                    self.db[content]["timer"].cancel()
                    self.db[content]["user"] = sender
                    self.used[content] = sender
                    del self.db[content]

        threading.Timer(10, self.CheckUser).start()

    def socket_server(self, host='127.0.0.1', port=10142):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(20)
        print(f"[+] Listening on {port}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        with conn:
            try:
                data = conn.recv(1024).decode().strip().lower()

                if data == "gen":
                    code = self.generate_code()
                    conn.sendall(code.encode())

                elif data.startswith("check"):
                    parts = data.split() 
                    if len(parts) == 2 and parts[1].isdigit():
                        code = parts[1]
                        with self.lock:
                            if code in self.used:
                                user = self.used.pop(code)
                                response = json.dumps({"token": user})
                                conn.sendall(response.encode())
                            else: conn.sendall(b"null")
                    else: conn.sendall(b"Usage: check <code>")
                else: conn.sendall(b"Invalid command")

            except Exception as e:
                print(f"[-] Error handling client {addr}: {e}")

app = Bot("Bot", "BOTKEY")
app.start()
app.CheckUser()

threading.Thread(target=app.socket_server, daemon=True).start()

while True: time.sleep(1)
