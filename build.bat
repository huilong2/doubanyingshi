@echo off
chcp 65001 >nul
echo ================================================
echo 豆瓣账号管理系统打包工具
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

echo ✓ Python已安装
echo.

REM 检查是否在正确的目录
if not exist "main.py" (
    echo 错误：请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo ✓ 在正确的目录中
echo.

REM 检查并安装PyInstaller
echo 检查PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    python -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if errorlevel 1 (
        echo 错误：PyInstaller安装失败
        pause
        exit /b 1
    )
    echo ✓ PyInstaller安装成功
) else (
    echo ✓ PyInstaller已安装
)

echo.
echo 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

REM 执行打包命令
pyinstaller --onefile --windowed --icon=1.ico --name="豆瓣账号管理系统" --add-data="data;data" --add-data="1.ico;." --add-data="styles.py;." --add-data="config.py;." --add-data="data_manager.py;." --add-data="douban_utils.py;." --add-data="douban_xieyi.py;." --add-data="liulanqi_gongcaozuo.py;." --add-data="renwuliucheng.py;." --add-data="suijipingpingxingliucheng.py;." --add-data="zhixingliucheng.py;." --add-data="utils.py;." --add-data="start_api.py;." --add-data="handlers;handlers" --add-data="ui;ui" --add-data="liulanqimokuai;liulanqimokuai" --add-data="qitagongju;qitagongju" --add-data="tests;tests" --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtGui --hidden-import=PySide6.QtWidgets --hidden-import=sqlite3 --hidden-import=json --hidden-import=logging --hidden-import=asyncio --hidden-import=threading --hidden-import=subprocess --hidden-import=platform --hidden-import=pathlib --hidden-import=random --hidden-import=time --hidden-import=requests --hidden-import=urllib3 --hidden-import=playwright --hidden-import=websockets --hidden-import=uvicorn --hidden-import=fastapi --hidden-import=pydantic main.py

if errorlevel 1 (
    echo.
    echo ✗ 打包失败
    echo 请检查错误信息并重试
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✓ 打包成功！
echo ================================================
echo 可执行文件位置: dist\豆瓣账号管理系统.exe
echo 请将整个 dist 目录分发给用户
echo ================================================
echo.

REM 询问是否打开输出目录
set /p choice="是否打开输出目录？(y/n): "
if /i "%choice%"=="y" (
    explorer dist
)

pause
