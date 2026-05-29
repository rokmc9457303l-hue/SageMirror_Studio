@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v17.1.4-A Starting...
python -m streamlit run app_v17_1_4A.py --server.port 8505 --theme.base="dark"
pause
