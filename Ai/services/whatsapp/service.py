import os
import logging

from services.whatsapp.twilio_provider import TwilioProvider
from services.whatsapp.dialog360_provider import Dialog360Provider

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Provider-independent WhatsApp service.

    The rest of the application talks to this class and does not
    need to know whether WhatsApp is being handled by Twilio,
    360dialog, or another provider.
    """

    def __init__(self):
        provider_name = os.getenv(
            "WHATSAPP_PROVIDER",
            "twilio"
        ).lower()

        if provider_name == "twilio":
            self.provider = TwilioProvider()

        elif provider_name in {"360dialog", "dialog360"}:
            self.provider = Dialog360Provider()

        else:
            raise ValueError(
                f"Unsupported WhatsApp provider: {provider_name}"
            )

        logger.info(
            "WhatsApp provider initialized: %s",
            provider_name
        )

    def send(
        self,
        to: str,
        message: str,
        template_name: str | None = None
    ) -> dict:
        return self.provider.send(
            to=to,
            message=message,
            template_name=template_name
        )

    def parse_incoming(self, data=None):
        return self.provider.parse_incoming(data)