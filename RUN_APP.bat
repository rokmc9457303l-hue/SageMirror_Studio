@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio Starting...
python -m streamlit run app_v15.py --server.port 8505 --theme.base="dark"
pause