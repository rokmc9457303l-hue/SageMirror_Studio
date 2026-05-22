@echo off
cd /d C:\SageMirror_Production
echo ?› ï¸?Sage Mirror DEBUG v15.0 Starting...
python -m streamlit run app_v15_9_8.py --server.port 8505 --theme.base="dark"
pause
