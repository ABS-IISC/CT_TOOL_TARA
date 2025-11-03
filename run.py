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
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    
    # Set environment variables for production
    if len(sys.argv) > 1 and sys.argv[1] == 'production':
        app.config['DEBUG'] = False
        app.config['ENV'] = 'production'
        print("Starting CT Review Tool in PRODUCTION mode...")
        print("Access the application at: http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        app.config['DEBUG'] = True
        app.config['ENV'] = 'development'
        print("Starting CT Review Tool in DEVELOPMENT mode...")
        print("Access the application at: http://localhost:5000")
        print("Debug mode is enabled - changes will auto-reload")
        app.run(host='0.0.0.0', port=5000, debug=True)