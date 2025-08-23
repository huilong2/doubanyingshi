#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试账号调试信息
验证账号序号和账号信息的显示
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'liulanqimokuai'))

from zhixingliucheng import panduan_zhanghaoshifoudenglu
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_account_debug():
    """测试账号调试信息"""
    print("🧪 开始测试账号调试信息...")
    
    try:
        # 调用账号判断函数
        result = panduan_zhanghaoshifoudenglu()
        print(f"\n📊 函数执行结果: {result}")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 账号调试信息测试")
    print("=" * 50)
    
    test_account_debug()
    
    print("\n✅ 测试完成！")

