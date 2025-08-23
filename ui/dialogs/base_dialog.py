"""
基础对话框类模块
提供统一的对话框基类和样式
"""

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from styles import DIALOG_STYLE


class BaseDialog(QDialog):
    """基础对话框类"""
    
    def __init__(self, parent=None, title="", min_width=350, min_height=180):
        """
        初始化基础对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            min_width: 最小宽度
            min_height: 最小高度
        """
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