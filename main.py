# main.py - 主程序入口 (多交易所版: Bitget + Binance)
# 交易日志自动同步系统

import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 导入功能模块
import bitget_client
import binance_client
import feishu_client
import logging
from logging.handlers import TimedRotatingFileHandler

# 加载环境变量
load_dotenv()

# ==========================
# 日志配置 (Log Rotation)
# ==========================
LOG_DIR = "data/logs"
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except:
        LOG_DIR = "logs"
        if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, "trade.log")

logger = logging.getLogger("TradeSync")
logger.setLevel(logging.INFO)

# 1. 文件处理器
file_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
file_handler.suffix = "%Y-%m-%d"
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)

# 2. 控制台处理器
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_info(msg): logger.info(msg)
def log_error(msg): logger.error(msg)

# 将状态文件移入 data 目录，配合 Docker 挂载整个 data 目录使用
STATE_FILE = "data/state.json"
# 确保 data 目录存在
if not os.path.exists("data"):
    try:
        os.makedirs("data")
    except:
        pass

try:
    poll_env = os.getenv("POLL_INTERVAL", "10")
    if not poll_env: poll_env = "10"
    POLL_INTERVAL = int(poll_env)
except Exception:
    POLL_INTERVAL = 10

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e:
            print(f"[Core] 加载状态文件失败: {e}")
            return {}
    return {}

def save_state(state: dict):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Core] 保存状态文件失败: {e}")

def get_unique_id(exchange, pos: dict) -> str:
    """唯一标识符: {Exchange}_{Symbol}_{Side}_{Time}"""
    # 1. 历史记录: 使用自带的唯一ID (Binance OrderId / TranId)
    if pos.get("id"):
        return f"{exchange}_{pos['symbol']}_{pos.get('holdSide', 'side')}_{pos['id']}"
    
    # 2. Binance 持仓: 使用固定 ID，方便平仓时查找并合并
    if exchange == "Binance":
         return f"Binance_{pos.get('symbol')}_{pos.get('holdSide')}_HOLDING"
         
    # 3. 常规持仓 (Bitget): 使用 cTime 去重
    symbol = pos.get("symbol", "")
    side = pos.get("holdSide", "")
    c_time = pos.get("cTime") or pos.get("ctime") or pos.get("CTime") or "0"
    return f"{exchange}_{symbol}_{side}_{c_time}"

def format_duration(start_ms, end_ms):
    try:
        if not end_ms or not start_ms: return ""
        diff_ms = int(end_ms) - int(start_ms)
        if diff_ms < 0: return "0s"
        seconds = int(diff_ms / 1000)
        if seconds < 60: return f"{seconds}s"
        elif seconds < 3600: return f"{seconds // 60}m {seconds % 60}s"
        elif seconds < 86400: return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
        else: return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"
    except: return ""

# 交易所配置
EXCHANGES = [
    {"name": "Bitget", "client": bitget_client},
    # {"name": "Binance", "client": binance_client} # 暂时关闭币安，专注于 Bitget 稳定性
]

def sync_tasks():
    state = load_state()
    synced_ids = set(state.get("synced_ids", []))
    feishu_cache = state.get("feishu_cache", {})
    
    # 优化: 如果缓存为空(全新启动)，先全量拉取飞书记录，避免 N+1 查询
    if not feishu_cache:
        try:
            feishu_cache = feishu_client.get_all_records()
            state["feishu_cache"] = feishu_cache
            # 不必立即保存，函数末尾会存
        except Exception as e:
            log_error(f"初始化飞书缓存失败: {e}")

    finalized_ids = set(state.get("finalized_ids", []))
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始同步 (Interval: {POLL_INTERVAL}s)")

    for ex in EXCHANGES:
        ex_name = ex["name"]
        client = ex["client"]
        
        # --- 1. 当前持仓 ---
        try:
            open_positions = client.get_positions()
        except Exception as e:
            log_error(f"[{ex_name}] 获取持仓失败: {e}")
            open_positions = []
            
        print(f"[{ex_name}] 持仓: {len(open_positions)} 个")

        for pos in open_positions:
            unique_id = get_unique_id(ex_name, pos)
            
            c_time_ms = int(pos.get("cTime") or 0)
            entry_price = float(pos.get("openPriceAvg") or pos.get("openAvgPrice") or 0)
            leverage = int(pos.get("leverage", 0))
            unrealized_pnl = float(pos.get("unrealizedPL", 0))
            
            # 计算 ROE
            roe = float(pos.get("roe", 0))
            margin_size = float(pos.get("marginSize", 0))
            if roe == 0 and margin_size > 0:
                 roe = round((unrealized_pnl / margin_size), 4)

            fields = {
                "交易所": ex_name,
                "开仓时间": c_time_ms, # 飞书日期字段建议传时间戳
                "币种": pos.get("symbol", ""),
                "方向": "多" if pos.get("holdSide") == "long" else "空",
                "杠杆": leverage,
                "入场价": entry_price,
                "出场价": 0,
                "收益额": unrealized_pnl, 
                "收益率": roe,
                "状态": "持仓中",
                "positionId": unique_id,
                "平仓时间": None,
                "持仓时间": format_duration(c_time_ms, int(time.time() * 1000)) + " (ing)"
            }
            
            # Smart Journal: 检查是否已存在
            cached_data = feishu_cache.get(unique_id)
            if not cached_data:
                # Case 1: 全新持仓 -> 必须创建
                log_info(f"  [{ex_name}] 🟢 新增持仓: {fields['币种']}")
                existing_id = feishu_client.find_record(unique_id)
                if existing_id:
                    feishu_client.update_record(existing_id, fields)
                    record_id = existing_id
                else:
                    record_id = feishu_client.create_record(fields)
                
                if record_id:
                    feishu_cache[unique_id] = {
                        "record_id": record_id,
                        "entry_price": entry_price,
                        "leverage": leverage
                    }
                    synced_ids.add(unique_id)
            else:
                # Case 2: 已存在的持仓 -> 检查是否发生"结构性变更" (DCA)
                last_entry_price = cached_data.get("entry_price", 0)
                last_leverage = cached_data.get("leverage", 0)
                record_id = cached_data.get("record_id")
                
                # Binance 特殊处理：因为 ID 是固定的，防止重复刷新，可以加一点价格阈值
                is_dca_event = abs(entry_price - last_entry_price) > (entry_price * 0.000001) or leverage != last_leverage
                
                if is_dca_event:
                    log_info(f"  [{ex_name}] 🟡 仓位变动: {fields['币种']}")
                    if feishu_client.update_record(record_id, fields):
                        feishu_cache[unique_id]["entry_price"] = entry_price
                        feishu_cache[unique_id]["leverage"] = leverage

    # 保存缓存状态 (Open Position loop end)
    
        # --- 2. 历史记录 (只更新，不创建) ---
        try:
            history_list = client.get_history_positions()
        except Exception as e:
            log_error(f"[{ex_name}] 获取历史仓位失败: {e}")
            history_list = []
        
        log_info(f"[{ex_name}] 历史记录: {len(history_list)} 条")
        
        for pos in history_list:
            unique_id = get_unique_id(ex_name, pos)
            if unique_id in finalized_ids:
                continue
            
            # === Step 1: 尝试找到飞书中对应的记录 ===
            cached_data = feishu_cache.get(unique_id, {})
            record_id = cached_data.get("record_id")
            cached_leverage = cached_data.get("leverage", 0)
            
            # 智能关联 (v4.6): 如果 ID 没匹配上，尝试用时间戳模糊匹配
            if not record_id:
                current_ctime = int(pos.get("ctime") or pos.get("cTime") or 0)
                for cid, cdata in feishu_cache.items():
                    if not cdata.get("record_id"):
                        continue
                    if not cid.startswith(f"{ex_name}_{pos['symbol']}_{pos['holdSide']}"):
                        continue
                    try:
                        cached_ctime = int(cid.split("_")[-1])
                        if abs(cached_ctime - current_ctime) < 3000:  # 3秒内视为同一单
                            log_info(f"[{ex_name}] 🔗 ID修复: 时间差 {abs(cached_ctime - current_ctime)}ms")
                            cached_data = cdata
                            record_id = cdata.get("record_id")
                            cached_leverage = cdata.get("leverage", 0)
                            break
                    except:
                        continue
            
            # === Step 2: 如果飞书里没有这条记录，跳过 (不创建新记录) ===
            if not record_id:
                continue
            
            # === Step 3: 构造更新数据 ===
            c_time_ms = int(pos.get("ctime") or pos.get("cTime") or 0)
            u_time_ms = int(pos.get("utime") or pos.get("uTime") or 0)
            pnl = float(pos.get("pnl", 0))
            total_fee = float(pos.get("openFee", 0)) + float(pos.get("closeFee", 0)) + float(pos.get("totalFunding", 0))
            final_profit = pnl + total_fee
            
            fields = {
                "交易所": ex_name,
                "开仓时间": c_time_ms,
                "币种": pos.get("symbol", ""),
                "方向": "多" if pos.get("holdSide") == "long" else "空",
                "入场价": float(pos.get("openAvgPrice", 0)),
                "出场价": float(pos.get("closeAvgPrice", 0)),
                "收益额": final_profit,
                "手续费": total_fee,
                "状态": "盈利" if final_profit > 0 else "亏损",
                "positionId": unique_id,
                "平仓时间": u_time_ms,
                "持仓时间": format_duration(c_time_ms, u_time_ms),
            }
            
            # === Step 4: 只有知道杠杆时才写入杠杆和收益率 ===
            if cached_leverage > 0:
                open_val = float(pos.get("openAvgPrice", 0)) * float(pos.get("openTotalPos", 0) or pos.get("size", 0))
                margin = open_val / cached_leverage if open_val > 0 else 0
                roe = final_profit / margin if margin > 0 else 0
                fields["杠杆"] = int(cached_leverage)
                fields["收益率"] = roe
            
            # === Step 5: 更新记录 ===
            log_info(f"  [{ex_name}] 🔵 订单完结: {fields['币种']}")
            if feishu_client.update_record(record_id, fields):
                finalized_ids.add(unique_id)
            
            time.sleep(0.2)

                    
        # Save
        state["feishu_cache"] = feishu_cache
        state["finalized_ids"] = list(finalized_ids)[-2000:]
        state["synced_ids"] = list(synced_ids)[-3000:]
        state["last_sync_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_state(state)
    
if __name__ == "__main__":
    log_info(f"启动双交易所同步 (Bitget + Binance)")
    log_info(f"轮询间隔: {POLL_INTERVAL} 秒")
    while True:
        try:
            sync_tasks()
            # log_info(f"等待 {POLL_INTERVAL} 秒...")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log_info("程序停止")
            break
        except Exception as e:
            log_error(f"主循环异常: {e}")
            time.sleep(POLL_INTERVAL)
