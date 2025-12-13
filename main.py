# main.py - 主程序入口
# Bitget 交易日志自动同步系统

import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 导入功能模块
import bitget_client
import feishu_client

# 加载环境变量
load_dotenv()

STATE_FILE = "state.json"


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
    # 元数据缓存：用于存储持仓时的杠杆等信息，以便历史记录回填
    # 结构: {"unique_id": {"leverage": 20, "margin": 100...}}
    pos_metadata = state.get("pos_metadata", {})
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始同步...")
    
    # ==========================
    # 1. 同步当前持仓 (Open Positions)
    # ==========================
    open_positions = bitget_client.get_positions()
    print(f"[Core] 当前持仓: {len(open_positions)} 个")
    
    for pos in open_positions:
        unique_id = get_unique_id(pos)
        
        # 缓存元数据 (特别是杠杆)
        if unique_id not in pos_metadata:
             pos_metadata[unique_id] = {
                 "leverage": int(pos.get("leverage", 0)),
                 "marginSize": float(pos.get("marginSize", 0))
             }
        
        # 字段映射
        c_time_ms = int(pos.get("cTime") or 0)
        
        # 处理 API 字段不一致问题 (active uses openPriceAvg, history uses openAvgPrice)
        entry_price = float(pos.get("openPriceAvg") or pos.get("openAvgPrice") or 0)
        
        # 即使 API 不返回 roe，我们也可以自己算
        margin_size = float(pos.get("marginSize", 0))
        unrealized_pnl = float(pos.get("unrealizedPL", 0))
        
        # 优先使用 API 的 roe，如果没有则计算
        roe = float(pos.get("roe", 0))
        if roe == 0 and margin_size > 0:
             roe = round((unrealized_pnl / margin_size), 4)
            
        fields = {
            "开仓时间": c_time_ms, 
            "币种": pos.get("symbol", ""),
            "方向": "多" if pos.get("holdSide") == "long" else "空",
            "杠杆": int(pos.get("leverage", 0)),
            "入场价": entry_price,
            "出场价": 0, # 持仓中
            "收益额": unrealized_pnl, # 持仓用未实现盈亏
            "收益率": roe,
            "状态": "持仓中",
            "positionId": unique_id,
            "平仓时间": None,
            "持仓时间": format_duration(c_time_ms, int(time.time() * 1000)) + " (ing)"
        }
            
        feishu_id = feishu_client.find_record(unique_id)
        
        if feishu_id:
            print(f"  -> 更新持仓: {fields['币种']}")
            feishu_client.update_record(feishu_id, fields)
        else:
            print(f"  -> 新增持仓: {fields['币种']}")
            new_id = feishu_client.create_record(fields)
            if new_id:
                synced_ids.add(unique_id)

    # 保存元数据缓存
    state["pos_metadata"] = pos_metadata
    save_state(state) # 中途保存一次防止崩溃

    # ==========================
    # 2. 同步历史仓位 (History Positions)
    # ==========================
    history_list = bitget_client.get_history_positions()
    print(f"[Core] 历史记录: {len(history_list)} 条 (最近)")
    history_list.reverse()
    
    for pos in history_list:
        unique_id = get_unique_id(pos)
        
        # 尝试从缓存获取杠杆
        cached_meta = pos_metadata.get(unique_id, {})
        leverage = cached_meta.get("leverage", 0) or int(pos.get("leverage", 0))
        
        # 字段映射
        c_time_ms = int(pos.get("ctime") or pos.get("cTime") or 0)
        u_time_ms = int(pos.get("utime") or pos.get("uTime") or 0)
        
        # 使用 netProfit (净收益，包含手续费)
        net_profit = float(pos.get("netProfit", 0))
        pnl = float(pos.get("pnl", 0))
        
        # 优先用净收益，如果API没返则回退到pnl
        final_profit = net_profit if net_profit != 0 else pnl
        
        fields = {
            "开仓时间": c_time_ms,
            "币种": pos.get("symbol", ""),
            "方向": "多" if pos.get("holdSide") == "long" else "空",
            # "杠杆": leverage, # 移出，下面判断
            "入场价": float(pos.get("openAvgPrice", 0)),
            "出场价": float(pos.get("closeAvgPrice", 0)),
            "收益额": final_profit,
            "状态": "盈利" if final_profit > 0 else "亏损",
            "positionId": unique_id,
            "平仓时间": u_time_ms,
            "持仓时间": format_duration(c_time_ms, u_time_ms)
        }
        
        # 仅当杠杆有效时才更新，防止覆盖用户手填的历史数据
        if leverage > 0:
            fields["杠杆"] = leverage
        
        # 补算收益率
        roe = calculate_roe(
            final_profit, 
            margin_size=cached_meta.get("marginSize", 0),
            open_avg=pos.get("openAvgPrice"),
            total=pos.get("openTotalPos"),
            leverage=leverage
        )
        # 仅当有计算结果时才更新，防止覆盖用户手填
        if roe != 0:
            fields["收益率"] = roe
        
        feishu_id = feishu_client.find_record(unique_id)
        
        if feishu_id:
            print(f"  -> 更新历史: {fields['币种']}")
            feishu_client.update_record(feishu_id, fields)
        else:
            print(f"  -> 补录历史: {fields['币种']}")
            new_id = feishu_client.create_record(fields)
            if new_id:
                synced_ids.add(unique_id)

    # 保存最终状态
    state["synced_ids"] = list(synced_ids)
    state["last_sync_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_state(state)


if __name__ == "__main__":
    while True:
        try:
            sync_tasks()
            print("\n等待 30 秒...")
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n程序停止")
            break
        except Exception as e:
            print(f"\n[Error] 主循环异常: {e}")
            time.sleep(30)
