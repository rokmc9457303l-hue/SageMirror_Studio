@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v15.9.34.21 Starting...
python -m streamlit run app_v15_9_34_21.py --server.port 8505 --theme.base="dark"
pause
