@echo off
echo ========================================
echo CT Review Tool - Deployment Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo ✓ Python is installed

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✓ pip is available

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo ✓ Dependencies installed

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "templates" mkdir templates

echo ✓ Directories created

echo.
echo ========================================
echo Deployment completed successfully!
echo ========================================
echo.
echo To start the application:
echo   Development mode: python run.py
echo   Production mode:  python run.py production
echo.
echo The application will be available at:
echo   http://localhost:5000
echo.
pause