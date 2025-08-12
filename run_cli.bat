@echo off
echo Product Description Generator - Command Line Interface
echo.
echo Usage examples:
echo   python main.py setup
echo   python main.py test "XJG104HDG" "Eaton Crouse-Hinds"
echo   python main.py process OPENAI.csv
echo.
python main.py %*
pause 