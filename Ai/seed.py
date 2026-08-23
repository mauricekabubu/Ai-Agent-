from app import app
from database.model import NotificationCategory, Notifications
from extensions.extension import db
import logging

logger = logging.getLogger(__name__)


def create_data():
    categories = [
        {
            "name": "customer",
            "description": "Customer messages and conversations"
        },
        {
            "name": "ai",
            "description": "AI agent events"
        },
        {
            "name": "payment",
            "description": "Payment related alerts"
        },
        {
            "name": "system",
            "description": "System errors and updates"
        },
        {
            "name": "security",
            "description": "Security alerts"
        },
        {
            "name": "subscription",
            "description": "Subscription and billing"
        }
    ]

    for item in categories:

        # prevent duplicates
        existing = NotificationCategory.query.filter_by(
            name=item["name"]
        ).first()

        if existing:
            continue

        category = NotificationCategory(**item)
        db.session.add(category)

    db.session.commit()

    print("Categories seeded successfully")
    
    
def create_notifications():
    try:
        notifications = [
            {
                "user_id":1,
                "category_id":1,
                "title":"Customer Request",
                "message":"Hi there Maurice i need a Point Of Sale system for my retail store.",
                "priority":"high",
                "read":False
            },
            {
                "user_id":1,
                "category_id":1,
                "title":"Class Update",
                "message":"Data structures class has been scheduled tommorrow at 8am",
                "priority":"critical",
                "read":False
            },
            {
                "user_id":1,
                "category_id":1,
                "title":"Date update",
                "message":"Hi Mambo Maurice umepotea xna i need us to have tyme to go for a date on weekend. Luv u Ella",
                "priority":"normal",
                "read":False
            },
            {
                "user_id":1,
                "category_id":1,
                "title":"Project update",
                "message":"Yooh mshenzi am done with the catalog Api",
                "priority":"normal",
                "read":False
            },
            {
                "user_id":1,
                "category_id":1,
                "title":"Birthday gift",
                "message":"Hope unakumbuka Ashley's Birthday present on Saturday",
                "priority":"high",
                "read":False
            }
        ]
        
        for item in notifications:
            existing_notification = Notifications.query.filter_by(
                user_id=item["user_id"],
                title=item["title"]
            ).first()
        
            if existing_notification:
                continue
            
            notification = Notifications(**item)
            db.session.add(notification)
            db.session.flush()
        
        db.session.commit()
        
        print("Notifications Successfully seeded")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Could not seed notifications: {e}")
        print(f"Error occured: {e}")
        
  


if __name__ == "__main__":
    with app.app_context():
        create_notifications()