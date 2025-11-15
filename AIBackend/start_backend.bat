@echo off
echo ================================================
echo    PBL4 HAR - Starting Backend Server
echo ================================================
echo.

cd /d C:\PBL4\AIBackend

REM Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if packages are installed
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Installing dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
    echo.
    echo ✅ Dependencies installed!
)

echo.
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo Docs available at: http://localhost:8000/docs
echo.

python main.py

pause
