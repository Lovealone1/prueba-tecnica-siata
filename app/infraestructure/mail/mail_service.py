import httpx
from app.core.settings import settings
from app.core.logger import logger

class MailService:
    """
    Service responsible for sending emails using Brevo's REST API.
    This replaces the SMTP approach to avoid common cloud provider port blocks (25, 465, 587).
    """
    def __init__(self):
        self.api_key = settings.MAIL_SERVICE_KEY
        self.api_url = settings.MAIL_SERVICE_URL
        self.from_email = settings.SMTP_FROM
        self.from_name = "Equipo de Seguridad PT SIATA"

    async def send_mail(self, to: str, subject: str, html: str) -> bool:
        """
        Sends an email using Brevo's Transactional Email API (v3).
        
        Args:
            to: Recipient email address.
            subject: Email subject line.
            html: HTML content of the email.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.api_key:
            logger.error("MAIL_SERVICE_KEY is not set. Cannot send email via API.")
            return False

        payload = {
            "sender": {"name": self.from_name, "email": self.from_email},
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.api_key
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=10.0
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f'Email sent successfully via Brevo API to {to}')
                    return True
                else:
                    logger.error(f"Brevo API Error ({response.status_code}): {response.text}")
                    return False
        except Exception as error:
            logger.error(f"Exception while sending email via API to {to}: {str(error)}", exc_info=True)
            return False
