#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试gouxuan字段的脚本
"""

import sqlite3
import os
from pathlib import Path

def test_gouxuan_field():
    """测试gouxuan字段是否正常工作"""
    
    # 获取数据库路径
    data_dir = Path(__file__).parent / "data"
    db_path = data_dir / "accounts.db"
    
    if not db_path.exists():
        print("数据库文件不存在，请先运行主程序创建数据库")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查accounts表结构
        print("=== 检查accounts表结构 ===")
        cursor.execute("PRAGMA table_info(accounts)")
        columns = cursor.fetchall()
        
        print("accounts表的字段:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - 默认值: {col[4]}")
        
        # 检查是否有gouxuan字段
        gouxuan_exists = any(col[1] == 'gouxuan' for col in columns)
        print(f"\ngouxuan字段存在: {gouxuan_exists}")
        
        if gouxuan_exists:
            # 测试插入一条测试数据
            print("\n=== 测试插入数据 ===")
            try:
                cursor.execute('''
                    INSERT INTO accounts (username, password, gouxuan) 
                    VALUES (?, ?, ?)
                ''', ('test_user', 'test_pass', 1))
                print("成功插入测试数据")
                
                # 查询数据验证
                cursor.execute('SELECT username, gouxuan FROM accounts WHERE username = ?', ('test_user',))
                result = cursor.fetchone()
                if result:
                    print(f"查询结果: username={result[0]}, gouxuan={result[1]}")
                
                # 清理测试数据
                cursor.execute('DELETE FROM accounts WHERE username = ?', ('test_user',))
                print("已清理测试数据")
                
            except Exception as e:
                print(f"插入测试数据时出错: {e}")
        
        # 显示现有账号数据
        print("\n=== 现有账号数据 ===")
        cursor.execute('SELECT username, gouxuan FROM accounts LIMIT 5')
        accounts = cursor.fetchall()
        
        if accounts:
            print("现有账号:")
            for account in accounts:
                print(f"  {account[0]} - gouxuan: {account[1]}")
        else:
            print("暂无账号数据")
        
        conn.commit()
        conn.close()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")

if __name__ == "__main__":
    test_gouxuan_field()
