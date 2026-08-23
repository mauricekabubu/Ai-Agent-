from flask import Blueprint, request, url_for, render_template, redirect, flash, session
from flask_login import login_required, LoginManager, login_user, logout_user
from dotenv import load_dotenv
from database.model import User, Business, Services
from werkzeug.security import check_password_hash, generate_password_hash
from extensions.extension import db
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)


auth_bp = Blueprint("auth",__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("index.html")

    try:
        username = request.form.get("username", "").strip()
        password = request.form.get("password")

        # Find the admin in the database
        existing_user = User.query.filter_by(username=username).first()

        if existing_user is None:
            flash("Invalid username or password.", category="danger")
            return redirect(url_for("auth.login"))

        # Verify password
        if not check_password_hash(existing_user.password, password):
            flash("Invalid username or password.", category="danger")
            return redirect(url_for("auth.login"))

        # Login user
        login_user(existing_user)

        flash("Login successful.", category="success")

        return redirect(url_for("main.dashboard"))

    except Exception as e:
        logger.error(f"Login failed: {e}")
        flash(f"Login failed: {e}", category="danger")
        return redirect(url_for("auth.login"))
            

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    try:
        #user details for registration
        username =  request.form.get("username", "").strip()
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        email = request.form.get("email","").strip()
        phone = request.form.get("phone")
        
        # Checking missing fields
        if not username or not password or not phone or not email:
            flash("All fields are required.", category="danger")
            return redirect(url_for("auth.register"))
        
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", category="danger")
            return redirect(url_for("auth.register"))
        
        elif "@" not in email or "." not in email:
            flash("Invalid email address.", category="danger")
            return redirect(url_for("auth.register"))
        
        elif password != password_confirm:
            flash("Passwords do not match.", category="danger")
            return redirect(url_for("auth.register"))
        
        elif phone and not phone.isdigit():
            flash("Phone number must contain only digits.", category="danger")
            return redirect(url_for("auth.register"))
        
        elif phone.isdigit() and len(phone) < 10:
            flash("Phone number must be at least 10 digits long.", category="danger")
            return redirect(url_for("auth.register"))
        
            
        # Check if the username or phone number already exists
        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email) |
            (User.phone == phone)
        ).first()
        
        if existing_user:
            flash("Username already exists. Please choose a different username.", category="danger")
            return redirect(url_for("auth.register"))
    
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            email=email,
            phone=phone
        )
        db.session.add(new_user)
        db.session.flush()
        
        # Business Details Registration
        business_name = request.form.get("business_name","").strip()
        business_description = request.form.get("business_description")
        business_email = request.form.get("business_email","").strip()
        business_phone = request.form.get("business_phone")
        business_location = request.form.get("business_location")
        business_hours = request.form.get("business_hours")
        
        #Checking missing fields
        if not business_name or not business_phone or not business_email or not business_location:
            flash("All business fields are required.", category="danger")
            return redirect(url_for("auth.register"))
        
        # Validating business email and phone number    
        elif "@" not in business_email or "." not in business_email:
            flash("Invalid business email address.", category="danger")
            return redirect(url_for("auth.register"))
        
        elif business_phone and not business_phone.isdigit():
            flash("Business phone number must contain only digits.", category="danger")
            return redirect(url_for("auth.register"))
        
        
        elif business_phone.isdigit() and len(business_phone) < 10:
            flash("Business phone number must be at least 10 digits long.", category="danger")
            return redirect(url_for("auth.register"))
        
        new_business = Business(
            user_id=new_user.id,
            business_name=business_name,
            business_description=business_description,
            business_email=business_email,
            business_phone=business_phone,
            business_location=business_location,
            business_hours=business_hours,
            greeting_message=request.form.get("greeting_message"),
            away_message=request.form.get("away_message"),
            tone=request.form.get("tone"),
            response_length=request.form.get("response_length"),
            auto_reply=request.form.get("auto_reply") == "true",
            notifications=request.form.get("notifications")
        )    
        db.session.add(new_business)
        db.session.flush()
        
        # Services Details Registration
        services = []

        index = 0

        while True:
            name = request.form.get(f"service_name_{index}")

            if not name:
                break

            services.append(
                Services(
                    business_id=new_business.id,
                    service_name=name,
                    description=request.form.get(f"service_desc_{index}"),
                    price=request.form.get(f"service_price_{index}"),
                    website=request.form.get(f"service_website_{index}"),
                    socials=request.form.get(f"service_social_{index}")
                )
            )

            index += 1

        db.session.add_all(services)
        db.session.commit()
        
        return redirect(url_for("auth.login"))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed: {e}")
        flash(f"Registration failed: {e}", category="danger")
        return redirect(url_for("auth.register"))
    
        

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()

    flash("Logged out successfully.", category="success")

    return redirect(url_for("auth.login"))
            
            
            
@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    pass

    

