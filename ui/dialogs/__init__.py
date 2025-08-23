"""
对话框模块
包含各种对话框类
"""

from .base_dialog import BaseDialog
from .account_dialog import AccountDialog, GroupDialog

__all__ = ['BaseDialog', 'AccountDialog', 'GroupDialog']