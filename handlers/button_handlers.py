"""
按钮事件处理模块
"""
import sys
import os
import platform
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QApplication, QTableWidgetItem
from PySide6.QtCore import Qt, QThread, Signal
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入项目模块
from data_manager import DataManager
from config import DATA_DIR as quan_shujuwenjianjia

# 配置日志
logger = logging.getLogger(__name__)

def add_account_handler(window):
    """添加账号处理函数"""
    from .main_account_dialog import MainAccountDialog
    dialog = MainAccountDialog(window)
    dialog.setWindowTitle("添加账号")
    
    if dialog.exec() == QDialog.Accepted:
        account_data = dialog.get_data()
        if account_data:
            # 检查用户名是否已存在
            existing_accounts = window.data_manager.get_accounts()
            if any(account[1] == account_data['username'] for account in existing_accounts):
                QMessageBox.warning(window, "警告", f"用户名 {account_data['username']} 已存在")
                return
            
            # 生成指纹
            try:
                from liulanqimokuai.fingerprint_manager import FingerprintGenerator
                fingerprint_generator = FingerprintGenerator()
                fingerprint = fingerprint_generator.generate_random_fingerprint()
                account_data['fingerprint'] = fingerprint
            except Exception as e:
                logger.error(f"生成指纹失败: {str(e)}")
                QMessageBox.warning(window, "警告", "指纹生成失败")
                return
            
            # 保存账号
            if window.data_manager.add_account(account_data):
                # 保存指纹数据到账号目录
                try:
                    username = account_data['username']
                    # 统一使用默认的data目录保存指纹数据
                    default_data_dir = Path('data') / username
                    from liulanqimokuai.fingerprint_manager import FingerprintManager
                    FingerprintManager().save_fingerprint_to_file(fingerprint, str(default_data_dir))
                except Exception as e:
                    logger.error(f"保存指纹数据失败: {str(e)}")
                window.load_accounts()
                QMessageBox.information(window, "成功", "账号添加成功")
            else:
                QMessageBox.warning(window, "失败", "账号添加失败")

def edit_account_handler(window):
    """编辑账号处理函数"""
    selected_items = window.account_table.selectedItems()
    if not selected_items:
        QMessageBox.warning(window, "警告", "请先选择要编辑的账号")
        return
    
    row = selected_items[0].row()
    username = window.account_table.item(row, 2).text()  # 用户名列
    
    # 获取账号信息
    accounts = window.data_manager.get_accounts()
    account_info = None
    for account in accounts:
        if account[1] == username:
            account_info = account
            break
    
    if not account_info:
        QMessageBox.warning(window, "错误", "未找到选中的账号")
        return
    
    from .main_account_dialog import MainAccountDialog
    dialog = MainAccountDialog(window, {
        'username': account_info[1],
        'password': account_info[2],
        'ck': account_info[3],
        'nickname': account_info[4],
        'account_id': account_info[5],
        'note': account_info[11]
    })
    dialog.setWindowTitle("编辑账号")
    
    if dialog.exec() == QDialog.Accepted:
        updated_data = dialog.get_data()
        if updated_data:
            # 更新账号信息
            if window.data_manager.update_account(account_info[0], updated_data):
                window.load_accounts()
                QMessageBox.information(window, "成功", "账号更新成功")
            else:
                QMessageBox.warning(window, "失败", "账号更新失败")

def delete_account_handler(window):
    """删除账号处理函数"""
    # 获取所有勾选的账号行
    selected_rows = set()
    for row in range(window.account_table.rowCount()):
        checkbox_item = window.account_table.item(row, 0)
        if checkbox_item and checkbox_item.checkState() == Qt.Checked:
            selected_rows.add(row)
    
    if not selected_rows:
        QMessageBox.warning(window, "警告", "请先勾选要删除的账号")
        return
    
    # 确认删除
    reply = QMessageBox.question(
        window,
        "确认删除",
        f"确定要删除选中的 {len(selected_rows)} 个账号吗？",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        success_count = 0
        logger.info(f"开始删除 {len(selected_rows)} 个账号")
        for row in sorted(selected_rows, reverse=True):  # 逆序删除避免索引问题
            username = window.account_table.item(row, 2).text()
            account_id = window.account_table.item(row, 2).data(Qt.UserRole)  # 获取账号ID
            logger.info(f"正在删除账号: {username}, ID: {account_id}")
            
            # 删除账号相关的浏览器缓存数据
            cache_path = window.config.get('browser_cache_path', '')
            if cache_path:
                # 优先使用配置的缓存路径
                user_data_dir = Path(cache_path) / username
                if user_data_dir.exists():
                    try:
                        import shutil
                        shutil.rmtree(user_data_dir)
                        logger.info(f"已删除账号 {username} 的浏览器缓存数据 (配置路径)")
                    except Exception as e:
                        logger.error(f"删除账号 {username} 的浏览器缓存数据失败 (配置路径): {str(e)}")
            else:
                # 如果未配置缓存路径，尝试删除默认的data目录下的数据
                default_data_dir = Path('data') / username
                if default_data_dir.exists():
                    try:
                        import shutil
                        shutil.rmtree(default_data_dir)
                        logger.info(f"已删除账号 {username} 的浏览器缓存数据 (默认路径)")
                    except Exception as e:
                        logger.error(f"删除账号 {username} 的浏览器缓存数据失败 (默认路径): {str(e)}")
            
            # 从数据库删除账号
            if window.data_manager.delete_account(account_id):
                success_count += 1
                logger.info(f"成功从数据库删除账号: {username}")
            else:
                logger.error(f"从数据库删除账号失败: {username}")
        
        # 刷新账号列表
        window.load_accounts()
        
        # 显示结果
        if success_count > 0:
            QMessageBox.information(window, "成功", f"成功删除 {success_count} 个账号")
        else:
            QMessageBox.warning(window, "失败", "删除账号失败")

def add_proxy_handler(window):
    """添加代理处理函数"""
    selected_rows = set()
    for item in window.account_table.selectedItems():
        selected_rows.add(item.row())
    
    if not selected_rows:
        QMessageBox.warning(window, "警告", "请先选择要添加代理的账号")
        return
    
    # 创建自定义对话框
    dialog = QDialog(window)
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
                username = window.account_table.item(row, 2).text()  # 修正：用户名在第2列（索引2）
                # 获取当前账号的所有信息
                accounts = window.data_manager.get_accounts()
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
                            if window.data_manager.update_account(account[0], account_data):
                                success_count += 1
                            break
                        except Exception as e:
                            logger.error(f"处理账号 {username} 的数据时出错: {str(e)}")
                            continue
            
            # 刷新账号列表
            window.load_accounts()
            
            # 显示结果
            if success_count > 0:
                QMessageBox.information(window, "成功", f"成功为 {success_count} 个账号添加代理")
            else:
                QMessageBox.warning(window, "失败", "添加代理失败")

def remove_proxy_handler(window):
    """删除代理处理函数"""
    # 获取选中的账号
    selected_items = window.account_table.selectedItems()
    if not selected_items:
        QMessageBox.warning(window, "警告", "请选择要删除代理的账号")
        return
    
    # 获取选中行的账号数据
    row = selected_items[0].row()
    account_data = window.data_manager.load_accounts()
    if not account_data or row >= len(account_data):
        return
    
    # 检查是否已有代理
    if not account_data[row].get('proxy', ''):
        QMessageBox.information(window, "提示", "该账号未设置代理")
        return
    
    # 确认删除
    reply = QMessageBox.question(window, "确认删除", "确定要删除该账号的代理吗？")
    if reply == QMessageBox.Yes:
        # 清除代理信息
        account_data[row]['proxy'] = ''
        
        # 保存更新后的账号数据
        if window.data_manager.save_accounts(account_data):
            # 更新表格显示
            proxy_item = QTableWidgetItem('')
            window.account_table.setItem(row, 3, proxy_item)
            QMessageBox.information(window, "成功", "代理删除成功")
        else:
            QMessageBox.warning(window, "失败", "代理删除失败")

def clear_all_movies_handler(window):
    """清空所有电影处理函数"""
    reply = QMessageBox.question(window, "确认清空", "确定要清空所有电影数据吗？此操作不可恢复！")
    if reply == QMessageBox.Yes:
        # 清空指定电影
        if window.data_manager.save_movies([], 'specific'):
            window.movie_specific_table.setRowCount(0)
        
        # 清空随机电影
        if window.data_manager.save_movies([], 'random'):
            window.movie_random_table.setRowCount(0)
        
        QMessageBox.information(window, "成功", "所有电影数据已清空")

def clear_all_contents_handler(window):
    """清空所有内容处理函数"""
    reply = QMessageBox.question(window, "确认清空", "确定要清空所有内容数据吗？此操作不可恢复！")
    if reply == QMessageBox.Yes:
        # 清空指定内容
        if window.data_manager.save_contents([], 'specific'):
            window.content_specific_table.setRowCount(0)
        
        # 清空随机内容
        if window.data_manager.save_contents([], 'random'):
            window.content_random_table.setRowCount(0)
        
        QMessageBox.information(window, "成功", "所有内容数据已清空")

def clear_specific_movies_handler(window):
    """清空指定电影处理函数"""
    reply = QMessageBox.question(window, "确认清空", "确定要清空所有指定电影数据吗？此操作不可恢复！")
    if reply == QMessageBox.Yes:
        if window.data_manager.save_movies([], 'specific'):
            window.movie_specific_table.setRowCount(0)
            QMessageBox.information(window, "成功", "指定电影数据已清空")

def clear_random_movies_handler(window):
    """清空随机电影处理函数"""
    reply = QMessageBox.question(window, "确认清空", "确定要清空所有随机电影数据吗？此操作不可恢复！")
    if reply == QMessageBox.Yes:
        if window.data_manager.save_movies([], 'random'):
            window.movie_random_table.setRowCount(0)
            QMessageBox.information(window, "成功", "随机电影数据已清空")

def clear_specific_contents_handler(window):
    """清空指定内容处理函数"""
    reply = QMessageBox.question(window, "确认清空", "确定要清空所有指定内容数据吗？此操作不可恢复！")
    if reply == QMessageBox.Yes:
        if window.data_manager.save_contents([], 'specific'):
            window.content_specific_table.setRowCount(0)
            QMessageBox.information(window, "成功", "指定内容数据已清空")

def clear_random_contents_handler(window):
    """清空随机内容处理函数"""
    reply = QMessageBox.question(window, "确认清空", "确定要清空所有随机内容数据吗？此操作不可恢复！")
    if reply == QMessageBox.Yes:
        if window.data_manager.save_contents([], 'random'):
            window.content_random_table.setRowCount(0)
            QMessageBox.information(window, "成功", "随机内容数据已清空")

def on_run_start_clicked_handler(window):
    """运行开始点击处理函数"""
    QMessageBox.information(window, "提示", "运行功能后续实现")

def add_movie_handler(window, movie_type):
    """添加电影处理函数（支持多行输入）"""
    from PySide6.QtWidgets import QInputDialog, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QPlainTextEdit, QLabel, QComboBox, QCheckBox, QHBoxLayout
    
    dialog = QDialog(window)
    dialog.setWindowTitle(f"添加{movie_type}电影")
    dialog.setModal(True)
    dialog.resize(500, 500)
    
    layout = QFormLayout(dialog)
    
    # 添加说明标签
    info_label = QLabel("请输入电影信息，每行一个电影。\n格式：电影ID 或 电影ID,星级\n例如：\n1234567\n2345678,3星\n\n注意：如果勾选了统一星级，将忽略行内星级，使用下方选择的星级。")
    info_label.setWordWrap(True)
    layout.addRow(info_label)
    
    # 创建多行文本输入区域
    movie_edit = QPlainTextEdit()
    movie_edit.setPlaceholderText("请输入电影信息，每行一个电影...\n例如：\n1234567\n2345678,3星\n3456789,5星")
    movie_edit.setMinimumHeight(200)
    
    layout.addRow("电影列表:", movie_edit)
    
    # 添加统一星级设置
    rating_layout = QHBoxLayout()
    
    # 是否使用统一星级的复选框
    use_uniform_rating = QCheckBox("为所有电影设置统一星级")
    rating_layout.addWidget(use_uniform_rating)
    
    # 星级选择下拉框
    rating_combo = QComboBox()
    rating_combo.addItems(["不评星", "1星", "2星", "3星", "4星", "5星"])
    rating_combo.setEnabled(False)  # 初始状态禁用
    rating_layout.addWidget(rating_combo)
    
    # 连接复选框状态变化事件
    use_uniform_rating.stateChanged.connect(lambda state: rating_combo.setEnabled(state == 2))
    
    layout.addRow("统一星级:", rating_layout)
    
    # 添加按钮
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    
    if dialog.exec() == QDialog.Accepted:
        movie_text = movie_edit.toPlainText().strip()
        
        if not movie_text:
            QMessageBox.warning(window, "警告", "电影信息不能为空")
            return
        
        # 获取统一星级设置
        use_uniform = use_uniform_rating.isChecked()
        uniform_rating = None
        if use_uniform:
            rating_text = rating_combo.currentText()
            if rating_text != "不评星":
                # 直接使用星级文本
                uniform_rating = rating_text
        
        # 解析多行输入
        movie_lines = [line.strip() for line in movie_text.split('\n') if line.strip()]
        
        if not movie_lines:
            QMessageBox.warning(window, "警告", "请输入有效的电影信息")
            return
        
        # 获取现有电影数据
        movies = window.data_manager.load_movies(movie_type)
        if movies is None:
            movies = []
        
        # 解析和验证每行数据
        new_movies = []
        errors = []
        duplicates = []
        
        for i, line in enumerate(movie_lines, 1):
            try:
                # 解析电影ID和星级
                if ',' in line and not use_uniform:
                    # 只有在不使用统一星级时才解析行内星级
                    parts = line.split(',', 1)
                    movie_id = parts[0].strip()
                    rating_str = parts[1].strip()
                    
                    if rating_str:
                        # 验证星级格式
                        valid_ratings = ["1星", "2星", "3星", "4星", "5星"]
                        if rating_str not in valid_ratings:
                            errors.append(f"第{i}行：星级必须是1星-5星之一")
                            continue
                        rating = rating_str
                    else:
                        rating = None
                else:
                    # 使用统一星级或者只有电影ID
                    movie_id = line.split(',')[0].strip() if ',' in line else line.strip()
                    rating = uniform_rating
                
                if not movie_id:
                    errors.append(f"第{i}行：电影ID不能为空")
                    continue
                
                # 检查是否已存在
                existing_ids = [movie[0] for movie in movies] + [movie[0] for movie in new_movies]
                if movie_id in existing_ids:
                    duplicates.append(f"第{i}行：电影ID {movie_id} 已存在")
                    continue
                
                new_movies.append([movie_id, rating if rating is not None else ""])
                
            except Exception as e:
                errors.append(f"第{i}行：解析错误 - {str(e)}")
                continue
        
        # 显示错误和重复信息
        if errors or duplicates:
            error_msg = ""
            if errors:
                error_msg += "错误信息：\n" + "\n".join(errors)
            if duplicates:
                if error_msg:
                    error_msg += "\n\n"
                error_msg += "重复信息：\n" + "\n".join(duplicates)
            
            if new_movies:
                error_msg += f"\n\n将添加 {len(new_movies)} 个有效电影，是否继续？"
                reply = QMessageBox.question(window, "警告", error_msg, 
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            else:
                QMessageBox.warning(window, "错误", error_msg)
                return
        
        if not new_movies:
            QMessageBox.warning(window, "警告", "没有有效的电影数据可添加")
            return
        
        # 添加新电影
        movies.extend(new_movies)
        
        if window.data_manager.save_movies(movies, movie_type):
            window.load_movies_and_contents()
            QMessageBox.information(window, "成功", f"成功添加 {len(new_movies)} 个电影")
        else:
            QMessageBox.warning(window, "失败", "电影添加失败")

def delete_movie_handler(window):
    """删除选中的电影处理函数"""
    # 检查指定电影表格的选中项
    selected_specific = window.movie_specific_table.selectedItems()
    selected_random = window.movie_random_table.selectedItems()
    
    if not selected_specific and not selected_random:
        QMessageBox.warning(window, "警告", "请选择要删除的电影")
        return
    
    # 确定要删除的电影类型和行
    if selected_specific:
        table = window.movie_specific_table
        movie_type = "specific"
        row = selected_specific[0].row()
        movie_id = table.item(row, 1).text()
    else:
        table = window.movie_random_table
        movie_type = "random"
        row = selected_random[0].row()
        movie_id = table.item(row, 1).text()
    
    reply = QMessageBox.question(window, "确认删除", f"确定要删除电影 '{movie_id}' 吗？")
    if reply == QMessageBox.Yes:
        # 获取现有电影数据
        movies = window.data_manager.load_movies(movie_type)
        if movies is None:
            return
        
        # 删除选中的电影
        del movies[row]
        
        if window.data_manager.save_movies(movies, movie_type):
            window.load_movies_and_contents()
            QMessageBox.information(window, "成功", "电影删除成功")
        else:
            QMessageBox.warning(window, "失败", "电影删除失败")

def delete_movies_batch_handler(window):
    """批量删除电影处理函数"""
    # 检查指定电影表格的选中项
    selected_specific = window.movie_specific_table.selectedItems()
    selected_random = window.movie_random_table.selectedItems()
    
    if not selected_specific and not selected_random:
        QMessageBox.warning(window, "警告", "请选择要删除的电影")
        return
    
    # 确定要删除的电影类型和行
    if selected_specific:
        table = window.movie_specific_table
        movie_type = "specific"
        selected_rows = set()
        for item in selected_specific:
            selected_rows.add(item.row())
    else:
        table = window.movie_random_table
        movie_type = "random"
        selected_rows = set()
        for item in selected_random:
            selected_rows.add(item.row())
    
    if not selected_rows:
        return
    
    reply = QMessageBox.question(window, "确认删除", f"确定要删除选中的 {len(selected_rows)} 部电影吗？")
    if reply == QMessageBox.Yes:
        # 获取现有电影数据
        movies = window.data_manager.load_movies(movie_type)
        if movies is None:
            return
        
        # 按行号倒序删除，避免索引变化问题
        for row in sorted(selected_rows, reverse=True):
            if row < len(movies):
                del movies[row]
        
        if window.data_manager.save_movies(movies, movie_type):
            window.load_movies_and_contents()
            QMessageBox.information(window, "成功", f"成功删除 {len(selected_rows)} 部电影")
        else:
            QMessageBox.warning(window, "失败", "电影删除失败")

def add_content_handler(window, content_type):
    """添加内容处理函数（支持多行输入）"""
    from PySide6.QtWidgets import QInputDialog, QDialog, QFormLayout, QPlainTextEdit, QDialogButtonBox, QLabel
    
    dialog = QDialog(window)
    dialog.setWindowTitle(f"添加{content_type}内容")
    dialog.setModal(True)
    dialog.resize(500, 400)
    
    layout = QFormLayout(dialog)
    
    # 添加说明标签
    info_label = QLabel("请输入内容，每行一个内容。\n支持多行输入，每行将作为一个独立的内容项。")
    info_label.setWordWrap(True)
    layout.addRow(info_label)
    
    # 创建文本输入区域
    content_edit = QPlainTextEdit()
    content_edit.setPlaceholderText("请输入内容，每行一个...\n例如：\n这是第一条内容\n这是第二条内容\n这是第三条内容")
    content_edit.setMinimumHeight(250)
    
    layout.addRow("内容列表:", content_edit)
    
    # 添加按钮
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    
    if dialog.exec() == QDialog.Accepted:
        content_text = content_edit.toPlainText().strip()
        
        if not content_text:
            QMessageBox.warning(window, "警告", "内容不能为空")
            return
        
        # 解析多行输入
        content_lines = [line.strip() for line in content_text.split('\n') if line.strip()]
        
        if not content_lines:
            QMessageBox.warning(window, "警告", "请输入有效的内容")
            return
        
        # 获取现有内容数据
        contents = window.data_manager.load_contents(content_type)
        if contents is None:
            contents = []
        
        # 检查重复和验证
        new_contents = []
        duplicates = []
        empty_lines = []
        
        for i, line in enumerate(content_lines, 1):
            if not line:
                empty_lines.append(f"第{i}行：内容为空")
                continue
            
            # 检查是否已存在
            if line in contents or line in new_contents:
                duplicates.append(f"第{i}行：内容 '{line[:20]}...' 已存在" if len(line) > 20 else f"第{i}行：内容 '{line}' 已存在")
                continue
            
            new_contents.append(line)
        
        # 显示重复和空行信息
        if duplicates or empty_lines:
            error_msg = ""
            if empty_lines:
                error_msg += "空行信息：\n" + "\n".join(empty_lines)
            if duplicates:
                if error_msg:
                    error_msg += "\n\n"
                error_msg += "重复信息：\n" + "\n".join(duplicates)
            
            if new_contents:
                error_msg += f"\n\n将添加 {len(new_contents)} 个有效内容，是否继续？"
                reply = QMessageBox.question(window, "警告", error_msg, 
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            else:
                QMessageBox.warning(window, "错误", error_msg)
                return
        
        if not new_contents:
            QMessageBox.warning(window, "警告", "没有有效的内容可添加")
            return
        
        # 添加新内容
        contents.extend(new_contents)
        
        if window.data_manager.save_contents(contents, content_type):
            window.load_movies_and_contents()
            QMessageBox.information(window, "成功", f"成功添加 {len(new_contents)} 个内容")
        else:
            QMessageBox.warning(window, "失败", "内容添加失败")

def delete_content_handler(window):
    """删除选中的内容处理函数"""
    # 检查指定内容表格的选中项
    selected_specific = window.content_specific_table.selectedItems()
    selected_random = window.content_random_table.selectedItems()
    
    if not selected_specific and not selected_random:
        QMessageBox.warning(window, "警告", "请选择要删除的内容")
        return
    
    # 确定要删除的内容类型和行
    if selected_specific:
        table = window.content_specific_table
        content_type = "specific"
        row = selected_specific[0].row()
        content = table.item(row, 1).text()
    else:
        table = window.content_random_table
        content_type = "random"
        row = selected_random[0].row()
        content = table.item(row, 1).text()
    
    reply = QMessageBox.question(window, "确认删除", f"确定要删除该内容吗？")
    if reply == QMessageBox.Yes:
        # 获取现有内容数据
        contents = window.data_manager.load_contents(content_type)
        if contents is None:
            return
        
        # 删除选中的内容
        del contents[row]
        
        if window.data_manager.save_contents(contents, content_type):
            window.load_movies_and_contents()
            QMessageBox.information(window, "成功", "内容删除成功")
        else:
            QMessageBox.warning(window, "失败", "内容删除失败")

def delete_contents_batch_handler(window):
    """批量删除内容处理函数"""
    # 检查指定内容表格的选中项
    selected_specific = window.content_specific_table.selectedItems()
    selected_random = window.content_random_table.selectedItems()
    
    if not selected_specific and not selected_random:
        QMessageBox.warning(window, "警告", "请选择要删除的内容")
        return
    
    # 确定要删除的内容类型和行
    if selected_specific:
        table = window.content_specific_table
        content_type = "specific"
        selected_rows = set()
        for item in selected_specific:
            selected_rows.add(item.row())
    else:
        table = window.content_random_table
        content_type = "random"
        selected_rows = set()
        for item in selected_random:
            selected_rows.add(item.row())
    
    if not selected_rows:
        return
    
    reply = QMessageBox.question(window, "确认删除", f"确定要删除选中的 {len(selected_rows)} 条内容吗？")
    if reply == QMessageBox.Yes:
        # 获取现有内容数据
        contents = window.data_manager.load_contents(content_type)
        if contents is None:
            return
        
        # 按行号倒序删除，避免索引变化问题
        for row in sorted(selected_rows, reverse=True):
            if row < len(contents):
                del contents[row]
        
        if window.data_manager.save_contents(contents, content_type):
            window.load_movies_and_contents()
            QMessageBox.information(window, "成功", f"成功删除 {len(selected_rows)} 条内容")
        else:
            QMessageBox.warning(window, "失败", "内容删除失败")

def update_movie_rating_handler(window):
    """更新电影星级处理函数"""
    from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox, QLabel
    
    # 检查指定电影表格的选中项
    selected_specific = window.movie_specific_table.selectedItems()
    selected_random = window.movie_random_table.selectedItems()
    
    if not selected_specific and not selected_random:
        QMessageBox.warning(window, "警告", "请选择要更新星级的电影")
        return
    
    # 确定要更新的电影类型和行
    if selected_specific:
        table = window.movie_specific_table
        movie_type = "specific"
        selected_rows = set()
        for item in selected_specific:
            selected_rows.add(item.row())
    else:
        table = window.movie_random_table
        movie_type = "random"
        selected_rows = set()
        for item in selected_random:
            selected_rows.add(item.row())
    
    if not selected_rows:
        return
    
    # 创建星级选择对话框
    dialog = QDialog(window)
    dialog.setWindowTitle("更新电影星级")
    dialog.setModal(True)
    dialog.resize(300, 150)
    
    layout = QFormLayout(dialog)
    
    # 添加说明标签
    info_label = QLabel(f"为选中的 {len(selected_rows)} 部电影设置新的星级：")
    info_label.setWordWrap(True)
    layout.addRow(info_label)
    
    # 星级选择下拉框
    rating_combo = QComboBox()
    rating_combo.addItems([
        "不评星", 
        "1星", 
        "2星", 
        "3星", 
        "4星", 
        "5星"
    ])
    layout.addRow("选择星级:", rating_combo)
    
    # 添加按钮
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    
    if dialog.exec() == QDialog.Accepted:
        # 获取选择的星级
        rating_text = rating_combo.currentText()
        
        if rating_text == "不评星":
            new_rating = ""
        else:
            # 直接使用星级文本
            new_rating = rating_text
        
        # 获取现有电影数据
        movies = window.data_manager.load_movies(movie_type)
        if movies is None:
            QMessageBox.warning(window, "错误", "无法加载电影数据")
            return
        
        # 更新选中电影的星级
        updated_count = 0
        for row in selected_rows:
            if row < len(movies):
                # 如果是元组，转换为列表
                if isinstance(movies[row], tuple):
                    movies[row] = list(movies[row])
                movies[row][1] = new_rating  # 星级在第二列（索引1）
                updated_count += 1
        
        # 保存更新后的数据
        if window.data_manager.save_movies(movies, movie_type):
            window.load_movies_and_contents()
            rating_display = new_rating if new_rating else "无评星"
            QMessageBox.information(window, "成功", f"成功更新 {updated_count} 部电影的星级为：{rating_display}")
        else:
            QMessageBox.warning(window, "失败", "星级更新失败")