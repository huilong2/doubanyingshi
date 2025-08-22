#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一样式管理模块 - Fluent Design 风格
整合所有UI样式，提供一致的视觉体验
"""

# ==================== 颜色定义 ====================

FLUENT_COLORS = {
    # 主色调
    'primary': '#0d6efd',           # 主蓝色
    'primary_hover': '#0b5ed7',     # 主蓝色悬停
    'primary_pressed': '#0a58ca',   # 主蓝色按下
    'primary_dark': '#084298',      # 主蓝色深色
    
    # 背景色
    'background': '#f8f9fa',        # 主背景
    'background_gradient_start': '#f8f9fa',
    'background_gradient_end': '#e9ecef',
    'surface': '#ffffff',           # 表面背景
    'surface_hover': '#f8f9ff',     # 表面悬停
    
    # 文字颜色
    'text_primary': '#212529',      # 主要文字
    'text_secondary': '#495057',    # 次要文字
    'text_muted': '#6c757d',        # 静音文字
    'text_disabled': '#adb5bd',     # 禁用文字
    'text_white': '#ffffff',        # 白色文字
    
    # 边框颜色
    'border': '#dee2e6',            # 主边框
    'border_light': '#e9ecef',      # 浅边框
    'border_focus': '#0d6efd',      # 焦点边框
    'border_hover': '#adb5bd',      # 悬停边框
    
    # 状态颜色
    'success': '#198754',           # 成功绿色
    'warning': '#ffc107',           # 警告黄色
    'danger': '#dc3545',            # 危险红色
    'info': '#0dcaf0',              # 信息青色
    
    # 选择和高亮
    'selection': '#e7f3ff',         # 选择背景
    'selection_text': '#0d6efd',    # 选择文字
    'hover': '#f8f9ff',             # 悬停背景
    'alternate': '#f8f9fa',         # 交替行背景
    
    # 阴影
    'shadow': 'rgba(0, 0, 0, 0.1)', # 阴影颜色
}

# ==================== 布局常量 ====================

LAYOUT = {
    'spacing': {
        'xs': 5,    # 极小间距
        'sm': 10,   # 小间距
        'md': 15,   # 中等间距
        'lg': 20,   # 大间距
        'xl': 25,   # 超大间距
    },
    'padding': {
        'xs': 5,    # 极小内边距
        'sm': 8,    # 小内边距
        'md': 12,   # 中等内边距
        'lg': 16,   # 大内边距
        'xl': 20,   # 超大内边距
    },
    'border_radius': {
        'sm': 4,    # 小圆角
        'md': 6,    # 中等圆角
        'lg': 8,    # 大圆角
        'xl': 12,   # 超大圆角
    },
    'font_size': {
        'xs': 12,   # 极小字体
        'sm': 13,   # 小字体
        'md': 14,   # 中等字体
        'lg': 16,   # 大字体
        'xl': 18,   # 超大字体
    }
}

# ==================== 主窗口样式 ====================

MAIN_WINDOW_STYLE = f"""
/* 主窗口样式 */
QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['background_gradient_start']}, 
        stop:1 {FLUENT_COLORS['background_gradient_end']});
    color: {FLUENT_COLORS['text_primary']};
}}
"""

# ==================== 标签页样式 ====================

TAB_WIDGET_STYLE = f"""
/* 标签页样式 */
QTabWidget::pane {{
    border: 1px solid {FLUENT_COLORS['border']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    background: {FLUENT_COLORS['surface']};
    margin-top: -1px;
}}

QTabBar::tab {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['background_gradient_start']}, 
        stop:1 {FLUENT_COLORS['background_gradient_end']});
    color: {FLUENT_COLORS['text_muted']};
    padding: {LAYOUT['padding']['md']}px {LAYOUT['padding']['xl']}px;
    margin-right: 2px;
    border-top-left-radius: {LAYOUT['border_radius']['lg']}px;
    border-top-right-radius: {LAYOUT['border_radius']['lg']}px;
    font-weight: 500;
    font-size: {LAYOUT['font_size']['md']}px;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['primary']};
    border-bottom: 3px solid {FLUENT_COLORS['primary']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['border_light']}, 
        stop:1 {FLUENT_COLORS['border']});
    color: {FLUENT_COLORS['text_secondary']};
}}
"""

# ==================== 分组框样式 ====================

GROUP_BOX_STYLE = f"""
QGroupBox {{
    font-weight: 600;
    font-size: {LAYOUT['font_size']['md']}px;
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['xl']}px;
    margin-top: {LAYOUT['spacing']['lg']}px;
    padding-top: {LAYOUT['padding']['lg']}px;
    color: {FLUENT_COLORS['text_secondary']};
    background: {FLUENT_COLORS['surface']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: {LAYOUT['padding']['lg']}px;
    padding: 0 {LAYOUT['padding']['md']}px 0 {LAYOUT['padding']['md']}px;
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['primary']};
}}
"""

# ==================== 按钮样式 ====================

BUTTON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary']}, 
        stop:1 {FLUENT_COLORS['primary_hover']});
    color: {FLUENT_COLORS['text_white']};
    border: none;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['md']}px;
    border-radius: {LAYOUT['border_radius']['md']}px;
    font-weight: 600;
    font-size: {LAYOUT['font_size']['sm']}px;
    min-width: 50px;
    min-height: 20px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary_hover']}, 
        stop:1 {FLUENT_COLORS['primary_pressed']});
    margin-top: -1px;
}}

QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary_pressed']}, 
        stop:1 {FLUENT_COLORS['primary_dark']});
}}

QPushButton:disabled {{
    background: {FLUENT_COLORS['text_muted']};
    color: {FLUENT_COLORS['text_disabled']};
}}
"""

# ==================== 输入框样式 ====================

INPUT_STYLE = f"""
QLineEdit {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['md']}px;
    font-size: {LAYOUT['font_size']['md']}px;
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['text_secondary']};
}}

QLineEdit:focus {{
    border: 2px solid {FLUENT_COLORS['border_focus']};
    background: {FLUENT_COLORS['surface_hover']};
}}

QLineEdit:hover {{
    border: 2px solid {FLUENT_COLORS['border_hover']};
}}
"""

# ==================== 文本编辑框样式 ====================

TEXT_EDIT_STYLE = f"""
QTextEdit {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    font-size: {LAYOUT['font_size']['md']}px;
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['text_secondary']};
    padding: {LAYOUT['padding']['sm']}px;
}}

QTextEdit:focus {{
    border: 2px solid {FLUENT_COLORS['border_focus']};
    background: {FLUENT_COLORS['surface_hover']};
}}
"""

# ==================== 表格样式 ====================

TABLE_STYLE = f"""
QTableWidget {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    font-size: {LAYOUT['font_size']['sm']}px;
    background: {FLUENT_COLORS['surface']};
    gridline-color: {FLUENT_COLORS['background_gradient_start']};
    selection-background-color: {FLUENT_COLORS['selection']};
    selection-color: {FLUENT_COLORS['selection_text']};
}}

QTableWidget::item {{
    padding: {LAYOUT['padding']['sm']}px;
    border-bottom: 1px solid {FLUENT_COLORS['background_gradient_start']};
}}

QTableWidget::item:selected {{
    background: {FLUENT_COLORS['selection']};
    color: {FLUENT_COLORS['selection_text']};
}}

QTableWidget::item:hover {{
    background: {FLUENT_COLORS['surface_hover']};
}}

QTableWidget::item:alternate {{
    background: {FLUENT_COLORS['alternate']};
}}

QTableWidget::item:selected:alternate {{
    background: {FLUENT_COLORS['selection']};
    color: {FLUENT_COLORS['selection_text']};
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['background_gradient_start']}, 
        stop:1 {FLUENT_COLORS['border_light']});
    color: {FLUENT_COLORS['text_secondary']};
    padding: {LAYOUT['padding']['md']}px {LAYOUT['padding']['sm']}px;
    border: none;
    border-bottom: 2px solid {FLUENT_COLORS['border']};
    font-weight: 600;
    font-size: {LAYOUT['font_size']['sm']}px;
}}

QHeaderView::section:hover {{
    background: {FLUENT_COLORS['border_light']};
}}
"""

# ==================== 下拉框样式 ====================

COMBO_BOX_STYLE = f"""
QComboBox {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['md']}px;
    font-size: {LAYOUT['font_size']['md']}px;
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['text_secondary']};
    min-width: 100px;
}}

QComboBox:focus {{
    border: 2px solid {FLUENT_COLORS['border_focus']};
    background: {FLUENT_COLORS['surface_hover']};
}}

QComboBox:hover {{
    border: 2px solid {FLUENT_COLORS['border_hover']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {FLUENT_COLORS['text_muted']};
    margin-right: {LAYOUT['padding']['sm']}px;
}}

QComboBox::down-arrow:hover {{
    border-top-color: {FLUENT_COLORS['primary']};
}}
"""

# ==================== 复选框样式 ====================

CHECKBOX_STYLE = f"""
QCheckBox {{
    font-size: {LAYOUT['font_size']['md']}px;
    color: {FLUENT_COLORS['text_secondary']};
    spacing: {LAYOUT['spacing']['sm']}px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['sm']}px;
    background: {FLUENT_COLORS['surface']};
}}

QCheckBox::indicator:checked {{
    background: {FLUENT_COLORS['primary']};
    border: 2px solid {FLUENT_COLORS['primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
}}

QCheckBox::indicator:hover {{
    border: 2px solid {FLUENT_COLORS['primary']};
}}
"""

# ==================== 标签样式 ====================

LABEL_STYLE = f"""
QLabel {{
    font-size: {LAYOUT['font_size']['md']}px;
    color: {FLUENT_COLORS['text_secondary']};
    font-weight: 500;
}}
"""

# ==================== 滚动条样式 ====================

SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: {FLUENT_COLORS['background_gradient_start']};
    width: 12px;
    border-radius: {LAYOUT['border_radius']['md']}px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {FLUENT_COLORS['text_disabled']};
    border-radius: {LAYOUT['border_radius']['md']}px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {FLUENT_COLORS['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {FLUENT_COLORS['background_gradient_start']};
    height: 12px;
    border-radius: {LAYOUT['border_radius']['md']}px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {FLUENT_COLORS['text_disabled']};
    border-radius: {LAYOUT['border_radius']['md']}px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {FLUENT_COLORS['text_muted']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""

# ==================== 进度条样式 ====================

PROGRESS_BAR_STYLE = f"""
QProgressBar {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    background: {FLUENT_COLORS['background_gradient_start']};
    text-align: center;
    font-weight: 600;
    color: {FLUENT_COLORS['text_secondary']};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary']}, 
        stop:1 {FLUENT_COLORS['primary_hover']});
    border-radius: {LAYOUT['border_radius']['md']}px;
}}
"""

# ==================== 对话框样式 ====================

DIALOG_STYLE = f"""
QDialog {{
    background: {FLUENT_COLORS['surface']};
    border-radius: {LAYOUT['border_radius']['xl']}px;
}}

QDialog QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary']}, 
        stop:1 {FLUENT_COLORS['primary_hover']});
    color: {FLUENT_COLORS['text_white']};
    border: none;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['lg']}px;
    border-radius: {LAYOUT['border_radius']['lg']}px;
    font-weight: 600;
    font-size: {LAYOUT['font_size']['md']}px;
    min-width: 50px;
    min-height: 20px;
}}

QDialog QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary_hover']}, 
        stop:1 {FLUENT_COLORS['primary_pressed']});
}}

QDialog QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary_pressed']}, 
        stop:1 {FLUENT_COLORS['primary_dark']});
}}

QDialog QLineEdit {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['md']}px;
    font-size: {LAYOUT['font_size']['md']}px;
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['text_secondary']};
}}

QDialog QLineEdit:focus {{
    border: 2px solid {FLUENT_COLORS['border_focus']};
    background: {FLUENT_COLORS['surface_hover']};
}}

QDialog QComboBox {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['md']}px;
    font-size: {LAYOUT['font_size']['md']}px;
    background: {FLUENT_COLORS['surface']};
    color: {FLUENT_COLORS['text_secondary']};
}}

QDialog QComboBox:focus {{
    border: 2px solid {FLUENT_COLORS['border_focus']};
    background: {FLUENT_COLORS['surface_hover']};
}}

QDialog QLabel {{
    font-size: {LAYOUT['font_size']['md']}px;
    color: {FLUENT_COLORS['text_secondary']};
    font-weight: 500;
}}
"""

# ==================== 指纹数据对话框样式 ====================

FINGERPRINT_DIALOG_STYLE = f"""
QDialog {{
    background: {FLUENT_COLORS['surface']};
    border-radius: {LAYOUT['border_radius']['xl']}px;
}}

QDialog QLabel {{
    font-size: {LAYOUT['font_size']['md']}px;
    color: {FLUENT_COLORS['text_secondary']};
    font-weight: 500;
}}

QDialog QTextEdit {{
    border: 2px solid {FLUENT_COLORS['border_light']};
    border-radius: {LAYOUT['border_radius']['lg']}px;
    font-size: {LAYOUT['font_size']['sm']}px;
    background: {FLUENT_COLORS['background_gradient_start']};
    color: {FLUENT_COLORS['text_secondary']};
    padding: {LAYOUT['padding']['sm']}px;
}}

QDialog QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary']}, 
        stop:1 {FLUENT_COLORS['primary_hover']});
    color: {FLUENT_COLORS['text_white']};
    border: none;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['lg']}px;
    border-radius: {LAYOUT['border_radius']['lg']}px;
    font-weight: 600;
    font-size: {LAYOUT['font_size']['md']}px;
    min-width: 80px;
}}

QDialog QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {FLUENT_COLORS['primary_hover']}, 
        stop:1 {FLUENT_COLORS['primary_pressed']});
}}
"""

# ==================== 消息框样式 ====================

MESSAGE_BOX_STYLE = f"""
QMessageBox {{
    background: {FLUENT_COLORS['surface']};
}}

QMessageBox QPushButton {{
    min-width: 80px;
    min-height: 30px;
}}
"""

# ==================== 文件对话框样式 ====================

FILE_DIALOG_STYLE = f"""
QFileDialog {{
    background: {FLUENT_COLORS['surface']};
}}
"""

# ==================== 工具提示样式 ====================

TOOLTIP_STYLE = f"""
QToolTip {{
    background: {FLUENT_COLORS['text_primary']};
    color: {FLUENT_COLORS['text_white']};
    border: none;
    border-radius: {LAYOUT['border_radius']['md']}px;
    padding: {LAYOUT['padding']['sm']}px {LAYOUT['padding']['md']}px;
    font-size: {LAYOUT['font_size']['xs']}px;
}}
"""

# ==================== 完整样式组合 ====================

def get_complete_fluent_style():
    """获取完整的 Fluent Design 样式"""
    return f"""
    {MAIN_WINDOW_STYLE}
    {TAB_WIDGET_STYLE}
    {GROUP_BOX_STYLE}
    {BUTTON_STYLE}
    {INPUT_STYLE}
    {TEXT_EDIT_STYLE}
    {TABLE_STYLE}
    {COMBO_BOX_STYLE}
    {CHECKBOX_STYLE}
    {LABEL_STYLE}
    {SCROLLBAR_STYLE}
    {PROGRESS_BAR_STYLE}
    {MESSAGE_BOX_STYLE}
    {FILE_DIALOG_STYLE}
    {TOOLTIP_STYLE}
    """

# ==================== 兼容性保持 ====================

# 保持与原有代码的兼容性
COLORS = FLUENT_COLORS  # 别名
COMMON_STYLE = MAIN_WINDOW_STYLE
EDITABLE_DELEGATE_STYLE = INPUT_STYLE
LOG_TEXT_STYLE = TEXT_EDIT_STYLE
TAB_STYLE = TAB_WIDGET_STYLE