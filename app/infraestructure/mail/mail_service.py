import aiosmtplib
from email.message import EmailMessage
from app.core.settings import settings
from app.core.logger import logger

class MailService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM
        
        # We interpolate the "Alias" alongside the validated email from SMTP_FROM
        self.from_address = f'"Equipo de Seguridad PT SIATA" <{self.from_email}>'

    async def send_mail(self, to: str, subject: str, html: str) -> bool:
        message = EmailMessage()
        message["From"] = self.from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(html, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=self.port != 465,
                use_tls=self.port == 465,
            )
            logger.info(f'Email sent successfully to {to} with subject "{subject}"')
            return True
        except Exception as error:
            logger.error(f"Failed to send email to {to}: {str(error)}", exc_info=True)
            return False
