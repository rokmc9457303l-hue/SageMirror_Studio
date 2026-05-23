@echo off
echo [MIRROR] Sage Mirror Studio Stopping (Port: 8505)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr 8505') do (
    taskkill /f /pid %%a
)
echo [MIRROR] Stopped successfully!
pause
