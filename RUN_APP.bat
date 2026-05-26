@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v16.1.9 Starting...
python -m streamlit run app_v16_1_9.py --server.port 8505 --theme.base="dark"
pause

