import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models.user import User
from extensions import db
from flask import current_app

from werkzeug.utils import secure_filename
import os


user_bp = Blueprint('user', __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.json  # Parse JSON request
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")
    role = data.get("role")
    profile_photo_file_path = data.get("profile_photo_file_path")


    if not email or not password or not username or not role:
        return jsonify({"message": "Missing required fields"}), 400


    # Check if the email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create new user and hash the password
    user = User(
        email=email,
        password=password,  # This will be hashed below
        username=username,
        role=role,
        profile_photo_file_path=profile_photo_file_path,
    )

    user.set_password(password)  # Assuming set_password hashes the password
    db.session.add(user)
    db.session.commit()


    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "profile_photo_file_path": user.profile_photo_file_path,
        }
        }), 201



@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Validate input fields
    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    # Find the user by email
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate an access token
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    expiration_time_str = expiration_time.isoformat()

    accessToken = jwt.encode({
        'userId': user.id,
        'email': user.email,
        'role': user.role,
        'expirationTime': expiration_time_str
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Login successful',
        'accessToken': accessToken
    }), 200

@user_bp.route('/<int:userId>', methods=['GET'])
def get_user(userId):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 403

    token = token.replace('Bearer ', '')

    try:
        decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if decoded_token['userId'] != userId:
            return jsonify({"error": "Unauthorized access"}), 401

        user = User.query.get(userId)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "userId": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "profile_photo_file_path": user.profile_photo_file_path
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
@user_bp.route('/all', methods=['GET'])
def get_all_users():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 403

    token = token.replace('Bearer ', '')

    try:
        decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # Check if the user has admin privileges
        if decoded_token['role'] != 'admin':
            return jsonify({"error": "Unauthorized access"}), 401

        users = User.query.all()
        users_list = []
        
        for user in users:
            users_list.append({
                "userId": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "profile_photo_file_path": user.profile_photo_file_path
            })
        
        return jsonify({"users": users_list}), 200
    
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    

@user_bp.route('/<int:userId>', methods=['PUT'])
def update_user(userId):
    # Verify token
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 403

    token = token.replace('Bearer ', '')

    try:
        decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        # Check if the user is updating their own profile or has admin role
        if decoded_token['userId'] != userId and decoded_token['role'] != 'admin':
            return jsonify({"error": "Unauthorized access"}), 401

        # Get user from database
        user = User.query.get(userId)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get data from request
        data = request.json
        
        # Update user fields if provided
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            # Check if new email already exists for another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != userId:
                return jsonify({"error": "Email already exists"}), 400
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])
        if 'role' in data:
            # Only allow admin to change roles
            if decoded_token['role'] != 'admin':
                return jsonify({"error": "Unauthorized to change role"}), 401
            user.role = data['role']
        if 'profile_photo_file_path' in data:
            user.profile_photo_file_path = data['profile_photo_file_path']

        # Save changes
        db.session.commit()

        return jsonify({
            "message": "User updated successfully",
            "user": {
                "userId": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "profile_photo_file_path": user.profile_photo_file_path
            }
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    
# delete single user
@user_bp.route('/<int:userId>', methods=['DELETE'])
def delete_user(userId):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 403

    token = token.replace('Bearer ', '')

    try:
        decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])

        # Check if the user has admin privileges
        if decoded_token['role'] != 'admin':
            return jsonify({"error": "Unauthorized access"}), 401

        # Get user from database
        user = User.query.get(userId)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Delete user
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
