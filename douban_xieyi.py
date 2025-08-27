import requests

def submit_movie_rating(cookie, movie_id, rating, interest, user_agent, comment, proxy=None, verify=True):
    """
    向豆瓣电影提交评分和评论
    
    参数:
        cookie: 包含登录信息的cookie字符串
        movie_id: 电影ID
        rating: 评分(1-5)
        interest: 兴趣类型，如'collect'表示想看
        user_agent: 浏览器的User-Agent字符串
        comment: 评论内容
        proxy: 代理服务器，可选，格式如'http://ip:port'
    """
    print(f"\n=== 开始提交评分和评论 ===")
    print(f"电影ID: {movie_id}")
    print(f"评分: {rating}")
    print(f"兴趣类型: {interest}")
    print(f"评论内容: {'有评论' if comment else '无评论'}")
    print(f"是否使用代理: {'是' if proxy else '否'}")
    
    # 构建请求URL
    url = f"https://movie.douban.com/j/subject/{movie_id}/interest"
    
    # 从cookie中提取ck值
    # 这里简单处理，实际可能需要更健壮的解析
    ck = None
    cookie_parts = cookie.split(';')
    for part in cookie_parts:
        part = part.strip()
        if part.startswith('ck='):
            ck = part[3:]
            break
    
    if not ck:
        print("错误: 未从cookie中找到ck值")
        raise ValueError("未从cookie中找到ck值")
    
    print(f"已从cookie中提取ck值: {'已获取' if ck else '未获取'}")
    
    # 构建请求头
    headers = {
        "Host": "movie.douban.com",
        "Connection": "keep-alive",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": user_agent,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://movie.douban.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": f"https://movie.douban.com/subject/{movie_id}/?_dtcc=1",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cookie": cookie
    }
    
    # 构建请求体
    data = {
        "interest": interest,
        "foldcollect": "F",
        "tags": "",
        "comment": comment,
        "share-shuo": "douban",
        "ck": ck
    }
    
    # 版本2：如果interest不等于"wish"，则添加rating参数
    if interest != "wish":
        data["rating"] = str(rating)
    
    # 构建代理配置
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
    try:
        # 发送POST请求
        print("正在发送请求...")
        response = requests.post(
            url,
            headers=headers,
            data=data,
            proxies=proxies,
            verify=verify  # 使用函数参数，默认为True
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析JSON响应
        result = response.json()
        print(f"请求成功，响应状态码: {response.status_code}")
        print(f"响应结果: {result}")
        print(f"=== 评分和评论提交完成 ===\n")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误状态码: {e.response.status_code}")
            try:
                error_result = e.response.json()
                print(f"错误响应内容: {error_result}")
            except:
                print(f"错误响应内容: {e.response.text}")
        print(f"=== 评分和评论提交失败 ===\n")
        return None

 
 