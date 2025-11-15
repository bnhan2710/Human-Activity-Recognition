@echo off
echo Replacing test_realtime_db.py with fixed version...

cd /d C:\PBL4\AIBackend

if exist test_realtime_db.py (
    del test_realtime_db.py
)

copy test_realtime_db_fixed.py test_realtime_db.py

echo Done!
echo Now you can run: python test_realtime_db.py
pause
