from extensions import db
from sqlalchemy.dialects.postgresql import JSON

# Dish model
class Dish(db.Model):
    __tablename__ = 'dishes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    avg_calories = db.Column(db.Float, nullable=False)
    ingredients = db.Column(JSON, nullable=False)

    def __repr__(self):
        return f"<Dish {self.name}>"