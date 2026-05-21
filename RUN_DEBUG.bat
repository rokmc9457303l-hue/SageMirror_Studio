@echo off
cd /d C:\SageMirror_Production
echo 🛠️ Sage Mirror DEBUG v13.41 Starting...
python -m streamlit run app_v13_41.py --server.port 8505 --theme.base="dark"
pause