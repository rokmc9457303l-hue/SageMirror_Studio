@echo off
echo [안전 실행] 모든 파이썬 프로세스를 종료하고 깨끗하게 시작합니다...
taskkill /f /im python.exe /t
taskkill /f /im ollama.exe /t

echo [로그 찌꺼기 제거] 582KB 오류 로그를 삭제합니다...
del /f /q "*.log" 2>nul

echo [앱 가동] 현자의 거울 스튜디오를 실행합니다.
python app_v17_1_22.py
pause