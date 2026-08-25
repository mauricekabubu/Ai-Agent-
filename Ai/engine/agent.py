from extensions.extension import db
from database.model import Contact, User, Message
from flask import Blueprint, request, jsonify
from engine.conversation import ConversationalManager
from services.whatsapp import WhatsAppService

import logging


logger = logging.getLogger(__name__)

agent_bp = Blueprint("agent", __name__)

conversation = ConversationalManager()
whatsapp = WhatsAppService()


@agent_bp.route("/api/webhooks/whatsapp",methods=["POST"])
def whatsapp_webhook():
    try:
        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "error": "Missing data"
            }), 400

        incoming = whatsapp.parse_incoming(
            data
        )

        if not incoming:
            return jsonify({
                "success": True,
                "ignored": True
            }), 200

        phone = incoming["phone"]
        name = incoming.get("name")
        current_message = incoming["message"]
        provider_message_id = incoming.get(
            "message_id"
        )

        if not phone or not current_message:
            return jsonify({
                "error": "Missing message data"
            }), 400

        # Ignore groups.
        if incoming.get("is_group"):
            return jsonify({
                "success": True,
                "ignored": True,
                "reason": "group"
            }), 200

        # Find owner.
        user = User.query.first()

        if not user:
            logger.error(
                "No user exists in database."
            )

            return jsonify({
                "error": "No owner configured"
            }), 500

        # Find contact.
        contact = Contact.query.filter_by(
            phone=phone,
            user_id=user.id
        ).first()

        if contact:

            if name and contact.name != name:
                contact.name = name

                db.session.commit()

        else:

            contact = Contact(
                phone=phone,
                name=name,
                user_id=user.id
            )

            db.session.add(contact)
            db.session.commit()

        # Process message.
        reply = conversation.process_messages(
            contact,
            current_message
        )

        # Send response through WhatsApp provider.
        result = whatsapp.send(
            to=phone,
            message=reply
        )

        if not result.get("success"):
            logger.error(
                "WhatsApp send failed: %s",
                result
            )

            return jsonify({
                "success": False,
                "error": "Failed to send WhatsApp reply"
            }), 502

        return jsonify({
            "success": True,
            "reply": reply,
            "message_id": result.get(
                "message_id"
            )
        }), 200

    except Exception as exc:

        db.session.rollback()

        logger.exception(
            "Error processing WhatsApp message"
        )

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500
        