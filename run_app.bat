@echo off
echo ===================================================
echo Starting CollegeConnect Application Server...
echo Unified Server (Flask REST APIs + Web Interface)
echo URL: http://localhost:5000
echo ===================================================
python "%~dp0backend\app.py"
pause
