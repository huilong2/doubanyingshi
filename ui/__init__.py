"""
UI模块
包含所有用户界面相关的类和组件
"""

# 导出主要的对话框类，方便外部使用
from .dialogs.base_dialog import BaseDialog
from .dialogs.account_dialog import AccountDialog

__all__ = ['BaseDialog', 'AccountDialog']