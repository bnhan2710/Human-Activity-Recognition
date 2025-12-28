@echo off
echo Cleaning up old screen files...

cd /d c:\PBL4\PBL4_Backend\flutter_app\lib\screens

REM Delete old broken files
if exist home_screen_broken.dart del /f home_screen_broken.dart
if exist home_screen_new.dart del /f home_screen_new.dart
if exist calo_screen_firebase.dart del /f calo_screen_firebase.dart
if exist calo_screen_firebase.dart.backup del /f calo_screen_firebase.dart.backup
if exist calo_screen_firebase.dart.broken del /f calo_screen_firebase.dart.broken
if exist history_screen_firebase_old.dart del /f history_screen_firebase_old.dart
if exist settings_screen.dart del /f settings_screen.dart
if exist settings_screen_old_broken.dart del /f settings_screen_old_broken.dart

REM Rename clean files to proper names
if exist calo_screen_firebase_fixed.dart (
    echo Renaming calo_screen_firebase_fixed.dart to calo_screen_firebase.dart
    ren calo_screen_firebase_fixed.dart calo_screen_firebase.dart
)

if exist history_screen_firebase_clean.dart (
    echo Renaming history_screen_firebase_clean.dart to history_screen_firebase.dart
    if exist history_screen_firebase.dart del /f history_screen_firebase.dart
    ren history_screen_firebase_clean.dart history_screen_firebase.dart
)

if exist settings_screen_new.dart (
    echo Renaming settings_screen_new.dart to settings_screen.dart
    ren settings_screen_new.dart settings_screen.dart
)

echo.
echo Cleanup complete!
echo.
echo Remaining screen files:
dir /b *.dart

pause
