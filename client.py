#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

        if not self.username or not self.password:
            return print("[-] Usuário ou senha estão vazios!")

        self.token = ""

        if len(sys.argv) == 2 and sys.argv[1] == "signup":
            if not self.signup():
                print("[-] Este nome de usuário já está em uso!")
                sys.exit(0)

        if not self.login():
            print("[-] Usuário ou senha incorretos!")
            sys.exit(0)

        self.run()

    def request(self, payload):
        try:
            headers = {
                "Authorization": self.token,
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://servidordomal.fun/api/mail",
                json=payload,
                headers=headers
            )
            return response.json().get('response', '')
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

    def login(self):
        try:
            response = requests.post(
                "https://servidordomal.fun/api/login",
                json={"username": self.username, "password": self.password}
            )
            if response.status_code == 200:
                self.token = response.json().get('response', '')
                return True
            return False
        except Exception as e:
            print(f"Erro ao fazer login: {e}")
            return False

    def signup(self):
        try:
            response = requests.post(
                "https://servidordomal.fun/api/signup",
                json={"username": self.username, "password": self.password}
            )
            if response.status_code == 200:
                self.token = response.json().get('response', '')
                return True
            return False
        except Exception as e:
            print(f"Erro ao registrar: {e}")
            return False

    def run(self):
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

                if not action:
                    continue

                elif action == "1":
                    print(self.request({"action": "read"}))

                elif action == "2":
                    print("[+] Enviar mensagem\n")
                    target = input("[+] Destinatário: ").strip()
                    message = input("[+] Mensagem: ").strip()

                    if not target or not message:
                        print("[-] Destinatário ou mensagem estão vazios!")
                    else:
                        print(self.request({"action": "send", "to": target, "content": message}))

                elif action == "3":
                    print(self.request({"action": "clear"}))

                elif action == "4":
                    print("[+] Enviar moedas\n")
                    target = input("[+] Destinatário: ").strip()
                    amount = input("[+] Quantidade: ").strip()

                    if not target or not amount:
                        print("[-] Destinatário ou quantidade estão vazios!")
                    else:
                        print(self.request({"action": "transfer", "to": target, "amount": amount}))

                elif action == "5":
                    user = input("[+] Nome do usuário para procurar: ").strip()
                    if not user:
                        print("[-] Nome de usuário não pode estar vazio!")
                    else:
                        print(self.request({"action": "search", "user": user}))

                elif action == "6":
                    print(self.request({"action": "me"}))

                elif action == "7":
                    print(self.request({"action": "coins"}))

                elif action == "8":
                    password = getpass.getpass("[+] Nova senha: ").strip()
                    if not password:
                        print("[-] A senha está vazia!")
                    else:
                        print(self.request({"action": "changepass", "newpass": password}))
                        self.password = password

                elif action == "9":
                    print(self.request({"action": "signoff"}))
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
