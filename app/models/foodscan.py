from extensions import db
from datetime import datetime

# FoodScan model
class FoodScan(db.Model):
    __tablename__ = "food_scans"

    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(255), nullable=False)
    food_image = db.Column(db.String(500), nullable=False)  # URL or base64
    ingredients = db.Column(db.Text, nullable=False)  # Store as JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationship with User model
    user = db.relationship("User", backref=db.backref("food_scans", lazy=True))

    def __repr__(self):
        return f"<FoodScan {self.food_name}, User {self.user_id}, Date {self.timestamp}>"