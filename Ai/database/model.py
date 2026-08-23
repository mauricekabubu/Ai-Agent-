from extensions.extension import db
from zoneinfo import ZoneInfo
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    KENYA_TZ = ZoneInfo("Africa/Nairobi")
except ZoneInfoNotFoundError:
    KENYA_TZ = None

def kenya_now():
    return datetime.now(KENYA_TZ)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=kenya_now)
    last_login = db.Column(db.DateTime, default=kenya_now)
    last_active = db.Column(db.DateTime, default=kenya_now)
    auto_reply = db.Column(db.Boolean, default=True)
    reminders = db.relationship(
        "Reminder",
        backref="user",
        lazy=True
    )

    contacts = db.relationship(
        "Contact",
        backref="owner",
        lazy=True
    )
    
    businesses = db.relationship(
        "Business",
        backref="owner",
        lazy=True
    )
    
    notifications = db.relationship(
        "Notifications",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )    
    
    def __repr__(self):
        return f"user_{self.username}"

    
class Business(db.Model):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, 
                        db.ForeignKey("users.id"), nullable=False)
    
    business_name = db.Column(db.String(100))
    business_description = db.Column(db.Text)
    business_email = db.Column(db.String(100), unique=True, nullable=True)
    business_phone = db.Column(db.String(20), unique=True, nullable=False)
    business_location = db.Column(db.String(200), nullable=True)
    business_hours = db.Column(db.String(500), nullable=True)
    
    # Ai settings
    greeting_message = db.Column(db.Text)
    away_message = db.Column(db.Text)
    tone = db.Column(db.String(50), default="Professional")
    response_length = db.Column(db.String(30), default="Balanced")
    auto_reply = db.Column(db.Boolean, default=True)
    notifications = db.Column(db.JSON)   # or db.Text if your database doesn't support JSON
    
    created_at = db.Column(db.DateTime, default=kenya_now)
    services = db.relationship(
        "Services",
        backref="business",
        lazy=True
    )
    
    customers = db.relationship(
        "Customer",
        backref="business",
        lazy=True
    )
    

class Services(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)

    business_id = db.Column(db.Integer, 
                        db.ForeignKey("businesses.id"), nullable=False)
    
    service_name = db.Column(db.Text)
    description = db.Column(db.Text)
    price = db.Column(db.String(100))
    website = db.Column(db.String(200), nullable=True)
    socials = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=kenya_now)
    
class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(db.Integer, 
                        db.ForeignKey("users.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(
        db.String(20),
        unique=True
    )
    category = db.Column(
        db.String(30),
        default="friend"
    )
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=kenya_now)
    conversations = db.relationship(
        "Conversation",
        backref="contact",
        lazy=True
    )

class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    contact_id = db.Column(
        db.Integer,
        db.ForeignKey("contacts.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200)
    )
    status = db.Column(
        db.String(20),
        default="active"
    )
    
    is_group = db.Column(db.Boolean, default=False)
    is_business = db.Column(db.Boolean, default=False)
    auto_reply = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(
        db.DateTime,
        default=kenya_now
    )
    messages = db.relationship(
        "Message",
        backref="conversation",
        lazy=True
    )
    
    
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversations.id"),
        nullable=False
    )

    sender = db.Column(db.String(20))
    content = db.Column(db.Text)

    is_auto_reply = db.Column(
        db.Boolean,
        default=False
    )

    direction = db.Column(
        db.String(20),
        nullable=True,
        default="inbound"
    )

    provider_message_id = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )

    response_to_id = db.Column(
        db.Integer,
        db.ForeignKey("messages.id"),
        nullable=True
    )

    response_time = db.Column(
        db.Integer,
        nullable=True
    )
    
    created_at = db.Column(
        db.DateTime,
        default=kenya_now
    )
    
class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(200))
    description = db.Column(db.Text)

    remind_at = db.Column(db.DateTime)

    completed = db.Column(
        db.Boolean,
        default=False
    )

class Customer(db.Model):
    __tablename__ = "customers"
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=True)
    customer_metadata = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=kenya_now)


class NotificationCategory(db.Model):
    __tablename__ = "notification_categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255)
    )

    notifications = db.relationship(
        "Notifications",
        backref="category",
        lazy=True,
        cascade="all, delete"
    )

class Notifications(db.Model):
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(
    db.Integer,
    db.ForeignKey(
            "notification_categories.id",
            name="fk_notifications_category_id"
        ),
        nullable=False
    )
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    priority = db.Column(
        db.String(20),
        default="normal",
        nullable=False
    )
    read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=kenya_now)
    