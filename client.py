#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import sys
import json
import socket
import getpass

class Client:
    def __init__(self):
        self.username = input("Username: ").strip()
        self.password = getpass.getpass("Password: ").strip()
        
        if not self.username or not self.password: return print("[-] Usuario ou senha estão vazios!")
        else: self.run()
    def request(self, payload):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('31.97.20.160', 10142))
            
        s.sendall(payload.encode())
        return s.recv(4096).decode()
        
    def run(self):
        status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "status"}))

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

                if not action: slef.clear()
                elif action == "1": 
                    print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "read"})))
                    input("\n\n[!] Pressione ENTER para continuar..."), self.clear()
                elif action == "2":
                    self.clear(), print("[+] Enviar mensagem\n")
                    target = input("[+] Destinatario: ").strip()
                    message = input("[+] Mensagem: ").strip()

                    if not target or not message: print("[-] Destinatario ou mensagem estao vazios!"); continue

                    status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "send", "to": target, "content": message}))
                    if status == "0": input("[+] Mensagem enviada com sucesso!"), self.clear()
                    elif status == "4": input("[-] Destinatario inexistente!"), self.clear()
                elif action == "3": 
                    self.request(json.dumps({"username": self.username, "password": self.password, "action": "clear"}))
                    
                    print("[+] Suas mensagens foram apagadas!")
                    input("[+] Pressione ENTER para continuar..."), self.clear()
                elif action == "4":
                    self.clear(), print("[+] Enviar moedas\n")
                    target = input("[+] Destinatario: ").strip()
                    amount = input("[+] Quantidade: ").strip()

                    if not target or not message: print("[-] Destinatario ou quantidade estao vazios!"); continue

                    status = self.request(json.dumps({"username": self.username, "password": self.password, "action": "transfer", "to": target, "amount": amount}))
                    if status == "0": input("[+] Moedas enviadas com sucesso!"), self.clear()
                    elif status == "4": input("[-] Destinatario inexistente!"), self.clear()
                    elif status == "6": input("[-] Voce nao possui saldo suficiente!"), self.clear()
                elif action == "5": print(self.request(json.dumps({"username": self.username, "password": self.password, "action": "me"}))), input("[+] Pressione ENTER para continuar...") 
                
                self.clear()
            except KeyboardInterrupt: sys.exit(0)
        
    
    def clear(self):
        if os.name == "posix": os.system("clear")
        else: os.system("cls")
        

Client()