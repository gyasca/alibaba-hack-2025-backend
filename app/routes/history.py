# Gregory Achilles Chua 220502T

from flask import Blueprint, request, jsonify
from ultralytics import YOLO
from io import BytesIO
from PIL import Image
import os
from datetime import datetime
from extensions import db
from models.oral_analysis_history import OralAnalysisHistory


# Define the Blueprint
history_bp = Blueprint('history', __name__)

@history_bp.route('/oha/save-results', methods=['POST'])
def save_results():
    data = request.json  # Expecting JSON data with the prediction details
    user_id = data['user_id']
    original_image_path = data['original_image_path']
    condition_count = data['condition_count']
    predictions = data['predictions']  # This is already a JSON list

    try:
        # Create a new entry with the full JSON predictions
        oral_history = OralAnalysisHistory(
            user_id=user_id,
            original_image_path=original_image_path,
            condition_count=condition_count,
            predictions=predictions  # Store full predictions JSON here
        )
        
        db.session.add(oral_history)
        db.session.commit()

        return jsonify({'message': 'Results saved successfully'}), 200

    except Exception as e:
        print(f"Error saving history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/oha/get-history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')  # Get the user_id from query parameters

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        # Query the OralAnalysisHistory table for the user's past analysis results
        history = OralAnalysisHistory.query.filter_by(user_id=user_id).all()

        # If no history is found
        if not history:
            return jsonify({'message': 'No history found for the given user ID'}), 404

        # Serialize the results to JSON format
        history_data = []
        for record in history:
            record_data = {
                'id': record.id,
                'user_id': record.user_id,
                'original_image_path': record.original_image_path,
                'predictions': record.predictions,  # This will be the full JSON string from the database
                'condition_count': record.condition_count,
                'analysis_date': record.analysis_date.strftime('%Y-%m-%d %H:%M:%S')  # Format date if needed
            }
            history_data.append(record_data)

        return jsonify({'history': history_data}), 200

    except Exception as e:
        print(f"Error fetching history: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@history_bp.route('/oha/delete-result', methods=['DELETE'])
def delete_history():
    # Get the 'id' from the query parameters
    history_id = request.args.get('id')

    if not history_id:
        return jsonify({'error': 'id is required'}), 400

    try:
        # Query the OralAnalysisHistory table to find the record by id
        record = OralAnalysisHistory.query.get(history_id)

        if not record:
            return jsonify({'error': 'History record not found'}), 404

        # Delete the record
        db.session.delete(record)
        db.session.commit()

        return jsonify({'message': 'History record deleted successfully'}), 200

    except Exception as e:
        print(f"Error deleting history: {str(e)}")
        return jsonify({'error': str(e)}), 500
