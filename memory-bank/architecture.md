# 项目架构说明 (v4.8)

## 目录结构

```
trade/
├── main.py              # 主程序 (319行)
├── bitget_client.py     # Bitget API 封装
├── binance_client.py    # Binance API 封装 (已禁用)
├── feishu_client.py     # 飞书 API 封装
├── requirements.txt     # Python 依赖
├── config.env           # 环境变量 (不提交 Git)
├── Dockerfile           # Docker 镜像配置
├── docker-compose.yml   # Docker 编排配置
├── bitget/              # Bitget 官方 SDK
├── data/                # 运行时数据 (Docker挂载)
│   ├── state.json       # 同步状态缓存
│   └── logs/            # 日志文件
└── memory-bank/         # 项目文档
```

---

## 核心模块

### main.py
- **持仓监控**: 检测新开仓 → 自动创建飞书记录
- **平仓同步**: 检测平仓 → 更新飞书记录为"盈利/亏损"
- **智能关联 (v4.6)**: 3秒时间窗口修复 ID 漂移
- **不碰原则 (v4.7)**: 未知杠杆时不写入杠杆/ROE
- **只更新原则 (v4.8)**: 历史记录只更新，不创建

### feishu_client.py
- `get_all_records()` - 批量获取所有记录 (启动时缓存)
- `create_record()` - 创建新记录
- `update_record()` - 更新现有记录
- `find_record()` - 按 positionId 查询

---

## 数据流

```
Bitget API  ──►  bitget_client.py  ──►  main.py  ──►  feishu_client.py  ──►  飞书表格
                                           │
                                           ▼
                                      data/state.json (缓存)
```

---

## 状态缓存结构 (state.json)

```json
{
  "feishu_cache": {
    "Bitget_BTCUSDT_long_1734567890123": {
      "record_id": "recXXXXXX",
      "entry_price": 95000.5,
      "leverage": 10
    }
  },
  "synced_ids": ["..."],
  "finalized_ids": ["..."],
  "last_sync_time": "2025-12-21 03:00:00"
}
```