import requests
def 获取ai短语(movie_id):
    url = f'http://127.0.0.1:8001/get_movie_name/{movie_id}'
    response = requests.get(url, headers={'accept': 'application/json'})
    if response.status_code == 200:
        content = response.json()['choices'][0]['message']['content']
        return content
    else:
        print(f"请求失败，状态码: {response.status_code}")
        return None
