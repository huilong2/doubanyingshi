"""
工具函数模块
提供统一的配置加载、缓存路径获取等功能
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_program_config() -> Dict[str, Any]:
    """
    统一获取程序配置
    
    Returns:
        Dict[str, Any]: 程序配置字典
    """
    try:
        from mokuai_chagyong import chagyong_load_config
        from config import DATA_DIR
        
        config = chagyong_load_config(DATA_DIR)
        return config
    except Exception as e:
        logger.error(f"加载程序配置失败: {str(e)}")
        return {}

def get_cache_path() -> str:
    """
    统一获取缓存路径
    
    Returns:
        str: 缓存路径，如果配置中没有则返回默认路径
    """
    try:
        config = get_program_config()
        cache_path = config.get('browser_cache_path', '')
        
        if not cache_path:
            # 如果设置中没有缓存路径，使用默认路径
            cache_path = str(Path(__file__).parent / "cache")
            
        return cache_path
    except Exception as e:
        logger.error(f"获取缓存路径失败: {str(e)}")
        # 返回默认路径
        return str(Path(__file__).parent / "cache")

def get_account_cache_dir(username: str) -> Path:
    """
    获取指定账号的缓存目录
    
    Args:
        username: 用户名
        
    Returns:
        Path: 账号缓存目录路径
    """
    cache_path = get_cache_path()
    return Path(cache_path) / username

def get_fingerprint_manager():
    """
    获取指纹管理器实例（单例模式）
    
    Returns:
        FingerprintManager: 指纹管理器实例
    """
    from liulanqimokuai.fingerprint_manager import FingerprintManager
    return FingerprintManager()

def ensure_account_fingerprint(username: str) -> Optional[Dict[str, Any]]:
    """
    确保账号有指纹数据，如果没有则生成
    
    Args:
        username: 用户名
        
    Returns:
        Optional[Dict[str, Any]]: 指纹数据，失败返回None
    """
    try:
        account_cache_dir = get_account_cache_dir(username)
        fingerprint_manager = get_fingerprint_manager()
        return fingerprint_manager.ensure_account_fingerprint(str(account_cache_dir))
    except Exception as e:
        logger.error(f"确保账号指纹数据失败: {str(e)}")
        return None

def get_account_fingerprint(username: str) -> Optional[Dict[str, Any]]:
    """
    获取账号指纹数据（仅读取，不生成）
    
    Args:
        username: 用户名
        
    Returns:
        Optional[Dict[str, Any]]: 指纹数据，失败返回None
    """
    try:
        account_cache_dir = get_account_cache_dir(username)
        fingerprint_manager = get_fingerprint_manager()
        return fingerprint_manager.get_account_fingerprint(str(account_cache_dir))
    except Exception as e:
        logger.error(f"获取账号指纹数据失败: {str(e)}")
        return None

def save_account_fingerprint(username: str, fingerprint: Dict[str, Any]) -> bool:
    """
    保存账号指纹数据
    
    Args:
        username: 用户名
        fingerprint: 指纹数据
        
    Returns:
        bool: 保存是否成功
    """
    try:
        account_cache_dir = get_account_cache_dir(username)
        fingerprint_manager = get_fingerprint_manager()
        return fingerprint_manager.save_account_fingerprint(str(account_cache_dir), fingerprint)
    except Exception as e:
        logger.error(f"保存账号指纹数据失败: {str(e)}")
        return False

def delete_account_cache(username: str) -> bool:
    """
    删除账号缓存目录
    
    Args:
        username: 用户名
        
    Returns:
        bool: 删除是否成功
    """
    try:
        import shutil
        account_cache_dir = get_account_cache_dir(username)
        
        if account_cache_dir.exists():
            shutil.rmtree(account_cache_dir)
            logger.info(f"已删除账号缓存目录: {account_cache_dir}")
            return True
        else:
            logger.info(f"账号缓存目录不存在: {account_cache_dir}")
            return True
            
    except Exception as e:
        logger.error(f"删除账号缓存目录失败: {str(e)}")
        return False 

def extract_fingerprint_headers(fingerprint: Dict[str, Any]) -> Dict[str, str]:
    """
    从指纹数据中提取HTTP头信息
    
    Args:
        fingerprint: 指纹数据字典
        
    Returns:
        Dict[str, str]: HTTP头信息字典
    """
    extra_headers = {}
    
    if isinstance(fingerprint, dict):
        if 'user_agent' in fingerprint:
            extra_headers['User-Agent'] = fingerprint['user_agent']
        if 'language' in fingerprint:
            extra_headers['Accept-Language'] = fingerprint['language']
    
    return extra_headers

def show_fingerprint_dialog(parent, username: str) -> bool:
    """
    显示指纹数据对话框
    
    Args:
        parent: 父窗口
        username: 用户名
        
    Returns:
        bool: 是否成功显示
    """
    try:
        # 获取指纹数据
        fingerprint = get_account_fingerprint(username)
        
        if not fingerprint:
            if hasattr(parent, 'browser_signals'):
                parent.browser_signals.error.emit("该账号未保存指纹数据，请先保存指纹数据")
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(parent, "警告", "该账号未保存指纹数据，请先保存指纹数据")
            return False
        
        # 指纹字段描述
        desc = {
            'user_agent': '浏览器UA',
            'screen_width': '屏幕宽度',
            'screen_height': '屏幕高度',
            'color_depth': '颜色深度',
            'timezone': '时区',
            'language': '语言',
            'platform': '平台',
            'webgl_vendor': 'WebGL厂商',
            'webgl_renderer': 'WebGL渲染器',
            'fonts': '字体列表',
            'plugins': '插件列表',
            'canvas': 'Canvas指纹',
            'audio': '音频指纹',
            'media_devices': '多媒体设备',
            'latitude': '纬度',
            'longitude': '经度',
        }
        
        # 创建对话框
        from PySide6.QtWidgets import QFormLayout, QLabel, QTextEdit, QDialog, QHBoxLayout, QPushButton
        from PySide6.QtCore import Qt
        import json
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("指纹数据")
        dialog.setMinimumSize(600, 500)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QFormLayout(dialog)
        
        # 显示指纹数据
        for key in [
            'user_agent','screen_width','screen_height','color_depth','timezone','language','platform',
            'webgl_vendor','webgl_renderer','fonts','plugins','canvas','audio','media_devices','latitude','longitude'
        ]:
            if key in fingerprint:
                label = f"{key}（{desc.get(key, key)}）"
                value = fingerprint[key]
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value, ensure_ascii=False, indent=2)
                    text = QTextEdit()
                    text.setReadOnly(True)
                    text.setText(value_str)
                    layout.addRow(label, text)
                else:
                    layout.addRow(label, QLabel(str(value)))
        
        # 添加关闭按钮
        button_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        layout.addRow(button_layout)
        dialog.setLayout(layout)
        
        # 应用样式
        try:
            from styles import FINGERPRINT_DIALOG_STYLE
            dialog.setStyleSheet(FINGERPRINT_DIALOG_STYLE)
        except ImportError:
            pass
        
        dialog.exec()
        return True
        
    except Exception as e:
        logger.error(f"显示指纹数据失败: {str(e)}")
        if hasattr(parent, 'browser_signals'):
            parent.browser_signals.error.emit(f"显示指纹数据失败: {str(e)}")
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(parent, "错误", f"显示指纹数据失败: {str(e)}")
        return False 