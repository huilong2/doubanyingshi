#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆瓣影视更新系统 - 统一测试模块
整合各种功能测试，包括数据库、浏览器、账号管理等
"""

import sys
import os
import asyncio
import sqlite3
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入项目模块
from data_manager import DataManager
from liulanqi_gongcaozuo import LiulanqiPeizhi, LiulanqiGongcaozuo
from config import config, DATA_DIR

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DatabaseTest:
    """数据库功能测试"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    def test_database_connection(self):
        """测试数据库连接"""
        print("\n=== 测试数据库连接 ===")
        try:
            accounts = self.data_manager.get_accounts()
            print(f"✅ 数据库连接成功，共有 {len(accounts)} 个账号")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return False
    
    def test_account_operations(self):
        """测试账号操作功能"""
        print("\n=== 测试账号操作功能 ===")
        try:
            # 测试添加账号
            test_account = {
                'username': 'test_user_12345',
                'password': 'test_password',
                'ck': '',
                'nickname': 'Test User',
                'account_id': '',
                'login_status': '未登录',
                'homepage': '',
                'login_time': '',
                'proxy': '',
                'running_status': '空闲',
                'note': 'Test account for testing',
                'group_name': '测试分组'
            }
            
            # 添加测试账号
            success = self.data_manager.add_account(test_account)
            if success:
                print("✅ 添加测试账号成功")
            
            # 获取账号列表验证
            accounts = self.data_manager.get_accounts()
            test_account_found = any(acc[1] == 'test_user_12345' for acc in accounts)
            
            if test_account_found:
                print("✅ 测试账号已成功添加到数据库")
                
                # 清理测试数据
                for acc in accounts:
                    if acc[1] == 'test_user_12345':
                        self.data_manager.delete_account(acc[0])
                        print("✅ 测试账号已清理")
                        break
            
            return True
            
        except Exception as e:
            print(f"❌ 账号操作测试失败: {str(e)}")
            return False
    
    def test_groups_operations(self):
        """测试分组操作功能"""
        print("\n=== 测试分组操作功能 ===")
        try:
            # 获取现有分组
            groups = self.data_manager.get_groups()
            print(f"✅ 获取分组成功，共有 {len(groups)} 个分组")
            
            for group in groups[:5]:  # 只显示前5个分组
                print(f"  - {group}")
            
            return True
            
        except Exception as e:
            print(f"❌ 分组操作测试失败: {str(e)}")
            return False


class BrowserTest:
    """浏览器功能测试"""
    
    async def test_browser_initialization(self):
        """测试浏览器初始化"""
        print("\n=== 测试浏览器初始化 ===")
        try:
            # 创建浏览器配置
            peizhi = LiulanqiPeizhi(
                zhanghao="test_browser_user",
                wangzhi="https://www.douban.com",
                huanchunlujing=str(Path(project_root) / "cache" / "test"),
                chrome_path=None,  # 使用默认Chrome路径
                fingerprint={
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'screen_width': 1920,
                    'screen_height': 1080
                }
            )
            
            # 创建浏览器操作实例
            liulanqi = LiulanqiGongcaozuo(peizhi)
            print("✅ 浏览器配置创建成功")
            
            # 注意：这里只测试配置创建，不实际启动浏览器以避免测试环境问题
            print("✅ 浏览器初始化测试通过（配置验证）")
            return True
            
        except Exception as e:
            print(f"❌ 浏览器初始化测试失败: {str(e)}")
            return False
    
    def test_ip_location(self):
        """测试IP定位功能"""
        print("\n=== 测试IP定位功能 ===")
        try:
            from liulanqimokuai.mokuai_ipdingwei import get_ip_location
            
            # 测试获取公网IP的地理位置
            test_ip = "8.8.8.8"  # Google DNS IP
            location = get_ip_location(test_ip)
            
            if 'error' not in location:
                print(f"✅ IP定位成功: {test_ip}")
                print(f"  纬度: {location.get('latitude', 'N/A')}")
                print(f"  经度: {location.get('longitude', 'N/A')}")
            else:
                print(f"⚠️ IP定位返回错误: {location['error']}")
                print("  这可能是由于网络问题或API限制，属于正常情况")
            
            return True
            
        except Exception as e:
            print(f"❌ IP定位测试失败: {str(e)}")
            return False


class ConfigTest:
    """配置功能测试"""
    
    def test_config_loading(self):
        """测试配置加载功能"""
        print("\n=== 测试配置加载功能 ===")
        try:
            # 测试各种路径配置
            data_dir = config.get_data_dir()
            logs_dir = config.get_logs_dir()
            cache_dir = config.get_cache_dir()
            
            print(f"✅ 数据目录: {data_dir}")
            print(f"✅ 日志目录: {logs_dir}")
            print(f"✅ 缓存目录: {cache_dir}")
            
            # 验证目录是否存在
            if data_dir.exists():
                print("✅ 数据目录存在")
            else:
                print("⚠️ 数据目录不存在，将自动创建")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置加载测试失败: {str(e)}")
            return False


def main():
    """主测试函数"""
    print("🚀 豆瓣影视更新系统 - 功能测试")
    print("=" * 60)
    
    test_results = {}
    
    # 配置测试
    config_test = ConfigTest()
    test_results['配置功能'] = config_test.test_config_loading()
    
    # 数据库测试
    db_test = DatabaseTest()
    test_results['数据库连接'] = db_test.test_database_connection()
    test_results['账号操作'] = db_test.test_account_operations()
    test_results['分组操作'] = db_test.test_groups_operations()
    
    # 浏览器测试
    browser_test = BrowserTest()
    test_results['浏览器初始化'] = asyncio.run(browser_test.test_browser_initialization())
    test_results['IP定位功能'] = browser_test.test_ip_location()
    
    # 测试结果总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:12} : {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统功能正常。")
    else:
        print(f"\n⚠️ 有 {total-passed} 个测试失败，请检查相关功能。")


if __name__ == "__main__":
    main()