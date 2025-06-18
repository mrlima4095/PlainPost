#!/usr/bin/env python
# -*- coding: utf-8 -*-
# |
# Imports
# | (Flask)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import send_file
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
import sqlite3
import threading, pytz
from threading import Timer
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
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token
def get_user(token):
    if not token: return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT * FROM users WHERE username = ?", (payload['username'],))
        status = mailcursor.fetchone() is not None

        if status: return payload['username']
        else: return None
    except ExpiredSignatureError: return None
    except InvalidTokenError: return None
# |
# |
# PlainPost
# |
# Auth API
# | (Login)
@app.route('/api/login', methods=['POST'])
def login():
    mailserver, mailcursor = getdb()
    if not request.is_json:
        return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()
    username = payload.get('username')

    mailcursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = mailcursor.fetchone()

    if row and bcrypt.checkpw(payload.get('password').encode('utf-8'), row['password']): return jsonify({"response": gen_token(username)}), 200
    else: return jsonify({"response": "Bad credentials"}), 401
# | (Register)
@app.route('/api/signup', methods=['POST'])
def signup():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    payload = request.get_json()
    username = payload['username']
    password = bcrypt.hashpw(payload['password'].encode('utf-8'), bcrypt.gensalt())

    mailcursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if mailcursor.fetchone(): return jsonify({"response": "This username is already in use."}), 409

    mailcursor.execute("INSERT INTO users (username, password, coins, biography) VALUES (?, ?, 0, 'A PlainPost user')", (username, password))
    mailserver.commit()

    return jsonify({"response": gen_token(username)}), 200
# |
# Social API
@app.route('/api/mail', methods=['POST'])
def mail():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    username = get_user(request.headers.get("Authorization"))
    if not username: return jsonify({ "response": "Bad credentials!" }), 401
    payload = request.get_json()

    if payload['action'] == "send":
        mailcursor.execute("SELECT * FROM users WHERE username = ?", (payload['to'],))
        if mailcursor.fetchone() is None: return jsonify({"response": "Target not found!"}), 404

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        content = fernet.encrypt(f"[{timestamp} - {username}] {payload['content']}".encode()).decode('utf-8')

        mailcursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", (payload['to'], username, content, timestamp))
        mailserver.commit()

        return jsonify({"response": "Mail sent!"}), 200
    elif payload['action'] == "read":
        mailcursor.execute("SELECT content FROM mails WHERE recipient = ?", (username,))
        rows = mailcursor.fetchall()

        decrypted_mails = []
        for row in rows:
            encrypted_content = row["content"]

            decrypted_content = fernet.decrypt(encrypted_content.encode('utf-8')).decode()
            decrypted_mails.append(decrypted_content)

        return jsonify({"response": '\n'.join(decrypted_mails) if decrypted_mails else "No messages"}), 200
    elif payload['action'] == "clear": 
        mailcursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        mailserver.commit()

        return jsonify({"response": "Inbox was cleared!"}), 200
    elif payload['action'] == "transfer":
        try:
            amount = int(payload['amount'])
            if amount <= 0: return jsonify({"response": "Invalid amount!"}), 406
        except ValueError: return jsonify({"response": "Invalid amount!"}), 406

        mailcursor.execute("SELECT coins FROM users WHERE username = ?", (payload['to'],))
        recipient_row = mailcursor.fetchone()
        if recipient_row is None: return jsonify({"response": "Target not found!"}), 404

        mailcursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
        sender_row = mailcursor.fetchone()
        if sender_row["coins"] < amount: return jsonify({"response": "No enough money!"}), 401

        mailcursor.execute("UPDATE users SET coins = coins - ? WHERE username = ?", (amount, username))
        mailcursor.execute("UPDATE users SET coins = coins + ? WHERE username = ?", (amount, payload['to']))
        mailserver.commit()
        
        return jsonify({"response": "OK"}), 200
    elif payload['action'] == "changepass":
        if not payload['newpass']: return jsonify({"response": "Blank new password!"}), 400

        mailcursor.execute("UPDATE users SET password = ? WHERE username = ?", (bcrypt.hashpw(payload['newpass'].encode('utf-8'), bcrypt.gensalt()), username))
        mailserver.commit() 

        return jsonify({"response": "Password changed!"}), 200
    elif payload['action'] == "search":
        mailcursor.execute("SELECT biography FROM users WHERE username = ?", (payload['user'],))
        row = mailcursor.fetchone()

        if row: return jsonify({"response": f"ID: {payload['user']}\nBio: {row['biography']}"}), 200 
        else: return jsonify({"response": "Target not found!"}), 404
    elif payload['action'] == "me":
        mailcursor.execute("SELECT biography FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        
        return jsonify({"response": f"ID: {username}\nBio: {row['biography']}"}), 200
    elif payload['action'] == "changebio":
        if not payload['bio']: return 400

        mailcursor.execute("UPDATE users SET biography = ? WHERE username = ?", (payload['bio'], username))
        mailserver.commit()

        return jsonify({"response": "Bio changed!"}), 200
    elif payload['action'] == "coins": 
        mailcursor.execute("SELECT coins FROM users WHERE username = ?", (username,))
        row = mailcursor.fetchone()
        
        return jsonify({"response": f"{row['coins']}"}), 200
    elif payload['action'] == "signoff": 
        mailcursor.execute("DELETE FROM mails WHERE recipient = ?", (username,))
        mailcursor.execute("DELETE FROM users WHERE username = ?", (username,))
        mailserver.commit()

        return jsonify({"response": "Account deleted!"}), 200
    elif payload['action'] == "status": return jsonify({"response": username}), 200
    else: return jsonify({"response": "Invalid payload!"}), 405
# |
# |
# Murals
# |
# Settings
# | (Change HTML page)
@app.route('/api/mural', methods=['POST'])
def mural_settings():
    mailserver, mailcursor = getdb()
    if not request.is_json: return jsonify({"response": "Invalid content type. Must be JSON."}), 400

    username = get_user(request.headers.get("Authorization"))
    if not username: return jsonify({"response": "Bad credentials!"}), 401
    payload = request.get_json()
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

    return jsonify({"response": "Page changed with sucess."}), 200
# | (Access mural from an user)
@app.route('/mural/<username>', methods=['GET'])
def mural(username):
    mailserver, mailcursor = getdb()

    mailcursor.execute("SELECT page FROM users WHERE username = ?", (username,))
    row = mailcursor.fetchone()

    if not row: return jsonify({"response": "User not found!."}), 404

    file_id = row[0]

    if not file_id: return jsonify({"response": "User dont have mural."}), 404

    mailcursor.execute("SELECT saved_name FROM files WHERE id = ?", (file_id,))
    row = mailcursor.fetchone()

    if not row: return jsonify({"response": "Mural file not found."}), 404

    saved_name = row[0]
    file_path = os.path.join(UPLOAD_FOLDER, saved_name)

    if not os.path.exists(file_path): return jsonify({"response": "Mural file is not avaliable."}), 410

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
                if re.search(pattern, tag, re.IGNORECASE):
                    return True
        return False
    except UnicodeDecodeError: return True
# |
# |
# BinDrop
# |
# Upload API
@app.route('/api/drive/upload', methods=['POST'])
def drive_upload():
    username = get_user(request.headers.get("Authorization"))
    if not username: return jsonify({ "response": "Bad credentials" }), 401
    
    file = request.files.get('file')
    
    file_id = str(uuid.uuid4())

    if not file or not username:
        return jsonify({"success": False, "response": "Arquivo ou usuário não fornecido."}), 400

    size = len(file.read())
    file.seek(0)

    if size > 100 * 1024 * 1024:
        return jsonify({"success": False, "response": "Arquivo excede o limite de 100MB."}), 413

    saved_name = f"{file_id}.bin"
    path = os.path.join(UPLOAD_FOLDER, saved_name)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(path)

    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(SAO_PAULO_TZ)
    expire_time = None
    if size > 20 * 1024 * 1024:
        expire_time = now + timedelta(hours=5)

    mailserver, mailcursor = getdb()
    mailcursor.execute("INSERT INTO files (id, owner, original_name, saved_name, size, upload_time, expire_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (file_id, username, secure_filename(file.filename), saved_name, size, now.isoformat(), expire_time.isoformat() if expire_time else None))
    mailserver.commit()

    return jsonify({"success": True}), 200
# |
# Download API
@app.route('/api/drive/download/<file_id>', methods=['GET'])
def drive_download(file_id):
    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT original_name, saved_name FROM files WHERE id = ?", (file_id,))
    row = mailcursor.fetchone()

    if not row:
        return jsonify({"response": "Arquivo não encontrado."}), 404

    original_name, saved_name = row
    path = os.path.join(UPLOAD_FOLDER, saved_name)
    return send_file(path, as_attachment=True, download_name=original_name)
# |
# View API
@app.route('/api/drive/list', methods=['GET'])
def drive_list():
    username = get_user(request.headers.get("Authorization"))
    if not username: return jsonify({ "response": "Bad credentials" }), 401
    
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
# |
# Delete API
@app.route('/api/drive/delete/<file_id>', methods=['DELETE'])
def drive_delete(file_id):
    mailserver, mailcursor = getdb()
    mailcursor.execute("SELECT saved_name FROM files WHERE id = ?", (file_id,))
    row = mailcursor.fetchone()

    if not row: return jsonify({"success": False}), 404

    saved_name = row[0]
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, saved_name))
    except FileNotFoundError:
        pass

    mailcursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    mailserver.commit()

    return jsonify({"success": True}), 200
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
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, saved_name))
            except FileNotFoundError:
                pass
            mailcursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        
        mailserver.commit()

        threading.Timer(300, check_expired_files).start()

    check_expired_files()
init_expiration_checker()
# |
# |
# |
# |
# Start API
if __name__ == '__main__':
    app.run(port = 9834, debug=True, host="127.0.0.1")
