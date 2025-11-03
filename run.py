#!/usr/bin/env python3
"""
CT Review Tool - Hawkeye AI Analysis
Deployment script for the web application
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Create necessary directories
    try:
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('outputs', exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directories: {e}")
    
    # Get port from environment (Railway, Heroku) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Set environment variables for production
    if len(sys.argv) > 1 and sys.argv[1] == 'production':
        app.config['DEBUG'] = False
        app.config['ENV'] = 'production'
        print("Starting CT Review Tool in PRODUCTION mode...")
        print(f"Access the application at: http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        app.config['DEBUG'] = True
        app.config['ENV'] = 'development'
        print("Starting CT Review Tool in DEVELOPMENT mode...")
        print(f"Access the application at: http://localhost:{port}")
        print("Debug mode is enabled - changes will auto-reload")
        app.run(host='0.0.0.0', port=port, debug=True)