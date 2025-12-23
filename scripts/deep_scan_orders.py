
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

def deep_scan():
    target_symbol = "LINKUSDT"
    print(f"--- Deep Scan for Orders on {target_symbol} ---")
    
    # 1. List of ALL possible planTypes found in various API docs/versions
    # 'normal_plan': Plan order
    # 'profit_loss': TP/SL
    # 'loss_plan': Stop loss?
    # 'pos_profit_loss': Position TP/SL?
    candidate_types = [
        "profit_loss", 
        "normal_plan", 
        "loss_plan", 
        "profit_plan", 
        "pos_profit_loss", 
        "pos_loss", 
        "pos_profit", 
        "moving_plan", 
        "track_plan"
    ]
    
    for pt in candidate_types:
        try:
            params = {
                "productType": "USDT-FUTURES",
                "planType": pt,
                "symbol": target_symbol
            }
            # print(f"Testing planType='{pt}'...", end=" ")
            resp = client.ordersPlanPending(params)
            code = resp.get("code")
            msg = resp.get("msg")
            
            if code == "00000":
                data = resp.get("data", {})
                orders = data.get("entrustList", [])
                if orders:
                    print(f"\n[FOUND!] Type: {pt} | Count: {len(orders)}")
                    print(json.dumps(orders[0], indent=2, ensure_ascii=False))
                else:
                    print(f"[Empty] Type: {pt} (Success but no orders)")
            elif code == "40812":
                 print(f"[N/A] Type: {pt} (Not supported/Condition not met)")
            else:
                print(f"[Error] Type: {pt} | Code: {code} | Msg: {msg}")
                
        except Exception as e:
            print(f"[Exception] {e}")

    # 2. Check Normal Pending again strictly
    print("\n--- Checking Normal Pending (Limit) ---")
    try:
        params = {
            "productType": "USDT-FUTURES",
            "symbol": target_symbol
        }
        resp = client.ordersPending(params)
        orders = resp.get("data", {}).get("entrustList", [])
        if orders:
            print(f"[FOUND!] Normal Orders: {len(orders)}")
            print(json.dumps(orders[0], indent=2, ensure_ascii=False))
        else:
            print("[Empty] Normal Pending")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deep_scan()
