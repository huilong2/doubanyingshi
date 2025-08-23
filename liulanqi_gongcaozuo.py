"""
浏览器公共操作模块
使用新模块的API实现浏览器相关功能
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from pathlib import Path

# 导入新模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'liulanqimokuai'))

from browser_core import BrowserController
from mokuai_ipdingwei import get_ip_location

# 导入全局变量
from bianlian_dingyi import DOUBAN_URL, DEFAULT_BROWSER_TIMEOUT, DEFAULT_PAGE_TIMEOUT

logger = logging.getLogger(__name__)

@dataclass
class LiulanqiPeizhi:
    """浏览器配置数据类"""
    zhanghao: str  # 账号
    mima: Optional[str] = None  # 密码
    daili: Optional[str] = None  # 代理服务器地址
    wangzhi: str = DOUBAN_URL  # 默认启动网址
    huanchunlujing: Optional[str] = None  # 缓存路径open_browser
    chrome_path: Optional[str] = None  # Chrome浏览器可执行文件路径
    fingerprint: Optional[Dict[str, Any]] = None  # 浏览器指纹

    def __post_init__(self):
        """初始化后处理，转换路径格式"""
        if self.chrome_path:
            logger.info(f"Chrome浏览器路径: {self.chrome_path}")
            self.chrome_path = str(Path(self.chrome_path))

class LiulanqiGongcaozuo:
    """浏览器公共操作类 - 使用新模块API"""
    
    def __init__(self, peizhi: LiulanqiPeizhi, browser_signals: Optional[Any] = None, 
                 db_manager: Optional[Any] = None, stop_event: Optional[Any] = None):
        """
        初始化浏览器操作类
        
        Args:
            peizhi: 浏览器配置对象
            browser_signals: 用于UI通信的信号对象
            db_manager: 数据库管理器对象
            stop_event: 用于外部停止信号的 threading.Event 对象
        """
        self.peizhi = peizhi
        self.browser_signals = browser_signals
        self.db_manager = db_manager
        self.stop_event = stop_event
        
        # 新模块组件
        self.controller = BrowserController()
        
        # 状态管理
        self._is_closed = False
        self._browser_status = "未启动"
        self._main_window = None
        self._ui_callback = None
        
        # 从账号目录加载指纹数据
        if self.peizhi.huanchunlujing:
            from utils import ensure_account_fingerprint
            fingerprint = ensure_account_fingerprint(self.peizhi.zhanghao)
            if fingerprint:
                self.peizhi.fingerprint = fingerprint
        
        # 设置事件监听
        self._setup_event_listeners()
    
    def set_ui_callback(self, callback):
        """设置UI更新回调函数"""
        self._ui_callback = callback

    def set_main_window(self, window):
        """设置主窗口引用"""
        self._main_window = window

    def update_status(self, status):
        """更新浏览器状态"""
        self._browser_status = status
        if self._ui_callback:
            self._ui_callback("status", status)

    def log_event(self, event_type, event_data, detailed_data=None):
        """记录浏览器事件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_data = {
            "timestamp": timestamp,
            "type": event_type,
            "data": event_data,
            "details": detailed_data
        }
        if self._ui_callback:
            self._ui_callback("event", log_data)
        logger.info(f"浏览器事件: {event_type} - {event_data}")

    def _setup_event_listeners(self):
        """设置事件监听器"""
        # 监听浏览器启动事件
        self.controller.on('browser_launch', lambda data: self.log_event("browser", "浏览器启动成功"))
        
        # 监听浏览器关闭事件
        self.controller.on('browser_close', lambda data: self._handle_browser_close())
        
        # 监听浏览器断开连接事件
        self.controller.on('browser_disconnected', lambda data: self._handle_browser_disconnected())

        # 监听上下文关闭（所有标签页关闭）
        self.controller.on('context_close', lambda data: self._handle_browser_close())
        
        # 监听页面加载事件
        self.controller.on('page_load', lambda data: self.log_event("page", "页面加载完成"))
        
        # 监听URL变化事件
        self.controller.on('url_change', lambda data: self.log_event("page", f"URL变化: {data.get('url', '')}"))
        
        # 监听错误事件
        self.controller.on('error', lambda data: self.log_event("error", data.get('message', '')))

        # 监听标签关闭：若所有标签关闭，则视为浏览器关闭
        def _on_page_closed(_data: dict):
            try:
                context = getattr(self.controller, 'context', None)
                if not context:
                    return
                remaining = []
                try:
                    remaining = list(context.pages)
                except Exception:
                    remaining = []
                if len(remaining) == 0:
                    self._handle_browser_close()
            except Exception:
                pass
        self.controller.on('page_closed', _on_page_closed)

    def _handle_browser_disconnected(self):
        """处理浏览器断开连接事件"""
        if not self._is_closed:
            logger.info(f"检测到浏览器断开连接事件 - 用户: {self.peizhi.zhanghao}")
            self.log_event("browser", "浏览器断开连接")
            self._is_closed = True
            self.update_status("已断开连接")
            
            # 更新数据库中的运行状态
            if self.db_manager:
                self._update_account_status('已断开连接')
            
            # 发送信号通知主界面更新账号状态
            if self.browser_signals:
                self.browser_signals.info.emit(f"浏览器 {self.peizhi.zhanghao} 已断开连接")
                self.browser_signals.account_closed.emit(self.peizhi.zhanghao)

    def _handle_browser_close(self):
        """处理浏览器关闭事件"""
        if not self._is_closed:
            logger.info(f"检测到浏览器关闭事件 - 用户: {self.peizhi.zhanghao}")
            self._is_closed = True
            self.update_status("已关闭")
            
            # 更新数据库中的运行状态
            if self.db_manager:
                self._update_account_status('已关闭')
            
            # 发送信号通知主界面更新账号状态
            if self.browser_signals:
                self.browser_signals.info.emit(f"浏览器 {self.peizhi.zhanghao} 已关闭")
                self.browser_signals.account_closed.emit(self.peizhi.zhanghao)

    def _update_account_status(self, status):
        """更新数据库中的账号状态"""
        try:
            if self.db_manager:
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == self.peizhi.zhanghao:
                        # 使用工具类创建标准化的账号数据
                        from douban_utils import DoubanUtils
                        account_data = DoubanUtils.create_account_data(
                            account, None, account[3], status
                        )
                        self.db_manager.update_account(account[0], account_data)
                        break
        except Exception as e:
            logger.error(f"更新账号状态失败: {str(e)}")

    async def chushihua(self) -> None:
        """初始化浏览器"""
        try:
            logger.info("开始初始化浏览器...")
            
            # 重置关闭状态
            self._is_closed = False
            
            # 若已有残留实例，先尝试关闭，避免重复启动失败
            try:
                if getattr(self.controller, 'browser', None):
                    logger.info("检测到残留浏览器实例，尝试先关闭...")
                    self.controller.guanbi_liulanqi()
                    await asyncio.sleep(0.5)
            except Exception as _e:
                logger.debug(f"关闭残留实例时忽略错误: {_e}")
            
            # 创建用户数据目录
            if self.peizhi.huanchunlujing:
                user_data_dir = Path(self.peizhi.huanchunlujing)
                user_data_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建用户数据目录: {user_data_dir}")
            
            # 使用新模块启动浏览器
            start_url = self.peizhi.wangzhi
            executable_path = self.peizhi.chrome_path
            account_name = self.peizhi.zhanghao
            cache_root = self.peizhi.huanchunlujing
            
            # 如果Chrome路径为空，让新模块自动查找
            if not executable_path:
                executable_path = self._find_chrome_path()
            
            # 启动浏览器（使用新模块的拼音API）
            self.controller.qiyong_liulanqi(
                executable_path=executable_path,
                start_url=start_url,
                account_name=account_name,
                cache_root=cache_root
            )
            
            # 智能等待浏览器启动完成 - 等待页面对象可用
            await self._wait_for_browser_ready()
            
            # 检查浏览器是否成功启动
            if not self.controller.browser:
                raise Exception("浏览器启动失败")
            
            # 检查context是否可用
            if not self.controller.context:
                raise Exception("浏览器上下文启动失败")
            
            # 应用指纹数据
            if self.peizhi.fingerprint:
                await self._apply_fingerprint(self.peizhi.fingerprint)
            
            # 更新状态
            self.update_status("已启动")
            
            logger.info("浏览器初始化成功")
            
        except Exception as e:
            error_msg = f"浏览器初始化失败: {str(e)}"
            logger.error(error_msg)
            self.update_status("初始化失败")
            raise

    async def _wait_for_browser_ready(self, timeout: int = DEFAULT_BROWSER_TIMEOUT):
        """智能等待浏览器准备就绪"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if (self.controller.browser and 
                self.controller.context and 
                self.controller.page):
                logger.info("浏览器已准备就绪")
                return
            await asyncio.sleep(0.1)
        
        raise Exception(f"浏览器启动超时 ({timeout}秒)")

    async def dakai_ye(self, url: Optional[str] = None) -> None:
        """
        打开指定网页
        
        Args:
            url: 要打开的网址，如果不指定则使用配置中的默认网址
        """
        if self._is_closed:
            return
            
        target_url = url or self.peizhi.wangzhi
        
        try:
            logger.info(f"正在打开页面: {target_url}")
            
            # 使用新模块导航到页面（使用拼音API）
            self.controller.tiaozhuan_url(target_url)
            
            # 针对豆瓣网站的特殊检测
            if "douban.com" in target_url:
                await self._check_douban_status()
            
            logger.info("页面打开成功")
            
        except Exception as e:
            error_msg = f"打开页面失败: {str(e)}"
            logger.error(error_msg)
            raise

    async def _check_douban_status(self):
        """检查豆瓣网站状态"""
        try:
            # 智能等待页面加载完成 - 等待关键元素出现
            await self._wait_for_douban_page_ready()
            
            # 检查登录状态
            login_status_future = self.controller.run_async(self.controller.page.evaluate("""
                () => {
                    const userAccount = document.querySelector('.nav-user-account') ||
                                      document.querySelector('.user-info');
                    return userAccount ? '已登录' : '未登录';
                }
            """))
            
            # 等待结果
            login_status = login_status_future.result(timeout=DEFAULT_BROWSER_TIMEOUT)
            logger.info(f"豆瓣登录状态: {login_status}")
            
            # 获取用户信息
            user_info = await self._get_douban_user_info()
            if user_info:
                logger.info(f"获取到用户数据: {user_info}")
                
                # 更新数据库
                if self.db_manager:
                    self._update_douban_account_info(user_info, login_status)
            
        except Exception as e:
            logger.error(f"检查豆瓣状态失败: {str(e)}")

    async def _wait_for_douban_page_ready(self, timeout: int = DEFAULT_BROWSER_TIMEOUT):
        """智能等待豆瓣页面准备就绪"""
        try:
            # 等待页面基本加载完成
            await self.controller.page.wait_for_load_state('domcontentloaded', timeout=timeout * 1000)
            
            # 等待关键元素出现（登录按钮或用户信息）
            try:
                # 尝试等待登录按钮（未登录状态）
                await self.controller.page.wait_for_selector('.nav-login', timeout=DEFAULT_PAGE_TIMEOUT)
                logger.info("检测到未登录状态")
            except:
                try:
                    # 尝试等待用户信息（已登录状态）
                    await self.controller.page.wait_for_selector('.nav-user-account, .user-info', timeout=DEFAULT_PAGE_TIMEOUT)
                    logger.info("检测到已登录状态")
                except:
                    # 如果都找不到，至少等待body元素
                    await self.controller.page.wait_for_selector('body', timeout=2000)
                    logger.info("页面基本加载完成")
            
        except Exception as e:
            logger.warning(f"等待页面元素超时，继续执行: {e}")
            # 即使超时也继续执行，不阻塞流程

    async def _get_douban_user_info(self) -> Optional[Dict[str, Any]]:
        """获取豆瓣用户信息"""
        try:
            # 使用统一的用户信息获取脚本
            from douban_utils import DoubanUtils
            user_info_future = self.controller.run_async(self.controller.page.evaluate(DoubanUtils.get_user_info_script()))
            # 等待结果
            user_info = user_info_future.result(timeout=DEFAULT_BROWSER_TIMEOUT)
            return user_info
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return None

    def _update_douban_account_info(self, user_info: Dict[str, Any], login_status: str):
        """更新豆瓣账号信息到数据库"""
        try:
            if self.db_manager:
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == self.peizhi.zhanghao:
                        # 创建用户信息字典用于数据库更新
                        user_info_for_db = {
                            'login_status': login_status,
                            'name': user_info.get('name'),
                            'id': user_info.get('id')
                        }
                        
                        # 使用工具类创建标准化的账号数据
                        from douban_utils import DoubanUtils
                        account_data = DoubanUtils.create_account_data(
                            account, user_info_for_db, account[3], account[10]
                        )
                        self.db_manager.update_account(account[0], account_data)
                        
                        if self.browser_signals:
                            self.browser_signals.info.emit("账号信息已更新")
                        break
        except Exception as e:
            logger.error(f"更新账号信息失败: {str(e)}")

    async def zhixing_script(self, script: str) -> Any:
        """
        在页面中执行JavaScript脚本
        
        Args:
            script: 要执行的JavaScript代码
            
        Returns:
            脚本执行结果
        """
        if self._is_closed:
            raise Exception("浏览器已关闭")
            
        try:
            # 使用新模块的事件循环执行脚本，并等待结果
            future = self.controller.run_async(self.controller.page.evaluate(script))
            return future.result(timeout=10)  # 等待最多10秒
        except Exception as e:
            if not self._is_closed:
                raise Exception(f"执行脚本失败: {str(e)}")

    async def guanbi(self):
        """关闭浏览器"""
        try:
            if self._is_closed:
                logger.info("浏览器已经关闭")
                return

            logger.info("开始关闭浏览器...")
            self._is_closed = True

            # 使用新模块关闭浏览器（使用拼音API）
            self.controller.guanbi_liulanqi()

            logger.info("浏览器关闭完成")
            # 将底层引用清空，避免二次启动拿到过期对象
            try:
                setattr(self.controller, 'page', None)
                setattr(self.controller, 'context', None)
                setattr(self.controller, 'browser', None)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {str(e)}")

    async def huoqu_zhinwen(self) -> Dict[str, Any]:
        """
        获取当前账号配置中保存的指纹数据
        
        Returns:
            Dict[str, Any]: 包含浏览器指纹信息的字典
        """
        try:
            if not self.peizhi.fingerprint:
                raise Exception("该账号未保存指纹数据")
            
            # 返回配置中保存的指纹数据
            fingerprint_data = {
                'fingerprint': self.peizhi.fingerprint,
                'config': {
                    'proxy': self.peizhi.daili,
                    'user_data_dir': self.peizhi.huanchunlujing,
                    'chrome_path': self.peizhi.chrome_path
                }
            }
            
            logger.info("成功获取指纹数据")
            return fingerprint_data
            
        except Exception as e:
            error_msg = f"获取指纹数据失败: {str(e)}"
            logger.error(error_msg)
            raise

    async def _apply_fingerprint(self, fingerprint: Dict[str, Any]) -> None:
        """应用指纹数据"""
        try:
            if not isinstance(fingerprint, dict):
                logger.error("指纹数据格式错误：不是字典类型")
                return

            # 检查浏览器是否已启动
            if not self.controller.browser or not self.controller.context:
                logger.warning("浏览器未启动，跳过指纹应用")
                return

            # 使用统一的指纹提取函数
            try:
                from utils import extract_fingerprint_headers
                extra_headers = extract_fingerprint_headers(fingerprint)
                
                if extra_headers and self.controller.context:
                    self.controller.run_async(self.controller.context.set_extra_http_headers(extra_headers))
            except Exception as e:
                logger.error(f"应用指纹数据失败: {str(e)}")

            # 注入指纹脚本
            fingerprint_script = """
                (function() {
                    // 指纹数据已注入到页面
                    window.fingerprint_data = %s;
                })();
            """ % json.dumps(fingerprint)

            try:
                if self.controller.page:
                    self.controller.run_async(self.controller.page.evaluate(fingerprint_script))
            except Exception as e:
                logger.error(f"注入指纹脚本失败: {str(e)}")

            # 设置地理位置
            if self.peizhi.daili and 'latitude' in fingerprint and 'longitude' in fingerprint:
                try:
                    if self.controller.page:
                        self.controller.run_async(self.controller.page.set_geolocation({
                            'latitude': float(fingerprint['latitude']),
                            'longitude': float(fingerprint['longitude'])
                        }))
                except Exception as e:
                    logger.error(f"设置地理位置失败: {str(e)}")

            logger.info("指纹数据应用成功")
        except Exception as e:
            logger.error(f"应用指纹数据失败: {str(e)}")
            raise

    def get_browser_status(self) -> str:
        """获取浏览器状态"""
        return self._browser_status

    def is_closed(self) -> bool:
        """检查浏览器是否已关闭"""
        return self._is_closed

    # 兼容旧调用：暴露只读属性供外部获取底层对象
    @property
    def page(self):
        return getattr(self.controller, 'page', None)

    @property
    def context(self):
        return getattr(self.controller, 'context', None)

    @property
    def browser(self):
        return getattr(self.controller, 'browser', None)

    def _find_chrome_path(self) -> str:
        """自动查找Chrome浏览器路径"""
        import platform
        import os
        
        system = platform.system()
        
        if system == "Windows":
            # Windows常见的Chrome安装路径
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    logger.info(f"找到Chrome浏览器: {path}")
                    return path
                    
        elif system == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    logger.info(f"找到Chrome浏览器: {path}")
                    return path
                    
        else:  # Linux
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    logger.info(f"找到Chrome浏览器: {path}")
                    return path
        
        # 如果找不到，返回空字符串，让Playwright使用系统默认
        logger.warning("未找到Chrome浏览器，将使用系统默认浏览器")
        return ""

# 使用示例
async def shili():
    # 创建配置
    peizhi = LiulanqiPeizhi(
        zhanghao="test_user",
        daili="http://proxy.example.com:8080",
        wangzhi="https://www.douban.com",
        huanchunlujing="./cache/test_user",
        chrome_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
        fingerprint={
            'screen_width': 1280,
            'screen_height': 800,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'language': 'zh-CN',
            'timezone': 'Asia/Shanghai',
            'webgl_vendor': 'Intel',
            'webgl_renderer': 'Intel(R) HD Graphics 530'
        }
    )
    
    # 创建浏览器操作实例
    liulanqi = LiulanqiGongcaozuo(peizhi)
    
    try:
        # 初始化浏览器
        await liulanqi.chushihua()
        
        # 打开页面
        await liulanqi.dakai_ye()
        
        # 执行脚本
        result = await liulanqi.zhixing_script("document.title")
        print(f"页面标题: {result}")
        
    finally:
        # 关闭浏览器
        await liulanqi.guanbi()

if __name__ == "__main__":
    asyncio.run(shili())
