#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
import os
import sys
import json
import bcrypt
import shutil 
import sqlite3
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
# |
# |
# Settings
DB_PATH = "mailserver.db"
CONFIG_PATH = "server.json"
SAO_PAULO_TZ = "America/Sao_Paulo"
# |
# Main Class
class AdminPanel:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.fernet = Fernet(json.load(open(CONFIG_PATH, "r"))['FERNET_KEY'].encode())

    def run(self, args=sys.argv):
        if len(args) < 2: 
            self.help()
            sys.exit(0)
        cmd = args[1]

        try:
            match cmd:
                case "register": self.register(args[2], args[3])
                case "unregister": self.unregister(args[2])
                case "password": self.changepass(args[2], args[3])
                case "role": self.changerole(args[2], args[3])
                case "bio": self.changebio(args[2], ' '.join(args[3:]))
                case "list": self.list_users()

                case "send": self.send(args[2], ' '.join(args[3:]))
                case "notify-all": self.notify_all(' '.join(args[2:]))
                case "read": self.read(args[2] if len(args) > 2 else None)
                case "rm-msg": self.delete_message(args[2])
                case "clear": self.clear(args[2])
                case "clear-all": self.clear_all()

                case "give-coin": self.give_coins(args[2], int(args[3]))
                case "take-coin": self.take_coins(args[2], int(args[3]))

                case "block": self.block(args[2], args[3])
                case "unblock": self.unblock(args[2], args[3])
                case "list-blocks": self.list_spam_blocks(args[2])

                case "list-reports": self.list_reports()
                case "user-reports": self.user_reports(args[2])
                case "rm-report": self.delete_report(args[2])
                case "clear-reports": self.clear_user_reports(args[2])

                case "user": self.user_info(args[2])
                case "mural": self.view_mural(args[2])
                case "user-files": self.list_user_files(args[2])
                case "file-info": self.file_info(args[2])
                case "extend-file": self.extend_file(args[2])

                case "list-links": self.list_short_links(args[2])
                case "link-owner": self.link_owner(args[2])
                case "rm-link": self.delete_link(args[2])

                case "clear-agent": self.clear_ai(args[2])
                case "read-agent": self.read_ai(args[2])

                case "block-id": self.block_username(args[2])
                case "unblock-id": self.unblock_username(args[2])
                case "used-ids": self.list_blocked_usernames()

                case "help": self.help()
                case _: print("[!] Invalid command")
        except IndexError: print("[!] Missing arguments")
        except Exception as e: print(f"[!] Error: {e}")

    def help(self):
        print("Usage: python admin.py [OPTIONS] <username> ...")
        print("       python admin.py cmd - Interactive mode\n")
        print("OPTIONS:")
        print("    register  unregister  password  role  bio  list")
        print("    send  notify-all  read  rm-msg  clear  clear-all")
        print("    give-coin  take-coin")
        print("    block  unblock  list-blocks")
        print("    user  mural  user-files  file-info  extend-file")
        print("    list-links  link-owner  rm-link")
        print("    clear-agent  read-agent")
        print("    block-id  unblock-id  used-ids")

    # Users
    # | (Register an user)
    def register(self, username, password):
        hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.cursor.execute("INSERT INTO users (username, password, coins, role, biography, credentials_update) VALUES (?, ?, 0, 'user', 'A PlainPost user', datetime('now'))", (username, hash_pw))
        self.cursor.execute("INSERT OR IGNORE INTO used_usernames (username) VALUES (?)", (username,))
        self.db.commit()
        print(f"[+] User '{username}' registered.")
    # | (Unregister an user)
    def unregister(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.cursor.execute("DELETE FROM agents WHERE username = ?", (username,))
        self.cursor.execute("DELETE FROM short_links WHERE owner = ?", (username,))
        self.cursor.execute("SELECT saved_name FROM files WHERE owner = ?", (username,))
        for row in self.cursor.fetchall():
            try: os.remove(os.path.join("uploads", row["saved_name"]))
            except: pass
        self.cursor.execute("DELETE FROM files WHERE owner = ?", (username,))
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.db.commit()
        print(f"[-] User '{username}' deleted.")
    # | (Change user password)
    def changepass(self, username, newpass):
        self.cursor.execute("UPDATE users SET password = ?, credentials_update = datetime('now') WHERE username = ?", (bcrypt.hashpw(newpass.encode(), bcrypt.gensalt()), username))
        self.db.commit()
        print(f"[~] Password updated for '{username}'.")
    # | (Change user biography)
    def changebio(self, username, bio):
        self.cursor.execute("UPDATE users SET biography = ? WHERE username = ?", (bio, username))
        self.db.commit()
        print(f"[~] Biography updated for '{username}'.")
    # | (Change user role)
    def changerole(self, username, role):
        self.cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        self.db.commit()
        print(f"[~] Role updated for '{username}'.")
    # | (List all users)
    def list_users(self):
        self.cursor.execute("SELECT username, role, coins, biography, page FROM users")
        for row in self.cursor.fetchall():
            mural = "yes" if row["page"] else "no"
            print(f"[{row['role']}] {row['username']} ({row['coins']}): {row['biography']} | Mural: {mural}")
    # |
    # |
    # User information
    def user_info(self, username):
        self.cursor.execute("SELECT role, biography, coins, page FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        mural = "yes" if row["page"] else "no"
        print(f"[{row['role']}] {username} (Coins: {row['coins']}) - {row['biography']} | Mural: {mural}")
    # |
    # |
    # Reports Managing
    # | (Print all reports)
    def list_reports(self):
        root = "reports"
        if not os.path.exists(root):
            print("[!] No reports found."); return
        for user in os.listdir(root):
            for file in os.listdir(os.path.join(root, user)):
                with open(os.path.join(root, user, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"[{file.replace('.json','')}] {data['type']} > {data['target']} - by: {data['sender']}")
    # | (Print reports to a user)
    def user_reports(self, username):
        path = os.path.join("reports", username)
        if not os.path.exists(path):
            print("[!] No reports for this user."); return
        for file in os.listdir(path):
            with open(os.path.join(path, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[{file.replace('.json','')}] {data['type']} - by: {data['sender']}\n{data['description']}\n")
    # | (Delete a report)
    def delete_report(self, report_id):
        root = "reports"
        found = False
        for user in os.listdir(root):
            file_path = os.path.join(root, user, f"{report_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[-] Report {report_id} deleted.")
                found = True
                break
        if not found:
            print("[!] Report ID not found.")
    # | (Clear all reports for an user)
    def clear_user_reports(self, username):
        path = os.path.join("reports", username)
        if not os.path.exists(path):
            print("[!] No reports found for this user."); return
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))
        os.rmdir(path)
        print(f"[~] All reports for '{username}' have been deleted.")
    # | 
    # | 
    # Mails
    # | (Send a mail)
    def send(self, user, msg):
        self.cursor.execute("SELECT 1 FROM users WHERE username = ?", (user,))
        if not self.cursor.fetchone():
            print("[!] User not found."); return
        encrypted = self.fernet.encrypt(f"[{datetime.now().strftime("%H:%M %d/%m/%Y")} - admin] {msg}".encode()).decode()
        self.cursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", (user, "admin", encrypted, datetime.now().strftime("%H:%M %d/%m/%Y")))
        self.db.commit()
        print(f"[+] Sent to '{user}'.")
    # | (Send a mail for all users)
    def notify_all(self, msg):
        self.cursor.execute("SELECT username FROM users")
        users = [r["username"] for r in self.cursor.fetchall()]
        for user in users:
            self.send(user, msg)
    # | (Read mails)
    def read(self, username=None):
        if username:
            self.cursor.execute("SELECT id, content FROM mails WHERE recipient = ?", (username,))
            rows = self.cursor.fetchall()
            print(f"[+] Mensagens para {username}:\n")
        else:
            self.cursor.execute("SELECT id, recipient, content FROM mails")
            rows = self.cursor.fetchall()
            print("[+] Todas as mensagens:\n")

        for row in rows:
            content = self.fernet.decrypt(row["content"].encode()).decode()
            if username:
                print(f"[{row['id']}] {content}")
            else:
                print(f"[{row['id']}] {row['recipient']} → {content}")
    # | (Delete a mail from ID)
    def delete_message(self, msg_id):
        self.cursor.execute("DELETE FROM mails WHERE id = ?", (msg_id,))
        self.db.commit()
        print(f"[~] Deleted message ID {msg_id}.")
    # | (Clear all mails from an user)
    def clear(self, username):
        self.cursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        self.db.commit()
        print(f"[~] Cleared inbox for '{username}'.")
    # | (Clear all mails from DB)
    def clear_all(self):
        self.cursor.execute("DELETE FROM mails")
        self.db.commit()
        print("[~] Cleared all mail.")
    # |
    # |
    # Coins
    # | (Give coin for a user)
    def give_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = coins + ? WHERE username = ?", (amount, username))
        self.db.commit()
        print(f"[+] Gave {amount} coins to '{username}'.")
    # | (Take coin from a user)
    def take_coins(self, username, amount):
        self.cursor.execute("UPDATE users SET coins = MAX(coins - ?, 0) WHERE username = ?", (amount, username))
        self.db.commit()
        print(f"[~] Took {amount} coins from '{username}'.")
    # |
    # |
    # Spam box
    # | (Block)
    def block(self, user, target):
        self.cursor.execute("SELECT blocked_users FROM users WHERE username = ?", (user,))
        blocked = json.loads(self.cursor.fetchone()["blocked_users"])
        if target not in blocked:
            blocked.append(target)
            self.cursor.execute("UPDATE users SET blocked_users = ? WHERE username = ?", (json.dumps(blocked), user))
            self.db.commit()
        print(f"[+] '{target}' blocked by '{user}'.")
    # | (Unblock)
    def unblock(self, user, target):
        self.cursor.execute("SELECT blocked_users FROM users WHERE username = ?", (user,))
        blocked = json.loads(self.cursor.fetchone()["blocked_users"])
        if target in blocked:
            blocked.remove(target)
            self.cursor.execute("UPDATE users SET blocked_users = ? WHERE username = ?", (json.dumps(blocked), user))
            self.db.commit()
        print(f"[-] '{target}' unblocked by '{user}'.")
    # | (List user blocks)
    def list_spam_blocks(self, username):
        self.cursor.execute("SELECT blocked_users FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if row is None:
            print("[!] User not found."); return
        blocked = json.loads(row["blocked_users"])
        print(f"[+] Blocks from '{username}':\n")
        for user in blocked:
            print(f"- {user}")
    # |
    # |
    # Mural
    # | (Print user mural file)
    def view_mural(self, username):
        self.cursor.execute("SELECT page FROM users WHERE username = ?", (username,))
        page = self.cursor.fetchone()["page"]
        self.cursor.execute("SELECT saved_name FROM files WHERE id = ?", (page,))
        name = self.cursor.fetchone()["saved_name"]
        print(f"[+] mural = uploads/{name}")
    # | (Change user mural)
    def set_mural(self, username, file_id):
        self.cursor.execute("SELECT saved_name FROM files WHERE id = ? AND owner = ?", (file_id, username))
        row = self.cursor.fetchone()
        if not row:
            print("[!] File not found or not owned by user.")
            return
        self.cursor.execute("UPDATE users SET page = ? WHERE username = ?", (file_id, username))
        self.db.commit()
        print(f"[+] Mural set for '{username}' with file ID '{file_id}'.")
    # |
    # |
    # BinDrop
    # | (Print all files of a user)
    def list_user_files(self, username):
        self.cursor.execute("SELECT id, original_name FROM files WHERE owner = ?", (username,))
        for row in self.cursor.fetchall():
            print(f"{row['id']} - {row['original_name']}")
    # | (Print information for a file)
    def file_info(self, file_id):
        self.cursor.execute("SELECT owner, original_name FROM files WHERE id = ?", (file_id,))
        row = self.cursor.fetchone()
        print(f"Owner: {row['owner']}\nName: {row['original_name']}")
    # | (Extend duration of a file)
    def extend_file(self, file_id):
        self.cursor.execute("SELECT expire_time FROM files WHERE id = ?", (file_id,))
        expire = self.cursor.fetchone()["expire_time"]
        if not expire:
            print("This file does not expire."); return
        dt = datetime.fromisoformat(expire) + timedelta(hours=2)
        self.cursor.execute("UPDATE files SET expire_time = ? WHERE id = ?", (dt.isoformat(), file_id))
        self.db.commit()
        print(f"[~] Expiration extended to {dt}")
    # |
    # |
    # Short Links
    # | (Print all Short links)
    def list_short_links(self, username):
        self.cursor.execute("SELECT id, original_url FROM short_links WHERE owner = ?", (username,))
        for row in self.cursor.fetchall():
            print(f"{row['id']} -> {row['original_url']}")
    # | (Look for Short link owner)
    def link_owner(self, short_id):
        self.cursor.execute("SELECT owner FROM short_links WHERE id = ?", (short_id,))
        print(f"Owner: {self.cursor.fetchone()['owner']}")
    # | (Delete a Shot link)
    def delete_link(self, short_id):
        self.cursor.execute("DELETE FROM short_links WHERE id = ?", (short_id,))
        self.db.commit()
        print(f"[-] Link '{short_id}' deleted.")
    # |
    # |
    # I.A Control
    # | (Clear history of Agent for a user)
    def clear_ai(self, username):
        self.cursor.execute("DELETE FROM agents WHERE username = ?", (username,))
        self.db.commit()
        print(f"[~] History cleared for '{username}'.")
    # | (Read history of Agent from an user)
    def read_ai(self, username):
        self.cursor.execute("SELECT role, content FROM agents WHERE username = ?", (username,))
        for row in self.cursor.fetchall(): print(f"[{row['role']}] {row['content']}")
    # |
    # |
    # Control used usernames
    # | (Block)
    def block_username(self, username):
        self.cursor.execute("INSERT OR IGNORE INTO used_usernames (username) VALUES (?)", (username,))
        self.db.commit()
        print(f"[+] Username '{username}' added to used list.")
    # | (Unblock)
    def unblock_username(self, username):
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone(): return print("[!] User is registered")

        self.cursor.execute("DELETE FROM used_usernames WHERE username = ?", (username,))
        self.db.commit()
        print(f"[-] Username '{username}' removed from used list.")
    # | (Print used IDs)
    def list_blocked_usernames(self):
        self.cursor.execute("SELECT username FROM used_usernames")
        for row in self.cursor.fetchall(): print(f"{row['username']}")



if __name__ == "__main__":
    AdminPanel().run()
