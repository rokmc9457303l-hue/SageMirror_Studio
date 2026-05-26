@echo off

cd /d C:\SageMirror_Production

echo ======================================
echo Sage Mirror Debug Mode
echo ======================================

python -m py_compile app_v16_1_15.py
python -m py_compile sage_popups.py
python -m py_compile rag_memory_utils.py
python -m py_compile rag_tag_system.py
python -m py_compile memory_state_manager.py
python -m py_compile research_router.py
python -m py_compile agent_toolkit.py
python -m py_compile agent_registry.py

if errorlevel 1 (
    echo.
    echo [ERROR] Compile Failed
    pause
    exit /b
)

echo.
echo [OK] Compile Success
echo.

python -m streamlit run app_v16_1_15.py --server.port 8505

pause