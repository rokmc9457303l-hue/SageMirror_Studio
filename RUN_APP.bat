@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v16.1.4 Starting...
python -m streamlit run app_v16_1_4.py --server.port 8505 --theme.base="dark"
pause

