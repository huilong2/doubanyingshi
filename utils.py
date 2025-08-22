import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QMessageBox, QWidget
from liulanqi_gongcaozuo import LiulanqiGongcaozuo, LiulanqiPeizhi
import json

class BrowserManager:
    """浏览器管理器，处理浏览器相关的共享功能"""
    
    @staticmethod
    async def init_browser(account: Dict[str, Any], publish_url: str, status_callback=None) -> Optional[LiulanqiGongcaozuo]:
        """初始化浏览器实例"""
        try:
            username = account.get('username', 'publisher')
            proxy = account.get('proxy', '')
            cache_path = account.get('user_data_dir', '')
            browser_path = account.get('browser_path', '')
            
            if not browser_path or not cache_path:
                if status_callback:
                    status_callback("浏览器路径或缓存路径未配置")
                return None
            
            peizhi = LiulanqiPeizhi(
                zhanghao=username,
                daili=proxy if proxy else None,
                wangzhi=publish_url,
                huanchunlujing=str(Path(cache_path) / username),
                chrome_path=browser_path
            )
            
            if status_callback:
                status_callback("正在启动浏览器...")
            
            browser = LiulanqiGongcaozuo(peizhi)
            await browser.chushihua()
            return browser
            
        except Exception as e:
            if status_callback:
                status_callback(f"初始化浏览器失败: {str(e)}")
            return None

class ConfigManager:
    """配置管理器，处理配置相关的共享功能"""
    
    @staticmethod
    def save_config(config_path: Path, config: Dict[str, Any], status_callback=None) -> bool:
        """保存配置"""
        try:
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            if status_callback:
                status_callback("配置已保存")
            return True
        except Exception as e:
            if status_callback:
                status_callback(f"保存配置失败: {str(e)}")
            return False
    
    @staticmethod
    def load_config(config_path: Path, status_callback=None) -> Dict[str, Any]:
        """加载配置"""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            if status_callback:
                status_callback(f"加载配置失败: {str(e)}")
            return {}

class UIManager:
    """UI管理器，处理UI相关的共享功能"""
    
    @staticmethod
    def show_message(parent: QWidget, title: str, message: str, icon=QMessageBox.Information):
        """显示消息框"""
        if icon == QMessageBox.Information:
            QMessageBox.information(parent, title, message)
        elif icon == QMessageBox.Warning:
            QMessageBox.warning(parent, title, message)
        else:
            QMessageBox.critical(parent, title, message)

class LogManager:
    """日志管理器，处理日志相关的共享功能"""
    
    @staticmethod
    def setup_logging(log_dir: Path) -> logging.Logger:
        """配置日志系统"""
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "app.log"
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        logging.getLogger('playwright').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        return root_logger 