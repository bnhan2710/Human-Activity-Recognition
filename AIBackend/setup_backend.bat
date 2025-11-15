@echo off
echo ================================================
echo    PBL4 HAR - Setup Backend Environment
echo ================================================
echo.

cd /d C:\PBL4\AIBackend

REM Delete old venv if exists
if exist venv (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

REM Create new venv
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies quickly (prefer binary wheels)
echo.
echo Installing dependencies (this may take a few minutes)...
echo.

echo [1/10] Installing FastAPI...
pip install --no-cache-dir fastapi

echo [2/10] Installing Uvicorn...
pip install --no-cache-dir "uvicorn[standard]"

echo [3/10] Installing Pydantic...
pip install --no-cache-dir pydantic

echo [4/10] Installing NumPy...
pip install --no-cache-dir "numpy<2.0.0"

echo [5/10] Installing Pandas...
pip install --no-cache-dir pandas

echo [6/10] Installing Scikit-learn...
pip install --no-cache-dir scikit-learn

echo [7/10] Installing TensorFlow (may take longer)...
pip install --no-cache-dir tensorflow

echo [8/10] Installing Firebase Admin...
pip install --no-cache-dir firebase-admin

echo [9/10] Installing Python Multipart...
pip install --no-cache-dir python-multipart

echo [10/10] Installing Requests...
pip install --no-cache-dir requests

echo.
echo ================================================
echo    SETUP COMPLETE!
echo ================================================
echo.
echo Installed packages:
pip list
echo.
echo Next steps:
echo 1. Put your serviceAccountKey.json in C:\PBL4\AIBackend\
echo 2. Put your model file in C:\PBL4\AIBackend\AI\models\best_model.h5
echo 3. Run: start_backend.bat
echo.
pause
