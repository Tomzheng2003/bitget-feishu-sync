import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# 基础配置
BINANCE_BASE_URL = "https://fapi.binance.com"
# 务必去除空格
API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "").strip()

def get_sign(query_string):
    """
    生成签名
    """
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature

def send_request(method, endpoint, params={}):
    """发送请求"""
    headers = {
        "X-MBX-APIKEY": API_KEY
    }
    
    # 1. 准备基础参数
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 10000 
    
    # 2. 生成 Query String
    query_string = urlencode(params)
    
    # 3. 计算签名
    signature = get_sign(query_string)
    
    # 4. 拼接最终 Query
    final_query = f"{query_string}&signature={signature}"
    
    url = f"{BINANCE_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            full_url = f"{url}?{final_query}"
            response = requests.get(full_url, headers=headers, timeout=15)
        else:
            response = requests.post(url, headers=headers, data=final_query, timeout=15)
            
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400 and "Signature" in response.text:
             print(f"[Binance] 签名错误: {response.text}")
             return None
        elif response.status_code == 418 or response.status_code == 429:
             print(f"[Binance] 限频警告: {response.text}")
             return None
        else:
            # 某些报错(如没数据)不打印Error
            # print(f"[Binance] Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"[Binance] Network Error: {e}")
        return None

def get_positions():
    """获取当前持仓 (U本位合约)"""
    data = send_request("GET", "/fapi/v2/positionRisk")
    if not data: return []
    
    positions = []
    for item in data:
        amt = float(item.get("positionAmt", 0))
        if amt != 0:
            pos = {
                "symbol": item["symbol"],
                "holdSide": "long" if amt > 0 else "short",
                "leverage": item["leverage"],
                "openAvgPrice": float(item["entryPrice"]),
                "cTime": int(item["updateTime"]),
                "marginSize": abs(float(item["positionAmt"]) * float(item["entryPrice"]) / float(item["leverage"])),
                "unrealizedPL": float(item["unRealizedProfit"]),
                "netProfit": 0,
                "roe": 0 
            }
            positions.append(pos)
    return positions

def _get_active_symbols_from_income():
    """
    Step 1: 从资金流水(Income)中找出最近有平仓盈亏的币种
    目的: 解决 userTrades 需要传 symbol 的限制，并自动发现所有有交易的币
    Bitget 默认7天，Binance Income 接口限制单次查询不能超过7天
    """
    symbols = set()
    now_ms = int(time.time() * 1000)
    
    # 循环查询过去 30 天 (4次)
    for i in range(4):
        end_time = now_ms - (i * 7 * 24 * 3600 * 1000)
        start_time = end_time - (7 * 24 * 3600 * 1000)
        
        params = {
            "incomeType": "REALIZED_PNL",
            "limit": 1000,
            "startTime": start_time,
            "endTime": end_time
        }
        
        try:
            data = send_request("GET", "/fapi/v1/income", params)
            if data:
                for item in data:
                    if item.get("symbol"):
                        symbols.add(item["symbol"])
        except Exception:
            pass # 某段失败不影响整体
            
    return symbols

def get_history_positions():
    """
    获取历史成交 (智能聚合版)
    1. 查 Income 发现活跃币种
    2. 查 userTrades 获取详细成交
    3. 按 OrderId 聚合，把多次成交合并为一条“平仓记录”
    """
    # 1. 发现活跃币种
    active_symbols = _get_active_symbols_from_income()
    # 如果列表为空，说明近期无平仓，直接返回
    if not active_symbols:
        return []
        
    history = []
    
    # 2. 遍历币种查详情 (注意: 币种多时会在此处产生多次请求，但 Docker 轮询有间隔，可接受)
    for symbol in active_symbols:
        params = {
            "symbol": symbol,
            "limit": 500 # 获取该币种最近500笔成交，足够覆盖 Income 的范围
        }
        trades = send_request("GET", "/fapi/v1/userTrades", params)
        if not trades: continue
        
        # 3. 聚合逻辑
        # key: orderId, value: {aggregated_data}
        aggregated_orders = {}
        
        for trade in trades:
            # 过滤掉开仓单 (realizedPnl == 0)
            pnl = float(trade.get("realizedPnl", 0))
            if pnl == 0: continue
            
            order_id = str(trade.get("orderId"))
            
            qty = float(trade.get("qty", 0))
            price = float(trade.get("price", 0))
            side = trade.get("side", "") # SELL or BUY
            time_ms = int(trade.get("time"))
            
            if order_id not in aggregated_orders:
                # 初始化聚合对象
                aggregated_orders[order_id] = {
                    "symbol": symbol,
                    "orderId": order_id,
                    "side": side, # 平仓方向
                    "total_pnl": 0.0,
                    "total_qty": 0.0,
                    "weighted_price_sum": 0.0, # 用于算均价: sum(price * qty)
                    "first_time": time_ms,
                    "last_time": time_ms
                }
            
            # 累加数据
            agg = aggregated_orders[order_id]
            agg["total_pnl"] += pnl
            agg["total_qty"] += qty
            agg["weighted_price_sum"] += (price * qty)
            agg["last_time"] = max(agg["last_time"], time_ms)
            
        # 4. 生成最终记录
        for order_id, agg in aggregated_orders.items():
            total_qty = agg["total_qty"]
            avg_price = agg["weighted_price_sum"] / total_qty if total_qty > 0 else 0
            
            # 转换方向: 如果平仓是 SELL (卖出平多)，则原方向是 Long
            hold_side = "long" if agg["side"] == "SELL" else "short"
            
            pos = {
                # 使用 OrderId 作为唯一标识，完美解决分单问题
                "id": order_id,
                "symbol": agg["symbol"],
                "holdSide": hold_side,
                "leverage": 0, # trade 接口无杠杆信息
                "openAvgPrice": 0, # 平仓单拿不到开仓均价
                "closeAvgPrice": avg_price, # 聚合后的出场均价
                "netProfit": agg["total_pnl"],
                "pnl": agg["total_pnl"],
                "ctime": agg["last_time"], # 使用最后一次成交时间
                "utime": agg["last_time"],
                "openTotalPos": total_qty
            }
            history.append(pos)
            
    return history
