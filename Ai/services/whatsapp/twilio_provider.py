import os
import logging

from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioProvider:

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

        if not self.account_sid:
            raise RuntimeError("TWILIO_ACCOUNT_SID is missing.")

        if not self.auth_token:
            raise RuntimeError("TWILIO_AUTH_TOKEN is missing.")

        if not self.from_number:
            raise RuntimeError("TWILIO_WHATSAPP_NUMBER is missing.")

        self.client = Client(
            self.account_sid,
            self.auth_token
        )

    @staticmethod
    def normalize_number(number: str) -> str:
        """
        Twilio WhatsApp numbers use:

        whatsapp:+2547XXXXXXXX
        """

        number = number.strip()

        if not number.startswith("whatsapp:"):
            number = f"whatsapp:{number}"

        return number

    def send(
        self,
        to: str,
        message: str,
        template_name: str | None = None
    ) -> dict:

        try:
            recipient = self.normalize_number(to)

            result = self.client.messages.create(
                from_=self.normalize_number(
                    self.from_number
                ),
                to=recipient,
                body=message
            )

            return {
                "success": True,
                "provider": "twilio",
                "message_id": result.sid,
                "to": to,
                "message": message
            }

        except Exception as exc:
            logger.exception(
                "Twilio WhatsApp send failed"
            )

            return {
                "success": False,
                "provider": "twilio",
                "to": to,
                "error": str(exc)
            }

    def parse_incoming(self, data=None):
        """
        Normalize Twilio's webhook payload into our
        application's internal format.
        """

        data = data or {}

        sender = data.get("From", "")
        body = data.get("Body", "")
        message_id = data.get("MessageSid")

        phone = sender.replace(
            "whatsapp:",
            "",
            1
        )

        profile_name = data.get(
            "ProfileName"
        )

        return {
            "phone": phone,
            "name": profile_name,
            "message": body,
            "message_id": message_id,
            "is_group": False,
            "raw": data
        }