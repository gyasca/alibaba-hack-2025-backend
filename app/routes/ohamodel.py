# Gregory Achilles Chua 220502T

from flask import Blueprint, request, jsonify, current_app, session
from ultralytics import YOLO
from io import BytesIO
from PIL import Image
import os
import google.generativeai as google_gen_ai
from oss_utils import upload_to_oss

# Define the Blueprint
ohamodel_bp = Blueprint('ohamodel', __name__)

# Load YOLOv8 model (Replace with your model path if needed)
model_path = os.path.join(os.getcwd(), 'aimodels/oha/best.pt')
model = YOLO(model_path)

# Generative AI Google Gemini model
def get_gen_ai_model():
    api_key = current_app.config.get("GREGORY_GEMINI_API_KEY")  # Use .get() to avoid errors if key is missing
    if not api_key:
        raise ValueError("API key for Google Gemini AI is missing")
    
    google_gen_ai.configure(api_key=api_key)
    return google_gen_ai.GenerativeModel("gemini-pro")

@ohamodel_bp.route('/predict', methods=['POST'])
def predict():
    try:
        # Check if an image is included in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        print(f"Received file: {file.filename}")  # Debugging line
        
        # Read file once into memory
        file_data = file.read()
        
        # Upload to OSS using a copy of the data
        try:
            file_copy = BytesIO(file_data)
            oss_url = upload_to_oss(file_copy, file.filename)
        except Exception as e:
            print(f"OSS upload error: {str(e)}")
            return jsonify({'error': 'Failed to upload to OSS'}), 500
        
        # Use another copy for model inference
        try:
            img = Image.open(BytesIO(file_data))
            results = model(img)  # Run inference on the image
            print(f"Results: {results}")  # Debugging line
        except Exception as e:
            print(f"Model inference error: {str(e)}")
            return jsonify({'error': 'Failed to process image with model'}), 500
        
        # Extract predictions from the results
        predictions = []
        for result in results:
            for box in result.boxes:
                box_values = box.xywh[0].cpu().numpy()
                prediction = {
                    'pred_class': int(box.cls.cpu().item()),
                    'confidence': float(box.conf.cpu().item()),
                    'x_center': float(box_values[0]),
                    'y_center': float(box_values[1]),
                    'width': float(box_values[2]),
                    'height': float(box_values[3]),
                }
                predictions.append(prediction)

        # Return comprehensive prediction results
        response_data = {
            'predictions': predictions,
            'image_url': oss_url,
            'condition_count': len(predictions)
        }
        return jsonify(response_data)

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
        chat_history = data.get("chat_history", "").strip()

        from openai import OpenAI
        import os

        client = OpenAI(
            api_key=os.getenv("SAMUELS_API_KEY"),
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )

        # Build the chat history
        messages = []
        system_message = """
            You are a helpful chatbot in an oral health analysis app. Format your responses using this structure:

            # [Main Title - Center Aligned]

            [Brief introduction paragraph]

            ## 🔍 Key Findings
            * Point 1
            * Point 2

            ## ⚠️ Important Warning
            > [Warning message in a blockquote]

            ## 📋 Symptoms & Signs
            * **Symptom 1**: Description
            * **Symptom 2**: Description

            ## 🎯 Recommended Actions
            1. **Immediate Steps**:
               * Action 1
               * Action 2

            2. **Long-term Care**:
               * Step 1
               * Step 2

            ## 🏥 Recommended Clinics
            * [Clinic Name 1](link) - Brief description
            * [Clinic Name 2](link) - Brief description

            ## 💡 Additional Tips
            * **Tip 1**: Description
            * **Tip 2**: Description

            Always use emojis for section headers, bold for important terms, and maintain consistent spacing.
        """
        
        messages.append({"role": "system", "content": system_message})
        
        if instruction and results:
            session["instruction"] = instruction
            session["results"] = results
            messages.append({"role": "system", "content": instruction})
            messages.append({"role": "user", "content": f"{results}\n\n{message}"})
        else:
            messages.append({"role": "user", "content": f"{chat_history}\n\n{message}"})

        # Generate response from Qwen
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            temperature=0.7,  # Add some creativity while maintaining coherence
            max_tokens=800    # Allow for longer, more detailed responses
        )

        return jsonify({"response": response.choices[0].message.content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
