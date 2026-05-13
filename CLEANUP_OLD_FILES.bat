@echo off
title Sage Mirror Studio - Directory Cleanup
chcp 65001 >nul

echo ========================================
echo  Sage Mirror Studio - 폴더 대청소 시작
echo ========================================
echo.

cd /d C:\SageMirror_Production

echo 1. 백업 폴더(_ZZ_OLD_BACKUP) 생성 중...
if not exist _ZZ_OLD_BACKUP mkdir _ZZ_OLD_BACKUP

echo 2. 예전 파일들 백업 폴더로 이동 중...
move 00_v*.bat _ZZ_OLD_BACKUP\ >nul 2>&1
move 00_긴급진단*.bat _ZZ_OLD_BACKUP\ >nul 2>&1
move 00_브리지서버*.bat _ZZ_OLD_BACKUP\ >nul 2>&1
move SageMirror.py _ZZ_OLD_BACKUP\ >nul 2>&1
move app.py _ZZ_OLD_BACKUP\ >nul 2>&1
move app_v7.2*.py _ZZ_OLD_BACKUP\ >nul 2>&1
move server.py _ZZ_OLD_BACKUP\ >nul 2>&1
move server_v*.py _ZZ_OLD_BACKUP\ >nul 2>&1
move 시스템_진단.py _ZZ_OLD_BACKUP\ >nul 2>&1
move 작업일지.md _ZZ_OLD_BACKUP\ >nul 2>&1
move 현자의거울*.bat _ZZ_OLD_BACKUP\ >nul 2>&1

echo.
echo ========================================
echo  청소 완료! 딱 6개의 핵심 파일만 남았습니다.
echo  (삭제되지 않고 _ZZ_OLD_BACKUP 폴더 안에 안전하게 보관됨)
echo ========================================
echo.
pause
del "%~f0"
