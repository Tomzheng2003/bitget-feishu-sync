# bitget_client.py - Bitget API 封装
# 负责与 Bitget 交易所 API 交互

import os
from dotenv import load_dotenv

# Step 1.1: 加载环境变量
load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

# Step 1.2: 初始化 Bitget 客户端
from bitget.bitget_api import BitgetApi

client = BitgetApi(API_KEY, SECRET_KEY, PASSPHRASE)


def get_positions():
    """
    Step 1.3: 获取当前持仓
    调用 Bitget V2 API: GET /api/v2/mix/position/all-position
    返回当前所有未平仓的仓位列表
    """
    try:
        params = {"productType": "USDT-FUTURES"}
        response = client.get("/api/v2/mix/position/all-position", params)
        
        if response.get("code") == "00000":
            return response.get("data", [])
        else:
            print(f"[Bitget] 获取持仓失败: {response.get('msg')}")
            return []
    except Exception as e:
        print(f"[Bitget] 获取持仓异常: {e}")
        return []


def get_history_positions():
    """
    Step 1.4: 获取历史仓位
    调用 Bitget V2 API: GET /api/v2/mix/position/history-position
    返回已平仓的仓位历史记录
    """
    try:
        import time
        # Bitget 默认只查7天，我们需要30天
        start_time = int((time.time() - 30 * 24 * 3600) * 1000)
        params = {
            "productType": "USDT-FUTURES",
            "startTime": str(start_time),
            "limit": 100 # 增加条数限制到最大100 (Int)
        }
        response = client.get("/api/v2/mix/position/history-position", params)
        
        if response.get("code") == "00000":
            return response.get("data", {}).get("list", [])
        else:
            print(f"[Bitget] 获取历史仓位失败: {response.get('msg')}")
            return []
    except Exception as e:
        print(f"[Bitget] 获取历史仓位异常: {e}")
        return []



