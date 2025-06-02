#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
import os
import requests

class Bot:
	def __init__(self, username, password):
		self.botname = username
		self.password = password
		self.token = None

	def start(self):
		try:
            headers = { "Content-Type": "application/json" }
            response = requests.post("https://servidordomal.fun/api/signup", json=payload, headers=headers)
            
            if response.status_code == 200: self.token = response.json().get('response', '')
            elif response.status_code == 409: 
            	try:
		            headers = { "Content-Type": "application/json" }
		            response = requests.post("https://servidordomal.fun/api/signup", json=payload, headers=headers)
		            
		            if response.status_code == 200: self.token = response.json().get('response', '')
		            elif response.status_code == 401: print("[-] Bad credentials!")
		        except Exception as e: return print(e) 
        except Exception as e: return print(e)

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
