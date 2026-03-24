@echo off
setlocal
:loop
echo [%date% %time%] Starting SHx Tip Bot...
.\venv\Scripts\python.exe bot.py
echo [%date% %time%] Bot exited with code %errorlevel%. Restarting in 5 seconds...
timeout /t 5
goto loop
