@echo off
echo ========================================
echo Product Description Generator Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Install Ollama from https://ollama.ai/
echo 2. Run: python main.py setup
echo 3. Test with: python main.py test "XJG104HDG" "Eaton Crouse-Hinds"
echo.
echo Or run the GUI version: python gui.py
echo.
pause 