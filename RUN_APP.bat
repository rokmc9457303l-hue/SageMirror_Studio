@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio Starting...
python -m streamlit run "00_History\app_v13_v13.1_20260515_1800.py" --server.port 8505 --theme.base="dark"
pause