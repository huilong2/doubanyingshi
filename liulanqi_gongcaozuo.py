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

from liulanqimokuai.browser_core import BrowserController
from liulanqimokuai.mokuai_ipdingwei import get_ip_location

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
        
        # 日志去抖状态
        import time
        self._last_log_ms = {}
        self._monotonic_ms = lambda: int(time.monotonic() * 1000)
        def _should_log(key: str, interval_ms: int = 800) -> bool:
            now = self._monotonic_ms()
            last = self._last_log_ms.get(key, 0)
            if now - last >= interval_ms:
                self._last_log_ms[key] = now
                return True
            return False
        self._should_log = _should_log
        
        # 用户信息获取状态（防止重复获取）
        self._user_info_fetched = False
        self._user_info_fetching = False
        
        # 从账号目录加载指纹数据
        if self.peizhi.huanchunlujing:
            from utils import ensure_account_fingerprint
            # 获取账号ID
            account_id = None
            if self.db_manager:
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == self.peizhi.zhanghao:  # account[1]是用户名
                        account_id = account[0]  # account[0]是ID
                        break
            fingerprint = ensure_account_fingerprint(account_id)
            if fingerprint:
                self.peizhi.fingerprint = fingerprint
            self._account_id = account_id  # 保存account_id供后续使用
        
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
        
        # 监听页面加载事件（按需触发一次用户信息获取）
        def _on_page_load(data):
            if self._should_log("page_load", 800):
                self.log_event("page", "页面加载完成")
            # 仅当未获取成功且当前不在获取中时触发
            if not self._user_info_fetched and not self._user_info_fetching:
                self._user_info_fetching = True
                try:
                    future = self.controller.run_async(self._get_douban_user_info())
                    def _done(f):
                        try:
                            user_info = f.result()
                            if user_info:
                                login_status = user_info.get('login_status') or ('已登录' if (user_info.get('id') or user_info.get('name')) else '未登录')
                                if login_status == '已登录' and (user_info.get('id') or user_info.get('name')):
                                    self._user_info_fetched = True
                                    logger.info(f"页面加载后获取到用户数据: {user_info}")
                                    if self.db_manager:
                                        # 使用异步回调更新账号信息
                                        self._schedule_account_update(user_info, login_status)
                        except Exception as e:
                            logger.warning(f"页面加载后获取账号信息失败: {str(e)}")
                        finally:
                            self._user_info_fetching = False
                    future.add_done_callback(_done)
                except Exception as e:
                    logger.warning(f"调度获取账号信息失败: {str(e)}")
                    self._user_info_fetching = False
        self.controller.on('page_load', _on_page_load)
        
        # 监听URL变化事件
        def _on_url_change(data):
            url = data.get('new_url') or data.get('url', '')
            if self._should_log("url_change", 500):
                self.log_event("page", f"URL变化: {url}")
        self.controller.on('url_change', _on_url_change)
        
        # 监听错误事件
        self.controller.on('error', lambda data: self.log_event("error", data.get('message', '')))
        
        # 监听标签关闭：若所有标签关闭，则视为浏览器关闭
        def _on_page_closed(_data: dict):
            # 如果浏览器已关闭，停止处理事件
            if self._is_closed:
                return
                
            try:
                context = getattr(self.controller, 'context', None)
                if not context:
                    return
                import asyncio
                loop = asyncio.get_event_loop()
                def check_remaining_pages():
                    try:
                        # 再次检查浏览器是否已关闭
                        if self._is_closed:
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
                loop.call_later(0.5, check_remaining_pages)
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

    def _schedule_account_update(self, user_info, login_status):
        """调度异步更新账号信息"""
        try:
            if self.controller and hasattr(self.controller, '_loop'):
                logger.info(f"开始调度账号信息更新: {login_status}")
                # 使用控制器的事件循环执行异步更新
                import asyncio
                future = asyncio.run_coroutine_threadsafe(
                    self._update_douban_account_info(user_info, login_status), 
                    self.controller._loop
                )
                # 减少超时时间到5秒，避免长时间阻塞
                result = future.result(timeout=5)
                logger.info(f"账号信息更新完成: {result if result else '无返回值'}")
            else:
                logger.warning("控制器事件循环不可用，无法更新账号信息")
        except asyncio.TimeoutError:
            logger.error("账号信息更新超时（5秒），可能卡住了")
        except Exception as e:
            logger.error(f"调度账号信息更新失败: {str(e)}")
            # 打印详细的异常信息
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

    def _update_account_status(self, status, keep_cookie=True):
        """更新数据库中的账号状态
        
        Args:
            status: 新的运行状态
            keep_cookie: 是否保留现有的cookie值
        """
        try:
            if self.db_manager:
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == self.peizhi.zhanghao:
                        # 如果不保留cookie，或者账号状态为未登录，则将cookie设置为空字符串
                        # 这里通过账号状态列(account[6])判断登录状态
                        login_status = account[6] if len(account) > 6 else "未知"
                        cookie_value = account[3] if (keep_cookie and login_status != "未登录") else ""
                        
                        # 使用工具类创建标准化的账号数据
                        from douban_utils import DoubanUtils
                        account_data = DoubanUtils.create_account_data(
                            account, None, cookie_value, status
                        )
                        
                        # 确保登录状态正确更新
                        account_data['login_status'] = login_status
                        
                        self.db_manager.update_account(account[0], account_data)
                        break
        except Exception as e:
            logger.error(f"更新账号状态失败: {str(e)}")

    async def chushihua(self) -> None:
        """初始化浏览器 - 增强版，确保资源完全释放"""
        try:
            # 记录账号信息
            account_info = f"账号: {self.peizhi.zhanghao}" + (f" (ID: {getattr(self, '_account_id', '未知')})" if hasattr(self, '_account_id') else "")
            logger.info(f"开始初始化浏览器... {account_info}")
            self.log_event("信息", f"开始初始化浏览器... {account_info}")
            
            # 1. 首先尝试终止所有可能残留的Chrome进程
            self._terminate_orphaned_chrome_processes()
            logger.info("已尝试终止残留的Chrome进程")
            
            # 重置关闭状态
            self._is_closed = False
            
            # 2. 若已有残留实例，先尝试关闭，避免重复启动失败
            try:
                if hasattr(self, 'controller') and getattr(self.controller, 'browser', None):
                    logger.info("检测到残留浏览器实例，尝试先关闭...")
                    self.controller.guanbi_liulanqi()
                    await asyncio.sleep(0.5)
            except Exception as _e:
                logger.debug(f"关闭残留实例时忽略错误: {_e}")
            
            # 3. 强制清理可能的循环引用
            import gc
            gc.collect()
            logger.debug("已执行垃圾回收")
            
            # 4. 创建用户数据目录
            if self.peizhi.huanchunlujing:
                user_data_dir = Path(self.peizhi.huanchunlujing)
                user_data_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建用户数据目录: {user_data_dir}")
            
            # 5. 浏览器启动增强：添加重试机制
            max_retries = 3
            retry_count = 0
            browser_started = False
            
            while retry_count < max_retries and not browser_started:
                try:
                    retry_count += 1
                    logger.info(f"浏览器初始化尝试 {retry_count}/{max_retries} - {account_info}")
                    
                    # 使用新模块启动浏览器
                    start_url = self.peizhi.wangzhi
                    executable_path = self.peizhi.chrome_path
                    account_name = self.peizhi.zhanghao
                    cache_root = self.peizhi.huanchunlujing
                    
                    # 记录详细的启动参数
                    logger.info(f"浏览器启动参数: 路径={executable_path}, 启动URL={start_url}, 缓存目录={cache_root}")
                    
                    # 如果Chrome路径为空，让新模块自动查找
                    if not executable_path:
                        executable_path = self._find_chrome_path()
                        logger.info(f"自动检测到浏览器路径: {executable_path}")
                    
                    # 启动浏览器（使用新模块的拼音API）
                    logger.info(f"正在启动Chrome浏览器... 路径: {executable_path}")
                    self.controller.qiyong_liulanqi(
                        executable_path=executable_path,
                        start_url=start_url,
                        account_name=account_name,
                        cache_root=cache_root,
                        account_id=getattr(self, '_account_id', None),
                        proxy=self.peizhi.daili  # 传递代理配置
                    )
                    
                    # 智能等待浏览器启动完成 - 等待页面对象可用
                    await self._wait_for_browser_ready()
                    
                    # 检查浏览器是否成功启动
                    if not self.controller.browser:
                        raise Exception("浏览器启动失败")
                    
                    # 检查context是否可用
                    if not self.controller.context:
                        raise Exception("浏览器上下文启动失败")
                    
                    browser_started = True
                    logger.info(f"浏览器初始化成功 (尝试 {retry_count}/{max_retries}) - {account_info}")
                    self.log_event("成功", f"浏览器初始化成功 - {account_info}")
                    
                except Exception as retry_err:
                    logger.warning(f"浏览器初始化尝试 {retry_count}/{max_retries} 失败: {str(retry_err)} - {account_info}")
                    # 清理失败的实例引用
                    if hasattr(self, 'controller'):
                        try:
                            if hasattr(self.controller, 'guanbi_liulanqi'):
                                self.controller.guanbi_liulanqi()
                        except:
                            pass
                    # 重试前等待1秒
                    if retry_count < max_retries:
                        logger.info(f"{retry_count}秒后将进行第 {retry_count+1} 次尝试...")
                        await asyncio.sleep(1)
            
            if not browser_started:
                error_msg = f"浏览器初始化失败，已尝试 {max_retries} 次 - {account_info}"
                logger.error(error_msg)
                self.log_event("错误", error_msg)
                raise Exception(error_msg)
            
            # 应用指纹数据
            if self.peizhi.fingerprint:
                logger.info(f"正在应用指纹数据 - {account_info}")
                await self._apply_fingerprint(self.peizhi.fingerprint)
            
            # 更新状态
            self.update_status("已启动")
            logger.info(f"浏览器流程已完成初始化 - {account_info}")
            
        except Exception as e:
            error_msg = f"浏览器初始化失败: {str(e)} - {account_info if 'account_info' in locals() else '未知账号'}"
            logger.error(error_msg)
            self.update_status("初始化失败")
            # 确保清理资源
            await self._cleanup_resources()
            raise
    
    def _terminate_orphaned_chrome_processes(self):
        """终止所有可能的孤立Chrome进程"""
        try:
            import psutil
            logger.info("开始清理孤立的Chrome进程")
            
            # 获取所有Chrome进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in proc.name().lower():
                        # 检查是否有我们的用户数据目录标记
                        cmdline = ' '.join(proc.cmdline() or [])
                        if hasattr(self.peizhi, 'huanchunlujing') and self.peizhi.huanchunlujing and self.peizhi.huanchunlujing in cmdline:
                            logger.info(f"终止孤立的Chrome进程: PID={proc.pid}, 命令行={cmdline}")
                            proc.terminate()
                            # 等待进程终止，最多等待2秒
                            try:
                                proc.wait(timeout=2)
                            except psutil.TimeoutExpired:
                                logger.warning(f"强制终止进程: PID={proc.pid}")
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            logger.info("孤立Chrome进程清理完成")
        except ImportError:
            logger.warning("psutil库未安装，无法自动清理Chrome进程")
        except Exception as e:
            logger.error(f"清理Chrome进程时出错: {str(e)}")
    
    async def _cleanup_resources(self):
        """清理所有浏览器相关资源"""
        try:
            if hasattr(self, 'controller') and self.controller:
                if hasattr(self.controller, 'browser'):
                    self.controller.browser = None
                if hasattr(self.controller, 'context'):
                    self.controller.context = None
                if hasattr(self.controller, 'page'):
                    self.controller.page = None
                if hasattr(self.controller, 'playwright'):
                    self.controller.playwright = None
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")
    
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
            
            # 使用异步方式导航到页面并等待完成
            future = self.controller.run_async(self.controller.page.goto(target_url, wait_until='domcontentloaded'))
            try:
                future.result(timeout=DEFAULT_BROWSER_TIMEOUT)
            except Exception as e:
                logger.warning(f"页面导航超时，但继续执行: {e}")
            
            # 确保页面对象有效
            if not self.controller.page or self.controller.page.is_closed():
                logger.warning("页面已关闭或无效，无法进行后续操作")
                return
            
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
            
            # 确保页面对象仍然有效
            if not self.controller.page or self.controller.page.is_closed():
                logger.warning("页面已关闭，无法检查登录状态")
                return
            
            # 检查登录状态
            login_status_future = self.controller.run_async(self.controller.page.evaluate("""
                () => {
                    const userAccount = document.querySelector('.nav-user-account') ||
                                      document.querySelector('.user-info');
                    return userAccount ? '已登录' : '未登录';
                }
            """))
            
            # 等待结果
            try:
                login_status = login_status_future.result(timeout=DEFAULT_BROWSER_TIMEOUT)
            except Exception as e:
                logger.error(f"获取登录状态失败: {str(e)}")
                return
            logger.info(f"豆瓣登录状态: {login_status}")
            
            # 获取用户信息
            user_info_future = self.controller.run_async(self._get_douban_user_info())
            try:
                user_info = user_info_future.result(timeout=DEFAULT_BROWSER_TIMEOUT)
                if user_info:
                    logger.info(f"获取到用户数据: {user_info}")
                    
                    # 更新数据库 - 使用调度方法避免事件循环问题
                    if self.db_manager:
                        self._schedule_account_update(user_info, login_status)
            except Exception as e:
                logger.error(f"获取用户信息超时: {str(e)}")
            
        except Exception as e:
            logger.error(f"检查豆瓣状态失败: {str(e)}")

    async def _wait_for_douban_page_ready(self, timeout: int = 10):
        """智能等待豆瓣页面准备就绪 - 优化版"""
        try:
            # 首先检查浏览器和页面状态
            if not self.controller or not self.controller.browser or not self.controller.page:
                logger.warning("浏览器或页面不可用，无法等待页面就绪")
                return
            
            if not self.controller.browser.is_connected():
                logger.warning("浏览器已断开连接，无法等待页面就绪")
                return
                
            if self.controller.page.is_closed():
                logger.warning("页面已关闭，无法等待页面就绪")
                return
            
            logger.info("开始智能等待页面就绪...")
            
            # 等待页面基本加载完成 - 使用较短的超时时间
            try:
                future = self.controller.run_async(self.controller.page.wait_for_load_state('domcontentloaded', timeout=5000))
                future.result(timeout=5000)
                logger.info("页面DOM加载完成")
            except Exception as e:
                logger.warning(f"等待页面DOM加载完成时出错: {e}")
                # 继续执行，不阻塞流程
            
            # 智能检测页面状态 - 并行尝试多个选择器，使用较短的超时时间
            import asyncio
            
            async def check_login_status():
                """并行检查登录状态"""
                selectors = [
                    ('.nav-login', '未登录'),
                    ('.nav-user-account', '已登录'),
                    ('.user-info', '已登录'),
                    ('a[href*="/people/"]', '已登录')
                ]
                
                for selector, expected_status in selectors:
                    try:
                        # 使用较短的超时时间
                        future = self.controller.run_async(self.controller.page.wait_for_selector(selector, timeout=3000))
                        future.result(timeout=3000)
                        logger.info(f"检测到{expected_status}状态 (选择器: {selector})")
                        return expected_status
                    except Exception:
                        continue
                
                # 如果都找不到，尝试检查body元素
                try:
                    future = self.controller.run_async(self.controller.page.wait_for_selector('body', timeout=2000))
                    future.result(timeout=2000)
                    logger.info("页面基本加载完成，但无法确定登录状态")
                    return "未知"
                except Exception:
                    logger.warning("无法检测页面状态")
                    return "未知"
            
            # 执行登录状态检查
            try:
                login_status = await asyncio.wait_for(check_login_status(), timeout=timeout)
                logger.info(f"页面就绪检测完成，登录状态: {login_status}")
            except asyncio.TimeoutError:
                logger.warning(f"页面就绪检测超时({timeout}秒)，继续执行")
            
        except Exception as e:
            logger.warning(f"等待页面元素时出错: {e}")
            # 即使出错也继续执行，不阻塞流程

    async def _wait_for_browser_ready(self, timeout: int = DEFAULT_BROWSER_TIMEOUT) -> None:
        """等待浏览器准备就绪"""
        # 获取账号信息用于日志
        account_info = f"账号: {self.peizhi.zhanghao}" + (f" (ID: {getattr(self, '_account_id', '未知')})" if hasattr(self, '_account_id') else "")
        
        start_time = asyncio.get_event_loop().time()
        self.log_event("信息", f"开始等待浏览器准备就绪，超时时间: {timeout}秒 - {account_info}")
        logger.info(f"开始等待浏览器准备就绪，超时时间: {timeout}秒 - {account_info}")
        
        # 最多等待timeout秒
        check_interval = 1.0  # 每1秒输出一次检查日志
        last_check_time = start_time
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # 检查浏览器核心组件是否都已初始化
            try:
                # 检查browser组件
                browser_available = hasattr(self.controller, 'browser') and self.controller.browser
                # 检查context组件
                context_available = hasattr(self.controller, 'context') and self.controller.context
                # 检查page组件
                page_available = hasattr(self.controller, 'page') and self.controller.page
                
                # 输出定期状态检查日志
                current_time = asyncio.get_event_loop().time()
                if current_time - last_check_time >= check_interval:
                    logger.info(f"浏览器组件状态检查 - browser: {'可用' if browser_available else '不可用'}, context: {'可用' if context_available else '不可用'}, page: {'可用' if page_available else '不可用'} - {account_info}")
                    last_check_time = current_time
                
                # 所有组件都可用时返回
                if browser_available and context_available and page_available:
                    self.log_event("成功", f"浏览器已准备就绪 - {account_info}")
                    logger.info(f"浏览器已准备就绪 - {account_info}")
                    return
            except Exception as e:
                logger.warning(f"检查浏览器组件时出错: {e} - {account_info}")
                self.log_event("警告", f"检查浏览器组件时出错: {e} - {account_info}")
            
            # 等待100毫秒后再次检查
            await asyncio.sleep(0.1)
        
        # 超时后，打印详细的组件状态信息用于调试
        browser_status = '可用' if (hasattr(self.controller, 'browser') and self.controller.browser) else '不可用'
        context_status = '可用' if (hasattr(self.controller, 'context') and self.controller.context) else '不可用'
        page_status = '可用' if (hasattr(self.controller, 'page') and self.controller.page) else '不可用'
        
        # 增加更详细的日志信息，使用正确的属性路径
        detailed_info = f"浏览器路径: {self.peizhi.chrome_path}\n缓存路径: {self.peizhi.huanchunlujing}\n启动URL: {self.peizhi.wangzhi}\n{account_info}"
        logger.error(f"浏览器启动超时 ({timeout}秒) - 组件状态: browser={browser_status}, context={context_status}, page={page_status}\n{detailed_info}")
        self.log_event("错误", f"浏览器启动超时 ({timeout}秒) - 组件状态: browser={browser_status}, context={context_status}, page={page_status} - {account_info}")
        raise Exception(f"浏览器启动超时 ({timeout}秒) - 请检查浏览器路径是否正确，或尝试使用其他浏览器 - {account_info}")
    
    async def _get_douban_user_info(self) -> Optional[Dict[str, Any]]:
        """获取豆瓣用户信息"""
        try:
            logger.info("开始获取豆瓣用户信息（_get_douban_user_info）")
            # 基本校验
            if not self.controller or not self.controller.page or not self.controller.context:
                logger.info("获取用户信息失败：page/context 不可用")
                return { 'login_status': '未登录' }

            # 1) 首选：在页面线程直接执行 JS（避免跨线程 result 阻塞）
            from douban_utils import DoubanUtils
            try:
                user_info = await asyncio.wait_for(
                    self.controller.page.evaluate(DoubanUtils.get_user_info_script()),
                    timeout=DEFAULT_BROWSER_TIMEOUT
                )
            except Exception:
                user_info = None

            if user_info and isinstance(user_info, dict):
                if user_info.get('login_status') == '已登录' and user_info.get('id') and user_info.get('name'):
                    logger.info(f"获取豆瓣用户信息成功: {user_info}")
                    return user_info

            # 2) 回退：从 Cookie 解析 dbcl2 获取 uid
            uid = None
            ck_value = None
            try:
                cookies = await asyncio.wait_for(
                    self.controller.context.cookies(),
                    timeout=DEFAULT_BROWSER_TIMEOUT
                )
                for c in cookies:
                    if c.get('name') == 'dbcl2' and isinstance(c.get('value'), str):
                        val = c.get('value')
                        if ':' in val:
                            uid = val.split(':', 1)[0]
                    if c.get('name') == 'ck':
                        ck_value = c.get('value')
            except Exception:
                pass

            # 3) 回退：多套 DOM 选择器尝试获取昵称
            name_value = None
            try:
                name_selectors = [
                    ".nav-user-account a span",
                    "li.nav-user-account a span",
                    "a[href*='/people/'] span",
                    ".user-info .name",
                    ".nav-user-account a"
                ]
                get_name_js = """
                    (sels) => {
                        for (const s of sels) {
                            const el = document.querySelector(s);
                            if (el && el.textContent && el.textContent.trim()) {
                                return el.textContent.trim();
                            }
                        }
                        return null;
                    }
                """
                name_value = await asyncio.wait_for(
                    self.controller.page.evaluate(get_name_js, name_selectors),
                    timeout=DEFAULT_BROWSER_TIMEOUT
                )
            except Exception:
                pass

            if uid or name_value:
                info = {
                    'login_status': '已登录',
                    'id': uid or '',
                    'name': name_value or ''
                }
                logger.info(f"获取豆瓣用户信息成功(回退): {info}")
                return info

            logger.info("获取豆瓣用户信息失败，判定未登录")
            return { 'login_status': '未登录' }
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return None

    async def _get_cookie_string(self):
        """获取当前浏览器的Cookie字符串"""
        try:
            # 基本可用性检查
            if not self.controller or not getattr(self.controller, 'context', None):
                self.log_event("警告", "浏览器上下文未初始化，无法获取Cookie")
                return ""
            if hasattr(self.controller, 'browser') and self.controller.browser and not self.controller.browser.is_connected():
                self.log_event("警告", "浏览器已断开连接，无法获取Cookie")
                return ""

            logger.info("开始获取Cookie...")
            # 使用原生 await 获取，避免跨事件循环阻塞，设置合理的超时时间
            cookies = await asyncio.wait_for(
                self.controller.context.cookies(),
                timeout=3.0  # 3秒超时，避免长时间等待
            )
            # 转换为标准Cookie字符串格式
            cookie_str = "; ".join([f"{c.get('name')}={c.get('value')}" for c in (cookies or []) if c.get('name') and c.get('value')])
            logger.info(f"成功获取Cookie，条目数: {len(cookies or [])}，长度: {len(cookie_str)} 字符")
            self.log_event("调试", f"成功获取Cookie，条目数: {len(cookies or [])}，长度: {len(cookie_str)} 字符")
            return cookie_str
        except asyncio.TimeoutError:
            error_msg = "获取Cookie超时（3秒）"
            logger.warning(error_msg)
            self.log_event("错误", error_msg)
            return ""
        except Exception as e:
            error_msg = f"获取Cookie失败: {str(e)}"
            logger.error(error_msg)
            self.log_event("错误", error_msg)
            return ""

    async def _update_douban_account_info(self, user_info: Dict[str, Any], login_status: str):
        """更新豆瓣账号信息到数据库"""
        try:
            if self.db_manager:
                accounts = self.db_manager.get_accounts()
                for account in accounts:
                    if account[1] == self.peizhi.zhanghao:
                        # 根据登录状态决定是否获取和更新cookie
                        cookie_str = account[3]  # 默认使用现有cookie值
                        
                        if login_status == "已登录":
                            # 只有当用户已登录时才获取cookie
                            try:
                                # 直接调用异步方法获取Cookie
                                cookie_str = await self._get_cookie_string()
                                if cookie_str:
                                    print(f"[调试] 获取到的Cookie: {cookie_str[:50]}...")  # 调试信息
                                else:
                                    print(f"[调试] 获取到的Cookie为空")
                            except Exception as e:
                                error_msg = f"获取Cookie时出错: {str(e)}"
                                self.log_event("警告", error_msg)
                                print(f"[错误] {error_msg}")  # 调试信息
                                # 出错时保留现有cookie值
                                cookie_str = account[3]
                        else:
                            # 未登录时，将cookie设置为空字符串
                            cookie_str = ""
                        
                        # 创建用户信息字典用于数据库更新
                        user_info_for_db = {
                            'login_status': login_status,
                            'name': user_info.get('name'),
                            'id': user_info.get('id')
                        }
                        
                        # 使用DoubanUtils创建标准的账号数据（使用正确的account对象）
                        from douban_utils import DoubanUtils
                        account_data = DoubanUtils.create_account_data(
                            account=account,
                            user_info=user_info,
                            cookie_str=cookie_str
                        )
                        
                        # 更新账号信息到数据库（使用正确的参数格式）
                        self.db_manager.update_account(account[0], account_data)
                        
                        if login_status == "已登录":
                            self.log_event("信息", f"已更新账号信息: {account_data.get('username', '未知')}，Cookie已保存")
                            print(f"[调试] 已保存Cookie到账号 {account[0]}")  # 调试信息
                        else:
                            self.log_event("信息", f"已更新账号信息: {account_data.get('username', '未知')}，未登录状态已处理")
                            print(f"[调试] 账号 {account[0]} 未登录，已清空Cookie")  # 调试信息
                        break
        except Exception as e:
            self.log_event("错误", f"更新账号信息失败: {str(e)}")

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
        """关闭浏览器 - 终极版，确保所有资源完全释放"""
        try:
            if self._is_closed:
                logger.info("浏览器已经关闭")
                return

            logger.info("开始关闭浏览器...")
            self._is_closed = True

            # 1. 直接调用异步关闭方法，确保完全关闭
            if hasattr(self.controller, '_async_close'):
                try:
                    # 使用控制器的事件循环而不是当前线程的事件循环
                    if hasattr(self.controller, '_loop'):
                        close_future = asyncio.run_coroutine_threadsafe(self.controller._async_close(), self.controller._loop)
                        close_future.result(timeout=5)  # 等待最多5秒
                    else:
                        # 降级方案：使用拼音API
                        self.controller.guanbi_liulanqi()
                        # 等待0.5秒让关闭操作有时间完成
                        await asyncio.sleep(0.5)
                except asyncio.TimeoutError:
                    logger.warning("浏览器关闭超时，继续执行清理")
                except Exception as inner_e:
                    logger.error(f"异步关闭浏览器时出错: {str(inner_e)}")
            else:
                # 降级方案：使用拼音API
                try:
                    self.controller.guanbi_liulanqi()
                    # 等待0.5秒让关闭操作有时间完成
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.warning(f"使用拼音API关闭浏览器时出错: {str(e)}")
                
            # 3. 强制垃圾回收 - 多次执行确保清理彻底
            import gc
            for _ in range(3):
                gc.collect()
                await asyncio.sleep(0.1)
            
            # 4. 额外延迟以确保操作系统完成资源回收
            await asyncio.sleep(0.5)
            
            # 5. 终止可能残留的Chrome进程
            self._terminate_orphaned_chrome_processes()
            
            logger.info("浏览器资源清理完成")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {str(e)}")
            # 发生错误也要确保标记为关闭
            self._is_closed = True

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
