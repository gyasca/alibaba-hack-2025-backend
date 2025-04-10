from flask import Flask, request, jsonify
from flask_cors import CORS
from extensions import db
from flask_jwt_extended import JWTManager
from sqlalchemy import inspect
import logging
from config import Config
from database.init_db import init_db
from oss_utils import get_oss_bucket, upload_to_oss, get_oss_url, delete_from_oss
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
cors = CORS()
cors.init_app(app)

# Set up logging
logging.basicConfig(level=logging.INFO)

# OSS Configuration
app.config['OSS_ACCESS_KEY_ID'] = os.getenv('OSS_ACCESS_KEY_ID')
app.config['OSS_ACCESS_KEY_SECRET'] = os.getenv('OSS_ACCESS_KEY_SECRET')
app.config['OSS_BUCKET_NAME'] = os.getenv('OSS_BUCKET_NAME')
app.config['OSS_ENDPOINT'] = os.getenv('OSS_ENDPOINT')

# Import and register Blueprints
from routes.user import user_bp
from routes.ohamodel import ohamodel_bp
from routes.auth import auth_bp
from routes.history import history_bp

app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(ohamodel_bp, url_prefix='/ohamodel')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(history_bp, url_prefix='/history')

# Import models here for Alembic
from models import *

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

create_all_tables()

# Chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    
    # Your chat logic here
    response = {
        'message': f"I received your message: {message}"
    }
    
    return jsonify(response)

# Start the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)

