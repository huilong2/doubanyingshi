"""
账号对话框模块
统一的账号编辑对话框实现
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QComboBox, QPushButton, QFormLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView

from .base_dialog import BaseDialog
from data_manager import DataManager
from utils import show_fingerprint_dialog


class AccountDialog(BaseDialog):
    """统一的账号编辑对话框"""
    
    def __init__(self, parent=None, account_data=None):
        """
        初始化账号对话框
        
        Args:
            parent: 父窗口
            account_data: 账号数据字典，如果为None则为添加模式
        """
        self.data_manager = DataManager()
        self.account_data = account_data or {}
        title = "编辑账号" if account_data else "添加账号"
        super().__init__(parent, title, 450, 500)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 创建输入控件
        self._create_form_widgets()
        
        # 添加表单项
        self._add_form_rows(form_layout)
        
        layout.addLayout(form_layout)
        
        # 如果是编辑模式，添加"查看指纹数据"按钮
        if self.account_data:
            self._add_fingerprint_button(layout)
        
        # 添加按钮
        self._add_buttons(layout)
        
        # 加载数据
        if self.account_data:
            self.load_account_data(self.account_data)
    
    def _create_form_widgets(self):
        """创建表单控件"""
        # 基本信息
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.ck_edit = QLineEdit()
        self.nickname_edit = QLineEdit()
        self.account_id_edit = QLineEdit()
        
        # 状态信息
        self.login_status_combo = QComboBox()
        self.login_status_combo.addItems(["未登录", "已登录", "登录失败"])
        
        self.running_status_combo = QComboBox()
        self.running_status_combo.addItems(["空闲", "运行中", "已完成", "错误"])
        
        # 其他信息
        self.homepage_edit = QLineEdit()
        self.login_time_edit = QLineEdit()
        self.proxy_edit = QLineEdit()
        
        # 分组下拉框
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)  # 允许编辑以添加新分组
        try:
            groups = self.data_manager.get_groups()
            self.group_combo.addItems(groups)
        except Exception:
            self.group_combo.addItems(["默认分组"])
        
        # 备注
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(80)
    
    def _add_form_rows(self, form_layout):
        """添加表单行"""
        form_layout.addRow("用户名*:", self.username_edit)
        form_layout.addRow("密码*:", self.password_edit)
        form_layout.addRow("Cookie:", self.ck_edit)
        form_layout.addRow("昵称:", self.nickname_edit)
        form_layout.addRow("账号ID:", self.account_id_edit)
        form_layout.addRow("登录状态:", self.login_status_combo)
        form_layout.addRow("主页地址:", self.homepage_edit)
        form_layout.addRow("登录时间:", self.login_time_edit)
        form_layout.addRow("代理IP:", self.proxy_edit)
        form_layout.addRow("运行状态:", self.running_status_combo)
        form_layout.addRow("分组:", self.group_combo)
        form_layout.addRow("备注:", self.note_edit)
    
    def _add_fingerprint_button(self, layout):
        """添加查看指纹数据按钮"""
        fingerprint_layout = QHBoxLayout()
        fingerprint_layout.setSpacing(10)
        
        fingerprint_btn = QPushButton("查看指纹数据")
        fingerprint_btn.clicked.connect(self.show_fingerprint_data)
        
        fingerprint_layout.addWidget(fingerprint_btn)
        fingerprint_layout.addStretch()
        layout.addLayout(fingerprint_layout)
    
    def _add_buttons(self, layout):
        """添加确认和取消按钮"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def load_account_data(self, data):
        """
        加载账号数据到界面
        
        Args:
            data: 账号数据字典
        """
        self.username_edit.setText(data.get('username', ''))
        self.password_edit.setText(data.get('password', ''))
        self.ck_edit.setText(data.get('ck', ''))
        self.nickname_edit.setText(data.get('nickname', ''))
        self.account_id_edit.setText(data.get('account_id', ''))
        
        # 设置下拉框选项
        login_status = data.get('login_status', '未登录')
        index = self.login_status_combo.findText(login_status)
        if index >= 0:
            self.login_status_combo.setCurrentIndex(index)
        
        running_status = data.get('running_status', '空闲')
        index = self.running_status_combo.findText(running_status)
        if index >= 0:
            self.running_status_combo.setCurrentIndex(index)
        
        self.homepage_edit.setText(data.get('homepage', ''))
        self.login_time_edit.setText(data.get('login_time', ''))
        self.proxy_edit.setText(data.get('proxy', ''))
        
        # 设置分组
        group_name = data.get('group_name', '')
        if group_name:
            index = self.group_combo.findText(group_name)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)
            else:
                self.group_combo.setCurrentText(group_name)
        
        self.note_edit.setPlainText(data.get('note', ''))
    
    def show_fingerprint_data(self):
        """显示指纹数据"""
        username = self.username_edit.text().strip()
        if not username:
            QMessageBox.warning(self, "提示", "请先输入用户名")
            return
        
        try:
            show_fingerprint_dialog(self, username)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示指纹数据失败: {str(e)}")
    
    def get_data(self):
        """
        获取账号数据
        
        Returns:
            dict: 账号数据字典，包含所有字段
        """
        return {
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text().strip(),
            'ck': self.ck_edit.text().strip(),
            'nickname': self.nickname_edit.text().strip(),
            'account_id': self.account_id_edit.text().strip(),
            'login_status': self.login_status_combo.currentText(),
            'homepage': self.homepage_edit.text().strip(),
            'login_time': self.login_time_edit.text().strip(),
            'proxy': self.proxy_edit.text().strip(),
            'running_status': self.running_status_combo.currentText(),
            'note': self.note_edit.toPlainText().strip(),
            'group_name': self.group_combo.currentText().strip() or '默认分组'
        }
    
    def validate_data(self):
        """
        验证输入数据
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username:
            return False, "用户名不能为空"
        
        if not password:
            return False, "密码不能为空"
        
        return True, ""
    
    def accept(self):
        """重写accept方法，添加数据验证"""
        valid, error_msg = self.validate_data()
        if not valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        super().accept()


class GroupDialog(BaseDialog):
    """分组编辑对话框"""
    
    def __init__(self, parent=None, group_name=None, mode="add"):
        """
        初始化分组对话框
        
        Args:
            parent: 父窗口
            group_name: 分组名称
            mode: 模式，"add"为添加，"edit"为编辑
        """
        self.group_name = group_name
        self.mode = mode
        title = "添加分组" if mode == "add" else "编辑分组"
        super().__init__(parent, title, 300, 150)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 分组名称输入
        name_layout = QHBoxLayout()
        name_layout.setSpacing(10)
        
        label = QLabel("分组名称:")
        self.name_edit = QLineEdit(self.group_name or '')
        
        name_layout.addWidget(label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def get_data(self):
        """获取分组名称"""
        return self.name_edit.text().strip()
    
    def validate_data(self):
        """验证输入数据"""
        name = self.name_edit.text().strip()
        if not name:
            return False, "分组名称不能为空"
        return True, ""
    
    def accept(self):
        """重写accept方法，添加数据验证"""
        valid, error_msg = self.validate_data()
        if not valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        super().accept()