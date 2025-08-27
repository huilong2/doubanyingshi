import os
import json
import random
import logging
import platform
from typing import Optional, Dict, Any
from pathlib import Path

from data_manager import DataManager


class FingerprintGenerator:
    """浏览器指纹生成器，用于生成和管理浏览器指纹数据"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def generate_random_fingerprint(self) -> Dict[str, Any]:
        """生成随机的浏览器指纹"""
        # 常用的User-Agent列表
        windows_chrome_versions = ['110.0.5481.177', '111.0.5563.111', '112.0.5615.138', '113.0.5672.63', '114.0.5735.198']
        mac_chrome_versions = ['110.0.5481.177', '111.0.5563.111', '112.0.5615.138', '113.0.5672.63', '114.0.5735.198']
        
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
        ]
        
        # 屏幕分辨率 - 更真实的分辨率组合
        screen_resolutions = [
            # 常见笔记本分辨率
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1600, 'height': 900},
            {'width': 1920, 'height': 1080},
            {'width': 1920, 'height': 1200},
            
            # 常见桌面分辨率
            {'width': 1680, 'height': 1050},
            {'width': 1920, 'height': 1080},
            {'width': 2560, 'height': 1440},
            {'width': 2560, 'height': 1600},
            {'width': 3440, 'height': 1440},  # 超宽屏
            {'width': 3840, 'height': 2160},  # 4K
        ]
        
        # 时区
        timezones = [
            'Asia/Shanghai',
            'Asia/Beijing',
            'Asia/Hong_Kong',
            'Asia/Taipei',
            'Asia/Singapore',
        ]
        
        # WebGL厂商和渲染器
        webgl_vendors = [
            'Google Inc. (Intel)',
            'Google Inc. (NVIDIA)',
            'Google Inc. (AMD)',
            'Intel Inc.',
            'NVIDIA Corporation',
            'AMD',
        ]
        
        webgl_renderers = [
            'Intel Iris OpenGL Engine',
            'NVIDIA GeForce GTX 1060/PCIe/SSE2',
            'AMD Radeon Pro 5500M OpenGL Engine',
            'Intel(R) UHD Graphics 620',
            'NVIDIA GeForce RTX 3060/PCIe/SSE2',
            'AMD Radeon RX 6600 XT',
        ]
        
        # 常用字体
        fonts = [
            'Arial', 'Helvetica', 'Times New Roman', 'Times', 'Courier New', 'Courier',
            'Verdana', 'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS',
            'Trebuchet MS', 'Arial Black', 'Impact', 'Lucida Sans Unicode', 'Tahoma',
            'Lucida Grande', 'Geneva', 'Monaco', 'Andale Mono', 'DejaVu Sans Mono',
            'Liberation Sans', 'Nimbus Sans L', 'FreeSans', 'Bitstream Vera Sans',
            'Lucida Console', 'Monaco', 'Consolas', 'Source Code Pro', 'Menlo',
            'Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi',
            'STXihei', 'STKaiti', 'STSong', 'STZhongsong', 'STFangsong', 'STHupo',
        ]
        
        # 浏览器插件
        plugins = [
            'Chrome PDF Plugin',
            'Chrome PDF Viewer',
            'Native Client',
            'Widevine Content Decryption Module',
            'Shockwave Flash',
            'Adobe Flash Player',
        ]
        
        # 生成指纹数据
        fingerprint = {
            'user_agent': user_agent,
            'platform': os_platform,
            'language': random.choice(languages),
            'screen': random.choice(screen_resolutions),
            'color_depth': random.choice([24, 32]),
            'timezone': random.choice(timezones),
            'webgl_vendor': random.choice(webgl_vendors),
            'webgl_renderer': random.choice(webgl_renderers),
            'fonts': random.sample(fonts, random.randint(20, 35)),
            'plugins': random.sample(plugins, random.randint(3, 6)),
            'canvas': self._generate_canvas_fingerprint(),
            'audio': self._generate_audio_fingerprint(),
            'media_devices': self._generate_media_devices(),
            'geolocation': self._generate_geolocation(),
            'hardware_concurrency': random.choice([4, 6, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16, 32]),
            'max_touch_points': random.choice([0, 1, 5, 10]),
            'connection': self._generate_connection_info(),
            'battery': self._generate_battery_info(),
            'permissions': self._generate_permissions(),
        }
        
        return fingerprint
    
    def _generate_canvas_fingerprint(self) -> str:
        """生成更真实的Canvas指纹"""
        import hashlib
        
        # 模拟Canvas绘制操作生成的内容
        # 实际浏览器中，Canvas指纹基于Canvas API绘制的图形计算
        canvas_content = [
            f"Mozilla-Canvas-rendering; {random.randint(1000000, 9999999)}",
            f"{random.choice(['Intel', 'NVIDIA', 'AMD'])} GPU acceleration; version={random.random():.6f}",
            f"Text rendering; size={random.randint(10, 30)}px; font={random.choice(['Arial', 'Times', 'Courier'])};",
            f"Gradient test; colors={random.randint(1, 10)}; steps={random.randint(5, 50)};",
            f"Image data; width={random.randint(100, 300)}; height={random.randint(100, 300)};",
            f"Canvas context properties; alpha={random.choice([True, False])}; premultipliedAlpha={random.choice([True, False])};",
            f"Antialiasing settings; mode={random.choice(['default', 'none', 'fast', 'good', 'best'])};",
            f"Pixel aspect ratio; value={random.uniform(0.9, 1.1):.6f};",
        ]
        
        # 随机选择一些内容组合
        selected_content = random.sample(canvas_content, random.randint(3, 6))
        content_str = "|".join(selected_content)
        
        # 计算哈希值
        canvas_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        # 添加一些指纹标识前缀，使其看起来更真实
        prefixes = ['canvas-', 'fp-', 'browser-', 'graphics-']
        return f"{random.choice(prefixes)}{canvas_hash}"
    
    def _generate_audio_fingerprint(self) -> str:
        """生成更真实的音频指纹"""
        import hashlib
        
        # 模拟AudioContext API生成的音频特征
        audio_content = [
            f"AudioContext; sampleRate={random.choice([44100, 48000, 96000])}Hz",
            f"Audio latency; input={random.uniform(0.01, 0.1):.6f}s; output={random.uniform(0.01, 0.1):.6f}s",
            f"Audio backend; {random.choice(['WebAudio', 'OpenAL', 'DirectSound'])}; version={random.randint(1, 3)}.{random.randint(0, 9)}",
            f"Supported formats; {random.sample(['MP3', 'AAC', 'OGG', 'WAV', 'FLAC'], random.randint(2, 5))}",
            f"Hardware acceleration; {random.choice(['true', 'false'])}; vendor={random.choice(['Intel', 'NVIDIA', 'AMD', 'Realtek'])}",
            f"Channel configuration; input={random.choice([1, 2, 4, 6])}; output={random.choice([1, 2, 4, 6, 8])}",
            f"Bit depth; {random.choice([16, 24, 32])}bit; float={random.choice([True, False])}",
            f"Audio processing; {random.choice(['real-time', 'buffered'])}; latencyHint={random.choice(['balanced', 'interactive', 'playback'])}",
        ]
        
        # 随机选择一些内容组合
        selected_content = random.sample(audio_content, random.randint(3, 6))
        content_str = "|".join(str(item) for item in selected_content)
        
        # 计算哈希值
        audio_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        # 添加一些指纹标识前缀，使其看起来更真实
        prefixes = ['audio-', 'sound-', 'media-', 'webaudio-']
        return f"{random.choice(prefixes)}{audio_hash}"
    
    def _generate_media_devices(self) -> Dict[str, Any]:
        """生成媒体设备信息"""
        return {
            'audioinput': random.randint(1, 3),
            'audiooutput': random.randint(1, 2),
            'videoinput': random.randint(1, 2),
        }
    
    def _generate_geolocation(self) -> Dict[str, float]:
        """生成地理位置信息"""
        # 中国主要城市的经纬度范围
        latitude = random.uniform(18.0, 53.0)  # 中国纬度范围
        longitude = random.uniform(73.0, 135.0)  # 中国经度范围
        return {
            'latitude': round(latitude, 6),
            'longitude': round(longitude, 6),
            'accuracy': random.uniform(10, 100),
        }
    
    def _generate_connection_info(self) -> Dict[str, Any]:
        """生成网络连接信息"""
        connection_types = ['wifi', '4g', '5g', 'ethernet']
        return {
            'type': random.choice(connection_types),
            'downlink': random.uniform(10, 100),
            'rtt': random.uniform(10, 100),
            'effectiveType': random.choice(['slow-2g', '2g', '3g', '4g']),
        }
    
    def _generate_battery_info(self) -> Dict[str, Any]:
        """生成电池信息"""
        return {
            'charging': random.choice([True, False]),
            'level': random.uniform(0.1, 1.0),
            'chargingTime': random.randint(0, 3600) if random.choice([True, False]) else float('inf'),
            'dischargingTime': random.randint(1800, 7200),
        }
    
    def _generate_permissions(self) -> Dict[str, str]:
        """生成权限信息"""
        return {
            'geolocation': random.choice(['granted', 'denied', 'prompt']),
            'notifications': random.choice(['granted', 'denied', 'prompt']),
            'camera': random.choice(['granted', 'denied', 'prompt']),
            'microphone': random.choice(['granted', 'denied', 'prompt']),
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
        self.data_manager = DataManager()
    
    def ensure_account_fingerprint(self, account_cache_dir: str) -> Optional[Dict[str, Any]]:
        """
        确保账号有指纹数据：
        - 优先从数据库加载指纹数据
        - 如果数据库中不存在，尝试从文件加载
        - 如果都不存在，则生成新的指纹数据并保存到数据库和文件
        
        Args:
            account_cache_dir: 账号缓存目录路径
            
        Returns:
            Dict[str, Any]: 指纹数据字典，如果失败则返回None
        """
        try:
            # 获取账号ID
            account_id = self.data_manager.get_account_id_by_cache_dir(account_cache_dir)
            
            # 优先从数据库加载指纹数据
            if account_id:
                fingerprint = self.data_manager.load_fingerprint(account_id)
                if fingerprint:
                    self.logger.info(f"已从数据库加载账号ID {account_id} 的指纹数据")
                    return fingerprint
            
            # 确保账号缓存目录存在
            cache_path = Path(account_cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # 指纹文件路径
            fingerprint_file = cache_path / "fingerprint.json"
            
            # 检查指纹文件是否存在（向后兼容）
            if fingerprint_file.exists():
                # 加载已存在的指纹数据
                fingerprint = self.generator.load_fingerprint_from_file(str(cache_path))
                if fingerprint:
                    self.logger.info(f"已从文件加载账号 {account_cache_dir} 的指纹数据")
                    # 如果能获取到账号ID，将指纹数据保存到数据库
                    if account_id:
                        self.data_manager.save_fingerprint(account_id, fingerprint)
                    return fingerprint
                else:
                    self.logger.warning(f"加载账号 {account_cache_dir} 的指纹数据失败，将重新生成")
            
            # 生成新的指纹数据
            self.logger.info(f"为账号 {account_cache_dir} 生成新的指纹数据")
            fingerprint = self.generator.generate_random_fingerprint()
            
            # 保存指纹数据到数据库
            if account_id:
                self.data_manager.save_fingerprint(account_id, fingerprint)
                self.logger.info(f"已保存账号ID {account_id} 的指纹数据到数据库")
            
            # 同时保存到文件（向后兼容）
            if self.generator.save_fingerprint_to_file(fingerprint, str(cache_path)):
                self.logger.info(f"已保存账号 {account_cache_dir} 的指纹数据到文件")
            else:
                self.logger.warning(f"保存账号 {account_cache_dir} 的指纹数据到文件失败")
            
            return fingerprint
                
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
            # 获取账号ID
            account_id = self.data_manager.get_account_id_by_cache_dir(account_cache_dir)
            
            # 优先从数据库加载指纹数据
            if account_id:
                fingerprint = self.data_manager.load_fingerprint(account_id)
                if fingerprint:
                    self.logger.info(f"已从数据库加载账号ID {account_id} 的指纹数据")
                    return fingerprint
            
            # 如果数据库中没有，尝试从文件加载（向后兼容）
            fingerprint = self.generator.load_fingerprint_from_file(account_cache_dir)
            if fingerprint:
                self.logger.info(f"已从文件加载账号 {account_cache_dir} 的指纹数据")
                # 如果能获取到账号ID，将指纹数据保存到数据库
                if account_id:
                    self.data_manager.save_fingerprint(account_id, fingerprint)
                return fingerprint
            else:
                self.logger.warning(f"账号 {account_cache_dir} 的指纹数据不存在")
                return None
                
        except Exception as e:
            self.logger.error(f"加载账号 {account_cache_dir} 的指纹数据时出错: {str(e)}")
            return None
    
    def save_account_fingerprint(self, account_cache_dir: str, fingerprint: Dict[str, Any]) -> bool:
        """
        保存账号的指纹数据到数据库和文件
        
        Args:
            account_cache_dir: 账号缓存目录路径
            fingerprint: 指纹数据字典
            
        Returns:
            bool: 保存是否成功（只要数据库或文件任一保存成功即返回True）
        """
        try:
            success = False
            
            # 获取账号ID
            account_id = self.data_manager.get_account_id_by_cache_dir(account_cache_dir)
            
            # 保存到数据库
            if account_id:
                db_result = self.data_manager.save_fingerprint(account_id, fingerprint)
                if db_result:
                    self.logger.info(f"已保存账号ID {account_id} 的指纹数据到数据库")
                    success = True
                else:
                    self.logger.error(f"保存账号ID {account_id} 的指纹数据到数据库失败")
            
            # 同时保存到文件（向后兼容）
            file_result = self.generator.save_fingerprint_to_file(fingerprint, account_cache_dir)
            if file_result:
                self.logger.info(f"已保存账号 {account_cache_dir} 的指纹数据到文件")
                success = True
            else:
                self.logger.warning(f"保存账号 {account_cache_dir} 的指纹数据到文件失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存账号 {account_cache_dir} 的指纹数据时出错: {str(e)}")
            return False