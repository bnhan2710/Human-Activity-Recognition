@echo off
echo ================================================
echo    PBL4 HAR - FULL SYSTEM TEST
echo ================================================
echo.
echo This script will test the complete flow:
echo   ESP32 -^> Realtime DB -^> FastAPI -^> AI Model -^> Firestore -^> Flutter
echo.

cd /d C:\PBL4\AIBackend

REM Check if venv exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup_backend.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo ================================================
echo STEP 1: Upload test data to Firebase
echo ================================================
echo.
echo Uploading 40 samples (WALKING activity)...
python upload_test_data.py << EOF
2
EOF

timeout /t 3

echo.
echo ================================================
echo STEP 2: Start Backend Server (in new window)
echo ================================================
echo.
start "HAR Backend" cmd /k "cd /d C:\PBL4\AIBackend && venv\Scripts\activate.bat && uvicorn main:app --reload"

echo Waiting for backend to start...
timeout /t 10

echo.
echo ================================================
echo STEP 3: Test prediction
echo ================================================
echo.
python test_realtime_db.py << EOF
2
EOF

echo.
echo ================================================
echo STEP 4: Verify in Firestore
echo ================================================
echo.
echo Check your Firebase Console:
echo https://console.firebase.google.com/project/YOUR_PROJECT/firestore
echo.
echo Collection: activity_predictions
echo Expected: New document with predicted activity
echo.

pause

echo.
echo ================================================
echo STEP 5: Run Flutter App (optional)
echo ================================================
echo.
set /p run_flutter="Do you want to run Flutter app? (y/n): "

if /i "%run_flutter%"=="y" (
    start "Flutter App" cmd /k "cd /d C:\PBL4\PBL4_Backend\flutter_app && flutter run -d chrome"
    echo.
    echo Flutter app starting...
    echo Navigate to Home screen to see realtime activity!
)

echo.
echo ================================================
echo    TEST COMPLETE!
echo ================================================
echo.
echo Summary:
echo 1. Test data uploaded to Realtime DB
echo 2. Backend processed and predicted
echo 3. Results saved to Firestore
echo 4. Flutter app displays realtime updates
echo.
echo Check logs in the Backend window for details.
echo.
pause
