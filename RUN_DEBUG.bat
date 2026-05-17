@echo off
cd /d C:\SageMirror_Production
echo 현재 폴더: %CD%
echo.
streamlit run app.py
echo.
echo 오류가 발생했습니다. 위 메시지를 확인하세요.
pause