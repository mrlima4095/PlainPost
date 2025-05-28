import os
import sqlite3
import psycopg2

def PlainPostDB():
    conn = psycopg2.connect(
        dbname=json.load(open("jwt.properties", "r"))['DB_NAME'],
        user=json.load(open("jwt.properties", "r"))['DB_USER'],
        password=json.load(open("jwt.properties", "r"))['DB_PASSWORD'],
        host=json.load(open("jwt.properties", "r"))['DB_HOST'], 
        port=json.load(open("jwt.properties", "r"))['DB_PORT'],
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            coins INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    """)
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user'")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            username TEXT,
            role TEXT,
            PRIMARY KEY(username, role),
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role TEXT PRIMARY KEY,
            price INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT,
            sender TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(recipient) REFERENCES users(username)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            original_name TEXT NOT NULL,
            saved_name TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_time TEXT NOT NULL,
            expire_time TEXT
        )
    """)

    conn.commit()
    conn.close()

PlainPostDB()