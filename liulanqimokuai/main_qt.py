import sys
import os
import glob
import asyncio
import threading
from datetime import datetime

# 确保输出能够及时显示111
def print_and_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit, 
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QSplitter,
    QGroupBox,
    QTabWidget,
)

from playwright.async_api import async_playwright, Error
from browser_core import BrowserController


class EventSignals(QObject):
    event_received = Signal(str, dict)  # event_type, event_data


class QtBrowserApp(QWidget):
    def __init__(self):
        super().__init__()
        print("Initializing QtBrowserApp...")
        self.setWindowTitle("浏览器自动化工具 - PySide6")

        # Browser state
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Async loop in background thread
        self.loop = None
        self.loop_thread = None
        self.nav_lock = None

        # Controller 封装
        print_and_flush("Creating BrowserController...")
        self.controller = BrowserController()
        print_and_flush("BrowserController created")
        self.signals = EventSignals()
        self.signals.event_received.connect(self.on_event_received)

        print_and_flush("Building UI...")
        self._build_ui()
        print_and_flush("UI built")
        self.__init_event_handlers()
        self._wire_events()
        self._start_event_loop()

        # Auto search browser path
        print_and_flush("Searching for browser path...")
        self._auto_search_browser_path()
        print_and_flush("Browser path search completed")
        print_and_flush("QtBrowserApp initialization completed")

    def _build_ui(self):
        """构建主界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页控件
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        
        # 创建三个独立的标签页
        self._create_main_page_tab()
        self._create_settings_page_tab()
        self._create_network_page_tab()
        
        # 创建日志区域（在标签页外部）
        self._create_log_area(layout)
        
        # 新增：添加清空日志和清空网络表格按钮
        self._create_clear_buttons(layout)
        
        # 连接信号槽
        self._connect_signals()

    def _create_main_page_tab(self):
        """创建主页标签页"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # URL控制区域
        self._create_url_controls(main_layout)
        
        # 标签页管理
        self._create_tabs_table(main_layout)
        
        self.tabs.addTab(main_widget, "主页")
    
    def _create_settings_page_tab(self):
        """创建设置标签页"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # 浏览器控制区域
        self._create_browser_controls(settings_layout)
        
        # 账号和缓存控制区域
        self._create_account_controls(settings_layout)
        
        # 添加一些空白空间
        settings_layout.addStretch()
        
        self.tabs.addTab(settings_widget, "设置")
    
    def _create_network_page_tab(self):
        """创建网络标签页"""
        network_widget = QWidget()
        network_layout = QVBoxLayout(network_widget)
        
        # 网络监控内容
        self._create_network_monitoring(network_layout)
        
        self.tabs.addTab(network_widget, "网络")

    def _create_clear_buttons(self, layout):
        """新增：创建清空日志和网络表格按钮"""
        row = QHBoxLayout()
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_net_btn = QPushButton("清空网络表")
        row.addWidget(self.clear_log_btn)
        row.addWidget(self.clear_net_btn)
        layout.addLayout(row)

    def _create_url_controls(self, layout):
        """创建URL控制区域"""
        row = QHBoxLayout()
        row.addWidget(QLabel("网址:"))
        
        self.url_edit = QLineEdit()
        self.url_edit.setText("https://www.baidu.com")
        row.addWidget(self.url_edit, 1)
        
        self.goto_btn = QPushButton("跳转")
        self.goto_btn.setEnabled(False)
        row.addWidget(self.goto_btn)
        
        layout.addLayout(row)
    
    def _create_browser_controls(self, layout):
        """创建浏览器控制区域"""
        row = QHBoxLayout()
        row.addWidget(QLabel("浏览器路径:"))
        
        self.path_edit = QLineEdit()
        row.addWidget(self.path_edit, 1)
        
        self.search_btn = QPushButton("自动搜索")
        row.addWidget(self.search_btn)
        
        self.toggle_btn = QPushButton("打开浏览器")
        row.addWidget(self.toggle_btn)
        
        layout.addLayout(row)
    
    def _create_account_controls(self, layout):
        """创建账号和缓存控制区域"""
        row = QHBoxLayout()
        row.addWidget(QLabel("账号名:"))
        
        self.account_name_edit = QLineEdit()
        self.account_name_edit.setText("default")
        row.addWidget(self.account_name_edit, 1)
        
        row.addWidget(QLabel("缓存路径:"))
        self.cache_path_edit = QLineEdit()
        self.cache_path_edit.setText(os.path.join(os.getcwd(), "account_cache"))
        row.addWidget(self.cache_path_edit, 2)
        
        layout.addLayout(row)
    
    def _create_tabs_table(self, layout):
        """创建标签页管理表格"""
        self.tabs_table = QTableWidget(0, 1)
        self.tabs_table.setHorizontalHeaderLabels(["URL"])
        self.tabs_table.horizontalHeader().setStretchLastSection(True)
        self.tabs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabs_table, 1)
    
    def _create_network_monitoring(self, layout):
        """创建网络监控界面"""
        # 网络请求表格
        self.net_table = QTableWidget(0, 6)
        self.net_table.setHorizontalHeaderLabels(["时间", "阶段", "方法", "类型", "状态", "URL"])
        self.net_table.horizontalHeader().setStretchLastSection(True)
        self.net_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.net_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.net_table, 2)
        
        # 响应体显示区域
        self.net_body = QTextEdit()
        self.net_body.setReadOnly(True)
        layout.addWidget(self.net_body, 3)
    
    def _create_log_area(self, layout):
        """创建日志区域"""
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        layout.addWidget(self.log_edit, 1)
    
    def _connect_signals(self):
        """连接信号槽"""
        # 按钮信号
        self.goto_btn.clicked.connect(self.navigate_url)
        self.search_btn.clicked.connect(self._auto_search_browser_path)
        self.toggle_btn.clicked.connect(self.toggle_browser)
        
        # 表格信号
        self.tabs_table.cellDoubleClicked.connect(self.activate_selected_tab)
        self.tabs_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs_table.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.net_table.cellClicked.connect(self._on_net_row_clicked)

        # 新增：清空日志和网络表格按钮
        self.clear_log_btn.clicked.connect(self._clear_log)
        self.clear_net_btn.clicked.connect(self._clear_network_table)

    def _clear_log(self):
        self.log_edit.clear()

    def _clear_network_table(self):
        self.net_table.setRowCount(0)

    def _wire_events(self):
        """订阅所有需要的事件"""
        events_to_monitor = [
            'browser_launch', 'browser_close', 'browser_disconnected',
            'new_page', 'page_closed', 'url_change', 'page_load', 'popup',
            'request_start', 'request_finished', 'request_failed', 'resource_response',
            'error', 'navigation_end',
            'loading_state_change', 'document_ready', 'frame_navigated',
            'websocket', 'websocket_error', 'websocket_message',
            'response_start', 'response_end'
        ]
        
        for evt in events_to_monitor:
            self.controller.on(evt, lambda data, event_type=evt: self._emit_event(event_type, data))

    def _emit_event(self, event_type: str, data: dict):
        # Thread-safe: emit Qt signal to main thread
        self.signals.event_received.emit(event_type, data or {})

    def _start_event_loop(self):
        if self.loop is not None:
            return
        self.loop = asyncio.new_event_loop()
        def _run():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        self.loop_thread = threading.Thread(target=_run, daemon=True)
        self.loop_thread.start()

    def run_async(self, coro):
        if not self.loop:
            raise RuntimeError("事件循环未启动")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def _auto_search_browser_path(self):
        possible_paths = []
        if sys.platform == "win32":
            paths = [
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
            for p in paths:
                if os.path.exists(p):
                    possible_paths.append(p)
            for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:
                if os.path.exists(pf):
                    possible_paths.extend(glob.glob(f"{pf}\\Google\\Chrome\\Application\\chrome.exe"))
        elif sys.platform == "darwin":
            for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
                if os.path.exists(p):
                    possible_paths.append(p)
        else:
            for p in ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]:
                if os.path.exists(p):
                    possible_paths.append(p)

        if possible_paths:
            self.path_edit.setText(possible_paths[0])
            self._append_log("[提示] 已找到Chrome浏览器并填充路径")
        else:
            self._append_log("[警告] 未找到Chrome浏览器，请手动设置路径")

    # UI helpers
    def _show_error(self, msg: str):
        # 不弹窗，仅写入日志区
        self._append_log(f"[错误] {msg}")

    def _append_log(self, text: str):
        self.log_edit.append(text)
        try:
            self.log_edit.moveCursor(QTextCursor.End)
        except Exception:
            # 兜底方式
            cursor = self.log_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_edit.setTextCursor(cursor)

    def __init_event_handlers(self):
        """初始化事件处理器映射"""
        self._event_handlers = {
            'browser_launch': self._handle_browser_launch,
            'browser_close': self._handle_browser_close,
            'browser_disconnected': self._handle_browser_close,
            'new_page': self._handle_new_page,
            'page_closed': self._handle_page_closed,
            'url_change': self._handle_url_change,
            'page_load': self._handle_page_load,
            'request_start': self._handle_network_event,
            'resource_response': self._handle_network_event,
            'request_finished': self._handle_network_event,
            'request_failed': self._handle_network_event,
            'response_start': self._handle_network_event,
            'response_end': self._handle_network_event,
            'resource_response_body': self._handle_response_body,
        }

    def on_event_received(self, event_type: str, data: dict):
        """事件接收主入口"""
        try:
            self._log_event(event_type, data)
            
            # 处理网络事件
            if self._is_network_event(event_type):
                self._append_network_row(event_type, data)
            
            # 分发到具体处理器
            handler = self._event_handlers.get(event_type)
            if handler:
                handler(data)
                
        except Exception as e:
            print_and_flush(f"事件处理失败: {str(e)}")
            self._append_log(f"[错误] 事件处理失败: {str(e)}")

    def _log_event(self, event_type: str, data: dict):
        """记录事件到日志"""
        ts = data.get('timestamp', datetime.now())
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts)
        zh_name = self._event_name_zh(event_type)
        
        # 只记录重要事件到控制台
        if event_type in ['browser_launch', 'browser_close', 'new_page', 'page_closed']:
            print_and_flush(f"收到事件: {event_type}")
        
        # 简化日志输出
        if event_type in ['request_start', 'resource_response', 'request_finished', 'request_failed']:
            url = data.get('url', '')
            self._append_log(f"[{ts_str}] {zh_name}: {url}")
        else:
            self._append_log(f"[{ts_str}] {zh_name}")

    def _is_network_event(self, event_type: str) -> bool:
        """判断是否为网络相关事件"""
        return event_type in [
            'request_start', 'request_finished', 'request_failed',
            'resource_response', 'response_start', 'response_end'
        ]

    # 具体事件处理器
    def _handle_browser_launch(self, data: dict):
        """处理浏览器启动事件"""
        self.goto_btn.setEnabled(True)
        self.toggle_btn.setText("关闭浏览器")

    def _handle_browser_close(self, data: dict):
        """处理浏览器关闭事件"""
        self.goto_btn.setEnabled(False)
        self.toggle_btn.setText("打开浏览器")
        self.tabs_table.setRowCount(0)

    def _handle_new_page(self, data: dict):
        """处理新页面事件"""
        self._upsert_tab_row(data)

    def _handle_page_closed(self, data: dict):
        """处理页面关闭事件"""
        self._remove_tab_row(data)

    def _handle_url_change(self, data: dict):
        """处理URL变化事件"""
        self._upsert_tab_row(data)

    def _handle_page_load(self, data: dict):
        """处理页面加载事件"""
        self._upsert_tab_row(data)

    def _handle_network_event(self, data: dict):
        """处理网络事件（已在主入口处理）"""
        pass

    def _handle_response_body(self, data: dict):
        """处理响应体事件"""
        self._update_network_body(data)

    def _event_name_zh(self, event_type: str) -> str:
        mapping = {
            # 浏览器生命周期
            'browser_launch': '浏览器启动',
            'browser_close': '浏览器关闭',
            'browser_disconnected': '浏览器断开连接',
            'browser_crash': '浏览器崩溃',
            
            # 页面事件
            'new_page': '新建页面',
            'page_closed': '页面关闭',
            'url_change': 'URL变化',
            'page_load': '页面加载',
            'dom_loaded': 'DOM加载完成',
            'document_ready': '文档就绪',
            
            # 网络请求
            'request_start': '请求开始',
            'request_finished': '请求完成',
            'request_failed': '请求失败',
            'request_end': '请求结束',
            'resource_response': '资源响应',
            'response_start': '响应开始',
            'response_end': '响应结束',
            
            # 框架
            'frame_navigated': '框架导航',
            'frame_attached': '框架附加',
            'frame_detached': '框架分离',
            
            # WebSocket
            'websocket': 'WebSocket连接',
            'websocket_error': 'WebSocket错误',
            'websocket_message': 'WebSocket消息',
            
            # 其他
            'error': '错误',
            'popup': '弹出窗口',
            'navigation_end': '导航完成',
            'loading_state_change': '加载状态改变',
        }
        return mapping.get(event_type, event_type)

    def _upsert_tab_row(self, data: dict):
        page_id = data.get('page_id')
        url = data.get('url') or data.get('new_url') or ''
        
        # 只处理有有效page_id的标签页
        if not page_id:
            return
            
        display = f"[{page_id}] {url}"

        # find existing
        for row in range(self.tabs_table.rowCount()):
            cell = self.tabs_table.item(row, 0)
            if not cell:
                continue
            if cell.text().startswith(f"[{page_id}]"):
                cell.setText(display)
                return

        # insert new
        row = self.tabs_table.rowCount()
        self.tabs_table.insertRow(row)
        self.tabs_table.setItem(row, 0, QTableWidgetItem(display))

    def _remove_tab_row(self, data: dict):
        page_id = data.get('page_id')
        if page_id is None:
            return
        for row in range(self.tabs_table.rowCount()):
            cell = self.tabs_table.item(row, 0)
            if not cell:
                continue
            if cell.text().startswith(f"[{page_id}]"):
                self.tabs_table.removeRow(row)
                return

    def _append_network_row(self, event_type: str, data: dict):
        """添加网络请求记录到表格"""
        try:
            # 提取基本信息
            ts = data.get('timestamp')
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            stage = self._event_name_zh(event_type)
            method = data.get('method', '')
            url = data.get('url', '')
            
            # 处理资源类型和状态
            rtype = data.get('resource_type', '')
            status = ''
            
            if event_type == 'resource_response':
                status = str(data.get('status', ''))
                # 优先使用content-type作为资源类型
                headers = data.get('headers', {})
                content_type = headers.get('content-type', '')
                if content_type:
                    rtype = content_type

            # 添加到表格
            self._add_network_table_row(ts_str, stage, method, rtype, status, url)
            
            # 限制表格行数
            self._limit_network_table_rows()
            
        except Exception as e:
            self._append_log(f"[错误] 添加网络记录失败: {str(e)}")

    def _add_network_table_row(self, timestamp: str, stage: str, method: str, 
                              resource_type: str, status: str, url: str):
        """向网络表格添加一行数据"""
        row = self.net_table.rowCount()
        self.net_table.insertRow(row)
        
        items = [timestamp, stage, method, resource_type, status, url]
        for col, item in enumerate(items):
            self.net_table.setItem(row, col, QTableWidgetItem(item))
        
        self.net_table.scrollToBottom()

    def _limit_network_table_rows(self, max_rows: int = 1000):
        """限制网络表格的最大行数"""
        while self.net_table.rowCount() > max_rows:
            self.net_table.removeRow(0)

    def _update_network_body(self, data: dict):
        url = data.get('url') or ''
        status = data.get('status')
        ctype = data.get('content_type') or ''
        body = data.get('body_text')
        header = f"URL: {url}\n状态: {status}\n类型: {ctype}\n\n"
        self.net_body.setPlainText(header + (body or '[非文本或无正文]'))

    def _on_net_row_clicked(self, row: int, col: int):
        # 点击表格时，若此前已收到该URL的响应体，显示在下方；否则显示基本信息
        try:
            url_item = self.net_table.item(row, 5)
            if not url_item:
                return
            url = url_item.text()
            # 日志里已有的最后一条相同URL响应体优先展示（简化处理）
            # 实际可维护一个 dict[url] = last_body
            # 这里尝试在 net_body 中刷新标题
            current = self.net_body.toPlainText()
            if current.startswith('URL:') and f"URL: {url}\n" in current:
                return
            header = f"URL: {url}\n\n"
            self.net_body.setPlainText(header + '（等待响应体事件或该资源非文本）')
        except Exception:
            pass

    # Controls
    # ============== UI Actions ==============
    def navigate_url(self):
        """跳转到指定URL"""
        if not self.controller.page:
            return
        url = self.url_edit.text().strip()
        try:
            self.controller.tiaozhuan_url(url)
        except Exception as e:
            self._show_error(f"导航到新页面时出错：{e}")

    def toggle_browser(self):
        """打开或关闭浏览器"""
        if self.controller.browser is None:
            print_and_flush("准备启动浏览器...")
            exec_path = self.path_edit.text().strip()
            if not exec_path or not os.path.exists(exec_path):
                self._show_error("请设置有效的浏览器路径！")
                return
            start_url = self.url_edit.text().strip()
            account_name = self.account_name_edit.text().strip()
            cache_root = self.cache_path_edit.text().strip()
            print_and_flush(f"浏览器路径: {exec_path}")
            print_and_flush(f"起始URL: {start_url}")
            print_and_flush(f"账号名: {account_name}")
            print_and_flush(f"缓存路径: {cache_root}")
            self.toggle_btn.setEnabled(False)
            try:
                self.controller.qiyong_liulanqi(exec_path, start_url, account_name=account_name, cache_root=cache_root)
                print_and_flush("浏览器启动命令已发送")
            except Exception as e:
                self._show_error(f"启动浏览器失败: {e}")
                self.toggle_btn.setEnabled(True)
                return
            self.toggle_btn.setEnabled(True)
        else:
            print_and_flush("准备关闭浏览器...")
            self.toggle_btn.setEnabled(False)
            try:
                self.controller.guanbi_liulanqi()
                print_and_flush("浏览器关闭命令已发送")
            except Exception as e:
                self._show_error(f"关闭浏览器失败: {e}")
            self.toggle_btn.setEnabled(True)

    def activate_selected_tab(self, row, col):
        """激活选中的标签页"""
        page_id = self._selected_page_id()
        if page_id is None:
            return
        self.controller.qian_tai_xianshi_yemian(page_id)

    def show_tab_context_menu(self, pos):
        """显示标签页右键菜单"""
        from PySide6.QtWidgets import QMenu
        index = self.tabs_table.indexAt(pos)
        if index.isValid():
            self.tabs_table.setCurrentCell(index.row(), 0)
        page_id = self._selected_page_id()
        if page_id is None:
            return
        menu = QMenu(self)
        action_close = menu.addAction("关闭此标签")
        action = menu.exec_(self.tabs_table.mapToGlobal(pos))
        if action == action_close:
            self.controller.guanbi_yemian_tongguo_id(page_id)

    # ============== UI Actions ==============


def main():
    # 在Windows上设置事件循环策略以解决I/O操作错误
    if sys.platform == "win32":
        from asyncio import WindowsProactorEventLoopPolicy, set_event_loop_policy
        set_event_loop_policy(WindowsProactorEventLoopPolicy())
    
    print_and_flush("Starting Qt application...")
    app = QApplication(sys.argv)
    print_and_flush("QApplication created")
    w = QtBrowserApp()
    print_and_flush("QtBrowserApp created")
    w.resize(900, 600)
    w.show()
    print_and_flush("Window shown")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


