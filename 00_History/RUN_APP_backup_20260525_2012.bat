@echo off
cd /d C:\SageMirror_Production
echo [MIRROR] Sage Mirror Studio v16.0.2 Starting...
python -m streamlit run app_v16_0_2.py --server.port 8505 --theme.base="dark"
pause

