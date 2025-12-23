
import os
import sys
import json
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bitget.v2.mix.order_api import OrderApi
    from bitget.bitget_api import BitgetApi
except ImportError:
    sys.path.append(os.getcwd())
    from bitget.v2.mix.order_api import OrderApi
    from bitget.bitget_api import BitgetApi

load_dotenv()
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

# Use generic client for positions, OrderApi for history
pos_client = BitgetApi(API_KEY, SECRET_KEY, PASSPHRASE)
order_client = OrderApi(API_KEY, SECRET_KEY, PASSPHRASE)

def get_active_symbols():
    try:
        params = {"productType": "USDT-FUTURES"}
        response = pos_client.get("/api/v2/mix/position/all-position", params)
        data = response.get("data", [])
        return [p.get("symbol") for p in data]
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []

def check_sl_for_symbol(symbol):
    try:
        # Search last 30 days
        start_time = int((time.time() - 30 * 86400) * 1000)
        params = {
            "productType": "USDT-FUTURES",
            "symbol": symbol,
            "startTime": str(start_time),
            "limit": 50 
        }
        
        # 1. Get Fills to find the opening order ID
        resp = order_client.fills(params) 
        fills = resp.get("data", {}).get("fillList", [])
        
        if not fills:
            return "No recent fills"
            
        # Strategy: Find the most recent 'open' trade
        # Note: 'tradeSide' is usually 'open' or 'close'
        opening_fill = None
        for fill in fills:
             if fill.get("tradeSide") == "open":
                 opening_fill = fill
                 break # Found the latest open
        
        if not opening_fill:
             # Fallback: just take the oldest fill if we can't find explicit open? 
             # Or maybe the position is older than 30 days.
             return "No 'open' fill found in 30d"

        order_id = opening_fill.get("orderId")
        
        # 2. Get Order Detail
        detail_params = {
            "productType": "USDT-FUTURES",
            "symbol": symbol,
            "orderId": order_id
        }
        detail_resp = order_client.detail(detail_params)
        detail_data = detail_resp.get("data", {})
        
        sl_price = detail_data.get("presetStopLossPrice")
        return sl_price if sl_price else "Not Set"

    except Exception as e:
        return f"Error: {e}"

def main():
    print("--- 正在批量核对持仓止损 (Batch Check SL) ---")
    symbols = get_active_symbols()
    
    if not symbols:
        print("当前无持仓。")
        return

    print(f"检测到 {len(symbols)} 个持仓: {symbols}")
    print("\n{:<15} | {:<20}".format("Symbol", "Initial SL Price"))
    print("-" * 40)
    
    for symbol in symbols:
        res = check_sl_for_symbol(symbol)
        print(f"{symbol:<15} | {res:<20}")
        time.sleep(0.2) # Rate limit niceness

if __name__ == "__main__":
    main()
