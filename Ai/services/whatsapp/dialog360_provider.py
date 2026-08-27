import os
import logging

import requests

logger = logging.getLogger(__name__)


class Dialog360Provider:

    BASE_URL = "https://waba-v2.360dialog.io"

    def __init__(self):
        self.api_key = os.getenv(
            "DIALOG360_API_KEY"
        )

        if not self.api_key:
            raise RuntimeError(
                "DIALOG360_API_KEY is missing."
            )

    @property
    def headers(self):
        return {
            "D360-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    def send(
        self,
        to: str,
        message: str,
        template_name: str | None = None
    ) -> dict:

        # Initial implementation for normal text messages.
        # Template sending will be added separately because
        # WhatsApp templates require additional parameters.

        url = f"{self.BASE_URL}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=15
            )

            response.raise_for_status()

            result = response.json()

            message_id = None

            messages = result.get(
                "messages",
                []
            )

            if messages:
                message_id = messages[0].get("id")

            return {
                "success": True,
                "provider": "360dialog",
                "message_id": message_id,
                "to": to,
                "message": message
            }

        except requests.RequestException as exc:
            logger.exception(
                "360dialog WhatsApp send failed"
            )

            return {
                "success": False,
                "provider": "360dialog",
                "to": to,
                "error": str(exc)
            }

    def parse_incoming(self, data=None):
        """
        Normalize an incoming WhatsApp Cloud/360dialog-style
        webhook payload.
        """

        data = data or {}

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            messages = value.get(
                "messages",
                []
            )

            if not messages:
                return None

            message = messages[0]

            if message.get("type") != "text":
                return None

            phone = message.get("from")
            message_id = message.get("id")

            contacts = value.get(
                "contacts",
                []
            )

            name = None

            if contacts:
                profile = contacts[0].get(
                    "profile",
                    {}
                )

                name = profile.get(
                    "name"
                )

            text = message.get(
                "text",
                {}
            ).get(
                "body",
                ""
            )

            return {
                "phone": phone,
                "name": name,
                "message": text,
                "message_id": message_id,
                "is_group": False,
                "raw": data
            }

        except (KeyError, IndexError, TypeError):
            logger.exception(
                "Could not parse 360dialog webhook"
            )
            return None