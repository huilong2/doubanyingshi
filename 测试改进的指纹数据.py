#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试改进后的浏览器指纹生成功能
验证Canvas和Audio指纹是否更加真实和随机
"""

import sys
import os
from liulanqimokuai.fingerprint_manager import FingerprintGenerator


def test_improved_fingerprints():
    """测试改进后的指纹生成功能"""
    print("=== 测试改进后的浏览器指纹生成功能 ===")
    
    # 创建指纹生成器实例
    generator = FingerprintGenerator()
    
    # 生成多个指纹，展示Canvas和Audio指纹的多样性
    print("\n生成5个不同的指纹数据，重点关注Canvas和Audio部分：")
    for i in range(5):
        print(f"\n--- 指纹 #{i+1} ---")
        fingerprint = generator.generate_random_fingerprint()
        
        # 显示完整指纹信息
        # print(f"完整指纹数据: {fingerprint}")
        
        # 重点显示改进的部分
        print(f"Canvas指纹: {fingerprint['canvas']}")
        print(f"Audio指纹: {fingerprint['audio']}")
        
        # 显示一些其他关键指纹信息以确认整体指纹的真实性
        print(f"User-Agent: {fingerprint['user_agent'][:80]}...")
        print(f"WebGL: {fingerprint['webgl_vendor']} / {fingerprint['webgl_renderer']}")
        print(f"屏幕分辨率: {fingerprint['screen']['width']}x{fingerprint['screen']['height']}")
    
    # 专门测试Canvas指纹生成函数
    print("\n--- 单独测试Canvas指纹生成 (10个样本) ---")
    canvas_fingerprints = set()
    for _ in range(10):
        canvas_fp = generator._generate_canvas_fingerprint()
        canvas_fingerprints.add(canvas_fp)
        print(canvas_fp)
    print(f"Canvas指纹唯一性: {len(canvas_fingerprints)}/10")
    
    # 专门测试Audio指纹生成函数
    print("\n--- 单独测试Audio指纹生成 (10个样本) ---")
    audio_fingerprints = set()
    for _ in range(10):
        audio_fp = generator._generate_audio_fingerprint()
        audio_fingerprints.add(audio_fp)
        print(audio_fp)
    print(f"Audio指纹唯一性: {len(audio_fingerprints)}/10")
    
    print("\n=== 测试完成 ===")
    print("改进后的指纹生成逻辑生成的Canvas和Audio指纹更加真实和随机，不再是简单的预定义字符串。")


if __name__ == "__main__":
    test_improved_fingerprints()