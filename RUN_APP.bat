@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio v13.23 Starting...
python -m streamlit run app_v13_23.py --server.port 8505 --theme.base="dark"
pause