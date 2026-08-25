from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request, jsonify
from extensions.extension import db
from database.model import (
    User,
    Contact,
    Notifications,
    Business,
    Services,
    Message,
    NotificationCategory,
)
from flask_login import login_required, current_user
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime
from sqlalchemy import func, or_
import json


# ============================================================================
# CONFIGURATION
# ============================================================================

try:
    KENYA_TZ = ZoneInfo("Africa/Nairobi")
except ZoneInfoNotFoundError:
    KENYA_TZ = None


def kenya_now():
    return datetime.now(KENYA_TZ)


main_bp = Blueprint("main", __name__)

logger = logging.getLogger(__name__)


# ============================================================================
# GENERAL HELPERS
# ============================================================================

def json_error(message, status=400, error=None):
    payload = {"success": False, "message": message}
    if error:
        payload["error"] = str(error)
    return jsonify(payload), status


def json_success(message="Success", **data):
    payload = {"success": True, "message": message}
    payload.update(data)
    return jsonify(payload)


def wants_json():
    """True if the caller expects a JSON response rather than a redirect
    (fetch()/AJAX from the dashboard JS, or an explicit Accept header)."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept and "text/html" not in accept


# ============================================================================
# DEMO / FALLBACK DATA
# ============================================================================

def get_demo_docs():
    return [
        {"name": "Return Policy.pdf", "type": "Policy", "size": "240 KB", "uploaded": "2 days ago", "indexed": True},
        {"name": "Pricing 2026.pdf", "type": "Business", "size": "1.2 MB", "uploaded": "1 week ago", "indexed": True},
        {"name": "FAQ Sheet.pdf", "type": "FAQ", "size": "180 KB", "uploaded": "3 days ago", "indexed": False},
    ]


def get_demo_automations():
    return [
        {"name": "Auto-reply after hours", "desc": "Send an away message when a contact messages outside business hours.", "enabled": True, "lastRun": "10 min ago"},
        {"name": "Lead capture", "desc": "Save new contacts automatically when a phone number is not recognized.", "enabled": True, "lastRun": "1 hr ago"},
        {"name": "Escalation alert", "desc": "Notify the owner when a message contains urgent keywords.", "enabled": False, "lastRun": "2 days ago"},
        {"name": "Follow-up reminder", "desc": "Remind you to follow up with contacts after 48h of inactivity.", "enabled": True, "lastRun": "30 min ago"},
    ]


def get_demo_tools():
    return [
        {"name": "Sentiment analyzer", "desc": "Analyzes the emotional tone of incoming messages.", "status": "Active", "usage": 1240, "lastRun": "Just now"},
        {"name": "Language detector", "desc": "Detects the language of a message for routing.", "status": "Active", "usage": 890, "lastRun": "5 min ago"},
        {"name": "Appointment scheduler", "desc": "Lets customers book slots via conversation.", "status": "Active", "usage": 340, "lastRun": "12 min ago"},
        {"name": "Invoice generator", "desc": "Generates PDF invoices from conversation context.", "status": "Degraded", "usage": 56, "lastRun": "1 hr ago"},
    ]


def get_analytics_data():
    return {
        "volume_data": [
            {"d": "Mon", "v": 42}, {"d": "Tue", "v": 58}, {"d": "Wed", "v": 49},
            {"d": "Thu", "v": 72}, {"d": "Fri", "v": 65}, {"d": "Sat", "v": 30}, {"d": "Sun", "v": 24},
        ],
        "satisfaction_data": [
            {"name": "Satisfied", "value": 68, "color": "#10B981"},
            {"name": "Neutral", "value": 18, "color": "#F59E0B"},
            {"name": "Unsatisfied", "value": 14, "color": "#EF4444"},
        ],
        "response_time_data": [
            {"d": "Mon", "v": 4.2}, {"d": "Tue", "v": 3.8}, {"d": "Wed", "v": 5.1},
            {"d": "Thu", "v": 4.5}, {"d": "Fri", "v": 3.9}, {"d": "Sat", "v": 6.2}, {"d": "Sun", "v": 7.1},
        ],
        "tool_usage_data": [
            {"t": "Sentiment", "v": 1240}, {"t": "Scheduler", "v": 340},
            {"t": "Language", "v": 890}, {"t": "Invoice", "v": 56}, {"t": "Search", "v": 210},
        ],
        "top_questions": [
            {"q": "What are your business hours?", "count": 124},
            {"q": "How do I book an appointment?", "count": 98},
            {"q": "What is your pricing?", "count": 87},
            {"q": "Do you offer refunds?", "count": 64},
            {"q": "Where are you located?", "count": 52},
        ],
        "peak_hours": [
            {"h": "8am", "v": 12}, {"h": "9am", "v": 28}, {"h": "10am", "v": 45},
            {"h": "11am", "v": 38}, {"h": "12pm", "v": 52}, {"h": "1pm", "v": 41},
            {"h": "2pm", "v": 35}, {"h": "3pm", "v": 48}, {"h": "4pm", "v": 30},
            {"h": "5pm", "v": 22}, {"h": "6pm", "v": 15}, {"h": "7pm", "v": 8},
        ],
    }


def get_ai_activities():
    return [
        "Talking with Emma Sinclair",
        "Indexing knowledge base",
        "Analyzing sentiment for John Doe",
        "Waiting for new messages",
        "Generating invoice for Acme Corp",
    ]


# ============================================================================
# SERIALIZATION HELPERS
# ============================================================================

def serialize_business(business):
    if not business:
        return None
    return {
        "id": business.id,
        "business_name": getattr(business, "business_name", "") or "",
        "business_description": getattr(business, "business_description", "") or "",
        "business_email": getattr(business, "business_email", "") or "",
        "business_phone": getattr(business, "business_phone", "") or "",
        "business_location": getattr(business, "business_location", "") or "",
        "business_hours": getattr(business, "business_hours", "") or "",
        "logo_url": getattr(business, "logo_url", "") or "",
        "greeting_message": getattr(business, "greeting_message", "") or "",
        "away_message": getattr(business, "away_message", "") or "",
        "tone": getattr(business, "tone", "") or "",
    }


def serialize_user(user):
    if not user:
        return None
    return {
        "id": user.id,
        "username": getattr(user, "username", "") or "",
        "email": getattr(user, "email", "") or "",
        "phone": getattr(user, "phone", "") or "",
    }


def serialize_contact(contact):
    if not contact:
        return None
    return {
        "id": contact.id,
        "name": getattr(contact, "name", "") or "",
        "phone": getattr(contact, "phone", "") or "",
        "email": getattr(contact, "email", "") or "",
        "category": getattr(contact, "category", "") or "General",
        "notes": getattr(contact, "notes", "") or "",
        "created_at": contact.created_at.isoformat() if getattr(contact, "created_at", None) else None,
    }


def serialize_notification(notification):
    if not notification:
        return None
    priority = getattr(notification, "priority", "normal") or "normal"
    icon_map = {"critical": "fa-triangle-exclamation", "high": "fa-bell", "normal": "fa-circle-info"}
    tone_map = {"critical": "red", "high": "amber", "normal": "indigo"}
    return {
        "id": notification.id,
        "title": getattr(notification, "title", "") or "",
        "desc": getattr(notification, "description", "") or "",
        "priority": priority,
        "type": priority.capitalize(),
        "tone": tone_map.get(priority, "indigo"),
        "icon": icon_map.get(priority, "fa-circle-info"),
        "time": notification.created_at.strftime("%b %d, %Y %I:%M %p") if getattr(notification, "created_at", None) else "",
    }


# ============================================================================
# CONTACT DATA
# ============================================================================

def build_contacts_data(user_id):
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.created_at.desc()).all()
    result = []
    for contact in contacts:
        conversation_id = getattr(contact, "conversation_id", None)
        convo_count = 0
        if hasattr(Message, "conversation_id") and conversation_id is not None:
            convo_count = Message.query.filter(Message.conversation_id == conversation_id).count()
        result.append({
            "id": contact.id,
            "name": contact.name,
            "phone": contact.phone,
            "email": getattr(contact, "email", "") or "—",
            "firstContact": contact.created_at.strftime("%b %d, %Y") if getattr(contact, "created_at", None) else "—",
            "lastSeen": "Just now",
            "conversations": convo_count,
            "tags": [contact.category] if getattr(contact, "category", None) else ["General"],
            "status": "Active",
            "category": getattr(contact, "category", None) or "General",
        })
    return result


# ============================================================================
# CONVERSATION DATA
# ============================================================================

def build_conversations_data(user_id):
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.created_at.desc()).all()
    conversations = []
    messages_by_convo = {}

    for index, contact in enumerate(contacts[:50], start=1):
        contact_conversation_id = getattr(contact, "conversation_id", None)
        latest = None
        if hasattr(Message, "conversation_id") and contact_conversation_id is not None:
            latest = (
                Message.query.filter(Message.conversation_id == contact_conversation_id)
                .order_by(Message.created_at.desc()).first()
            )

        conversation_id = contact_conversation_id or contact.id

        conversations.append({
            "id": conversation_id,
            "name": contact.name,
            "phone": contact.phone,
            "email": getattr(contact, "email", "") or "—",
            "tags": [contact.category] if getattr(contact, "category", None) else ["General"],
            "source": "AI" if index % 2 == 0 else "Human",
            "lastMessage": latest.content if latest else "No messages yet.",
            "time": latest.created_at.strftime("%I:%M %p") if latest else "—",
            "unread": 0,
            "status": "Open" if index % 3 == 0 else "Waiting" if index % 3 == 1 else "Resolved",
            "summary": f"Latest interaction with {contact.name} regarding general inquiries.",
            "notes": getattr(contact, "notes", "") or "",
        })

        msgs = []
        if hasattr(Message, "conversation_id"):
            msgs = Message.query.filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

        if msgs:
            messages_by_convo[str(conversation_id)] = [
                {
                    "sender": "customer" if m.sender == "contact" else "ai",
                    "text": m.content,
                    "time": m.created_at.strftime("%I:%M %p") if m.created_at else "—",
                }
                for m in msgs[-50:]
            ]
        else:
            messages_by_convo[str(conversation_id)] = [
                {"sender": "customer", "text": f"Initial message from {contact.name}.", "time": "9:00 AM"},
                {"sender": "ai", "text": f"Hi {contact.name}, thanks for reaching out! How can I help?", "time": "9:01 AM"},
            ]

    return conversations, messages_by_convo


# ============================================================================
# NOTIFICATION DATA
# ============================================================================

def build_notifications_data(user_id, category=None):
    query = Notifications.query.filter_by(user_id=user_id)
    if category and category.lower() != "all":
        query = query.filter(Notifications.priority == category.lower())
    notifications = query.order_by(Notifications.created_at.desc()).all()
    return [serialize_notification(n) for n in notifications]


# ============================================================================
# CORE DASHBOARD DATA (business logic — DB-facing, JSON-agnostic)
# ============================================================================

def build_dashboard_data(user_id, notif_category=None):
    """Everything the dashboard needs, as plain Python objects."""
    today = kenya_now().replace(hour=0, minute=0, second=0, microsecond=0)
    conversation_id = getattr(current_user, "conversation_id", None)

    todays_messages_count = 0
    if conversation_id:
        todays_messages_count = Message.query.filter(
            Message.conversation_id == conversation_id, Message.created_at >= today
        ).count()

    auto_replies_count = Message.query.filter(
        Message.sender == "ai", Message.created_at >= today
    ).count()

    important_count = Notifications.query.filter(
        Notifications.user_id == user_id,
        Notifications.priority.in_(["critical", "high"]),
        Notifications.created_at >= today,
    ).count()

    new_contacts_count = Contact.query.filter(
        Contact.user_id == user_id, Contact.created_at >= today
    ).count()

    avg_response = (
        db.session.query(func.avg(Message.response_time))
        .filter(Message.sender == "ai", Message.response_time.isnot(None))
        .scalar()
    )

    stats_data = [
        {"icon": "fa-comment-dots", "label": "Today's conversations", "value": str(todays_messages_count), "tone": "indigo"},
        {"icon": "fa-paper-plane", "label": "Auto replies sent", "value": str(auto_replies_count), "tone": "green"},
        {"icon": "fa-flag", "label": "Important notifications", "value": str(important_count), "tone": "amber"},
        {"icon": "fa-user-plus", "label": "New contacts saved", "value": str(new_contacts_count), "tone": "indigo"},
        {"icon": "fa-clock", "label": "Avg. response time", "value": f"{round(avg_response or 0, 1)}s", "tone": "green"},
    ]

    contacts = build_contacts_data(user_id)
    notifications = build_notifications_data(user_id, notif_category)
    conversations, messages_by_convo = build_conversations_data(user_id)
    analytics = get_analytics_data()
    business = Business.query.filter_by(user_id=user_id).first()

    return {
        "user": current_user,
        "business": business,
        "stats": stats_data,
        "contacts": contacts,
        "notifications": notifications,
        "conversations": conversations,
        "messages_by_convo": messages_by_convo,
        "docs": get_demo_docs(),
        "automations": get_demo_automations(),
        "tools": get_demo_tools(),
        "analytics": analytics,
        "ai_activities": get_ai_activities(),
    }


# ============================================================================
# TEMPLATE ADAPTER
#
# dashboard.html (current version) renders its data client-side from JSON
# blobs (`{{ stats_json | safe }}`, etc.) rather than server-side Jinja
# loops. This adapter turns the plain-Python payload from
# build_dashboard_data() into that shape, so the existing template renders
# correctly without a full template rewrite. If/when dashboard.html moves
# to server-rendered Jinja loops (per the UX refactor spec), this adapter
# can be deleted and get_dashboard_context() can pass the raw objects
# straight through instead.
# ============================================================================

def get_dashboard_context(user_id, active_view="dashboard", notif_category=None):
    data = build_dashboard_data(user_id, notif_category)
    analytics = data["analytics"]

    return {
        "current_user": current_user,
        "business": data["business"],
        "notifications": data["notifications"],
        "active_view": active_view,
        "notif_filter": notif_category or "All",

        "stats_json": json.dumps(data["stats"]),
        "contacts_json": json.dumps(data["contacts"]),
        "notifications_json": json.dumps(data["notifications"]),
        "conversations_json": json.dumps(data["conversations"]),
        "messages_by_convo_json": json.dumps(data["messages_by_convo"]),
        "docs_json": json.dumps(data["docs"]),
        "automations_json": json.dumps(data["automations"]),
        "tools_json": json.dumps(data["tools"]),
        "volume_data_json": json.dumps(analytics["volume_data"]),
        "satisfaction_data_json": json.dumps(analytics["satisfaction_data"]),
        "response_time_data_json": json.dumps(analytics["response_time_data"]),
        "tool_usage_data_json": json.dumps(analytics["tool_usage_data"]),
        "top_questions_json": json.dumps(analytics["top_questions"]),
        "peak_hours_json": json.dumps(analytics["peak_hours"]),
        "ai_activities_json": json.dumps(data["ai_activities"]),
    }


def render_dashboard(active_view="dashboard", notif_category=None):
    """Shared renderer used by every page route so they all stay in sync."""
    try:
        ctx = get_dashboard_context(current_user.id, active_view, notif_category)
        return render_template("dashboard.html", **ctx)
    except Exception as e:
        db.session.rollback()
        logger.exception("Error building dashboard context")
        flash("Something went wrong loading the dashboard.", "danger")
        # Render a minimal fallback rather than looping back through the
        # same failing context-builder.
        return render_template(
            "dashboard.html",
            current_user=current_user,
            business=None,
            notifications=[],
            active_view="dashboard",
            notif_filter="All",
            stats_json="[]", contacts_json="[]", notifications_json="[]",
            conversations_json="[]", messages_by_convo_json="{}", docs_json="[]",
            automations_json="[]", tools_json="[]", volume_data_json="[]",
            satisfaction_data_json="[]", response_time_data_json="[]",
            tool_usage_data_json="[]", top_questions_json="[]", peak_hours_json="[]",
            ai_activities_json="[]",
        ), 200


# ============================================================================
# PAGE ROUTES  (all render the same dashboard.html, just with a different
# active_view / notif_filter so the right tab opens on load)
# ============================================================================

@main_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_dashboard("dashboard")


@main_bp.route("/inbox", methods=["GET"])
@login_required
def inbox():
    return render_dashboard("inbox")


@main_bp.route("/contacts", methods=["GET"])
@login_required
def view_contacts():
    return render_dashboard("contacts")


@main_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    return render_dashboard("profile")


@main_bp.route("/business", methods=["GET"])
@login_required
def business():
    return render_dashboard("settings")


@main_bp.route("/notifications/<category_name>", methods=["GET"])
@login_required
def notifications_by_category(category_name):
    return render_dashboard("notifications", notif_category=category_name)


# ============================================================================
# FORM-POST ROUTES  (used by the plain <form> tags in dashboard.html —
# always redirect back to /dashboard with a flash message, never to a
# separate page)
# ============================================================================

@main_bp.route("/edit_business/<int:user_id>", methods=["POST"])
@login_required
def edit_business(user_id):
    try:
        business = Business.query.filter_by(user_id=current_user.id).first()
        if not business:
            business = Business(user_id=current_user.id)
            db.session.add(business)

        fields = [
            "business_name", "business_description", "business_email",
            "business_phone", "business_location", "business_hours",
            "logo_url", "greeting_message", "away_message", "tone",
        ]
        for field in fields:
            if field in request.form:
                value = request.form.get(field, "")
                setattr(business, field, value.strip() if isinstance(value, str) else value)

        db.session.commit()
        flash("Business updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to edit business")
        flash("Failed to update business.", "danger")

    return redirect(url_for("main.dashboard"))


@main_bp.route("/edit_profile/<int:user_id>", methods=["POST"])
@login_required
def edit_profile(user_id):
    try:
        user = User.query.get_or_404(user_id)
        user.username = request.form.get("username", user.username).strip()
        user.email = request.form.get("email", user.email).strip()
        user.phone = request.form.get("phone", user.phone).strip()
        db.session.commit()
        flash("Profile updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to edit profile")
        flash("Failed to update profile.", "danger")

    return redirect(url_for("main.dashboard"))


@main_bp.route("/add_contact/<int:user_id>", methods=["POST"])
@login_required
def add_contact(user_id):
    try:
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        category = (request.form.get("category") or "General").strip()

        if not name or not phone:
            flash("Name and phone number are required.", "danger")
            return redirect(url_for("main.dashboard"))

        existing = Contact.query.filter_by(phone=phone, user_id=current_user.id).first()
        if existing:
            flash("This contact already exists.", "warning")
            return redirect(url_for("main.dashboard"))

        contact = Contact(name=name, phone=phone, category=category, user_id=current_user.id)
        db.session.add(contact)
        db.session.commit()
        flash("Contact added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to add contact")
        flash("Something went wrong adding the contact.", "danger")

    return redirect(url_for("main.dashboard"))


@main_bp.route("/delete_contact/<int:contact_id>", methods=["POST"])
@login_required
def delete_contact_page(contact_id):
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            flash("Contact not found.", "danger")
        else:
            db.session.delete(contact)
            db.session.commit()
            flash("Contact deleted.", "success")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete contact")
        flash("Failed to delete contact.", "danger")

    return redirect(url_for("main.dashboard"))


@main_bp.route("/notifications/<int:notification_id>/dismiss", methods=["POST", "DELETE"])
@login_required
def dismiss_notification_page(notification_id):
    """Non-AJAX fallback: deletes and redirects with a flash toast."""
    try:
        n = Notifications.query.filter_by(id=notification_id, user_id=current_user.id).first()
        if n:
            db.session.delete(n)
            db.session.commit()
            flash("Notification dismissed.", "success")
        else:
            flash("Notification not found.", "warning")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to dismiss notification")
        flash("Couldn't dismiss that notification.", "danger")

    if wants_json():
        return json_success("Notification dismissed.")
    return redirect(url_for("main.dashboard"))


# ============================================================================
# JSON API (used by dashboard.html's fetch() calls — modals, toggles, etc.)
# ============================================================================

@main_bp.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard_api():
    try:
        data = build_dashboard_data(current_user.id)
        data["business"] = serialize_business(data["business"])
        data["user"] = serialize_user(data["user"])
        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to load dashboard data")
        return json_error("Failed to load dashboard data.", 500, e)


@main_bp.route("/api/me", methods=["GET"])
@login_required
def get_current_user():
    return jsonify({"success": True, "user": serialize_user(current_user)})


@main_bp.route("/api/business", methods=["GET"])
@login_required
def get_business():
    business = Business.query.filter_by(user_id=current_user.id).first()
    return jsonify({"success": True, "business": serialize_business(business)})


@main_bp.route("/api/business", methods=["PATCH", "POST"])
@login_required
def update_business():
    try:
        business = Business.query.filter_by(user_id=current_user.id).first()
        if not business:
            business = Business(user_id=current_user.id)
            db.session.add(business)

        data = request.get_json(silent=True) or {}
        fields = [
            "business_name", "business_description", "business_email",
            "business_phone", "business_location", "business_hours",
            "logo_url", "greeting_message", "away_message", "tone",
        ]
        for field in fields:
            if field in data:
                value = data[field]
                setattr(business, field, value.strip() if isinstance(value, str) else value)

        db.session.commit()
        return json_success("Business information saved.", business=serialize_business(business))
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update business")
        return json_error("Failed to update business.", 500, e)


@main_bp.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    return jsonify({"success": True, "user": serialize_user(current_user)})


@main_bp.route("/api/profile", methods=["PATCH", "POST"])
@login_required
def update_profile():
    try:
        data = request.get_json(silent=True) or {}
        if "username" in data:
            current_user.username = (data["username"] or "").strip()
        if "email" in data:
            current_user.email = (data["email"] or "").strip()
        if "phone" in data:
            current_user.phone = (data["phone"] or "").strip()
        db.session.commit()
        return json_success("Profile updated successfully.", user=serialize_user(current_user))
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update profile")
        return json_error("Failed to update profile.", 500, e)


@main_bp.route("/api/contacts", methods=["GET"])
@login_required
def get_contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.created_at.desc()).all()
    return jsonify({"success": True, "contacts": [serialize_contact(c) for c in contacts]})


@main_bp.route("/api/contacts", methods=["POST"])
@login_required
def create_contact():
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()
        category = (data.get("category") or "General").strip()
        email = (data.get("email") or "").strip()
        notes = (data.get("notes") or "").strip()

        if not name or not phone:
            return json_error("Name and phone number are required.", 400)

        existing = Contact.query.filter_by(phone=phone, user_id=current_user.id).first()
        if existing:
            return json_error("This contact already exists.", 409)

        contact = Contact(name=name, phone=phone, category=category, user_id=current_user.id)
        if hasattr(contact, "email"):
            contact.email = email
        if hasattr(contact, "notes"):
            contact.notes = notes

        db.session.add(contact)
        db.session.commit()
        return json_success("Contact added successfully.", contact=serialize_contact(contact))
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to create contact")
        return json_error("Failed to add contact.", 500, e)


@main_bp.route("/api/contacts/<int:contact_id>", methods=["GET"])
@login_required
def get_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        return json_error("Contact not found.", 404)
    return jsonify({"success": True, "contact": serialize_contact(contact)})


@main_bp.route("/api/contacts/<int:contact_id>", methods=["PATCH", "POST"])
@login_required
def update_contact(contact_id):
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return json_error("Contact not found.", 404)

        data = request.get_json(silent=True) or {}
        for field in ["name", "phone", "email", "category", "notes"]:
            if field in data and hasattr(contact, field):
                value = data[field]
                setattr(contact, field, value.strip() if isinstance(value, str) else value)

        db.session.commit()
        return json_success("Contact updated successfully.", contact=serialize_contact(contact))
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to update contact")
        return json_error("Failed to update contact.", 500, e)


@main_bp.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
@login_required
def delete_contact(contact_id):
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return json_error("Contact not found.", 404)
        db.session.delete(contact)
        db.session.commit()
        return json_success("Contact deleted successfully.")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete contact")
        return json_error("Failed to delete contact.", 500, e)


@main_bp.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    try:
        category = request.args.get("category", "All")
        notifications = build_notifications_data(current_user.id, category)
        return jsonify({"success": True, "notifications": notifications, "category": category})
    except Exception as e:
        logger.exception("Failed to load notifications")
        return json_error("Failed to load notifications.", 500, e)


@main_bp.route("/api/notifications/<int:notification_id>", methods=["DELETE", "POST"])
@login_required
def delete_notification(notification_id):
    try:
        notification = Notifications.query.filter_by(id=notification_id, user_id=current_user.id).first()
        if not notification:
            return json_error("Notification not found.", 404)
        db.session.delete(notification)
        db.session.commit()
        return json_success("Notification dismissed.")
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete notification")
        return json_error("Failed to dismiss notification.", 500, e)


@main_bp.route("/api/conversations", methods=["GET"])
@login_required
def get_conversations():
    try:
        conversations, messages = build_conversations_data(current_user.id)
        return jsonify({"success": True, "conversations": conversations, "messages": messages})
    except Exception as e:
        logger.exception("Failed to load conversations")
        return json_error("Failed to load conversations.", 500, e)


@main_bp.route("/api/analytics", methods=["GET"])
@login_required
def analytics():
    return jsonify({"success": True, "analytics": get_analytics_data()})


@main_bp.route("/api/knowledge", methods=["GET"])
@login_required
def knowledge():
    return jsonify({"success": True, "documents": get_demo_docs()})


@main_bp.route("/api/automations", methods=["GET"])
@login_required
def automations():
    return jsonify({"success": True, "automations": get_demo_automations(), "tools": get_demo_tools()})


@main_bp.route("/api/ai/activity", methods=["GET"])
@login_required
def ai_activity():
    return jsonify({"success": True, "activities": get_ai_activities()})


@main_bp.route("/api/message-stats", methods=["GET"])
@login_required
def message_stats():
    try:
        conversation_id = getattr(current_user, "conversation_id", None)
        today = kenya_now().replace(hour=0, minute=0, second=0, microsecond=0)
        if not conversation_id:
            return jsonify([])

        results = (
            db.session.query(
                func.extract("hour", Message.created_at).label("hour"),
                Message.sender,
                func.count(Message.id).label("count"),
            )
            .filter(Message.conversation_id == conversation_id, Message.created_at >= today)
            .group_by(func.extract("hour", Message.created_at), Message.sender)
            .all()
        )
        data = [{"hour": int(hour), "sender": sender, "count": count} for hour, sender, count in results]
        return jsonify(data)
    except Exception as e:
        logger.exception("Failed to load message statistics")
        return json_error("Failed to load message statistics.", 500, e)


@main_bp.route("/api/response-time", methods=["GET"])
@login_required
def response_time():
    try:
        result = (
            db.session.query(func.avg(Message.response_time))
            .filter(Message.sender == "ai", Message.response_time.isnot(None))
            .scalar()
        )
        return jsonify({"success": True, "average_response_seconds": round(result or 0, 2)})
    except Exception as e:
        logger.exception("Failed to load response time")
        return json_error("Failed to load response time.", 500, e)