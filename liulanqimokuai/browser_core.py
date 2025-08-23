import asyncio
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from fingerprint_manager import FingerprintManager
import os

from browser_events import BrowserEventManager


class BrowserController:
    """可复用的浏览器控制器：封装启动/关闭/导航与事件分发。

    - 自带后台事件循环线程
    - 统一事件订阅 on(event, handler)
    - 提供拼音别名方法，便于中文项目调用
    """

    def __init__(self) -> None:
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._nav_lock: Optional[asyncio.Lock] = None
        self._fingerprint_manager = FingerprintManager()
        self._fingerprint: Optional[dict] = None

        # 事件系统
        self.event_manager = BrowserEventManager()
        self._subscribers: Dict[str, List[Callable[[dict], None]]] = {}
        self._subscribers['*'] = []  # 通配

        self._start_event_loop()

    # -------------------- 事件循环 --------------------
    def _start_event_loop(self) -> None:
        if self._loop is not None:
            return
        self._loop = asyncio.new_event_loop()

        def _run() -> None:
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._loop_thread = threading.Thread(target=_run, daemon=True)
        self._loop_thread.start()

    def run_async(self, coro):
        if not self._loop:
            raise RuntimeError('事件循环未启动')
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    # -------------------- 事件订阅 --------------------
    def on(self, event_type: str, handler: Callable[[dict], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def off(self, event_type: str, handler: Callable[[dict], None]) -> None:
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    # 拼音别名
    def ting_shijian(self, event_type: str, handler: Callable[[dict], None]) -> None:
        self.on(event_type, handler)

    def _emit(self, event_type: str, data: dict) -> None:
        # 指定类型
        for h in self._subscribers.get(event_type, []):
            try:
                h(data)
            except Exception:
                pass
        # 通配
        for h in self._subscribers.get('*', []):
            try:
                h({'event_type': event_type, **(data or {})})
            except Exception:
                pass

    def _wire_event_manager(self) -> None:
        # 绑定所有我们关心的事件类型
        def make_cb(evt: str):
            return lambda d: self._emit(evt, d or {})

        for evt in [
            'browser_launch', 'browser_close', 'browser_disconnected',
            'new_page', 'page_closed', 'url_change', 'page_load',
            'popup', 'popup_created', 'popup_closed',  # 添加弹出窗口相关事件
            'request_start', 'request_finished', 'request_failed', 'resource_response',
            'error', 'navigation_end'
        ]:
            self.event_manager.add_event_handler(evt, make_cb(evt))

    # -------------------- 浏览器控制 --------------------
    async def _async_start(self, executable_path: str, start_url: str, account_name: Optional[str] = None, cache_root: Optional[str] = None) -> None:
        try:
            if not self._nav_lock:
                self._nav_lock = asyncio.Lock()

            if not os.path.exists(executable_path):
                raise FileNotFoundError(f"找不到浏览器程序: {executable_path}")

            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '正在启动playwright...'})
            self.playwright = await async_playwright().start()
            
            # 用户数据目录（账号独立缓存）
            user_data_dir = None
            if cache_root and account_name:
                user_data_dir = os.path.join(cache_root, account_name)
                # 确保目录存在
                os.makedirs(user_data_dir, exist_ok=True)
                self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'使用缓存目录: {user_data_dir}'})

            # 指纹：首次为账号生成并保存，后续读取
            if account_name and cache_root:
                self._fingerprint = self._fingerprint_manager.ensure_account_fingerprint(
                    os.path.join(cache_root, account_name)
                )
        except Exception as e:
            self._emit('error', {'timestamp': datetime.now(), 'message': f'初始化失败: {str(e)}'})
            raise

        try:
            # 启动浏览器/上下文
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '正在启动Chrome浏览器...'})
            
            # 获取浏览器启动参数和上下文选项
            browser_args = self._get_browser_args()
            context_options = self._get_context_options()
            
            if user_data_dir:
                self.browser = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    executable_path=executable_path,
                    headless=False,
                    args=browser_args,
                    **context_options
                )
                self.context = self.browser  # type: ignore
            else:
                self.browser = await self.playwright.chromium.launch(
                    executable_path=executable_path,
                    headless=False,
                    args=browser_args
                )
                self.context = await self.browser.new_context(**context_options)
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': 'Chrome浏览器已启动'})
        except Exception as e:
            self._emit('error', {'timestamp': datetime.now(), 'message': f'启动浏览器失败: {str(e)}'})
            # 清理资源
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            raise
        try:
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '正在创建新页面...'})
            self.page = await self.context.new_page()

            # 事件桥接
            self._wire_event_manager()
            self.event_manager.shezhi_liulanqi_shijian(self.browser, self.context, self.page)
            


            # 主动发事件，便于外部UI初始化
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '浏览器初始化完成'})
            self._emit('new_page', {'timestamp': datetime.now(), 'url': self.page.url, 'page_id': id(self.page)})
        except Exception as e:
            self._emit('error', {'timestamp': datetime.now(), 'message': f'页面初始化失败: {str(e)}'})
            # 清理资源
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            raise

        try:
            # 应用部分指纹（UA/语言）
            if self._fingerprint:
                self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '正在设置浏览器指纹...'})
                try:
                    # 使用统一的指纹提取函数
                    from utils import extract_fingerprint_headers
                    extra_headers = extract_fingerprint_headers(self._fingerprint)
                    if extra_headers:
                        await self.context.set_extra_http_headers(extra_headers)  # type: ignore
                except Exception as e:
                    self._emit('warning', {'timestamp': datetime.now(), 'message': f'应用指纹数据失败: {str(e)}'})

            # 导航
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在打开页面: {start_url}'})
            async with self._nav_lock:
                await self.page.goto(start_url, wait_until='domcontentloaded', timeout=30000)
            
            # 注入反检测脚本
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '正在注入反检测脚本...'})
            await self._inject_stealth_scripts()
            
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': '页面加载完成'})
            
        except Exception as e:
            error_msg = f'页面加载失败: {str(e)}'
            self._emit('error', {'timestamp': datetime.now(), 'message': error_msg})
            # 清理资源
            if self.page:
                await self.page.close()
                self.page = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            raise Exception(error_msg)

    async def _async_close(self) -> None:
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        finally:
            self._emit('browser_close', {'timestamp': datetime.now(), 'message': '浏览器已关闭'})

    async def _async_goto(self, url: str) -> None:
        if not self.browser or not self.browser.is_connected():
            self._emit('error', {'timestamp': datetime.now(), 'message': '浏览器未连接'})
            return
        if not self.context:
            self.context = await self.browser.new_context()
        if not self.page or self.page.is_closed():
            self.page = await self.context.new_page()
        if not self._nav_lock:
            self._nav_lock = asyncio.Lock()
        async with self._nav_lock:
            await self.page.goto(url, wait_until='domcontentloaded')

    async def _async_bring_to_front(self, page_id: int) -> None:
        await self.event_manager.qian_tai_xianshi_yemian(page_id)

    async def _async_close_tab(self, page_id: int) -> None:
        await self.event_manager.guanbi_yemian_tongguo_id(page_id)

    async def _async_new_tab(self, url: str = "about:blank") -> None:
        """创建新标签页"""
        if not self.context:
            self._emit('error', {'timestamp': datetime.now(), 'message': '浏览器上下文未初始化'})
            return
        try:
            page = await self.context.new_page()
            # 为新页面设置事件监听
            self.event_manager.setup_page_events(page)
            # 导航到指定URL
            if url != "about:blank":
                await page.goto(url, wait_until='domcontentloaded')
            # 触发新页面事件
            self._emit('new_page', {'timestamp': datetime.now(), 'url': page.url, 'page_id': id(page)})
        except Exception as e:
            self._emit('error', {'timestamp': datetime.now(), 'message': f'创建新标签页失败: {e}'})

    # -------------------- 对外拼音API --------------------
    def qiyong_liulanqi(self, executable_path: str, start_url: str, account_name: Optional[str] = None, cache_root: Optional[str] = None) -> None:
        future = self.run_async(self._async_start(executable_path, start_url, account_name, cache_root))
        try:
            # 等待异步操作完成，但设置超时时间为30秒
            future.result(timeout=30)
        except Exception as e:
            self._emit('error', {'timestamp': datetime.now(), 'message': f'启动浏览器失败: {str(e)}'})

    def guanbi_liulanqi(self) -> None:
        self.run_async(self._async_close())

    def xinjian_biaoqian(self, url: str = "about:blank") -> None:
        """创建新标签页（拼音别名）"""
        self.run_async(self._async_new_tab(url))

    def tiaozhuan_url(self, url: str) -> None:
        self.run_async(self._async_goto(url))

    def qian_tai_xianshi_yemian(self, page_id: int) -> None:
        self.run_async(self._async_bring_to_front(page_id))

    def guanbi_yemian_tongguo_id(self, page_id: int) -> None:
        self.run_async(self._async_close_tab(page_id))

    def _get_browser_args(self) -> list:
        """获取浏览器启动参数"""
        args = [
            # 基础设置
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            
            # 反检测参数
            '--disable-blink-features',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',
            '--disable-javascript',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            
            # 隐藏自动化标志
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-hang-monitor',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-domain-reliability',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-features=VizDisplayCompositor',
            
            # 性能优化
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            
            # 网络设置
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            
            # 用户代理设置
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36',
            
            # 窗口设置 - 固定为1280x700
            '--window-size=1280,700',
            '--window-position=0,0',
            
            # 其他设置
            '--allow-running-insecure-content',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
        ]
        
        return args

    def _get_context_options(self) -> dict:
        """获取浏览器上下文选项"""
        options = {
            'viewport': {'width': 1280, 'height': 700},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36',
            'locale': 'zh-CN',
            'timezone_id': 'Asia/Shanghai',
            'permissions': ['geolocation'],
            'extra_http_headers': {
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            },
            'ignore_https_errors': True,
            'java_script_enabled': True,
            'has_touch': False,
            'is_mobile': False,
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
        }
        
        return options

    async def _inject_stealth_scripts(self):
        """注入反检测脚本"""
        try:
            from .stealth_scripts import get_stealth_script
            
            # 获取所有反检测脚本
            stealth_script = get_stealth_script()
            
            # 注入脚本
            await self.page.add_init_script(stealth_script)
            
            # 等待脚本执行
            await self.page.wait_for_timeout(1000)
            
        except Exception as e:
            self._emit('warning', {'timestamp': datetime.now(), 'message': f'注入反检测脚本失败: {str(e)}'})


