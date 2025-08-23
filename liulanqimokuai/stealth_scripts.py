"""
反检测JavaScript脚本
用于隐藏自动化特征，避免被网站检测
"""

STEALTH_SCRIPTS = {
    # 隐藏WebDriver属性
    "hide_webdriver": """
    // 删除webdriver属性
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    // 删除chrome属性
    delete window.chrome;
    
    // 修改plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    
    // 修改languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-CN', 'zh', 'en'],
    });
    """,
    
    # 隐藏自动化特征
    "hide_automation": """
    // 删除自动化相关属性
    delete window.navigator.__proto__.webdriver;
    
    // 修改permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // 修改webgl
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };
    """,
    
    # 模拟用户行为
    "simulate_user": """
    // 添加随机鼠标移动
    function addRandomMouseMovement() {
        const events = ['mousemove', 'mouseover', 'mouseenter'];
        events.forEach(eventType => {
            document.addEventListener(eventType, (e) => {
                // 添加随机延迟
                setTimeout(() => {
                    e.target.dispatchEvent(new MouseEvent(eventType, {
                        clientX: e.clientX + Math.random() * 10 - 5,
                        clientY: e.clientY + Math.random() * 10 - 5,
                        bubbles: true
                    }));
                }, Math.random() * 100);
            }, { passive: true });
        });
    }
    
    // 添加随机滚动
    function addRandomScroll() {
        let scrollCount = 0;
        const maxScrolls = 3;
        
        const scrollInterval = setInterval(() => {
            if (scrollCount >= maxScrolls) {
                clearInterval(scrollInterval);
                return;
            }
            
            const scrollY = Math.random() * 100;
            window.scrollBy(0, scrollY);
            scrollCount++;
        }, 2000 + Math.random() * 3000);
    }
    
    // 初始化用户行为模拟
    setTimeout(() => {
        addRandomMouseMovement();
        addRandomScroll();
    }, 1000);
    """,
    
    # 修改Canvas指纹
    "modify_canvas": """
    // 修改Canvas指纹
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, ...args) {
        const context = originalGetContext.apply(this, [type, ...args]);
        
        if (type === '2d') {
            const originalFillText = context.fillText;
            context.fillText = function(...args) {
                // 添加随机偏移
                args[1] += Math.random() * 0.1;
                args[2] += Math.random() * 0.1;
                return originalFillText.apply(this, args);
            };
        }
        
        return context;
    };
    """,
    
    # 修改音频指纹
    "modify_audio": """
    // 修改音频指纹
    const originalGetChannelData = AudioBuffer.prototype.getChannelData;
    AudioBuffer.prototype.getChannelData = function(channel) {
        const data = originalGetChannelData.apply(this, [channel]);
        
        // 添加微小随机变化
        for (let i = 0; i < data.length; i += 100) {
            data[i] += (Math.random() - 0.5) * 0.0001;
        }
        
        return data;
    };
    """,
    
    # 修改WebRTC
    "modify_webrtc": """
    // 修改WebRTC
    const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
    navigator.mediaDevices.getUserMedia = function(constraints) {
        return originalGetUserMedia.apply(this, [constraints]).then(stream => {
            // 修改stream的id
            stream.id = 'stream_' + Math.random().toString(36).substr(2, 9);
            return stream;
        });
    };
    """,
    
    # 修改时区
    "modify_timezone": """
    // 修改时区相关
    const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
    Date.prototype.getTimezoneOffset = function() {
        return -480; // 中国时区
    };
    """,
    
    # 修改屏幕信息
    "modify_screen": """
    // 修改屏幕信息
    Object.defineProperty(screen, 'width', {
        get: () => 1920,
    });
    Object.defineProperty(screen, 'height', {
        get: () => 1080,
    });
    Object.defineProperty(screen, 'availWidth', {
        get: () => 1920,
    });
    Object.defineProperty(screen, 'availHeight', {
        get: () => 1040,
    });
    Object.defineProperty(screen, 'colorDepth', {
        get: () => 24,
    });
    Object.defineProperty(screen, 'pixelDepth', {
        get: () => 24,
    });
    """,
}

def get_stealth_script(script_name: str = None) -> str:
    """
    获取反检测脚本
    
    Args:
        script_name: 脚本名称，如果为None则返回所有脚本
        
    Returns:
        str: JavaScript脚本内容
    """
    if script_name:
        return STEALTH_SCRIPTS.get(script_name, "")
    
    # 返回所有脚本的组合
    return "\n".join(STEALTH_SCRIPTS.values())

def get_stealth_script_names() -> list:
    """获取所有可用的脚本名称"""
    return list(STEALTH_SCRIPTS.keys())
