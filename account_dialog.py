import sys
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QFormLayout, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

class AccountDialog(QDialog):
    """账号编辑对话框"""
    
    def __init__(self, parent=None, account_data=None):
        super().__init__(parent)
        self.account_data = account_data
        self.setWindowTitle("编辑账号" if account_data else "添加账号")
        self.resize(400, 500)
        
        self.init_ui()
        
        if account_data:
            self.load_account_data(account_data)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 账号信息
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.ck_edit = QLineEdit()
        self.nickname_edit = QLineEdit()
        self.account_id_edit = QLineEdit()
        self.login_status_combo = QComboBox()
        self.login_status_combo.addItems(["未登录", "已登录", "登录失败"])
        self.homepage_edit = QLineEdit()
        self.login_time_edit = QLineEdit()
        self.proxy_edit = QLineEdit()
        self.running_status_combo = QComboBox()
        self.running_status_combo.addItems(["空闲", "运行中", "已完成", "错误"])
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(60)
        self.group_edit = QLineEdit()
        
        # 添加表单项
        form_layout.addRow("用户名:", self.username_edit)
        form_layout.addRow("密码:", self.password_edit)
        form_layout.addRow("Cookie:", self.ck_edit)
        form_layout.addRow("昵称:", self.nickname_edit)
        form_layout.addRow("账号ID:", self.account_id_edit)
        form_layout.addRow("登录状态:", self.login_status_combo)
        form_layout.addRow("主页地址:", self.homepage_edit)
        form_layout.addRow("登录时间:", self.login_time_edit)
        form_layout.addRow("代理IP:", self.proxy_edit)
        form_layout.addRow("运行状态:", self.running_status_combo)
        form_layout.addRow("备注:", self.note_edit)
        form_layout.addRow("分组:", self.group_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_account_data(self, data):
        """加载账号数据"""
        self.username_edit.setText(data.get('username', ''))
        self.password_edit.setText(data.get('password', ''))
        self.ck_edit.setText(data.get('ck', ''))
        self.nickname_edit.setText(data.get('nickname', ''))
        self.account_id_edit.setText(data.get('account_id', ''))
        
        login_status = data.get('login_status', '未登录')
        index = self.login_status_combo.findText(login_status)
        if index >= 0:
            self.login_status_combo.setCurrentIndex(index)
        
        self.homepage_edit.setText(data.get('homepage', ''))
        self.login_time_edit.setText(data.get('login_time', ''))
        self.proxy_edit.setText(data.get('proxy', ''))
        
        running_status = data.get('running_status', '空闲')
        index = self.running_status_combo.findText(running_status)
        if index >= 0:
            self.running_status_combo.setCurrentIndex(index)
        
        self.note_edit.setPlainText(data.get('note', ''))
        self.group_edit.setText(data.get('group_name', ''))
    
    def get_data(self):
        """获取账号数据"""
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
            'group_name': self.group_edit.text().strip()
        }