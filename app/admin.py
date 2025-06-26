#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
import os
import sys
import json
import bcrypt
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
# |
# Main Class
class AdminPanel:
    def __init__(self):
        self.db = sqlite3.connect("mailserver.db")
        self.db.row_factory = sqlite3.Row 
        self.cursor = self.db.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.fernet = Fernet(json.load(open("server.json", "r"))['FERNET_KEY'].encode())
    # |
    # Run command
    def run(self, args=sys.argv):
        if len(args) < 2: self.help(); sys.exit(0)

        try:
            if args[1] == "register": self.register(args[2], args[3])
            elif args[1] == "unregister": self.unregister(args[2])
            elif args[1] == "password": self.changepass(args[2], args[3])
            elif args[1] == "role": self.changerole(args[2], args[3])
            elif args[1] == "bio": self.changebio(args[2], ' '.join(args[3:]))
            elif args[1] == "list": self.list_users()

            elif args[1] == "send": self.send(args[2], ' '.join(args[3:]))
            elif args[1] == "notifyall": self.notify_all(' '.join(args[2:]))
            elif args[1] == "read": self.list_all_mails()
            elif args[1] == "clear": self.clear(args[2])
            elif args[1] == "clear-all": self.clear_all()

            elif args[1] == "give-coin": self.give_coins(args[2], int(args[3]))
            elif args[1] == "take-coin": self.take_coins(args[2], int(args[3]))

            elif args[1] == "help": self.help()
            elif args[1] == "cmd": self.cmd()

            else: print("[!] invalid request")
        except IndexError as e: print(f"[!] Missed arguments")
        except Exception as e: print(f"[!] Error: {e}")
    # |
    # Interactive Mode
    def chat(self):
        print("[+] Admin Panel\n[+]")
        print("[1] Register         [7] Send mail (as admin)    [c] Exit")
        print("[2] Unregister       [8] Notify all")
        print("[3] Change passowrd  [9] Read messages")
        print("[4] Change role      [0] Clear user inbox")
        print("[5] Change biography [a] Give coins")
        print("[6] List users       [b] Take coins\n[+]")
    def cmd(self):
        while True:
            try:
                self.cleartty(); self.chat()
                cmd = input("[+] ").strip()

                if cmd == "1":
                    username = input("[+] Username: ").strip()
                    password = input("[+] Password: ").strip()

                    self.register(username, password)
                elif cmd == "2":
                    username = input("[+] Username: ").strip()

                    self.unregister(username)
                elif cmd == "3":
                    username = input("[+] Username: ").strip()
                    password = input("[+] Password: ").strip()

                    self.changepass(username, password)
                elif cmd == "4":
                    username = input("[+] Username: ").strip()
                    role = input("[+] Role: ").strip()

                    self.changerole(username, role)
                elif cmd == "5":
                    username = input("[+] Username: ").strip()
                    biography = input("[+] Biography: ").strip()

                    self.changebio(username, biography)
                elif cmd == "6": self.cleartty(); self.list_users()
                elif cmd == "7":
                    username = input("[+] Username: ").strip()
                    message = input("[+] Message: ").strip()

                    self.send(username, message)
                elif cmd == "8":
                    message = input("[+] Message: ").strip()

                    self.notify_all(message)
                elif cmd == "9":
                    username = input("[+] Username: ").strip()

                    self.read(username, password)
                elif cmd == "0":
                    username = input("[+] Username: ").strip()

                    self.clear(username)
                elif cmd == "a":
                    username = input("[+] Username: ").strip()
                    amount = input("[+] Amount: ").strip()

                    self.give_coins(username, amount)
                elif cmd == "b":
                    username = input("[+] Username: ").strip()
                    amount = input("[+] Amount: ").strip()

                    self.take_coins(username, amount)
                elif cmd == "c": os.exit()
                else: print("[-] Unknown option!")

                input("\n[+] Press ENTER to continue...")

            except KeyboardInterrupt: break
    def cleartty(self): os.system("cls" if os.name == "nt" else "clear")
    # |
    def help(self): print("cmd,register,unregister,password,bio,list,send,read,clear,clear-all,notifyall,give-coin,take-coin")
    # |
    # |
    # User credentials 
    def register(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password, coins, role, biography) VALUES (?, ?, 0, 'user', 'A PlainPost user')", (username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())))
        self.db.commit()

        print(f"[+] User '{username}' created.")
    def unregister(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.db.commit()

        print(f"[-] User '{username}' deleted.")
    def changepass(self, username, newpass):
        self.cursor.execute("UPDATE users SET password = ? WHERE username = ?", (bcrypt.hashpw(newpass.encode('utf-8'), bcrypt.gensalt()), username))
        self.db.commit()

        print(f"[+] Password for '{username}' changed.")
    def changebio(self, username, bio):
        self.cursor.execute("UPDATE users SET biography = ? WHERE username = ?", (bio, username))
        self.db.commit()
        
        print(f"[+] User '{username}' bio changed to '{bio}'.")
    def changerole(self, username, role):
        self.cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        self.db.commit()
        
        print(f"[+] User '{username}' role changed to '{role}'.")
    # |
    # View all users
    def list_users(self):
        self.cursor.execute("SELECT username, biography, coins FROM users")
        for row in self.cursor.fetchall():
            print(f"[+] {row['username']} (Coins: {row['coins']}) - {row['biography']}")
    # |
    # Mails Tools
    def send(self, target, content):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (target,))
        if not self.cursor.fetchone():
            print("[!] Target user does not exist.")
            return

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        content = self.fernet.encrypt(f"[{timestamp} - admin] {content}".encode()).decode('utf-8')
        self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", 
                            (target, "admin", content, timestamp))
        self.db.commit()
        print(f"[+] Email sent to {target}.")
    def notify_all(self, content):
        self.cursor.execute("SELECT username FROM users")
        users = self.cursor.fetchall()

        if not users:
            print("[~] No users to notify.")
            return

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        content = self.fernet.encrypt(f"[{timestamp} - admin] {content}".encode()).decode('utf-8')

        for user in users:
            self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", 
                                (user['username'], "admin", content, timestamp))
        
        self.db.commit() 
        print(f"[+] Notification sent to all users.")
    def list_all_mails(self):
        self.cursor.execute("SELECT * FROM mails")
        for mail in self.cursor.fetchall():
            if len(sys.argv) >= 3:
                if sys.argv[2] == mail['recipient']:
                    print(self.fernet.decrypt(mail['content'].encode('utf-8')).decode())

            else:
                print(f"At: {mail['recipient']} -> {self.fernet.decrypt(mail['content'].encode('utf-8')).decode()}")
    def clear(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.db.commit()
        print(f"[~] Cleared all emails for '{username}'.")
    def clear_all(self):
        self.cursor.execute("DELETE FROM mails")
        self.db.commit()
        print("[~] All emails cleared from database.")
    # |
    # Coins API
    def give_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = coins + ? WHERE username = ?", (amount, username))
        self.db.commit()
        print(f"[+] Added {amount} coins to '{username}'.")
    def take_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = MAX(coins - ?, 0) WHERE username = ?", (amount, username))
        self.db.commit()
        print(f"[-] Removed {amount} coins from '{username}'.")

if __name__ == '__main__':
    panel = AdminPanel()
    panel.run()
