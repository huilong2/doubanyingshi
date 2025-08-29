"""
工具函数模块
提供统一的配置加载、缓存路径获取等功能
"""

import logging
import os
import shutil
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
        from config import load_config, DATA_DIR
        
        config = load_config(DATA_DIR)
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

def ensure_account_fingerprint(account_id: int) -> Optional[Dict[str, Any]]:
    """
    确保账号指纹数据存在（如果不存在则生成）
    
    Args:
        account_id: 账号ID
        
    Returns:
        Optional[Dict[str, Any]]: 指纹数据，失败返回None
    """
    try:
        fingerprint_manager = get_fingerprint_manager()
        return fingerprint_manager.ensure_account_fingerprint(account_id)
    except Exception as e:
        logger.error(f"确保账号指纹数据失败: {str(e)}")
        return None

def get_account_fingerprint(account_id: int) -> Optional[Dict[str, Any]]:
    """
    获取账号指纹数据（仅读取，不生成）
    
    Args:
        account_id: 账号ID
        
    Returns:
        Optional[Dict[str, Any]]: 指纹数据，失败返回None
    """
    try:
        fingerprint_manager = get_fingerprint_manager()
        return fingerprint_manager.get_account_fingerprint(account_id)
    except Exception as e:
        logger.error(f"获取账号指纹数据失败: {str(e)}")
        return None

def save_account_fingerprint(account_id: int, fingerprint: Dict[str, Any]) -> bool:
    """
    保存账号指纹数据
    
    Args:
        account_id: 账号ID
        fingerprint: 指纹数据
        
    Returns:
        bool: 保存是否成功
    """
    try:
        fingerprint_manager = get_fingerprint_manager()
        return fingerprint_manager.save_account_fingerprint(account_id, fingerprint)
    except Exception as e:
        logger.error(f"保存账号指纹数据失败: {str(e)}")
        return False

def delete_account_cache(account_id: int) -> bool:
    """
    删除账号相关的缓存数据
    - 删除数据库中的指纹数据
    - 删除浏览器缓存目录
    
    Args:
        account_id: 账号ID
        
    Returns:
        bool: 删除是否成功
    """
    try:
        success = True
        logger.debug(f"开始删除账号ID={account_id}的缓存数据")
        
        # 1. 删除数据库中的指纹数据
        if account_id is not None:
            logger.debug(f"步骤1: 删除数据库中的指纹数据")
            fingerprint_manager = get_fingerprint_manager()
            if not fingerprint_manager.delete_account_fingerprint(account_id):
                logger.warning(f"删除账号{account_id}的数据库指纹数据失败")
                success = False
        
        # 2. 获取账号信息，查找用户名
        username = None
        if account_id is not None:
            logger.debug(f"步骤2: 获取账号信息，查找用户名")
            from data_manager import DataManager
            data_manager = DataManager()
            accounts = data_manager.get_accounts()
            
            if not accounts:
                logger.warning(f"数据库中没有账号记录")
            else:
                logger.debug(f"数据库中找到{len(accounts)}条账号记录")
                
            for account in accounts:
                if len(account) > 0 and account[0] == account_id:
                    username = account[1]  # 用户名在账号记录的第2列
                    logger.debug(f"找到账号信息: ID={account_id}, 用户名={username}")
                    break
        
        if not username:
            logger.warning(f"无法找到账号ID={account_id}对应的用户名")
            
        # 3. 删除浏览器缓存目录
        if username:
            logger.debug(f"步骤3: 删除浏览器缓存目录，用户名为: {username}")
            try:
                # 读取配置文件中的浏览器缓存路径
                from config import config
                config_path = config.get_config_path()
                logger.debug(f"配置文件路径: {config_path}")
                
                browser_cache_path = None
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        browser_cache_path = config_data.get('browser_cache_path', '')
                        logger.debug(f"从配置文件读取browser_cache_path: {browser_cache_path}")
                
                # 如果配置中没有缓存路径，使用默认路径
                if not browser_cache_path:
                    browser_cache_path = os.path.join(config.program_root, 'temp', 'browser_cache')
                    logger.debug(f"使用默认缓存路径: {browser_cache_path}")
                
                # 确保路径格式正确（处理Windows路径中的正斜杠）
                browser_cache_path = browser_cache_path.replace('/', '\\')
                logger.debug(f"格式化后的缓存路径: {browser_cache_path}")
                
                # 构建账号缓存目录路径
                account_cache_dir = os.path.join(browser_cache_path, username)
                logger.info(f"账号缓存目录路径: {account_cache_dir}")
                
                # 删除账号缓存目录
                if os.path.exists(account_cache_dir):
                    logger.info(f"账号缓存目录存在，尝试删除: {account_cache_dir}")
                    try:
                        shutil.rmtree(account_cache_dir)
                        logger.info(f"已成功删除账号 {username} 的缓存目录: {account_cache_dir}")
                    except PermissionError:
                        logger.error(f"权限不足，无法删除缓存目录: {account_cache_dir}")
                        logger.error("请以管理员身份运行程序或手动删除该目录")
                        success = False
                    except Exception as e:
                        logger.error(f"删除账号 {username} 的缓存目录时出错: {str(e)}")
                        success = False
                else:
                    logger.info(f"账号 {username} 的缓存目录不存在: {account_cache_dir}")
            except Exception as e:
                logger.error(f"删除账号 {username} 的缓存目录时出错: {str(e)}")
                success = False
        
        logger.debug(f"账号缓存删除完成，结果: {'成功' if success else '失败'}")
        return success
            
    except Exception as e:
        logger.error(f"删除账号缓存数据失败: {str(e)}", exc_info=True)
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

def show_fingerprint_dialog(parent, account_id: int) -> bool:
    """
    显示指纹数据对话框
    
    Args:
        parent: 父窗口
        account_id: 账号ID
        
    Returns:
        bool: 是否成功显示
    """
    try:
        # 获取指纹数据
        fingerprint = get_account_fingerprint(account_id)
        
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