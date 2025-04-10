from flask import Blueprint, request, jsonify
from models.skin_analysis import SkinAnalysis
from extensions import db
from datetime import datetime
import json
from sqlalchemy import text

skin_analysis_bp = Blueprint('skin_analysis', __name__)

@skin_analysis_bp.route('/save', methods=['POST'])
def save_analysis():
    try:
        data = request.json
        print("Received data for saving:", {
            'has_image': bool(data.get('imageUrl')),
            'has_annotated_image': bool(data.get('annotatedImageUrl')),
            'predictions_length': len(data.get('predictions', [])),
            'timestamp': data.get('timestamp')
        })

        # Debug log the actual URLs (first 100 chars)
        print("Image URLs:", {
            'image_url': data.get('imageUrl')[:100] if data.get('imageUrl') else None,
            'annotated_url': data.get('annotatedImageUrl')[:100] if data.get('annotatedImageUrl') else None
        })

        analysis = SkinAnalysis(
            user_id=1,  # Replace with actual user ID from session
            image_url=data.get('imageUrl'),
            annotated_image_url=data.get('annotatedImageUrl'),
            predictions=data.get('predictions'),
            notes=data.get('notes', ''),
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        # Debug log the saved analysis
        print("Saved analysis:", {
            'id': analysis.id,
            'has_annotated_image': bool(analysis.annotated_image_url)
        })
        
        return jsonify({
            'message': 'Analysis saved successfully',
            'id': analysis.id
        }), 201
    
    except Exception as e:
        print(f"Error saving analysis: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@skin_analysis_bp.route('/history', methods=['GET'])
def get_history():
    try:
        analyses = SkinAnalysis.query.order_by(SkinAnalysis.timestamp.desc()).all()
        analyses_list = [{
            'id': analysis.id,
            'imageUrl': analysis.image_url,
            'annotatedImageUrl': analysis.annotated_image_url,  # Make sure this matches your frontend
            'predictions': analysis.predictions,
            'notes': analysis.notes,
            'timestamp': analysis.timestamp.isoformat() if analysis.timestamp else None,
            'userId': analysis.user_id
        } for analysis in analyses]
        
        # Debug log
        if analyses_list:
            print("First analysis data:", {
                'id': analyses_list[0]['id'],
                'hasAnnotatedImage': bool(analyses_list[0]['annotatedImageUrl']),
                'predictionsLength': len(analyses_list[0]['predictions']) if isinstance(analyses_list[0]['predictions'], list) else 'not a list'
            })
        
        return jsonify(analyses_list)
    except Exception as e:
        print(f"Error fetching analyses: {e}")
        return jsonify({'error': str(e)}), 500
    
@skin_analysis_bp.route('/<int:analysis_id>', methods=['PUT'])
def update_analysis(analysis_id):
    try:
        analysis = SkinAnalysis.query.get_or_404(analysis_id)
        data = request.json
        
        if 'notes' in data:
            analysis.notes = data['notes']
        
        db.session.commit()
        return jsonify({'message': 'Analysis updated successfully'}), 200
    
    except Exception as e:
        print(f"Error updating analysis: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@skin_analysis_bp.route('/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    try:
        analysis = SkinAnalysis.query.get_or_404(analysis_id)
        db.session.delete(analysis)
        db.session.commit()
        return jsonify({'message': 'Analysis deleted successfully'}), 200
    
    except Exception as e:
        print(f"Error deleting analysis: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500