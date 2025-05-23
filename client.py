#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import sys
import json
import socket
import getpass
import requests

class Client:
    def __init__(self):
        self.username = input("Username: ").strip()
        self.password = getpass.getpass("Password: ").strip()

        if not self.username or not self.password: return print("[-] Usuario ou senha estão vazios!")

        if len(sys.argv) == 2 and sys.argv[1] == "signup":
            status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "signup"})).strip()
            if status == "3":
                print("[-] Este nome de usuario ja esta em uso!")
                sys.exit(0)

        self.run()

    def request(self, payload):
        if "--proxy" in sys.argv:
            try:
                response = requests.post("https://servidordomal.fun/api/mail", json=json.loads(payload))
                return response.json().get('response', '')
            except Exception:
                return "9"

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('31.97.20.160', 10142))
        s.sendall(payload.encode())
        return s.recv(4096).decode()

    def run(self):
        status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "status"})).strip()

        if status == "1": return print("\n[-] Usuario ou senha incorretos!")

        print(f"\n[+] Você entrou como {self.username}")
        while True:
            try:
                print("\n[+] Opções")
                print("[1] Ler mensagens     [6] Meus dados")
                print("[2] Enviar mensagem   [7] Meu saldo")
                print("[3] Limpar mensagens  [8] Trocar senha")
                print("[4] Enviar moedas     [9] Apagar conta")
                print("[5] Procurar usuário  [10] Sair")

                action = input("[+] ").strip()
                self.clear()

                if not action: continue

                elif action == "1": print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "read"})).strip())
                elif action == "2":
                    print("[+] Enviar mensagem\n")
                    target = input("[+] Destinatário: ").strip()
                    message = input("[+] Mensagem: ").strip()

                    if not target or not message: print("[-] Destinatário ou mensagem estão vazios!")
                    else:
                        status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "send", "to": target, "content": message})).strip()

                        if status == "0": print("[+] Mensagem enviada com sucesso!")
                        elif status == "4": print("[-] Destinatário inexistente!")
                elif action == "3":
                    status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "clear"})).strip()
                    
                    if status == "0": print("[+] Suas mensagens foram apagadas!")
                    else: print("[-] Ocorreu um erro ao apagar suas mensagens!")
                elif action == "4":
                    print("[+] Enviar moedas\n")
                    target = input("[+] Destinatário: ").strip()
                    amount = input("[+] Quantidade: ").strip()

                    if not target or not amount: print("[-] Destinatário ou quantidade estão vazios!")
                    else: 
                        status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "transfer", "to": target, "amount": amount})).strip()

                        if status == "0": print("[+] Moedas enviadas com sucesso!")
                        elif status == "4": print("[-] Destinatário inexistente!")
                        elif status == "6": print("[-] Quantidade inválida!")
                        elif status == "7": print("[-] Saldo insuficiente!")
                elif action == "5": 
                    user = input("[+] Nome do usuário para procurar: ").strip()
                    if not user: print("[-] Nome de usuário não pode estar vazio!")
                    else: 
                        result = self.request(json.dumps({"username": self.username, "password": self.password, "action": "search", "user": user})).strip()

                        if result == "4": print("[-] Usuário não encontrado!")
                        else: print(f"[+] {result}")
                elif action == "6": print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "me"})).strip())
                elif action == "7": print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "coins"})).strip())
                elif action == "8":
                    password = getpass.getpass("[+] Nova senha: ").strip()
                    if not password:
                        print("[-] A senha está vazia!")
                    else:
                        if self.request(json.dumps({"username": self.username, "password": self.password, "action": "changepass", "newpass": password})).strip() == "0":
                            print("[+] Senha alterada com sucesso!")
                            self.password = password

                elif action == "9":
                    status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "signoff"})).strip()
                    if status == "0":
                        print("[!] Sua conta foi deletada!")
                        break

                elif action == "10":
                    print("[+] Saindo...")
                    break

            except KeyboardInterrupt:
                print("\n[+] Encerrado pelo usuário.")
                sys.exit(0)

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

if __name__ == "__main__":
    Client()
