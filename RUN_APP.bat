@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio v13.8 Starting...
python -m streamlit run app_v13_8.py --server.port 8505 --theme.base="dark"
pause