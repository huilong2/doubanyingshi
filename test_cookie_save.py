#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试Cookie是否被正确保存到数据库"""

import sqlite3
import os
from pathlib import Path

# 获取数据库路径
def get_db_path():
    """获取数据库文件路径"""
    data_dir = Path(__file__).parent / "data"
    return data_dir / "accounts.db"

# 测试Cookie保存
def test_cookie_save():
    """测试Cookie是否被正确保存到数据库"""
    db_path = get_db_path()
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在 - {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有账号的用户名和ck字段
        print("查询数据库中的账号信息...")
        cursor.execute('SELECT username, ck FROM accounts')
        accounts = cursor.fetchall()
        
        if not accounts:
            print("数据库中没有账号信息")
        else:
            print(f"找到 {len(accounts)} 个账号")
            for idx, (username, ck) in enumerate(accounts, 1):
                ck_status = "已保存" if ck else "未保存"
                ck_preview = f"{ck[:30]}..." if ck else "空"
                print(f"账号 {idx}: {username} - Cookie状态: {ck_status}")
                print(f"  Cookie预览: {ck_preview}")
                print(f"  Cookie长度: {len(ck) if ck else 0} 字符")
                print("-")
        
    except Exception as e:
        print(f"查询数据库时出错: {str(e)}")
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始测试Cookie保存功能")
    print("=" * 50)
    test_cookie_save()
    print("=" * 50)
    print("测试完成")