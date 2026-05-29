@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v17.1.4-B Starting...
python -m streamlit run app_v17_1_4B.py --server.port 8505 --theme.base="dark"
pause
