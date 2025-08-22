import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QFormLayout, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 导入项目模块
from styles import DIALOG_STYLE, FINGERPRINT_DIALOG_STYLE
from data_manager import DataManager
from liulanqimokuai.fingerprint_manager import FingerprintManager
from config import config


class BaseDialog(QDialog):
    """基础对话框类"""
    def __init__(self, parent=None, title="", min_width=350, min_height=180):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(min_width, min_height)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 移除帮助按钮
        self.init_ui()
        self.apply_dialog_style()
    
    def init_ui(self):
        """初始化UI，子类需要重写此方法"""
        pass
    
    def apply_dialog_style(self):
        """应用对话框样式"""
        self.setStyleSheet(DIALOG_STYLE)


class MainAccountDialog(BaseDialog):
    """账号编辑对话框"""
    def __init__(self, parent=None, account_data=None):
        self.data_manager = DataManager()  # 初始化数据管理器
        self.account_data = account_data or self.data_manager.load_peizhi()  # 从peizhi.json加载配置数据
        title = "编辑账号" if account_data else "添加账号"
        super().__init__(parent, title, 450, 350)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建输入字段
        fields = [
            ("用户名:", "username"),
            ("密码:", "password"),
            ("分组:", "group_name", True),
            ("代理:", "proxy")
        ]
        
        for label_text, field_name, *args in fields:
            field_layout = QHBoxLayout()
            field_layout.setSpacing(10)
            label = QLabel(label_text)
            field_layout.addWidget(label)
            
            if args and args[0]:  # 如果是下拉框
                widget = QComboBox()
                # 使用DataManager获取分组列表
                groups = self.data_manager.get_groups()
                widget.addItems(groups)
                if self.account_data.get(field_name):
                    widget.setCurrentText(self.account_data[field_name])
            else:
                # 从配置数据中读取内容，无数据时使用空字符串（确保键名匹配）
                initial_value = self.account_data.get(field_name, '')
                widget = QLineEdit(initial_value)
            
            field_layout.addWidget(widget)
            layout.addLayout(field_layout)
            setattr(self, f"{field_name}_widget", widget)
        
        # 如果是编辑模式，添加"查看指纹数据"按钮
        if self.account_data:
            fingerprint_layout = QHBoxLayout()
            fingerprint_layout.setSpacing(10)
            fingerprint_btn = QPushButton("查看指纹数据")
            fingerprint_btn.clicked.connect(self.show_fingerprint_data)
            fingerprint_layout.addWidget(fingerprint_btn)
            layout.addLayout(fingerprint_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def show_fingerprint_data(self):
        """显示指纹数据（分项展示并带中文说明）"""
        try:
            username = self.username_widget.text()
            if not username:
                self.parent().browser_signals.error.emit("无法获取账号信息")
                return
            
            # 从文件系统读取指纹数据
            cache_path = self.parent().config.get('browser_cache_path', '')
            # 优先使用配置的缓存路径，如果不存在则使用默认的data目录
            if cache_path and Path(cache_path).exists():
                account_dir = Path(cache_path) / username
            else:
                # 使用默认的data目录
                account_dir = Path('data') / username
            fingerprint_manager = FingerprintManager()
            fingerprint = fingerprint_manager.load_fingerprint_from_file(str(account_dir))
            
            if not fingerprint:
                self.parent().browser_signals.error.emit("该账号未保存指纹数据")
                return
                
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
            from PySide6.QtWidgets import QFormLayout, QLabel, QTextEdit, QDialog, QHBoxLayout, QPushButton
            dialog = QDialog(self)
            dialog.setWindowTitle("指纹数据")
            dialog.setMinimumSize(600, 500)
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            layout = QFormLayout(dialog)
            for key in [
                'user_agent','screen_width','screen_height','color_depth','timezone','language','platform',
                'webgl_vendor','webgl_renderer','fonts','plugins','canvas','audio','media_devices','latitude','longitude']:
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
            button_layout = QHBoxLayout()
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            layout.addRow(button_layout)
            dialog.setLayout(layout)
            
            # 应用Fluent风格到指纹数据对话框
            dialog.setStyleSheet(FINGERPRINT_DIALOG_STYLE)
            dialog.exec()
        except Exception as e:
            error_msg = f"显示指纹数据失败: {str(e)}"
            import logging
            logger = logging.getLogger("MainAccountDialog")
            logger.error(error_msg)
            self.parent().browser_signals.error.emit(error_msg)
    
    def get_data(self):
        """
        获取账号数据，保证所有字段齐全，未填写的补空字符串，防止数据库错位。
        """
        return {
            'username': self.username_widget.text(),
            'password': self.password_widget.text(),
            'ck': getattr(self, 'ck_widget', None).text() if hasattr(self, 'ck_widget') else '',
            'nickname': getattr(self, 'nickname_widget', None).text() if hasattr(self, 'nickname_widget') else '',
            'account_id': getattr(self, 'account_id_widget', None).text() if hasattr(self, 'account_id_widget') else '',
            'login_status': getattr(self, 'login_status_widget', None).text() if hasattr(self, 'login_status_widget') else '',
            'homepage': getattr(self, 'homepage_widget', None).text() if hasattr(self, 'homepage_widget') else '',
            'login_time': getattr(self, 'login_time_widget', None).text() if hasattr(self, 'login_time_widget') else '',
            'proxy': self.proxy_widget.text(),
            'running_status': getattr(self, 'running_status_widget', None).text() if hasattr(self, 'running_status_widget') else '',
            'note': getattr(self, 'note_widget', None).text() if hasattr(self, 'note_widget') else '',
            'group_name': self.group_name_widget.currentText()
        }