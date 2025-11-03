"""
Configuration settings for CT Review Tool
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ct-review-tool-secret-key-change-in-production'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    ALLOWED_EXTENSIONS = {'docx'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # AWS Bedrock settings
    AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    # Application settings
    HAWKEYE_SECTIONS = {
        1: "Initial Assessment",
        2: "Investigation Process", 
        3: "Seller Classification",
        4: "Enforcement Decision-Making",
        5: "Additional Verification (High-Risk Cases)",
        6: "Multiple Appeals Handling",
        7: "Account Hijacking Prevention",
        8: "Funds Management",
        9: "REs-Q Outreach Process",
        10: "Sentiment Analysis",
        11: "Root Cause Analysis",
        12: "Preventative Actions",
        13: "Documentation and Reporting",
        14: "Cross-Team Collaboration",
        15: "Quality Control",
        16: "Continuous Improvement",
        17: "Communication Standards",
        18: "Performance Metrics",
        19: "Legal and Compliance",
        20: "New Service Launch Considerations"
    }
    
    STANDARD_SECTIONS = [
        "Executive Summary",
        "Background",
        "Resolving Actions",
        "Root Cause",
        "Preventative Actions",
        "Investigation Process",
        "Seller Classification",
        "Documentation and Reporting",
        "Impact Assessment",
        "Timeline",
        "Recommendations"
    ]
    
    EXCLUDED_SECTIONS = [
        "Original Email",
        "Email Correspondence",
        "Raw Data",
        "Logs",
        "Attachments"
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-THIS-IN-PRODUCTION'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}