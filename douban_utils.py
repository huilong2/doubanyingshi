"""
豆瓣相关工具函数
避免循环导入问题
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DoubanUtils:
    """豆瓣工具类"""
    
    @staticmethod
    def get_user_info_script():
        """获取豆瓣用户信息的JavaScript代码"""
        return """
            () => {
                // 首先检查全局状态
                if (window.__INIT_STATE__ && window.__INIT_STATE__.user) {
                    return {
                        login_status: '已登录',
                        id: window.__INIT_STATE__.user.id,
                        name: window.__INIT_STATE__.user.name
                    };
                }
                
                // 检查本地存储
                const storedInfo = localStorage.getItem('douban_user_info');
                if (storedInfo) {
                    try {
                        const parsed = JSON.parse(storedInfo);
                        if (parsed && parsed.id && parsed.name) {
                            return {
                                login_status: '已登录',
                                id: parsed.id,
                                name: parsed.name
                            };
                        }
                    } catch(e) {}
                }
                
                // 检查DOM元素
                const userAccount = document.querySelector('.nav-user-account');
                if (userAccount) {
                    const nameElement = userAccount.querySelector('a span');
                    const idElement = userAccount.querySelector('a');
                    if (nameElement && idElement) {
                        const name = nameElement.textContent.trim();
                        const id = idElement.href.split('/').filter(Boolean).pop();
                        return {
                            login_status: '已登录',
                            id: id,
                            name: name
                        };
                    }
                }
                
                return { login_status: '未登录' };
            }
        """
    
    @staticmethod
    def create_account_data(account, user_info: Optional[Dict[str, Any]] = None, 
                          cookie_str: str = "", running_status: str = "运行中") -> Dict[str, Any]:
        """
        创建标准的账号数据字典
        
        Args:
            account: 数据库中的账号记录
            user_info: 用户信息字典
            cookie_str: Cookie字符串
            running_status: 运行状态
            
        Returns:
            Dict: 标准化的账号数据
        """
        return {
            'username': account[1],
            'password': account[2],
            'ck': cookie_str if cookie_str is not None else account[3],
            'nickname': user_info.get('name', account[4]) if user_info else account[4],
            'account_id': user_info.get('id', account[5]) if user_info else account[5],
            'login_status': user_info.get('login_status', '未登录') if user_info else account[6],
            'homepage': account[7],
            'login_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'proxy': account[9],
            'running_status': running_status,
            'note': account[11],
            'group': account[12]
        }
    
    @staticmethod
    def print_account_debug_info(account_data: Dict[str, Any], context: str = ""):
        """打印账号调试信息"""
        context_prefix = f"[调试-{context}] " if context else "[调试] "
        print(f"{context_prefix}account_data: 用户名={account_data['username']}, "
              f"昵称={account_data['nickname']}, 账号ID={account_data['account_id']}, "
              f"登录状态={account_data['login_status']}, 主页={account_data['homepage']}, "
              f"登录时间={account_data['login_time']}, 代理={account_data['proxy']}, "
              f"运行状态={account_data['running_status']}, 备注={account_data['note']}, "
              f"分组={account_data['group']}, Cookie长度={len(account_data['ck']) if account_data['ck'] else 0}")
