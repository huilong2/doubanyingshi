from zhixingliucheng import get_proxy_ip
 

proxy_api_url = "http://proxy.siyetian.com/apis_get.html?token=AesJWLNp2Z31kaJdXTqFFeNRUQz4ERVdXTn1STqFUeORUR31ERjBTTEFEeOR0a65EVnpnT6d2M.AOycTMwcTN1cTM&limit=1&type=0&time=&split=1&split_text="
    
    # 获取代理IP
proxy_ip = get_proxy_ip(proxy_api_url)
    
if proxy_ip:
    print(f"获取到的代理IP: {proxy_ip}")
else:
    print("获取代理IP失败")