@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v16.1.18 Starting...
python -m streamlit run app_v16_1_18.py --server.port 8505 --theme.base="dark"
pause
