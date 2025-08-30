#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣账号管理系统打包脚本
使用 PyInstaller 将程序打包成可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_pyinstaller():
    """检查是否安装了 PyInstaller"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        return False

def install_pyinstaller():
    """安装 PyInstaller"""
    print("正在安装 PyInstaller...")
    try:
        # 使用国内镜像源安装
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "pyinstaller", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"
        ])
        print("✓ PyInstaller 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller 安装失败: {e}")
        return False

def create_spec_file():
    """创建 PyInstaller 配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('1.ico', '.'),
        ('styles.py', '.'),
        ('config.py', '.'),
        ('data_manager.py', '.'),
        ('douban_utils.py', '.'),
        ('douban_xieyi.py', '.'),
        ('liulanqi_gongcaozuo.py', '.'),
        ('renwuliucheng.py', '.'),
        ('suijipingpingxingliucheng.py', '.'),
        ('zhixingliucheng.py', '.'),
        ('utils.py', '.'),
        ('start_api.py', '.'),
        ('handlers', 'handlers'),
        ('ui', 'ui'),
        ('liulanqimokuai', 'liulanqimokuai'),
        ('qitagongju', 'qitagongju'),
        ('tests', 'tests'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'sqlite3',
        'json',
        'logging',
        'asyncio',
        'threading',
        'subprocess',
        'platform',
        'pathlib',
        'random',
        'time',
        'requests',
        'urllib3',
        'playwright',
        'websockets',
        'uvicorn',
        'fastapi',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='豆瓣账号管理系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='1.ico',
)
'''
    
    with open('豆瓣账号管理系统.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✓ 配置文件创建成功")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 使用 Python 模块方式调用 PyInstaller
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller', '--clean', '豆瓣账号管理系统.spec'
        ])
        print("✓ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 构建失败: {e}")
        return False

def copy_additional_files():
    """复制额外的文件到输出目录"""
    dist_dir = Path("dist")
    if not dist_dir.exists():
        return
    
    print("复制额外文件...")
    
    # 复制必要的文件
    files_to_copy = [
        'requirements.txt',
        'README.md',
        'database_schema.md',
        '项目分析.md',
        '制作要求.md',
        '登录账号的流程.md',
    ]
    
    for file_name in files_to_copy:
        if Path(file_name).exists():
            shutil.copy2(file_name, dist_dir)
            print(f"✓ 复制 {file_name}")
    
    # 创建数据目录
    data_dir = dist_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 复制数据文件（如果存在）
    if Path("data").exists():
        for item in Path("data").iterdir():
            if item.is_file():
                shutil.copy2(item, data_dir)
                print(f"✓ 复制数据文件 {item.name}")
    
    print("✓ 额外文件复制完成")

def create_installer():
    """创建安装包（可选）"""
    print("创建安装包...")
    
    # 这里可以添加创建安装包的逻辑
    # 例如使用 Inno Setup 或其他工具
    print("安装包创建功能待实现")

def main():
    """主函数"""
    print("=" * 50)
    print("豆瓣账号管理系统打包工具")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("main.py").exists():
        print("✗ 错误：请在项目根目录运行此脚本")
        return
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            print("✗ 无法安装 PyInstaller，请手动安装")
            return
    
    # 创建配置文件
    create_spec_file()
    
    # 构建可执行文件
    if build_executable():
        # 复制额外文件
        copy_additional_files()
        
        print("\n" + "=" * 50)
        print("打包完成！")
        print("=" * 50)
        print("可执行文件位置: dist/豆瓣账号管理系统.exe")
        print("请将整个 dist 目录分发给用户")
        print("=" * 50)
        
        # 询问是否创建安装包
        try:
            choice = input("\n是否创建安装包？(y/n): ").lower().strip()
            if choice == 'y':
                create_installer()
        except KeyboardInterrupt:
            print("\n用户取消操作")
    else:
        print("✗ 打包失败")

if __name__ == "__main__":
    main()
