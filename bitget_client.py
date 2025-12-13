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
        params = {"productType": "USDT-FUTURES"}
        response = client.get("/api/v2/mix/position/history-position", params)
        
        if response.get("code") == "00000":
            return response.get("data", {}).get("list", [])
        else:
            print(f"[Bitget] 获取历史仓位失败: {response.get('msg')}")
            return []
    except Exception as e:
        print(f"[Bitget] 获取历史仓位异常: {e}")
        return []


# 测试代码 (仅在直接运行此文件时执行)
if __name__ == "__main__":
    print("=" * 50)
    print("Bitget Client 测试")
    print("=" * 50)
    
    print(f"\nAPI Key: {API_KEY[:10]}..." if API_KEY else "API Key: 未设置")
    
    print("\n[测试] 获取当前持仓...")
    positions = get_positions()
    print(f"当前持仓数量: {len(positions)}")
    if positions:
        for p in positions[:3]:  # 只显示前3个
            print(f"  - {p.get('symbol')}: {p.get('holdSide')} x {p.get('total')}")
    
    print("\n[测试] 获取历史仓位...")
    history = get_history_positions()
    print(f"历史仓位数量: {len(history)}")
    if history:
        for h in history[:3]:  # 只显示前3个
            print(f"  - {h.get('symbol')}: PnL={h.get('pnl')}, ID={h.get('positionId')}")
