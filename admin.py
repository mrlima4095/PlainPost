#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import sqlite3
from datetime import datetime

class AdminPanel:
    def __init__(self):
        self.db = sqlite3.connect("mailserver.db")
        self.db.row_factory = sqlite3.Row 
        self.cursor = self.db.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    # Users
    def create_user(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password, coins, role) VALUES (?, ?, 0, 'user')", (username, password))
        self.db.commit()
        print(f"[+] User '{username}' created.")
    def delete_user(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.db.commit()
        print(f"[-] User '{username}' deleted.")
    def change_password(self, username, newpass):
        self.cursor.execute("UPDATE users SET password = ? WHERE username = ?", (newpass, username))
        self.db.commit()
        print(f"[+] Password for '{username}' changed.")
    def change_role(self, username, role):
        self.cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        self.db.commit()
        print(f"[+] User '{username}' role changed to '{role}'.")
        
    # Mails
    def send_mail(self, target, content):
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
    def clear_user_mail(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.db.commit()
        print(f"[~] Cleared all emails for '{username}'.")
    def clear_all_mail(self):
        self.cursor.execute("DELETE FROM mails")
        self.db.commit()
        print("[~] All emails cleared from database.")

    
    def list_users(self):
        self.cursor.execute("SELECT username, role, coins FROM users")
        for row in self.cursor.fetchall():
            print(f"- {row['username']} (role={row['role']}, coins={row['coins']})")

    def list_all_mails(self):
        self.cursor.execute("SELECT * FROM mails")
        for mail in self.cursor.fetchall():
            print(f"{mail['recipient']} -> {mail['content']}\n")

    
    # Coins
    def add_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = coins + ? WHERE username = ?", (amount, username))
        self.db.commit()
        print(f"[+] Added {amount} coins to '{username}'.")
    def remove_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = MAX(coins - ?, 0) WHERE username = ?", (amount, username))
        self.db.commit()
        print(f"[-] Removed {amount} coins from '{username}'.")

if __name__ == '__main__':
    panel = AdminPanel()
    args = sys.argv

    if len(args) < 2:
        sys.exit(0)

    try:
        if args[1] == "create": panel.create_user(args[2], args[3])
        elif args[1] == "delete": panel.delete_user(args[2])
        elif args[1] == "send": panel.send_mail(args[2], ' '.join(args[3:]))
        elif args[1] ==  "clear-user": panel.clear_user_mail(args[2])
        elif args[1] ==  "clear-all": panel.clear_all_mail()
        elif args[1] ==  "role": panel.change_role(args[2], args[3])
        elif args[1] ==  "list-users": panel.list_users()
        elif args[1] ==  "list-mails": panel.list_all_mails()
        elif args[1] ==  "password": panel.change_password(args[2], args[3])
        elif args[1] ==  "add-coins": panel.add_coins(args[2], int(args[3]))
        elif args[1] ==  "remove-coins": panel.remove_coins(args[2], int(args[3]))
        else: print("[-] invalid request")
    except Exception as e:
        print(f"[!] Error: {e}")