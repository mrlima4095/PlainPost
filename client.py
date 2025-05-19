#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import socket
import sys

HOST = '127.0.0.1'
PORT = 10142

mensagem = ' '.join(sys.argv[1:])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(mensagem.encode())

    print(s.recv(4096).decode())
