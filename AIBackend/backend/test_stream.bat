@echo off
REM Test Firebase Realtime Stream
REM This script tests the complete flow: Realtime DB -> Prediction -> Firestore

echo ========================================
echo  Firebase Realtime Stream Test
echo ========================================
echo.

cd /d %~dp0

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using global Python...
)

echo.
echo Starting test script...
echo.

python test_stream.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo  ERROR: Test failed!
    echo ========================================
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================
echo  Test complete!
echo ========================================
echo.
pause
