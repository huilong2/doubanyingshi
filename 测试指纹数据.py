#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from data_manager import DataManager
from liulanqimokuai.fingerprint_manager import FingerprintGenerator

print("开始测试指纹数据功能...")

# 初始化数据管理器
dm = DataManager()

# 准备测试账号数据
test_account = {
    'username': 'test_zh_account',
    'password': 'test_password',
    'ck': 'test_cookie',
    'nickname': '测试用户',
    'account_id': 'test_account_id',
    'login_status': '未登录',
    'homepage': '',
    'login_time': '',
    'proxy': '',
    'running_status': '',
    'note': '测试账号，用于验证指纹功能'
}

# 先尝试删除测试账号（如果存在）
print("\n1. 清理可能存在的测试账号...")
accounts = dm.get_accounts()
for account in accounts:
    if account[1] == test_account['username']:  # 账号名在第二个位置
        dm.delete_account(account[0])
        print(f"  已删除测试账号: {test_account['username']}")
        break

# 测试添加账号时自动生成指纹数据
print("\n2. 添加测试账号，验证是否自动生成指纹数据...")
result = dm.add_account(test_account)
if result:
    print("  账号添加成功！")
    
    # 查询刚添加的账号，检查指纹数据
    accounts = dm.get_accounts()
    added_account = None
    for account in accounts:
        if account[1] == test_account['username']:
            added_account = account
            break
    
    if added_account and len(added_account) > 13 and added_account[13]:
        print(f"  账号表中的指纹数据字段已填充！")
        fingerprint_data = json.loads(added_account[13])
        print(f"  指纹数据包含以下键: {list(fingerprint_data.keys())}")
    else:
        print("  警告: 账号表中的指纹数据字段为空！")
else:
    print("  账号添加失败！")

# 测试更新指纹数据功能
if added_account:
    account_id = added_account[0]
    print(f"\n3. 测试更新指纹数据功能 (账号ID: {account_id})...")
    
    # 生成新的指纹数据
    generator = FingerprintGenerator()
    new_fingerprint = generator.generate_random_fingerprint()
    
    # 更新指纹数据
    update_result = dm.save_fingerprint(account_id, new_fingerprint)
    if update_result:
        print("  指纹数据更新成功！")
        
        # 验证是否同时更新了accounts表中的zhiwenshuju字段
        accounts = dm.get_accounts()
        updated_account = None
        for account in accounts:
            if account[0] == account_id:
                updated_account = account
                break
        
        if updated_account and len(updated_account) > 13 and updated_account[13]:
            updated_fingerprint = json.loads(updated_account[13])
            print(f"  账号表中的指纹数据已更新，新的指纹数据包含以下键: {list(updated_fingerprint.keys())}")
        else:
            print("  警告: 账号表中的指纹数据字段未更新！")
    else:
        print("  指纹数据更新失败！")

print("\n测试完成！")