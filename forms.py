from models.model import Users,db,Communities,Posts
from flask_login import login_required,current_user,login_manager
from flask import request, render_template, jsonify,Blueprint,url_for,current_app,redirect
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os

form_bp = Blueprint("forms",__name__)

#Image configurations 


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]




@form_bp.route("/upload",methods=["POST"])
def upload():
    image_file = request.files.get("image")
    
    try:
        if not image_file or image_file.filename == "":
            return jsonify(
                {
                    "error":"File not selected."
                }
            ),400
            
        extension = os.path.splitext(image_file.filename)[1].lower().lstrip(".")
        if extension not in current_app.config["ALLOWED_EXTENSIONS"]:
            return jsonify(
                {
                    "error":"Invalid image format"
                }
            ),400
        upload_dir = current_app.config["UPLOAD_DIRECTORY"]
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(image_file.filename)
        file_path  = os.path.join(upload_dir,filename)
        image_file.save(file_path)
        profile_filename = filename
        
        try:
            new_profile = Users(
                profile_img=profile_filename
            )
            db.session.add(new_profile)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            return jsonify(
                {
                    "error":f"{str(e)}"
                }
            ),500
            
            
        
        return jsonify(
            {
                "message":"File uploaded successfully"
            }
        ),200
        
    except RequestEntityTooLarge:
        return jsonify(
            {
                "error":"File exceeds 16MB"
            }
        ),413
           
    

#create a community api blueprint route
@form_bp.route("/community", methods=["POST"])
@login_required
def community():
    data = request.get_json() or {}

    name = data.get("name")
    description = data.get("description")
    whatsapp_link = data.get("whatsapp_link")  

    # Basic validations
    if not name or not description:
        return jsonify({"error": "Name and description are required"}), 400

    if whatsapp_link and not whatsapp_link.startswith("https://chat.whatsapp.com/"):
        return jsonify({"error": "Invalid WhatsApp group link"}), 400

    try:
        new_community = Communities(
            name=name,
            description=description,
            whatsapp_link=whatsapp_link,
            created_by=current_user.id
        )
        db.session.add(new_community)
        db.session.commit()

        return jsonify({
            "message": "Community created successfully",
            "community": {
                "id": new_community.id,
                "name": new_community.name,
                "description": new_community.description,
                "whatsapp_link": new_community.whatsapp_link,
                "created_by": new_community.created_by
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error creating a community: {e}")
        return jsonify({"error": "Failed to create community"}), 500

#Searching api
@form_bp.route("/search",methods=["GET"])
@login_required
def searching():
    query = request.args.get("q")
    
    try:
        if query:
            results = Communities.query.filter(or_(
                Communities.name.ilike(f"%{query}%"),
                Communities.description.ilike(f"%{query}%")
            )).all()
        
        else:
            results = Communities.query.all()
            
        return jsonify([
            {
                "id":c.id,
                "name":c.name,
                "description":c.description,
                "whatsapp_link": c.whatsapp_link
            }
            for c in results
        ]),200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(
            {
                "error":str(e)
            }
        ),500

@form_bp.route("/post", methods=["POST"])
@login_required
def post():
    # Detect request type
    if request.content_type and request.content_type.startswith("application/json"):
        data = request.get_json()
        title = data.get("title")
        content = data.get("content")
    else:
        title = request.form.get("title")
        content = request.form.get("content")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    if not content:
        return jsonify({"error": "Content is required"}), 400

    image_file = request.files.get("image")
    image_filename = None

    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)

        upload_folder = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        image_path = os.path.join(upload_folder, filename)
        image_file.save(image_path)

        image_filename = filename

    new_post = Posts(
        user_id=current_user.id,
        title=title,
        content=content,
        image=image_filename
    )

    try:
        db.session.add(new_post)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"error": "Failed to create post"}), 500

    print("UPLOAD FOLDER:", upload_folder)
    print("SAVING TO:", image_path)
    return jsonify({
        "message": "Post created successfully",
        "id": new_post.id,
        "image": image_filename
    }), 201
    
    