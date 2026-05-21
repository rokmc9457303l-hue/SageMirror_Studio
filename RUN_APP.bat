@echo off
cd /d C:\SageMirror_Production
echo Sage Mirror Studio v13.29 Starting...
python -m streamlit run app_v13_29.py --server.port 8505 --theme.base="dark"
pause