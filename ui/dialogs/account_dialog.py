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
        super().__init__(parent, title, 400, 300)
    
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
        
        # 备注
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(80)
    
    def _add_form_rows(self, form_layout):
        """添加表单行"""
        form_layout.addRow("用户名*:", self.username_edit)
        form_layout.addRow("密码*:", self.password_edit)
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
        # 保存原始数据，用于编辑时保留未显示的字段
        self.original_data = data.copy()
        
        # 只加载显示的字段
        self.username_edit.setText(data.get('username', ''))
        self.password_edit.setText(data.get('password', ''))
        self.note_edit.setPlainText(data.get('note', ''))
    
    def show_fingerprint_data(self):
        """显示指纹数据"""
        # 获取账号ID（如果存在）
        account_id = None
        if hasattr(self, 'original_data') and self.original_data:
            # 使用账号的id字段而不是account_id字段
            account_id = self.original_data.get('id')
            # 确保account_id是整数类型
            if account_id is not None:
                try:
                    account_id = int(account_id)
                except (ValueError, TypeError):
                    account_id = None
        
        if account_id is None:
            QMessageBox.warning(self, "提示", "账号ID无效")
            return
        
        try:
            show_fingerprint_dialog(self, account_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示指纹数据失败: {str(e)}")
    
    def get_data(self):
        """
        获取账号数据
        
        Returns:
            dict: 账号数据字典，包含所有字段
        """
        # 基础数据（用户输入的字段）
        data = {
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text().strip(),
            'note': self.note_edit.toPlainText().strip()
        }
        
        # 如果是编辑模式，保留原始数据中的其他字段
        if hasattr(self, 'original_data') and self.original_data:
            # 保留未显示的字段
            for key in ['ck', 'nickname', 'account_id', 'login_status', 
                       'homepage', 'login_time', 'proxy', 'running_status']:
                data[key] = self.original_data.get(key, '')
        else:
            # 添加模式，设置默认值
            data.update({
                'ck': '',
                'nickname': '',
                'account_id': '',
                'login_status': '未登录',
                'homepage': '',
                'login_time': '',
                'proxy': '',
                'running_status': '空闲'
            })
        
        return data
    
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


# GroupDialog类已删除