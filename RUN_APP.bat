@echo off
title Sage Mirror Studio v11.0 (Design Edition)

echo [1/3] Closing old servers...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8501" ^| find "LISTENING"') do (
    echo Killing old Streamlit process %%a on port 8501...
    taskkill /F /PID %%a >nul 2>&1
)

cd /d C:\SageMirror_Production

echo ========================================
echo  Sage Mirror Studio v11.0
echo  Python: C:\Python314\python.exe
echo  App Ver: app_v11.py
echo  Lock: OS-level Read-Only Active
echo ========================================
echo.

set PYTHON=C:\Python314\python.exe

echo [2/3] Checking Dependencies...
"%PYTHON%" -m pip install streamlit ollama requests GitPython pandas --quiet

echo [3/3] Starting v11.0 App...
echo.
echo    http://localhost:8501
echo    Password: master1234
echo    PIN: 7777
echo.

"%PYTHON%" -m streamlit run app_v11.py --server.port 8501 --server.headless false

pause
