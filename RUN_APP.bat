@echo off
set APP_VER=app_v17_1_6.py
set PORT=8505
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v17.1.6 Starting...
python -m streamlit run %APP_VER% --server.port %PORT% --theme.base="dark"
pause
