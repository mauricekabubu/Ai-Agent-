from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask import Blueprint, request, redirect, url_for, render_template, session, flash, current_app
from models.model import Users,db,FarmerProfile
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
import os
from flask_mail import Mail, Message

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    profile_img = request.files.get("profile_img")

    if profile_img:
        upload_dir = current_app.config["UPLOAD_DIRECTORY"]
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(profile_img.filename)
        file_path = os.path.join(upload_dir, filename)
        profile_img.save(file_path)

        user = current_user
        user.profile_img = filename
        db.session.commit()

        return {"message": "Upload successful"}, 200

    return {"error": "No file uploaded"}, 400


@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method =="POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            
            flash("You have been successfully logged in",category="success")
            
            if user.role == "farmer":
                return redirect(url_for("farmer_dash"))
            
            #elif user.role == "specialist":
                #return redirect(url_for("specialist_dashboard"))
            
            elif user.role == "customer":
                return redirect(url_for("farmer_dash"))
            

            return redirect(url_for("farmer_dash"))

        else:
            flash("Invalid username or password!",category="danger")
            return redirect(url_for("auth.login"))
    
            
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        full_names = request.form.get("full_names")
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        phone = request.form.get("phone")
        role = request.form.get("role")
        location = request.form.get("location")
        profile_img = request.files.get("profile_img")
        
        existing_user = Users.query.filter_by(username=username).first()
        existing_email = Users.query.filter_by(email=email).first()
        
        if existing_user and existing_email:
            flash("Account already exists with the above username or email!", category="danger")
            
            return redirect(url_for("auth.login"))

        if not full_names or not username or not password or not email or not phone or not role or not location or not profile_img:
            flash("All fields must be filled", "danger")
            return redirect(url_for("auth.register"))

        elif len(password) < 8:
            flash("Password must be at least 8 characters", "danger")
            return redirect(url_for("auth.register"))

        elif "@" not in email:
            flash("Invalid email", "danger")
            return redirect(url_for("auth.register"))

        elif len(username) < 4:
            flash("Username must be at least 4 characters", "danger")
            return redirect(url_for("auth.register"))


        else:
            filename = None

            if profile_img and profile_img.filename:
                try:
                    extension = os.path.splitext(profile_img.filename)[1].lower().lstrip(".")

                    if extension not in current_app.config["ALLOWED_EXTENSIONS"]:
                        flash("Invalid image format",category="danger")
                        return redirect(url_for("auth.register"))

                    
                    upload_dir = current_app.config["UPLOAD_DIRECTORY"]
                    os.makedirs(upload_dir, exist_ok=True)
                    filename = secure_filename(profile_img.filename)
                    file_path = os.path.join(upload_dir, filename)

                    profile_img.save(file_path)

                except RequestEntityTooLarge:
                    flash("File exceeds 16MB", "danger")
                    return redirect(url_for("auth.register"))
            
            new_user = Users(
            username=username,
            full_names=full_names,
            email=email,
            password=generate_password_hash(password),
            role=role,
            phone=phone,
            location=location,
            profile_img=filename
            )

            db.session.add(new_user)
            db.session.commit()

            flash(f"{new_user.username} account created successfully",category="success")

            return redirect(url_for("auth.form"))

    return render_template("register.html")

@auth_bp.route("/forgot_password",methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        user = Users.query.filter_by(email=email).first()
        
        if user and user.email:
            token = user.generate_reset_token()
            
            reset_link = url_for(
                "auth.reset_password",
                token=token,
                _external=True
            )
            
            msg = Message(
                subject="Password_reset",
                recipients=[user.email],
                body=f"""
                    Hello {user.username},
                    To reset your password, click the link below:
                    {reset_link}
                    This link will expire in 30 minutes.
                    If you did not request this, ignore this email.
                    """)
            mail = current_app.extensions["mail"]
            mail.send(msg)
            
            flash("A reset link has been successfully sent to your given email above.\n",category="success")
            
            return redirect(url_for("auth.login"))
        
        else:
            flash("Invalid email does not exist!",category="danger")
            
            return redirect(url_for("auth.forgot_password"))
        
    return render_template("forgot.html")
    

@auth_bp.route("/reset_password/<token>",methods=["GET","POST"])
def reset_password(token):
    user = Users.verify_reset_token(token)
    
    if not user:
        flash("Invalid or expired token!",category="danger")
        
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == "POST":
        password = request.form.get("password")
        password1 = request.form.get("password1")
        
        if password != password1:
            flash("Both passwords must match!",category="danger")
            
            return redirect(request.url)
        
        user.password = generate_password_hash(password)
        db.session.commit()
        
        flash("New password updated, you can now login!", category="success")
        
        return redirect(url_for("auth.login"))
    
    return render_template("reset.html",token=token)
                                

@auth_bp.route("/form",methods=["GET","POST"])
def form():
    if request.method=="POST":
        farm_name = request.form.get("farm_name")
        farm_size = request.form.get("farm_size")
        crops_grown = request.form.get("crops_grown")
        type_farmer = request.form.get("type_farmer")
        
        new_items = FarmerProfile(user_id=current_user.id,farm_name=farm_name,farm_size=farm_size,
                         crops_grown=crops_grown, type_farmer=type_farmer)
        db.session.add(new_items)
        db.session.commit()
        
        flash("Account created successfully", "success")
        
        return redirect(url_for("auth.login"))
    return render_template("form.html")


@auth_bp.route("/logout",methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out!",category="success")
    
    return redirect(url_for('index'))   
            
        
@auth_bp.route("/update_account", methods=["POST"])
@login_required
def update_account():
    data = request.get_json()

    if not data:
        return {"error": "No data received"}, 400

    full_names = data.get("full_names")
    username = data.get("username")
    email = data.get("email")

    #  Validation
    if not full_names or not username or not email:
        return {"error": "All fields are required"}, 400

    current_user.full_names = full_names
    current_user.username = username
    current_user.email = email

    db.session.commit()

    return {"message": "Account updated"}, 200
        
@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()

    if not data:
        return {"error": "No data received"}, 400

    old = data.get("old_password")
    new = data.get("new_password")
    confirm = data.get("confirm_password")

    if not old or not new or not confirm:
        return {"error": "All fields required"}, 400

    if not check_password_hash(current_user.password, old):
        return {"error": "Old password incorrect"}, 400

    if new != confirm:
        return {"error": "Passwords do not match"}, 400

    current_user.password = generate_password_hash(new)
    db.session.commit()

    return {"message": "Password updated"}, 200
    
@auth_bp.route("/update_location", methods=["POST"])
@login_required
def update_location():
    data = request.get_json()

    location = data.get("location")

    if not location:
        return {"error": "Location required"}, 400

    current_user.location = location
    db.session.commit()

    return {"message": "Location updated"}, 200
    
        