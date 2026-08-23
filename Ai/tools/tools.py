"""
tools.py
Tool definitions for Atom AI — a WhatsApp business assistant.

Framework: Flask (webhook/app layer) + LangChain/LangGraph (agent/tool orchestration)

Each tool is decorated with LangChain's @tool so it can be bound directly to an
LLM (e.g. via `llm.bind_tools([...])` or passed into a LangGraph node/ToolNode).

Conventions:
- Every tool takes/returns simple JSON-serializable types (str, int, float, bool,
  dict, list) since results may be sent back through the LLM and/or over WhatsApp.
- Every tool returns a dict with at least {"success": bool, ...}. This keeps
  error handling consistent for the agent and easy to log/trace.
- Business logic (DB calls, external APIs) is stubbed out with TODOs — wire these
  to your actual services (CRM, calendar, email/WhatsApp provider, vector store).
- Keep tools narrow and single-purpose; compose them in the graph rather than
  building "god tools".
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os
import logging

from extensions.extension import db
from database.model import Business, Customer, Notifications, Services, NotificationCategory

load_dotenv()  # Load environment variables from .env file

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")

logger = logging.getLogger(__name__)

# langchain's package name can differ by installation. Try both common imports
# and fall back to a no-op decorator to allow the module to be imported in
# environments without langchain during development or static analysis.
try:
    from langchain_core.tools import tool  # type: ignore
except Exception:  # pragma: no cover - import fallback
    try:
        from langchain.tools import tool  # type: ignore
    except Exception:
        logger.warning("LangChain not found; using no-op @tool decorator.")
        # Minimal passthrough decorator when langchain is unavailable.
        def tool(func=None, **_kwargs):
            if func is None:
                return lambda f: f
            return func


# ---------------------------------------------------------------------------
# Business
# ---------------------------------------------------------------------------

@tool
def get_business_info() -> dict:
    """Return general information about the business: name, description,
    address, website, and social links. Use when a customer asks what the
    business does, where it's located, or how to find it online."""
    # TODO: fetch from DB / config (e.g. `Business` table or settings service)
    try:
        business = Business.query.first()
            
            
        return {
            "success": True,
            "business_name": business.business_name if business else "",
            "business_description": business.business_description if business else "",
            "business_email": business.business_email if business else "",
            "business_phone": business.business_phone if business else "",
            "business_location": business.business_location if business else "",
            "business_hours": business.business_hours if business else ""        
        }
    except Exception as e:
        logger.error(f"Error fetching business info: {e}")
        return {
            "success": False,
            "error": str(e)
        }
        
    

@tool
def get_business_hours() -> dict:
    """Return the business's operating hours for each day of the week.
    Use when a customer asks if the business is open, or what time it closes."""
    # TODO: fetch from DB / config
    
    try:
        business_hours = Business.query.first()
    except Exception as e:
        logger.error(f"Error fetching business hours: {e}")
        return {
            "success": False,
            "error": str(e)
        }

    return {
        "success": True,
        "timezone": "",
        "hours": {
            "Monday": business_hours.business_hours if business_hours else "",
            "Tuesday": business_hours.business_hours if business_hours else "",
            "Wednesday": business_hours.business_hours if business_hours else "",
            "Thursday": business_hours.business_hours if business_hours else "",
            "Friday": business_hours.business_hours if business_hours else "",
            "Saturday": business_hours.business_hours if business_hours else "",
            "Sunday": business_hours.business_hours if business_hours else "",
        },
    }


@tool
def get_services() -> dict:
    """Return the list of services or products the business offers, including
    short descriptions. Use when a customer asks what the business offers."""
    # TODO: fetch from DB (e.g. `Service` table)
    try:
        services = Services.query.all()
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
        return {
            "success": False,
            "error": str(e)
        }

    return {
        "success":True,
        "services": [
            {
                "service_name":s.service_name,
                "description":s.description,
                "price":s.price,
                "website":s.website,
                "socials":s.socials
            } for s in services
        ]                       
    }

# ---------------------------------------------------------------------------
# CRM
# ---------------------------------------------------------------------------


@tool
def save_customer(name: str, phone: str, email: Optional[str] = None, metadata: Optional[dict] = None) -> dict:
    """Create or update a customer record.

    Args:
        name: Full name of the customer.
        phone: Phone number (WhatsApp number), used as the unique identifier.
        email: Optional email address.
        metadata: Optional extra fields to store (e.g. preferences, tags).
    """
    # TODO: upsert into `Customer` table
    try:
        customer = Customer.query.filter_by(phone=phone).first()
        
        if customer:
            customer.name = name
            customer.email = email
    
        else:        
            customer = Customer(
                        name=name,
                        phone=phone,
                        email=email,
                        metadata=metadata
            )
            db.session.add(customer)
        
        db.session.commit()
            
                
        return {
            "success": True,
            "customer_id": customer.id,
            "phone": phone
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving customer {phone}: {e}")
        return {
            "success": False,
            "error": str(e),
            "phone": phone
        }
        
    

# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@tool
def notify_owner(
    title: str,
    message: str,
    user_id: int,
    category: str = "system",
    priority: str = "normal"
) -> dict:
    """
    Create an internal notification for the business owner/admin.

    Args:
        title: Short notification title.
        message: Notification details.
        user_id: Owner/admin user ID.
        category: Notification category:
            customer, ai, payment, system, security, subscription
        priority: Notification priority:
            low, normal, high, critical
    """

    try:
        category_obj = NotificationCategory.query.filter_by(
            name=category
        ).first()

        if not category_obj:
            return {
                "success": False,
                "error": f"Unknown category: {category}"
            }

        notification = Notifications(
            title=title,
            message=message,
            user_id=user_id,
            category_id=category_obj.id,
            priority=priority
        )

        db.session.add(notification)
        db.session.commit()

        return {
            "success": True,
            "notification_id": notification.id,
            "title": title,
            "category": category,
            "priority": priority
        }

    except Exception as e:
        db.session.rollback()

        logger.error(
            f"Error creating notification: {e}"
        )

        return {
            "success": False,
            "error": str(e)
        }
@tool
def save_notification(title: str, message: str, user_id: int) -> dict:
    """Save a notification to the database for later retrieval.

    Args:
        title: Short title of the notification.
        message: Full notification content.
        user_id: ID of the user to whom the notification belongs.
    """
    # TODO: save notification to database
    try:
        notification = Notifications(
                title=title,
                message=message,
                user_id=user_id
            )
        db.session.add(notification)
        db.session.commit()
        
        return {"success": True, "title": title, "message": message, "user_id": user_id}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving notification: {e}")
        return {"success": False, "error": str(e), "title": title, "message": message, "user_id": user_id}
        
    
    
    
@tool
def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body content (plain text or HTML).
    """
    # TODO: send via email provider (e.g. SendGrid, SES, SMTP)
    try:
        message = Mail(
                from_email=SENDGRID_FROM_EMAIL,
                to_emails=to,
                subject=subject,
                html_content=body
            )
            
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        if not SENDGRID_API_KEY:
            return {
                "success": False,
                "error": "SENDGRID_API_KEY missing."
            }
        
        response = sg.send(message)
            
        
        return {"success": True, "to": to, "subject": subject,
                "status_code": response.status_code, "body": response.body}
    
    except Exception as e:
        logger.error(f"Error sending email to {to}: {e}")
        return {"success": False, "error": str(e), "to": to, "subject": subject}
        
        

# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------

@tool
def search_faq(query: str, top_k: int = 3) -> dict:
    """Search the business's FAQ knowledge base for an answer to a customer
    question.

    Args:
        query: The customer's question or search terms.
        top_k: Number of top matching FAQ entries to return (default 3).
    """
    # TODO: query FAQ store (DB full-text search or vector search)
    return {"success": True, "query": query, "results": []}


@tool
def search_documents(query: str, top_k: int = 5) -> dict:
    """Search uploaded business documents (policies, brochures, manuals, etc.)
    for relevant passages using semantic search.

    Args:
        query: The search query.
        top_k: Number of top matching document chunks to return (default 5).
    """
    # TODO: query vector store (e.g. Pinecone, Chroma, pgvector) via embeddings
    return {"success": True, "query": query, "results": []}






# ---------------------------------------------------------------------------
# Tool registry — convenient for binding to an LLM or building a LangGraph ToolNode
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    # Business
    get_business_info,
    get_business_hours,
    get_services,
    save_customer,
    # Notifications
    notify_owner,
    send_email,
    save_notification,
    # Knowledge
    search_faq,
    search_documents
]