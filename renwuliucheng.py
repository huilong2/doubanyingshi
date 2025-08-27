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

# 导入全局变量
from bianlian_dingyi import DOUBAN_URL

logger = logging.getLogger(__name__)

# 仅格式化本模块内以"[流程]"开头的打印为带时间的终端输出
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
            douban_url = DOUBAN_URL
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
            if not self.liulanqi or not self.liulanqi.controller.page:
                return None
                
            # 使用统一的用户信息获取脚本
            user_info_future = self.liulanqi.controller.run_async(
                self.liulanqi.controller.page.evaluate(DoubanUtils.get_user_info_script())
            )
            user_info = user_info_future.result(timeout=10)
            
            if user_info:
                print(f"[流程] 获取到的用户信息: {user_info}")
                
                # 更新数据库
                if self.db_manager:
                    self._gengxin_zhanghaoxinxi(user_info)
                    
            return user_info
            
        except Exception as e:
            logger.error(f"获取豆瓣账号信息失败: {str(e)}")
            return None
    
    async def _chuli_denglu_moshi(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """处理登录模式"""
        if result["login_status"] == "已登录":
            print("[流程] 进入登录模式 - 等待手动操作")
            result["message"] = "浏览器已启动，等待手动操作"
        else:
            print("[流程] 未登录状态 - 等待手动登录")
            result["message"] = "浏览器已启动，请手动登录"
        return result
    
    async def _chuli_gengxin_moshi(self, result: Dict[str, Any], peizhi: LiulanqiPeizhi) -> Dict[str, Any]:
        """处理更新模式"""
        if result["login_status"] == "已登录":
            print("[流程] 进入更新模式 - 开始更新账号信息")
            # 这里可以添加具体的更新逻辑
            result["message"] = "账号信息更新完成"
        else:
            print("[流程] 未登录状态 - 无法更新")
            result["message"] = "未登录状态，无法更新账号信息"
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
    
    def _gengxin_zhanghaoxinxi(self, user_info: Dict[str, Any]):
        """更新账号信息到数据库"""
        try:
            if not self.db_manager:
                return
                
            accounts = self.db_manager.get_accounts()
            for account in accounts:
                if account[1] == self.liulanqi.peizhi.zhanghao:
                    # 创建用户信息字典用于数据库更新
                    user_info_for_db = {
                        'login_status': user_info.get('login_status', '未知'),
                        'name': user_info.get('name'),
                        'id': user_info.get('id')
                    }
                    
                    # 根据登录状态决定是否更新cookie
                    # 如果已登录，保留现有cookie；如果未登录，将cookie设置为空字符串
                    cookie_value = account[3] if user_info.get('login_status') == '已登录' else ''
                    
                    # 使用工具类创建标准化的账号数据
                    account_data = DoubanUtils.create_account_data(
                        account, user_info_for_db, cookie_value, '运行中'
                    )
                    
                    # 明确设置登录状态
                    account_data['login_status'] = user_info.get('login_status', '未知')
                    
                    # 更新数据库
                    self.db_manager.update_account(account[0], account_data)
                    print("账号信息已更新")
                    break
                    
        except Exception as e:
            logger.error(f"更新账号信息失败: {str(e)}")

    async def guanbi_liulanqi(self):
        """关闭浏览器"""
        try:
            if self.liulanqi:
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
        huanchunlujing="E:/liulanqi/example_user",  # 示例缓存路径
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
