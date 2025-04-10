from extensions import db
import datetime

class OralAnalysisHistory(db.Model):
    __tablename__ = 'oral_analysis_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Link to the User model
    user = db.relationship('User', backref=db.backref('oral_analysis_history', lazy=True))

    original_image_path = db.Column(db.String(255), nullable=False)  # Path to the original uploaded image
    predictions = db.Column(db.JSON, nullable=False)  # Store predictions in JSON format
    condition_count = db.Column(db.Integer, nullable=False)  # Number of conditions detected
    analysis_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Timestamp for the analysis

    def __init__(self, user_id, original_image_path, predictions, condition_count):
        self.user_id = user_id
        self.original_image_path = original_image_path
        self.predictions = predictions
        self.condition_count = condition_count

    def __repr__(self):
        return f"<OralAnalysisHistory(user_id={self.user_id}, condition_count={self.condition_count}, analysis_date={self.analysis_date})>"
