@echo off
cd /d C:\SageMirror_Production
echo [CHECK] py_compile...
python -m py_compile app_v17_1_4B.py sage_popups_v17_1_4B.py memory_state_manager.py rag_memory_utils.py rag_tag_system.py research_router.py agent_toolkit.py agent_registry.py
if errorlevel 1 (
    echo [ERROR] Compile failed.
    pause
    exit /b 1
)
echo [MIRROR] Sage Mirror Studio v17.1.4-B Debug Starting...
python -m streamlit run app_v17_1_4B.py --server.port 8505 --theme.base="dark"
pause
