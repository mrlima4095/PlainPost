import os
import sqlite3

def PlainPostDB():
    conn = sqlite3.connect('mailserver.db')
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            coins INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            biography TEXT DEFAULT 'A PlainPost user',
            page TEXT,
            blocked_users TEXT DEFAULT '[]',
            credentials_update TEXT DEFAULT (datetime('now'))
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            content TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS short_links (
            id TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            original_url TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS used_usernames (
            username TEXT PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()

PlainPostDB()