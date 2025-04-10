from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import User  # Import your User model
from extensions import db  # Import your db instance


auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/refresh", methods=["GET"])
@jwt_required()  # Ensure user is authenticated
def refresh():
    user_id = get_jwt_identity()  # Get user ID from the token
    user = User.query.get(user_id)  # Fetch latest user details

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Define the user info payload
    user_info = {
        "id": user.id,
        "email": user.email,
        "phone_number": user.phone_number,
        "name": user.name,
        "account_type": user.account_type,
        "profile_picture": user.profile_picture,
        "profile_picture_type": user.profile_picture_type,
        "driver_application_sent": user.driver_application_sent
    }

    # Generate a new token with updated user info
    token = create_access_token(identity=user.id, additional_claims={"user": user_info}, expires_delta=False)  # Set expiration as needed

    return jsonify({"token": token, "user": user_info}), 200
