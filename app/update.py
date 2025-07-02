import sqlite3
from datetime import datetime
import pytz

# Define o timezone UTC
UTC = pytz.utc

# Pega o datetime atual com timezone UTC
now_utc = datetime.utcnow().replace(tzinfo=UTC).isoformat()

# Conecte no banco SQLite (ajuste o caminho para o seu banco)
conn = sqlite3.connect('mailserver.db')
cur = conn.cursor()

# Atualiza o campo credentials_update para todos os usuários
cur.execute("UPDATE users SET credentials_update = ?", (str(datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Sao_Paulo')).isoformat())),)

conn.commit()
conn.close()

print(f"Atualizado credentials_update para todos os usuários: {now_utc}")
