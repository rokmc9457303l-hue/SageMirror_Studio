@echo off
cd /d C:\SageMirror_Production
echo 🛠️ Sage Mirror DEBUG v13.38 Starting...
python -m streamlit run app_v13_38.py --server.port 8505 --theme.base="dark"
pause