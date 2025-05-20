#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import socket
import getpass

class Client:
    def __init__(self):
        self.username = input("Username: ").strip()
        self.password = getpass.getpass("Password: ").strip()
        
        if not self.username or not self.password: return print("[-] Usuario ou senha estão vazios!")
        else: self.run()
    def request(self, payload)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('31.97.20.160', 10142))
            
        s.sendall(payload.encode())
        return s.recv(4096).decode()
        
    def run(self):
        payload = {"username": self.username, "password": self.password, "action": "status"}
        status = self.request(json.dumps())

        if status == "1": return print("[-] Usuario ou senha incorretos!")
        else:
            while True:
                
        
        
