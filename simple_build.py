#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版打包脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("豆瓣账号管理系统 - 简化打包脚本")
    print("=" * 40)
    
    # 检查是否在正确的目录
    if not Path("main.py").exists():
        print("错误：请在项目根目录运行此脚本")
        return
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "pyinstaller", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"
            ])
            print("✓ PyInstaller 安装成功")
        except:
            print("✗ PyInstaller 安装失败，请手动安装：pip install pyinstaller")
            return
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # 打包成单个文件
        "--windowed",  # 无控制台窗口
        "--icon=1.ico",  # 设置图标
        "--name=豆瓣账号管理系统",  # 设置名称
        "--add-data=data;data",  # 添加数据目录
        "--add-data=1.ico;.",  # 添加图标
        "--add-data=styles.py;.",  # 添加样式文件
        "--add-data=config.py;.",  # 添加配置文件
        "--add-data=data_manager.py;.",  # 添加数据管理器
        "--add-data=douban_utils.py;.",  # 添加豆瓣工具
        "--add-data=douban_xieyi.py;.",  # 添加豆瓣协议
        "--add-data=liulanqi_gongcaozuo.py;.",  # 添加浏览器操作
        "--add-data=renwuliucheng.py;.",  # 添加任务流程
        "--add-data=suijipingpingxingliucheng.py;.",  # 添加随机评论流程
        "--add-data=zhixingliucheng.py;.",  # 添加执行流程
        "--add-data=utils.py;.",  # 添加工具文件
        "--add-data=start_api.py;.",  # 添加API启动文件
        "--add-data=handlers;handlers",  # 添加处理器目录
        "--add-data=ui;ui",  # 添加UI目录
        "--add-data=liulanqimokuai;liulanqimokuai",  # 添加浏览器模块
        "--add-data=qitagongju;qitagongju",  # 添加其他工具
        "--add-data=tests;tests",  # 添加测试目录
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=sqlite3",
        "--hidden-import=json",
        "--hidden-import=logging",
        "--hidden-import=asyncio",
        "--hidden-import=threading",
        "--hidden-import=subprocess",
        "--hidden-import=platform",
        "--hidden-import=pathlib",
        "--hidden-import=random",
        "--hidden-import=time",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=playwright",
        "--hidden-import=websockets",
        "--hidden-import=uvicorn",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "main.py"
    ]
    
    print("开始打包...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 40)
        print("✓ 打包成功！")
        print("可执行文件位置: dist/豆瓣账号管理系统.exe")
        print("=" * 40)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()
