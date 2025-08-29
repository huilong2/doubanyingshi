#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
账号缓存删除测试工具
用于诊断删除账号后缓存未被删除的问题
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path

# 设置日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_delete_cache.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_delete_account_cache")

def setup_project_path():
    """设置项目路径，确保可以导入项目模块"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

def load_config():
    """加载配置文件"""
    from config import config
    config_path = config.get_config_path()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return {}
    else:
        logger.error(f"配置文件不存在: {config_path}")
        return {}

def get_account_info_by_id(account_id):
    """根据账号ID获取账号信息"""
    try:
        from data_manager import DataManager
        data_manager = DataManager()
        accounts = data_manager.get_accounts()
        
        for account in accounts:
            if len(account) > 0 and account[0] == account_id:
                logger.info(f"找到账号信息: ID={account[0]}, 用户名={account[1]}")
                return account
        
        logger.warning(f"未找到账号ID为 {account_id} 的账号")
        return None
    except Exception as e:
        logger.error(f"获取账号信息失败: {str(e)}")
        return None

def check_and_delete_cache_manually(account_id, username):
    """手动检查并删除账号缓存"""
    try:
        # 加载配置
        config_data = load_config()
        browser_cache_path = config_data.get('browser_cache_path', '')
        
        # 如果配置中没有缓存路径，使用默认路径
        if not browser_cache_path:
            from config import config
            browser_cache_path = os.path.join(config.program_root, 'temp', 'browser_cache')
            logger.info(f"使用默认缓存路径: {browser_cache_path}")
        else:
            logger.info(f"从配置文件获取缓存路径: {browser_cache_path}")
        
        # 构建账号缓存目录路径
        account_cache_dir = os.path.join(browser_cache_path, username)
        logger.info(f"账号缓存目录路径: {account_cache_dir}")
        
        # 检查缓存目录是否存在
        if os.path.exists(account_cache_dir):
            logger.info(f"账号缓存目录存在: {account_cache_dir}")
            logger.info(f"尝试手动删除缓存目录...")
            
            # 尝试删除缓存目录
            try:
                shutil.rmtree(account_cache_dir)
                logger.info(f"成功删除缓存目录: {account_cache_dir}")
                return True
            except PermissionError as e:
                logger.error(f"权限不足，无法删除缓存目录: {str(e)}")
                logger.error("请以管理员身份运行此脚本或手动删除缓存目录")
            except Exception as e:
                logger.error(f"删除缓存目录失败: {str(e)}")
        else:
            logger.info(f"账号缓存目录不存在: {account_cache_dir}")
            
        return False
    except Exception as e:
        logger.error(f"手动检查和删除缓存失败: {str(e)}")
        return False

def test_delete_account_cache(account_id):
    """测试删除账号缓存功能"""
    logger.info(f"==== 开始测试账号缓存删除功能 - 账号ID: {account_id} ====")
    
    # 获取账号信息
    account_info = get_account_info_by_id(account_id)
    if not account_info:
        logger.error("无法获取账号信息，测试中止")
        return False
    
    username = account_info[1]
    logger.info(f"准备测试删除账号 '{username}' (ID: {account_id}) 的缓存")
    
    # 先手动检查和删除缓存
    logger.info("\n=== 步骤1: 手动检查和删除缓存 ===")
    manual_delete_success = check_and_delete_cache_manually(account_id, username)
    
    # 测试调用原有的delete_account_cache函数
    logger.info("\n=== 步骤2: 调用delete_account_cache函数 ===")
    try:
        from utils import delete_account_cache
        
        # 输出函数定义信息，用于调试
        logger.debug(f"delete_account_cache函数定义: {delete_account_cache.__code__.co_filename}:{delete_account_cache.__code__.co_firstlineno}")
        logger.debug(f"函数参数: {delete_account_cache.__code__.co_varnames[:delete_account_cache.__code__.co_argcount]}")
        
        logger.info(f"调用delete_account_cache({account_id})...")
        result = delete_account_cache(account_id)
        logger.info(f"delete_account_cache返回结果: {result}")
    except ImportError as e:
        logger.error(f"导入delete_account_cache函数失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"调用delete_account_cache函数失败: {str(e)}")
        return False
    
    # 再次检查缓存目录是否存在
    logger.info("\n=== 步骤3: 验证缓存是否已删除 ===")
    config_data = load_config()
    browser_cache_path = config_data.get('browser_cache_path', '')
    
    from config import config
    if not browser_cache_path:
        browser_cache_path = os.path.join(config.program_root, 'temp', 'browser_cache')
    
    account_cache_dir = os.path.join(browser_cache_path, username)
    cache_exists = os.path.exists(account_cache_dir)
    
    logger.info(f"缓存目录 '{account_cache_dir}' 存在状态: {cache_exists}")
    
    # 生成测试报告
    logger.info("\n==== 测试报告 ====")
    logger.info(f"账号ID: {account_id}")
    logger.info(f"账号名: {username}")
    logger.info(f"缓存路径: {browser_cache_path}")
    logger.info(f"手动删除结果: {'成功' if manual_delete_success else '失败'}")
    logger.info(f"函数调用结果: {'成功' if result else '失败'}")
    logger.info(f"最终缓存状态: {'已删除' if not cache_exists else '仍然存在'}")
    
    if not cache_exists:
        logger.info("\n✅ 测试成功! 账号缓存已被删除。")
    else:
        logger.error("\n❌ 测试失败! 账号缓存仍然存在。")
        logger.error("建议: 请检查文件夹权限，尝试以管理员身份运行程序，或手动删除缓存文件夹。")
    
    return not cache_exists

def main():
    """主函数"""
    setup_project_path()
    
    # 获取账号ID参数
    if len(sys.argv) > 1:
        try:
            account_id = int(sys.argv[1])
        except ValueError:
            logger.error("请提供有效的账号ID")
            print("用法: python test_delete_account_cache.py <账号ID>")
            return 1
    else:
        # 如果没有提供账号ID，显示帮助信息
        print("账号缓存删除测试工具")
        print("\n用法:")
        print("  python test_delete_account_cache.py <账号ID>")
        print("\n功能:")
        print("  1. 检查指定账号的缓存目录是否存在")
        print("  2. 尝试手动删除缓存目录")
        print("  3. 调用原有的delete_account_cache函数")
        print("  4. 验证缓存是否已删除")
        print("\n示例:")
        print("  python test_delete_account_cache.py 1")
        return 1
    
    # 运行测试
    test_result = test_delete_account_cache(account_id)
    
    # 生成日志文件路径
    log_file_path = os.path.join(os.getcwd(), "test_delete_cache.log")
    logger.info(f"详细日志已保存至: {log_file_path}")
    print(f"\n详细日志已保存至: {log_file_path}")
    
    return 0 if test_result else 1

if __name__ == "__main__":
    sys.exit(main())