from flask import Flask, render_template
from dotenv import load_dotenv
from extensions.extension import db, login_manager, migrate
from auth.auth import auth_bp
from engine.agent import agent_bp
from database.model import User
from main.main import main_bp
import os

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app,db)

login_manager.login_view = "auth.login"
login_manager.login_message = "Please login first."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Blueprints registration
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(agent_bp, url_prefix="/agent")
app.register_blueprint(main_bp, url_prefix="/main")



@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=7000)