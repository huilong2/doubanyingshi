import asyncio
import threading
import random
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
    async def _async_start(self, executable_path: str, start_url: str, account_name: Optional[str] = None, cache_root: Optional[str] = None, account_id: Optional[int] = None, proxy: Optional[str] = None) -> None:
        # 导入日志模块
        import logging
        logger = logging.getLogger(__name__)
        
        # 构建账号信息用于日志
        account_info = f"账号: {account_name or '匿名'}" + (f" (ID: {account_id})" if account_id else "")
        logger.info(f"开始浏览器启动流程 - {account_info}")
        logger.info(f"浏览器路径: {executable_path}")
        logger.info(f"启动URL: {start_url}")
        logger.info(f"缓存根目录: {cache_root or '未设置'}")
        logger.info(f"代理设置: {proxy or '未设置'}")
        logger.info(f"代理设置: {proxy or '未设置'}")
        
        try:
            if not self._nav_lock:
                self._nav_lock = asyncio.Lock()

            # 验证浏览器路径
            if not os.path.exists(executable_path):
                logger.error(f"浏览器路径不存在: {executable_path} - {account_info}")
                raise FileNotFoundError(f"找不到浏览器程序: {executable_path}")
            
            logger.info(f"浏览器路径验证通过 - {account_info}")
            
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在启动playwright... - {account_info}'})
            logger.info(f"正在初始化Playwright... - {account_info}")
            self.playwright = await async_playwright().start()
            logger.info(f"Playwright初始化成功 - {account_info}")
            
            # 用户数据目录（账号独立缓存）
            user_data_dir = None
            if cache_root and account_name:
                user_data_dir = os.path.join(cache_root, account_name)
                # 确保目录存在
                os.makedirs(user_data_dir, exist_ok=True)
                self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'使用缓存目录: {user_data_dir} - {account_info}'})
                logger.info(f"创建用户数据目录: {user_data_dir} - {account_info}")

            # 指纹：首次为账号生成并保存，后续读取
            if account_name and cache_root:
                logger.info(f"正在加载/生成账号指纹数据 - {account_info}")
                # 修改为正确的参数调用方式
                if account_id:
                    self._fingerprint = self._fingerprint_manager.ensure_account_fingerprint(account_id)
                    logger.info(f"指纹数据加载/生成完成 - {account_info}")
                else:
                    logger.warning(f"未提供账号ID，无法从数据库加载指纹数据 - {account_info}")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)} - {account_info}")
            self._emit('error', {'timestamp': datetime.now(), 'message': f'初始化失败: {str(e)} - {account_info}'})
            raise

        try:
            # 启动浏览器/上下文
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在启动Chrome浏览器... - {account_info}'})
            logger.info(f"正在启动Chrome浏览器... - {account_info}")
            
            # 获取浏览器启动参数和上下文选项
            browser_args = self._get_browser_args()
            context_options = self._get_context_options(proxy)
            logger.debug(f"浏览器启动参数: {browser_args}")
            logger.debug(f"浏览器上下文选项: {context_options}")
            
            if user_data_dir:
                logger.info(f"使用持久化上下文模式启动 - 用户数据目录: {user_data_dir} - {account_info}")
                # 注意：launch_persistent_context返回的是BrowserContext对象
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    executable_path=executable_path,
                    headless=False,
                    args=browser_args,
                    **context_options
                )
                # 获取真正的browser对象
                self.browser = self.context.browser
            else:
                logger.info(f"使用普通模式启动浏览器 - {account_info}")
                self.browser = await self.playwright.chromium.launch(
                    executable_path=executable_path,
                    headless=False,
                    args=browser_args
                )
                self.context = await self.browser.new_context(**context_options)
            
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'Chrome浏览器已启动 - {account_info}'})
            logger.info(f"Chrome浏览器启动成功 - {account_info}")
        except Exception as e:
            logger.error(f"启动浏览器失败: {str(e)} - {account_info}")
            self._emit('error', {'timestamp': datetime.now(), 'message': f'启动浏览器失败: {str(e)} - {account_info}'})
            # 清理资源
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            raise
        try:
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在创建新页面... - {account_info}'})
            logger.info(f"正在创建浏览器页面... - {account_info}")
            self.page = await self.context.new_page()
            logger.info(f"浏览器页面创建成功 - {account_info}")

            # 事件桥接
            self._wire_event_manager()
            self.event_manager.shezhi_liulanqi_shijian(self.browser, self.context, self.page)
            logger.info(f"事件系统已设置完成 - {account_info}")
             
            # 主动发事件，便于外部UI初始化
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'浏览器初始化完成 - {account_info}'})
            self._emit('new_page', {'timestamp': datetime.now(), 'url': self.page.url, 'page_id': id(self.page)})
            logger.info(f"浏览器初始化完成事件已发送 - {account_info}")
        except Exception as e:
            logger.error(f"页面初始化失败: {str(e)} - {account_info}")
            self._emit('error', {'timestamp': datetime.now(), 'message': f'页面初始化失败: {str(e)} - {account_info}'})
            # 清理资源
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            raise

        try:
            # 应用指纹数据
            if self._fingerprint:
                self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在设置浏览器指纹... - {account_info}'})
                logger.info(f"正在应用指纹数据... - {account_info}")
                try:
                    # 注意：主要的指纹数据已经在_get_context_options中应用到浏览器上下文中
                    # 这里只需要补充应用一些可能需要在启动后设置的指纹数据
                    
                    # 使用统一的指纹提取函数设置HTTP头
                    from utils import extract_fingerprint_headers
                    extra_headers = extract_fingerprint_headers(self._fingerprint)
                    if extra_headers:
                        await self.context.set_extra_http_headers(extra_headers)  # type: ignore
                        logger.info(f"指纹HTTP头信息应用成功 - {account_info}")
                    
                    # 记录指纹应用情况
                    fingerprint_keys = list(self._fingerprint.keys())
                    logger.debug(f"已应用的指纹数据字段: {fingerprint_keys} - {account_info}")
                    
                except Exception as e:
                    logger.warning(f"应用指纹数据失败: {str(e)} - {account_info}")
                    self._emit('warning', {'timestamp': datetime.now(), 'message': f'应用指纹数据失败: {str(e)} - {account_info}'})

            # 导航
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在打开页面: {start_url} - {account_info}'})
            logger.info(f"正在导航到: {start_url} - {account_info}")
            async with self._nav_lock:
                await self.page.goto(start_url, wait_until='domcontentloaded', timeout=30000)
                logger.info(f"成功导航到页面: {start_url} - {account_info}")
            
            # 注入反检测脚本
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'正在注入反检测脚本... - {account_info}'})
            logger.info(f"正在注入反检测脚本... - {account_info}")
            await self._inject_stealth_scripts()
            logger.info(f"反检测脚本注入完成 - {account_info}")
            
            self._emit('browser_launch', {'timestamp': datetime.now(), 'message': f'页面加载完成 - {account_info}'})
            logger.info(f"浏览器启动流程全部完成 - {account_info}")
            
        except Exception as e:
            error_msg = f'页面加载失败: {str(e)} - {account_info}'
            logger.error(error_msg)
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
    def qiyong_liulanqi(self, executable_path: str, start_url: str, account_name: Optional[str] = None, cache_root: Optional[str] = None, account_id: Optional[int] = None, proxy: Optional[str] = None) -> None:
        # 导入日志模块
        import logging
        logger = logging.getLogger(__name__)
        
        # 构建账号信息用于日志
        account_info = f"账号: {account_name or '匿名'}" + (f" (ID: {account_id})" if account_id else "")
        logger.info(f"开始调用浏览器启动API - {account_info}")
        if proxy:
            logger.info(f"使用代理: {proxy} - {account_info}")
        
        try:
            future = self.run_async(self._async_start(executable_path, start_url, account_name, cache_root, account_id, proxy))
            try:
                # 等待异步操作完成，但设置超时时间为30秒
                logger.info(f"等待浏览器异步启动完成，超时时间: 30秒 - {account_info}")
                future.result(timeout=30)
                logger.info(f"浏览器API启动调用成功完成 - {account_info}")
            except asyncio.TimeoutError:
                logger.error(f"浏览器API启动调用超时 (30秒) - {account_info}")
                self._emit('error', {'timestamp': datetime.now(), 'message': f'启动浏览器超时 (30秒) - {account_info}'})
            except Exception as e:
                logger.error(f"浏览器API启动调用失败: {str(e)} - {account_info}")
                self._emit('error', {'timestamp': datetime.now(), 'message': f'启动浏览器失败: {str(e)} - {account_info}'})
        except Exception as e:
            logger.error(f"调用浏览器启动API时发生错误: {str(e)} - {account_info}")
            self._emit('error', {'timestamp': datetime.now(), 'message': f'启动浏览器API调用失败: {str(e)} - {account_info}'})

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
        # 移除重复和可能导致问题的参数
        args = [
            # 基础设置
            '--disable-blink-features=AutomationControlled',
            '--disable-features=VizDisplayCompositor',
            
            # 反检测参数
            '--disable-extensions',
            '--disable-plugins',
            # '--disable-images',  # 注释掉这行以启用图片加载
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            
            # 隐藏自动化标志
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-hang-monitor',
            '--disable-client-side-phishing-detection',
            
            # 性能优化
            '--disable-dev-shm-usage',
            '--no-sandbox',
            
            # 用户代理设置
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36',
            
            # 窗口设置
            '--window-size=1280,720',
            '--window-position=0,0',
        ]
        
        return args

    def _get_context_options(self, proxy: Optional[str] = None) -> dict:
        """获取浏览器上下文选项"""
        # 默认选项
        options = {
            'viewport': {'width': 1280, 'height': 720},
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
        
        # 如果有指纹数据，更新上下文选项
        if self._fingerprint:
            # 注意：窗口大小已固定为1280x720像素，不再从指纹数据中更新视口大小
            
            # 更新用户代理
            if 'user_agent' in self._fingerprint:
                options['user_agent'] = self._fingerprint['user_agent']
            
            # 更新时区 - 注意：Playwright需要标准的IANA时区ID
            if 'timezone' in self._fingerprint:
                timezone = self._fingerprint['timezone']
                # 处理常见的非标准时区ID
                if timezone == 'Asia/Beijing':
                    timezone = 'Asia/Shanghai'  # 转换为标准IANA时区ID
                options['timezone_id'] = timezone
            
            # 更新语言
            if 'language' in self._fingerprint:
                # 提取主要语言用于locale
                main_language = self._fingerprint['language'].split(',')[0].split(';')[0]
                options['locale'] = main_language
                options['extra_http_headers']['Accept-Language'] = self._fingerprint['language']
            
            # 更新设备内存
            if 'device_memory' in self._fingerprint:
                options['device_scale_factor'] = self._fingerprint['device_memory'] / 4.0  # 近似转换
            
            # 更新硬件并发 - 注意：Playwright不支持直接设置hardware_concurrency参数
            # 如果需要模拟这个特性，我们会在JavaScript脚本中处理
            
            # 更新触摸屏支持
            if 'max_touch_points' in self._fingerprint:
                options['has_touch'] = self._fingerprint['max_touch_points'] > 0
        
        # 如果有代理设置，添加到上下文选项
        if proxy:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"正在配置代理: {proxy}")
            options['proxy'] = {
                'server': proxy if '://' in proxy else f'http://{proxy}',
                'bypass': '<-loopback>'  # 绕过本地地址
            }
        
        return options

    async def _inject_stealth_scripts(self):
        """注入反检测脚本"""
        try:
            from .stealth_scripts import get_stealth_script
            
            # 基础反检测脚本
            stealth_script = get_stealth_script("hide_webdriver") + "\n" + get_stealth_script("hide_automation")
            
            # 如果有指纹数据，注入更多与指纹相关的脚本
            if self._fingerprint:
                # 注入修改Canvas指纹的脚本
                stealth_script += "\n" + get_stealth_script("modify_canvas")
                
                # 注入修改音频指纹的脚本
                stealth_script += "\n" + get_stealth_script("modify_audio")
                
                # 注入修改WebRTC的脚本
                stealth_script += "\n" + get_stealth_script("modify_webrtc")
                
                # 注入用户行为模拟脚本
                stealth_script += "\n" + get_stealth_script("simulate_user")
                
                # 自定义脚本：强制设置固定的屏幕信息为1280x720
                # 注意：无论指纹数据中包含什么屏幕信息，我们都强制使用固定的尺寸
                color_depth = self._fingerprint.get('color_depth', 24)
                
                custom_screen_script = f"""
                // 强制设置固定的屏幕信息（1280x720）
                Object.defineProperty(screen, 'width', {{
                    get: () => 1280,
                }});
                Object.defineProperty(screen, 'height', {{
                    get: () => 720,
                }});
                Object.defineProperty(screen, 'availWidth', {{
                    get: () => 1280,
                }});
                Object.defineProperty(screen, 'availHeight', {{
                    get: () => 680, // 减去任务栏高度
                }});
                Object.defineProperty(screen, 'colorDepth', {{
                    get: () => {color_depth},
                }});
                Object.defineProperty(screen, 'pixelDepth', {{
                    get: () => {color_depth},
                }});
                """
                stealth_script += "\n" + custom_screen_script
                
                # 自定义脚本：设置WebGL信息
                if 'webgl_vendor' in self._fingerprint and 'webgl_renderer' in self._fingerprint:
                    webgl_vendor = self._fingerprint['webgl_vendor']
                    webgl_renderer = self._fingerprint['webgl_renderer']
                    
                    custom_webgl_script = f"""
                    // 根据指纹数据设置WebGL信息
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                            return '{webgl_vendor}';
                        }}
                        if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                            return '{webgl_renderer}';
                        }}
                        return getParameter.apply(this, arguments);
                    }};
                    """
                    stealth_script += "\n" + custom_webgl_script
                
                # 自定义脚本：Windows特有指纹信息
                if 'windows_specific' in self._fingerprint:
                    windows_specific = self._fingerprint['windows_specific']
                    
                    # 计算性能相关的值
                    device_memory = self._fingerprint.get('device_memory', 8)
                    total_memory = device_memory * 1024 * 1024 * 1024
                    used_memory = random.randint(1, device_memory) * 1024 * 1024 * 1024 // 2
                    startup_time = random.randint(500, 3000)
                    total_disk = random.randint(256, 2048) * 1024 * 1024 * 1024
                    free_disk = random.randint(10, device_memory * 100) * 1024 * 1024 * 1024
                    hardware_concurrency = self._fingerprint.get('hardware_concurrency', 4)
                    
                    custom_windows_script = f"""
                    // Windows特有指纹信息
                    Object.defineProperty(navigator, 'platform', {{
                        get: () => 'Win32',
                        configurable: true
                    }});
                    
                    // 模拟Windows系统的额外特性
                    if (!window.navigator.win) {{
                        Object.defineProperty(window.navigator, 'win', {{
                            value: {{
                                deviceId: '{windows_specific.get('device_id', '')}',
                                osBuild: '{windows_specific.get('os_build', '')}',
                                defenderStatus: '{windows_specific.get('defender_status', 'enabled')}',
                                edgeVersion: '{windows_specific.get('edge_version', '')}'
                            }},
                            configurable: true
                        }});
                    }}
                    
                    // 模拟Windows特有的硬件信息
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: () => {hardware_concurrency},
                        configurable: true
                    }});
                    
                    // 模拟Windows系统特有的性能特性
                    Object.defineProperty(window, 'WindowsPerformanceInfo', {{
                        value: {{
                            memory: {{ totalJSHeapSize: {total_memory}, usedJSHeapSize: {used_memory} }},
                            deviceMemory: {device_memory},
                            // 增加Windows特有的性能指标
                            startupTime: {startup_time},
                            diskSpace: {{ total: {total_disk}, free: {free_disk} }}
                        }},
                        configurable: true
                    }});
                    """
                    stealth_script += "\n" + custom_windows_script
                
                # 自定义脚本：设置时区
                if 'timezone' in self._fingerprint:
                    # 这里可以添加根据时区计算时差的逻辑
                    # 目前我们保持原有设置
                    stealth_script += "\n" + get_stealth_script("modify_timezone")
            
            # 注入脚本
            await self.page.add_init_script(stealth_script)
            
            # 减少等待时间
            await self.page.wait_for_timeout(500)
        except Exception as e:
            self._emit('warning', {'timestamp': datetime.now(), 'message': f'注入反检测脚本失败: {str(e)}'})


