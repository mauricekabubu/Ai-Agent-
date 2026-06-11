from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.model import Users, db, Communities, Posts
from auths.auth import auth_bp
from files.api import api_bp
from files.forms import form_bp
from flask_login import LoginManager,current_user, login_required
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_mail import Mail,Message
from sendgrid import SendGridAPIClient, SendGridException


load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"


#App factory function
def create_app():
    #Flask app initialization
    app = Flask(__name__)   
    
    #Blueprints registration
    app.register_blueprint(auth_bp, url_prefix="/auth")   
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(form_bp,url_prefix="/forms")
    
    #Flask_migrate configurations
    migrate = Migrate()
    
    
    #Secret Key configurations
    app.config["SECRET_KEY"]= os.getenv("SECRET_KEY")

    
    #Database configurations 
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///farmhub.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False

    #Mail configuration for sending emails
    # ================= MAIL CONFIG =================
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = os.getenv("DEL_EMAIL")
    app.config["MAIL_PASSWORD"] = os.getenv("PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("SENDGRID_SENDER")
    
    mail = Mail(app)
        
    #Database initialization 
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app,db)
    
    
    @login_manager.user_loader
    def loader(user_id):
        return Users.query.get(int(user_id))

    
    #Image files configurations and allowed size and extensions
    app.config["UPLOAD_DIRECTORY"] = os.path.join("static", "uploads") 
    app.config["MAX_CONTENT_LENGTH"]= 16*1024*1024 #16MB
    app.config["ALLOWED_EXTENSIONS"]= ["png","jpg","webp","jfif","avif","jpeg","gif"]


    #index page route
    @app.route('/')
    def index():
        return render_template("index.html")

    #About us route
    @app.route("/about", methods=["POST", "GET"])
    def about():
        return render_template("about.html")

    #Contact us route
    @app.route("/contact",methods=["POST", "GET"])
    def contact():
        
        return render_template("contact.html")

    #Blog route
    @app.route("/blog", methods=["POST", "GET"])
    def blog():
        posts = Posts.query.all()
        
        return render_template("blog.html",posts=posts)

    #Market route
    @app.route("/market",methods=["POST","GET"])
    def market():
        return render_template("market.html")

    #Market listing route
    @app.route("/market_listing", methods=["POST","GET"])
    def market_listing():
        return render_template("market_listing.html")
    
    #Dashboards
    @app.route("/farmers",methods=["GET","POST"])
    @login_required
    def farmer_dash():
        return render_template("quick_stats.html")
    
    
    @app.route("/specialists",methods=["POST","GET"])
    def specialist_dash():
        return render_template("specialist.html")
      
    
    @app.route("/market_farm",methods=["GET","POST"])
    @login_required
    def market_farm():
        return render_template("market_farm.html")
    
    @app.route("/farmhub_ai",methods=["GET","POST"])
    @login_required
    def farmhub_ai():
        return render_template("farmhub_AI.html")
    
    
    @app.route("/communities",methods=["GET","POST"])
    @login_required
    def communities():
        all_communities = Communities.query.all()
        return render_template("community.html",all_communities=all_communities)
    
    
    @app.route("/inbox",methods=["GET","POST"])
    @login_required
    def inbox():
        return render_template("inbox.html")
    
    @app.route("/profile",methods=["POST","GET"])
    @login_required
    def profile():
        user = Users.query.all()
        
        return render_template("profile.html",user=current_user)
    
    @app.route("/settings",methods=["POST","GET"])
    @login_required
    def settings():
        return render_template("settings.html")
    
    
    return app


