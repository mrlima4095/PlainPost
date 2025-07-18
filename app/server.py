#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
# | (Flask)
from flask import Flask, request, jsonify, send_from_directory, make_response, render_template
from flask_cors import CORS
from flask import send_file
# | (SMTP Proxy)
from aiosmtpd.controller import Controller
from email import message_from_bytes
import asyncio
# |
import smtplib
from email.mime.text import MIMEText
# | (Others) 
import jwt
import time
import json
import uuid
import flask
import os, re
import socket
import random
import bcrypt
import shutil
import sqlite3
import requests
import threading, pytz
from random import randint
from threading import Timer
from threading import Thread
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
# |
# |
app = Flask(__name__)
CORS(app)
# |
SAO_PAULO_TZ = pytz.timezone("America/Sao_Paulo")
# |
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
# |
# | (JWT Settings)
JWT_SECRET = json.load(open("server.json", "r"))['JWT_SECRET']
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 604800
# | (Fernet Settings)
fernet = Fernet(json.load(open("server.json", "r"))['FERNET_KEY'].encode())
# |
# SQLite3  
# | (Open Connection)
def getdb():
    conn = sqlite3.connect('mailserver.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor
# |
# JWT Tokens
# |
def gen_token(username):
    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT credentials_update FROM users WHERE username = ?", (username,))
    row = mailcursor.fetchone()
    credentials_update = row['credentials_update'] if row else None

    payload = {
        'username': username,
        'credentials_update': credentials_update,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token
def get_user(token):
    if not token: return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload['username']
        token_pass_time = payload.get('credentials_update')

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT credentials_update FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()

        if row is None: return None

        db_pass_time = row['credentials_update']
        if token_pass_time != db_pass_time: return None 

        return username
    except (ExpiredSignatureError, InvalidTokenError): return None
# |
# |
# PlainPost
# |
# Auth API
# | (Login)
@app.route('/api/login', methods=['POST'])
def login():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()
    username = payload.get('username')

    mailcursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = mailcursor.fetchone()

    if row and bcrypt.checkpw(payload.get('password').encode('utf-8'), row['password']):
        token = gen_token(username)

        response = make_response(jsonify({"response": "Login successful!"}), 200)
        response.set_cookie('token', token, httponly=True, secure=True, samesite='Lax', max_age=60*60*24*71)

        return response
    else: return jsonify({"response": "Bad credentials!"}), 401
# | (Register)
@app.route('/api/signup', methods=['POST'])
def signup():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()
    username = payload.get('username')
    password = bcrypt.hashpw(payload['password'].encode('utf-8'), bcrypt.gensalt())

    mailcursor.execute("SELECT 1 FROM used_usernames WHERE username = ?", (username,))
    if mailcursor.fetchone(): return jsonify({"response": "This username is unavailable."}), 409

    mailcursor.execute(
        "INSERT INTO users (username, password, coins, role, biography, credentials_update) VALUES (?, ?, 0, 'user', 'A PlainPost user', ?)",
        (username, password, datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(SAO_PAULO_TZ).isoformat())
    )
    mailcursor.execute("INSERT OR IGNORE INTO used_usernames (username) VALUES (?)", (username,))
    mailserver.commit()

    token = gen_token(username)
    response = make_response(jsonify({"response": "Signup successful!"}), 200)
    response.set_cookie('token', token, httponly=True, secure=True, samesite='Lax', max_age=60*60*24*7)

    return response
# |
# Social API
# | (Main Handler)
@app.route('/api/mail', methods=['POST'])
def mail():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({ "response": "Bad credentials!" }), 401
    payload = request.get_json()

    if payload['action'] == "send":
        to = payload.get("to", ""); subject = payload.get("subject", "(no subject)"); body = payload.get("content", "");
        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")

        if "@" in to:
            sender = f"{username}@archsource.xyz"

            msg = MIMEText(body, "plain", "utf-8")
            msg["To"] = to; msg["From"] = sender; msg["Subject"] = subject;

            try:
                with smtplib.SMTP("localhost", 2525) as smtp: smtp.sendmail(sender, [to], msg.as_string())
                
                return jsonify({"response": "OK"}), 200
            except Exception as e: return jsonify({"response": f"SMTP error: {str(e)}"}), 500

        mailcursor.execute("SELECT * FROM users WHERE username = ?", (to,))
        if mailcursor.fetchone() is None: return jsonify({"response": "Target not found!"}), 404

        content = fernet.encrypt(f"[{timestamp} - {username}] {body}".encode()).decode()

        mailcursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", (to, username, content, timestamp))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "read" or payload['action'] == "read_blocked":
        mailcursor.execute("SELECT blocked_users FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        blocked_users = json.loads(row['blocked_users']) if row and row['blocked_users'] else []

        mailcursor.execute("SELECT id, sender, content FROM mails WHERE recipient = ?", (username,))
        rows = mailcursor.fetchall()

        decrypted_mails = []
        for row in rows:
            sender_email = row['sender']
            if sender_email.endswith("@archsource.xyz"):
                sender_user = sender_email.split('@')[0]
                is_blocked = sender_user in blocked_users
            else: is_blocked = sender_email in blocked_users

            if payload['action'] == "read" and is_blocked: continue 
            elif payload['action'] == "read_blocked" and not is_blocked: continue

            decrypted_content = fernet.decrypt(row["content"].encode('utf-8')).decode()
            decrypted_mails.append({ "id": row["id"], "content": decrypted_content })

        return jsonify({"response": decrypted_mails if decrypted_mails else "No messages"}), 200
    elif payload['action'] == "clear": 
        mailcursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "delete":
        message_id = payload.get("id")
        if not message_id: return jsonify({"response": "Missing message ID!"}), 400

        mailcursor.execute("SELECT * FROM mails WHERE id = ? AND recipient = ?", (message_id, username))
        if not mailcursor.fetchone(): return jsonify({"response": "Message not found!"}), 404

        mailcursor.execute("DELETE FROM mails WHERE id = ?", (message_id,))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "transfer":
        try: 
            to = payload.get("to"); amount = int(payload.get("amount"))
            if amount <= 0: raise ValueError("Invalid amount!")
        except ValueError: return jsonify({"response": "Invalid amount!"}), 406

        if to.endswith("@archsource.xyz") or to.endswith("@mail.archsource.xyz"): to = to.replace("@archsource.xyz", "").replace("@mail.archsource.xyz", "")
        elif "@" in to: return jsonify({"response": "Only supported to other PlainPost users!"}), 405

        mailcursor.execute("SELECT coins FROM users WHERE username = ?", (to,))
        recipient_row = mailcursor.fetchone()
        if recipient_row is None: return jsonify({"response": "Target not found!"}), 404

        mailcursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
        sender_row = mailcursor.fetchone()
        if sender_row["coins"] < amount: return jsonify({"response": "No enough money!"}), 402

        mailcursor.execute("UPDATE users SET coins = coins - ? WHERE username = ?", (amount, username))
        mailcursor.execute("UPDATE users SET coins = coins + ? WHERE username = ?", (amount, to))
        mailserver.commit()
        
        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "changepass":
        if not payload.get('newpass'): return jsonify({"response": "Invalid blank new password!"}), 400

        mailcursor.execute("UPDATE users SET password = ?, credentials_update = ? WHERE username = ?", (bcrypt.hashpw(payload['newpass'].encode('utf-8'), bcrypt.gensalt()), datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(SAO_PAULO_TZ).isoformat(), username))
        mailserver.commit() 

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "changepage":
        file_id = payload['file_id']
        file_id = file_id if not "/" in file_id else file_id.split("/")[6]

        if not file_id: return jsonify({"response": ""}), 400

        mailcursor.execute("SELECT saved_name FROM files WHERE id = ? AND owner = ?", (file_id, username))
        row = mailcursor.fetchone()

        if not row: return jsonify({"response": "File not found or you arent owner of it."}), 404

        saved_name = row[0]
        file_path = os.path.join(UPLOAD_FOLDER, saved_name)
        if not os.path.exists(file_path): return jsonify({"response": "File not found."}), 410

        if detect_js(file_path) == True: return jsonify({"response": "Binary file or JavaScript have been blocked!"}), 406

        mailcursor.execute("UPDATE users SET page = ? WHERE username = ?", (file_id, username))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "search":
        user = payload.get('user')

        if user.endswith("@archsource.xyz") or user.endswith("@mail.archsource.xyz"): user = user.replace("@archsource.xyz", "").replace("@mail.archsource.xyz", "");
        elif "@" in user: return jsonify({"response": "Only supported to other PlainPost users!"}), 405

        mailcursor.execute("SELECT role, biography FROM users WHERE username = ?", (user,))
        row = mailcursor.fetchone()

        if row: return jsonify({"response": f"ID: {user}\nRole: [{row['role']}]\nBio: {row['biography']}"}), 200 
        else: return jsonify({"response": "Target not found!"}), 404
    elif payload['action'] == "me":
        mailcursor.execute("SELECT role, biography FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        
        return jsonify({"response": f"ID: {username}\nRole: [{row['role']}]\nBio: {row['biography']}"}), 200
    elif payload['action'] == "blocked_users":
        mailcursor.execute("SELECT blocked_users FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        blocked_users = json.loads(row['blocked_users']) if row and row['blocked_users'] else []

        return jsonify({"response": blocked_users}), 200
    elif payload['action'] == "changebio":
        if not payload['bio']: return 400

        mailcursor.execute("UPDATE users SET biography = ? WHERE username = ?", (payload['bio'], username))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "coins": 
        mailcursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        
        return jsonify({"response": f"{row['coins']}"}), 200
    elif payload['action'] == "block":
        to_block = payload.get('user_to_block')
        if not to_block: return jsonify({"response": "Missing user to block!"}), 400

        is_internal = True
        if to_block.endswith("@archsource.xyz") or to_block.endswith("@mail.archsource.xyz"): to_block = to_block.replace("@archsource.xyz", "").replace("@mail.archsource.xyz", "")
        if "@" in to_block: is_internal = False

        if to_block == username: return jsonify({"response": "You can't block yourself!"}), 405

        if is_internal:
            mailserver, mailcursor = getdb()
            mailcursor.execute("SELECT * FROM users WHERE username = ?", (to_block,))
            if mailcursor.fetchone() is None: return jsonify({"response": "Target not found!"}), 404
        else: mailserver, mailcursor = getdb()

        mailcursor.execute("SELECT blocked_users FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        blocked_users = json.loads(row['blocked_users']) if row and row['blocked_users'] else []

        if to_block in blocked_users: return jsonify({"response": "User already blocked."}), 409

        blocked_users.append(to_block)
        mailcursor.execute("UPDATE users SET blocked_users = ? WHERE username = ?", (json.dumps(blocked_users), username))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "unblock":
        to_unblock = payload.get('user_to_unblock')
        if to_unblock.endswith("@archsource.xyz") or to_unblock.endswith("@mail.archsource.xyz"): to_unblock = to_unblock.replace("@archsource.xyz", "").replace("@mail.archsource.xyz", "")

        if not to_unblock: return jsonify({"response": "Missing user to unblock!"}), 400

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT blocked_users FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()

        blocked_users = json.loads(row['blocked_users']) if row and row['blocked_users'] else []

        if to_unblock not in blocked_users: return jsonify({"response": "User is not blocked."}), 404

        blocked_users.remove(to_unblock)
        mailcursor.execute("UPDATE users SET blocked_users = ? WHERE username = ?", (json.dumps(blocked_users), username))
        mailserver.commit()

        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "signoff":
        mailcursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        mailcursor.execute("DELETE FROM agents WHERE username = ?", (username,))

        mailcursor.execute("SELECT saved_name FROM files WHERE owner = ?", (username,))
        arquivos = mailcursor.fetchall()
        for row in arquivos:
            try: os.remove(os.path.join(UPLOAD_FOLDER, row['saved_name']))
            except FileNotFoundError: pass
        mailcursor.execute("DELETE FROM files WHERE owner = ?", (username,))

        mailcursor.execute("DELETE FROM short_links WHERE owner = ?", (username,))

        mailcursor.execute("DELETE FROM users WHERE username = ?", (username,))
        mailserver.commit()

        response = make_response(jsonify({"response": "OK"}), 200)
        response.set_cookie('token', '', max_age=0, httponly=True, secure=True, samesite='Lax', path='/')

        return response
    elif payload['action'] == "logout":
        response = make_response(jsonify({"response": "OK"}), 200)
        response.set_cookie('token', '', max_age=0, httponly=True, secure=True, samesite='Lax', path='/')

        return response
    elif payload['action'] == "status": return jsonify({"response": username}), 200
    else: return jsonify({"response": "Invalid payload!"}), 405
# | (SMTP Proxy)
class ProxySMTP:
    async def handle_DATA(self, server, session, envelope):
        raw = envelope.original_content or envelope.content
        msg = message_from_bytes(raw)

        to_addr = envelope.rcpt_tos[0]
        from_addr = envelope.mail_from
        username = to_addr.split('@')[0]

        subject = msg['Subject'] or "(sem assunto)"
        if msg.is_multipart():
            body = ""
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(errors='replace')
                    break
        else: body = msg.get_payload(decode=True).decode(errors='replace')

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        content = f"[{timestamp} - {from_addr}] Assunto: {subject} - {body}"
        encrypted = fernet.encrypt(content.encode()).decode()

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not mailcursor.fetchone(): return '550 Usuário não encontrado no PlainPost'

        mailcursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)",
                           (username, from_addr, encrypted, timestamp))
        mailserver.commit()

        return '250 Mensagem recebida com sucesso'
# | 
# Reports
@app.route('/api/report', methods=['POST'])
def submit_report():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"response": "Bad credentials!"}), 401

    payload = request.get_json()
    required_fields = ["type", "description", "links", "date", "time", "target"]
    if not all(field in payload for field in required_fields): return jsonify({"response": "Missing fields!"}), 400

    target = payload['target']
    if target.endswith("@archsource.xyz") or target.endswith("@mail.archsource.xyz"): target = target.replace("@archsource.xyz", "").replace("@mail.archsource.xyz", "")
    elif "@" in target: return jsonify({"response": "Only supported to other PlainPost users!"}), 405

    if target.lower() not in ["desconhecido", "unknown"]:
        mailcursor.execute("SELECT * FROM users WHERE username = ?", (target,))
        if not mailcursor.fetchone(): return jsonify({"response": "Target not found!"}), 404
    else: target = target.lower()
    
    report_id = str(uuid.uuid4())
    report_dir = os.path.join("reports", target, report_id)
    os.makedirs(report_dir, exist_ok=True)

    report_json_path = os.path.join(report_dir, "report.json")
    payload['sender'] = username
    payload['report-time'] = datetime.now().strftime("%H:%M %d/%m/%Y")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
        
    if payload['type'] == "mail":
        mailcursor.execute("SELECT content FROM mails WHERE recipient = ?", (username,))
        messages = mailcursor.fetchall()
        with open(os.path.join(report_dir, "inbox.txt"), "w", encoding="utf-8") as inbox:
            for msg in messages:
                try: inbox.write(fernet.decrypt(msg['content'].encode()).decode() + "\n")
                except: pass
        mailcursor.execute("SELECT content FROM mails WHERE recipient = ?", (target,))
        messages = mailcursor.fetchall()
        with open(os.path.join(report_dir, "reported_inbox.txt"), "w", encoding="utf-8") as inbox:
            for msg in messages:
                try: inbox.write(fernet.decrypt(msg['content'].encode()).decode() + "\n")
                except: pass
    elif payload['type'] == "mural":
        mailcursor.execute("SELECT page FROM users WHERE username = ?", (target,))
        row = mailcursor.fetchone()
        if row and row['page']:
            mailcursor.execute("SELECT saved_name FROM files WHERE id = ?", (row['page'],))
            file_row = mailcursor.fetchone()
            if file_row:
                file_path = os.path.join(UPLOAD_FOLDER, file_row['saved_name'])
                if os.path.exists(file_path): shutil.copy(file_path, os.path.join(report_dir, file_row['saved_name']))
    elif payload['type'] == "file":
        mailcursor.execute("SELECT saved_name FROM files WHERE owner = ?", (target,))
        for row in mailcursor.fetchall():
            file_path = os.path.join(UPLOAD_FOLDER, row['saved_name'])
            if os.path.exists(file_path): shutil.copy(file_path, os.path.join(report_dir, row['saved_name']))
    elif payload['type'] == "short_link":
        mailcursor.execute("SELECT * FROM short_links")
        with open(os.path.join(report_dir, "short_links.txt"), "w", encoding="utf-8") as f:
            for row in mailcursor.fetchall(): f.write(f"ID: {row['id']} | Owner: {row['owner']} | To: {row['original_url']}\n")
    else: shutil.copy("mailserver.db", os.path.join(report_dir, "mailserver_copy.db"))

    return jsonify({"response": "Report saved successfully!"}), 200
# |
# |
# Source A.I
# | (Requests)
@app.route('/api/agent', methods=['POST'])
def ollama_agent():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"response": "Bad credentials!"}), 401

    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()
    prompt = payload.get("prompt", "")

    if not prompt.strip(): return jsonify({"response": "Prompt cannot be empty"}), 400

    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT role, coins FROM users WHERE username = ?", (username,))
    row = mailcursor.fetchone()
    role = row["role"]
    coins = row["coins"]

    if role not in ["Admin", "MOD", "DEV"]:
        if coins <= 0: return jsonify({"response": "Not enough coins!"}), 402

        mailcursor.execute("UPDATE users SET coins = coins - 1 WHERE username = ?", (username,))
        mailserver.commit()

    try:
        mailcursor.execute("INSERT INTO agents (username, role, content) VALUES (?, ?, ?)", (username, 'user', prompt))
        mailserver.commit()

        mailcursor.execute("SELECT role, content FROM agents WHERE username = ? ORDER BY id DESC LIMIT 64", (username,))
        rows = mailcursor.fetchall()
        messages = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

        ollama_response = requests.post("http://localhost:11434/v1/chat/completions", json={"model": "agent", "messages": messages} )

        if ollama_response.status_code != 200:
            ollama_refund(mailcursor, mailserver)
            return jsonify({"response": "Ollama error"}), 502

        result = ollama_response.json()
        message = ollama_locking(result['choices'][0]['message']['content'])

        mailcursor.execute("INSERT INTO agents (username, role, content) VALUES (?, ?, ?)", (username, 'assistant', message))
        mailserver.commit()

        mailcursor.execute("""
            DELETE FROM agents 
            WHERE id IN (
                SELECT id FROM agents 
                WHERE username = ? 
                ORDER BY id ASC 
                LIMIT (SELECT MAX(0, COUNT(*) - 64) FROM agents WHERE username = ?)
            )
        """, (username, username))
        mailserver.commit()

        return jsonify({"response": message}), 200

    except Exception as e:
        return jsonify({"response": f"Internal error: {str(e)}"}), 500
def ollama_locking(text):
    blocked = ["inteligência artificial", "modelo de linguagem", "OpenAI", "DeepMind"]
    for word in blocked: 
        text = re.sub(rf'\b{re.escape(word)}\b', '[INFORMAÇÃO REDIGIDA]', text, flags=re.IGNORECASE)
    
    return text
def ollama_refund(cursor, server, username):
    try:
        cursor.execute("UPDATE users SET coins = coins + 1 WHERE username = ?", (username,))
        server.commit()
    except Exception as e: print(f"[WARN] Refounding error to '{username}': {e}")
# | (Clear agent)
@app.route('/api/agent/forget', methods=['POST'])
def forget_history():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"response": "Bad credentials!"}), 401

    mailserver, mailcursor = getdb()
    mailcursor.execute("DELETE FROM agents WHERE username = ?", (username,))
    mailserver.commit()

    return jsonify({"response": "All agent memory cleared!"}), 200
# | (Read history)
@app.route('/api/agent/history', methods=['GET'])
def get_agent_history():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"response": "Bad credentials!"}), 401

    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT role, content FROM agents WHERE username = ? ORDER BY id DESC LIMIT 64", (username,))
    rows = mailcursor.fetchall()

    history = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    return jsonify({"response": history}), 200
# |
# |
# Murals
# |
# | (Access mural from an user)
@app.route('/mural/<username>', methods=['GET'])
def mural(username):
    mailserver, mailcursor = getdb()

    mailcursor.execute("SELECT page FROM users WHERE username = ?", (username,))
    row = mailcursor.fetchone()

    if not row: return render_template('404.html', message="Usuário não encontrado."), 404

    file_id = row[0]

    if not file_id: return render_template('404.html', message="Usuário não possui um mural."), 404

    mailcursor.execute("SELECT saved_name FROM files WHERE id = ?", (file_id,))
    row = mailcursor.fetchone()

    if not row: return render_template('404.html', message="Arquivo do mural não encontrado."), 404

    saved_name = row[0]
    file_path = os.path.join(UPLOAD_FOLDER, saved_name)

    if not os.path.exists(file_path): return render_template('410.html', message="O mural não está mais disponível."), 410

    return send_file(file_path, mimetype='text/html')
# | (Detect JavaScript)
def detect_js(file):
    try:
        with open(file, "rt", encoding="utf-8") as f:
            content = f.read()

        inTag = False
        buffer = ""
        tags = []

        js_patterns = [ r"<script\b", r"javascript\s*:", r"\s(onabort|onblur|onchange|onclick|oncontextmenu|ondblclick|ondrag|ondrop|onerror|onfocus|oninput|onkeydown|onkeypress|onkeyup|onload|onmousedown|onmousemove|onmouseout|onmouseover|onmouseup|onreset|onresize|onscroll|onselect|onsubmit|onunload)\s*=" ]

        for char in content:
            if char == "<":
                inTag = True
                buffer = "<"

            elif char == ">":
                if inTag:
                    buffer += ">"
                    tags.append(buffer)
                    buffer = ""
                inTag = False

            elif inTag: buffer += char

        for tag in tags:
            for pattern in js_patterns:
                if re.search(pattern, tag, re.IGNORECASE): return True
        
        return False
    except UnicodeDecodeError: return True
# |
# |
# URL Shorter
# | (Redirection API)
@app.route('/s/<short_id>', methods=['GET'])
def redirect_short_link(short_id):
    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT original_url FROM short_links WHERE id = ?", (short_id,))
    row = mailcursor.fetchone()

    if row: return flask.redirect(row['original_url'])
    
    return render_template('404.html', message="O link curto não foi encontrado."), 404
# | (Requests Handler API)
@app.route('/api/short', methods=['POST'])
def short_links_handler():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"response": "Bad credentials!"}), 401

    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()
    action = payload.get("action")

    mailserver, mailcursor = getdb()

    if payload['action'] == "create":
        url = payload.get("url", "").strip()
        if not url: return jsonify({"response": "Missing URL!"}), 400

        mailcursor.execute("SELECT role, coins FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        role = row['role']
        coins = row['coins']

        if role == "user":
            mailcursor.execute("SELECT COUNT(*) FROM short_links WHERE owner = ?", (username,))
            count = mailcursor.fetchone()[0]
            if count >= 5: return jsonify({"response": "Short link limit reached (5 links for user)."}), 429
        
        if role not in ["Admin", "MOD", "DEV"]:
            if coins < 5: return jsonify({"response": "Not enough coins!"}), 402
            mailcursor.execute("UPDATE users SET coins = coins - 5 WHERE username = ?", (username,))

        while True:
            short_id = str(randint(10000, 99999))
            mailcursor.execute("SELECT 1 FROM short_links WHERE id = ?", (short_id,))
            if not mailcursor.fetchone(): break 

        mailcursor.execute("INSERT INTO short_links (id, owner, original_url) VALUES (?, ?, ?)", (short_id, username, url))
        mailserver.commit()

        return jsonify({"response": short_id}), 200
    elif action == "list":
        mailcursor.execute("SELECT id, original_url FROM short_links WHERE owner = ?", (username,))
        rows = mailcursor.fetchall()

        result = [{"id": row["id"], "url": row["original_url"], "short": f"/s/{row['id']}"} for row in rows]
        return jsonify({"response": result}), 200
    elif action == "delete":
        short_id = payload.get("id")
        if not short_id: return jsonify({"response": "Missing short link ID!"}), 400

        mailcursor.execute("SELECT * FROM short_links WHERE id = ? AND owner = ?", (short_id, username))
        row = mailcursor.fetchone()
        if not row: return jsonify({"response": "Link not found or access denied."}), 404

        mailcursor.execute("DELETE FROM short_links WHERE id = ?", (short_id,))
        mailserver.commit()

        return jsonify({"response": "Short link deleted."}), 200
    else: return jsonify({"response": "Invalid action!"}), 405
# |
# |
# BinDrop
# | (Upload API)
@app.route('/api/drive/upload', methods=['POST'])
def drive_upload():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({ "response": "Bad credentials!" }), 401
    
    file = request.files.get('file')
    
    file_id = str(uuid.uuid4())

    if not file or not username: return jsonify({"success": False, "response": "Bad request. File or user not found!"}), 400

    size = len(file.read())
    file.seek(0)

    if size > 100 * 1024 * 1024: return jsonify({"success": False, "response": "File is large then 100MB."}), 413

    saved_name = f"{file_id}.bin"
    path = os.path.join(UPLOAD_FOLDER, saved_name)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(path)

    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(SAO_PAULO_TZ)
    expire_time = None
    if size > 20 * 1024 * 1024: expire_time = now + timedelta(hours=5)

    mailserver, mailcursor = getdb()
    mailcursor.execute("INSERT INTO files (id, owner, original_name, saved_name, size, upload_time, expire_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (file_id, username, secure_filename(file.filename), saved_name, size, now.isoformat(), expire_time.isoformat() if expire_time else None))
    mailserver.commit()

    return jsonify({"success": True}), 200
# | (Download API)
@app.route('/api/drive/download/<file_id>', methods=['GET'])
def drive_download(file_id):
    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT original_name, saved_name FROM files WHERE id = ?", (file_id,))
    row = mailcursor.fetchone()

    if not row: return jsonify({"response": "File not found."}), 404

    original_name, saved_name = row
    path = os.path.join(UPLOAD_FOLDER, saved_name)
    return send_file(path, as_attachment=True, download_name=original_name)
@app.route('/api/drive/delete/<file_id>', methods=['DELETE'])
def drive_delete(file_id):
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"success": False, "response": "Bad credentials!"}), 401

    mailserver, mailcursor = getdb()

    mailcursor.execute("SELECT saved_name FROM files WHERE id = ? AND owner = ?", (file_id, username))
    row = mailcursor.fetchone()

    if not row: return jsonify({"success": False, "response": "File not found or permission denied."}), 404

    saved_name = row[0]

    try: os.remove(os.path.join(UPLOAD_FOLDER, saved_name))
    except FileNotFoundError: pass

    mailcursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    mailserver.commit()

    return jsonify({"success": True}), 200
# | (View API)
@app.route('/api/drive/list', methods=['GET'])
def drive_list():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({ "response": "Bad credentials!" }), 401
    
    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT id, original_name, size, upload_time, expire_time FROM files WHERE owner = ?", (username,))
    rows = mailcursor.fetchall()

    result = []
    for row in rows:
        result.append({
            "file_id": row[0],
            "filename": row[1],
            "size": row[2],
            "upload_time": row[3],
            "expire_time": row[4]
        })
    return jsonify(result), 200
# | (Extend File expire time API)
@app.route('/api/drive/extend_expires', methods=['POST'])
def extend_expires():
    username = get_user(request.cookies.get('token'))
    if not username: return jsonify({"response": "Bad credentials!"}), 401

    data = request.get_json()
    if not data or "file_id" not in data: return jsonify({"response": "Missing file_id"}), 400
    
    file_id = data["file_id"]

    mailserver, mailcursor = getdb()

    mailcursor.execute("SELECT expire_time FROM files WHERE id = ? AND owner = ?", (file_id, username))
    row = mailcursor.fetchone()
    if not row: return jsonify({"response": "File not found or access denied."}), 404

    current_expire = row[0]
    if current_expire is None: return jsonify({"response": "This file does not expire. Cannot extend expiration."}), 400

    mailcursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
    user_row = mailcursor.fetchone()
    if not user_row or user_row[0] < 1: return jsonify({"response": "Not enough coins."}), 402

    mailcursor.execute("UPDATE users SET coins = coins - 1 WHERE username = ?", (username,))

    current_dt = datetime.fromisoformat(current_expire).astimezone(SAO_PAULO_TZ)
    new_expire = current_dt + timedelta(hours=2)

    mailcursor.execute("UPDATE files SET expire_time = ? WHERE id = ?", (new_expire.isoformat(), file_id))
    mailserver.commit()

    return jsonify({"success": True, "new_expire_time": new_expire.isoformat()}), 200
# |
# |
# |
# |
# Thread - Clear expired files
def init_expiration_checker():
    def check_expired_files():
        now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(SAO_PAULO_TZ)

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT id, saved_name FROM files WHERE expire_time IS NOT NULL AND expire_time <= ?", (now.isoformat(),))
        expired = mailcursor.fetchall()

        for file_id, saved_name in expired:
            try: os.remove(os.path.join(UPLOAD_FOLDER, saved_name))
            except FileNotFoundError: pass
        
            mailcursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        
        mailserver.commit()

        threading.Timer(300, check_expired_files).start()

    check_expired_files()
init_expiration_checker()
# |
# |
# |
# Start API
if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true": app.run(port=9834, debug=True, host="127.0.0.1")
    else:
        proxy = Controller(ProxySMTP(), hostname='0.0.0.0', port=25)
        proxy.start(); print(" * Running SMTP Proxy at port 25")

        app.run(port=9834, debug=True, host="127.0.0.1")
    