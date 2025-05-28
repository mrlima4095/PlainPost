#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import json
import psycopg2
from datetime import datetime

class AdminPanel:
    def __init__(self):
        with open("jwt.properties", "r") as f:
            config = json.load(f)

        self.db = psycopg2.connect(
            dbname=config['DB_NAME'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            host=config['DB_HOST'], 
            port=config['DB_PORT'],
        )
        self.cursor = self.db.cursor()

    def run(self, args=sys.argv):
        if len(args) < 2:
            self.help()
            sys.exit(0)

        try:
            if args[1] == "register": self.register(args[2], args[3])
            elif args[1] == "unregister": self.unregister(args[2])
            elif args[1] == "password": self.changepass(args[2], args[3])
            elif args[1] == "role": self.changerole(args[2], args[3])
            elif args[1] == "list": self.list_users()

            elif args[1] == "send": self.send(args[2], ' '.join(args[3:]))
            elif args[1] == "notifyall": self.notify_all(' '.join(args[2:]))
            elif args[1] == "read": self.list_all_mails()
            elif args[1] == "clear": self.clear(args[2])
            elif args[1] == "clear-all": self.clear_all()

            elif args[1] == "give-role": self.give_role(args[2], args[3])
            elif args[1] == "take-role": self.take_role(args[2], args[3])
            elif args[1] == "give-coin": self.give_coins(args[2], int(args[3]))
            elif args[1] == "take-coin": self.take_coins(args[2], int(args[3]))

            elif args[1] == "add-role": self.add_buyable_role(args[2], int(args[3]))
            elif args[1] == "remove-role": self.remove_buyable_role(args[2])
            elif args[1] == "list-roles": self.list_buyable_roles()

            elif args[1] == "help": self.help()

            else: print("[!] Invalid request.")
        except IndexError:
            print("[!] Missing arguments.")
        except Exception as e:
            print(f"[!] Error: {e}")

    def help(self):
        print("register,unregister,password,give-role,take-role,role,list,send,read,clear,clear-all,notifyall,give-coin,take-coin,add-role,remove-role,list-roles")

    # User payloads
    def register(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password, coins, role) VALUES (%s, %s, 0, 'user')", (username, password))
        self.db.commit()
        print(f"[+] User '{username}' created.")

    def unregister(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = %s", (username,))
        self.cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        self.db.commit()
        print(f"[-] User '{username}' deleted.")

    def changepass(self, username, newpass):
        self.cursor.execute("UPDATE users SET password = %s WHERE username = %s", (newpass, username))
        self.db.commit()
        print(f"[+] Password for '{username}' changed.")

    def changerole(self, username, role):
        self.cursor.execute("UPDATE users SET role = %s WHERE username = %s", (role, username))
        self.db.commit()
        print(f"[+] User '{username}' role changed to '{role}'.")

    def give_role(self, username, role):
        self.cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if not self.cursor.fetchone():
            print("[!] User not found.")
            return

        self.cursor.execute("SELECT 1 FROM user_roles WHERE username = %s AND role = %s", (username, role))
        if self.cursor.fetchone():
            print("[~] User already has this role.")
            return

        self.cursor.execute("INSERT INTO user_roles (username, role) VALUES (%s, %s)", (username, role))
        self.db.commit()
        print(f"[+] Role '{role}' granted to '{username}'.")

    def take_role(self, username, role):
        self.cursor.execute("DELETE FROM user_roles WHERE username = %s AND role = %s", (username, role))
        self.db.commit()
        print(f"[-] Role '{role}' removed from '{username}'.")

    def list_users(self):
        self.cursor.execute("SELECT username, role, coins FROM users")
        for row in self.cursor.fetchall():
            print(f"[{row[1]}] {row[0]} (Coins: {row[2]})")

    # Mails
    def send(self, target, content):
        self.cursor.execute("SELECT 1 FROM users WHERE username = %s", (target,))
        if not self.cursor.fetchone():
            print("[!] Target user does not exist.")
            return

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        full_content = f"[{timestamp} - admin] {content}"
        self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (%s, %s, %s, %s)", 
                            (target, "admin", full_content, timestamp))
        self.db.commit()
        print(f"[+] Email sent to {target}.")

    def notify_all(self, content):
        self.cursor.execute("SELECT username FROM users")
        users = self.cursor.fetchall()

        if not users:
            print("[~] No users to notify.")
            return

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        full_content = f"[{timestamp} - admin] {content}"

        for user in users:
            self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (%s, %s, %s, %s)", 
                                (user[0], "admin", full_content, timestamp))
        
        self.db.commit()
        print(f"[+] Notification sent to all users.")

    def list_all_mails(self):
        self.cursor.execute("SELECT recipient, content FROM mails")
        mails = self.cursor.fetchall()

        if len(sys.argv) >= 3:
            target = sys.argv[2]
            for mail in mails:
                if mail[0] == target:
                    print(mail[1])
        else:
            for mail in mails:
                print(f"At: {mail[0]} -> {mail[1]}")

    def clear(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = %s", (username,))
        self.db.commit()
        print(f"[~] Cleared all emails for '{username}'.")

    def clear_all(self):
        self.cursor.execute("DELETE FROM mails")
        self.db.commit()
        print("[~] All emails cleared from database.")

    # Shop
    def add_buyable_role(self, role, price):
        self.cursor.execute("SELECT 1 FROM roles WHERE role = %s", (role,))
        if self.cursor.fetchone():
            print("[~] This role is already in the store.")
            return

        self.cursor.execute("INSERT INTO roles (role, price) VALUES (%s, %s)", (role, price))
        self.db.commit()
        print(f"[+] Role '{role}' is now available for {price} coins.")

    def remove_buyable_role(self, role):
        self.cursor.execute("DELETE FROM roles WHERE role = %s", (role,))
        self.db.commit()
        print(f"[-] Role '{role}' removed from the store.")

    def list_buyable_roles(self):
        self.cursor.execute("SELECT role, price FROM roles")
        roles = self.cursor.fetchall()

        if not roles:
            print("[~] No roles available for purchase.")
            return

        print("[=] Roles available for purchase:")
        for row in roles:
            print(f"[+] {row[0]} - {row[1]} coins")

    # Coins
    def give_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = coins + %s WHERE username = %s", (amount, username))
        self.db.commit()
        print(f"[+] Added {amount} coins to '{username}'.")

    def take_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = GREATEST(coins - %s, 0) WHERE username = %s", (amount, username))
        self.db.commit()
        print(f"[-] Removed {amount} coins from '{username}'.")


if __name__ == '__main__':
    panel = AdminPanel()
    panel.run()
