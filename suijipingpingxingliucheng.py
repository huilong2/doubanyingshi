from data_manager import DataManager
import random
import time
import json
from qitagongju.qita import 获取ai短语

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


def 随机打星_电影电视音乐读书(window):
    # 初始化DataManager
    data_manager = DataManager('data')
    
    # 定义rating_type到表名的映射
    table_mapping = {
        '电影': 'dianying',
        '电视': 'dianshi',
        '读书': 'dushu',
        '音乐': 'yinyue'
    }
    
    # 从UI组件获取rating_type值
    dianying_leixing_xuhao = window.rating_type.currentIndex()
    # 根据选择的索引确定表名
    if dianying_leixing_xuhao == 4:  # 随机选择
        dianying_leixing_xuhao = random.randint(0, 3)
        if dianying_leixing_xuhao == 0:
            shujuku_biaoming = 'dianying'
        elif dianying_leixing_xuhao == 1:
            shujuku_biaoming = 'dianshi'
        elif dianying_leixing_xuhao == 2:
            shujuku_biaoming = 'dushu'
        else:
            shujuku_biaoming = 'yinyue'
    else:
        # 根据索引选择对应的表
        rating_types = ['电影', '电视', '读书', '音乐']
        if 0 <= dianying_leixing_xuhao < len(rating_types):
            shujuku_biaoming = table_mapping[rating_types[dianying_leixing_xuhao]]
        else:
            # 如果索引无效，默认使用'电影'
            shujuku_biaoming = 'dianying'
    
    # 从数据库中随机获取一个完整记录
    shuju_shuzu = 随机获取一个数据(shujuku_biaoming)
    if shuju_shuzu:
        print (shuju_shuzu[1], shuju_shuzu[2], shuju_shuzu[3])
        # 获取对应的类型名称
        rating_types = ['电影', '电视', '读书', '音乐']
        type_name = rating_types[dianying_leixing_xuhao] if 0 <= dianying_leixing_xuhao < len(rating_types) else '电影'
        # 返回随机记录、类型名称、表名和random_choice
        return shuju_shuzu, type_name, shujuku_biaoming, dianying_leixing_xuhao
    else:
        print(f"表 {shujuku_biaoming} 中没有数据")
        return None, '电影', shujuku_biaoming, dianying_leixing_xuhao
    
    print("随机打星_电影电视音乐读书")
 
    
def 随机评论(window=None):
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
            执行随机评论操作(username, account, window)
        else:  # 账号未勾选
            print(f"跳过未勾选账号: {username}")
            continue
    
    print("随机评论流程执行完成")

def 执行随机评论操作(username, account, window):
    print(f"  为账号 {username} 执行随机评论操作")
    suijipingxingjige = random.randint(rating_min, rating_max)
    print(f"随机评星几个{suijipingxingjige}")
    for i in range(suijipingxingjige):
        caozuojiange = random.randint(operation_interval_min, operation_interval_max)
        print(f"第 {i + 1} 次循环 延迟：{caozuojiange}")
        time.sleep(caozuojiange)
        shuju_shuzu, type_name, shujuku_biaoming, dianying_leixing_xuhao = 随机打星_电影电视音乐读书(window)
        if shuju_shuzu is None:
            print(f"警告: 未能获取到{type_name}数据，跳过本次评星")
            continue    
        else:
         # 当有数据时，执行后续步骤
            print(f"成功获取{type_name}数据，开始处理...")
            import douban_xieyi  
            # 从配置读取评星列表与状态
            star_rating_str = str(config.get('star_rating', '3|4|5'))
            values_list = [v for v in star_rating_str.split('|') if v]
            dajixing = random.choice(values_list) if values_list else '3'
            print(f"选择的星级: {dajixing}")
            run_status = config.get('run_status', '看过')
            interest = get_status(run_status)
            if dianying_leixing_xuhao == 0 or dianying_leixing_xuhao == 1:
                print(f"选择的类型: {type_name}")
                baifenbi_text = window.percentage_label.text() if hasattr(window.percentage_label, 'text') else ''
                print(f"百分比文本: {baifenbi_text}")
                random_number = random.randint(1, 100)
                print(f"随机数: {random_number}")
                # 安全地将百分比文本转换为整数，默认为0
                try:
                    percentage = int(baifenbi_text)
                except (ValueError, TypeError):
                    print(f"警告: 无效的百分比值 '{baifenbi_text}'，使用默认值0")
                    percentage = 0
                if random_number <= percentage:
                    comment_text = 获取ai短语(shuju_shuzu[1])
                    print(f"获取到的ai短语: {comment_text}")
                else:
                    print(f"没有获取到ai短语")
                    comment_text = ""
            else:
                comment_text = ""
            # 取对应表的条目ID作为 movie_id（第2列为 *_id）
            movie_id = shuju_shuzu[1]
            # 从account中获取cookie（根据之前的代码结构，cookie在第4个位置，索引为3）
            cookie = account[3] if len(account) > 3 else ''
            # 尝试从window获取user_agent，如果不可用则使用默认值
            user_agent = window.user_agent if hasattr(window, 'user_agent') else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            
            douban_xieyi.submit_movie_rating(
                cookie=cookie,
                movie_id=movie_id,
                rating=dajixing,
                interest=interest,
                user_agent=user_agent,
                comment=comment_text,
                proxy=account[9],
                verify=False
            )

# 随机评论（）    # 这行代码已注释，避免语法错误







# 生成 rating_min 到 rating_max 之间的随机整数（包含两端值）
