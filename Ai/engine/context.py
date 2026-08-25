from database.model import Message
from prompts.prompt import SYSTEM_PROMPT


class ContextBuilder:

    def build(self, conversation, current_message):

        history = (
            Message.query
            .filter_by(
                conversation_id=conversation.id
            )
            .order_by(
                Message.created_at.desc()
            )
            .limit(20)
            .all()
        )

        # oldest first
        history.reverse()

        messages = []

        # system prompt
        messages.append(
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        )

        # contact info
        messages.append(
            {
                "role": "system",
                "content": f"""
                Contact name:
                {conversation.contact.name}

                Category:
                {conversation.contact.category}
                """
            }
        )


        # history
        for msg in history:

            role = "user"

            if msg.sender == "ai":
                role = "assistant"


            messages.append(
                {
                    "role": role,
                    "content": msg.content
                }
            )

        # current message
        messages.append(
            {
                "role": "user",
                "content": current_message
            }
        )

        return messages