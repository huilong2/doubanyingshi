import os
import requests
import re
import json
import http.client
from fastapi import FastAPI

app = FastAPI()

# 定义默认端口
DEFAULT_PORT = 8001
# 定义请求头，模拟浏览器访问
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# 定义 API 相关信息
API_HOST = "ark.cn-beijing.volces.com"
API_PATH = "/api/v3/chat/completions"
API_MODEL = "doubao-1-5-lite-32k-250115"
API_AUTH = 'Bearer 100a2599-f1e5-4dec-a901-551c74970e19'


def get_movie_name(url):
    """
    根据电影 URL 获取电影名称
    :param url: 豆瓣电影页面的 URL
    :return: 电影名称或错误信息
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pattern = r'<script\s+type="application/ld\+json">([\s\S]*?)<\/script>'
        match = re.search(pattern, response.text)
        if match:
            json_data = match.group(1)
            data = json.loads(json_data)
            return data.get('name')
        return {"error": "未找到符合条件的 JSON 数据。"}
    except requests.RequestException as e:
        return {"error": f"请求出错: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析出错: {str(e)}"}
    except Exception as e:
        return {"error": f"发生未知错误: {str(e)}"}


def generate_movie_review(movie_name):
    """
    根据电影名称生成短评
    :param movie_name: 电影名称
    :return: 生成的短评或错误信息
    """
    try:
        conn = http.client.HTTPSConnection(API_HOST)
        payload = json.dumps({
            "model": API_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的影视短评撰写人，擅长根据用户提供的影视信息，精准且生动地撰写短评"
                },
                {
                    "role": "user",
                    "content": f"根据电影 {movie_name} 帮我生成一个20 - 50字的短评，不需要带电影名称"
                }
            ]
        })
        headers = {
            'Authorization': API_AUTH,
            'Content-Type': 'application/json'
        }
        conn.request("POST", API_PATH, payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return {"error": f"生成短评时出错: {str(e)}"}


@app.get("/get_movie_name/{movie_id}", summary="获取电影名称并生成短评",
         description="根据豆瓣电影ID获取电影名称并调用API生成短评")
async def get_movie_name_endpoint(movie_id: str):
    """
    根据豆瓣电影ID获取电影名称并生成短评
    :param movie_id: 豆瓣电影ID
    :return: 电影短评或错误信息
    """
    url = f"https://movie.douban.com/subject/{movie_id}/"
    result = get_movie_name(url)
    if isinstance(result, str):
        review = generate_movie_review(result)
        return review
    return result


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", DEFAULT_PORT))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
    