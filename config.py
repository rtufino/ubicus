import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    # Use a simpler SQLite database path
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///products.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 31536000  # 1 year in seconds
    REMEMBER_COOKIE_DURATION = 31536000    # 1 year in seconds
    REMEMBER_COOKIE_SECURE = False         # Set to True in production with HTTPS
    REMEMBER_COOKIE_HTTPONLY = True