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
# 导入枚举值
from PySide6.QtWidgets import QAbstractItemView, QSizePolicy
from data_manager import DataManager
from pathlib import Path
from mokuai_chagyong import chagyong_load_config, chagyong_save_config
from liulanqi_gongcaozuo import LiulanqiGongcaozuo, LiulanqiPeizhi
from renwuliucheng import RenwuLiucheng
from liulanqimokuai.fingerprint_manager import FingerprintManager
from config import config, DATA_DIR, LOGS_DIR, TEMP_DIR, BACKUP_DIR
from styles import (
    get_complete_fluent_style, DIALOG_STYLE, FINGERPRINT_DIALOG_STYLE,
    FLUENT_COLORS, LAYOUT
)
# 导入按钮处理函数
from handlers.button_handlers import (
    add_account_handler, edit_account_handler, delete_account_handler,
    add_proxy_handler, remove_proxy_handler, clear_all_movies_handler,
    clear_all_contents_handler, clear_specific_movies_handler, 
    clear_random_movies_handler, clear_specific_contents_handler, 
    clear_random_contents_handler, on_run_start_clicked_handler,
    add_movie_handler, delete_movie_handler, delete_movies_batch_handler,
    add_content_handler, delete_content_handler, delete_contents_batch_handler,
    update_movie_rating_handler
)
# 导入统一的UI组件
from ui.dialogs import BaseDialog, AccountDialog, GroupDialog

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
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
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

# BaseDialog 类已移至 ui.dialogs.base_dialog 模块

# AccountDialog 类已移至 ui.dialogs.account_dialog 模块

# GroupDialog 类已移至 ui.dialogs.account_dialog 模块

class BrowserSignals(QObject):
    """浏览器信号类"""
    error = Signal(str)  # 错误信号
    info = Signal(str)   # 信息信号
    account_closed = Signal(str)  # 账号关闭信号

class AccountManagerWindow(QMainWindow):
    """账号管理主窗口"""
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.group_table = QTableWidget()    # 只在这里创建一次
        self.account_table = QTableWidget()  # 只在这里创建一次
        self.config = {}
        self.browser_signals = BrowserSignals()
        self.browser_signals.error.connect(self.show_error)
        self.browser_signals.info.connect(self.show_info)
        self.browser_signals.account_closed.connect(self.handle_browser_closed)

        self.active_browser_sessions = {} # Store {username: {'thread': Thread, 'stop_event': Event, 'liulanqi': Liulanqi_instance}}
        
        # 初始化分组选择状态跟踪
        self.group_selected = False
        self.selected_group_name = None
        
        self.load_config()
        self.init_ui()
        self.apply_fluent_style()  # 应用Fluent风格
        logger.info("账号管理系统初始化完成")
    
    def apply_fluent_style(self):
        """应用Fluent设计风格"""
        self.setStyleSheet(get_complete_fluent_style())
    
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
        self.group_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.group_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.group_table.verticalHeader().setVisible(False)
        self.group_table.setMinimumWidth(180)
        
        # 设置分组表格样式优化
        self.group_table.setAlternatingRowColors(True)  # 交替行颜色
        self.group_table.setShowGrid(True)  # 显示网格线
        self.group_table.setGridStyle(Qt.PenStyle.SolidLine)  # 实线网格
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
        self.account_table.setGridStyle(Qt.PenStyle.SolidLine)  # 实线网格
        
        self.account_table.horizontalHeader().setStretchLastSection(True)
        self.account_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.account_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
        
        self.open_browser2_btn = QPushButton("打开浏览器2")
        self.open_browser2_btn.setMinimumSize(90, 32)  # 缩小宽度

        # 新增：关闭浏览器按钮
        self.close_browser_btn = QPushButton("关闭浏览器")
        self.close_browser_btn.setMinimumSize(90, 32)
        
        self.update_browser_btn = QPushButton("更新账号")
        self.update_browser_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        self.add_proxy_btn = QPushButton("添加代理")
        self.add_proxy_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        self.remove_proxy_btn = QPushButton("删除代理")
        self.remove_proxy_btn.setMinimumSize(80, 32)  # 缩小宽度
        
        # 连接按钮信号
        self.add_account_btn.clicked.connect(self.add_account)
        self.edit_account_btn.clicked.connect(self.edit_account)
        self.delete_account_btn.clicked.connect(self.delete_account)
        self.open_browser_btn.clicked.connect(self.open_browser)
        self.open_browser2_btn.clicked.connect(self.open_browser2)
        self.close_browser_btn.clicked.connect(self.close_browser)
        self.update_browser_btn.clicked.connect(self.update_account)
        self.add_proxy_btn.clicked.connect(self.add_proxy)
        self.remove_proxy_btn.clicked.connect(self.remove_proxy)
        
        # 添加按钮到布局
        account_btn_layout.addWidget(self.select_all_btn)
        account_btn_layout.addWidget(self.deselect_all_btn)
        account_btn_layout.addWidget(self.add_account_btn)
        account_btn_layout.addWidget(self.edit_account_btn)
        account_btn_layout.addWidget(self.delete_account_btn)
        account_btn_layout.addWidget(self.open_browser_btn)
        account_btn_layout.addWidget(self.open_browser2_btn)
        account_btn_layout.addWidget(self.close_browser_btn)
        account_btn_layout.addWidget(self.update_browser_btn)
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
            table.setHorizontalHeaderLabels(["序号", "电影ID", "星级"])
            table.horizontalHeader().setStretchLastSection(True)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
            table.setColumnWidth(2, 100)  # 星级列
            
            # 设置Fluent风格优化
            table.setAlternatingRowColors(True)  # 交替行颜色
            table.setShowGrid(True)  # 显示网格线
            table.setGridStyle(Qt.PenStyle.SolidLine)  # 实线网格
        
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
        add_specific_movie_btn.clicked.connect(lambda: add_movie_handler(self, "specific"))
        
        add_random_movie_btn = QPushButton("添加随机")
        add_random_movie_btn.setMinimumSize(80, 32)  # 缩小宽度
        add_random_movie_btn.clicked.connect(lambda: add_movie_handler(self, "random"))
        
        delete_movie_btn = QPushButton("删除选中")
        delete_movie_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_movie_btn.clicked.connect(lambda: delete_movie_handler(self))
        
        delete_movies_batch_btn = QPushButton("批量删除")
        delete_movies_batch_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_movies_batch_btn.clicked.connect(lambda: delete_movies_batch_handler(self))
        
        update_rating_btn = QPushButton("更新星级")
        update_rating_btn.setMinimumSize(80, 32)  # 缩小宽度
        update_rating_btn.clicked.connect(lambda: update_movie_rating_handler(self))
        
        movie_btn_layout.addWidget(add_specific_movie_btn)
        movie_btn_layout.addWidget(add_random_movie_btn)
        movie_btn_layout.addWidget(delete_movie_btn)
        movie_btn_layout.addWidget(delete_movies_batch_btn)
        movie_btn_layout.addWidget(update_rating_btn)
        
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
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
            table.setGridStyle(Qt.PenStyle.SolidLine)  # 实线网格
        
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
        add_specific_content_btn.clicked.connect(lambda: add_content_handler(self, "specific"))
        
        add_random_content_btn = QPushButton("添加随机")
        add_random_content_btn.setMinimumSize(80, 32)  # 缩小宽度
        add_random_content_btn.clicked.connect(lambda: add_content_handler(self, "random"))
        
        delete_content_btn = QPushButton("删除选中")
        delete_content_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_content_btn.clicked.connect(lambda: delete_content_handler(self))
        
        delete_contents_batch_btn = QPushButton("批量删除")
        delete_contents_batch_btn.setMinimumSize(80, 32)  # 缩小宽度
        delete_contents_batch_btn.clicked.connect(lambda: delete_contents_batch_handler(self))
        
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
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                edit.setFixedWidth(60)
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
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
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.run_mode_combo.addItems(["指定电影评论评星", "随机评论", "其他功能"])
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

        # 添加开启代理复选框
        self.enable_proxy_checkbox = QCheckBox("开启代理")
        self.enable_proxy_checkbox.setToolTip("勾选后将使用账号配置的代理设置")
        run_layout.addWidget(self.enable_proxy_checkbox)

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
        
        browser_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        layout.addWidget(browser_group)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
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
        groups = self.data_manager.get_groups()
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
            self.group_selected = True
            self.selected_group_name = selected[0].text()
            print(f"✅ 已选择分组: {self.selected_group_name}")
            self.load_accounts(selected[0].text())
        else:
            self.group_selected = False
            self.selected_group_name = None
            print(f"⚠️ 未选择任何分组")
            self.load_accounts()
    
    def on_account_checkbox_clicked(self, row, column):
        """处理账号复选框点击事件"""
        if column == 0:  # 只有点击复选框列才处理
            item = self.account_table.item(row, 0)
            if item:
                # 切换复选框状态
                current_state = item.checkState()
                new_state = Qt.CheckState.Checked if current_state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
                item.setCheckState(new_state)
                
                # 更新数据库中的勾选状态
                try:
                    # 获取账号ID（存储在账号列的UserRole中）
                    account_id = self.account_table.item(row, 2).data(Qt.ItemDataRole.UserRole)
                    if account_id:
                        # 转换勾选状态为数据库值
                        gouxuan_value = 1 if new_state == Qt.CheckState.Checked else 0
                        # 更新数据库
                        if self.data_manager.update_account_gouxuan(account_id, gouxuan_value):
                            logger.debug(f"账号 {account_id} 勾选状态已更新为: {gouxuan_value}")
                        else:
                            logger.error(f"更新账号 {account_id} 勾选状态失败")
                except Exception as e:
                    logger.error(f"处理账号勾选状态更新时出错: {str(e)}")
    
    def get_selected_accounts(self):
        """获取所有选中的账号"""
        selected_accounts = []
        for row in range(self.account_table.rowCount()):
            checkbox_item = self.account_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                username = self.account_table.item(row, 2).text()
                account_id = self.account_table.item(row, 2).data(Qt.ItemDataRole.UserRole)
                selected_accounts.append({
                    'row': row,
                    'username': username,
                    'account_id': account_id
                })
        return selected_accounts
    
    def is_group_selected(self):
        """检查是否已选择分组"""
        return self.group_selected
    
    def get_selected_group_name(self):
        """获取当前选中的分组名称"""
        return self.selected_group_name
    
    def select_all_accounts(self, select=True):
        """全选或取消全选所有账号"""
        for row in range(self.account_table.rowCount()):
            checkbox_item = self.account_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setCheckState(Qt.CheckState.Checked if select else Qt.CheckState.Unchecked)
                
                # 更新数据库中的勾选状态
                try:
                    account_id = self.account_table.item(row, 2).data(Qt.ItemDataRole.UserRole)
                    if account_id:
                        gouxuan_value = 1 if select else 0
                        if self.data_manager.update_account_gouxuan(account_id, gouxuan_value):
                            logger.debug(f"账号 {account_id} 全选状态已更新为: {gouxuan_value}")
                        else:
                            logger.error(f"更新账号 {account_id} 全选状态失败")
                except Exception as e:
                    logger.error(f"处理账号全选状态更新时出错: {str(e)}")
    
    def load_accounts(self, group_name=None):
        """加载账号数据"""
        accounts = self.data_manager.get_accounts(group_name)
        self.account_table.setRowCount(len(accounts))

        for i, account in enumerate(accounts):
            # account字段顺序: id, username, password, ck, nickname, account_id, login_status, homepage, login_time, proxy, running_status, note, group_name
            
            # 第一列添加复选框
            checkbox_item = QTableWidgetItem()
            # 恢复之前保存的勾选状态（account[13]是gouxuan字段）
            gouxuan_state = account[13] if len(account) > 13 else 0
            checkbox_item.setCheckState(Qt.CheckState.Checked if gouxuan_state == 1 else Qt.CheckState.Unchecked)
            checkbox_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
            self.account_table.item(i, 2).setData(Qt.ItemDataRole.UserRole, account[0])
            
            # 设置行高
            self.account_table.setRowHeight(i, 36)
            
            # 设置所有单元格居中对齐（跳过复选框列）
            for j in range(1, self.account_table.columnCount()):
                item = self.account_table.item(i, j)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def add_account(self):
        """添加账号"""
        add_account_handler(self)
    
    def edit_account(self):
        """编辑账号"""
        edit_account_handler(self)
    
    def delete_account(self):
        """删除所有勾选的账号（基于复选框状态）"""
        delete_account_handler(self)
    
    def add_group(self):
        """添加分组"""
        dialog = GroupDialog(self)
        if dialog.exec():
            group_name = dialog.get_data()
            if group_name:
                if self.data_manager.add_group(group_name):
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.data_manager.delete_group(group_name):
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
        default_dir = str(Path(__file__).parent / "cache")
        
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
        try:
            from datetime import datetime
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{ts}] {message}")
        except Exception:
            pass

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
        """打开浏览器（登录模式）"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._safe_open_browser("denglu"))
            loop.close()
        threading.Thread(target=run, daemon=True).start()
    
    def open_browser2(self):
        """打开浏览器2（更新模式）"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._safe_open_browser("gengxin"))
            loop.close()
        threading.Thread(target=run, daemon=True).start()

    def close_browser(self):
        """关闭当前选中账号的浏览器"""
        try:
            selected_items = self.account_table.selectedItems()
            if not selected_items:
                self.browser_signals.error.emit("请选择要关闭浏览器的账号")
                return
            username = self.account_table.item(selected_items[0].row(), 2).text()
            session = self.active_browser_sessions.get(username)
            if not session:
                self.browser_signals.error.emit("该账号没有正在运行的浏览器")
                return
            liulanqi = session.get('liulanqi')
            if not liulanqi:
                self.browser_signals.error.emit("未找到浏览器实例")
                return

            def run_close():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(liulanqi.guanbi())
                finally:
                    loop.close()
                # 主线程上清理会话并刷新
                QTimer.singleShot(0, lambda: self.handle_browser_closed(username))

            threading.Thread(target=run_close, daemon=True).start()
        except Exception as e:
            self.browser_signals.error.emit(f"关闭浏览器失败: {str(e)}")
    
    def update_account(self):
        """更新账号（更新模式）"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._safe_open_browser("gengxin"))
            loop.close()
        threading.Thread(target=run, daemon=True).start()

    async def _safe_open_browser(self, zhixingmoshi="denglu"):
        """
        安全打开浏览器
        
        Args:
            zhixingmoshi: 执行模式 ("denglu" 或 "gengxin")
        """
        selected_items = self.account_table.selectedItems()
        if not selected_items:
            self.browser_signals.error.emit("请选择要查看的账号")
            return
        
        row = selected_items[0].row()
        username = self.account_table.item(row, 2).text()  # 用户名在第2列
        password = self.account_table.item(row, 3).text()  # 密码在第3列
        proxy = self.account_table.item(row, 10).text()  # 代理IP在第10列

        # 确保只允许每个账号同时打开一个浏览器实例
        if username in self.active_browser_sessions and self.active_browser_sessions[username]['thread'].is_alive():
            self.browser_signals.info.emit(f"账号 {username} 的浏览器已在运行。")
            return

        cache_path = self.config.get('browser_cache_path', '')
        if not cache_path:
            self.browser_signals.error.emit("请先在设置中配置浏览器缓存路径")
            return
        
        account_dir = Path(cache_path) / username
        # 检查必要的配置
        browser_path = self.config.get('browser_path', '')
        if not browser_path:
            self.browser_signals.error.emit("请先在设置中配置浏览器路径")
            return
        
        # 检查指纹数据
        from utils import get_account_fingerprint
        fingerprint = get_account_fingerprint(username)
        if not fingerprint:
            self.browser_signals.error.emit("该账号未保存指纹数据，请先保存指纹数据")
            return
        
        # 创建浏览器配置
        peizhi = LiulanqiPeizhi(
            zhanghao=username,
            mima=password,  # 添加密码字段
            daili=proxy if proxy else None,
            wangzhi=DEFAULT_URL,
            huanchunlujing=str(account_dir),
            chrome_path=browser_path,
            fingerprint=fingerprint
        )
        
        # 创建任务流程控制器
        liucheng = RenwuLiucheng(self.data_manager, self.browser_signals)
        
        logger.info(f"正在启动浏览器流程 - 用户: {username}, 模式: {zhixingmoshi}")
        # 使用新的流程系统
        try:
            # 执行浏览器流程
            result = await liucheng.qidong_liulanqi_liucheng(peizhi, zhixingmoshi)
            
            if result["success"]:
                self.browser_signals.info.emit(f"浏览器流程执行成功: {result['message']}")
                logger.info(f"浏览器流程执行成功 - 用户: {username}, 结果: {result}")
                
                # 如果是更新模式，显示更详细的结果并自动关闭浏览器
                if zhixingmoshi == "gengxin":
                    if result.get("user_info"):
                        user_info = result["user_info"]
                        self.browser_signals.info.emit(
                            f"账号信息已更新: {user_info.get('name', '未知')} "
                            f"(ID: {user_info.get('id', '未知')}) "
                            f"状态: {result['login_status']}"
                        )
                    # 更新模式完成后自动关闭浏览器
                    await liucheng.guanbi_liulanqi()
                    QTimer.singleShot(0, lambda: self.handle_browser_closed(username))
                else:
                    # 登录模式：保持浏览器打开，记录会话
                    stop_event = threading.Event()
                    self.active_browser_sessions[username] = {
                        'thread': threading.current_thread(),
                        'stop_event': stop_event,
                        'liulanqi': liucheng.liulanqi
                    }
                    
                    # 登录模式下不自动关闭浏览器，等待用户手动关闭
                    self.browser_signals.info.emit("登录模式：浏览器已启动，请手动关闭浏览器")
                    logger.info(f"登录模式：浏览器已启动，等待用户手动关闭 - 用户: {username}")
                    
                    # 登录模式下完全由用户手动控制浏览器关闭
                    # 不进行任何自动检测，让浏览器保持打开状态
                    logger.info(f"登录模式：浏览器已启动，完全由用户手动控制 - 用户: {username}")
                    
                    # 等待用户手动关闭浏览器（不进行任何检测）
                    try:
                        while not stop_event.is_set():
                            # 只检查停止事件，不检查浏览器状态
                            await asyncio.sleep(5)  # 每5秒检查一次停止事件
                    except Exception as e:
                        logger.info(f"登录模式检测循环结束: {str(e)}")
                    
                    # 登录模式下不自动关闭浏览器，让用户手动控制
                    logger.info(f"登录模式：浏览器保持打开状态，由用户手动关闭 - 用户: {username}")
                    # 不执行 guanbi_liulanqi()，让浏览器保持打开状态
                    # 用户需要手动关闭浏览器窗口
            else:
                # 更新模式失败时也要自动关闭浏览器
                if zhixingmoshi == "gengxin":
                    self.browser_signals.error.emit(f"更新失败: {result['message']}")
                    logger.error(f"更新失败 - 用户: {username}, 错误: {result['message']}")
                    # 自动关闭浏览器
                    await liucheng.guanbi_liulanqi()
                    QTimer.singleShot(0, lambda: self.handle_browser_closed(username))
                else:
                    self.browser_signals.error.emit(f"浏览器流程执行失败: {result['message']}")
                    logger.error(f"浏览器流程执行失败 - 用户: {username}, 错误: {result['message']}")
                
        except Exception as e:
            error_msg = f"浏览器流程执行异常 - 用户: {username}, 错误: {str(e)}"
            logger.error(error_msg)
            self.browser_signals.error.emit(error_msg)
            
            # 确保清理资源
            try:
                # 只有在更新模式下才自动关闭浏览器
                if zhixingmoshi == "gengxin":
                    await liucheng.guanbi_liulanqi()
                    QTimer.singleShot(0, lambda: self.handle_browser_closed(username))
                else:
                    # 登录模式下异常时不自动关闭浏览器，让用户手动处理
                    self.browser_signals.info.emit("登录模式异常：浏览器保持打开状态，请手动关闭")
                    logger.info(f"登录模式异常：浏览器保持打开状态 - 用户: {username}")
            except:
                pass

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
            logger.info(f"开始处理浏览器关闭事件 - 用户: {username}")
            # 从活动会话中移除
            if username in self.active_browser_sessions:
                del self.active_browser_sessions[username]
                logger.info(f"已从活动会话中移除浏览器 - 用户: {username}")
            else:
                logger.info(f"浏览器不在活动会话中 - 用户: {username}")
            
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
            specific_movies = self.data_manager.load_movies('specific')
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
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 加载随机电影数据
            random_movies = self.data_manager.load_movies('random')
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
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 加载指定内容数据
            specific_contents = self.data_manager.load_contents('specific')
            if specific_contents is not None:
                self.content_specific_table.setRowCount(len(specific_contents))
                for i, content in enumerate(specific_contents):
                    self.content_specific_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.content_specific_table.setItem(i, 1, QTableWidgetItem(str(content)))
                    # 设置单元格居中对齐
                    for col in range(2):
                        item = self.content_specific_table.item(i, col)
                        if item:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 加载随机内容数据
            random_contents = self.data_manager.load_contents('random')
            if random_contents is not None:
                self.content_random_table.setRowCount(len(random_contents))
                for i, content in enumerate(random_contents):
                    self.content_random_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.content_random_table.setItem(i, 1, QTableWidgetItem(str(content)))
                    # 设置单元格居中对齐
                    for col in range(2):
                        item = self.content_random_table.item(i, col)
                        if item:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
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


    

    

    

    

    

    

    
    def clear_all_movies(self):
        """清空所有电影"""
        clear_all_movies_handler(self)
    
    def clear_all_contents(self):
        """清空所有内容"""
        clear_all_contents_handler(self)
    
    def clear_specific_movies(self):
        """清空指定电影"""
        clear_specific_movies_handler(self)
    
    def clear_random_movies(self):
        """清空随机电影"""
        clear_random_movies_handler(self)
    
    def clear_specific_contents(self):
        """清空指定内容"""
        clear_specific_contents_handler(self)
    
    def clear_random_contents(self):
        """清空随机内容"""
        clear_random_contents_handler(self)
    
    def on_run_start_clicked(self):
        """运行开始点击"""
        on_run_start_clicked_handler(self)
    
    def add_proxy(self):
        """添加代理"""
        add_proxy_handler(self)

    def remove_proxy(self):
        """删除代理"""
        remove_proxy_handler(self)

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
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

    
    elif platform.system() == "Windows":  # Windows
        # Qt 5.14+ 中已弃用 AA_EnableHighDpiScaling 和 AA_UseHighDpiPixmaps
        # 新版本Qt会自动处理高DPI缩放，无需手动设置这些属性
        pass
    
    window = AccountManagerWindow()
    window.show()
    sys.exit(app.exec())