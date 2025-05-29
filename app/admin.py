#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
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
            if args[1] == "register": panel.register(args[2], args[3])
            elif args[1] == "unregister": panel.unregister(args[2])
            elif args[1] == "password": panel.changepass(args[2], args[3])
            elif args[1] == "bio": panel.bio(args[2], ' '.join(args[3:]))
            elif args[1] == "list": panel.list_users()

            elif args[1] == "send": panel.send(args[2], ' '.join(args[3:]))
            elif args[1] == "notifyall": panel.notify_all(' '.join(args[2:]))
            elif args[1] == "read": panel.list_all_mails()
            elif args[1] == "clear": panel.clear(args[2])
            elif args[1] == "clear-all": panel.clear_all()

            elif args[1] == "give-coin": panel.give_coins(args[2], int(args[3]))
            elif args[1] == "take-coin": panel.take_coins(args[2], int(args[3]))

            elif args[1] == "help": self.help()

            else: print("[!] invalid request")
        except IndexError as e: print(f"[!] Missed arguments")
        except Exception as e: print(f"[!] Error: {e}")

    def help(self): print("register,unregister,password,bio,list,send,read,clear,clear-all,notifyall,give-coin,take-coin")

    # |
    # User credentials 
    def register(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password, coins, biography) VALUES (?, ?, 0, 'user')", (username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())))
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
                    print(mail['content'])

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
