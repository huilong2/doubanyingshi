import requests
import re
import sys
import json
import time

# 确保中文显示正常
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def 获取ai短语(movie_id):
    url = f'http://127.0.0.1:8001/get_movie_name/{movie_id}'
    try:
        response = requests.get(url, headers={'accept': 'application/json'})
        if response.status_code == 200:
            data = response.json()
            # 确保JSON结构正确并获取content字段
            if 'choices' in data and data['choices'] and isinstance(data['choices'], list) and \
               'message' in data['choices'][0] and 'content' in data['choices'][0]['message']:
                content = data['choices'][0]['message']['content']
                return content
            else:
                print(f"警告: JSON响应格式不正确，缺少必要字段")
                return None
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取AI短语时发生错误: {str(e)}")
        return None

def huo_qu_dai_li(tiquApiUrl, max_retries=3):
    """获取代理IP，失败时最多重试指定次数"""
    for attempt in range(1, max_retries + 1):
        print(f"第{attempt}次尝试获取代理...")
        try:
            apiRes = requests.get(tiquApiUrl, timeout=5)
            
            # 首先检查响应状态
            if apiRes.status_code != 200:
                print(f"API请求失败，状态码: {apiRes.status_code}")
                if attempt < max_retries:
                    print("准备重试...")
                    time.sleep(2)  # 间隔2秒后重试
                continue
            
            # 获取原始文本
            ip = apiRes.text.strip()
            print(f"获取到的原始数据: {ip}")
            
            # 进行IP格式有效性检查
            if not ip:
                print("获取的IP为空")
                if attempt < max_retries:
                    print("准备重试...")
                    time.sleep(2)
                continue
            
            # 检查是否为JSON格式的错误响应
            if ip.startswith('{') and ip.endswith('}'):
                try:
                    data = json.loads(ip)
                    if isinstance(data, dict) and ('code' in data and data['code'] != 0):
                        print(f"API返回错误: code={data.get('code')}, info={data.get('info', '未知错误')}")
                        if attempt < max_retries:
                            print("准备重试...")
                            time.sleep(2)
                        continue
                except json.JSONDecodeError:
                    pass  # 不是有效的JSON
            
            # 简单的IP格式验证 (支持IPv4和包含端口的格式)
            if re.match(r'^\d+\.\d+\.\d+\.\d+(?:\:\d+)?$', ip):
                # 验证代理IP是否有效
                check_url = f'http://ip.hl22.com/ip.php?action=getip&ip_url={ip}'
                response = requests.get(check_url, timeout=5)
                
                if response.status_code == 200:
                    response_text = response.text.strip()
                    print(f"代理验证响应: {response_text}")
                    # 提取地理位置信息
                    location = ""
                    if '来自：' in response_text:
                        # 提取'来自：'后面的内容
                        location_part = response_text.split('来自：')[-1]
                        # 移除可能的HTML标签
                        location = re.sub(r'<[^>]+>', '', location_part).strip()
                    # 返回True, IP和地理位置信息
                    return True, ip, location
                else:
                    print(f"代理验证请求失败，状态码: {response.status_code}")
                    if attempt < max_retries:
                        print("准备重试...")
                        time.sleep(2)
                    continue
            else:
                print(f"获取的IP格式无效: {ip}")
                if attempt < max_retries:
                    print("准备重试...")
                    time.sleep(2)
                continue
                
        except requests.RequestException as e:
            print(f"请求异常: {str(e)}")
            if attempt < max_retries:
                print("准备重试...")
                time.sleep(2)
            continue
    
    # 所有尝试都失败
    return False, None, None



# success, ip, location =huo_qu_dai_li('http://proxy.siyetian.com/apis_get.html?token=1AesJWLNp2Z31kaJdXTqFFeNRUQz4ERVdXTn1STqFUeORUR31ERjBTTEFEeOR0a65EVnpnT6d2M.AO3UzM1QjN1cTM&limit=1&type=0&time=&split=1&split_text=')
# print(success, ip, location)