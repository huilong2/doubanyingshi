import uvicorn
from qitagongju.api import app

def start_api():
    """启动API服务"""
    import threading
    
    def run():
        uvicorn.run(app, host="0.0.0.0", port=8001)
    
    # 在后台线程中启动API服务
    api_thread = threading.Thread(target=run, daemon=True)
    api_thread.start()
    return api_thread

if __name__ == "__main__":
    start_api()
    # 保持主线程运行
    import time
    while True:
        time.sleep(1)