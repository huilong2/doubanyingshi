import requests
import sqlite3

def get_proxy_ip(proxy_url):
    try:
        response = requests.get(proxy_url, timeout=10)
        if response.status_code == 200:
            # 假设返回的是纯IP地址
            proxy_ip = response.text.strip()
            return proxy_ip
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取代理IP时发生错误: {e}")
        return None
def read_content_specific():
    """读取指定内容数据，返回内容列表"""
    try:
        # 连接数据库
        conn = sqlite3.connect('data/accounts.db')
        cursor = conn.cursor()
        
        # 查询指定内容
        cursor.execute("SELECT content FROM contents WHERE type = 'specific' ORDER BY id")
        results = cursor.fetchall()
        
        # 将结果转换为列表
        content_list = [row[0] for row in results]
        
        conn.close()
        return content_list
        
    except Exception as e:
        print(f"读取失败: {e}")
        return []

def read_movies_specific():
    """读取指定电影数据，返回电影列表"""
    try:
        # 连接数据库
        conn = sqlite3.connect('data/accounts.db')
        cursor = conn.cursor()
        
        # 查询指定电影
        cursor.execute("SELECT movie_id, rating FROM movies WHERE type = 'specific' ORDER BY id")
        results = cursor.fetchall()
        
        # 将结果转换为列表，每个元素为 (movie_id, rating) 元组
        movies_list = [(row[0], row[1]) for row in results]
        
        conn.close()
        return movies_list
        
    except Exception as e:
        print(f"读取电影数据失败: {e}")
        return []


zhanghao_xuhao = 0  # 默认从第一个账号开始

def panduan_zhanghaoshifoudenglu():
    """
    判断全局账号序号对应的账号是否已登录豆瓣。
    登录成功返回True，否则尝试下一个账号，直到账号用尽。
    """
    global zhanghao_xuhao

    # 读取所有账号信息（假设有一个函数read_all_accounts返回账号列表）
    try:
        import sqlite3
        conn = sqlite3.connect('data/accounts.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM accounts ORDER BY id")
        accounts = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"读取账号失败: {e}")
        return False

    total_accounts = len(accounts)
    if total_accounts == 0:
        print("没有可用账号")
        return False

    while zhanghao_xuhao < total_accounts:
        username, password = accounts[zhanghao_xuhao]
        print(f"尝试账号序号 {zhanghao_xuhao+1}: {username}")

        # 打开浏览器并判断登录状态（假设有LiulanqiPeizhi和RenwuLiucheng类）
        from renwuliucheng import LiulanqiPeizhi, RenwuLiucheng
        import asyncio

        peizhi = LiulanqiPeizhi(
            zhanghao=username,
            mima=password,
            huanchunlujing="./browser_data"
        )
        liucheng = RenwuLiucheng()
        try:
            # 登录模式
            result = asyncio.run(liucheng.qidong_liulanqi_liucheng(peizhi, "denglu"))
            if result:  # 登录成功
                print(f"账号 {username} 登录成功")
                return True
            else:
                print(f"账号 {username} 登录失败，关闭浏览器，尝试下一个账号")
                asyncio.run(liucheng.guanbi_liulanqi())
                zhanghao_xuhao += 1
        except Exception as e:
            print(f"账号 {username} 登录过程出错: {e}")
            zhanghao_xuhao += 1
            continue

    print("所有账号均未登录成功")
    return False




def zhixingyanzhengpinglunchengxu(content, movie_id, rating):
    print(f"正在处理内容: {content}，电影ID: {movie_id}，评分: {rating}")
    panduan_zhanghaoshifoudenglu()
    # 这里可以添加具体的处理逻辑
    # ...


def suijidianyingpinglunpingxing():
    # 判断内容数量必须大于电影数量，否则弹窗提示并返回
    content_data = read_content_specific()
    movies_data = read_movies_specific()
    if len(content_data) <= len(movies_data):
        print("数量不符：内容的数量必须大于电影的数量！")
        return [], []
    else:
        print("符合条件，开始依次处理每个内容和电影")
        for i in range(len(movies_data)):
            content = content_data[i]
            movie_id, rating = movies_data[i]
            zhixingyanzhengpinglunchengxu(content, movie_id, rating)
        return content_data, movies_data


 
     

if __name__ == "__main__":
    #read_content_specific()
    suijidianyingpinglunpingxing()
