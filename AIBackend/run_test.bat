@echo off
echo ================================================
echo    PBL4 HAR - TEST WITH REAL DATA
echo ================================================
echo.

cd /d C:\PBL4\AIBackend

REM Activate venv
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo.
echo Choose test option:
echo 1. Upload test data to Firebase
echo 2. Test prediction with existing data
echo 3. Both (upload then test)
echo.

set /p choice="Enter choice (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo Running upload script...
    python upload_test_data.py
) else if "%choice%"=="2" (
    echo.
    echo Make sure backend is running at http://localhost:8000
    echo.
    pause
    python test_realtime_db.py
) else if "%choice%"=="3" (
    echo.
    echo Step 1: Uploading test data...
    python upload_test_data.py
    
    echo.
    echo Step 2: Testing prediction...
    echo Make sure backend is running!
    pause
    python test_realtime_db.py
) else (
    echo Invalid choice!
)

echo.
pause
