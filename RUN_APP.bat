@echo off
cd /d C:\SageMirror_Production
echo 🪞 Sage Mirror Studio v13.2 Starting...
python -m streamlit run app_v13_2.py --theme.base="dark"
pause