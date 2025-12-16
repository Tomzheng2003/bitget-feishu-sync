# main.py - 主程序入口 (智能日志模式)
# Bitget 交易日志自动同步系统

import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 导入功能模块
import bitget_client
import feishu_client
import logging
from logging.handlers import TimedRotatingFileHandler

# 加载环境变量
load_dotenv()

# ==========================
# 日志配置 (Log Rotation)
# ==========================
LOG_DIR = "/app/logs"
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except:
        LOG_DIR = "logs" # 如果在本地运行
        if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, "trade.log")

# 创建 Logger
logger = logging.getLogger("TradeSync")
logger.setLevel(logging.INFO)

# 1. 文件处理器: 每天午夜轮转，保留7天
file_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
file_handler.suffix = "%Y-%m-%d" # 文件后缀格式
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)

# 2. 控制台处理器: 用于 Docker logs 查看
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)


STATE_FILE = "state.json"
# 默认轮询间隔 10 秒，可通过环境变量覆盖
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 10))


def load_state() -> dict:
    """Step 3.1: 状态读取"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Core] 加载状态文件失败: {e}")
            return {}
    return {}


def save_state(state: dict):
    """Step 3.2: 状态写入"""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Core] 保存状态文件失败: {e}")


def get_unique_id(pos: dict) -> str:
    """
    生成唯一标识符
    逻辑：{symbol}_{holdSide}_{cTime}
    """
    symbol = pos.get("symbol", "")
    side = pos.get("holdSide", "")
    c_time = pos.get("cTime") or pos.get("ctime") or pos.get("CTime") or "0"
    return f"{symbol}_{side}_{c_time}"


def calculate_roe(pnl, margin_size=0, open_avg=0, total=0, leverage=0):
    """计算收益率 (%)"""
    try:
        pnl = float(pnl)
        if margin_size and float(margin_size) > 0:
            return round((pnl / float(margin_size)), 4)
        
        # 否则尝试推算保证金
        if open_avg and total and leverage:
             margin = (float(open_avg) * float(total)) / int(leverage)
             if margin > 0:
                 return round((pnl / margin), 4)
        return 0.0
    except:
        return 0.0


def format_duration(start_ms, end_ms):
    """计算持仓时长，返回人性化字符串"""
    try:
        if not end_ms or not start_ms: return ""
        diff_ms = int(end_ms) - int(start_ms)
        if diff_ms < 0: return "0s"
        
        seconds = int(diff_ms / 1000)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        elif seconds < 86400:
            return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
        else:
            return f"{seconds // 86400}d {(seconds % 86400) // 3600}h"
    except:
        return ""


def sync_tasks():
    state = load_state()
    synced_ids = set(state.get("synced_ids", []))
    
    # 智能缓存：不仅存 Record ID，还存关键状态 (Entry Price, Leverage)
    # 用于本地对比，决定是否需要调用 API 更新
    # 结构: {"unique_id": {"record_id": "xxx", "entry_price": 1.23, "leverage": 20}}
    feishu_cache = state.get("feishu_cache", {})
    
    # 已完结 ID 集合 (防止重复更新历史)
    finalized_ids = set(state.get("finalized_ids", []))
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始同步 (间隔: {POLL_INTERVAL}s)...")
    
    # ==========================
    # 1. 同步当前持仓 (Open Positions)
    # ==========================
    try:
        open_positions = bitget_client.get_positions()
    except Exception as e:
        print(f"[Bitget] 获取持仓失败: {e}")
        open_positions = []
        
    print(f"[Core] 当前持仓: {len(open_positions)} 个")
    
    current_holding_ids = set()

    for pos in open_positions:
        unique_id = get_unique_id(pos)
        current_holding_ids.add(unique_id)
        
        # 提取关键数据
        c_time_ms = int(pos.get("cTime") or 0)
        # 兼容不同接口的字段名
        entry_price = float(pos.get("openPriceAvg") or pos.get("openAvgPrice") or 0)
        leverage = int(pos.get("leverage", 0))
        
        # 浮动盈亏 (即便我们平时不更新它，但如果触发更新时还是需要带上最新的)
        margin_size = float(pos.get("marginSize", 0))
        unrealized_pnl = float(pos.get("unrealizedPL", 0))
        roe = float(pos.get("roe", 0))
        if roe == 0 and margin_size > 0:
             roe = round((unrealized_pnl / margin_size), 4)

        fields = {
            "开仓时间": c_time_ms, 
            "币种": pos.get("symbol", ""),
            "方向": "多" if pos.get("holdSide") == "long" else "空",
            "杠杆": leverage,
            "入场价": entry_price,
            "出场价": 0, # 持仓中
            "收益额": unrealized_pnl, 
            "收益率": roe,
            "状态": "持仓中",
            "positionId": unique_id,
            "平仓时间": None,
            "持仓时间": format_duration(c_time_ms, int(time.time() * 1000)) + " (ing)"
        }
        
        # === 核心优化逻辑 ===
        cached_data = feishu_cache.get(unique_id)
        
        if not cached_data:
            # Case 1: 全新持仓 -> 必须创建
            print(f"  -> 🟢 新增持仓: {fields['币种']} (API Call)")
            # 先尝试找一下万一已有记录 (防止 state 丢失导致重复创建)
            existing_id = feishu_client.find_record(unique_id)
            if existing_id:
                record_id = existing_id
                print(f"     (发现已存在记录: {record_id})")
                feishu_client.update_record(record_id, fields)
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
            
            # 判断是否有关键变化 (价格变动超过 0.0001% 视为补仓/减仓; 杠杆变化)
            # 浮动盈亏的变化被忽略，不触发 API 调用
            is_dca_event = abs(entry_price - last_entry_price) > (entry_price * 0.000001) or leverage != last_leverage
            
            if is_dca_event:
                print(f"  -> 🟡 仓位变动(补仓/调杠杆): {fields['币种']} (API Call)")
                success = feishu_client.update_record(record_id, fields)
                if success:
                    # 更新缓存
                    feishu_cache[unique_id]["entry_price"] = entry_price
                    feishu_cache[unique_id]["leverage"] = leverage
            else:
                # Case 3: 只有浮动盈亏变化 -> 跳过更新 (省钱!)
                # print(f"  -> ⚪️ 忽略浮动盈亏: {fields['币种']} (Cached)")
                pass

    # 保存缓存状态
    state["feishu_cache"] = feishu_cache
    state["synced_ids"] = list(synced_ids)
    save_state(state)

    # ==========================
    # 2. 同步历史仓位 (History Positions)
    # ==========================
    try:
        history_list = bitget_client.get_history_positions()
    except Exception as e:
        print(f"[Bitget] 获取历史失败: {e}")
        history_list = []
        
    print(f"[Core] 历史记录: {len(history_list)} 条 (最近)")
    history_list.reverse()
    
    for pos in history_list:
        unique_id = get_unique_id(pos)
        
        # 如果已经标记为"完结"，直接跳过 (绝对零消耗)
        if unique_id in finalized_ids:
            continue
            
        # 准备数据
        c_time_ms = int(pos.get("ctime") or pos.get("cTime") or 0)
        u_time_ms = int(pos.get("utime") or pos.get("uTime") or 0)
        net_profit = float(pos.get("netProfit", 0))
        pnl = float(pos.get("pnl", 0))
        final_profit = net_profit if net_profit != 0 else pnl
        
        # 尝试从缓存获取之前的 marginSize 来计算精确 ROE
        cached_data = feishu_cache.get(unique_id, {})
        # 注意: 这里的 openAvg 可能是补仓后的均价，这是我们想要的
        open_avg = float(pos.get("openAvgPrice", 0))
        total_vol = float(pos.get("openTotalPos", 0)) # 总成交量
        leverage = int(pos.get("leverage", 0))
        
        # 自动计算 ROE (净收益 / 保证金)
        # 保证金 = (均价 * 数量) / 杠杆
        cal_margin = 0
        if leverage > 0 and total_vol > 0:
            cal_margin = (open_avg * total_vol) / leverage
            
        roe = 0
        if cal_margin > 0:
            roe = round(final_profit / cal_margin, 4)
        
        fields = {
            "开仓时间": c_time_ms,
            "币种": pos.get("symbol", ""),
            "方向": "多" if pos.get("holdSide") == "long" else "空",
            "入场价": open_avg,
            "出场价": float(pos.get("closeAvgPrice", 0)),
            "收益额": final_profit,
            "收益率": roe, # 使用一定要重新计算的 ROE
            "状态": "盈利" if final_profit > 0 else "亏损",
            "positionId": unique_id,
            "平仓时间": u_time_ms,
            "持仓时间": format_duration(c_time_ms, u_time_ms)
        }
        if leverage > 0:
            fields["杠杆"] = leverage

        # 查找 Record ID (优先本地缓存)
        record_id = cached_data.get("record_id")
        
        if not record_id:
            # 缓存里没有，说明可能是系统还没跑时开的单，去飞书查一次
            record_id = feishu_client.find_record(unique_id)
        
        if record_id:
            log_info(f"  -> 🔵 订单完结: {fields['币种']} (API Call)")
            success = feishu_client.update_record(record_id, fields)
            if success:
                finalized_ids.add(unique_id)
                # 完结后可以清除 cache 里的过程数据，但为了 ID 映射建议保留
        else:
            log_info(f"  -> 🟣 补录历史: {fields['币种']} (API Call)")
            new_id = feishu_client.create_record(fields)
            if new_id:
                synced_ids.add(unique_id)
                finalized_ids.add(unique_id)

    # 保存最终状态
    state["feishu_cache"] = feishu_cache
    state["finalized_ids"] = list(finalized_ids)
    state["synced_ids"] = list(synced_ids)
    state["last_sync_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_state(state)


if __name__ == "__main__":
    log_info(f"启动智能同步模式 (API 节约版)")
    log_info(f"轮询间隔: {POLL_INTERVAL} 秒")
    while True:
        try:
            sync_tasks()
            log_info(f"等待 {POLL_INTERVAL} 秒...")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log_info("程序停止")
            break
        except Exception as e:
            log_error(f"主循环异常: {e}")
            time.sleep(POLL_INTERVAL) # 出错也等待同样时间
