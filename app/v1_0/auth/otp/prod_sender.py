from .base import OtpSender
from app.infraestructure.mail.mail_service import MailService
from app.infraestructure.mail.templates.otp_template import get_otp_email_template
from fastapi import HTTPException, status

class ProdOtpSender(OtpSender):
    def __init__(self, mail_service: MailService):
        self.mail_service = mail_service

    async def send(self, email: str, otp: str, intent: str) -> None:
        html_content = get_otp_email_template(otp, intent)
        success = await self.mail_service.send_mail(email, "Código de Acceso", html_content)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
