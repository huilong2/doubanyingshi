@echo off
chcp 65001
echo ========================================
echo �����˺Ź���ϵͳ - ������
echo ========================================
echo.

cd /d "%~dp0"
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "temp" mkdir temp
if not exist "backup" mkdir backup

echo ������������...
start "" "�����˺Ź���ϵͳ.exe"

echo.
echo ����������
pause
