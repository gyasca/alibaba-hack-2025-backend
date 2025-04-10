from extensions import db
from flask import current_app
from sqlalchemy import text

def init_db():
    with current_app.app_context():
        # Create the skin_analyses table
        sql = text("""
        CREATE TABLE IF NOT EXISTS skin_analyses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            image_url LONGTEXT,
            predictions JSON,
            notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        try:
            # Execute the SQL with text() wrapper
            db.session.execute(sql)
            db.session.commit()
            print("Database tables initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()
            raise