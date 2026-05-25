@echo off

cd /d C:\SageMirror_Production

echo ======================================
echo Sage Mirror Debug Mode
echo ======================================

python -m py_compile app_v15_9_34_19.py
python -m py_compile sage_popups.py

if errorlevel 1 (
    echo.
    echo [ERROR] Compile Failed
    pause
    exit /b
)

echo.
echo [OK] Compile Success
echo.

python -m streamlit run app_v15_9_34_19.py

pause