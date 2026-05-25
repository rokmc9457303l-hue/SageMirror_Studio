@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v16.0.3 Starting...
python -m streamlit run app_v16_0_3.py --server.port 8505 --theme.base="dark"
pause

