# Gregory Achilles Chua 220502T

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from extensions import db
from models.oral_analysis_history import OralAnalysisHistory

# Define the Blueprint
history_bp = Blueprint('history', __name__)

@history_bp.route('/oha/save-results', methods=['POST'])
def save_results():
    try:
        # Validate input data
        data = request.json
        if not data:
            print("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['user_id', 'image_url', 'predictions']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"Missing fields in request: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        try:
            # Ensure predictions is valid JSON
            if isinstance(data['predictions'], str):
                predictions_json = data['predictions']
            else:
                predictions_json = json.dumps(data['predictions'])
            
            # Validate JSON by parsing it
            json.loads(predictions_json)
        except (TypeError, ValueError) as e:
            print(f"JSON encoding error: {str(e)}")
            return jsonify({'error': 'Invalid predictions format'}), 400

        try:
            # Create new history entry
            history = OralAnalysisHistory(
                user_id=data['user_id'],
                original_image_path=data['image_url'],
                predictions=predictions_json,
                condition_count=len(data['predictions']) if isinstance(data['predictions'], list) else 0
            )
            
            db.session.add(history)
            db.session.commit()
            
            print(f"Successfully saved history for user {data['user_id']}")
            return jsonify({'message': 'Results saved successfully', 'id': history.id}), 200

        except Exception as e:
            print(f"Database error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Failed to save to database'}), 500

    except Exception as e:
        print(f"Error saving history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@history_bp.route('/oha/get-history', methods=['GET'])
def get_history():
    try:
        user_id = request.args.get('user_id')
        print(f"Fetching history for user_id: {user_id}")
        
        if not user_id:
            print("No user_id provided")
            return jsonify({'error': 'user_id is required'}), 400

        try:
            # Query with explicit ordering and type casting
            history = OralAnalysisHistory.query.filter_by(user_id=int(user_id))\
                .order_by(OralAnalysisHistory.analysis_date.desc())\
                .all()
            
            print(f"Found {len(history)} records for user {user_id}")

            # Handle empty result explicitly
            if not history:
                print(f"No history found for user {user_id}")
                return jsonify({
                    'history': [],
                    'message': 'No history found',
                    'user_id': user_id
                }), 200

            # Parse history records with error handling
            history_data = []
            for record in history:
                try:
                    # Verify the predictions field is valid JSON
                    if record.predictions:
                        predictions = json.loads(record.predictions)
                    else:
                        predictions = []

                    history_data.append({
                        'id': record.id,
                        'user_id': record.user_id,
                        'image_url': record.original_image_path,
                        'predictions': predictions,
                        'condition_count': record.condition_count,
                        'analysis_date': record.analysis_date.isoformat()
                    })
                    print(f"Processed record {record.id} successfully")
                except json.JSONDecodeError as e:
                    print(f"Error parsing predictions for record {record.id}: {str(e)}")
                    # Include record with empty predictions rather than skipping
                    history_data.append({
                        'id': record.id,
                        'user_id': record.user_id,
                        'image_url': record.original_image_path,
                        'predictions': [],
                        'condition_count': 0,
                        'analysis_date': record.analysis_date.isoformat()
                    })
                except Exception as e:
                    print(f"Error processing record {record.id}: {str(e)}")
                    continue

            print(f"Successfully processed {len(history_data)} records")
            return jsonify({
                'history': history_data,
                'count': len(history_data),
                'user_id': user_id
            }), 200

        except ValueError as e:
            print(f"Invalid user_id format: {str(e)}")
            return jsonify({'error': 'Invalid user_id format'}), 400

    except Exception as e:
        print(f"Error fetching history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@history_bp.route('/oha/delete-result', methods=['DELETE'])
def delete_history():
    try:
        history_id = request.args.get('id')
        if not history_id:
            return jsonify({'error': 'id is required'}), 400

        try:
            record = OralAnalysisHistory.query.get(history_id)
            if not record:
                print(f"No record found with id {history_id}")
                return jsonify({'error': 'History record not found'}), 404

            db.session.delete(record)
            db.session.commit()
            print(f"Successfully deleted history record {history_id}")
            return jsonify({'message': 'History record deleted successfully'}), 200

        except Exception as e:
            print(f"Database error during deletion: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Failed to delete record'}), 500

    except Exception as e:
        print(f"Error deleting history: {str(e)}")
        return jsonify({'error': str(e)}), 500
