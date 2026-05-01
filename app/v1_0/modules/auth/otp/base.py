from abc import ABC, abstractmethod

class OtpSender(ABC):
    @abstractmethod
    async def send(self, email: str, otp: str, intent: str) -> None:
        pass
