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
        else: 
            if len(sys.argv) == 2 and sys.argv[1] == "signup":
                status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "signup"})).strip()

                if status == "3": print("[-] Este nome de usuario ja esta em uso!"), sys.exit(0)
                
        self.run()

    def request(self, payload):
        if "--proxy" in sys.argv:
            try:
                response = requests.post("https://servidordomal.fun/api/mail", json=json.loads(payload))

                return response.json().get('response', '')
            except Exception as e:
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
                print("[+] Opções")
                print("[1] Ler mails     [5] Meus dados")
                print("[2] Enviar mails  [6] Trocar senha")
                print("[3] Limpar mails  [7] Apagar conta")
                print("[4] Enviar moedas [8] Sair")

                action = input("[+] ").strip()

                self.clear()

                if not action: continue 
                elif action == "1": print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "read"})).strip())
                elif action == "2":
                    print("[+] Enviar mensagem\n")
                    target = input("[+] Destinatario: ").strip()
                    message = input("[+] Mensagem: ").strip()

                    if not target or not message: print("[-] Destinatario ou mensagem estao vazios!")
                    else:

                        status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "send", "to": target, "content": message})).strip()
                        if status == "0": print("[+] Mensagem enviada com sucesso!")
                        elif status == "4": print("[-] Destinatario inexistente!")
                elif action == "3":
                    self.request(json.dumps({"username": self.username, "password": self.password, "action": "clear"}))

                    if status == "0": print("[+] Suas mensagens foram apagadas!")
                    else: print("[-] Ocorreu um erro ao apagar suas mensagens!")
                elif action == "4":
                    print("[+] Enviar moedas\n")
                    target = input("[+] Destinatario: ").strip()
                    amount = input("[+] Quantidade: ").strip()

                    if not target or not amount: print("[-] Destinatario ou quantidade estao vazios!")
                    else:
                        status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "transfer", "to": target, "amount": amount})).strip()

                        if status == "0": print("[+] Moedas enviadas com sucesso!")
                        elif status == "4": print("[-] Destinatario inexistente!")
                        elif status == "6": print("[-] Ocorreu um erro!")
                        elif status == "7": print("[-] Voce nao possui saldo suficiente!")
                elif action == "5": print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "me"})).strip())
                elif action == "6":
                    password = getpass.getpass("[+] New Password: ").strip()

                    if not password: 
                        print("[-] A senha esta vazia!")

                    if self.request(json.dumps({"username": self.username, "password": self.password, "action": "changepass","newpass":password})).strip() == "0":
                        print("[+] Senha alterada com sucesso!")
                        self.password = password
                elif action == "7": 
                    status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "signoff"})).strip()

                    if status == "0": print("[!] Sua conta foi deletada!"); break
                elif action == "8": break
                else: print("[-] Opção não existe!")

                input("[+] Pressione ENTER para continuar...")
                self.clear()

            except KeyboardInterrupt: sys.exit(0)


    def clear(self):
        if os.name == "posix": os.system("clear")
        else: os.system("cls")


Client()