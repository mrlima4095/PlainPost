#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import socket
import getpass

HOST = '31.97.20.160'
PORT = 10142

USERNAME = input("User: ")
PASSWORD = input("Password: ")

    
    
class Client:
    def __init__(self):
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
        
        if not username or not password: return print("[-] Usuario ou senha estão vazios!")
        else: self.run()
    def request(self, payload)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
            
        s.sendall(payload.encode())
        return s.recv(4096).decode()
        
    def run(self):
        payload = 
        status = self.request(json.dumps())
        
        
