import os
import sys
import traceback

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将当前目录添加到系统路径，确保能导入douban_xieyi模块
sys.path.append(current_dir)

# 导入豆瓣协议模块
from douban_xieyi import submit_movie_rating


def read_cookie_from_file(file_path):
    """从文件中读取cookie字符串"""
    try:
        print(f"尝试读取cookie文件: {file_path}")
        print(f"文件是否存在: {os.path.exists(file_path)}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取所有内容
            content = f.read()
            print(f"文件内容长度: {len(content)} 字符")
            # 去除可能的前后空格和换行符
            cookie = content.strip()
            return cookie
    except Exception as e:
        print(f"读取cookie文件失败: {e}")
        print("错误详情:")
        traceback.print_exc()
        return None


def main():
    # cookie文件路径
    # 先尝试读取新创建的cookie.txt文件
    cookie_file_path = os.path.join(current_dir, 'cookie.txt')
    
    # 读取cookie
    cookie = read_cookie_from_file(cookie_file_path)
    
    if not cookie:
        print("无法获取cookie，测试失败")
        return
    
    print(f"成功读取cookie，长度: {len(cookie)}字符")
    
    # 测试参数
    movie_id = "30429388"  # 示例电影ID，可根据需要修改
    rating = 3  # 评分(1-5)
    interest = "collect"  # 兴趣类型，如'collect'表示想看
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"  # 用户代理
    comment = "这是一条测试评论，通过读取外部cookie文件进行提交"
    
    print(f"\n开始测试提交电影评分和评论...")
    print(f"电影ID: {movie_id}")
    print(f"评分: {rating}")
    print(f"兴趣类型: {interest}")
    print(f"评论内容: {comment}")
    
    # 调用submit_movie_rating函数进行测试
    # 注意：这里为了测试添加了verify=False来跳过SSL验证
    # 实际使用时应考虑配置正确的CA证书
    try:
        result = submit_movie_rating(
            cookie=cookie,
            movie_id=movie_id,
            rating=rating,
            interest=interest,
            user_agent=user_agent,
            comment=comment,
            verify=False  # 跳过SSL证书验证
        )
    
        if result:
            print(f"\n测试结果: 成功")
            print(f"返回数据: {result}")
        else:
            print("\n测试结果: 失败，未获取到返回数据")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")


if __name__ == "__main__":
    main()