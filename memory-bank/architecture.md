# 项目架构说明

## 目录结构

```
trade/
├── main.py              # 主程序入口
├── bitget_client.py     # Bitget API 封装
├── feishu_client.py     # 飞书 API 封装
├── requirements.txt     # Python 依赖清单
├── .env                 # 环境变量配置（不提交到 Git）
├── state.json           # 同步状态存储（运行时生成）
├── bitget/              # Bitget 官方 SDK
├── memory-bank/         # 项目文档
├── feature-implementation.md # 功能规划
├── feishu-api/          # 飞书 API 参考文档
└── README.md            # 项目使用说明
```

---

## 文件说明

### main.py
主程序入口，负责：
- 加载状态文件
- 协调同步流程
- 实现轮询循环（每 30 秒）
- 处理程序退出

### bitget_client.py
Bitget 交易所 API 封装，负责：
- 加载 Bitget API 凭据
- 初始化 Bitget 客户端
- `get_positions()` - 获取当前持仓
- `get_history_positions()` - 获取历史仓位

### feishu_client.py
飞书多维表格 API 封装，负责：
- 加载飞书应用凭据
- 初始化飞书客户端
- `create_record()` - 创建表格记录
- `find_record()` - 查询记录
- `update_record()` - 更新记录

### bitget/
Bitget 官方 Python SDK，包含：
- `bitget_api.py` - 基础 API 类
- `client.py` - HTTP 客户端封装
- `v1/` - V1 版本 API
- `v2/` - V2 版本 API（本项目使用）
- `ws/` - WebSocket 支持

### .env
环境变量配置文件：
```
BITGET_API_KEY      # Bitget API 密钥
BITGET_SECRET_KEY   # Bitget 密钥
BITGET_PASSPHRASE   # Bitget 口令

FEISHU_APP_ID       # 飞书应用 ID
FEISHU_APP_SECRET   # 飞书应用密钥
FEISHU_APP_TOKEN    # 多维表格 Token
FEISHU_TABLE_ID     # 数据表 ID
```

### state.json
运行时生成的状态文件：
- 记录已同步的 `synced_ids` 集合
- `pos_metadata` 缓存：
  - 存储持仓时的杠杆 (`leverage`) 和保证金 (`marginSize`)
  - 即使仓位平仓后，也能从缓存回填杠杆信息
- JSON 格式，人类可读

---

## 数据流

```
Bitget API  ──►  bitget_client.py  ──►  main.py  ──►  feishu_client.py  ──►  飞书表格
                                            │
                                            ▼
                                       state.json
```

---

## Bitget API 响应结构

### 当前持仓 (all-position)
```json
{
  "symbol": "BTCUSDT",
  "holdSide": "long",
  "openPriceAvg": "90405.8",
  "total": "0.0032",
  "leverage": "10",
  "unrealizedPL": "0.056"
}
```

### 历史仓位 (history-position)
```json
{
  "positionId": "1383079723100946434",  // 唯一标识
  "symbol": "ZECUSDT",
  "holdSide": "short",
  "openAvgPrice": "455.48",
  "closeAvgPrice": "473.97",
  "pnl": "-7.18993",
  "netProfit": "-7.61832118"
}