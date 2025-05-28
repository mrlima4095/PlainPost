import json
import psycopg2

def PlainPostDB():
    config = json.load(open("jwt.properties", "r"))

    conn = psycopg2.connect(
        dbname=config['DB_NAME'],
        user=config['DB_USER'],
        password=config['DB_PASSWORD'],
        host=config['DB_HOST'], 
        port=config['DB_PORT'],
    )
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user'")
    

    # users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            coins INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    """)

    # user_roles
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            username TEXT,
            role TEXT,
            PRIMARY KEY(username, role),
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """)

    # roles
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role TEXT PRIMARY KEY,
            price INTEGER NOT NULL
        )
    """)

    # mails
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mails (
            id SERIAL PRIMARY KEY,
            recipient TEXT,
            sender TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(recipient) REFERENCES users(username)
        )
    """)

    # files
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