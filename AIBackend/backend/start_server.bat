@echo off
echo ========================================
echo Starting Human Activity Recognition API
echo ========================================
echo.
echo API will be available at:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo API Documentation:
echo   - http://localhost:8000/docs
echo   - http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
python main.py

pause
