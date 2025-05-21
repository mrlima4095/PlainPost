#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import sqlite3
from datetime import datetime

class AdminPanel:
    def __init__(self):
        self.db = sqlite3.connect("mailserver.db")
        self.db.row_factory = sqlite3.Row 
        self.cursor = self.db.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def run(self, args=sys.argv):
        if len(args) < 2: self.help(); sys.exit(0)

        try:
            if args[1] == "register": panel.register(args[2], args[3])
            elif args[1] == "unregister": panel.unregister(args[2])
            elif args[1] ==  "password": panel.changepass(args[2], args[3])
            elif args[1] ==  "role": panel.changerole(args[2], args[3])
            elif args[1] ==  "bio": panel.changebio(args[2], args[3])
            elif args[1] ==  "list": panel.list_users()

            elif args[1] == "send": panel.send(args[2], ' '.join(args[3:]))
            elif args[1] ==  "read": panel.list_all_mails()
            elif args[1] ==  "clear": panel.clear(args[2])
            elif args[1] ==  "clear-all": panel.clear_all()

            elif args[1] ==  "give-coin": panel.give_coins(args[2], int(args[3]))
            elif args[1] ==  "take-coin": panel.take_coins(args[2], int(args[3]))

            elif args[1] == "help": self.help()

            else: print("[!] invalid request")
        except IndexError as e: print(f"[!] Missed arguments")
        except Exception as e: print(f"[!] Error: {e}")

    def help(self): print("register,unregister,password,role,list,send,read,clear,clear-all,give-coin,take-coin")

    # User payloads
    def register(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password, coins, role, bio) VALUES (?, ?, 0, 'user', 'A BadMail user')", (username, password))
        self.db.commit()
        print(f"[+] User '{username}' created.")
    def unregister(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.db.commit()
        print(f"[-] User '{username}' deleted.")
    def changepass(self, username, newpass):
        self.cursor.execute("UPDATE users SET password = ? WHERE username = ?", (newpass, username))
        self.db.commit()
        print(f"[+] Password for '{username}' changed.")
    def changerole(self, username, role):
        self.cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        self.db.commit()
        print(f"[+] User '{username}' role changed to '{role}'.")
    def changebio(self, username, content):
        self.cursor.execute("UPDATE users SET bio = ? WHERE username = ?", (content, username))
        self.db.commit()
        print(f"[+] Biography for '{username}' changed.")
    def list_users(self):
        self.cursor.execute("SELECT username, role, coins, biography FROM users")
        for row in self.cursor.fetchall():
            print(f"[{row['role']}] {row['username']} (Coins: {row['coins']}) - {row['biography']}")
        
    # Mails
    def send(self, target, content):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (target,))
        if not self.cursor.fetchone():
            print("[!] Target user does not exist.")
            return

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        full_content = f"[{timestamp} - admin] {content}"
        self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", 
                            (target, "admin", full_content, timestamp))
        self.db.commit()
        print(f"[+] Email sent to {target}.")
    def list_all_mails(self):
        self.cursor.execute("SELECT * FROM mails")
        for mail in self.cursor.fetchall():
            if len(sys.argv) >= 3:
                if sys.argv[2] == mail['recipient']:
                    print(mail['content'])

            else:  
                print(f"At: {mail['recipient']} -> {mail['content']}")
    def clear(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.db.commit()
        print(f"[~] Cleared all emails for '{username}'.")
    def clear_all(self):
        self.cursor.execute("DELETE FROM mails")
        self.db.commit()
        print("[~] All emails cleared from database.")
    
    # Coins
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
