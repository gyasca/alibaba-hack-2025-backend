from flask import Flask, request, jsonify
from flask_cors import CORS
from extensions import db
from flask_jwt_extended import JWTManager
from sqlalchemy import inspect
import logging
from config import Config
from database.init_db import init_db
from routes.skin_analysis import skin_analysis_bp
from models.skin_analysis import SkinAnalysis
from migrations.create_skin_analyses import create_skin_analyses_table
from migrations.add_annotated_image import add_annotated_image_column

from flask import send_from_directory
import os
from nanoid import generate  # Import nanoid
from flask_jwt_extended import JWTManager

from models.ingredient import populate_ingredients


app = Flask(__name__, static_folder='uploads')
# cors = CORS(app, resources={
#     r"/*": {
#         "origins": ["http://localhost:3000", "http://localhost:5173"],
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type"]
#     }
# })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    
    # Your chat logic here
    response = {
        'message': f"I received your message: {message}"
    }
    
    return jsonify(response)
# Configurations
app.config.from_object(Config)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
cors = CORS()
cors.init_app(app)
jwt = JWTManager(app)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Import and register Blueprints
from routes.user import user_bp
from routes.ohamodel import ohamodel_bp

app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(ohamodel_bp, url_prefix='/ohamodel')


from routes.dpmodel import dpmodel_bp
app.register_blueprint(dpmodel_bp, url_prefix='/dpmodel')

from routes.acnemodel import acnemodel_bp
app.register_blueprint(acnemodel_bp, url_prefix='/acnemodel')

app.register_blueprint(skin_analysis_bp, url_prefix='/skin-analysis')


from routes.foodmodel import foodmodel_bp
app.register_blueprint(foodmodel_bp, url_prefix='/foodmodel')

from routes.gpt import gpt_bp
app.register_blueprint(gpt_bp, url_prefix='/gpt')

from routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from routes.history import history_bp
app.register_blueprint(history_bp, url_prefix='/history')

# Import models here for Alembic
from models import *

# new one (2)
# Function to dynamically check and create all tables 
def create_all_tables():
    with app.app_context():
        try:
            # Get the list of existing tables in the database
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()

            # Get all models registered with SQLAlchemy
            mappers = db.Model.registry.mappers
            required_tables = [mapper.class_.__tablename__ for mapper in mappers]

            # Check if any required table is missing
            if not all(table in existing_tables for table in required_tables):
                logging.info('Creating missing tables...')
                logging.info(f'Expected tables: {required_tables}')
                logging.info(f'Existing tables: {existing_tables}')
                db.create_all()
            else:
                logging.info('All required tables exist.')
        except Exception as e:
            logging.error(f"Error during table creation: {e}")
            raise

        populate_ingredients()

create_all_tables()


@app.route('/uploads/<filename>', methods=["GET"])
def get_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "profilePhoto" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["profilePhoto"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique ID for the file
    file_extension = os.path.splitext(file.filename)[1]  # Get the file extension
    unique_filename = f"{generate(size=10)}{file_extension}"  # Generate a 10-character unique ID

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(file_path)

    # Construct the full URL dynamically
    file_url = f"{request.host_url}uploads/{unique_filename}"

    return jsonify({"filePath": file_path, "filePathWithHostURL": file_url})

# oral image functions
@app.route('/uploads/oha/<filename>', methods=["GET"])
def get_uploaded_oral_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'] + "/oha/", filename)

@app.route("/upload/oral", methods=["POST"])
def upload_oral_file():
    if "oralPhoto" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["oralPhoto"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique ID for the file
    file_extension = os.path.splitext(file.filename)[1]  # Get the file extension
    unique_filename = f"{generate(size=10)}{file_extension}"  # Generate a 10-character unique ID

    file_path = os.path.join(app.config["UPLOAD_FOLDER"] + "/oha/", unique_filename)
    file.save(file_path)

    # Construct the full URL dynamically
    file_url = f"{request.host_url}uploads/oha/{unique_filename}"

    return jsonify({"filePath": file_path, "filePathWithHostURL": file_url})
# end of oral image functions


@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        os.remove(file_path)
        return jsonify({"message": "File deleted successfully"}), 200
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Start the application
if __name__ == '__main__':
    app.run(debug=True, port=3001)
