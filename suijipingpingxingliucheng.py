from data_manager import DataManager
import random
import time
import json

# 从 peizhi.json 加载设置
def get_status(status_str):
    if status_str == "看过":
        return "COLLECT"
    elif status_str == "在看":
        return "DO"
    elif status_str == "想看":
        return "WISH"
    else:
        return None


def load_settings():
    try:
        with open('data/peizhi.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get('function_settings', {})
    except FileNotFoundError:
        print("错误: 未找到 'data/peizhi.json' 文件。")
        return {}
    except json.JSONDecodeError:
        print("错误: 'data/peizhi.json' 文件格式不正确。")
        return {}

# 从配置文件获取rating_type值
def get_rating_type_from_config():
    config = load_settings()
    return config.get('rating_type', '电影')  # 默认为'电影'

# 加载配置并赋值给全局变量
config = load_settings()
rating_min = int(config.get('rating_min', 1))
rating_max = int(config.get('rating_max', 3))
operation_interval_min = int(config.get('operation_interval_min', 3))
operation_interval_max = int(config.get('operation_interval_max', 5))

# 初始化rating_type下拉框
# 注意：此处仅为示例，实际应用中应根据GUI框架进行初始化
# 例如，在PyQt5中可以使用：self.rating_type = QComboBox()
rating_type = None


def 随机获取一个数据(table_name): 
    # 初始化DataManager
    data_manager = DataManager('data')
    table_data = data_manager.get_table_data(table_name)   
    # 如果没有数据，返回None
    if not table_data:
        return None    
    # 随机选择一条完整数据并返回
    random_record = random.choice(table_data)    
    return random_record


def 随机打星_电影电视音乐读书():
    # 初始化DataManager
    data_manager = DataManager('data')
    
    # 定义rating_type到表名的映射
    table_mapping = {
        '电影': 'dianying',
        '电视': 'dianshi',
        '读书': 'dushu',
        '音乐': 'yinyue'
    }
    
    # 从配置文件获取rating_type值
    config_rating_type = get_rating_type_from_config()
    
    # 根据配置的rating_type选择不同的表
    if config_rating_type in table_mapping:
        table_name = table_mapping[config_rating_type]
    elif config_rating_type == '随机':  # 随机选择
        random_choice = random.randint(0, 3)
        if random_choice == 0:
            table_name = 'dianying'
        elif random_choice == 1:
            table_name = 'dianshi'
        elif random_choice == 2:
            table_name = 'dushu'
        else:  # random_choice == 3
            table_name = 'yinyue'
    else:
        # 如果配置值无效，默认使用'电影'
        table_name = 'dianying'
    
    # 从数据库中随机获取一个完整记录
    random_record = 随机获取一个数据(table_name)
    if random_record:
        print (random_record[1], random_record[2], random_record[3])
        # 返回随机记录和对应的序号
        return random_record, config_rating_type
    else:
        print(f"表 {table_name} 中没有数据")
        return None, config_rating_type
    
    print("随机打星_电影电视音乐读书")
 
    
def 随机评论():
    data_manager = DataManager()    
    accounts = data_manager.get_accounts()       
    # 遍历账号列表
    for account in accounts:
        # 解析账号数据
        # 根据data_manager.py中的accounts表结构，字段顺序为：
        # id, username, password, ck, nickname, account_id, login_status, homepage, 
        # login_time, proxy, running_status, note, gouxuan
        account_id, username, password, ck, nickname, account_db_id, login_status, homepage, \
        login_time, proxy, running_status, note, gouxuan = account
        
        # 检查账号是否勾选
        if gouxuan == 1:  # 账号已勾选
            print(f"正在处理账号: {username}")
            # 在这里执行随机评论操作
            # 例如：执行评论逻辑、评星等
            执行随机评论操作(username, account)
        else:  # 账号未勾选
            print(f"跳过未勾选账号: {username}")
            continue
    
    print("随机评论流程执行完成")

def 执行随机评论操作(username, account, ):
    print(f"  为账号 {username} 执行随机评论操作")
    suijipingxingjige = random.randint(rating_min, rating_max)
    print(f"随机评星几个{suijipingxingjige}")
    for i in range(suijipingxingjige):
        caozuojiange = random.randint(operation_interval_min, operation_interval_max)
        print(f"第 {i + 1} 次循环 延迟：{caozuojiange}")
        time.sleep(caozuojiange)
        result, rating_type = 随机打星_电影电视音乐读书()
        if result is None:
            print(f"警告: 未能获取到{rating_type}数据，跳过本次评星")
            continue    
        else:
         # 当有数据时，执行后续步骤
            print(f"成功获取{rating_type}数据，开始处理...")
            import douban_xieyi  
            # 假设界面上的文本框对象名为 star_rating_textbox，获取其文本内容
            star_rating = star_rating_textbox.get()
            values_list = star_rating.split('|')
            dajixing = random.choice(values_list)
            print(dajixing)
            print(f"🔍 DEBUG: 选择框_类型_文本值: {window.run_status_combo.currentText()}")
            print(f"🔍 DEBUG: 选择框_类型_索引: {window.run_status_combo.currentIndex()}")
            # 分组选择检查已删除
            # 获取选择框的当前值
            rating_type = window.rating_type.currentText()
          
            interest = get_status(rating_type)


            douban_xieyi.submit_movie_rating(   
                movie_id=result[0],
                interest="watch",
                rating=dajixing
                comment=result[4],
                proxy=account[10],
                verify=False
            )

# 随机评论（）    # 这行代码已注释，避免语法错误







# 生成 rating_min 到 rating_max 之间的随机整数（包含两端值）
