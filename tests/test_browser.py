"""
测试新的浏览器操作模块
"""

import asyncio
import logging
from pathlib import Path
from liulanqi_gongcaozuo import LiulanqiPeizhi, LiulanqiGongcaozuo

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_browser_operations():
    """测试浏览器操作"""
    
    # 创建配置
    peizhi = LiulanqiPeizhi(
        zhanghao="111",
        wangzhi="https://www.douban.com",
        huanchunlujing="E:/liulanqi",
        chrome_path=None,  # 使用默认Chrome路径，让新模块自动查找
        fingerprint={
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'screen_width': 1920,
            'screen_height': 1080
        }
    )
    
    # 创建浏览器操作实例
    liulanqi = LiulanqiGongcaozuo(peizhi)
    
    try:
        print("开始测试浏览器操作...")
        
        # 1. 初始化浏览器
        print("1. 初始化浏览器...")
        await liulanqi.chushihua()
        print(f"浏览器状态: {liulanqi.get_browser_status()}")
        
        # 2. 打开页面
        print("2. 打开豆瓣页面...")
        await liulanqi.dakai_ye()
        print("页面打开成功")
        
        # 3. 执行脚本获取页面标题
        print("3. 获取页面标题...")
        title = await liulanqi.zhixing_script("document.title")
        print(f"页面标题: {title}")
        
        # 4. 检查登录状态
        print("4. 检查登录状态...")
        login_status = await liulanqi.zhixing_script("""
            () => {
                const userAccount = document.querySelector('.nav-user-account') ||
                                  document.querySelector('.user-info');
                return userAccount ? '已登录' : '未登录';
            }
        """)
        print(f"登录状态: {login_status}")
        
        # 5. 等待一段时间
        print("5. 等待5秒...")
        await asyncio.sleep(5)
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        
    finally:
        # 6. 关闭浏览器
        print("6. 关闭浏览器...")
        await liulanqi.guanbi()
        print("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(test_browser_operations())
