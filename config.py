#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序配置文件
统一管理所有路径和配置设置
"""

import os
import platform
from pathlib import Path

class ProgramConfig:
    """程序配置类"""
    
    def __init__(self):
        # 获取程序根目录
        self.program_root = self._get_program_root()
        
        # 初始化目录结构
        self.init_directories()
    
    def _get_program_root(self):
        """获取程序根目录，兼容exe打包后的情况"""
        import sys
        
        # 如果是打包后的exe
        if getattr(sys, 'frozen', False):
            # 使用exe文件所在目录
            return Path(sys.executable).parent
        else:
            # 开发环境，使用脚本所在目录
            return Path(__file__).parent
    
    def init_directories(self):
        """初始化程序目录结构"""
        # 数据目录 - 存储数据库、配置文件等
        self.data_dir = self.program_root / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 日志目录 - 存储程序日志
        self.logs_dir = self.program_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 缓存目录 - 存储浏览器缓存、临时文件等
        self.cache_dir = self.program_root / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # 临时文件目录
        self.temp_dir = self.program_root / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 备份目录
        self.backup_dir = self.program_root / "backup"
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_database_path(self):
        """获取数据库文件路径"""
        return self.data_dir / "accounts.db"
    
    def get_config_path(self):
        """获取配置文件路径"""
        return self.data_dir / "peizhi.json"
    
    def get_log_path(self):
        """获取日志文件路径"""
        return self.logs_dir / "app.log"
    
    def get_cache_path(self):
        """获取缓存目录路径"""
        return self.cache_dir
    
    def get_temp_path(self):
        """获取临时文件目录路径"""
        return self.temp_dir
    
    def get_backup_path(self):
        """获取备份目录路径"""
        return self.backup_dir
    
    def get_browser_cache_path(self, username):
        """获取指定用户的浏览器缓存路径"""
        return self.cache_dir / username
    
    def get_system_info(self):
        """获取系统信息"""
        return {
            'system': platform.system(),
            'version': platform.version(),
            'architecture': platform.architecture(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    
    def get_default_browser_paths(self):
        """获取默认浏览器路径"""
        system = platform.system()
        
        if system == "Windows":
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
            
            return [
                f"{program_files}\\Google\\Chrome\\Application\\chrome.exe",
                f"{program_files_x86}\\Google\\Chrome\\Application\\chrome.exe",
                f"{program_files}\\Microsoft\\Edge\\Application\\msedge.exe",
                f"{program_files_x86}\\Microsoft\\Edge\\Application\\msedge.exe",
                f"{program_files}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                f"{program_files_x86}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                f"{program_files}\\Opera\\launcher.exe",
                f"{program_files_x86}\\Opera\\launcher.exe",
                f"{program_files}\\Mozilla Firefox\\firefox.exe",
                f"{program_files_x86}\\Mozilla Firefox\\firefox.exe"
            ]
        
        elif system == "Darwin":  # macOS
            return [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                "/Applications/Opera.app/Contents/MacOS/Opera",
                "/Applications/Safari.app/Contents/MacOS/Safari"
            ]
        
        else:  # Linux
            return [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/microsoft-edge",
                "/usr/bin/brave-browser",
                "/usr/bin/opera",
                "/usr/bin/firefox"
            ]
    
    def get_program_info(self):
        """获取程序信息"""
        return {
            'name': '豆瓣影视更新系统',
            'version': '1.0.0',
            'description': 'Windows 适配版本',
            'author': 'System',
            'program_root': str(self.program_root),
            'data_dir': str(self.data_dir),
            'logs_dir': str(self.logs_dir),
            'cache_dir': str(self.cache_dir),
            'temp_dir': str(self.temp_dir),
            'backup_dir': str(self.backup_dir)
        }

# 创建全局配置实例
config = ProgramConfig()

# 导出常用路径
PROGRAM_ROOT = config.program_root
DATA_DIR = config.data_dir
LOGS_DIR = config.logs_dir
CACHE_DIR = config.cache_dir
TEMP_DIR = config.temp_dir
BACKUP_DIR = config.backup_dir
