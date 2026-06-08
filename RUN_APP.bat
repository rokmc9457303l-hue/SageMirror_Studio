@echo off
echo [안전 실행] 뒤에 숨어있는 낡은 유령 프로세스들을 전부 강제 종료합니다...
taskkill /f /im python.exe /t 2>nul
taskkill /f /im ollama.exe /t 2>nul

set APP_VER=app_v17_1_27.py
set PORT=8505
cd /d C:\SageMirror_Production

echo [MIRROR] Sage Mirror Studio v17.1.27 Starting...
python -m streamlit run %APP_VER% --server.port %PORT% --theme.base="dark"
pause