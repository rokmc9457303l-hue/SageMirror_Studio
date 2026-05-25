@echo off

cd /d C:\SageMirror_Production

echo ======================================
echo Sage Mirror Debug Mode
echo ======================================

python -m py_compile app_v16_1_2.py
python -m py_compile sage_popups.py
python -m py_compile rag_memory_utils.py

if errorlevel 1 (
    echo.
    echo [ERROR] Compile Failed
    pause
    exit /b
)

echo.
echo [OK] Compile Success
echo.

python -m streamlit run app_v16_1_2.py --server.port 8505

pause