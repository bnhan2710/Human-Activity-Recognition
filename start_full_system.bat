@echo off
echo ================================================
echo    PBL4 HAR SYSTEM - FULL START
echo ================================================
echo.

echo [1/3] Pairing Bluetooth...
call auto_pair_bluetooth.bat

echo.
echo [2/3] Starting Backend Server...
start "HAR Backend" cmd /k "cd /d C:\PBL4\AIBackend && start_backend.bat"

timeout /t 5

echo.
echo [3/3] Starting Flutter App...
start "Flutter App" cmd /k "cd /d C:\PBL4\PBL4_Backend\flutter_app && flutter run -d chrome"

echo.
echo ================================================
echo    SYSTEM STARTED!
echo ================================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Flutter App: Opening in Chrome...
echo.
echo Check backend logs in the Backend window
echo Check Flutter logs in the Flutter window
echo.
pause
