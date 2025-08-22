"""
浏览器运行流程模块
根据不同的执行模式处理浏览器启动、登录和信息获取流程
"""

import asyncio
from datetime import datetime
import builtins as _builtins
import time
from datetime import datetime
from typing import Optional, Dict, Any
from liulanqi_gongcaozuo import LiulanqiGongcaozuo, LiulanqiPeizhi
from douban_utils import DoubanUtils
import logging

logger = logging.getLogger(__name__)

# 仅格式化本模块内以“[流程]”开头的打印为带时间的终端输出
_orig_print = _builtins.print
def _flow_print(*args, **kwargs):
    try:
        if args and isinstance(args[0], str) and args[0].startswith("[流程]"):
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            args = (f"[{ts}] {args[0]}",) + args[1:]
    except Exception:
        pass
    return _orig_print(*args, **kwargs)

_builtins.print = _flow_print

class RenwuLiucheng:
    """任务流程控制器"""
    
    def __init__(self, db_manager=None, browser_signals=None):
        self.db_manager = db_manager
        self.browser_signals = browser_signals
        self.liulanqi = None
        
    async def qidong_liulanqi_liucheng(self, peizhi: LiulanqiPeizhi, zhixingmoshi: str = "denglu") -> Dict[str, Any]:
        """
        启动浏览器流程
        
        Args:
            peizhi: 浏览器配置
            zhixingmoshi: 执行模式 ("denglu" 或 "gengxin")
            
        Returns:
            Dict: 包含执行结果的字典
        """
        result = {
            "success": False,
            "message": "",
            "user_info": None,
            "login_status": "未知"
        }
        
        try:
            # 1. 初始化浏览器
            print(f"[流程] 开始启动浏览器 - 模式: {zhixingmoshi}")
            self.liulanqi = LiulanqiGongcaozuo(peizhi, self.browser_signals, self.db_manager)
            
            # 2. 启动浏览器
            await self.liulanqi.chushihua()
            print("[流程] 浏览器初始化成功")
            
            # 3. 打开豆瓣网站
            douban_url = "https://www.douban.com"
            await self.liulanqi.dakai_ye(douban_url)
            print("[流程] 豆瓣网站加载成功")
            
            # 4. 智能等待页面完全加载 - 页面加载已在dakai_ye中处理
            # 不再需要固定等待，因为_check_douban_status已经包含了智能等待
            
            # 5. 获取豆瓣账号信息
            user_info = await self._huoqu_douban_zhanghaoxinxi()
            result["user_info"] = user_info
            
            if user_info and user_info.get("id"):
                result["login_status"] = "已登录"
                print(f"[流程] 检测到已登录用户: {user_info.get('name', '未知')} (ID: {user_info.get('id')})")
            else:
                result["login_status"] = "未登录"
                print("[流程] 检测到未登录状态")
            
            # 6. 根据执行模式处理
            if zhixingmoshi == "denglu":
                result = await self._chuli_denglu_moshi(result)
            elif zhixingmoshi == "gengxin":
                result = await self._chuli_gengxin_moshi(result, peizhi)
            else:
                result["message"] = f"不支持的执行模式: {zhixingmoshi}"
                return result
                
            result["success"] = True
            
        except Exception as e:
            error_msg = f"浏览器流程执行失败: {str(e)}"
            logger.error(error_msg)
            result["message"] = error_msg
            
        return result
    
    @staticmethod
    def get_douban_user_info_script():
        """获取豆瓣用户信息的JavaScript代码"""
        return DoubanUtils.get_user_info_script()

    async def _huoqu_douban_zhanghaoxinxi(self) -> Optional[Dict[str, Any]]:
        """获取豆瓣账号信息"""
        try:
            if not self.liulanqi or not self.liulanqi.page:
                return None
                
            # 使用统一的JavaScript代码获取用户信息
            # 通过新模块封装的脚本执行，避免直接跨事件循环
            user_info = await self.liulanqi.zhixing_script(self.get_douban_user_info_script())
            
            print(f"[流程] 获取到的用户信息: {user_info}")
            return user_info
            
        except Exception as e:
            logger.error(f"获取豆瓣账号信息失败: {str(e)}")
            return None
    
    async def _chuli_denglu_moshi(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """处理登录模式"""
        print("[流程] 进入登录模式 - 等待手动操作")
        result["message"] = "浏览器已启动，等待手动操作"
        
        # 更新数据库中的账号状态
        if self.db_manager and self.liulanqi:
            await self._gengxin_zhanghaozhuangtai(result["user_info"], "运行中")
        
        return result
    
    async def _chuli_gengxin_moshi(self, result: Dict[str, Any], peizhi: LiulanqiPeizhi) -> Dict[str, Any]:
        """处理更新模式"""
        print("[流程] 进入更新模式")
        
        if result["login_status"] == "已登录":
            print("[流程] 账号已登录，更新信息")
            result["message"] = "账号已登录，信息已更新"
            result["success"] = True
            
            # 更新数据库中的账号信息
            if self.db_manager:
                await self._gengxin_zhanghaozhuangtai(result["user_info"], "已登录")
                
        else:
            print("[流程] 账号未登录，开始自动登录")
            login_result = await self._zidong_denglu(peizhi)
            
            if login_result["success"]:
                # 重新获取用户信息
                user_info = await self._huoqu_douban_zhanghaoxinxi()
                result["user_info"] = user_info
                result["login_status"] = "已登录" if user_info and user_info.get("id") else "登录失败"
                
                if result["login_status"] == "已登录":
                    result["message"] = "自动登录成功，信息已更新"
                    result["success"] = True
                    
                    # 更新数据库
                    if self.db_manager:
                        await self._gengxin_zhanghaozhuangtai(user_info, result["login_status"])
                else:
                    result["message"] = "自动登录失败，无法获取用户信息"
                    result["success"] = False
            else:
                result["message"] = f"自动登录失败: {login_result['message']}"
                result["success"] = False
        
        return result
    
    async def _zidong_denglu(self, peizhi: LiulanqiPeizhi) -> Dict[str, Any]:
        """自动登录豆瓣账号（基于易语言代码转换）"""
        result = {"success": False, "message": ""}
        
        try:
            if not self.liulanqi or not self.liulanqi.page:
                result["message"] = "浏览器页面不可用"
                return result
            
            print("[流程] 开始自动登录流程")
            
            # 1. 导航到登录页面
            login_url = "https://accounts.douban.com/passport/login?source=movie"
            await self.liulanqi.page.goto(login_url)
            await asyncio.sleep(2)
            
            # 2. 点击手机号登录链接
            try:
                await self.liulanqi.page.click("a.link-phone", timeout=5000)
                await asyncio.sleep(5)
                print("[流程] 已点击手机号登录")
            except Exception as e:
                print(f"[流程] 点击手机号登录失败: {e}")
            
            # 3. 点击账号密码登录选项卡
            try:
                await self.liulanqi.page.click("li.account-tab-account", timeout=5000)
                await asyncio.sleep(0.5)
                print("[流程] 已切换到账号密码登录")
            except Exception as e:
                print(f"[流程] 切换登录方式失败: {e}")
            
            # 4. 输入用户名
            try:
                username_selector = "input[name='username']"
                await self.liulanqi.page.click(username_selector)
                await asyncio.sleep(0.1)
                await self.liulanqi.page.fill(username_selector, peizhi.zhanghao)
                await asyncio.sleep(0.2)
                print(f"[流程] 已输入用户名: {peizhi.zhanghao}")
            except Exception as e:
                print(f"[流程] 输入用户名失败: {e}")
                result["message"] = f"输入用户名失败: {e}"
                return result
            
            # 5. 输入密码
            try:
                password_selector = "input[name='password']"
                await self.liulanqi.page.click(password_selector)
                await asyncio.sleep(0.1)
                await self.liulanqi.page.fill(password_selector, peizhi.mima)
                await asyncio.sleep(0.1)
                print("[流程] 已输入密码")
            except Exception as e:
                print(f"[流程] 输入密码失败: {e}")
                result["message"] = f"输入密码失败: {e}"
                return result
            
            # 6. 点击登录按钮
            try:
                login_button_selector = "[class*='btn btn-account']"
                await self.liulanqi.page.click(login_button_selector)
                await asyncio.sleep(1.5)
                print("[流程] 已点击登录按钮")
            except Exception as e:
                print(f"[流程] 点击登录按钮失败: {e}")
                result["message"] = f"点击登录按钮失败: {e}"
                return result
            
            # 7. 等待登录完成并检查结果
            await self._dengdai_denglu_wancheng()
            
            # 8. 验证登录是否成功
            current_url = self.liulanqi.page.url
            if "accounts.douban.com" not in current_url:
                print("[流程] 登录成功，已跳转到主页")
                result["success"] = True
                result["message"] = "自动登录成功"
            else:
                print("[流程] 登录可能失败，仍在登录页面")
                result["message"] = "登录失败，请检查账号密码"
            
        except Exception as e:
            error_msg = f"自动登录过程出错: {str(e)}"
            logger.error(error_msg)
            result["message"] = error_msg
        
        return result
    
    async def _dengdai_denglu_wancheng(self, max_wait_time: int = 20):
        """智能判断是否加载成功（对应易语言的智能判断是否加载成功函数）"""
        print("[流程] 等待登录完成...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                current_url = self.liulanqi.page.url
                
                # 如果不在登录页面了，说明登录成功
                if "accounts.douban.com" not in current_url:
                    print(f"[流程] 检测到页面跳转: {current_url}")
                    break
                
                # 检查是否有错误提示
                error_element = await self.liulanqi.page.query_selector(".error, .err-tip")
                if error_element:
                    error_text = await error_element.text_content()
                    print(f"[流程] 检测到登录错误: {error_text}")
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"[流程] 等待登录完成时出错: {e}")
                break
    
    async def gengxin_zhanghaoxinxi(self, username: str, user_info: Optional[Dict[str, Any]] = None, running_status: str = "运行中") -> bool:
        """
        统一的账号信息更新方法
        
        Args:
            username: 用户名
            user_info: 用户信息字典，如果为None则自动获取
            running_status: 运行状态
            
        Returns:
            bool: 更新是否成功
        """
        if not self.db_manager:
            return False
            
        try:
            # 如果没有提供用户信息，尝试自动获取
            if user_info is None and self.liulanqi and self.liulanqi.page:
                user_info = await self._huoqu_douban_zhanghaoxinxi()
            
            # 获取当前cookies
            cookie_str = ""
            if self.liulanqi and self.liulanqi.page:
                try:
                    cookies = await self.liulanqi.page.context.cookies()
                    cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
                except Exception as e:
                    logger.warning(f"获取cookies失败: {str(e)}")
            
            # 查找并更新账号
            accounts = self.db_manager.get_accounts()
            for account in accounts:
                if account[1] == username:
                    # 使用工具类创建标准化的账号数据
                    account_data = DoubanUtils.create_account_data(
                        account, user_info, cookie_str, running_status
                    )
                    
                    # 调试输出
                    DoubanUtils.print_account_debug_info(account_data, "流程-数据库更新")
                    
                    return self.db_manager.update_account(account[0], account_data)
            
            logger.warning(f"未找到用户名为 {username} 的账号")
            return False
                    
        except Exception as e:
            logger.error(f"更新账号状态失败: {str(e)}")
            return False

    async def _gengxin_zhanghaozhuangtai(self, user_info: Optional[Dict[str, Any]], running_status: str):
        """更新数据库中的账号状态（兼容性方法）"""
        if not self.liulanqi:
            return
        return await self.gengxin_zhanghaoxinxi(self.liulanqi.peizhi.zhanghao, user_info, running_status)
    
    async def guanbi_liulanqi(self):
        """关闭浏览器"""
        if self.liulanqi:
            try:
                await self.liulanqi.guanbi()
                print("[流程] 浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {str(e)}")


# 使用示例函数
async def zhixing_liucheng_example():
    """执行流程示例"""
    
    # 创建浏览器配置
    peizhi = LiulanqiPeizhi(
        zhanghao="your_username",
        mima="your_password",
        huanchunlujing="./browser_data",
        # 其他配置...
    )
    
    # 创建流程控制器
    liucheng = RenwuLiucheng()
    
    try:
        # 执行登录模式
        result = await liucheng.qidong_liulanqi_liucheng(peizhi, "denglu")
        print(f"登录模式结果: {result}")
        
        # 或执行更新模式
        # result = await liucheng.qidong_liulanqi_liucheng(peizhi, "gengxin")
        # print(f"更新模式结果: {result}")
        
    finally:
        # 关闭浏览器
        await liucheng.guanbi_liulanqi()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(zhixing_liucheng_example())
