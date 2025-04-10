from flask import Blueprint, request, jsonify, current_app, session
from ultralytics import YOLO
from io import BytesIO
from PIL import Image
import os
import base64
from models.skin_analysis import SkinAnalysis
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import google.generativeai as google_gen_ai
from flask_cors import CORS

acnemodel_bp = Blueprint('acnemodel', __name__)
CORS(acnemodel_bp, resources={r"/*": {"origins": "*"}})


# Load YOLOv8 model
model_path = os.path.join(os.getcwd(), 'aimodels/acne/best.pt')
model = YOLO(model_path)

# Generative AI Google Gemini model
# Initialize Google Gemini AI API
def get_gen_ai_model():
    api_key = current_app.config.get("RYAN_API_KEY")  # Use .get() to avoid errors if key is missing
    if not api_key:
        raise ValueError("API key for Google Gemini AI is missing")
    
    google_gen_ai.configure(api_key=api_key)
    return google_gen_ai.GenerativeModel("gemini-pro")


@acnemodel_bp.route('/predict', methods=['POST'])
def predict():
    try:
        print("Request received")
        print("Request headers:", dict(request.headers))
        print("Request files:", request.files)
        print("Request form:", request.form)
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 422
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 422

        # Verify file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Invalid file type'}), 422

        # Read the image
        img_bytes = file.read()
        if not img_bytes:
            return jsonify({'error': 'Empty file'}), 422

        # Convert bytes to image
        img = Image.open(BytesIO(img_bytes))
        
        # Run model prediction
        results = model(img)
        
        # Process predictions
        predictions = []
        for result in results:
            for box in result.boxes:
                box_values = box.xywh[0].cpu().numpy()
                prediction = {
                    'class': int(box.cls.cpu().item()),
                    'confidence': float(box.conf.cpu().item()),
                    'x_center': float(box_values[0]),
                    'y_center': float(box_values[1]),
                    'width': float(box_values[2]),
                    'height': float(box_values[3]),
                }
                predictions.append(prediction)
        
        print("Predictions generated:", predictions)
        return jsonify({'predictions': predictions})

    except Exception as e:
        import traceback
        print("Error in prediction:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@acnemodel_bp.route('/skin-analysis/save', methods=['POST'])
@jwt_required()
def save_analysis():
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        # Create new analysis
        analysis = SkinAnalysis(
            user_id=user_id,
            image_url=data['imageUrl'],
            predictions=data['predictions'],
            notes=data.get('notes', ''),
            timestamp=data.get('timestamp')
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({'message': 'Analysis saved successfully', 'id': analysis.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@acnemodel_bp.route('/skin-analysis/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        user_id = get_jwt_identity()
        analyses = SkinAnalysis.query.filter_by(user_id=user_id).order_by(SkinAnalysis.timestamp.desc()).all()
        return jsonify([analysis.to_dict() for analysis in analyses])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@acnemodel_bp.route('/skin-analysis/<int:analysis_id>', methods=['PUT'])
@jwt_required()
def update_analysis(analysis_id):
    try:
        user_id = get_jwt_identity()
        analysis = SkinAnalysis.query.filter_by(id=analysis_id, user_id=user_id).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        data = request.json
        if 'notes' in data:
            analysis.notes = data['notes']
        
        db.session.commit()
        return jsonify({'message': 'Analysis updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@acnemodel_bp.route('/skin-analysis/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    try:
        user_id = get_jwt_identity()
        analysis = SkinAnalysis.query.filter_by(id=analysis_id, user_id=user_id).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        db.session.delete(analysis)
        db.session.commit()
        return jsonify({'message': 'Analysis deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# chat with context
@acnemodel_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400
        
        message = data.get("message", "").strip()
        instruction = data.get("instruction", "").strip()
        context = data.get("context", "").strip()

        model = get_gen_ai_model()

        # Build the prompt
        if instruction and context:
            chat_history = f"{instruction}\n{context}\n\nUser: {message}"
        else:
            chat_history = f"User: {message}"

        # Generate AI response
        response = model.generate_content(chat_history)

        return jsonify({"response": response.text})

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")  # Add logging
        return jsonify({"error": str(e)}), 500