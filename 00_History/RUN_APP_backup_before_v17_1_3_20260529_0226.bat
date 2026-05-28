@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v17.1.2 Starting...
python -m streamlit run app_v17_1_2.py --server.port 8505 --theme.base="dark"
pause
