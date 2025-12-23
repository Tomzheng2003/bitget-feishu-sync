
import os
import sys
import json
import time
from dotenv import load_dotenv

# Add parent directory to sys.path to import bitget_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bitget.v2.mix.order_api import OrderApi
    from bitget.bitget_api import BitgetApi # For positions
except ImportError:
    # Try alternate path if running from root
    sys.path.append(os.getcwd())
    from bitget.v2.mix.order_api import OrderApi
    from bitget.bitget_api import BitgetApi

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

if not API_KEY:
    print("Error: Bitget credentials not found in .env")
    sys.exit(1)

order_client = OrderApi(API_KEY, SECRET_KEY, PASSPHRASE)
# Use generic client for positions if needed, or re-use bitget_api 
# bitget_client.py uses BitgetApi class directly.
base_client = BitgetApi(API_KEY, SECRET_KEY, PASSPHRASE)

def get_positions():
    print(f"\n--- 1. 查询当前持仓 ---")
    try:
        params = {"productType": "USDT-FUTURES"}
        response = base_client.get("/api/v2/mix/position/all-position", params)
        data = response.get("data", [])
        if data:
            print(f"发现 {len(data)} 个持仓:")
            for p in data:
                print(f"  - {p.get('symbol')} ({p.get('holdSide')}) | Size: {p.get('total')}")
            return [p.get('symbol') for p in data]
        else:
            print("当前无任何持仓。")
            return []
    except Exception as e:
        print(f"查询持仓异常: {e}")
        return []

def check_orders(symbols):
    print(f"\n--- 2. 针对持仓币种查询挂单 ---")
    
    # Plan Types to check
    # Also check 'normal_plan' (Limit Trigger) and 'profit_loss' (TPSL)
    plan_types = ["profit_loss", "normal_plan"]
    
    for symbol in set(symbols):
        print(f"\n>> 检查币种: {symbol}")
        
        # A. Check Plan Orders (TPSL)
        for pt in plan_types:
            try:
                params = {"productType": "USDT-FUTURES", "planType": pt, "symbol": symbol}
                resp = order_client.ordersPlanPending(params)
                orders = resp.get("data", {}).get("entrustList", [])
                if orders:
                    print(f"   [Plan: {pt}] 发现 {len(orders)} 单:")
                    for o in orders:
                        print(f"     -> 触发价: {o.get('triggerPrice')}, 类型: {o.get('planType')}, ID: {o.get('orderId')}")
                else:
                    print(f"   [Plan: {pt}] 无")
            except Exception as e:
                print(f"   [Plan: {pt}] Error: {e}")

        # B. Check Normal Pending (Limit Orders)
        try:
            params = {"productType": "USDT-FUTURES", "symbol": symbol}
            resp = order_client.ordersPending(params)
            orders = resp.get("data", {}).get("entrustList", [])
            if orders:
                print(f"   [Normal Limit] 发现 {len(orders)} 单:")
                for o in orders:
                    print(f"     -> 价格: {o.get('price')}, 类型: 挂单, ID: {o.get('orderId')}")
            else:
                 print(f"   [Normal Limit] 无")
        except Exception as e:
            print(f"   [Normal Limit] Error: {e}")

if __name__ == "__main__":
    active_symbols = get_positions()
    if active_symbols:
        check_orders(active_symbols)
        print("\n检测结束。如果您看到了您的止损单，请确认其类型 (Plan vs Normal)。")
    else:
        print("\n由于无持仓，无法针对特定币种查询。请确认您当前账号是否有活跃持仓。")
