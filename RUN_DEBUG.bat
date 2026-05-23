@echo off
cd /d C:\SageMirror_Production
echo [DEBUG] Sage Mirror DEBUG v15.0 Starting...
python -m streamlit run app_v15_9_15.py --server.port 8505 --theme.base="dark"
pause
