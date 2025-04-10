# Gregory Achilles Chua 220502T

from flask import Blueprint, request, jsonify, current_app, session
from ultralytics import YOLO
from io import BytesIO
from PIL import Image
import os
import google.generativeai as google_gen_ai

# Define the Blueprint
ohamodel_bp = Blueprint('ohamodel', __name__)

# Load YOLOv8 model (Replace with your model path if needed)
model_path = os.path.join(os.getcwd(), 'aimodels/oha/best.pt')
model = YOLO(model_path)

# Generative AI Google Gemini model
# Initialize Google Gemini AI API
def get_gen_ai_model():
    api_key = current_app.config.get("GREGORY_GEMINI_API_KEY")  # Use .get() to avoid errors if key is missing
    if not api_key:
        raise ValueError("API key for Google Gemini AI is missing")
    
    google_gen_ai.configure(api_key=api_key)
    return google_gen_ai.GenerativeModel("gemini-pro")


@ohamodel_bp.route('/predict', methods=['POST'])
def predict():
    # Check if an image is included in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        print(f"Received file: {file.filename}")  # Debugging line
        # Convert the image to the format YOLOv8 expects
        img = Image.open(file.stream)
        
        # Run inference on the image using YOLOv8
        results = model(img)  # Run inference on the image
        print(f"Results: {results}")  # Debugging line
        
        # Extract predictions from the results
        predictions = []
        for result in results:
            # Access bounding boxes and labels (assuming results is a list)
            for box in result.boxes:
                # Convert the box object into a list or array format
                box_values = box.xywh[0].cpu().numpy()  # Accessing box as tensor and converting to NumPy array
                prediction = {
                    'pred_class': int(box.cls.cpu().item()),  # Ensure class is an integer
                    'confidence': float(box.conf.cpu().item()),  # Ensure confidence is a float
                    'x_center': float(box_values[0]),  # Extract the x-center
                    'y_center': float(box_values[1]),  # Extract the y-center
                    'width': float(box_values[2]),  # Extract the width
                    'height': float(box_values[3]),  # Extract the height
                }
                predictions.append(prediction)

        # Return the predictions in a JSON format
        return jsonify({'predictions': predictions})

    except Exception as e:
        print(f"Error: {e}")  # Debugging line
        return jsonify({'error': str(e)}), 500
    

# chat with context and chathistory
@ohamodel_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400
        
        instruction = data.get("instruction", "").strip()
        results = data.get("results", "").strip()
        message = data.get("message", "").strip()
        chat_history = data.get("chat_history", "").strip()  # Accept chat history from frontend

        model = get_gen_ai_model()

        # Check if this is the first message
        if instruction and results:
            # Store context in session
            session["instruction"] = instruction
            session["results"] = results
            full_chat_history = f"{instruction}\n{results}\n\nUser: {message}"
        else:
            # Use provided chat_history instead of reconstructing it
            full_chat_history = chat_history + f"\nUser: {message}"

        # Generate AI response
        response = model.generate_content(full_chat_history)

        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

