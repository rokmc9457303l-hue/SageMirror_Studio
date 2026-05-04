@echo off
chcp 65001 >nul
echo [SYSTEM] Starting GitHub Backup...
echo ==========================================

:: Check Git installation
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git from https://git-scm.com/
    pause
    exit /b
)

:: Re-setup repository
echo [1/4] Initializing Git...
git init
git remote remove origin >nul 2>&1
git remote add origin https://github.com/rokmc9457303l-hue/AI-.git
git branch -M main

:: Add and Commit
echo [2/4] Adding files...
git add .
echo [3/4] Committing...
git commit -m "Organized P-Reinforce Structure"

:: Push
echo [4/4] Uploading to GitHub...
echo If a login window appears, please sign in.
git push -u origin main --force

echo.
echo ==========================================
echo   BACKUP FINISHED! 
echo   Check your GitHub page now.
echo ==========================================
pause
