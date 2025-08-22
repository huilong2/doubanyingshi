from typing import Callable, Dict, Any
from datetime import datetime
import tkinter as tk
import asyncio
import sys
from playwright.async_api import Page, Browser, BrowserContext

def print_and_flush(message):
    """立即打印并刷新输出缓冲区"""
    print(message)
    sys.stdout.flush()

class BrowserEventManager:
    def __init__(self):
        # 存储事件回调函数
        self.event_handlers: Dict[str, list] = {
            # 浏览器生命周期事件
            'browser_launch': [],             # 浏览器启动
            'browser_close': [],              # 浏览器关闭
            'context_close': [],              # 上下文关闭
            'browser_created': [],            # 浏览器创建完毕
            'browser_before_close': [],       # 即将关闭
            'browser_destroyed': [],          # 浏览器销毁
            
            # 导航和加载事件
            'before_browse': [],              # 即将导航
            'loading_state_change': [],       # 加载状态改变
            'loading_start': [],              # 加载开始
            'loading_end': [],                # 加载结束
            'loading_error': [],              # 加载错误
            'document_ready': [],             # Document准备就绪
            
            # 页面内容和状态事件
            'address_change': [],             # 地址改变
            'title_change': [],               # 标题改变
            'favicon_change': [],             # 网站图标改变
            'fullscreen_change': [],          # 全屏状态改变
            'focus_change': [],               # 焦点改变
            'status_message': [],             # 状态消息
            'console_message': [],            # 控制台消息
            
            # 框架相关事件
            'frame_created': [],              # 框架创建
            'frame_attached': [],             # 框架附加
            'frame_detached': [],             # 框架分离
            'frame_load_start': [],           # 框架开始加载
            'frame_load_end': [],             # 框架加载完成
            'frame_error': [],                # 框架加载错误
            'main_frame_changed': [],         # 主框架改变
            
            # 资源加载事件
            'before_resource_load': [],       # 即将加载资源
            'resource_response': [],          # 资源响应
            'resource_redirect': [],          # 资源重定向
            'resource_load_complete': [],     # 资源加载完成
            'resource_load_error': [],        # 资源加载错误
            
            # 下载相关事件
            'before_download': [],            # 即将下载
            'download_updated': [],           # 下载更新
            'download_progress': [],          # 下载进度
            'can_download': [],               # 可以下载
            'download_complete': [],          # 下载完成
            
            # 对话框和权限事件
            'before_popup': [],               # 即将打开新窗口
            'popup_created': [],              # 新窗口已创建
            'popup_closed': [],               # 新窗口已关闭
            'dialog_open': [],                # 对话框打开
            'dialog_close': [],               # 对话框关闭
            'file_dialog': [],                # 文件对话框
            'permission_prompt': [],          # 权限提示
            'media_access': [],               # 媒体访问权限
            
            # 渲染进程事件
            'render_process_terminated': [],   # 渲染进程终止
            'render_view_ready': [],          # 渲染视图就绪
            'render_process_crashed': [],     # 渲染进程崩溃
            
            # WebSocket事件
            'websocket_created': [],          # WebSocket创建
            'websocket_handshake': [],        # WebSocket握手
            'websocket_message': [],          # WebSocket消息
            'websocket_error': [],            # WebSocket错误
            'websocket_closed': [],           # WebSocket关闭
            
            # 音频事件
            'audio_stream_started': [],       # 音频流开始
            'audio_stream_packet': [],        # 音频流数据包
            'audio_stream_stopped': [],       # 音频流停止
            'audio_stream_error': [],         # 音频流错误
            'audio_state_changed': [],        # 音频状态改变
            
            # 视频事件
            'video_stream_started': [],       # 视频流开始
            'video_stream_stopped': [],       # 视频流停止
            'video_stream_error': [],         # 视频流错误
            'video_state_changed': [],        # 视频状态改变
            
            # URL请求事件
            'url_request_progress': [],       # URL请求进度
            'url_request_complete': [],       # URL请求完成
            'url_request_data': [],           # URL请求数据
            'url_request_error': [],          # URL请求错误
            'url_request_canceled': [],       # URL请求取消
            
            # 开发者工具事件
            'devtools_message': [],           # 开发者工具消息
            'devtools_event': [],             # 开发者工具事件
            'devtools_agent_attached': [],    # 开发者工具代理附加
            'devtools_focused': [],           # 开发者工具获得焦点
            'devtools_method_result': [],     # 开发者工具方法结果
            
            # 安全和证书事件
            'security_state_changed': [],     # 安全状态改变
            'ssl_certificate_error': [],      # SSL证书错误
            'client_certificate_request': [], # 客户端证书请求
            
            # 进程和通信事件
            'process_message': [],            # 进程间消息
            'process_created': [],            # 进程创建
            'process_terminated': [],         # 进程终止
            'ipc_message': [],               # IPC消息
            
            # 用户界面事件
            'context_menu': [],               # 上下文菜单
            'menu_command': [],               # 菜单命令
            'accelerator_command': [],        # 快捷键命令
            'find_result': [],                # 查找结果
            'scale_changed': [],              # 缩放比例改变
            
            # 存储和配额事件
            'quota_request': [],              # 配额请求
            'storage_cleared': [],            # 存储已清除
            'storage_quota_updated': [],      # 存储配额更新
            
            # 系统事件
            'system_memory_warning': [],      # 系统内存警告
            'system_gpu_info_update': [],     # GPU信息更新
            'system_display_change': [],      # 显示器变化
            
            # 页面生命周期事件
            'new_page': [],                   # 新页面创建
            'page_closed': [],                # 页面关闭
            'page_load': [],                  # 页面加载完成
            'url_change': [],                 # URL变化
            'navigation_end': [],             # 导航完成
            
            # 其他事件
            'error': [],                      # 错误
            'warning': [],                    # 警告
            'info': [],                       # 信息
            'log': []                         # 日志
        }
        
        # 状态记录
        self.current_url = None
        self.is_browser_open = False
        self.page_load_time = None
        self.navigation_start_time = None
        
    def add_event_handler(self, event_type: str, handler: Callable):
        """添加事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            
    def remove_event_handler(self, event_type: str, handler: Callable):
        """移除事件处理器"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            
    def _trigger_event(self, event_type: str, event_data: Any = None):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    self._log_error(f'事件处理器调用失败 ({event_type})', e)
                
    def shezhi_liulanqi_shijian(self, browser: Browser, context: BrowserContext, page: Page):
        """设置浏览器事件监听（中文拼音别名）"""
        self.setup_browser_events(browser, context, page)
        
    def setup_page_events(self, page: Page):
        """为页面设置事件监听"""
        # 处理页面生命周期事件
        def handle_close():
            try:
                page_id = id(page)
                url = page.url if not page.is_closed() else None
                
                # 发送关闭事件
                event_data = {
                    'timestamp': datetime.now(),
                    'message': '页面已关闭',
                    'url': url,
                    'page_id': page_id
                }
                self._trigger_event('page_closed', event_data)

                # 异步延迟后再检查是否所有标签页已关闭（避免时序问题）
                async def _deferred_check_all_closed():
                    try:
                        await asyncio.sleep(0.2)
                        if hasattr(self, 'context') and self.context:
                            remaining = []
                            try:
                                remaining = list(self.context.pages)
                            except:
                                remaining = []
                            if not remaining:
                                self.is_browser_open = False
                                self._trigger_event('context_close', {
                                    'timestamp': datetime.now(),
                                    'message': '所有页面已关闭（上下文关闭）'
                                })
                                self._trigger_event('browser_close', {
                                    'timestamp': datetime.now(),
                                    'message': '检测到所有标签页关闭，触发浏览器关闭事件'
                                })
                    except Exception as e:
                        self._log_error('检测所有页面关闭时出错', e)
                asyncio.create_task(_deferred_check_all_closed())
            except Exception as e:
                self._log_error('页面关闭事件处理错误', e)
                
        def handle_crash(): self._handle_page_crash()
        def handle_dom_loaded(): self._handle_dom_loaded()
        def handle_load(): asyncio.create_task(self._handle_page_load(page))
        
        page.on("close", handle_close)
        page.on("crash", handle_crash)
        page.on("domcontentloaded", handle_dom_loaded)
        page.on("load", handle_load)
        
        # URL变化监听
        def handle_frame_nav(frame):
            if frame == page.main_frame:
                self._handle_url_change(frame, page)
        page.on("framenavigated", handle_frame_nav)
        
        # 导航和内容事件
        def handle_frame_attached(frame): self._handle_frame_attached(frame)
        def handle_frame_detached(frame): self._handle_frame_detached(frame)
        def handle_frame_navigated(frame): self._handle_frame_navigated(frame)
        def handle_frame_load_start(frame): self._handle_frame_load_start(frame)
        def handle_frame_load_error(frame, error): self._handle_frame_load_error(frame, error)
        def handle_frame_load_end(frame): self._handle_frame_load_end(frame)
        
        page.on("frameattached", handle_frame_attached)
        page.on("framedetached", handle_frame_detached)
        page.on("framenavigated", handle_frame_navigated)
        page.on("frameloadstart", handle_frame_load_start)
        page.on("frameloaderror", handle_frame_load_error)
        page.on("frameloadend", handle_frame_load_end)
        
        # 弹出窗口监听
        async def handle_popup(popup):
            try:
                # 发送弹出窗口事件
                self._trigger_event('popup', {
                    'timestamp': datetime.now(),
                    'url': popup.url,
                    'page_id': id(popup)
                })
                # 为新页面设置事件监听
                self.setup_page_events(popup)
                # 等待页面加载完成
                await popup.wait_for_load_state('domcontentloaded')
                # 发送新页面和URL变化事件
                self._trigger_event('new_page', {
                    'timestamp': datetime.now(),
                    'url': popup.url,
                    'page_id': id(popup)
                })
            except Exception as e:
                self._log_error('处理弹出窗口事件失败', e)
                
        page.on("popup", lambda popup: asyncio.create_task(handle_popup(popup)))
        
        # 网络请求事件（确保响应事件触发）
        async def handle_request(request):
            try:
                self._handle_request_start(request)
                response = await request.response()
                if response:
                    self._handle_response(response)
            except Exception as e:
                self._log_error('处理请求响应时出错', e)
                
        page.on("request", lambda request: asyncio.create_task(handle_request(request)))
        page.on("requestfailed", lambda request: self._handle_request_failed(request))
        page.on("requestfinished", lambda request: self._handle_request_finished(request))
        page.on("response", lambda response: self._handle_response(response))
        
        # 下载事件
        page.on("download", lambda download: self._handle_download(download))
        page.on("downloadprogress", lambda progress: self._handle_download_progress(progress))
        page.on("downloadcomplete", lambda download: self._handle_download_complete(download))
        
        # 对话框事件
        page.on("dialog", lambda dialog: self._handle_dialog(dialog))
        page.on("filechooser", lambda chooser: self._handle_file_chooser(chooser))
        page.on("popup", lambda popup: self._handle_popup(popup))
        
        # Web Workers和WebSocket事件
        page.on("worker", lambda worker: self._handle_worker(worker))
        page.on("websocket", lambda ws: self._handle_websocket(ws))
        page.on("websocketerror", lambda ws, error: self._handle_websocket_error(ws, error))
        page.on("websocketmessage", lambda ws, data: self._handle_websocket_message(ws, data))
        
        # 错误和控制台事件
        page.on("pageerror", lambda error: self._handle_page_error(error))
        page.on("console", lambda msg: self._handle_console_message(msg))
        page.on("jserror", lambda error: self._handle_javascript_error(error))
        
        # 开发者工具事件
        page.on("devtools", lambda msg: self._handle_devtools_message(msg))
        page.on("devtoolsevent", lambda event: self._handle_devtools_event(event))
        
        # 媒体事件
        page.on("media", lambda request: self._handle_media_request(request))
        page.on("mediaerror", lambda error: self._handle_media_error(error))
        page.on("mediastate", lambda state: self._handle_media_state(state))
        
        # 安全事件
        page.on("security", lambda info: self._handle_security_info(info))
        page.on("certificate", lambda info: self._handle_certificate_info(info))
        
    def setup_browser_events(self, browser: Browser, context: BrowserContext, page: Page):
        """设置浏览器事件监听"""
        # 初始化状态
        self.is_browser_open = True
        self.current_url = 'about:blank'
        self.browser = browser
        self.page = page
        self.context = context
        
        # 触发浏览器启动事件
        self._trigger_event('browser_launch', {
            'timestamp': datetime.now(),
            'message': '浏览器已启动'
        })
        
        # 浏览器生命周期事件
        browser.on("disconnected", lambda: self._handle_disconnected())
        
        # 上下文事件
        context.on("page", lambda page: self._handle_new_page(page))
        context.on("close", lambda: self._handle_context_close())
        
        # 为初始页面设置事件监听
        self.setup_page_events(page)
        
        # 系统事件
        browser.on("systeminfo", lambda info: self._handle_system_info(info))
        browser.on("memoryinfo", lambda info: self._handle_memory_info(info))
        
        # 进程事件
        browser.on("targetcreated", lambda target: self._handle_target_created(target))
        browser.on("targetchanged", lambda target: self._handle_target_changed(target))
        browser.on("targetdestroyed", lambda target: self._handle_target_destroyed(target))
        
        # 其他辅助事件
        # 移除了重复的事件监听，因为已经在上面注册过了
        pass

    def _handle_context_close(self):
        """BrowserContext 被关闭（通常意味着所有标签页已被关闭）"""
        try:
            self.is_browser_open = False
            self._trigger_event('context_close', {
                'timestamp': datetime.now(),
                'message': 'BrowserContext 已关闭'
            })
            # 紧接着触发浏览器关闭事件，便于上层统一清理
            self._trigger_event('browser_close', {
                'timestamp': datetime.now(),
                'message': '因上下文关闭，判定浏览器关闭'
            })
        except Exception as e:
            self._log_error('处理上下文关闭事件失败', e)

    def _handle_disconnected(self):
        """浏览器进程断开连接（例如手动关闭窗口）"""
        try:
            self.is_browser_open = False
            self._trigger_event('browser_disconnected', {
                'timestamp': datetime.now(),
                'message': '浏览器已断开连接'
            })
            # 断开后立即视为关闭，触发关闭事件
            self._trigger_event('browser_close', {
                'timestamp': datetime.now(),
                'message': '因浏览器断开连接，判定浏览器关闭'
            })
        except Exception as e:
            self._log_error('处理浏览器断开事件失败', e)
        
    async def _handle_page_load(self, page: Page):
        """处理页面加载事件"""
        try:
            # 检查页面是否仍然有效
            if not hasattr(page, 'is_closed') or page.is_closed():
                self._trigger_event('error', {
                    'timestamp': datetime.now(),
                    'message': '页面已关闭，无法处理加载事件'
                })
                return
                
            self.page_load_time = datetime.now()
            event_data = {
                'timestamp': self.page_load_time,
                'url': page.url
            }
            try:
                event_data['title'] = await page.main_frame.title()
            except:
                event_data['title'] = '无标题'
                
            self._trigger_event('page_load', event_data)
        except Exception as e:
            self._trigger_event('error', {
                'timestamp': datetime.now(),
                'message': f'页面加载事件处理错误: {str(e)}'
            })
        
    def _handle_url_change(self, frame, page: Page):
        """处理URL变化事件"""
        try:
            if frame == page.main_frame and page.url != self.current_url:
                old_url = self.current_url
                self.current_url = page.url
                self._trigger_event('url_change', {
                    'timestamp': datetime.now(),
                    'old_url': old_url,
                    'new_url': self.current_url
                })
        except Exception as e:
            self._trigger_event('error', {
                'timestamp': datetime.now(),
                'message': f'URL变化事件处理错误: {str(e)}'
            })
            
    def _handle_console_message(self, message):
        """处理控制台消息事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('console_message', {
                'timestamp': datetime.now(),
                'type': message.type,
                'text': message.text,
                'location': message.location if hasattr(message, 'location') else None
            })
        except Exception as e:
            self._log_error('控制台消息事件处理错误', e)
        
    def _handle_dialog(self, dialog):
        """处理对话框事件"""
        try:
            self._trigger_event('dialog_open', {
                'timestamp': datetime.now(),
                'type': dialog.type,
                'message': dialog.message,
                'default_value': dialog.default_value() if hasattr(dialog, 'default_value') else None
            })
        except Exception as e:
            self._log_error('对话框事件处理错误', e)
        
    def _handle_download(self, download):
        """处理下载事件"""
        try:
            self._trigger_event('download_start', {
                'timestamp': datetime.now(),
                'suggested_filename': download.suggested_filename
            })
        except Exception as e:
            self._log_error('下载事件处理错误', e)
        
    def _handle_error(self, error):
        """处理错误事件"""
        self._trigger_event('error', {
            'timestamp': datetime.now(),
            'message': str(error)
        })
        
    def _handle_page_error(self, error):
        """处理页面错误事件"""
        try:
            self._trigger_event('page_error', {
                'timestamp': datetime.now(),
                'message': str(error),
                'name': getattr(error, 'name', None),
                'stack': getattr(error, 'stack', None)
            })
        except Exception as e:
            self._log_error('页面错误事件处理错误', e)

    def _handle_new_page(self, page):
        """处理新页面创建事件"""
        try:
            # 为新页面设置事件监听
            self.setup_page_events(page)
            
            # 触发新页面事件
            self._trigger_event('new_page', {
                'timestamp': datetime.now(),
                'url': page.url,
                'page_id': id(page)
            })
        except Exception as e:
            self._log_error('新页面事件处理错误', e)

    def _handle_request_start(self, request):
        """处理请求开始事件"""
        try:
            event_data = {
                'timestamp': datetime.now(),
                'url': getattr(request, 'url', ''),
                'method': getattr(request, 'method', 'GET'),
                'headers': getattr(request, 'headers', {}),
                'post_data': getattr(request, 'post_data', None),
                'resource_type': getattr(request, 'resource_type', '')
            }
            self._trigger_event('request_start', event_data)
        except Exception as e:
            self._log_error('请求开始事件处理错误', e)

    def _handle_response_start(self, response):
        """处理响应开始事件"""
        try:
            self._trigger_event('response_start', {
                'timestamp': datetime.now(),
                'url': getattr(response, 'url', ''),
                'status': getattr(response, 'status', 0),
                'status_text': getattr(response, 'status_text', None),
                'headers': getattr(response, 'headers', {})
            })
        except Exception as e:
            self._log_error('响应开始事件处理错误', e)

    def _handle_frame_attached(self, frame):
        """处理框架附加事件"""
        try:
            self._trigger_event('frame_attached', {
                'timestamp': datetime.now(),
                'frame_url': getattr(frame, 'url', ''),
                'frame_name': getattr(frame, 'name', ''),
                'is_main_frame': frame == self.page.main_frame if self.page else False
            })
        except Exception as e:
            self._log_error('框架附加事件处理错误', e)

    def _handle_frame_detached(self, frame):
        """处理框架分离事件"""
        try:
            self._trigger_event('frame_detached', {
                'timestamp': datetime.now(),
                'frame_url': getattr(frame, 'url', ''),
                'frame_name': getattr(frame, 'name', ''),
                'is_main_frame': frame == self.page.main_frame if self.page else False
            })
        except Exception as e:
            self._log_error('框架分离事件处理错误', e)

    def _handle_frame_navigated(self, frame):
        """处理框架导航事件"""
        try:
            self._trigger_event('frame_navigated', {
                'timestamp': datetime.now(),
                'frame_url': getattr(frame, 'url', ''),
                'frame_name': getattr(frame, 'name', ''),
                'is_main_frame': frame == self.page.main_frame if self.page else False
            })
        except Exception as e:
            self._log_error('框架导航事件处理错误', e)

    def _handle_crash(self):
        """处理浏览器崩溃事件"""
        try:
            self._trigger_event('browser_crash', {
                'timestamp': datetime.now(),
                'message': '浏览器已崩溃'
            })
        except Exception as e:
            self._log_error('浏览器崩溃事件处理错误', e)

    def _handle_disconnected(self):
        """处理浏览器断开连接事件"""
        try:
            self._trigger_event('browser_disconnected', {
                'timestamp': datetime.now(),
                'message': '浏览器已断开连接'
            })
        except Exception as e:
            self._log_error('浏览器断开连接事件处理错误', e)

    def _handle_permission_request(self, permission):
        """处理权限请求事件"""
        try:
            self._trigger_event('permission_requested', {
                'timestamp': datetime.now(),
                'permission': permission
            })
        except Exception as e:
            self._log_error('权限请求事件处理错误', e)

    def _handle_permission_response(self, permission, state):
        """处理权限响应事件"""
        try:
            self._trigger_event('permission_response', {
                'timestamp': datetime.now(),
                'permission': permission,
                'state': state
            })
        except Exception as e:
            self._log_error('权限响应事件处理错误', e)

    def _handle_authentication(self, request):
        """处理身份验证事件"""
        try:
            self._trigger_event('authentication_requested', {
                'timestamp': datetime.now(),
                'url': getattr(request, 'url', ''),
                'method': getattr(request, 'method', 'GET')
            })
        except Exception as e:
            self._log_error('身份验证事件处理错误', e)



    def _handle_metrics(self, metrics):
        """处理性能指标事件"""
        try:
            self._trigger_event('performance_metrics', {
                'timestamp': datetime.now(),
                'metrics': metrics
            })
        except Exception as e:
            self._log_error('性能指标事件处理错误', e)

    def _handle_screencast_frame(self, frame):
        """处理屏幕录像帧事件"""
        try:
            self._trigger_event('screencast_frame', {
                'timestamp': datetime.now(),
                'frame': frame
            })
        except Exception as e:
            self._log_error('屏幕录像帧事件处理错误', e)

    def _handle_binding_called(self, binding):
        """处理绑定调用事件"""
        try:
            self._trigger_event('binding_called', {
                'timestamp': datetime.now(),
                'binding': binding
            })
        except Exception as e:
            self._log_error('绑定调用事件处理错误', e)

    def _handle_route(self, route):
        """处理路由事件"""
        try:
            self._trigger_event('route_handled', {
                'timestamp': datetime.now(),
                'url': getattr(route, 'url', ''),
                'method': getattr(route, 'method', 'GET')
            })
        except Exception as e:
            self._log_error('路由事件处理错误', e)

    def _handle_video_chunk(self, chunk):
        """处理视频块事件"""
        try:
            self._trigger_event('video_chunk', {
                'timestamp': datetime.now(),
                'chunk': chunk
            })
        except Exception as e:
            self._log_error('视频块事件处理错误', e)

    def _handle_file_chooser(self, filechooser):
        """处理文件选择器事件"""
        try:
            self._trigger_event('file_chooser', {
                'timestamp': datetime.now(),
                'is_multiple': getattr(filechooser, 'is_multiple', lambda: False)(),
                'accepts': getattr(filechooser, 'accepts', [])
            })
        except Exception as e:
            self._log_error('文件选择器事件处理错误', e)

    def _handle_worker(self, worker):
        """处理Web Worker事件"""
        try:
            self._trigger_event('worker', {
                'timestamp': datetime.now(),
                'url': getattr(worker, 'url', ''),
                'worker_id': id(worker)
            })
        except Exception as e:
            self._log_error('Worker事件处理错误', e)

    def _handle_websocket(self, websocket):
        """处理WebSocket事件"""
        try:
            self._trigger_event('websocket', {
                'timestamp': datetime.now(),
                'url': getattr(websocket, 'url', ''),
                'websocket_id': id(websocket)
            })
        except Exception as e:
            self._log_error('WebSocket事件处理错误', e)

    def _handle_popup(self, popup):
        """处理弹出窗口事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('popup', {
                'timestamp': datetime.now(),
                'url': getattr(popup, 'url', ''),
            })
            # 弹出窗口的事件监听已经在context.on("page", ...)中设置
            # 这里不需要再次调用_handle_new_page
        except Exception as e:
            self._log_error('弹出窗口事件处理错误', e)

    # CEF风格的新事件处理方法
    def _handle_frame_load_start(self, frame):
        """处理框架开始加载事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('frame_load_start', {
                'timestamp': datetime.now(),
                'frame_url': frame.url,
                'frame_name': frame.name,
                'is_main_frame': frame == self.page.main_frame if self.page else False
            })
        except Exception as e:
            self._log_error('框架加载开始事件处理错误', e)

    def _handle_frame_load_error(self, frame, error):
        """处理框架加载错误事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('frame_error', {
                'timestamp': datetime.now(),
                'frame_url': getattr(frame, 'url', ''),
                'frame_name': getattr(frame, 'name', ''),
                'error': str(error),
                'is_main_frame': frame == self.page.main_frame if self.page else False
            })
        except Exception as e:
            self._log_error('框架加载错误事件处理错误', e)

    def _handle_frame_load_end(self, frame):
        """处理框架加载完成事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('frame_load_end', {
                'timestamp': datetime.now(),
                'frame_url': getattr(frame, 'url', ''),
                'frame_name': getattr(frame, 'name', ''),
                'is_main_frame': frame == self.page.main_frame if self.page else False
            })
        except Exception as e:
            self._log_error('框架加载完成事件处理错误', e)

    def _handle_download_progress(self, progress):
        """处理下载进度事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            received_bytes = getattr(progress, 'receivedBytes', 0)
            total_bytes = getattr(progress, 'totalBytes', 0)
            self._trigger_event('download_progress', {
                'timestamp': datetime.now(),
                'received_bytes': received_bytes,
                'total_bytes': total_bytes,
                'percent_complete': (received_bytes / total_bytes) * 100 if total_bytes > 0 else 0
            })
        except Exception as e:
            self._log_error('下载进度事件处理错误', e)

    def _handle_download_complete(self, download):
        """处理下载完成事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('download_complete', {
                'timestamp': datetime.now(),
                'url': download.url,
                'suggested_filename': download.suggested_filename,
                'save_path': download.save_path if hasattr(download, 'save_path') else None,
                'state': getattr(download, 'state', None)
            })
        except Exception as e:
            self._log_error('下载完成事件处理错误', e)

    def _handle_websocket_error(self, ws, error):
        """处理WebSocket错误事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('websocket_error', {
                'timestamp': datetime.now(),
                'url': getattr(ws, 'url', ''),
                'error': str(error)
            })
        except Exception as e:
            self._log_error('WebSocket错误事件处理错误', e)

    def _handle_javascript_error(self, error):
        """处理JavaScript错误事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('javascript_error', {
                'timestamp': datetime.now(),
                'message': str(error),
                'stack_trace': getattr(error, 'stack', None),
                'name': getattr(error, 'name', None)
            })
        except Exception as e:
            self._log_error('JavaScript错误事件处理错误', e)

    def _handle_media_error(self, error):
        """处理媒体错误事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('media_error', {
                'timestamp': datetime.now(),
                'message': str(error)
            })
        except Exception as e:
            self._log_error('媒体错误事件处理错误', e)

    def _handle_media_state(self, state):
        """处理媒体状态事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('media_state_changed', {
                'timestamp': datetime.now(),
                'state': state
            })
        except Exception as e:
            self._log_error('媒体状态事件处理错误', e)

    def _handle_system_info(self, info):
        """处理系统信息事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('system_info', {
                'timestamp': datetime.now(),
                'info': info
            })
        except Exception as e:
            self._log_error('系统信息事件处理错误', e)

    def _handle_memory_info(self, info):
        """处理内存信息事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('memory_info', {
                'timestamp': datetime.now(),
                'info': info
            })
        except Exception as e:
            self._log_error('内存信息事件处理错误', e)

    def _handle_security_info(self, info):
        """处理安全信息事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('security_state_changed', {
                'timestamp': datetime.now(),
                'info': info
            })
        except Exception as e:
            self._log_error('安全信息事件处理错误', e)

    def _handle_certificate_info(self, info):
        """处理证书信息事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('ssl_certificate_info', {
                'timestamp': datetime.now(),
                'info': info
            })
        except Exception as e:
            self._log_error('证书信息事件处理错误', e)

    def _handle_devtools_event(self, event):
        """处理开发者工具事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('devtools_event', {
                'timestamp': datetime.now(),
                'event': event
            })
        except Exception as e:
            self._log_error('开发者工具事件处理错误', e)

    def _handle_load_event(self):
        """处理页面加载完成事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('loading_end', {
                'timestamp': datetime.now(),
                'url': self.page.url if self.page else None
            })
        except Exception as e:
            self._log_error('页面加载完成事件处理错误', e)

    def _handle_dom_content_loaded_event(self):
        """处理DOM内容加载完成事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('document_ready', {
                'timestamp': datetime.now(),
                'url': self.page.url if self.page else None
            })
        except Exception as e:
            self._log_error('DOM内容加载完成事件处理错误', e)

    def _handle_dom_loaded(self):
        """处理DOM加载完成事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('dom_loaded', {
                'timestamp': datetime.now(),
                'url': self.page.url if self.page else None
            })
        except Exception as e:
            self._log_error('DOM加载完成事件处理错误', e)

    def _handle_response(self, response):
        """处理响应事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            # 发送resource_response事件，包含详细信息
            self._trigger_event('resource_response', {
                'timestamp': datetime.now(),
                'url': getattr(response, 'url', ''),
                'status': getattr(response, 'status', 0),
                'ok': getattr(response, 'ok', False),
                'headers': getattr(response, 'headers', {}),
                'resource_type': getattr(response.request, 'resource_type', '') if getattr(response, 'request', None) else ''
            })
            
            # 如果是主框架导航，也触发导航结束事件
            if hasattr(response, 'frame') and response.frame and response.frame == getattr(response.frame.page, 'main_frame', None):
                self._trigger_event('navigation_end', {
                    'timestamp': datetime.now(),
                    'url': response.url,
                    'status': response.status,
                    'ok': response.ok
                })
        except Exception as e:
            self._trigger_event('error', {
                'timestamp': datetime.now(),
                'message': f'响应事件处理错误: {str(e)}'
            })
            
    def _handle_request_finished(self, request):
        """处理请求完成事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('request_finished', {
                'timestamp': datetime.now(),
                'url': getattr(request, 'url', ''),
                'method': getattr(request, 'method', 'GET'),
                'resource_type': getattr(request, 'resource_type', ''),
                'response': getattr(request, 'response', None),
                'failure': getattr(request, 'failure', None)
            })
        except Exception as e:
            self._log_error('请求完成事件处理错误', e)

    def _handle_request_end(self, request):
        """处理请求结束事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('request_end', {
                'timestamp': datetime.now(),
                'url': getattr(request, 'url', ''),
                'method': getattr(request, 'method', 'GET'),
                'resource_type': getattr(request, 'resource_type', ''),
                'response': getattr(request, 'response', None)
            })
        except Exception as e:
            self._log_error('请求结束事件处理错误', e)

    def _handle_request_failed(self, request):
        """处理请求失败事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('request_failed', {
                'timestamp': datetime.now(),
                'url': getattr(request, 'url', ''),
                'method': getattr(request, 'method', 'GET'),
                'resource_type': getattr(request, 'resource_type', ''),
                'failure': getattr(request, 'failure', None)
            })
        except Exception as e:
            self._log_error('请求失败事件处理错误', e)

    def _log_error(self, message: str, error: Exception):
        """统一的错误日志处理"""
        self._trigger_event('error', {
            'timestamp': datetime.now(),
            'message': f'{message}: {str(error)}',
            'stack_trace': getattr(error, '__traceback__', None)
        })
            
    def handle_browser_close(self):
        """处理浏览器关闭事件"""
        if self.is_browser_open:
            self.is_browser_open = False
            self._trigger_event('browser_close', {
                'timestamp': datetime.now(),
                'message': '浏览器已关闭'
            })
            
    def _handle_context_close(self):
        """处理浏览器上下文关闭事件"""
        # 检查页面是否仍然有效
        if not hasattr(self.page, 'is_closed') or (self.page and self.page.is_closed()):
            return
            
        try:
            self._trigger_event('context_close', {
                'timestamp': datetime.now(),
                'message': '浏览器上下文已关闭'
            })
        except Exception as e:
            self._log_error('浏览器上下文关闭事件处理错误', e)
            


# 使用示例：
def create_event_handlers(text_widget: tk.Text):
    """创建事件处理器示例"""
    event_manager = BrowserEventManager()
    
    def log_to_widget(event_name: str, data: dict):
        """将事件记录到文本框"""
        try:
            text_widget.insert('end', f"[{data['timestamp']}] {event_name}: {data}\n")
            text_widget.see('end')
        except:
            # 如果GUI已经关闭，忽略错误
            pass
    
    # 添加各种事件处理器
    event_manager.add_event_handler('browser_launch', 
        lambda data: log_to_widget('浏览器启动', data))
    event_manager.add_event_handler('browser_close', 
        lambda data: log_to_widget('浏览器关闭', data))
    event_manager.add_event_handler('page_load', 
        lambda data: log_to_widget('页面加载', data))
    event_manager.add_event_handler('url_change', 
        lambda data: log_to_widget('URL变化', data))
    event_manager.add_event_handler('navigation_end', 
        lambda data: log_to_widget('导航完成', data))
    event_manager.add_event_handler('page_close', 
        lambda data: log_to_widget('页面关闭', data))
    event_manager.add_event_handler('new_page', 
        lambda data: log_to_widget('新页面', data))
    event_manager.add_event_handler('console_message', 
        lambda data: log_to_widget('控制台消息', data))
    event_manager.add_event_handler('dialog_open', 
        lambda data: log_to_widget('对话框打开', data))
    event_manager.add_event_handler('download_start', 
        lambda data: log_to_widget('开始下载', data))
    event_manager.add_event_handler('error', 
        lambda data: log_to_widget('错误', data))
    event_manager.add_event_handler('request_start', 
        lambda data: log_to_widget('请求开始', data))
    event_manager.add_event_handler('request_end', 
        lambda data: log_to_widget('请求结束', data))
        
    return event_manager
