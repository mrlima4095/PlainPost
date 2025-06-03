#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
import os
import time
import random
import requests
import threading

class Bot:
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.token = None

		self.db = {}

	def start(self):
		try:
            headers = { "Content-Type": "application/json" }
            response = requests.post("https://servidordomal.fun/api/signup", json={"username": self.username, "password": self.password}, headers=headers)
            
            if response.status_code == 200: self.token = response.json().get('response', '')
            elif response.status_code == 409: 
            	try:
		            headers = { "Content-Type": "application/json" }
		            response = requests.post("https://servidordomal.fun/api/login", json={"username": self.username, "password": self.password}, headers=headers)
		            
		            if response.status_code == 200: self.token = response.json().get('response', '')
		            elif response.status_code == 401: print("[-] Bad credentials!")
        	except Exception as e: return print(f"[-] {e}")
        except Exception as e: return print(f"[-] {e}")

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
        except Exception as e: return print(f"[-] {e}")


    def StartGetUserProcess(self):
    	while True:
    		this = random.randint(100000, 999999)

    		if not this in self.db: break

    	def expire(that): del self.db[that]

    	thr = threading.Timer(300, expire, args=(this,))
    	thr.start()

    	self.db[this] = thr

    	print(f"[+] Waiting a user for Token {this}")

    def CheckUser(self):
    	messages = self.request({"action": "read"})

    	if not messages: return print("[-] Reading failed!")

    	messages = messages.split('\n')
    	for message in messages:
    		sender = message.split(']')[0].split('-')[1].strip()
    		content = message.split(']')[1].strip()

    		if content in self.db:
    			print(f"[+] Authorized {sender} from code: {content}")
    			self.db[content].cancel()
    			del self.db[content]



app = Bot()
app.StartGetUserProcess()



