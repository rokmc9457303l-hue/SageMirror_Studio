@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v16.1.8 Starting...
python -m streamlit run app_v16_1_8.py --server.port 8505 --theme.base="dark"
pause

