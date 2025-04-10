from flask import Flask, request, jsonify, Blueprint, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageDraw
import os
import re
import tensorflow as tf
import json
from models import *
from extensions import db
from routes.gpt import generate_response
from datetime import datetime

# Define the Blueprint
foodmodel_bp = Blueprint('foodmodel', __name__)

# Load the pre-trained model
model_path = os.path.join(
    os.getcwd(), 'aimodels/food/food_classifier_model.keras')
model = tf.keras.models.load_model(model_path)

ingredients_model_path = os.path.join(
    os.getcwd(), 'aimodels/food/ingredient_detection_best.pt')
ingredients_model = YOLO(ingredients_model_path)

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Utility function to check if file extension is allowed


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@foodmodel_bp.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@foodmodel_bp.route('/runs/detect/predict3/<path:filename>')
def serve_uploaded_file2(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Endpoint to handle image upload and prediction


@foodmodel_bp.route('/identify-food', methods=['POST'])
def detect_food():
    print("[INFO] Starting food detection process.")

    # Define the upload directory
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"[INFO] Upload folder set to: {UPLOAD_FOLDER}")

    # Check if an image file was sent in the request
    if 'image' not in request.files:
        print("[ERROR] No image part in the request.")
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        print("[ERROR] No file selected.")
        return jsonify({"error": "No selected file"}), 400

    # Validate and process the uploaded file
    if file and allowed_file(file.filename):
        try:
            # Secure the file name and determine the save path
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            print(f"[INFO] Saving uploaded file to: {filepath}")

            # Save the file to the server
            file.save(filepath)

            # Process the saved image to detect food and ingredients
            print("[INFO] Processing the uploaded image.")
            food_data = process_image(filepath)

            # Handle any errors during image processing
            if "error" in food_data:
                error_message = food_data["error"]
                print(
                    f"[ERROR] Error during image processing: {error_message}")
                return jsonify({"error": error_message}), 500

            # Return the detected food data as a JSON response
            print("[INFO] Successfully detected food and ingredients.")
            return jsonify({
                "name": food_data['name'],
                # Include detected ingredients
                "ingredients": food_data['ingredients'],
                # Relative path to the uploaded image
                "image": f"/uploads/{filename}"
            })

        except Exception as e:
            error_message = f"Error processing the image: {str(e)}"
            print(f"[ERROR] {error_message}")
            return jsonify({"error": error_message}), 500
    else:
        print("[ERROR] Invalid file type.")
        return jsonify({"error": "Invalid file type"}), 400

# Image processing and prediction function


def process_image(filepath):
    try:
        print("[INFO] Opening and preprocessing the image.")

        # Open image using PIL
        img = Image.open(filepath)

        # Preprocess image for model input (assuming the model expects 128x128 images)
        img = img.resize((128, 128))
        img_array = np.array(img) / 255.0  # Normalize the image

        # Expand dimensions to match the model input shape (batch_size, height, width, channels)
        img_array = np.expand_dims(img_array, axis=0)
        print("[INFO] Image preprocessing completed.")

        # Get prediction from the food classification model
        print("[INFO] Predicting food type from the image.")
        predictions = model.predict(img_array)

        # Predict ingredients using the YOLO model
        print("[INFO] Predicting ingredients using the YOLO model.")
        try:
            ingredients_json = predict_ingredients(filepath)
            detected_ingredients = parse_ingredients_json(ingredients_json)
        except Exception as e:
            error_message = f"Error during ingredients prediction: {str(e)}"
            print(f"[ERROR] {error_message}")
            return {"error": error_message}

        # Map the model's prediction to a food label
        food_name = map_prediction_to_data(predictions)
        print(f"[INFO] Predicted food: {food_name}")

        # Fetch nutritional data for the detected ingredients
        ingredients_with_nutritional_data = []
        for ingredient_name, quantity in detected_ingredients.items():
            nutritional_data = get_ingredient_data(
                ingredient_name, quantity=quantity)
            if nutritional_data:
                ingredients_with_nutritional_data.append(nutritional_data)

        print(
            f"[INFO] Ingredient list with nutritional data: {ingredients_with_nutritional_data}")
        
        enhanced_ingredients = enhance_gpt(food_name, ingredients_with_nutritional_data)

        try:
            return {
                "name": food_name,
                "ingredients": enhanced_ingredients
                # "ingredients": ingredients_with_nutritional_data
            }
        except Exception as e:
            error_message = f"Error enhancing ingredients: {str(e)}"
            print(f"[ERROR] {error_message}")
            return {
                "name": food_name,
                "ingredients": ingredients_with_nutritional_data
            }

    except Exception as e:
        print(f"[ERROR] Error in process_image: {str(e)}")
        return {"error": f"Error in process_image: {str(e)}"}


# Map model prediction to food name


def map_prediction_to_data(predictions):
    try:
        print("[INFO] Mapping prediction to food label.")
        # Get the index of the highest probability
        predicted_class_index = np.argmax(predictions)

        # List of food labels corresponding to model classes
        food_labels = [
            "Chicken Rice",  # Index 0
            "Char Kway Teow",  # Index 1
            "Nasi Lemak",     # Index 2
            # Add more class names here
        ]

        # Get the predicted food name
        food_name = food_labels[predicted_class_index]
        print(f"[INFO] Prediction mapped to food: {food_name}")
        return food_name
    except Exception as e:
        print(f"[ERROR] Error in map_prediction_to_data: {str(e)}")
        return "Unknown Food"

# Parse JSON data for ingredients


def parse_ingredients_json(json_data):
    try:
        print("[INFO] Parsing detected ingredients JSON.")
        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        ingredient_count = {}
        for ingredient in json_data:
            name = ingredient.get('name')
            if name:
                ingredient_count[name] = ingredient_count.get(name, 0) + 1

        print(f"[INFO] Parsed ingredients: {ingredient_count}")
        return ingredient_count
    except Exception as e:
        print(f"[ERROR] Error in parse_ingredients_json: {str(e)}")
        return {}

# Predict ingredients using the YOLO model


def predict_ingredients(filepath):
    try:
        print("[INFO] Running YOLO ingredients detection.")
        results = ingredients_model.predict(
            source=filepath,
            conf=0.5,
            device="cpu",
            save=True
        )
        print("[INFO] YOLO prediction completed.")
        return results[0].to_json()
    except Exception as e:
        print(f"[ERROR] Error in predict_ingredients: {str(e)}")
        raise e


def get_ingredient_data(name, quantity=1):
    try:
        print(f"[INFO] Fetching nutritional data for ingredient: {name}")
        ingredient = Ingredient.query.filter_by(name=name).first()
        if not ingredient:
            print(f"[INFO] No nutritional data found for ingredient: {name}")
            return None

        return {
            "name": ingredient.name,
            "calories": ingredient.calories,
            "carb": ingredient.carb,
            "protein": ingredient.protein,
            "fat": ingredient.fat,
            "increment_type": ingredient.increment_type,
            "quantity": quantity  # Include quantity in the return value
        }
    except Exception as e:
        print(
            f"[ERROR] Error retrieving nutritional data for ingredient {name}: {str(e)}")
        return None


# Placeholder function for GPT augmentation (to be implemented)


def enhance_gpt(food_name, ingredients_with_nutritional_data):
    try:
        print("[INFO] Enhancing ingredient list using OpenAI API.")
        
        # Prepare the role
        role = "You are a culinary and nutrition expert robot."

        # Prepare the prompt
        prompt = (
            f"The food detected is '{food_name}'. Here is the list of ingredients with their nutritional data:\n"
            f"{ingredients_with_nutritional_data}\n\n"
            f"Please provide corrections, adjustments, or enhancements to this ingredient JSON based on the food name and typical preparation methods.\n"
            f"Ensure you return only a JSON in the same format as the input, as your output will be passed into code.\n"
            f"Do NOT alter quantity of ingredients or add new ingredients, but you may change its name if it provided more information unless its egg."
        )

        # Call the OpenAI API
        response = generate_response(prompt, role)
        print(f"[INFO] GPT response: {response}")

        enhanced_ingredients_json = extract_json(response)
        print(f"[INFO] Enhanced ingredient list: {enhanced_ingredients_json}")
        return enhanced_ingredients_json

    except Exception as e:
        error_message = f"Error during OpenAI API call: {str(e)}"
        print(f"[ERROR] {error_message}")
        return error_message

def extract_json(gpt_response):
    """
    Extracts the JSON portion from a GPT response.

    Args:
        gpt_response (str): The full response from GPT containing text and a JSON block.

    Returns:
        dict or list: Parsed JSON data extracted from the response, or an error message if parsing fails.
    """
    try:
        # Use a regular expression to extract the JSON enclosed in square brackets
        json_match = re.search(r"\[(.*?)]", gpt_response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON block found in the response.")
        
        # Extract and sanitize the JSON content
        json_str = json_match.group(0)  # Include the brackets
        # Ensure proper formatting for JSON parsing
        json_str = json_str.replace("\'", "\"")  # Replace single quotes with double quotes
        
        # Parse the JSON content
        parsed_json = json.loads(json_str)
        return parsed_json

    except Exception as e:
        error_message = f"Error extracting JSON: {str(e)}"
        print(f"[ERROR] {error_message}")
        return {"error": error_message}
    
@foodmodel_bp.route('/api/ingredients', methods=['POST'])
def add_ingredient():
    try:
        # Parse JSON data from the request
        data = request.json
        print("[INFO] Received data to add ingredient:", data)

        # Create a new Ingredient object
        new_ingredient = Ingredient(
            name=data['name'],
            calories=data['calories'],
            carb=data['carb'],
            protein=data['protein'],
            fat=data['fat'],
            increment_type=data['increment_type']
        )

        # Add the new ingredient to the database
        db.session.add(new_ingredient)
        db.session.commit()

        print("[INFO] Ingredient added successfully:", new_ingredient.name)
        return jsonify({"message": "Ingredient added successfully"}), 201

    except Exception as e:
        error_message = f"Error adding ingredient: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({"error": "Failed to add ingredient"}), 500


@foodmodel_bp.route('/api/dishes', methods=['POST'])
def add_dish():
    try:
        # Parse JSON data from the request
        data = request.json
        print("[INFO] Received data to add dish:", data)

        # Create a new Dish object
        new_dish = Dish(
            name=data['name'],
            avg_calories=data['avg_calories'],
            ingredients=data.get('ingredients', [])
        )

        # Add the new dish to the database
        db.session.add(new_dish)
        db.session.commit()

        print("[INFO] Dish added successfully:", new_dish.name)
        return jsonify({"message": "Dish added successfully"}), 201

    except Exception as e:
        error_message = f"Error adding dish: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({"error": "Failed to add dish"}), 500


@foodmodel_bp.route('/api/dishes', methods=['GET'])
def get_all_dishes():
    try:
        dishes = Dish.query.all()
        dishes_data = [{"id": dish.id, "name": dish.name, "avg_calories": dish.avg_calories,
                        "ingredients": dish.ingredients} for dish in dishes]
        print("[INFO] Retrieved all dishes successfully")
        return jsonify(dishes_data), 200
    except Exception as e:
        error_message = f"Error retrieving dishes: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({"error": error_message}), 500


@foodmodel_bp.route('/api/ingredients', methods=['GET'])
def get_all_ingredients():
    try:
        ingredients = Ingredient.query.all()
        ingredients_data = [{"id": ingredient.id, "name": ingredient.name, "calories": ingredient.calories, "carb": ingredient.carb,
                             "protein": ingredient.protein, "fat": ingredient.fat, "increment_type": ingredient.increment_type} for ingredient in ingredients]
        print("[INFO] Retrieved all ingredients successfully")
        return jsonify(ingredients_data), 200
    except Exception as e:
        error_message = f"Error retrieving ingredients: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({"error": error_message}), 500


@foodmodel_bp.route('/api/dishes/<string:name>', methods=['GET'])
def get_dish_by_name(name):
    try:
        dish = Dish.query.filter_by(name=name).first()
        if not dish:
            print(f"[INFO] Dish with name '{name}' not found")
            return jsonify({"error": "Dish not found"}), 404

        dish_data = {
            "id": dish.id,
            "name": dish.name,
            "avg_calories": dish.avg_calories,
            "ingredients": dish.ingredients
        }
        print(f"[INFO] Retrieved dish: {dish.name}")
        return jsonify(dish_data), 200
    except Exception as e:
        error_message = f"Error retrieving dish: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({"error": error_message}), 500


@foodmodel_bp.route('/api/ingredients/<string:name>', methods=['GET'])
def get_ingredient_by_name(name):
    try:
        ingredient = Ingredient.query.filter_by(name=name).first()
        if not ingredient:
            print(f"[INFO] Ingredient with name '{name}' not found")
            return jsonify({"error": "Ingredient not found"}), 404

        ingredient_data = {
            "id": ingredient.id,
            "name": ingredient.name,
            "calories": ingredient.calories,
            "carb": ingredient.carb,
            "protein": ingredient.protein,
            "fat": ingredient.fat,
            "increment_type": ingredient.increment_type
        }
        print(f"[INFO] Retrieved ingredient: {ingredient.name}")
        return jsonify(ingredient_data), 200
    except Exception as e:
        error_message = f"Error retrieving ingredient: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({"error": error_message}), 500

@foodmodel_bp.route('/api/foodscan', methods=['POST'])
def create_foodscan():
    try:
        data = request.get_json()
        print(f"[INFO] Received data for FoodScan creation: {data}")

        food_name = data.get('food_name')
        food_image = data.get('food_image')
        ingredients = data.get('ingredients')
        user_id = data.get('user_id')

        if not all([food_name, food_image, ingredients, user_id]):
            missing_fields = [field for field in ['food_name', 'food_image', 'ingredients', 'user_id'] if not data.get(field)]
            error_message = f"Missing fields in request: {', '.join(missing_fields)}"
            print(f"[ERROR] {error_message}")
            return jsonify({'error': error_message}), 400

        foodscan = FoodScan(
            food_name=food_name,
            food_image=food_image,
            ingredients=ingredients,
            user_id=user_id
        )
        db.session.add(foodscan)
        db.session.commit()
        
        print(f"[INFO] FoodScan successfully created with ID: {foodscan.id}")
        return jsonify({'message': 'FoodScan created successfully!', 'id': foodscan.id}), 201

    except Exception as e:
        error_message = f"Error creating FoodScan: {str(e)}"
        print(f"[ERROR] {error_message}")
        return jsonify({'error': error_message}), 500

@foodmodel_bp.route('/api/foodscans/<int:user_id>', methods=['GET'])
def get_foodscans_by_user(user_id):
    try:
        foodscans = FoodScan.query.filter_by(user_id=user_id).all()
        result = [
            {
                'id': scan.id,
                'food_name': scan.food_name,
                'food_image': scan.food_image,
                'ingredients': scan.ingredients,
                'timestamp': scan.timestamp.isoformat(),  # Convert to string for JSON
            }
            for scan in foodscans
        ]
        return jsonify(result), 200
    except Exception as e:
        print("[ERROR] Error fetching FoodScans:", str(e))
        return jsonify({'error': f"Error fetching FoodScans: {str(e)}"}), 500
