#!/bin/bash

echo "========================================"
echo "CT Review Tool - Deployment Script"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python is installed"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not available"
    echo "Please ensure pip is installed with Python"
    exit 1
fi

echo "✓ pip is available"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Create necessary directories
mkdir -p uploads
mkdir -p outputs
mkdir -p templates

echo "✓ Directories created"

# Make run script executable
chmod +x run.py

echo
echo "========================================"
echo "Deployment completed successfully!"
echo "========================================"
echo
echo "To start the application:"
echo "  Development mode: python run.py"
echo "  Production mode:  python run.py production"
echo
echo "The application will be available at:"
echo "  http://localhost:5000"
echo