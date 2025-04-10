from extensions import db
from datetime import datetime

# Define the HealthPrediction model
class HealthPrediction(db.Model):
    __tablename__ = 'health_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    gender = db.Column(db.Integer)
    age = db.Column(db.Integer)
    current_smoker = db.Column(db.Integer)
    cigs_per_day = db.Column(db.Float)
    bp_meds = db.Column(db.Integer)
    prevalent_stroke = db.Column(db.Integer)
    prevalent_hyp = db.Column(db.Integer)
    diabetes = db.Column(db.Integer)
    sys_bp = db.Column(db.Float)
    dia_bp = db.Column(db.Float)
    bmi = db.Column(db.Float)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)