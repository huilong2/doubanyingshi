import requests

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
