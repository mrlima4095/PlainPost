import sqlite3
from datetime import datetime
import pytz

SAO_PAULO_TZ = pytz.timezone('America/Sao_Paulo')

# Pega a hora UTC agora
now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

# Converte para horário de São Paulo
now_sp = now_utc.astimezone(SAO_PAULO_TZ)

# Formata como ISO 8601 com timezone
timestamp_sp = now_sp.isoformat()

conn = sqlite3.connect('seu_banco.db')
cur = conn.cursor()

cur.execute("SELECT username FROM users")
users = cur.fetchall()

for (username,) in users:
    cur.execute("""
        UPDATE users SET credentials_update = ? WHERE username = ?
    """, (timestamp_sp, username))

conn.commit()
conn.close()

print(f"Atualizou credentials_update para {len(users)} usuários com o timestamp {timestamp_sp}")
