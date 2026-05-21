@echo off
cd /d C:\SageMirror_Production
echo 🛠️ Sage Mirror DEBUG v14.0 Starting...
python -m streamlit run app_v14.py --server.port 8505 --theme.base="dark"
pause