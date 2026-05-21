@echo off
cd /d C:\SageMirror_Production
echo ? Sage Mirror Studio v13.27 Starting...
python -m streamlit run app_v13_27.py --server.port 8505 --theme.base="dark"
pause