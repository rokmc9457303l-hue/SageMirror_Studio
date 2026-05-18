@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio v13.9 Starting...
python -m streamlit run app_v13_9.py --server.port 8505 --theme.base="dark"
pause