import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_DATABASE_URI")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = os.getenv("JWT_TOKEN_LOCATION")
    JWT_HEADER_NAME = os.getenv("JWT_HEADER_NAME")
    JWT_HEADER_TYPE = os.getenv("JWT_HEADER_TYPE")
    JWT_ACCESS_TOKEN_EXPIRES = os.getenv("JWT_ACCESS_TOKEN_EXPIRES")
    RYAN_API_KEY = os.getenv("RYAN_API_KEY")
    GREGORY_GEMINI_API_KEY = os.getenv("GREGORY_GEMINI_API_KEY")