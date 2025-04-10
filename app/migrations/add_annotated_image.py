from extensions import db
from sqlalchemy import text

def add_annotated_image_column():
    sql = text("""
    ALTER TABLE skin_analyses 
    ADD COLUMN annotated_image_url TEXT;
    """)
    
    try:
        db.session.execute(sql)
        db.session.commit()
        print("Added annotated_image_url column successfully")
    except Exception as e:
        print(f"Error adding column: {e}")
        db.session.rollback()