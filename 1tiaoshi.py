# content_specific_table 列表内的全部内容 按照顺序调试出来的例子 
# 你感觉是 直接读取表格内容 还是直接从数据库读取 哪种方式好点

import sqlite3

# 简单直接的方式：从数据库读取content_specific_table数据
def read_content_specific():
    """读取指定内容数据"""
    try:
        # 连接数据库
        conn = sqlite3.connect('data/accounts.db')
        cursor = conn.cursor()
        
        # 查询指定内容
        cursor.execute("SELECT content FROM contents WHERE type = 'specific' ORDER BY id")
        results = cursor.fetchall()
        
        print("content_specific_table 数据:")
        for i, (content,) in enumerate(results, 1):
            print(f"{i}. {content}")
        
        conn.close()
        
    except Exception as e:
        print(f"读取失败: {e}")

if __name__ == "__main__":
    read_content_specific()

