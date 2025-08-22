#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    print("豆瓣账号管理系统 - exe打包工具")
    
    # 安装PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller已安装")
    except ImportError:
        print("安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 创建spec文件
    spec = '''# -*- mode: python ; coding: utf-8 -*-
datas = [
    ('data', 'data'),
    ('styles.py', '.'),
    ('database_manager.py', '.'),
    ('mokuai_chagyong.py', '.'),
    ('mokuai_liulanqi.py', '.'),
    ('mokuai_zhiwen.py', '.'),
    ('mikuai_youjian.py', '.'),
    ('data_file_manager.py', '.'),
    ('utils.py', '.'),
]
hiddenimports = ['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'sqlite3', 'playwright', 'beautifulsoup4', 'requests']
a = Analysis(['main.py'], datas=datas, hiddenimports=hiddenimports)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='豆瓣账号管理系统', console=False)
'''
    
    with open('豆瓣账号管理系统.spec', 'w', encoding='utf-8') as f:
        f.write(spec)
    
    print("✅ 已创建spec文件")
    
    # 构建exe
    print("🚀 开始构建...")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "豆瓣账号管理系统.spec"]
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ 构建成功！")
        print(f"📁 exe文件: {os.path.abspath('dist/豆瓣账号管理系统.exe')}")
    else:
        print("❌ 构建失败")

if __name__ == "__main__":
    main() 