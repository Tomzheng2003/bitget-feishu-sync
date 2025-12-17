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

# 交易所配置列表
# 交易所配置列表
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
            
            # Smart Journal Logic
            # Smart Journal Logic
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
    
        # --- 2. 历史记录 ---
        try:
            history_list = client.get_history_positions()
        except Exception as e:
            log_error(f"[{ex_name}] 获取历史仓位失败: {e}")
            history_list = []
        
        log_info(f"[{ex_name}] 历史记录: {len(history_list)} 条")
        
        for pos in history_list:
            unique_id = get_unique_id(ex_name, pos)
            if unique_id in finalized_ids: continue
            
            c_time_ms = int(pos.get("ctime") or pos.get("cTime") or 0)
            u_time_ms = int(pos.get("utime") or pos.get("uTime") or 0)
            # 1. 提取 PnL (Gross Profit)
            pnl = float(pos.get("pnl", 0))

            # 2. 计算总手续费 (开仓费 + 平仓费 + 资金费) - 通常为负数
            total_fee = float(pos.get("openFee", 0)) + float(pos.get("closeFee", 0)) + float(pos.get("totalFunding", 0))
            
            # 3. 计算净收益 (Net Profit) = PnL + Total Fee
            # Bitget 的 netProfit 字段通常已经是净值，但为了确保万无一失，我们手动算
            final_profit = pnl + total_fee

            # === 核心逻辑: 尝试关联 Holding 记录以获取杠杆信息 ===
            # === 核心逻辑: 尝试关联 Holding 记录以获取杠杆信息 ===
            cached_data = feishu_cache.get(unique_id, {})
            cached_leverage = cached_data.get("leverage", 0)
            
            # 如果缓存没有，且是 Binance (未来备用)，尝试去找 Holding
            if not cached_leverage and ex_name == "Binance":
                 holding_id = f"Binance_{pos['symbol']}_{pos['holdSide']}_HOLDING"
                 if holding_id in feishu_cache:
                     cached_leverage = feishu_cache[holding_id].get("leverage", 0)

            # 严格模式: 如果不知道杠杆(cached_leverage == 0)，说明这是机器人未追踪过的历史数据
            # 为了防止覆盖用户手动填写的正确数据，直接跳过处理
            if cached_leverage == 0:
                # log_info(f"[{ex_name}] ⏭️ 跳过未追踪历史: {pos.get('symbol')} (无杠杆信息)")
                continue
            
            # 计算 ROE (使用净收益)
            
            # 计算 ROE (使用净收益)
            roe = 0
            open_val = float(pos.get("openAvgPrice", 0)) * float(pos.get("openTotalPos", 0) or pos.get("size", 0))
            if open_val > 0:
                margin = open_val / cached_leverage
                roe = final_profit / margin

            fields = {
                "交易所": ex_name,
                "开仓时间": c_time_ms,
                "币种": pos.get("symbol", ""),
                "方向": "多" if pos.get("holdSide") == "long" else "空",
                "入场价": float(pos.get("openAvgPrice", 0)),
                "出场价": float(pos.get("closeAvgPrice", 0)),
                "收益额": final_profit, # 确认是净收益
                "收益率": roe,
                "手续费": total_fee,
                "状态": "盈利" if final_profit > 0 else "亏损",
                "positionId": unique_id, # 最终 ID
                "平仓时间": u_time_ms,
                "持仓时间": format_duration(c_time_ms, u_time_ms),
                "杠杆": int(cached_leverage)
            }
    
            # === 核心逻辑: 尝试关联 Holding 记录 ===
            record_id = None
            
            # 1. 先查缓存里的 History ID (常规)
            cached_data = feishu_cache.get(unique_id, {})
            record_id = cached_data.get("record_id")
            
            # 2. 如果没找到，且是 Binance，尝试去找对应的 "HOLDING" 记录进行合并
            if not record_id and ex_name == "Binance":
                holding_id = f"Binance_{pos['symbol']}_{pos['holdSide']}_HOLDING"
                # 查缓存
                if holding_id in feishu_cache:
                    record_id = feishu_cache[holding_id].get("record_id")
                    log_info(f"  [{ex_name}] 🔗 关联持仓记录: {holding_id} -> {unique_id}")
                    # 清除 Holding 缓存，因为它变身了
                    del feishu_cache[holding_id]
                    
                # 如果缓存也没，查飞书 (双保险)
                if not record_id:
                    record_id = feishu_client.find_record(holding_id)
                    if record_id:
                        log_info(f"  [{ex_name}] 🔗 发现远程持仓: {holding_id}")
    
            # 3. 如果还是没有，按常规 ID 查 (补录情况)
            if not record_id: 
                record_id = feishu_client.find_record(unique_id)
            
            if record_id:
                log_info(f"  [{ex_name}] 🔵 订单完结: {fields['币种']}")
                if feishu_client.update_record(record_id, fields): finalized_ids.add(unique_id)
            else:
                log_info(f"  [{ex_name}] 🟣 补录历史: {fields['币种']}")
                if feishu_client.create_record(fields):
                    # synced_ids.add(unique_id)
                    finalized_ids.add(unique_id)
            
            # 频率限制保护: 飞书 API 创建记录通常有 5 QPS 限制
            # 如果大量补录，必须暂停以防被封禁或卡死
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
