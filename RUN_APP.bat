@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio v13.16 Starting...
python -m streamlit run app_v13_16.py --server.port 8505 --theme.base="dark"
pause