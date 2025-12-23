
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bitget.bitget_api import BitgetApi
except ImportError:
    sys.path.append(os.getcwd())
    from bitget.bitget_api import BitgetApi

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

client = BitgetApi(API_KEY, SECRET_KEY, PASSPHRASE)

def inspect_positions():
    print("--- Inspecting Raw Position Data ---")
    try:
        params = {"productType": "USDT-FUTURES"}
        response = client.get("/api/v2/mix/position/all-position", params)
        data = response.get("data", [])
        
        if not data:
            print("No positions found.")
            return

        print(f"Found {len(data)} positions. Dumping first one fully:")
        # Dump the first key position to see all available fields
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
        
        # Check specific fields for all
        print("\n\n--- Quick Check for SL fields ---")
        for p in data:
            symbol = p.get('symbol')
            # Potential keys for SL based on experience: 'sl', 'stopLoss', 'monitor', 'planType'
            print(f"Symbol: {symbol}")
            print(f"  > sl: {p.get('sl')}")
            print(f"  > stopLoss: {p.get('stopLoss')}")
            print(f"  > stopLossPrice: {p.get('stopLossPrice')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_positions()
