from extensions import db

# Ingredient model
class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    carb = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    increment_type = db.Column(db.String(20), nullable=False)  # e.g., 'grams', 'pieces', etc.

    def __repr__(self):
        return f"<Ingredient {self.name}>"
    
def populate_ingredients():
    # Define the ingredients data
    ingredients_data = [
        {"name": "egg", "calories": 155, "carb": 1.1, "protein": 13, "fat": 11, "increment_type": "piece"},
        {"name": "sambal", "calories": 150, "carb": 15, "protein": 2, "fat": 10, "increment_type": "tablespoon"},
        {"name": "rice", "calories": 130, "carb": 28, "protein": 2.7, "fat": 0.3, "increment_type": "grams"},
        {"name": "chicken", "calories": 165, "carb": 0, "protein": 31, "fat": 3.6, "increment_type": "grams"},
        {"name": "peanuts", "calories": 567, "carb": 16, "protein": 25, "fat": 49, "increment_type": "grams"},
        {"name": "cucumber", "calories": 15, "carb": 3.6, "protein": 0.7, "fat": 0.1, "increment_type": "grams"},
        {"name": "anchovies", "calories": 210, "carb": 0, "protein": 20, "fat": 15, "increment_type": "grams"},
    ]

    # Loop through each ingredient and add it to the database
    for ingredient in ingredients_data:
        new_ingredient = Ingredient(
            name=ingredient["name"],
            calories=ingredient["calories"],
            carb=ingredient["carb"],
            protein=ingredient["protein"],
            fat=ingredient["fat"],
            increment_type=ingredient["increment_type"]
        )
        db.session.add(new_ingredient)

    # Commit the changes to the database
    try:
        db.session.commit()
        print("Ingredients successfully added to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding ingredients: {e}")