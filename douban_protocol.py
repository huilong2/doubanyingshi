"""
豆瓣协议相关函数
"""

import requests
import json
from urllib.parse import quote
from typing import Dict, Any
# 导入 update_poster_status 函数
from biaojie_hanshu import update_poster_status

def 电影电视评价协议(账号的数据: Dict[str, Any], 几颗心: str, 内容: str, 电影ID: str, 是否老剧: bool, window=None) -> bool:
    """
    豆瓣电影/电视评价协议
    
    Args:
        账号的数据: 账号数据字典
        几颗心: 评分星数
        内容: 评价内容
        电影ID: 电影/电视ID
        是否老剧: 是否为老剧
        window: UI窗口对象，用于获取run_status_combo的选中项
        
    Returns:
        bool: 评价是否成功
    """
    # 确定评价类型
    if 是否老剧:
        # 使用 update_poster_status 函数获取类型
        全_海报图数据, 类型 = update_poster_status(window, is_old_series=True)
    else:
        # 使用 update_poster_status 函数获取类型
        全_海报图数据, 类型 = update_poster_status(window, is_old_series=False)
    
    # 从 cookies 中提取 ck
    ck = None
    if "ck" in 账号的数据.get("cookies", ""):
        # 简单提取 ck，实际可能需要更复杂的解析
        import re
        match = re.search(r'ck=([^;]+)', 账号的数据["cookies"])
        if match:
        	ck = match.group(1)
    
    # 构造请求URL
    局_网址 = f"https://movie.douban.com/j/subject/{电影ID}/interest"
    
    # 构造POST数据
    ADD_数据包 = {
        "ck": ck or "",
        "interest": 类型,
        "foldcollect": "F",
        "tags": "",
        "comment": quote(内容, safe=''),
        "share-shuo": "douban"
    }
    
    # 如果不是想看类型，添加评分
    if 类型 != "wish":
        ADD_数据包["rating"] = 几颗心
    
    # 构造请求头
    ADD_协议头 = {
        "Host": "movie.douban.com",
        "Connection": "keep-alive",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": 账号的数据.get("ua", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        "Origin": "https://movie.douban.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    
    # 发送请求
    try:
        response = requests.post(
            局_网址,
            data=ADD_数据包,
            headers=ADD_协议头,
            cookies=账号的数据.get("cookies_dict", {}),  # 需要将 cookies 字符串转换为字典
            allow_redirects=True,
            proxies=账号的数据.get("代理ip", {})
        )
        
        # 解析返回的JSON
        JSON = response.json()
        
        # 检查返回结果
        if JSON.get("r") == "0":
            return True
        else:
            账号的数据["错误原因"] = JSON.get("code", "")
            账号的数据["错误代码"] = JSON.get("r", "")
            return False
            
    except Exception as e:
        账号的数据["错误原因"] = str(e)
        账号的数据["错误代码"] = "-1"
        return False