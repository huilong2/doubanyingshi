@echo off
chcp 65001
echo ========================================
echo 豆瓣账号管理系统 - 启动器
echo ========================================
echo.

cd /d "%~dp0"
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "temp" mkdir temp
if not exist "backup" mkdir backup

echo 正在启动程序...
start "" "豆瓣账号管理系统.exe"

echo.
echo 程序已启动
pause
