# 全局变量定义文件
# 集中管理所有全局配置变量

import os
from pathlib import Path

# 获取程序设置中的路径
def get_program_data_dir():
    """获取程序设置中的数据目录"""
    try:
        from config import DATA_DIR
        return DATA_DIR
    except ImportError:
        # 如果无法导入，使用默认路径
        return Path(__file__).parent / "data"



# 账号相关
zhanghao_xuhao = 0  # 默认从第一个账号开始

# 浏览器相关
DEFAULT_BROWSER_TIMEOUT = 30  # 浏览器操作默认超时时间（秒）
DEFAULT_PAGE_TIMEOUT = 30000  # 页面操作默认超时时间（毫秒）

# 数据库相关
DATABASE_PATH = str(get_program_data_dir() / 'accounts.db')  # 数据库文件路径

def get_account_cache_path(username):
    """获取指定账号的缓存路径"""
    try:
        # 从peizhi.json获取程序界面设置的缓存路径
        import json
        peizhi_path = Path(__file__).parent / "data" / "peizhi.json"
        if peizhi_path.exists():
            with open(peizhi_path, 'r', encoding='utf-8') as f:
                peizhi_data = json.load(f)
                browser_cache_path = peizhi_data.get("browser_cache_path", "")
                if browser_cache_path:
                    return str(Path(browser_cache_path) / username)
    except Exception as e:
        print(f"⚠️ 读取peizhi.json失败: {e}")
    
    # 如果无法获取，使用默认路径
    return str(Path(__file__).parent / "browser_data" / username)

# 豆瓣相关
DOUBAN_URL = "https://www.douban.com"  # 豆瓣网站地址

# 日志相关
LOG_LEVEL = "INFO"  # 日志级别
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # 日志格式