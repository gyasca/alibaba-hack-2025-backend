from extensions import db
from models.skin_analysis import SkinAnalysis

def create_skin_analyses_table():
    # Create the table
    sql = """
    CREATE TABLE IF NOT EXISTS skin_analyses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        image_url TEXT,
        predictions JSON NOT NULL,
        notes TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    try:
        db.session.execute(sql)
        db.session.commit()
        print("skin_analyses table created successfully")
    except Exception as e:
        print(f"Error creating skin_analyses table: {e}")
        db.session.rollback()