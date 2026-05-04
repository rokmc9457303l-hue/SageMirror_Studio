@echo off
echo [SYSTEM] Starting CapCut Auto Assembler...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit
)
python "C:\Users\admin\Downloads\AI-Project\CapCut_Auto_Assembler.py"
if %errorlevel% neq 0 (
    echo [ERROR] Script failed to run.
    pause
)
exit
