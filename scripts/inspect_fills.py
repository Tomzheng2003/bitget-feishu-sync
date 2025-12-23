
import os
import sys
import json
import time
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

def inspect_fills():
    symbol = "LINKUSDT"
    print(f"--- Inspecting Fills for {symbol} ---")
    
    try:
        # Search last 30 days
        start_time = int((time.time() - 30 * 86400) * 1000)
        params = {
            "productType": "USDT-FUTURES",
            "symbol": symbol,
            "startTime": str(start_time),
            "limit": 20
        }
        
        resp = client.fills(params) # Endpoint: /api/v2/mix/order/fills
        data = resp.get("data", {}).get("fillList", [])
        
        if data:
            print(f"Found {len(data)} fills.")
            print("--- Latest Fill Details ---")
            latest_fill = data[0]
            print(json.dumps(latest_fill, indent=2, ensure_ascii=False))
            
            order_id = latest_fill.get("orderId")
            if order_id:
                print(f"\n--- Fetching Order Detail for ID: {order_id} ---")
                detail_params = {
                    "productType": "USDT-FUTURES",
                    "symbol": symbol,
                    "orderId": order_id
                }
                detail_resp = client.detail(detail_params)
                detail_data = detail_resp.get("data", {})
                print(json.dumps(detail_data, indent=2, ensure_ascii=False))
                
                # Check for preset SL
                print(f"\n[Result] PresetSL: {detail_data.get('presetStopLossPrice')}")
        else:
            print("No fills found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_fills()
