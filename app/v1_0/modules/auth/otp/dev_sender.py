from .base import OtpSender

class DevOtpSender(OtpSender):
    async def send(self, email: str, otp: str, intent: str) -> None:
        print("\n" + "="*50)
        print("🛠️  [DEVELOPMENT MODE] OTP GENERATED")
        print(f"📧 Email:  {email}")
        print(f"🎯 Intent: {intent}")
        print(f"🔑 OTP:    {otp}")
        print("="*50 + "\n")
