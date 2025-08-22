import sys
import os
import json
import logging
import asyncio
import stat
import threading
import subprocess
import platform
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QLabel, QLineEdit, QComboBox, QTabWidget, QTextEdit, QProgressBar, QGroupBox, QFileDialog,
    QStyledItemDelegate, QSizePolicy, QSpacerItem, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QIcon
from database_manager import DatabaseManager
from pathlib import Path
from mokuai_chagyong import chagyong_load_config, chagyong_save_config
from mokuai_liulanqi import Liulanqi, LiulanqiPeizhi
from mokuai_zhiwen import FingerprintGenerator

from data_file_manager import DataFileManager
from config import config, DATA_DIR, LOGS_DIR, CACHE_DIR, TEMP_DIR, BACKUP_DIR

# 配置日志
def setup_logging():
    """配置日志系统"""
    # 使用配置系统中的日志目录
    log_file = config.get_log_path()
    
    # 确保日志目录存在
    log_file.parent.mkdir(exist_ok=True)
    
    # Windows系统不需要设置Unix风格的权限
    if platform.system() != "Windows":
        # 确保日志目录和文件有正确的权限
        try:
            # 设置目录权限为 755
            os.chmod(log_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            # 如果日志文件存在，设置文件权限为 644
            if log_file.exists():
                os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        except Exception as e:
            print(f"设置日志文件权限失败: {str(e)}")
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 添加文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # 设置自定义模块的日志级别
    logging.getLogger('AccountManager').setLevel(logging.WARNING)
    logging.getLogger('root').setLevel(logging.WARNING)
    
    return root_logger

# 初始化日志系统
logger = setup_logging()

# 使用配置系统中的数据目录
quan_shujuwenjianjia = DATA_DIR

# 默认网站地址
DEFAULT_URL = "https://www.douban.com/"

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
        dialog_stylesheet = """
        QDialog {
            background: white;
            border-radius: 12px;
        }
        
        QDialog QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0d6efd, stop:1 #0b5ed7);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            min-width: 50px;
            min-height: 20px;
        }
        
        QDialog QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0b5ed7, stop:1 #0a58ca);
        }
        
        QDialog QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0a58ca, stop:1 #084298);
        }
        
        QDialog QLineEdit {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 14px;
            background: white;
            color: #495057;
        }
        
        QDialog QLineEdit:focus {
            border: 2px solid #0d6efd;
            background: #f8f9ff;
        }
        
        QDialog QComboBox {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            background: white;
            color: #495057;
        }
        
        QDialog QComboBox:focus {
            border: 2px solid #0d6efd;
            background: #f8f9ff;
        }
        
        QDialog QLabel {
            font-size: 14px;
            color: #495057;
            font-weight: 500;
        }
        """
        self.setStyleSheet(dialog_stylesheet)

class AccountDialog(BaseDialog):
    """账号编辑对话框"""
    def __init__(self, parent=None, account_data=None):
        self.data_manager = DataFileManager()  # 初始化数据管理器
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
                widget.addItems(self.parent().db_manager.get_groups())
                if self.account_data.get(field_name):
                    widget.setCurrentText(self.account_data[field_name])
            else:
                # 从配置数据中读取内容，无数据时使用空字符串（确保键名匹配）
                initial_value = self.account_data.get(field_name, '')
                logger.debug(f'加载配置数据：{field_name} = {initial_value}')  # 添加日志验证
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
            if not cache_path:
                self.parent().browser_signals.error.emit("请先在设置中配置浏览器缓存路径")
                return
                
            account_dir = Path(cache_path) / username
            fingerprint_generator = FingerprintGenerator()
            fingerprint = fingerprint_generator.load_fingerprint_from_file(account_dir)
            
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
            fingerprint_dialog_style = """
            QDialog {
                background: white;
                border-radius: 12px;
            }
            
            QDialog QLabel {
                font-size: 14px;
                color: #495057;
                font-weight: 500;
            }
            
            QDialog QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 13px;
                background: #f8f9fa;
                color: #495057;
                padding: 8px;
            }
            
            QDialog QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0d6efd, stop:1 #0b5ed7);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }
            
            QDialog QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0b5ed7, stop:1 #0a58ca);
            }
            """
            dialog.setStyleSheet(fingerprint_dialog_style)
            dialog.exec()
        except Exception as e:
            error_msg = f"显示指纹数据失败: {str(e)}"
            import logging
            logger = logging.getLogger("AccountDialog")
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

class GroupDialog(BaseDialog):
    """分组编辑对话框"""
    def __init__(self, parent=None, group_name=None, mode="add"):
        self.group_name = group_name
        self.mode = mode
        super().__init__(parent, "添加分组" if mode == "add" else "编辑分组")
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 分组名称输入
        name_layout = QHBoxLayout()
        name_layout.setSpacing(10)
        label = QLabel("分组名称:")
        name_layout.addWidget(label)
        self.name_edit = QLineEdit(self.group_name or '')
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
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
    
    def get_data(self):
        return self.name_edit.text()

class BrowserSignals(QObject):
    """浏览器信号类"""
    error = Signal(str)  # 错误信号
    info = Signal(str)   # 信息信号

class AccountManagerWindow(QMainWindow):
    """账号管理主窗口"""
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.group_table = QTableWidget()    # 只在这里创建一次
        self.account_table = QTableWidget()  # 只在这里创建一次
        self.config = {}
        self.browser_signals = BrowserSignals()
        self.browser_signals.error.connect(self.show_error)
        self.browser_signals.info.connect(self.show_info)

        self.active_browser_sessions = {} # Store {username: {'thread': Thread, 'stop_event': Event, 'liulanqi': Liulanqi_instance}}
        self.load_config()
        self.init_ui()
        self.apply_fluent_style()  # 应用Fluent风格
        logger.info("账号管理系统初始化完成")
    
    def apply_fluent_style(self):
        """应用Fluent设计风格"""
        fluent_stylesheet = """
        /* 主窗口样式 */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f9fa, stop:1 #e9ecef);
            color: #212529;
        }
        
        /* 标签页样式 */
        QTabWidget::pane {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            background: white;
            margin-top: -1px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f9fa, stop:1 #e9ecef);
            color: #6c757d;
            padding: 12px 24px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #0d6efd;
            border-bottom: 3px solid #0d6efd;
            font-weight: 600;
        }
        
        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #e9ecef, stop:1 #dee2e6);
            color: #495057;
        }
        
        /* 分组框样式 */
        QGroupBox {
            font-weight: 600;
            font-size: 14px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            margin-top: 16px;
            padding-top: 16px;
            color: #495057;
            background: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 12px 0 12px;
            background: white;
            color: #0d6efd;
        }
        
        /* 按钮样式 */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0d6efd, stop:1 #0b5ed7);
            color: white;
            border: none;
            padding: 6px 12px;  /* 进一步减小内边距 */
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;  /* 减小字体大小 */
            min-width: 50px;  /* 缩小按钮的最小宽度 */
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0b5ed7, stop:1 #0a58ca);
            margin-top: -1px;
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0a58ca, stop:1 #084298);
        }
        
        QPushButton:disabled {
            background: #6c757d;
            color: #adb5bd;
        }
        
        /* 输入框样式 */
        QLineEdit {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 14px;
            background: white;
            color: #495057;
        }
        
        QLineEdit:focus {
            border: 2px solid #0d6efd;
            background: #f8f9ff;
        }
        
        QLineEdit:hover {
            border: 2px solid #adb5bd;
        }
        
        /* 文本编辑框样式 */
        QTextEdit {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            color: #495057;
            padding: 8px;
        }
        
        QTextEdit:focus {
            border: 2px solid #0d6efd;
            background: #f8f9ff;
        }
        
        /* 表格样式 */
        QTableWidget {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 13px;
            background: white;
            gridline-color: #f8f9fa;
            selection-background-color: #e7f3ff;
            selection-color: #0d6efd;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f8f9fa;
        }
        
        QTableWidget::item:selected {
            background: #e7f3ff;
            color: #0d6efd;
        }
        
        QTableWidget::item:hover {
            background: #f8f9ff;
        }
        
        QTableWidget::item:alternate {
            background: #f8f9fa;
        }
        
        QTableWidget::item:selected:alternate {
            background: #e7f3ff;
            color: #0d6efd;
        }
        
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f9fa, stop:1 #e9ecef);
            color: #495057;
            padding: 12px 8px;
            border: none;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
            font-size: 13px;
        }
        
        QHeaderView::section:hover {
            background: #e9ecef;
        }
        
        /* 下拉框样式 */
        QComboBox {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            background: white;
            color: #495057;
            min-width: 100px;
        }
        
        QComboBox:focus {
            border: 2px solid #0d6efd;
            background: #f8f9ff;
        }
        
        QComboBox:hover {
            border: 2px solid #adb5bd;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #6c757d;
            margin-right: 8px;
        }
        
        QComboBox::down-arrow:hover {
            border-top-color: #0d6efd;
        }
        
        /* 复选框样式 */
        QCheckBox {
            font-size: 14px;
            color: #495057;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #e9ecef;
            border-radius: 4px;
            background: white;
        }
        
        QCheckBox::indicator:checked {
            background: #0d6efd;
            border: 2px solid #0d6efd;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
        }
        
        QCheckBox::indicator:hover {
            border: 2px solid #0d6efd;
        }
        
        /* 标签样式 */
        QLabel {
            font-size: 14px;
            color: #495057;
            font-weight: 500;
        }
        
        /* 滚动条样式 */
        QScrollBar:vertical {
            background: #f8f9fa;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: #adb5bd;
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #6c757d;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background: #f8f9fa;
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background: #adb5bd;
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: #6c757d;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        /* 进度条样式 */
        QProgressBar {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            background: #f8f9fa;
            text-align: center;
            font-weight: 600;
            color: #495057;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0d6efd, stop:1 #0b5ed7);
            border-radius: 6px;
        }
        
        /* 消息框样式 */
        QMessageBox {
            background: white;
        }
        
        QMessageBox QPushButton {
            min-width: 80px;
            min-height: 30px;
        }
        
        /* 文件对话框样式 */
        QFileDialog {
            background: white;
        }
        
        /* 工具提示样式 */
        QToolTip {
            background: #212529;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
        }
        """
        
        self.setStyleSheet(fluent_stylesheet)
    
    def create_table_with_label(self, label_text, table):
        """创建带标签的表格容器"""
        container = QWidget()
        layout = QVBoxLayout(container)
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(table)
        return container
    
    def init_ui(self):
        """初始化主窗口UI"""
        self.setWindowTitle("豆瓣账号管理系统 - Fluent Design")
        self.setMinimumSize(1000, 600)
        
        # 设置窗口图标（如果有的话）
        try:
            icon_path = Path(__file__).parent / "1.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            logger.debug(f"设置窗口图标失败: {str(e)}")
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 创建并初始化各个标签页
        self.tabs = {
            "账号管理": self.init_account_tab(),
            "电影管理": self.init_movie_tab(),
            "内容管理": self.init_content_tab(),
            "功能设置": self.init_function_tab(),
            "操作设置": self.init_operation_tab(),
            "程序设置": self.init_settings_tab()
        }
        
        for name, widget in self.tabs.items():
            self.tab_widget.addTab(widget, name)
        
        main_layout.addWidget(self.tab_widget)
        
        # 设置中央窗口
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 加载数据
        self.load_data()
    
    def create_button(self, text, callback):
        """创建按钮的辅助方法"""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        
        # 为特定按钮设置较小的宽度
        if text in ["添加", "删除"]:
            btn.setFixedSize(25, 32)  # 使用更小的固定宽度
        
        return btn
    
    def create_input_field(self, label_text, widget_type=QLineEdit, **kwargs):
        """创建输入字段的辅助方法"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        label = QLabel(label_text)
        layout.addWidget(label)
        
        widget = widget_type()
        layout.addWidget(widget)
        
        if isinstance(widget, QLineEdit):
            if 'placeholder' in kwargs:
                widget.setPlaceholderText(kwargs['placeholder'])
            if 'readonly' in kwargs:
                widget.setReadOnly(kwargs['readonly'])
        return layout, widget
    
    def init_account_tab(self):
        """初始化账号管理标签页"""
        account_tab = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 分组管理（左侧）
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(5, 5, 5, 5)
        
        # 分组表格表头设置
        self.group_table.setColumnCount(1)
        self.group_table.setHorizontalHeaderLabels(["分组名称"])
        self.group_table.horizontalHeader().setStretchLastSection(True)
        self.group_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.group_table.setSelectionMode(QTableWidget.SingleSelection)
        self.group_table.verticalHeader().setVisible(False)
        self.group_table.setMinimumWidth(180)
        
        # 设置分组表格样式优化
        self.group_table.setAlternatingRowColors(True)  # 交替行颜色
        self.group_table.setShowGrid(True)  # 显示网格线
        self.group_table.setGridStyle(Qt.SolidLine)  # 实线网格
        group_layout.addWidget(self.group_table)
        
        # 分组按钮
        group_btn_layout = QHBoxLayout()
        group_btn_layout.setSpacing(10)
        group_btn_layout.addWidget(self.create_button("添加", self.add_group))
        group_btn_layout.addWidget(self.create_button("删除", self.delete_group))
        group_layout.addLayout(group_btn_layout)
        group_widget.setMaximumWidth(220)
        
        # 账号管理（右侧）
        account_widget = QWidget()
        account_layout = QVBoxLayout(account_widget)
        account_layout.setSpacing(10)
        account_layout.setContentsMargins(5, 5, 5, 5)
        
        # 账号表格表头设置
        self.account_table.setColumnCount(13)
        self.account_table.setHorizontalHeaderLabels([
            "选择", "分组", "账号", "密码", "CK", "账号昵称", "账号ID", 
            "登录状态", "主页地址", "登录时间", "代理IP", "运行状态", "备注"
        ])
        
        # 设置列宽
        column_widths = {
            0: 50,   # 选择（复选框列）
            1: 100,  # 分组
            2: 150,  # 账号
            3: 80,   # 密码
            4: 80,   # CK
            5: 120,  # 账号昵称
            6: 100,  # 账号ID
            7: 100,  # 登录状态
            8: 100,  # 主页地址
            9: 150,  # 登录时间
            10: 120, # 代理IP
            11: 100, # 运行状态
            12: 80   # 备注
        }
        
        for col, width in column_widths.items():
            self.account_table.setColumnWidth(col, width)
        
        # 设置表格样式优化
        self.account_table.setAlternatingRowColors(True)  # 交替行颜色
        self.account_table.setShowGrid(True)  # 显示网格线
        self.account_table.setGridStyle(Qt.SolidLine)  # 实线网格
        
        self.account_table.horizontalHeader().setStretchLastSection(True)
        self.account_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.account_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.account_table.verticalHeader().setVisible(False)
        
        # 连接复选框点击事件
        self.account_table.cellClicked.connect(self.on_account_checkbox_clicked)
        
        account_layout.addWidget(self.account_table)
        
        # 账号操作按钮区域
        account_btn_layout = QHBoxLayout()
        account_btn_layout.setSpacing(10)
        
        # 添加全选/取消全选按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMinimumSize(50, 35)  # 缩小宽度
        self.select_all_btn.clicked.connect(lambda: self.select_all_accounts(True))
        
        self.deselect_all_btn = QPushButton("取消")
        self.deselect_all_btn.setMinimumSize(50, 32)  # 缩小宽度
        self.deselect_all_btn.clicked.connect(lambda: self.select_all_accounts(False))
        
        # 添加账号操作按钮（替代右键菜单功能）
        self.add_account_btn = QPushButton("添加账号")
        self.add_account_btn.setMinimumSize(50, 32)  # 缩小宽度
        
        self.edit_account_btn = QPushButton("编辑账号")
        self.edit_account_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        self.delete_account_btn = QPushButton("删除账号")
        self.delete_account_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        self.open_browser_btn = QPushButton("打开浏览器")
        self.open_browser_btn.setMinimumSize(90, 32)  # 缩小宽度
        
        self.add_proxy_btn = QPushButton("添加代理")
        self.add_proxy_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        self.remove_proxy_btn = QPushButton("删除代理")
        self.remove_proxy_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        # 连接按钮信号
        self.add_account_btn.clicked.connect(self.add_account)
        self.edit_account_btn.clicked.connect(self.edit_account)
        self.delete_account_btn.clicked.connect(self.delete_account)
        self.open_browser_btn.clicked.connect(self.open_browser)
        self.add_proxy_btn.clicked.connect(self.add_proxy)
        self.remove_proxy_btn.clicked.connect(self.remove_proxy)
        
        # 添加按钮到布局
        account_btn_layout.addWidget(self.select_all_btn)
        account_btn_layout.addWidget(self.deselect_all_btn)
        account_btn_layout.addWidget(self.add_account_btn)
        account_btn_layout.addWidget(self.edit_account_btn)
        account_btn_layout.addWidget(self.delete_account_btn)
        account_btn_layout.addWidget(self.open_browser_btn)
        account_btn_layout.addWidget(self.add_proxy_btn)
        account_btn_layout.addWidget(self.remove_proxy_btn)
        account_btn_layout.addStretch()
        
        account_layout.addLayout(account_btn_layout)
        
        # 合并布局
        layout.addWidget(group_widget)
        layout.addWidget(account_widget, 1)
        account_tab.setLayout(layout)
        return account_tab
    
    def init_movie_tab(self):
        """初始化电影管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 创建电影列表框组
        movie_group = QGroupBox("电影管理")
        movie_group_layout = QHBoxLayout(movie_group)
        
        # 创建电影表格
        self.movie_specific_table = QTableWidget()
        self.movie_random_table = QTableWidget()
        
        # 设置电影表格样式
        for table in [self.movie_specific_table, self.movie_random_table]:
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["序号", "电影ID", "评分"])
            table.horizontalHeader().setStretchLastSection(True)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.ExtendedSelection)
            table.verticalHeader().setVisible(False)
            # 设置表格最小高度
            table.setMinimumHeight(400)
            # 设置行高
            table.verticalHeader().setDefaultSectionSize(40)
            # 设置表头高度
            table.horizontalHeader().setFixedHeight(40)
            # 设置列宽
            table.setColumnWidth(0, 80)  # 序号列
            table.setColumnWidth(1, 200)  # 电影ID列
            table.setColumnWidth(2, 100)  # 评分列
            
            # 设置Fluent风格优化
            table.setAlternatingRowColors(True)  # 交替行颜色
            table.setShowGrid(True)  # 显示网格线
            table.setGridStyle(Qt.SolidLine)  # 实线网格
        
        # 添加电影表格到布局
        movie_group_layout.addWidget(self.create_table_with_label("指定电影", self.movie_specific_table))
        movie_group_layout.addWidget(self.create_table_with_label("随机电影", self.movie_random_table))
        
        layout.addWidget(movie_group)
        
        # 电影操作按钮区域
        movie_btn_layout = QHBoxLayout()
        movie_btn_layout.setSpacing(10)
        
        # 添加电影按钮
        add_specific_movie_btn = QPushButton("添加指定")
        add_specific_movie_btn.setMinimumSize(80, 32)  # 缩小宽度
        add_specific_movie_btn.clicked.connect(lambda: self.add_movie("specific"))
        
        add_random_movie_btn = QPushButton("添加随机")
        add_random_movie_btn.setMinimumSize(80, 32)  # 缩小宽度
        add_random_movie_btn.clicked.connect(lambda: self.add_movie("random"))
        
        delete_movie_btn = QPushButton("删除选中")
        delete_movie_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_movie_btn.clicked.connect(self.delete_movie)
        
        delete_movies_batch_btn = QPushButton("批量删除")
        delete_movies_batch_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_movies_batch_btn.clicked.connect(self.delete_movies_batch)
        
        movie_btn_layout.addWidget(add_specific_movie_btn)
        movie_btn_layout.addWidget(add_random_movie_btn)
        movie_btn_layout.addWidget(delete_movie_btn)
        movie_btn_layout.addWidget(delete_movies_batch_btn)
        
        # 添加清空按钮
        clear_movies_btn = QPushButton("清空所有")
        clear_movies_btn.setMinimumSize(80, 32)
        clear_movies_btn.clicked.connect(self.clear_all_movies)
        movie_btn_layout.addWidget(clear_movies_btn)
        
        movie_btn_layout.addStretch()
        
        layout.addLayout(movie_btn_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def init_content_tab(self):
        """初始化内容管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 创建内容列表框组
        content_group = QGroupBox("内容管理")
        content_group_layout = QHBoxLayout(content_group)
        
        # 创建内容表格
        self.content_specific_table = QTableWidget()
        self.content_random_table = QTableWidget()
        
        # 设置内容表格样式
        for table in [self.content_specific_table, self.content_random_table]:
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["序号", "内容"])
            table.horizontalHeader().setStretchLastSection(True)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.ExtendedSelection)
            table.verticalHeader().setVisible(False)
            # 设置表格最小高度
            table.setMinimumHeight(400)
            # 设置行高
            table.verticalHeader().setDefaultSectionSize(40)
            # 设置表头高度
            table.horizontalHeader().setFixedHeight(40)
            # 设置列宽
            table.setColumnWidth(0, 80)  # 序号列
            table.setColumnWidth(1, 400)  # 内容列
            
            # 设置Fluent风格优化
            table.setAlternatingRowColors(True)  # 交替行颜色
            table.setShowGrid(True)  # 显示网格线
            table.setGridStyle(Qt.SolidLine)  # 实线网格
        
        # 添加内容表格到布局
        content_group_layout.addWidget(self.create_table_with_label("指定内容", self.content_specific_table))
        content_group_layout.addWidget(self.create_table_with_label("随机内容", self.content_random_table))
        
        layout.addWidget(content_group)
        
        # 内容操作按钮区域
        content_btn_layout = QHBoxLayout()
        content_btn_layout.setSpacing(10)
        
        # 添加内容按钮
        add_specific_content_btn = QPushButton("添加指定")
        add_specific_content_btn.setMinimumSize(80, 32)  # 缩小宽度
        add_specific_content_btn.clicked.connect(lambda: self.add_content("specific"))
        
        add_random_content_btn = QPushButton("添加随机")
        add_random_content_btn.setMinimumSize(80, 32)  # 缩小宽度
        add_random_content_btn.clicked.connect(lambda: self.add_content("random"))
        
        delete_content_btn = QPushButton("删除选中")
        delete_content_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_content_btn.clicked.connect(self.delete_content)
        
        delete_contents_batch_btn = QPushButton("批量删除")
        delete_contents_batch_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_contents_batch_btn.clicked.connect(self.delete_contents_batch)
        
        content_btn_layout.addWidget(add_specific_content_btn)
        content_btn_layout.addWidget(add_random_content_btn)
        content_btn_layout.addWidget(delete_content_btn)
        content_btn_layout.addWidget(delete_contents_batch_btn)
        
        # 添加清空按钮
        clear_contents_btn = QPushButton("清空所有")
        clear_contents_btn.setMinimumSize(80, 32)
        clear_contents_btn.clicked.connect(self.clear_all_contents)
        content_btn_layout.addWidget(clear_contents_btn)
        
        content_btn_layout.addStretch()
        
        layout.addLayout(content_btn_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def init_function_tab(self):
        """初始化功能设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)  # 增加组件之间的间距
        layout.setContentsMargins(20, 20, 20, 20)  # 设置边距
        
        # 创建左侧和右侧布局
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        # 左侧布局：功能选择和输入内容
        # 创建复选框组
        checkbox_group = QGroupBox("功能选择")
        checkbox_group.setMinimumWidth(260)  # 设置最小宽度
        checkbox_layout = QVBoxLayout(checkbox_group)
        checkbox_layout.setSpacing(10)
        
        # 创建复选框
        self.signature_checkbox = QCheckBox("签名")
        self.status_checkbox = QCheckBox("说说")
        self.group_checkbox = QCheckBox("小组")
        self.phrase_checkbox = QCheckBox("短语")
        
        # 添加复选框
        for checkbox in [self.signature_checkbox, self.status_checkbox, 
                        self.group_checkbox, self.phrase_checkbox]:
            checkbox_layout.addWidget(checkbox)
        
        left_layout.addWidget(checkbox_group)
        
        # 间隔设置组
        interval_group = QGroupBox("间隔设置")
        interval_layout = QVBoxLayout(interval_group)
        interval_layout.setSpacing(15)
        
        # 创建间隔设置项
        intervals = [
            ("操作间隔", "operation_interval"),
            ("换号间隔", "account_interval"),
            ("错误间隔", "error_interval")
        ]
        
        for label, name in intervals:
            interval_item_layout = QHBoxLayout()
            interval_item_layout.setSpacing(10)
            
            label_widget = QLabel(f"{label}：")
            interval_item_layout.addWidget(label_widget)
            
            min_edit = QLineEdit("3")
            max_edit = QLineEdit("5")
            for edit in [min_edit, max_edit]:
                edit.setFixedWidth(60)
                edit.setAlignment(Qt.AlignCenter)
                edit.setFixedWidth(60)
                edit.setAlignment(Qt.AlignCenter)
            
            setattr(self, f"{name}_min", min_edit)
            setattr(self, f"{name}_max", max_edit)
            
            interval_item_layout.addWidget(min_edit)
            interval_item_layout.addWidget(QLabel("-"))
            interval_item_layout.addWidget(max_edit)
            interval_item_layout.addStretch()
            
            interval_layout.addLayout(interval_item_layout)
        
        left_layout.addWidget(interval_group)
        left_layout.addStretch()
        
        # 右侧布局：评星设置和输入内容
        # 评星设置组
        rating_group = QGroupBox("评星设置")
        rating_layout = QVBoxLayout(rating_group)
        rating_layout.setSpacing(15)
        
        # 评论后随机评星
        rating_range_layout = QHBoxLayout()
        rating_range_layout.setSpacing(10)
        rating_label = QLabel("评论后随机评星：")
        rating_range_layout.addWidget(rating_label)
        
        self.rating_min = QLineEdit("1")
        self.rating_max = QLineEdit("2")
        for edit in [self.rating_min, self.rating_max]:
            edit.setFixedWidth(60)
            edit.setAlignment(Qt.AlignCenter)
        rating_range_layout.addWidget(self.rating_min)
        rating_range_layout.addWidget(QLabel("-"))
        rating_range_layout.addWidget(self.rating_max)
        rating_range_layout.addStretch()
        rating_layout.addLayout(rating_range_layout)
        
        # 评星的打几星
        star_rating_layout = QHBoxLayout()
        star_rating_layout.setSpacing(10)
        star_label = QLabel("评星的打几星（|）分割：")
        star_rating_layout.addWidget(star_label)
        
        self.star_rating = QLineEdit("3|4|5")
        self.star_rating.setFixedWidth(120)
        star_rating_layout.addWidget(self.star_rating)
        
        # 评星类型下拉框
        self.rating_type = QComboBox()
        self.rating_type.addItems(["电影", "电视", "读书", "音乐", "随机"])
        
        self.rating_type.setFixedWidth(100)
        star_rating_layout.addWidget(self.rating_type)
        star_rating_layout.addStretch()
        rating_layout.addLayout(star_rating_layout)
        
        right_layout.addWidget(rating_group)
        
        # 创建文本框
        text_group = QGroupBox("输入内容")
        text_layout = QVBoxLayout(text_group)
        
        self.content_text = QTextEdit()
        self.content_text.setPlaceholderText("请输入内容（支持换行）")
        self.content_text.setMinimumHeight(200)  # 设置最小高度
        text_layout.addWidget(self.content_text)
        
        right_layout.addWidget(text_group)
        right_layout.addStretch()
        
        # 运行设置组
        run_group = QGroupBox("运行设置")
        run_layout = QHBoxLayout(run_group)
        run_layout.setSpacing(10)

        self.run_start_btn = QPushButton("开始")
        self.run_start_btn.setMinimumSize(100, 50)  # 缩小宽度
        self.run_start_btn.clicked.connect(self.on_run_start_clicked)
        run_layout.addWidget(self.run_start_btn)

        self.run_mode_combo = QComboBox()
        self.run_mode_combo.addItems(["指定电影评论评星", "只评论"])
        run_layout.addWidget(self.run_mode_combo)

        self.run_status_combo = QComboBox()
        self.run_status_combo.addItems(["看过", "在看", "想看"])
        self.run_status_combo.setFixedWidth(80) 
        run_layout.addWidget(self.run_status_combo)

        cookie_label = QLabel("cookie更新时间:")
        run_layout.addWidget(cookie_label)
        self.run_cookie_time = QLineEdit("86400")
        self.run_cookie_time.setFixedWidth(80)
        run_layout.addWidget(self.run_cookie_time)

        right_layout.addWidget(run_group)
        
        # 设置左右布局的比例
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
        
        layout.addLayout(main_layout)
        widget.setLayout(layout)
        return widget
    
    def init_operation_tab(self):
        """初始化操作设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 创建操作设置组
        operation_group = QGroupBox("操作设置")
        operation_layout = QVBoxLayout(operation_group)
        
        # 添加操作设置项
        operation_layout.addWidget(QLabel("操作设置（待实现）"))
        
        layout.addWidget(operation_group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def init_settings_tab(self):
        """初始化设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 浏览器设置组
        browser_group = QGroupBox("浏览器设置")
        browser_layout = QVBoxLayout(browser_group)
        browser_layout.setSpacing(10)

        # 浏览器路径
        browser_path_layout = QHBoxLayout()
        label = QLabel("浏览器路径:")
        browser_path_layout.addWidget(label)
        self.browser_path_edit = QLineEdit()
        self.browser_path_edit.setPlaceholderText("请选择浏览器可执行文件路径")
        browser_path_layout.addWidget(self.browser_path_edit)
        browser_path_layout.addWidget(self.create_button("自动检测", self.detect_browser_path))
        browser_path_layout.addWidget(self.create_button("浏览", self.browse_browser))
        browser_layout.addLayout(browser_path_layout)

        # 缓存路径
        cache_path_layout = QHBoxLayout()
        label = QLabel("缓存路径:")
        cache_path_layout.addWidget(label)
        self.cache_path_edit = QLineEdit()
        self.cache_path_edit.setPlaceholderText("请选择浏览器缓存目录")
        cache_path_layout.addWidget(self.cache_path_edit)
        cache_path_layout.addWidget(self.create_button("浏览", self.browse_cache))
        browser_layout.addLayout(cache_path_layout)
        
        browser_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        layout.addWidget(browser_group)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # 显示已保存的配置
        if self.config:
            self.browser_path_edit.setText(self.config.get('browser_path', ''))
            self.cache_path_edit.setText(self.config.get('browser_cache_path', ''))
        
        widget.setLayout(layout)
        return widget
    
    def load_config(self):
        """加载配置文件"""
        try:
            self.config = chagyong_load_config(quan_shujuwenjianjia)
            logger.info(f"已加载配置: {self.config}")
            
            # 使用 QTimer 延迟加载配置，确保 UI 组件已创建
            QTimer.singleShot(100, self.apply_config)
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            self.config = {}

    def apply_config(self):
        """应用配置到 UI 组件"""
        try:
            if not self.config:
                return
            
            # 加载浏览器设置
            if 'browser_path' in self.config and hasattr(self, 'browser_path_edit'):
                self.browser_path_edit.setText(self.config['browser_path'])
            if 'browser_cache_path' in self.config and hasattr(self, 'cache_path_edit'):
                self.cache_path_edit.setText(self.config['browser_cache_path'])
            
            # 加载功能设置
            if 'function_settings' in self.config:
                settings = self.config['function_settings']
                if hasattr(self, 'signature_checkbox'):
                    self.signature_checkbox.setChecked(settings.get('signature', False))
                if hasattr(self, 'status_checkbox'):
                    self.status_checkbox.setChecked(settings.get('status', False))
                if hasattr(self, 'group_checkbox'):
                    self.group_checkbox.setChecked(settings.get('group', False))
                if hasattr(self, 'phrase_checkbox'):
                    self.phrase_checkbox.setChecked(settings.get('phrase', False))
                if hasattr(self, 'content_text'):
                    self.content_text.setText(settings.get('content', ''))
                
                # 加载评星设置
                if hasattr(self, 'rating_min'):
                    self.rating_min.setText(str(settings.get('rating_min', '1')))
                if hasattr(self, 'rating_max'):
                    self.rating_max.setText(str(settings.get('rating_max', '2')))
                if hasattr(self, 'star_rating'):
                    self.star_rating.setText(settings.get('star_rating', '3|4|5'))
                if hasattr(self, 'rating_type'):
                    self.rating_type.setCurrentText(settings.get('rating_type', '电影'))
                
                # 加载间隔设置
                if hasattr(self, 'operation_interval_min'):
                    self.operation_interval_min.setText(str(settings.get('operation_interval_min', '3')))
                if hasattr(self, 'operation_interval_max'):
                    self.operation_interval_max.setText(str(settings.get('operation_interval_max', '5')))
                if hasattr(self, 'account_interval_min'):
                    self.account_interval_min.setText(str(settings.get('account_interval_min', '3')))
                if hasattr(self, 'account_interval_max'):
                    self.account_interval_max.setText(str(settings.get('account_interval_max', '5')))
                if hasattr(self, 'error_interval_min'):
                    self.error_interval_min.setText(str(settings.get('error_interval_min', '3')))
                if hasattr(self, 'error_interval_max'):
                    self.error_interval_max.setText(str(settings.get('error_interval_max', '5')))
                
            logger.info("配置已成功应用到 UI 组件")
        except Exception as e:
            error_msg = f"应用配置到 UI 组件失败: {str(e)}"
            logger.error(error_msg)
            self.browser_signals.error.emit(error_msg)

    def load_data(self):
        """加载数据"""
        # 加载分组数据
        groups = self.db_manager.get_groups()
        self.group_table.setRowCount(len(groups))
        for i, group in enumerate(groups):
            self.group_table.setItem(i, 0, QTableWidgetItem(group))
        self.group_table.itemSelectionChanged.connect(self.on_group_selected)
        
        # 加载账号数据
        self.load_accounts()
        
        # 加载电影和内容数据
        self.load_movies_and_contents()
    
    def on_group_selected(self):
        """处理分组选择变化"""
        selected = self.group_table.selectedItems()
        if selected:
            self.load_accounts(selected[0].text())
        else:
            self.load_accounts()
    
    def on_account_checkbox_clicked(self, row, column):
        """处理账号复选框点击事件"""
        if column == 0:  # 只有点击复选框列才处理
            item = self.account_table.item(row, 0)
            if item:
                # 切换复选框状态
                current_state = item.checkState()
                new_state = Qt.Checked if current_state == Qt.Unchecked else Qt.Unchecked
                item.setCheckState(new_state)
    
    def get_selected_accounts(self):
        """获取所有选中的账号"""
        selected_accounts = []
        for row in range(self.account_table.rowCount()):
            checkbox_item = self.account_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                username = self.account_table.item(row, 2).text()
                account_id = self.account_table.item(row, 2).data(Qt.UserRole)
                selected_accounts.append({
                    'row': row,
                    'username': username,
                    'account_id': account_id
                })
        return selected_accounts
    
    def select_all_accounts(self, select=True):
        """全选或取消全选所有账号"""
        for row in range(self.account_table.rowCount()):
            checkbox_item = self.account_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.Checked if select else Qt.Unchecked)
    
    def load_accounts(self, group_name=None):
        """加载账号数据"""
        accounts = self.db_manager.get_accounts(group_name)
        self.account_table.setRowCount(len(accounts))

        for i, account in enumerate(accounts):
            # account字段顺序: id, username, password, ck, nickname, account_id, login_status, homepage, login_time, proxy, running_status, note, group_name
            
            # 第一列添加复选框
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Unchecked)
            checkbox_item.setTextAlignment(Qt.AlignCenter)
            self.account_table.setItem(i, 0, checkbox_item)
            
            # 其他列数据
            self.account_table.setItem(i, 1, QTableWidgetItem(account[12] or ''))  # 分组
            self.account_table.setItem(i, 2, QTableWidgetItem(account[1] or ''))   # 账号
            self.account_table.setItem(i, 3, QTableWidgetItem(account[2] or ''))   # 密码
            self.account_table.setItem(i, 4, QTableWidgetItem(account[3] or ''))   # CK
            self.account_table.setItem(i, 5, QTableWidgetItem(account[4] or ''))   # 账号昵称
            self.account_table.setItem(i, 6, QTableWidgetItem(account[5] or ''))   # 账号ID
            self.account_table.setItem(i, 7, QTableWidgetItem(account[6] or ''))   # 登录状态
            self.account_table.setItem(i, 8, QTableWidgetItem(account[7] or ''))   # 主页地址
            self.account_table.setItem(i, 9, QTableWidgetItem(account[8] or ''))   # 登录时间
            self.account_table.setItem(i, 10, QTableWidgetItem(account[9] or ''))   # 代理IP
            self.account_table.setItem(i, 11, QTableWidgetItem(account[10] or '')) # 运行状态
            self.account_table.setItem(i, 12, QTableWidgetItem(account[11] or '')) # 备注
            
            # 保存账号ID到第二列（账号列）的UserRole中
            self.account_table.item(i, 2).setData(Qt.UserRole, account[0])
            
            # 设置行高
            self.account_table.setRowHeight(i, 36)
            
            # 设置所有单元格居中对齐（跳过复选框列）
            for j in range(1, self.account_table.columnCount()):
                item = self.account_table.item(i, j)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
    
    def add_account(self):
        """添加账号"""
        dialog = AccountDialog(self)
        if dialog.exec():
            account_data = dialog.get_data()
            if account_data is None:
                return
            # 检查用户名是否已存在
            accounts = self.db_manager.get_accounts()
            for account in accounts:
                if account[1] == account_data['username']:
                    self.browser_signals.error.emit("该用户名已存在")
                    return
            # 创建账号数据文件夹并保存指纹数据
            cache_path = self.config.get('browser_cache_path', '')
            if cache_path:
                account_dir = Path(cache_path) / account_data['username']
                account_dir.mkdir(parents=True, exist_ok=True)
                fingerprint_generator = FingerprintGenerator()
                fingerprint = fingerprint_generator.generate_random_fingerprint(account_data['proxy'])
                fingerprint_generator.save_fingerprint_to_file(fingerprint, account_dir)
            if self.db_manager.add_account(account_data):
                self.load_accounts()
                self.browser_signals.info.emit("添加账号成功")
            else:
                self.browser_signals.error.emit("添加账号失败")
    
    def edit_account(self):
        """编辑账号"""
        selected_items = self.account_table.selectedItems()
        if not selected_items:
            self.browser_signals.error.emit("请选择要编辑的账号")
            return
        
        row = selected_items[0].row()
        account_id = self.account_table.item(row, 2).data(Qt.UserRole)
        
        # 获取当前账号信息
        accounts = self.db_manager.get_accounts()
        current_account = None
        for account in accounts:
            if account[0] == account_id:
                current_account = account
                break
        
        if not current_account:
            self.browser_signals.error.emit("未找到账号信息")
            return
        
        # 准备编辑数据
        account_data = {
            'username': current_account[1],
            'password': current_account[2],
            'ck': current_account[3],
            'nickname': current_account[4],
            'account_id': current_account[5],
            'login_status': current_account[6],
            'homepage': current_account[7],
            'login_time': current_account[8],
            'proxy': current_account[9],
            'running_status': current_account[10],
            'note': current_account[11],
            'group_name': current_account[12]
        }
        
        # 加载指纹数据
        if self.config.get('browser_cache_path'):
            account_dir = str(Path(self.config['browser_cache_path']) / account_data['username'])
            fingerprint_generator = FingerprintGenerator()
            fingerprint = fingerprint_generator.load_fingerprint_from_file(account_dir)
            if fingerprint:
                account_data['fingerprint'] = fingerprint
        
        dialog = AccountDialog(self, account_data)
        if dialog.exec():
            new_data = dialog.get_data()
            if new_data is None:
                return
                
            # 检查用户名是否已存在（排除当前账号）
            if new_data['username'] != account_data['username']:
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == new_data['username'] and account[0] != account_id:
                        self.browser_signals.error.emit("该用户名已存在")
                        return
            
            if self.db_manager.update_account(account_id, new_data):
                self.load_accounts()
                self.browser_signals.info.emit("更新账号成功")
            else:
                self.browser_signals.error.emit("更新账号失败")
    
    def delete_account(self):
        """删除所有勾选的账号（基于复选框状态）"""
        # 获取所有勾选的账号
        checked_accounts = []
        for row in range(self.account_table.rowCount()):
            checkbox_item = self.account_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                # 获取账号ID（从第2列的UserRole中）
                account_item = self.account_table.item(row, 2)
                if account_item:
                    account_id = account_item.data(Qt.UserRole)
                    username = account_item.text()
                    try:
                        account_id = int(account_id)
                        checked_accounts.append((account_id, username, row))
                    except (TypeError, ValueError):
                        continue
        
        if not checked_accounts:
            self.browser_signals.error.emit("请先勾选要删除的账号")
            return
            
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除勾选的{len(checked_accounts)}个账号吗？\n该操作将同时删除账号的用户数据目录。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cache_path = self.config.get('browser_cache_path', '')
            deleted_count = 0
            
            for account_id, username, row in checked_accounts:
                try:
                    # 删除用户数据目录
                    if cache_path:
                        user_data_dir = Path(cache_path) / username
                        if user_data_dir.exists():
                            import shutil
                            shutil.rmtree(user_data_dir)
                            logger.info(f"已删除用户数据目录: {user_data_dir}")
                    
                    # 删除数据库中的账号记录
                    self.db_manager.delete_account(account_id)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"删除账号 {username} 失败: {str(e)}")
                    continue
            
            # 重新加载账号列表
            self.load_accounts()
            
            if deleted_count > 0:
                self.browser_signals.info.emit(f"成功删除 {deleted_count} 个账号")
            else:
                self.browser_signals.error.emit("删除账号失败")
    
    def add_group(self):
        """添加分组"""
        dialog = GroupDialog(self)
        if dialog.exec():
            group_name = dialog.get_data()
            if group_name:
                if self.db_manager.add_group(group_name):
                    self.load_data()
                else:
                    self.browser_signals.error.emit("添加分组失败")
    
    def delete_group(self):
        """删除分组"""
        selected_items = self.group_table.selectedItems()
        if not selected_items:
            self.browser_signals.error.emit("请选择要删除的分组")
            return
        
        group_name = selected_items[0].text()
        if group_name == "默认分组":
            self.browser_signals.error.emit("不能删除默认分组")
            return
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除分组 '{group_name}' 吗？\n该分组下的账号将移至默认分组",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db_manager.delete_group(group_name):
                self.load_data()
            else:
                self.browser_signals.error.emit("删除分组失败")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存浏览器设置
            config = {
                "browser_path": self.browser_path_edit.text() if hasattr(self, 'browser_path_edit') else '',
                "browser_cache_path": self.cache_path_edit.text() if hasattr(self, 'cache_path_edit') else '',
                
                # 保存功能设置
                "function_settings": {
                    "signature": self.signature_checkbox.isChecked() if hasattr(self, 'signature_checkbox') else False,
                    "status": self.status_checkbox.isChecked() if hasattr(self, 'status_checkbox') else False,
                    "group": self.group_checkbox.isChecked() if hasattr(self, 'group_checkbox') else False,
                    "phrase": self.phrase_checkbox.isChecked() if hasattr(self, 'phrase_checkbox') else False,
                    "content": self.content_text.toPlainText() if hasattr(self, 'content_text') else '',
                    # 合并其他设置到功能设置中
                    "rating_min": self.rating_min.text() if hasattr(self, 'rating_min') else '1',
                    "rating_max": self.rating_max.text() if hasattr(self, 'rating_max') else '2',
                    "star_rating": self.star_rating.text() if hasattr(self, 'star_rating') else '3|4|5',
                    "rating_type": self.rating_type.currentText() if hasattr(self, 'rating_type') else '电影',
                    "operation_interval_min": self.operation_interval_min.text() if hasattr(self, 'operation_interval_min') else '3',
                    "operation_interval_max": self.operation_interval_max.text() if hasattr(self, 'operation_interval_max') else '5',
                    "account_interval_min": self.account_interval_min.text() if hasattr(self, 'account_interval_min') else '3',
                    "account_interval_max": self.account_interval_max.text() if hasattr(self, 'account_interval_max') else '5',
                    "error_interval_min": self.error_interval_min.text() if hasattr(self, 'error_interval_min') else '3',
                    "error_interval_max": self.error_interval_max.text() if hasattr(self, 'error_interval_max') else '5'
                }
            }
            
            if chagyong_save_config(quan_shujuwenjianjia, config):
                self.config = config  # 更新当前配置
                self.browser_signals.info.emit("设置已保存")
                logger.info(f"配置已保存: {config}")
            else:
                self.browser_signals.error.emit("保存设置失败")
        except Exception as e:
            error_msg = f"保存设置失败: {str(e)}"
            logger.error(error_msg)
            self.browser_signals.error.emit(error_msg)
    
    def browse_browser(self):
        """浏览浏览器文件"""
        if platform.system() == "Darwin":  # macOS
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择浏览器", 
                "/Applications", 
                "应用程序 (*.app)"
            )
            if file_path:
                # 如果是 .app 包，获取实际的可执行文件路径
                if file_path.endswith('.app'):
                    app_name = os.path.basename(file_path).replace('.app', '')
                    executable_path = os.path.join(file_path, 'Contents', 'MacOS', app_name)
                    if os.path.exists(executable_path):
                        file_path = executable_path
                self.browser_path_edit.setText(file_path)
        elif platform.system() == "Windows":  # Windows
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择浏览器", 
                "C:\\Program Files", 
                "可执行文件 (*.exe)"
            )
            if file_path:
                self.browser_path_edit.setText(file_path)
        else:  # Linux
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择浏览器", 
                "", 
                "可执行文件 (*)"
            )
            if file_path:
                self.browser_path_edit.setText(file_path)
    
    def browse_cache(self):
        """浏览缓存目录"""
        # 默认使用程序目录内的 cache 文件夹
        default_dir = str(CACHE_DIR)
        
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择缓存目录",
            default_dir
        )
        if dir_path:
            self.cache_path_edit.setText(dir_path)
    
    def show_error(self, message):
        """在主线程中显示错误消息"""
        logger.error(message)
        QMessageBox.warning(self, "错误", message)

    def show_info(self, message):
        """在主线程中显示信息消息"""
        logger.info(message)

    def closeEvent(self, event):
        """程序关闭时自动保存所有配置"""
        try:
            # 保存所有设置
            self.save_settings()
            logger.info("配置已自动保存")
        except Exception as e:
            logger.error(f"程序关闭时出错: {str(e)}")
        finally:
            event.accept()

    def detect_browser_path(self):
        """自动检测浏览器路径"""
        try:
            # 使用配置系统获取默认浏览器路径
            common_paths = config.get_default_browser_paths()
            
            # 检查路径是否存在
            for path in common_paths:
                if os.path.exists(path):
                    self.browser_path_edit.setText(path)
                    self.browser_signals.info.emit(f"已找到浏览器: {path}")
                    return
            
            self.browser_signals.error.emit("未找到已安装的浏览器，请手动选择浏览器路径")
            
        except Exception as e:
            error_msg = f"检测浏览器路径失败: {str(e)}"
            logger.error(error_msg)
            self.browser_signals.error.emit(error_msg)
    
    def open_browser(self):
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._safe_open_browser())
            loop.close()
        threading.Thread(target=run, daemon=True).start()

    async def _safe_open_browser(self):
        selected_items = self.account_table.selectedItems()
        if not selected_items:
            self.browser_signals.error.emit("请选择要查看的账号")
            return
        row = selected_items[0].row()
        username = self.account_table.item(row, 2).text()  # 修正：用户名在第2列（索引2）
        proxy = self.account_table.item(row, 10).text()  # 修正：代理IP在第10列（索引10）

        # 确保只允许每个账号同时打开一个浏览器实例
        if username in self.active_browser_sessions and self.active_browser_sessions[username]['thread'].is_alive():
            self.browser_signals.info.emit(f"账号 {username} 的浏览器已在运行。")
            return

        cache_path = self.config.get('browser_cache_path', '')
        if not cache_path:
            self.browser_signals.error.emit("请先在设置中配置浏览器缓存路径")
            return
        account_dir = Path(cache_path) / username
        lock_file = account_dir / "SingletonLock"
        liulanqi = None
        if username in self.active_browser_sessions:
            liulanqi = self.active_browser_sessions[username].get('liulanqi')

        def chrome_process_exists(user_data_dir):
            try:
                if platform.system() == "Windows":
                    # Windows 使用 tasklist 命令
                    result = subprocess.run([
                        "tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV"], 
                        capture_output=True, text=True, encoding='gbk'
                    )
                    return "chrome.exe" in result.stdout
                else:
                    # Unix/Linux/macOS 使用 ps 命令
                    result = subprocess.run([
                        "ps", "aux"], capture_output=True, text=True
                    )
                    for line in result.stdout.splitlines():
                        if "Google Chrome" in line and str(user_data_dir) in line:
                            return True
                    return False
            except Exception as e:
                print(f"检测进程失败: {e}")
                return False

        def kill_chrome_process(user_data_dir):
            try:
                if platform.system() == "Windows":
                    # Windows 使用 taskkill 命令
                    subprocess.run([
                        "taskkill", "/F", "/IM", "chrome.exe"], 
                        capture_output=True, text=True
                    )
                else:
                    # Unix/Linux/macOS 使用 ps 和 kill 命令
                    result = subprocess.run([
                        "ps", "aux"], capture_output=True, text=True
                    )
                    for line in result.stdout.splitlines():
                        if "Google Chrome" in line and str(user_data_dir) in line:
                            pid = int(line.split()[1])
                            subprocess.run(["kill", "-9", str(pid)])
            except Exception as e:
                print(f"强制杀进程失败: {e}")

        # 检查锁文件或进程
        if (lock_file.exists() or chrome_process_exists(account_dir)) and liulanqi:
            self.browser_signals.info.emit("检测到浏览器未完全关闭，正在尝试自动关闭...")
            await liulanqi.guanbi()
            wait_time = 0
            while (lock_file.exists() or chrome_process_exists(account_dir)) and wait_time < 5:
                await asyncio.sleep(1)
                wait_time += 1
            if lock_file.exists() or chrome_process_exists(account_dir):
                self.browser_signals.info.emit("优雅关闭失败，尝试强制关闭浏览器进程...")
                kill_chrome_process(account_dir)
                # 再等2秒
                await asyncio.sleep(2)
                if lock_file.exists() or chrome_process_exists(account_dir):
                    self.browser_signals.error.emit("浏览器强制关闭失败，请重启电脑或手动清理进程。")
                    return

        fingerprint_generator = FingerprintGenerator()
        fingerprint = fingerprint_generator.load_fingerprint_from_file(account_dir)
        if not fingerprint:
            self.browser_signals.error.emit("该账号未保存指纹数据，请先保存指纹数据")
            return
        browser_path = self.config.get('browser_path', '')
        if not browser_path:
            self.browser_signals.error.emit("请先在设置中配置浏览器路径")
            return
        logger.info(f"正在启动浏览器 - 用户: {username}")
        peizhi = LiulanqiPeizhi(
            zhanghao=username,
            daili=proxy if proxy else None,
            wangzhi=DEFAULT_URL,
            huanchunlujing=str(account_dir),
            chrome_path=browser_path,
            fingerprint=fingerprint
        )
        stop_event = threading.Event()
        liulanqi = Liulanqi(peizhi, self.browser_signals, self.db_manager)
        liulanqi.set_main_window(self)
        async def run_browser_session():
            try:
                logger.info(f"开始初始化浏览器 - 用户: {username}...")
                await liulanqi.chushihua()
                if liulanqi._is_closed:
                    logger.info(f"浏览器 {username} 在初始化过程中被关闭")
                    return
                logger.info(f"浏览器 {username} 初始化成功，正在打开页面...")
                await liulanqi.dakai_ye()
                if liulanqi._is_closed:
                    logger.info(f"浏览器 {username} 在打开页面过程中被关闭")
                    return
                logger.info(f"浏览器 {username} 页面打开成功，进入监控循环...")
                while not stop_event.is_set() and not liulanqi._is_closed:
                    try:
                        await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        logger.info(f"浏览器任务 {username} 被取消")
                        break
                    except Exception as e:
                        if not liulanqi._is_closed:
                            logger.error(f"检查浏览器 {username} 状态时出错: {str(e)}")
                        break
            except Exception as e:
                error_msg = f"浏览器 {username} 操作失败: {str(e)}"
                logger.error(error_msg)
                self.browser_signals.error.emit(error_msg)
            finally:
                logger.info(f"浏览器 {username} 会话结束，尝试关闭浏览器...")
                if liulanqi:
                    try:
                        await liulanqi.guanbi()
                    except Exception as e:
                        logger.info(f"关闭浏览器 {username} 时出错: {str(e)}")
                else:
                    logger.info(f"浏览器 {username} 实例未创建，跳过关闭。")
                QTimer.singleShot(0, lambda: self.handle_browser_closed(username))
        def run_thread_sync():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(run_browser_session())
                except Exception as e:
                    logger.error(f"运行浏览器会话 {username} 任务失败: {str(e)}")
                finally:
                    try:
                        pending_tasks = asyncio.all_tasks(loop=loop)
                        for task in pending_tasks:
                            task.cancel()
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                        loop.close()
                        logger.info(f"浏览器会话 {username} 的事件循环已关闭。")
                    except Exception as e:
                        logger.error(f"关闭浏览器会话 {username} 的事件循环时出错: {str(e)}")
            except Exception as e:
                error_msg = f"运行浏览器线程 {username} 失败: {str(e)}"
                logger.error(error_msg)
                self.browser_signals.error.emit(error_msg)
        logger.info(f"正在创建浏览器 {username} 启动线程...")
        thread = threading.Thread(target=run_thread_sync, daemon=False)
        thread.start()
        self.active_browser_sessions[username] = {'thread': thread, 'stop_event': stop_event, 'liulanqi': liulanqi}
        logger.info(f"浏览器 {username} 启动线程已创建并记录。")

    def refresh_account_info(self, username):
        """刷新指定账号的信息显示"""
        try:
            # 获取当前选中的分组
            selected_items = self.group_table.selectedItems()
            current_group = selected_items[0].text() if selected_items else None
            
            # 重新加载账号数据
            self.load_accounts(current_group)
            
            # 找到并选中更新后的账号行
            for row in range(self.account_table.rowCount()):
                if self.account_table.item(row, 2).text() == username:  # 修正：用户名在第2列（索引2）
                    self.account_table.selectRow(row)
                    break
                    
            logger.info(f"已刷新账号 {username} 的信息显示")
        except Exception as e:
            logger.error(f"刷新账号信息显示失败: {str(e)}")

    def handle_browser_closed(self, username):
        """处理浏览器关闭事件"""
        try:
            # 从活动会话中移除
            if username in self.active_browser_sessions:
                del self.active_browser_sessions[username]
            
            # 刷新账号信息显示
            self.refresh_account_info(username)
            logger.info(f"已处理浏览器关闭事件并刷新账号 {username} 的信息")
        except Exception as e:
            logger.error(f"处理浏览器关闭事件失败: {str(e)}")

    def load_movies_and_contents(self):
        """加载电影和内容数据"""
        try:
            # 使用数据库管理器加载数据
            # 加载指定电影数据
            specific_movies = self.db_manager.load_movies('specific')
            if specific_movies is not None:
                self.movie_specific_table.setRowCount(len(specific_movies))
                for i, movie_data in enumerate(specific_movies):
                    if isinstance(movie_data, (list, tuple)) and len(movie_data) == 2:
                        movie_id, rating = movie_data
                        self.movie_specific_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                        self.movie_specific_table.setItem(i, 1, QTableWidgetItem(str(movie_id)))
                        self.movie_specific_table.setItem(i, 2, QTableWidgetItem(str(rating)))
                        # 设置单元格居中对齐
                        for col in range(3):
                            item = self.movie_specific_table.item(i, col)
                            if item:
                                item.setTextAlignment(Qt.AlignCenter)
            
            # 加载随机电影数据
            random_movies = self.db_manager.load_movies('random')
            if random_movies is not None:
                self.movie_random_table.setRowCount(len(random_movies))
                for i, movie_data in enumerate(random_movies):
                    if isinstance(movie_data, (list, tuple)) and len(movie_data) == 2:
                        movie_id, rating = movie_data
                        self.movie_random_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                        self.movie_random_table.setItem(i, 1, QTableWidgetItem(str(movie_id)))
                        self.movie_random_table.setItem(i, 2, QTableWidgetItem(str(rating)))
                        # 设置单元格居中对齐
                        for col in range(3):
                            item = self.movie_random_table.item(i, col)
                            if item:
                                item.setTextAlignment(Qt.AlignCenter)
            
            # 加载指定内容数据
            specific_contents = self.db_manager.load_contents('specific')
            if specific_contents is not None:
                self.content_specific_table.setRowCount(len(specific_contents))
                for i, content in enumerate(specific_contents):
                    self.content_specific_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.content_specific_table.setItem(i, 1, QTableWidgetItem(str(content)))
                    # 设置单元格居中对齐
                    for col in range(2):
                        item = self.content_specific_table.item(i, col)
                        if item:
                            item.setTextAlignment(Qt.AlignCenter)
            
            # 加载随机内容数据
            random_contents = self.db_manager.load_contents('random')
            if random_contents is not None:
                self.content_random_table.setRowCount(len(random_contents))
                for i, content in enumerate(random_contents):
                    self.content_random_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.content_random_table.setItem(i, 1, QTableWidgetItem(str(content)))
                    # 设置单元格居中对齐
                    for col in range(2):
                        item = self.content_random_table.item(i, col)
                        if item:
                            item.setTextAlignment(Qt.AlignCenter)
            
            logger.info("电影和内容数据加载成功")
        except Exception as e:
            error_msg = f"加载电影和内容数据失败: {str(e)}"
            logger.error(error_msg)
            self.browser_signals.error.emit(error_msg)
        finally:
            # 清理数据
            try:
                del specific_movies
                del random_movies
                del specific_contents
                del random_contents
            except:
                pass

    def add_movie(self, movie_type):
        """添加电影"""
        from PySide6.QtWidgets import QInputDialog, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"添加{movie_type}电影")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        
        # 创建输入字段
        movie_id_edit = QLineEdit()
        rating_edit = QLineEdit()
        rating_edit.setPlaceholderText("评分(可选)")
        
        layout.addRow("电影ID:", movie_id_edit)
        layout.addRow("评分:", rating_edit)
        
        # 添加按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            movie_id = movie_id_edit.text().strip()
            rating_str = rating_edit.text().strip()
            
            if not movie_id:
                QMessageBox.warning(self, "警告", "电影ID不能为空")
                return
            
            try:
                rating = float(rating_str) if rating_str else None
                if rating is not None and (rating < 0 or rating > 10):
                    QMessageBox.warning(self, "警告", "评分必须在0-10之间")
                    return
            except ValueError:
                QMessageBox.warning(self, "警告", "评分必须是数字")
                return
            
            # 获取现有电影数据
            movies = self.db_manager.load_movies(movie_type)
            if movies is None:
                movies = []
            
            # 检查重复
            for existing_movie in movies:
                if existing_movie[0] == movie_id:
                    QMessageBox.warning(self, "警告", "该电影ID已存在")
                    return
            
            # 添加新电影
            movies.append([movie_id, str(rating) if rating else ""])
            
            if self.db_manager.save_movies(movies, movie_type):
                self.load_movies_and_contents()
                QMessageBox.information(self, "成功", "电影添加成功")
            else:
                QMessageBox.warning(self, "失败", "电影添加失败")
    
    def delete_movie(self):
        """删除选中的电影"""
        # 检查指定电影表格的选中项
        selected_specific = self.movie_specific_table.selectedItems()
        selected_random = self.movie_random_table.selectedItems()
        
        if not selected_specific and not selected_random:
            QMessageBox.warning(self, "警告", "请选择要删除的电影")
            return
        
        # 确定要删除的电影类型和行
        if selected_specific:
            table = self.movie_specific_table
            movie_type = "specific"
            row = selected_specific[0].row()
            movie_id = table.item(row, 1).text()
        else:
            table = self.movie_random_table
            movie_type = "random"
            row = selected_random[0].row()
            movie_id = table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除电影 '{movie_id}' 吗？")
        if reply == QMessageBox.Yes:
            # 获取现有电影数据
            movies = self.db_manager.load_movies(movie_type)
            if movies is None:
                return
            
            # 删除选中的电影
            del movies[row]
            
            if self.db_manager.save_movies(movies, movie_type):
                self.load_movies_and_contents()
                QMessageBox.information(self, "成功", "电影删除成功")
            else:
                QMessageBox.warning(self, "失败", "电影删除失败")
    
    def delete_movies_batch(self):
        """批量删除电影"""
        # 检查指定电影表格的选中项
        selected_specific = self.movie_specific_table.selectedItems()
        selected_random = self.movie_random_table.selectedItems()
        
        if not selected_specific and not selected_random:
            QMessageBox.warning(self, "警告", "请选择要删除的电影")
            return
        
        # 确定要删除的电影类型和行
        if selected_specific:
            table = self.movie_specific_table
            movie_type = "specific"
            selected_rows = set()
            for item in selected_specific:
                selected_rows.add(item.row())
        else:
            table = self.movie_random_table
            movie_type = "random"
            selected_rows = set()
            for item in selected_random:
                selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 部电影吗？")
        if reply == QMessageBox.Yes:
            # 获取现有电影数据
            movies = self.db_manager.load_movies(movie_type)
            if movies is None:
                return
            
            # 按行号倒序删除，避免索引变化问题
            for row in sorted(selected_rows, reverse=True):
                if row < len(movies):
                    del movies[row]
            
            if self.db_manager.save_movies(movies, movie_type):
                self.load_movies_and_contents()
                QMessageBox.information(self, "成功", f"成功删除 {len(selected_rows)} 部电影")
            else:
                QMessageBox.warning(self, "失败", "电影删除失败")
    
    def add_content(self, content_type):
        """添加内容"""
        from PySide6.QtWidgets import QInputDialog, QDialog, QFormLayout, QPlainTextEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"添加{content_type}内容")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QFormLayout(dialog)
        
        # 创建文本输入区域
        content_edit = QPlainTextEdit()
        content_edit.setPlaceholderText("请输入内容...")
        
        layout.addRow("内容:", content_edit)
        
        # 添加按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            content = content_edit.toPlainText().strip()
            
            if not content:
                QMessageBox.warning(self, "警告", "内容不能为空")
                return
            
            # 获取现有内容数据
            contents = self.db_manager.load_contents(content_type)
            if contents is None:
                contents = []
            
            # 检查重复
            if content in contents:
                QMessageBox.warning(self, "警告", "该内容已存在")
                return
            
            # 添加新内容
            contents.append(content)
            
            if self.db_manager.save_contents(contents, content_type):
                self.load_movies_and_contents()
                QMessageBox.information(self, "成功", "内容添加成功")
            else:
                QMessageBox.warning(self, "失败", "内容添加失败")
    
    def delete_content(self):
        """删除选中的内容"""
        # 检查指定内容表格的选中项
        selected_specific = self.content_specific_table.selectedItems()
        selected_random = self.content_random_table.selectedItems()
        
        if not selected_specific and not selected_random:
            QMessageBox.warning(self, "警告", "请选择要删除的内容")
            return
        
        # 确定要删除的内容类型和行
        if selected_specific:
            table = self.content_specific_table
            content_type = "specific"
            row = selected_specific[0].row()
            content = table.item(row, 1).text()
        else:
            table = self.content_random_table
            content_type = "random"
            row = selected_random[0].row()
            content = table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除该内容吗？")
        if reply == QMessageBox.Yes:
            # 获取现有内容数据
            contents = self.db_manager.load_contents(content_type)
            if contents is None:
                return
            
            # 删除选中的内容
            del contents[row]
            
            if self.db_manager.save_contents(contents, content_type):
                self.load_movies_and_contents()
                QMessageBox.information(self, "成功", "内容删除成功")
            else:
                QMessageBox.warning(self, "失败", "内容删除失败")
    
    def delete_contents_batch(self):
        """批量删除内容"""
        # 检查指定内容表格的选中项
        selected_specific = self.content_specific_table.selectedItems()
        selected_random = self.content_random_table.selectedItems()
        
        if not selected_specific and not selected_random:
            QMessageBox.warning(self, "警告", "请选择要删除的内容")
            return
        
        # 确定要删除的内容类型和行
        if selected_specific:
            table = self.content_specific_table
            content_type = "specific"
            selected_rows = set()
            for item in selected_specific:
                selected_rows.add(item.row())
        else:
            table = self.content_random_table
            content_type = "random"
            selected_rows = set()
            for item in selected_random:
                selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        reply = QMessageBox.question(self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 条内容吗？")
        if reply == QMessageBox.Yes:
            # 获取现有内容数据
            contents = self.db_manager.load_contents(content_type)
            if contents is None:
                return
            
            # 按行号倒序删除，避免索引变化问题
            for row in sorted(selected_rows, reverse=True):
                if row < len(contents):
                    del contents[row]
            
            if self.db_manager.save_contents(contents, content_type):
                self.load_movies_and_contents()
                QMessageBox.information(self, "成功", f"成功删除 {len(selected_rows)} 条内容")
            else:
                QMessageBox.warning(self, "失败", "内容删除失败")
    

    
    def clear_all_movies(self):
        """清空所有电影"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有电影数据吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            # 清空指定电影
            if self.db_manager.save_movies([], 'specific'):
                self.movie_specific_table.setRowCount(0)
            
            # 清空随机电影
            if self.db_manager.save_movies([], 'random'):
                self.movie_random_table.setRowCount(0)
            
            QMessageBox.information(self, "成功", "所有电影数据已清空")
    
    def clear_all_contents(self):
        """清空所有内容"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有内容数据吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            # 清空指定内容
            if self.db_manager.save_contents([], 'specific'):
                self.content_specific_table.setRowCount(0)
            
            # 清空随机内容
            if self.db_manager.save_contents([], 'random'):
                self.content_random_table.setRowCount(0)
            
            QMessageBox.information(self, "成功", "所有内容数据已清空")
    
    def clear_specific_movies(self):
        """清空指定电影"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有指定电影数据吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            if self.db_manager.save_movies([], 'specific'):
                self.movie_specific_table.setRowCount(0)
                QMessageBox.information(self, "成功", "指定电影数据已清空")
    
    def clear_random_movies(self):
        """清空随机电影"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有随机电影数据吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            if self.db_manager.save_movies([], 'random'):
                self.movie_random_table.setRowCount(0)
                QMessageBox.information(self, "成功", "随机电影数据已清空")
    
    def clear_specific_contents(self):
        """清空指定内容"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有指定内容数据吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            if self.db_manager.save_contents([], 'specific'):
                self.content_specific_table.setRowCount(0)
                QMessageBox.information(self, "成功", "指定内容数据已清空")
    
    def clear_random_contents(self):
        """清空随机内容"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有随机内容数据吗？此操作不可恢复！")
        if reply == QMessageBox.Yes:
            if self.db_manager.save_contents([], 'random'):
                self.content_random_table.setRowCount(0)
                QMessageBox.information(self, "成功", "随机内容数据已清空")
    
    def on_run_start_clicked(self):
        QMessageBox.information(self, "提示", "运行功能后续实现")
    
    def add_proxy(self):
        """添加代理"""
        selected_rows = set()
        for item in self.account_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要添加代理的账号")
            return
        
        # 创建自定义对话框
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle("添加代理")
        dialog.setMinimumSize(400, 150)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加说明标签
        label = QLabel("请输入代理地址：")
        layout.addWidget(label)
        
        # 添加输入框
        proxy_input = QLineEdit()
        proxy_input.setPlaceholderText("例如：http://127.0.0.1:7890")
        layout.addWidget(proxy_input)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # 连接信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.Accepted:
            proxy = proxy_input.text()
            if proxy:
                success_count = 0
                for row in selected_rows:
                    username = self.account_table.item(row, 2).text()  # 修正：用户名在第2列（索引2）
                    # 获取当前账号的所有信息
                    accounts = self.db_manager.get_accounts()
                    for account in accounts:
                        if account[1] == username:
                            try:
                                account_data = {
                                    'username': account[1],
                                    'password': account[2],
                                    'ck': account[3],
                                    'nickname': account[4],
                                    'account_id': account[5],
                                    'login_status': account[6],
                                    'homepage': account[7],
                                    'login_time': account[8],
                                    'proxy': proxy,
                                    'running_status': account[10],
                                    'note': account[11],
                                    'group_name': account[12]
                                }
                                if self.db_manager.update_account(account[0], account_data):
                                    success_count += 1
                                break
                            except Exception as e:
                                logger.error(f"处理账号 {username} 的数据时出错: {str(e)}")
                                continue
                
                # 刷新账号列表
                self.load_accounts()
                
                # 显示结果
                if success_count > 0:
                    QMessageBox.information(self, "成功", f"成功为 {success_count} 个账号添加代理")
                else:
                    QMessageBox.warning(self, "失败", "添加代理失败")

    def remove_proxy(self):
        """删除代理"""
        selected_rows = set()
        for item in self.account_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除代理的账号")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除选中账号的代理吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            for row in selected_rows:
                username = self.account_table.item(row, 2).text()  # 修正：用户名在第2列（索引2）
                # 获取当前账号的所有信息
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == username:
                        try:
                            account_data = {
                                'username': account[1],
                                'password': account[2],
                                'ck': account[3],
                                'nickname': account[4],
                                'account_id': account[5],
                                'login_status': account[6],
                                'homepage': account[7],
                                'login_time': account[8],
                                'proxy': '',
                                'running_status': account[10],
                                'note': account[11],
                                'group_name': account[12]
                            }
                            if self.db_manager.update_account(account[0], account_data):
                                success_count += 1
                            break
                        except Exception as e:
                            logger.error(f"处理账号 {username} 的数据时出错: {str(e)}")
                            continue
            
            # 刷新账号列表
            self.load_accounts()
            
            # 显示结果
            if success_count > 0:
                QMessageBox.information(self, "成功", f"成功删除 {success_count} 个账号的代理")
            else:
                QMessageBox.warning(self, "失败", "删除代理失败")

if __name__ == "__main__":
    # 系统特定的配置
    if platform.system() == "Darwin":  # macOS
        # 设置 Mac 特定的环境变量
        os.environ["QT_MAC_WANTS_LAYER"] = "1"
        os.environ["QT_MAC_DISABLE_LAYER_BACKING"] = "0"
        # 禁用 Qt 的图层警告
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.*=false"
        
        # 设置 Mac 特定的文件权限
        try:
            # 检查并修复数据目录权限
            if not os.access(quan_shujuwenjianjia, os.R_OK | os.W_OK | os.X_OK):
                os.chmod(quan_shujuwenjianjia, 0o755)  # rwxr-xr-x
                logger.info("已修复数据目录权限")
            
            # 检查并修复日志目录权限
            log_dir = Path(__file__).parent / "logs"
            if not os.access(log_dir, os.R_OK | os.W_OK | os.X_OK):
                os.chmod(log_dir, 0o755)  # rwxr-xr-x
                logger.info("已修复日志目录权限")
                
            # 检查并修复 .nomedia 文件权限
            nomedia_file = quan_shujuwenjianjia / ".nomedia"
            if nomedia_file.exists() and not os.access(nomedia_file, os.R_OK | os.W_OK):
                os.chmod(nomedia_file, 0o644)  # rw-r--r--
                logger.info("已修复 .nomedia 文件权限")
        except Exception as e:
            logger.error(f"修复文件权限失败: {str(e)}")
    
    elif platform.system() == "Windows":  # Windows
        # Windows 特定的配置
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
        
        # 设置 Windows 特定的样式
        os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
    
    app = QApplication(sys.argv)
    
    # 设置Fluent风格
    app.setStyle('Fusion')  # 使用Fusion风格作为基础
    
    # 设置系统特定的应用程序属性
    if platform.system() == "Darwin":  # macOS
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
        app.setAttribute(Qt.AA_EnableHighDpiScaling)

    
    elif platform.system() == "Windows":  # Windows
        app.setAttribute(Qt.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    window = AccountManagerWindow()
    window.show()
    sys.exit(app.exec())