#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import socket

HOST = '127.0.0.1'
PORT = 10142



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        try: 
            mensagem = input("");
            s.sendall(mensagem.encode())

            print(s.recv(4096).decode())
