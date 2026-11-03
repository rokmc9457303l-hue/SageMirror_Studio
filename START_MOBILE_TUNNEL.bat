@echo off
REM ============================================================
REM  Sage Mirror Studio - Phone access via ngrok
REM  1) Starts the Streamlit app on port 8505 (new window)
REM  2) Opens an ngrok tunnel to it, protected by a password
REM  Open the https://xxxx.ngrok-free.app URL shown below on your phone.
REM ============================================================
setlocal
set PORT=8505
set APP_VER=app_v17_2_3.py

REM --- Change these before first use (password: 8+ chars) ---
set NGROK_USER=mirror
set NGROK_PASS=ChangeThisPassword123

where ngrok >nul 2>nul
if errorlevel 1 (
  echo [ERROR] ngrok not found in PATH.
  echo   Install: https://ngrok.com/download  then run once:
  echo   ngrok config add-authtoken YOUR_TOKEN
  pause
  exit /b 1
)

cd /d "%~dp0"

REM Start the app only if the port is not already in use
netstat -ano | findstr ":%PORT% " | findstr LISTENING >nul
if errorlevel 1 (
  echo [MIRROR] Starting app on port %PORT% ...
  start "SageMirror App" cmd /k python -m streamlit run %APP_VER% --server.port %PORT% --server.headless true --theme.base="dark"
  timeout /t 8 /nobreak >nul
) else (
  echo [MIRROR] App already running on port %PORT%.
)

echo [MIRROR] Starting ngrok tunnel (Port: %PORT%) ...
ngrok http %PORT% --basic-auth "%NGROK_USER%:%NGROK_PASS%"
pause
