import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Firebase configuration options
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
    FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')
    FIREBASE_CREDENTIALS_BASE64 = os.getenv('FIREBASE_CREDENTIALS_BASE64')
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    
    # Hotel default configuration
    HOTEL_NAME = "Nur-e-Haya Luxury Resort & Hotel"
    HOTEL_CURRENCY = "INR"
    HOTEL_CURRENCY_SYMBOL = "₹"
    HOTEL_TAX_PERCENT = 5.0
    MEMBER_DISCOUNT_PERCENT = 5.0

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
