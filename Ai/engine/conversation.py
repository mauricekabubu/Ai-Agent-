from database.model import Message, Conversation
from extensions.extension import db

from engine.context import ContextBuilder
from services.ai import AIService


class ConversationalManager:

    def __init__(self):
        self.ai = AIService()
        self.context = ContextBuilder()


    def get_or_create_conversation(self, contact):

        conversation = Conversation.query.filter_by(
            contact_id=contact.id,
            status="active"
        ).first()


        if not conversation:

            conversation = Conversation(
                contact_id=contact.id,
                title="New conversation"
            )

            db.session.add(conversation)
            db.session.commit()


        return conversation



    def process_messages(self, contact, message_text):

        # 1. Get conversation
        conversation = self.get_or_create_conversation(contact)


        # 2. Save user message
        user_message = Message(
            conversation_id=conversation.id,
            sender="contact",
            content=message_text
        )

        db.session.add(user_message)
        db.session.commit()



        # 3. Build AI context
        messages = self.context.build(
            conversation,
            message_text
        )


        # 4. Ask AI
        reply = self.ai.chat(messages)



        # 5. Save AI reply
        ai_message = Message(
            conversation_id=conversation.id,
            sender="ai",
            content=reply
        )


        db.session.add(ai_message)
        db.session.commit()


        return reply