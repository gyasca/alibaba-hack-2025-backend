from extensions import db
from datetime import datetime
import json

class SkinAnalysis(db.Model):
    __tablename__ = 'skin_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_url = db.Column(db.Text)
    annotated_image_url = db.Column(db.Text)  # Add this line
    predictions = db.Column(db.JSON)
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_url': self.image_url,
            'predictions': self.predictions,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }