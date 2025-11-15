@echo off
echo ================================================
echo    QUICK INSTALL (Binary Only)
echo ================================================
echo.

cd /d C:\PBL4\AIBackend

if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing packages (binary wheels only)...
pip install --upgrade pip --quiet

REM Install binary wheels only (no source compilation)
pip install --only-binary :all: fastapi uvicorn pydantic numpy pandas scikit-learn requests python-multipart

REM TensorFlow and Firebase require special handling
pip install tensorflow firebase-admin

echo.
echo ✅ Done! Run: start_backend.bat
pause
