"""
执行流程模块
处理账号登录验证和评论程序执行
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple, Optional

# 配置基本日志（当单独运行时使用）
def setup_basic_logging():
    """设置基本日志配置，用于单独运行时的调试"""
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除已有的处理器，避免重复
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    root_logger.addHandler(console_handler)
    
    return root_logger

# 导入全局变量
from bianlian_dingyi import zhanghao_xuhao, DATABASE_PATH, DOUBAN_URL, get_account_cache_path

logger = logging.getLogger(__name__)

def read_content_specific():
    """读取指定内容数据，返回内容列表"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM contents WHERE type = 'specific' ORDER BY id")
        content_list = [row[0] for row in cursor.fetchall()]
        conn.close()
        return content_list
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return []

def read_movies_specific():
    """读取指定电影数据，返回电影列表"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT movie_id, rating FROM movies WHERE type = 'specific' ORDER BY id")
        movies_list = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return movies_list
    except Exception as e:
        print(f"❌ 读取电影数据失败: {e}")
        return []

async def panduan_zhanghaoshifoudenglu():
    """
    判断全局账号序号对应的账号是否已登录豆瓣。
    登录成功返回(True, liucheng实例)，否则返回(False, None)。
    """
    global zhanghao_xuhao
    
    # 显示当前全局账号序号
    print(f"🚀 开始执行账号登录判断")
    print(f"全局账号序号 zhanghao_xuhao = {zhanghao_xuhao}")
   
    # 读取所有账号信息
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM accounts ORDER BY id")
        accounts = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"❌ 读取账号失败: {e}")
        return False, None

    total_accounts = len(accounts)
    if total_accounts == 0:
        print("❌ 没有可用账号，结束任务")
        return False, None
    
    # 获取当前序号的账号数据
    username, password = accounts[zhanghao_xuhao]
    
    # 详细的账号调试信息
    print(f"=== 账号调试信息 ===")
    print(f"当前账号序号: {zhanghao_xuhao}")
    print(f"总账号数量: {total_accounts}")
    print(f"当前使用账号: {username}")
    print(f"账号密码: {'*' * len(password)}")
    print("=" * 30)
    
    # 打开浏览器并判断登录状态
    try:
        from renwuliucheng import LiulanqiPeizhi, RenwuLiucheng
        import asyncio
        from pathlib import Path

        print(f"🔐 正在尝试账号序号 {zhanghao_xuhao+1}/{total_accounts}: {username}")
        
        # 为每个账号创建独立的缓存目录
        account_cache_path = get_account_cache_path(username)
        print(f"🔧 账号缓存路径: {account_cache_path}")
        
        peizhi = LiulanqiPeizhi(
            zhanghao=username,
            mima=password,
            huanchunlujing=account_cache_path
        )
        liucheng = RenwuLiucheng()
        
        # 登录模式
        print(f"🌐 正在启动浏览器，使用缓存路径: {account_cache_path}")
        print(f"🔍 DEBUG: 开始调用 qidong_liulanqi_liucheng...")
        
        # 检查是否已有事件循环
        try:
            loop = asyncio.get_running_loop()
            print(f"🔍 DEBUG: 检测到运行中的事件循环，使用 create_task")
            # 如果已有事件循环，创建任务
            task = loop.create_task(liucheng.qidong_liulanqi_liucheng(peizhi, "denglu"))
            result = await task
        except RuntimeError:
            print(f"🔍 DEBUG: 没有运行中的事件循环，使用 asyncio.run")
            # 如果没有事件循环，使用 asyncio.run
            result = asyncio.run(liucheng.qidong_liulanqi_liucheng(peizhi, "denglu"))
        
        print(f"🔍 DEBUG: qidong_liulanqi_liucheng 调用完成")
        print(f"📊 浏览器启动结果: {result}")
        
        # 检查浏览器是否启动成功
        if not result or not result.get("success"):
            print(f"❌ 账号 {username} 浏览器启动失败")
            if result:
                print(f"❌ 失败原因: {result.get('message', '未知错误')}")
            # 关闭浏览器
            await liucheng.guanbi_liulanqi()
            return False, None
        
        # 检查登录状态
        login_status = result.get("login_status", "未知")
        user_info = result.get("user_info", {})
        user_login_status = user_info.get("login_status", "未知")
        
        print(f"🔍 登录状态检查: login_status={login_status}, user_login_status={user_login_status}")
        
        # 只有当登录状态为"已登录"时才认为登录成功
        if login_status == "已登录" or user_login_status == "已登录":
            print(f"✅ 账号 {username} 登录成功")
            return True, liucheng
        else:
            print(f"❌ 账号 {username} 未登录，状态: {login_status}")
            print(f"❌ 用户信息状态: {user_login_status}")
            # 关闭浏览器
            await liucheng.guanbi_liulanqi()
            return False, None
            
    except Exception as e:
        print(f"❌ 账号 {username} 登录过程出错: {e}")
        # 尝试关闭浏览器
        try:
            await liucheng.guanbi_liulanqi()
        except:
            pass
        return False, None

async def zhixingyanzhengpinglunchengxu(content, movie_id, rating, group_name, used_accounts=None):
    print(f"🎬 正在处理内容: {content}，电影ID: {movie_id}，评分: {rating}")
    print(f"👥 使用分组: {group_name}")
    
    if used_accounts is None:
        used_accounts = set()
    
    # 读取指定分组的账号信息
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM accounts WHERE group_name = ? ORDER BY id", (group_name,))
        accounts = cursor.fetchall()
        conn.close()
        
        if not accounts:
            print(f"❌ 分组 '{group_name}' 内没有任何账号，无法执行任务")
            print(f"💡 请先在账号管理中为该分组添加账号，或者选择其他分组")
            return False, None
            
    except Exception as e:
        print(f"❌ 读取分组账号失败: {e}")
        return False, None
    
    total_accounts = len(accounts)
    print(f"🔍 分组 '{group_name}' 内账号数量: {total_accounts}")
    print(f"📋 已使用账号: {list(used_accounts)}")
    
    # 找到可用的账号（未使用过的）
    available_accounts = []
    for i, (username, password) in enumerate(accounts):
        if i not in used_accounts:
            available_accounts.append((i, username, password))
    
    print(f"🔍 可用账号数量: {len(available_accounts)}")
    
    if not available_accounts:
        print(f"❌ 没有可用账号，所有账号都已使用过")
        return False, None
    
    # 尝试每个可用账号
    global zhanghao_xuhao
    
    for account_index, username, password in available_accounts:
        zhanghao_xuhao = account_index
        print(f"🔄 尝试账号序号 {account_index}: {username}")
        
        # 判断账号是否登录成功，获取浏览器实例
        login_success, liucheng = await panduan_zhanghaoshifoudenglu()
        
        if login_success and liucheng:
            print(f"✅ 账号 {account_index} ({username}) 登录成功，开始执行发布任务")
            try:
                # 执行发布任务
                zhixfabuzichongxing()
                print(f"✅ 发布任务执行完成")
                
                return True, account_index
                
            except Exception as e:
                print(f"❌ 发布任务执行失败: {e}")
            finally:
                # 关闭浏览器
                try:
                    print(f"🔒 正在关闭浏览器...")
                    await liucheng.guanbi_liulanqi()
                    print(f"🔒 浏览器已成功关闭")
                except Exception as e:
                    print(f"⚠️ 关闭浏览器时出错: {e}")
        else:
            print(f"❌ 账号 {account_index} ({username}) 登录失败，尝试下一个账号")
            # 继续尝试下一个账号
    
    # 所有可用账号都尝试失败
    print(f"❌ 所有可用账号都登录失败，无法执行任务")
    return False, None
def zhixfabuzichongxing():
    """执行发布任务"""
    print("🚀 准备执行发布任务")
    
    # 这里可以添加具体的发布逻辑
    # 例如：发布评论、评分等
    
    print("📝 正在发布评论...")
    # 模拟发布过程
    import time
    time.sleep(1)  # 模拟网络延迟
    
    print("⭐ 正在评分...")
    time.sleep(1)  # 模拟评分过程
    
    print("✅ 发布任务执行完成")

async def suijidianyingpinglunpingxing(group_name=None):
    # 如果没有传入分组名称，返回错误
    if not group_name:
        print("❌ 错误：未指定分组名称，无法执行任务")
        return [], []
    
    print(f"👥 使用分组: {group_name}")
    
    # 判断内容数量必须大于等于电影数量，否则弹窗提示并返回
    content_data = read_content_specific()
    movies_data = read_movies_specific()
    
    print(f"📊 读取到 {len(content_data)} 个内容，{len(movies_data)} 个电影")
    
    if len(content_data) < len(movies_data):
        print("❌ 数量不符：内容的数量必须大于等于电影的数量！")
        return [], []
    else:
        print("✅ 符合条件，开始依次处理每个内容和电影")
        
        # 初始化已使用账号列表
        used_accounts = set()
        successful_tasks = 0
        
        # 依次处理每个内容和电影
        for i in range(len(movies_data)):
            content = content_data[i]
            movie_id, rating = movies_data[i]
            print(f"🎯 处理第{i+1}个任务：内容='{content}'，电影ID={movie_id}，评分={rating}")
            
            try:
                # 执行发布任务，传递分组名称和已使用账号列表
                task_success, used_account = await zhixingyanzhengpinglunchengxu(content, movie_id, rating, group_name, used_accounts)
                
                if task_success:
                    print(f"✅ 第{i+1}个任务完成，使用账号: {used_account}")
                    used_accounts.add(used_account)
                    successful_tasks += 1
                else:
                    print(f"❌ 第{i+1}个任务失败：没有可用账号")
                    print(f"⚠️ 已用完所有账号，停止执行剩余任务")
                    break
                    
            except Exception as e:
                print(f"❌ 第{i+1}个任务异常: {e}")
                break
        
        print(f"🎉 任务处理完成！成功完成 {successful_tasks} 个任务，共 {len(movies_data)} 个任务")
        print(f"📋 已使用账号: {list(used_accounts)}")
        return content_data, movies_data


