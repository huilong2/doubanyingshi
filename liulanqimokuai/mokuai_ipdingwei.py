import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_ip_geolocation(ip_address):
    """使用IP-API获取IP地理位置信息"""
    url = f"http://ip-api.com/json/{ip_address}"
    try:
        response = requests.get(url, timeout=10)  # 添加超时设置
        if response.status_code != 200:
            return {'error': f'IP-API 请求失败，状态码：{response.status_code}'}
            
        data = response.json()
        if data.get('status') == 'success':
            return {
                'latitude': str(data.get('lat', '')),
                'longitude': str(data.get('lon', ''))
            }
        else:
            return {'error': data.get('message', 'IP-API 查询失败')}
    except requests.exceptions.Timeout:
        return {'error': 'IP-API 请求超时'}
    except requests.exceptions.RequestException as e:
        return {'error': f'IP-API 请求异常：{str(e)}'}
    except Exception as e:
        return {'error': f'IP-API 未知错误：{str(e)}'}

def get_ip_geolocation_ipshu(ip_address):
    """使用IPSHU获取IP地理位置信息作为备用方案"""
    url = f"https://zh-hans.ipshu.com/ipv4/{ip_address}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)  # 添加超时设置
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 只提取纬度和经度信息
            location_info = {}
            
            # 查找包含地理位置信息的表格
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).replace(':', '').strip()
                        value = cols[1].get_text(strip=True)
                        if '纬度' in key:
                            location_info['latitude'] = value
                        elif '经度' in key:
                            location_info['longitude'] = value
            
            if 'latitude' in location_info and 'longitude' in location_info:
                return {
                    'latitude': location_info['latitude'],
                    'longitude': location_info['longitude']
                }
            else:
                return {'error': '未找到经纬度信息'}
        else:
            return {'error': f'IPSHU 请求失败，状态码：{response.status_code}'}
    except requests.exceptions.Timeout:
        return {'error': 'IPSHU 请求超时'}
    except requests.exceptions.RequestException as e:
        return {'error': f'IPSHU 请求异常：{str(e)}'}
    except Exception as e:
        return {'error': f'IPSHU 未知错误：{str(e)}'}

def get_ip_location(ip_address):
    """
    获取IP地址的地理位置信息，优先使用IP-API，如果失败则尝试IPSHU
    
    Args:
        ip_address: IP地址字符串
        
    Returns:
        dict: 包含地理位置信息的字典，格式为 {'latitude': str, 'longitude': str}
              如果获取失败则包含error键
    """
    logger.debug(f"开始获取IP地址 {ip_address} 的地理位置信息")
    
    # 首先尝试 IP-API
    result = get_ip_geolocation(ip_address)
    if 'error' not in result:
        logger.info(f"通过IP-API成功获取IP {ip_address} 的位置信息")
        return result
    
    logger.warning(f"IP-API获取失败: {result.get('error')}，尝试备用方案")
    
    # 如果 IP-API 失败，尝试 IPSHU
    result = get_ip_geolocation_ipshu(ip_address)
    if 'error' not in result:
        logger.info(f"通过IPSHU成功获取IP {ip_address} 的位置信息")
        return result
    
    logger.error(f"所有IP定位服务均失败: {result.get('error')}")
    return result