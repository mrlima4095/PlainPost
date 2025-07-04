import asyncio
from aiosmtpd.controller import Controller
from email.message import EmailMessage
from server import getdb, fernet  # usa seu PlainPost

class PlainPostSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        from_address = envelope.mail_from
        to_address = envelope.rcpt_tos[0]
        raw_msg = envelope.content.decode('utf8', errors='replace')
        
        # Analisa conteúdo como email
        email = EmailMessage()
        email.set_content(raw_msg)

        body = email.get_payload()
        username = to_address.split('@')[0]  # exemplo: fernanda@plainpost.xyz → fernanda

        mailserver, mailcursor = getdb()
        mailcursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if mailcursor.fetchone() is None:
            return '550 Usuário não encontrado'

        timestamp = datetime.now().strftime("%H:%M %d/%m/%Y")
        content = fernet.encrypt(f"[{timestamp} - {from_address}] {body}".encode()).decode('utf-8')

        mailcursor.execute("INSERT INTO mails (recipient, sender, content, timestamp) VALUES (?, ?, ?, ?)", (username, from_address, content, timestamp))
        mailserver.commit()

        return '250 Mensagem recebida com sucesso'

controller = Controller(PlainPostSMTPHandler(), hostname='0.0.0.0', port=25)
controller.start()
