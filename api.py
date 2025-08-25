from fastapi import FastAPI, HTTPException
import httpx
import asyncio

app = FastAPI(title="IP Address API", description="API to get IP address information")

async def get_ip_info(ip: str = None):
    """获取IP地址信息"""
    try:
        # 构建请求URL
        if ip:
            url = f"http://ip.hl22.com/ip.php?action=getip&ip_url={ip}"
        else:
            url = "http://ip.hl22.com/ip.php?action=getip&ip_url="
        
        # 发送HTTP请求
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"请求失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取IP信息失败: {str(e)}")

@app.get("/ip", summary="获取IP地址信息", description="获取当前IP地址或指定IP地址的信息")
async def get_ip(ip: str = None):
    """获取IP地址信息接口"""
    ip_info = await get_ip_info(ip)
    return {"ip_info": ip_info}

@app.get("/", summary="API根路径", description="返回API基本信息")
async def root():
    """API根路径"""
    return {
        "message": "IP Address API",
        "description": "API to get IP address information",
        "endpoints": {
            "get_ip": "/ip?ip={ip_address} (ip参数可选)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)