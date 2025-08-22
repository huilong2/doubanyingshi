import random
import logging

def get_ip_location(ip: str) -> dict:
    """
    获取IP地址的地理位置信息（简化实现）
    
    Args:
        ip: IP地址字符串
        
    Returns:
        dict: 包含地理位置信息的字典，如果获取失败则包含error键
    """
    try:
        # 简化的实现，随机生成中国地区的经纬度
        # 实际应用中这里应该调用真实的IP地理位置服务API
        latitude = round(random.uniform(20.0, 50.0), 6)  # 中国的纬度范围大致在20-50度之间
        longitude = round(random.uniform(73.0, 136.0), 6)  # 中国的经度范围大致在73-136度之间
        
        return {
            'latitude': latitude,
            'longitude': longitude
        }
    except Exception as e:
        logging.error(f"获取IP地理位置失败: {str(e)}")
        return {
            'error': str(e)
        }