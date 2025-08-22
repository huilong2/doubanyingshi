import os
import json
import random
import logging
import platform
from typing import Optional, Dict, Any
from pathlib import Path


class FingerprintGenerator:
    """浏览器指纹生成器，用于生成和管理浏览器指纹数据"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def generate_random_fingerprint(self) -> Dict[str, Any]:
        """生成随机的浏览器指纹"""
        # 常用的User-Agent列表
        windows_chrome_versions = ['110.0.5481.177', '111.0.5563.111', '112.0.5615.138']
        mac_chrome_versions = ['110.0.5481.177', '111.0.5563.111', '112.0.5615.138']
        
        # 随机选择平台
        os_platform = random.choice(['Windows', 'MacOS'])
        
        if os_platform == 'Windows':
            os_info = random.choice(['Windows NT 10.0', 'Windows NT 11.0'])
            chrome_version = random.choice(windows_chrome_versions)
            platform_info = f"({os_info}; Win64; x64)"
        else:
            os_info = random.choice(['Macintosh', 'MacIntel'])
            chrome_version = random.choice(mac_chrome_versions)
            platform_info = f"({os_info}; Intel Mac OS X 10_15_7)"
        
        # 构建User-Agent
        user_agent = f"Mozilla/5.0 {platform_info} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
        
        # 常用语言设置
        languages = [
            'zh-CN,zh;q=0.9,en;q=0.8',
            'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'zh-CN,zh;q=0.9',
            'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        ]
        
        return {
            'user_agent': user_agent,
            'platform': os_platform,
            'language': random.choice(languages),
            'screen': {
                'width': random.choice([1920, 2560, 3840]),
                'height': random.choice([1080, 1440, 2160]),
                'depth': 24
            }
        }
        
    def load_fingerprint_from_file(self, cache_dir: str) -> Optional[Dict[str, Any]]:
        """从文件加载指纹数据"""
        try:
            fingerprint_path = Path(cache_dir) / 'fingerprint.json'
            if not fingerprint_path.exists():
                return None
                
            with fingerprint_path.open('r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载指纹数据时出错: {str(e)}")
            return None
            
    def save_fingerprint_to_file(self, fingerprint: Dict[str, Any], cache_dir: str) -> bool:
        """保存指纹数据到文件"""
        try:
            fingerprint_path = Path(cache_dir) / 'fingerprint.json'
            fingerprint_path.parent.mkdir(parents=True, exist_ok=True)
            
            with fingerprint_path.open('w', encoding='utf-8') as f:
                json.dump(fingerprint, f, ensure_ascii=False, indent=2)
            return True
            
        except Exception as e:
            self.logger.error(f"保存指纹数据时出错: {str(e)}")
            return False


class FingerprintManager:
    """浏览器指纹管理器，用于管理每个账号的独立指纹数据"""
    
    def __init__(self):
        self.generator = FingerprintGenerator()
        self.logger = logging.getLogger(__name__)
    
    def ensure_account_fingerprint(self, account_cache_dir: str) -> Optional[Dict[str, Any]]:
        """
        确保账号有指纹数据：
        - 如果账号目录下已存在指纹文件，则加载它
        - 如果不存在，则生成新的指纹数据并保存
        
        Args:
            account_cache_dir: 账号缓存目录路径
            
        Returns:
            Dict[str, Any]: 指纹数据字典，如果失败则返回None
        """
        try:
            # 确保账号缓存目录存在
            cache_path = Path(account_cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # 指纹文件路径
            fingerprint_file = cache_path / "fingerprint.json"
            
            # 检查指纹文件是否存在
            if fingerprint_file.exists():
                # 加载已存在的指纹数据
                fingerprint = self.generator.load_fingerprint_from_file(str(cache_path))
                if fingerprint:
                    self.logger.info(f"已加载账号 {account_cache_dir} 的指纹数据")
                    return fingerprint
                else:
                    self.logger.warning(f"加载账号 {account_cache_dir} 的指纹数据失败，将重新生成")
            
            # 生成新的指纹数据
            self.logger.info(f"为账号 {account_cache_dir} 生成新的指纹数据")
            fingerprint = self.generator.generate_random_fingerprint()
            
            # 保存指纹数据
            if self.generator.save_fingerprint_to_file(fingerprint, str(cache_path)):
                self.logger.info(f"已保存账号 {account_cache_dir} 的指纹数据")
                return fingerprint
            else:
                self.logger.error(f"保存账号 {account_cache_dir} 的指纹数据失败")
                return None
                
        except Exception as e:
            self.logger.error(f"处理账号 {account_cache_dir} 的指纹数据时出错: {str(e)}")
            return None
    
    def get_account_fingerprint(self, account_cache_dir: str) -> Optional[Dict[str, Any]]:
        """
        获取账号的指纹数据（仅加载，不生成）
        
        Args:
            account_cache_dir: 账号缓存目录路径
            
        Returns:
            Dict[str, Any]: 指纹数据字典，如果失败或文件不存在则返回None
        """
        try:
            fingerprint = self.generator.load_fingerprint_from_file(account_cache_dir)
            if fingerprint:
                self.logger.info(f"已加载账号 {account_cache_dir} 的指纹数据")
                return fingerprint
            else:
                self.logger.warning(f"账号 {account_cache_dir} 的指纹数据文件不存在")
                return None
                
        except Exception as e:
            self.logger.error(f"加载账号 {account_cache_dir} 的指纹数据时出错: {str(e)}")
            return None
    
    def save_account_fingerprint(self, account_cache_dir: str, fingerprint: Dict[str, Any]) -> bool:
        """
        保存账号的指纹数据
        
        Args:
            account_cache_dir: 账号缓存目录路径
            fingerprint: 指纹数据字典
            
        Returns:
            bool: 保存是否成功
        """
        try:
            result = self.generator.save_fingerprint_to_file(fingerprint, account_cache_dir)
            if result:
                self.logger.info(f"已保存账号 {account_cache_dir} 的指纹数据")
            else:
                self.logger.error(f"保存账号 {account_cache_dir} 的指纹数据失败")
            return result
            
        except Exception as e:
            self.logger.error(f"保存账号 {account_cache_dir} 的指纹数据时出错: {str(e)}")
            return False