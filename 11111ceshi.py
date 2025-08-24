import random
import time
 
def 随机打星_电影电视音乐读书():
 
    print("随机打星_电影电视音乐读书")
    

rating_min =1
rating_max =3
operation_interval_min=3
operation_interval_max=5
# 生成 rating_min 到 rating_max 之间的随机整数（包含两端值）
random_rating = random.randint(rating_min, rating_max)
print(random_rating)
for i in range(random_rating):
    caozuojiange = random.randint(operation_interval_min, operation_interval_max)
    print( f"第 {i+1} 次循环 延迟：{caozuojiange}")
    time.sleep(caozuojiange)
    随机打星_电影电视音乐读书()
    
 