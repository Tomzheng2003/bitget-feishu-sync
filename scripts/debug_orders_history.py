
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

client = OrderApi(API_KEY, SECRET_KEY, PASSPHRASE)

def debug_history():
    symbol = "LINKUSDT"
    print(f"--- Debugging History for {symbol} ---")
    
    # 1. Normal Order History (Last 24h)
    print("\n[Normal Order History]")
    try:
        start_time = int((time.time() - 30 * 86400) * 1000)
        params = {
            "productType": "USDT-FUTURES",
            "symbol": symbol, # Explicitly requested
            "startTime": str(start_time),
            "limit": 50
        }
        resp = client.ordersHistory(params)
        orders = resp.get("data", {}).get("list", [])
        if orders:
            print(f"Found {len(orders)} historical orders.")
            # Filter for LINKUSDT manually to see if any exist
            targets = [o for o in orders if o.get('symbol') == symbol]
            if targets:
                print("Latest LINKUSDT Order:")
                print(json.dumps(targets[0], indent=2, ensure_ascii=False))
            else:
                print("No LINKUSDT orders in recent history.")
        else:
            print("No history found.")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Plan Order History (Last 7 days)
    print("\n[Plan Order History]")
    try:
        start_time = int((time.time() - 30 * 86400) * 1000)
        # Try different plan types if needed? Or does it return all?
        # Often ordersPlanHistory requires planType? Docs say 'profit_loss' is default? Or separate?
        # Let's try iterating types again if it requires it.
        
        # Test 1: profit_loss
        params = {
            "productType": "USDT-FUTURES",
             "startTime": str(start_time),
             "planType": "profit_loss",
             "limit": 20
        }
        resp = client.ordersPlanHistory(params)
        orders = resp.get("data", {}).get("list", [])
        if orders:
            print(f"Found {len(orders)} Plan(profit_loss) history.")
            targets = [o for o in orders if o.get('symbol') == symbol]
            if targets:
                print("Latest LINKUSDT Plan Order:")
                print(json.dumps(targets[0], indent=2, ensure_ascii=False))
        else:
            print("No profit_loss history.")

        # Test 2: normal_plan
        params["planType"] = "normal_plan"
        resp = client.ordersPlanHistory(params)
        orders = resp.get("data", {}).get("list", [])
        if orders:
            print(f"Found {len(orders)} Plan(normal_plan) history.")
            targets = [o for o in orders if o.get('symbol') == symbol]
            if targets:
                print("Latest LINKUSDT Normal Plan Order:")
                print(json.dumps(targets[0], indent=2, ensure_ascii=False))
        else:
            print("No normal_plan history.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_history()
