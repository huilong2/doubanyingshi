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
        """生成随机的浏览器指纹 - Windows专用"""
        # 常用的Chrome版本列表（针对Windows系统）
        windows_chrome_versions = [
            '110.0.5481.177', '111.0.5563.111', '112.0.5615.138', 
            '113.0.5672.63', '114.0.5735.198', '115.0.5790.171',
            '116.0.5845.188', '117.0.5938.132', '118.0.5993.118'
        ]
        
        # 固定为Windows平台
        os_platform = 'Windows'
        
        # Windows版本列表
        windows_versions = [
            'Windows NT 10.0',  # Windows 10
            'Windows NT 11.0',  # Windows 11
            'Windows NT 6.3',   # Windows 8.1
            'Windows NT 6.2',   # Windows 8
            'Windows NT 6.1',   # Windows 7
            'Windows NT 6.0',   # Windows Vista
        ]
        
        os_info = random.choice(windows_versions)
        chrome_version = random.choice(windows_chrome_versions)
        
        # 系统架构
        architecture = random.choice(['Win64; x64', 'Win32'])
        platform_info = f"({os_info}; {architecture})"
        
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
        ]
        
        # WebGL厂商和渲染器（Windows系统特有）
        webgl_vendors = [
            'Google Inc. (Intel)',
            'Google Inc. (NVIDIA)',
            'Google Inc. (AMD)',
            'Intel Corporation',
            'NVIDIA Corporation',
            'Advanced Micro Devices, Inc.',
            'Microsoft Corporation',
        ]
        
        webgl_renderers = [
            'Intel(R) UHD Graphics 620',
            'Intel(R) HD Graphics 630',
            'NVIDIA GeForce GTX 1060/PCIe/SSE2',
            'NVIDIA GeForce RTX 3060/PCIe/SSE2',
            'NVIDIA GeForce RTX 2060/PCIe/SSE2',
            'AMD Radeon RX 580 Series',
            'AMD Radeon RX 6600 XT',
            'AMD Radeon(TM) Vega 8 Graphics',
            'Microsoft Basic Render Driver',
            'Intel(R) Iris(R) Plus Graphics',
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
        
        # 生成指纹数据 - Windows专用
        fingerprint = {
            'user_agent': user_agent,
            'platform': os_platform,
            'platform_details': {
                'os_version': os_info,
                'architecture': architecture,
                'windows_build': random.randint(17000, 22000),  # Windows 10/11 版本号范围
            },
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
            'hardware_concurrency': random.choice([2, 4, 6, 8, 12, 16, 24]),  # 增加更多CPU核心数选项
            'device_memory': random.choice([2, 4, 8, 16, 32, 64]),  # 增加更多内存选项
            'max_touch_points': random.choice([0, 1, 5, 10]) if 'NT 10.0' in os_info or 'NT 11.0' in os_info else 0,  # 仅Win10/11支持触摸屏
            'connection': self._generate_connection_info(),
            'battery': self._generate_battery_info(),
            'permissions': self._generate_permissions(),
            # Windows特有指纹信息
            'windows_specific': {
                'device_id': f'{{{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}}}',
                'os_build': f'{random.randint(10, 25)}.{random.randint(0, 999)}.{random.randint(1000, 9999)}',
                'defender_status': random.choice(['enabled', 'disabled']),
                'edge_version': f'{random.randint(90, 118)}.{random.randint(0, 9999)}.{random.randint(0, 9999)}.{random.randint(0, 9999)}',
            }
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
        
class FingerprintManager:
    """浏览器指纹管理器，用于管理每个账号的独立指纹数据"""
    
    def __init__(self):
        self.generator = FingerprintGenerator()
        self.logger = logging.getLogger(__name__)
        self.data_manager = DataManager()
    
    def ensure_account_fingerprint(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        确保账号有指纹数据：
        - 只从数据库加载指纹数据
        - 如果数据库中不存在且提供了account_id，则生成新的指纹数据并保存到数据库
        
        Args:
            account_id: 账号ID
            
        Returns:
            Dict[str, Any]: 指纹数据字典，如果失败则返回None
        """
        try:
            # 尝试从数据库获取指纹数据
            fingerprint_json = self.data_manager.get_account_fingerprint(account_id)
            if fingerprint_json:
                try:
                    fingerprint = json.loads(fingerprint_json)
                    self.logger.info(f"已从数据库加载账号 {account_id} 的指纹数据")
                    return fingerprint
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析数据库中的指纹数据失败: {str(e)}")
            
            # 如果数据库中没有指纹数据，生成新的指纹数据
            self.logger.info(f"为账号 {account_id} 生成新的指纹数据")
            fingerprint = self.generator.generate_random_fingerprint()
            
            # 保存指纹数据到数据库
            fingerprint_json = json.dumps(fingerprint, ensure_ascii=False)
            if self.data_manager.update_account_fingerprint(account_id, fingerprint_json):
                self.logger.info(f"已保存账号 {account_id} 的指纹数据到数据库")
            else:
                self.logger.warning(f"保存账号 {account_id} 的指纹数据到数据库失败")
            
            return fingerprint
                
        except Exception as e:
            self.logger.error(f"处理账号 {account_id} 的指纹数据时出错: {str(e)}")
            return None
    
    def get_account_fingerprint(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        获取账号的指纹数据（仅加载，不生成）
        
        Args:
            account_id: 账号ID
            
        Returns:
            Dict[str, Any]: 指纹数据字典，如果失败则返回None
        """
        try:
            # 尝试从数据库获取指纹数据
            fingerprint_json = self.data_manager.get_account_fingerprint(account_id)
            if fingerprint_json:
                try:
                    fingerprint = json.loads(fingerprint_json)
                    self.logger.info(f"已从数据库加载账号 {account_id} 的指纹数据")
                    return fingerprint
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析数据库中的指纹数据失败: {str(e)}")
                    return None
            
            # 如果数据库中没有数据，返回None
            self.logger.warning(f"账号 {account_id} 的指纹数据不存在")
            return None
                
        except Exception as e:
            self.logger.error(f"加载账号 {account_id} 的指纹数据时出错: {str(e)}")
            return None
    
    def save_account_fingerprint(self, account_id: int, fingerprint: Dict[str, Any]) -> bool:
        """
        保存账号的指纹数据到数据库
        
        Args:
            account_id: 账号ID
            fingerprint: 指纹数据字典
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 保存到数据库
            fingerprint_json = json.dumps(fingerprint, ensure_ascii=False)
            if self.data_manager.update_account_fingerprint(account_id, fingerprint_json):
                self.logger.info(f"已保存账号 {account_id} 的指纹数据到数据库")
                return True
            else:
                self.logger.warning(f"保存账号 {account_id} 的指纹数据到数据库失败")
                return False
            
        except Exception as e:
            self.logger.error(f"保存账号 {account_id} 的指纹数据时出错: {str(e)}")
            return False
    
    def delete_account_fingerprint(self, account_id: int) -> bool:
        """
        从数据库中删除账号的指纹数据
        
        Args:
            account_id: 账号ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 将zhiwenshuju字段设置为空字符串来删除指纹数据
            if self.data_manager.update_account_fingerprint(account_id, ""):
                self.logger.info(f"已删除账号 {account_id} 的指纹数据")
                return True
            else:
                self.logger.warning(f"删除账号 {account_id} 的指纹数据失败")
                return False
                
        except Exception as e:
            self.logger.error(f"删除账号 {account_id} 的指纹数据时出错: {str(e)}")
            return False