from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

class AddEditDataDialog(QDialog):
    """添加/编辑数据对话框"""
    
    def __init__(self, parent=None, table_name_cn="", table_name_en="", mode="add", data=None):
        super().__init__(parent)
        self.table_name_cn = table_name_cn
        self.table_name_en = table_name_en
        self.mode = mode  # "add" 或 "edit"
        self.data = data or []
        
        self.init_ui()
        
        # 如果是编辑模式，填充数据
        if mode == "edit" and data:
            self.fill_data(data)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{self.mode == 'add' and '添加' or '编辑'}{self.table_name_cn}数据")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 根据表名创建不同的输入字段
        if self.table_name_en in ["dianying", "dianshi"]:
            self.id_edit = QLineEdit()
            self.name_edit = QLineEdit()
            self.year_edit = QLineEdit()
            
            form_layout.addRow(QLabel(f"{self.table_name_cn}ID:"), self.id_edit)
            form_layout.addRow(QLabel("名称:"), self.name_edit)
            form_layout.addRow(QLabel("年代:"), self.year_edit)
            
        elif self.table_name_en in ["yinyue", "dushu"]:
            self.id_edit = QLineEdit()
            self.name_edit = QLineEdit()
            self.year_edit = QLineEdit()
            
            form_layout.addRow(QLabel(f"{self.table_name_cn}ID:"), self.id_edit)
            form_layout.addRow(QLabel("名称:"), self.name_edit)
            form_layout.addRow(QLabel("年代:"), self.year_edit)
        
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def fill_data(self, data):
        """填充数据用于编辑"""
        if len(data) >= 3:
            self.id_edit.setText(data[1])  # 第2列是ID
            self.name_edit.setText(data[2])  # 第3列是名称
            self.year_edit.setText(data[3])  # 第4列是年代
    
    def get_data(self):
        """获取输入的数据"""
        # 验证输入
        if not self.id_edit.text().strip():
            return None
            
        return (
            self.id_edit.text().strip(),
            self.name_edit.text().strip(),
            self.year_edit.text().strip()
        )