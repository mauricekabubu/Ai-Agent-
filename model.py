from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from flask import current_app



db = SQLAlchemy()

# USERS TABLE
class Users(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_names = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    phone = db.Column(db.String(50))
    role = db.Column(db.String(100), nullable=False)

    profile_img = db.Column(db.String(200),default="Ai.avif")
    location = db.Column(db.String(200))

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # RELATIONSHIPS
    farmer_profile = db.relationship("FarmerProfile", backref="user", uselist=False)
    specialist_profile = db.relationship("SpecialistProfile", backref="user", uselist=False)

    communities = db.relationship("Communities", backref="user", lazy=True)
    posts = db.relationship("Posts", backref="user", lazy=True)

    blog_posts = db.relationship("BlogPost", backref="user", lazy=True)

    cart_items = db.relationship("CartItem", backref="user", lazy=True)

    products = db.relationship("Products", backref="user", lazy=True)

    orders = db.relationship("Orders", backref="user", lazy=True)

    ai_chat_history = db.relationship("AiChatHistory", backref="user", lazy=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    
    def generate_reset_token(self,expires_secs=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id":self.id}, salt="password-reset")
    
    @staticmethod
    def verify_reset_token(token, expire_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        
        try:
            data = s.loads(
                token,
                salt="password-reset",
                max_age=expire_sec
            )
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
        
        return Users.query.get(data["user_id"])

    def __repr__(self):
        return f"<user>{self.username},{self.email}"


# FARMER PROFILE
class FarmerProfile(db.Model):
    __tablename__ = "farmer_profile"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    farm_name = db.Column(db.String(200))
    farm_size = db.Column(db.Float)
    crops_grown = db.Column(db.Text)
    type_farmer = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# SPECIALIST PROFILE
class SpecialistProfile(db.Model):
    __tablename__ = "specialist_profile"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    experience = db.Column(db.Integer, nullable=False)
    certification = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# COMMUNITIES
class Communities(db.Model):
    __tablename__ = "communities"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    whatsapp_link = db.Column(db.Text, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Posts", backref="community", lazy=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# COMMUNITY POSTS
class Posts(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)

    community_id = db.Column(db.Integer, db.ForeignKey("communities.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    image = db.Column(db.String(200), nullable=False)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# BLOG POSTS
class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)

    image_url = db.Column(db.String(200))

    published = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# PRODUCTS
class Products(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    price = db.Column(db.Float, nullable=False)

    quantity = db.Column(db.Integer)

    image_url = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cart_items = db.relationship("CartItem", backref="product", lazy=True)
    order_items = db.relationship("OrderItems", backref="product", lazy=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# CART ITEMS
class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id'),)

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))

    quantity = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# ORDERS
class Orders(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    total_price = db.Column(db.Float)

    status = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship("OrderItems", backref="order", lazy=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# ORDER ITEMS
class OrderItems(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    quantity = db.Column(db.Integer)

    price = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


# MESSAGES
class Messages(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    message = db.Column(db.Text)

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


# AI CHAT HISTORY
class AiChatHistory(db.Model):
    __tablename__ = "ai_chat_history"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    question = db.Column(db.Text)

    response = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    