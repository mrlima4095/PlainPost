import asyncio
from aiosmtpd.controller import Controller
from email.message import EmailMessage
from email import message_from_bytes
from datetime import datetime
from server import getdb, fernet  # Reaproveita seu PlainPost

class PlainPostSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        raw = envelope.original_content or envelope.content
        msg = message_from_bytes(raw)

        to_addr = envelope.rcpt_tos[0]
        from_addr = envelope.mail_from
        username = to_addr.split('@')[0]  # "user@mail.plainpost.xyz" → "user"

        subject = msg['Subject'] or "(sem assunto)"
        if msg.is_multipart():
            body = ""
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(errors='replace')
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors='replace')

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        content = f"[{timestamp} - {from_addr}] Assunto: {subject} - {body}"
        encrypted = fernet.encrypt(content.encode()).decode()

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not mailcursor.fetchone():
            return '550 Usuário não encontrado no PlainPost'

        mailcursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)",
                           (username, from_addr, encrypted, timestamp))
        mailserver.commit()

        return '250 Mensagem recebida com sucesso'

controller = Controller(PlainPostSMTPHandler(), hostname='0.0.0.0', port=25)
controller.start()
print("SMTP Proxy rodando na porta 25...")
