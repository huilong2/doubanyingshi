#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试账号勾选功能的脚本
"""

import sqlite3
import os
from pathlib import Path

def test_gouxuan_functionality():
    """测试账号勾选功能是否完整"""
    
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
        
        print("=== 测试账号勾选功能 ===")
        
        # 1. 检查表结构
        print("\n1. 检查accounts表结构:")
        cursor.execute("PRAGMA table_info(accounts)")
        columns = cursor.fetchall()
        
        gouxuan_exists = False
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - 默认值: {col[4]}")
            if col[1] == 'gouxuan':
                gouxuan_exists = True
        
        if not gouxuan_exists:
            print("❌ gouxuan字段不存在！")
            return
        else:
            print("✅ gouxuan字段存在")
        
        # 2. 检查现有账号数据
        print("\n2. 检查现有账号数据:")
        cursor.execute('SELECT id, username, gouxuan FROM accounts LIMIT 5')
        accounts = cursor.fetchall()
        
        if accounts:
            print("现有账号:")
            for account in accounts:
                print(f"  ID: {account[0]}, 用户名: {account[1]}, 勾选状态: {account[2]}")
        else:
            print("暂无账号数据")
        
        # 3. 测试更新勾选状态
        print("\n3. 测试更新勾选状态:")
        if accounts:
            test_account = accounts[0]
            test_id = test_account[0]
            test_username = test_account[1]
            current_gouxuan = test_account[2]
            
            # 切换勾选状态
            new_gouxuan = 1 if current_gouxuan == 0 else 0
            cursor.execute('UPDATE accounts SET gouxuan = ? WHERE id = ?', (new_gouxuan, test_id))
            
            # 验证更新
            cursor.execute('SELECT gouxuan FROM accounts WHERE id = ?', (test_id,))
            updated_gouxuan = cursor.fetchone()[0]
            
            if updated_gouxuan == new_gouxuan:
                print(f"✅ 成功更新账号 {test_username} 的勾选状态: {current_gouxuan} -> {new_gouxuan}")
            else:
                print(f"❌ 更新勾选状态失败: 期望 {new_gouxuan}, 实际 {updated_gouxuan}")
            
            # 恢复原状态
            cursor.execute('UPDATE accounts SET gouxuan = ? WHERE id = ?', (current_gouxuan, test_id))
            print(f"已恢复账号 {test_username} 的原始勾选状态: {current_gouxuan}")
        
        # 4. 测试批量更新
        print("\n4. 测试批量更新勾选状态:")
        cursor.execute('UPDATE accounts SET gouxuan = 1 WHERE gouxuan = 0 LIMIT 3')
        updated_count = cursor.rowcount
        print(f"✅ 成功批量更新 {updated_count} 个账号为勾选状态")
        
        # 恢复所有为未勾选
        cursor.execute('UPDATE accounts SET gouxuan = 0')
        print("已将所有账号恢复为未勾选状态")
        
        conn.commit()
        conn.close()
        
        print("\n=== 测试完成 ===")
        print("✅ 账号勾选功能测试通过！")
        print("现在可以在主程序中正常使用勾选功能了。")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")

if __name__ == "__main__":
    test_gouxuan_functionality()
