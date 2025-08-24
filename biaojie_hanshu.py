def update_poster_status(window, is_old_series=False):
    """更新海报状态和类型"""
    global 全_海报图数据, 类型
    
    # 假设全_海报图数据用字典表示
    全_海报图数据 = {"看过或想看": ""}

    if is_old_series:
        类型 = "collect"
        全_海报图数据["看过或想看"] = "看过"
    else:
        # 获取main.py中run_status_combo的选中项
        选中项文本 = window.run_status_combo.currentText()
        
        if 选中项文本 == "看过":
            类型 = "collect"
            全_海报图数据["看过或想看"] = "看过"
        elif 选中项文本 == "在看":
            类型 = "do"
            全_海报图数据["看过或想看"] = "在看"
        elif 选中项文本 == "想看":
            类型 = "wish"
            全_海报图数据["看过或想看"] = "想看"
    
    return 全_海报图数据, 类型