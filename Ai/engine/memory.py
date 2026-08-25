from extensions.extension import db
from database.model import Message

# Memory manager we only need 4 things: save,getting recent and last messages and clear history

class MemoryManager:
        
    def save_message(self,conversation_id,sender,content):
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        return message
    
    def get_recent_messages(self, contact_id, limit=20):
        
        return (
            Message.query
            .filter_by(contact_id=contact_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_last_messages(self, contact_id):
        
        return (
            Message.query
            .filter_by(contact_id=contact_id)
            .order_by(Message.created_at.desc())
            .first()
        )
    
    def clear_history(self, contact_id):
        message = Message.query.filter_by(
            contact_id=contact_id
        ).first()
        
        db.session.delete(message)
        db.session.commit()
        
        
        
        