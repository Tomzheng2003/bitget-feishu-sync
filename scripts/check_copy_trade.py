
import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bitget.v2.mix.order_api import OrderApi
except ImportError:
    sys.path.append(os.getcwd())
    from bitget.v2.mix.order_api import OrderApi

load_dotenv()
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

client = OrderApi(API_KEY, SECRET_KEY, PASSPHRASE)

def check_copy_trade():
    print("--- Checking Copy Trading Endpoints (Revised) ---")
    
    # As a Follower
    try:
        params = {"productType": "USDT-FUTURES"}
        resp = client.followerQueryCurrentOrders(params)
        data = resp.get("data")
        
        if not data:
            print("[Follower Current] No data returned.")
            return

        order_list = []
        if isinstance(data, list):
            order_list = data
        elif isinstance(data, dict):
            # Try common keys
            if "entrustList" in data:
                order_list = data["entrustList"]
            elif "list" in data:
                order_list = data["list"]
            else:
                print(f"[Follower Current] Unknown data dict keys: {data.keys()}")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return

        if order_list:
            print(f"[Follower Current] Found {len(order_list)} orders.")
            print("--- First Order Details ---")
            print(json.dumps(order_list[0], indent=2, ensure_ascii=False))
            
            # Check for SL fields
            print("\n--- Check SL Fields ---")
            for o in order_list:
                print(f"Symbol: {o.get('symbol')}, SL: {o.get('stopLossPrice')}, PresetSL: {o.get('presetStopLossPrice')}")
        else:
            print("[Follower Current] List is empty.")
            
    except Exception as e:
        print(f"[Follower Error] {e}")

if __name__ == "__main__":
    check_copy_trade()
